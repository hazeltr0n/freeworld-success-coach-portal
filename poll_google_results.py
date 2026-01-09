#!/usr/bin/env python3
"""
Google Results Poller
Checks for completed Google job scrapes and processes them through the pipeline.

Runs every 30 mins on Mon/Wed/Fri from 2:30am-5am Central (after main scraper submits tasks).
"""

import os
import sys
import csv
import requests
import logging
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional
from send_scrape_notification import (
    collect_job_stats_from_dataframe,
    send_detailed_scrape_report
)

# Configure logging to both file and stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/google_poller.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_pending_google_tasks() -> List[Dict]:
    """Get Google tasks that have been submitted but not yet processed"""
    from supabase_utils import get_client

    client = get_client()
    if not client:
        print("❌ Supabase client not available")
        return []

    try:
        result = client.table('async_job_queue')\
            .select('*')\
            .eq('job_type', 'google_jobs')\
            .eq('status', 'submitted')\
            .execute()

        return result.data or []
    except Exception as e:
        print(f"❌ Error fetching pending tasks: {e}")
        return []


def check_outscraper_task(task_id: str) -> Optional[Dict]:
    """Check if Outscraper task is complete and download results"""
    api_key = os.getenv('OUTSCRAPER_API_KEY')
    if not api_key:
        print("❌ OUTSCRAPER_API_KEY not set")
        return None

    try:
        # Step 1: Check task status
        status_url = f"https://api.outscraper.cloud/requests/{task_id}"
        headers = {'X-API-KEY': api_key}

        response = requests.get(status_url, headers=headers, timeout=30)
        response.raise_for_status()

        result = response.json()
        status = result.get('status')

        if status in ['In Progress', 'Pending']:
            return None  # Not ready yet
        elif status != 'Success':
            print(f"⚠️  Task {task_id} status: {status}")
            return None

        # Step 2: Task complete - download the actual results
        print(f"   📥 Downloading results from Outscraper...")
        sys.stdout.flush()  # Force flush to ensure output is visible
        download_url = f"https://api.outscraper.cloud/requests/{task_id}?format=json"

        download_response = requests.get(download_url, headers=headers, timeout=300)  # 5 minute timeout for large files
        download_response.raise_for_status()

        # Parse the downloaded JSON data
        downloaded_data = download_response.json()

        # Outscraper returns data directly as a list OR wrapped in {'data': [...]}
        if isinstance(downloaded_data, list):
            # Direct list format
            print(f"   ✅ Downloaded {len(downloaded_data)} jobs")
            return {'data': downloaded_data}  # Wrap in dict for consistent processing
        elif isinstance(downloaded_data, dict) and 'data' in downloaded_data:
            # Wrapped format
            print(f"   ✅ Downloaded {len(downloaded_data.get('data', []))} result batches")
            return downloaded_data
        else:
            print(f"   ⚠️  No data in downloaded results")
            return None

    except Exception as e:
        print(f"❌ Error checking/downloading task {task_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_google_results(task_id: str, results_data: Dict, csv_mapping: str) -> Dict:
    """Process Google results through pipeline and upload to Supabase"""
    from pipeline_v3 import FreeWorldPipelineV3
    from canonical_transforms import transform_ingest_google

    try:
        # Load query-to-market mapping
        with open(csv_mapping, 'r') as f:
            reader = csv.DictReader(f)
            query_to_market = {row['Query']: row['Market'] for row in reader}

        print(f"   📋 Loaded {len(query_to_market)} query→market mappings")

        # Extract jobs from Outscraper response
        raw_jobs = results_data.get('data', [])
        print(f"   📊 Raw results: {len(raw_jobs)} job batches from Outscraper")

        # Flatten and map to markets
        all_jobs = []
        for item in raw_jobs:
            if isinstance(item, dict):
                # Single job dict (flat response)
                query = item.get('query', '')
                market = query_to_market.get(query, 'Unknown')
                item['market'] = market
                all_jobs.append(item)
            elif isinstance(item, list):
                # List of jobs (nested response)
                for job in item:
                    if isinstance(job, dict):
                        query = job.get('query', '')
                        market = query_to_market.get(query, 'Unknown')
                        job['market'] = market
                        all_jobs.append(job)

        print(f"   📦 Extracted {len(all_jobs)} individual jobs")

        if not all_jobs:
            return {
                'success': False,
                'total_jobs': 0,
                'quality_jobs': 0,
                'error': 'No jobs in results'
            }

        # Transform to canonical format
        print(f"   🔄 Transforming to canonical format...")
        df = transform_ingest_google(all_jobs, f'google_poll_{task_id}', 'scheduled_config')

        if df.empty:
            return {
                'success': False,
                'total_jobs': 0,
                'quality_jobs': 0,
                'error': 'Transform produced empty DataFrame'
            }

        print(f"   ✅ Transformed {len(df)} jobs")

        # Run through pipeline
        print(f"   🧠 Processing through pipeline...")
        pipeline = FreeWorldPipelineV3()

        df = pipeline._stage2_normalization(df)
        df = pipeline._stage3_business_rules(df, "", {})
        df = pipeline._stage4_deduplication(df)
        df = pipeline._stage5_5_route_rules(df)

        # AI Classification
        print(f"   🤖 Running AI classification...")
        df = pipeline._stage5_ai_classification(df, classifier_type="cdl")

        # Routing
        df = pipeline._stage6_routing(df, "")

        # Link tracking (SKIP for scheduled scraper)
        pipeline._stage7_output(
            df=df,
            market="",
            custom_location="",
            generate_pdf=False,
            generate_csv=False,
            generate_html=False,
            force_memory_only=False
        )

        # Upload to Supabase
        print(f"   💾 Uploading to Supabase...")
        pipeline._stage8_storage(pipeline.df, push_to_airtable=False)

        # Calculate metrics
        total_jobs = len(df)
        quality_jobs = len(df[df.get('ai.match', '').isin(['good', 'so-so'])]) if 'ai.match' in df.columns else 0
        uploaded_count = pipeline.supabase_upload_count if hasattr(pipeline, 'supabase_upload_count') else 0

        print(f"   ✅ Complete: {total_jobs} jobs, {quality_jobs} quality, {uploaded_count} uploaded")

        return {
            'success': True,
            'total_jobs': total_jobs,
            'quality_jobs': quality_jobs,
            'uploaded_count': uploaded_count,
            'df': pipeline.df  # Return DataFrame for notification stats
        }

    except Exception as e:
        print(f"   ❌ Error processing results: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'total_jobs': 0,
            'quality_jobs': 0,
            'error': str(e),
            'df': None
        }


def update_job_status(job_id: int, status: str, result_data: Dict):
    """Update job status in async_job_queue"""
    from supabase_utils import get_client

    client = get_client()
    if not client:
        return

    try:
        update_data = {
            'status': status,
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'result_count': result_data.get('total_jobs', 0),
            'quality_job_count': result_data.get('quality_jobs', 0)
        }

        if result_data.get('error'):
            update_data['error_message'] = result_data['error']

        client.table('async_job_queue').update(update_data).eq('id', job_id).execute()
        print(f"   💾 Updated job {job_id} status to '{status}'")

    except Exception as e:
        print(f"   ⚠️  Failed to update job {job_id}: {e}")


def main():
    """Main poller execution"""
    try:
        logger.info("="*80)
        logger.info("🔍 GOOGLE RESULTS POLLER")
        logger.info(f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info("="*80)
        sys.stdout.flush()

        # Get pending Google tasks
        pending_tasks = get_pending_google_tasks()

        if not pending_tasks:
            logger.info("📭 No pending Google tasks found")
            return

        logger.info(f"📋 Found {len(pending_tasks)} pending Google task(s)")
        sys.stdout.flush()

        processed_count = 0
        total_jobs_processed = 0
        all_dfs = []  # Collect DataFrames for notification

        for task in pending_tasks:
            job_id = task['id']
            task_id = task.get('request_id')
            search_params = task.get('search_params', {})
            csv_mapping = search_params.get('csv_mapping', 'google_query_to_market.csv')

            logger.info(f"\n🔍 Checking task {task_id} (Job ID: {job_id})")
            sys.stdout.flush()

            # Check if Outscraper task is complete
            results = check_outscraper_task(task_id)

            if not results:
                logger.info(f"   ⏳ Not ready yet, will check again later")
                sys.stdout.flush()
                continue

            logger.info(f"   ✅ Task complete! Processing results...")
            sys.stdout.flush()

            # Process results through pipeline
            result_data = process_google_results(task_id, results, csv_mapping)

            # CRITICAL: Fail loudly if zero jobs found
            if result_data['success'] and result_data['total_jobs'] == 0:
                error_msg = f"❌ ZERO JOBS FOUND - Batch completed but produced no results!"
                logger.error(error_msg)
                result_data['success'] = False
                result_data['error'] = error_msg
                update_job_status(job_id, 'failed', result_data)
                # Exit with error code so GitHub Actions shows this as a failure
                sys.exit(1)

            # Update job status
            if result_data['success']:
                total_jobs_processed += result_data['total_jobs']
                update_job_status(job_id, 'completed', result_data)
                processed_count += 1
                logger.info(f"   ✅ Success: {result_data['total_jobs']} jobs, {result_data['quality_jobs']} quality")
                # Collect DataFrame for notification
                if result_data.get('df') is not None and not result_data['df'].empty:
                    all_dfs.append(result_data['df'])
            else:
                logger.error(f"   ❌ Failed: {result_data.get('error', 'Unknown error')}")
                update_job_status(job_id, 'failed', result_data)

            sys.stdout.flush()

        logger.info("\n" + "="*80)
        logger.info(f"✅ Poller complete: {processed_count}/{len(pending_tasks)} tasks processed")
        logger.info(f"📊 Total jobs processed: {total_jobs_processed}")
        logger.info("="*80)
        sys.stdout.flush()

        # Send notification email if configured and we have results
        notification_email = os.getenv('NOTIFICATION_EMAIL')
        if notification_email and all_dfs:
            logger.info(f"\n📧 Sending scrape report to {notification_email}...")

            # Combine all DataFrames
            combined_df = pd.concat(all_dfs, ignore_index=True)

            # Collect detailed stats
            stats = collect_job_stats_from_dataframe(combined_df)

            # Add search configuration info
            stats['source_name'] = 'Google Jobs (Outscraper)'
            stats['markets_searched'] = ['Multi-market batch']
            stats['search_terms'] = ['CDL Driver jobs']

            # Send the report
            try:
                success = send_detailed_scrape_report("Google Jobs", stats, notification_email)
                if success:
                    logger.info(f"✅ Scrape report sent successfully")
                else:
                    logger.warning(f"⚠️  Failed to send scrape report (non-fatal)")
            except Exception as e:
                logger.warning(f"⚠️  Error sending scrape report: {e} (non-fatal)")
        elif notification_email:
            logger.info(f"ℹ️  No results to report - skipping notification")
        else:
            logger.info(f"ℹ️  NOTIFICATION_EMAIL not set, skipping scrape report")

    except Exception as e:
        logger.error(f"\n{'='*80}")
        logger.error(f"💥 FATAL ERROR IN POLLER")
        logger.error(f"{'='*80}")
        logger.error(f"Error: {str(e)}")
        logger.error(f"{'='*80}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()
