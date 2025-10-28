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
from datetime import datetime, timezone
from typing import Dict, List, Optional

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
        download_url = f"https://api.outscraper.cloud/requests/{task_id}?format=json"

        download_response = requests.get(download_url, headers=headers, timeout=60)
        download_response.raise_for_status()

        # Parse the downloaded JSON data
        downloaded_data = download_response.json()

        # Outscraper returns data in 'data' field of the response
        if 'data' in downloaded_data and downloaded_data['data']:
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

        # Link tracking
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
            'uploaded_count': uploaded_count
        }

    except Exception as e:
        print(f"   ❌ Error processing results: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'total_jobs': 0,
            'quality_jobs': 0,
            'error': str(e)
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
    print(f"\n{'='*80}")
    print(f"🔍 GOOGLE RESULTS POLLER")
    print(f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*80}\n")

    # Get pending Google tasks
    pending_tasks = get_pending_google_tasks()

    if not pending_tasks:
        print("📭 No pending Google tasks found")
        return

    print(f"📋 Found {len(pending_tasks)} pending Google task(s)\n")

    processed_count = 0

    for task in pending_tasks:
        job_id = task['id']
        task_id = task.get('request_id')
        search_params = task.get('search_params', {})
        csv_mapping = search_params.get('csv_mapping', 'google_query_to_market.csv')

        print(f"🔍 Checking task {task_id} (Job ID: {job_id})")

        # Check if Outscraper task is complete
        results = check_outscraper_task(task_id)

        if not results:
            print(f"   ⏳ Not ready yet, will check again later\n")
            continue

        print(f"   ✅ Task complete! Processing results...")

        # Process results through pipeline
        result_data = process_google_results(task_id, results, csv_mapping)

        # Update job status
        if result_data['success']:
            update_job_status(job_id, 'completed', result_data)
            processed_count += 1
        else:
            update_job_status(job_id, 'failed', result_data)

        print()

    print(f"{'='*80}")
    print(f"✅ Poller complete: {processed_count}/{len(pending_tasks)} tasks processed")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
