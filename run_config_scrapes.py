#!/usr/bin/env python3
"""
Simple Config-Based Scheduled Scraper
Reads scheduled_scrapes_config.json and runs all configured scrapes.

No database tracking, no UI complexity - just runs the scrapes and uploads to Supabase.
"""

import json
import sys
from datetime import datetime, timezone
from typing import Dict, List

def run_indeed_scrapes(scrapes: List[Dict]) -> Dict:
    """Run all Indeed scrapes from config"""
    from async_job_manager import AsyncJobManager

    manager = AsyncJobManager()
    results = []

    print(f"\n{'='*80}")
    print(f"📋 INDEED SCRAPES - {len(scrapes)} configured")
    print(f"{'='*80}\n")

    for i, scrape in enumerate(scrapes, 1):
        print(f"\n🔍 Indeed Scrape {i}/{len(scrapes)}: {scrape['search_terms']}")
        print(f"   Limit: {scrape['limit']} jobs")
        print(f"   No Experience Filter: {scrape.get('no_experience', True)}")

        try:
            # Build search params for all markets
            from market_mapper import MarketMapper

            market_mapper = MarketMapper()
            markets = market_mapper.get_all_markets()

            total_jobs = 0
            total_quality = 0

            # Run for each market
            for market_name in markets:
                # Get first city in market as location
                cities = market_mapper.get_cities_in_market(market_name)
                if not cities:
                    print(f"\n   ⚠️ Market {market_name}: No cities found, skipping")
                    continue
                location = cities[0]  # Use first city as representative location

                print(f"\n   📍 Market: {market_name} ({location})")

                search_params = {
                    'location': location,
                    'search_terms': scrape['search_terms'],
                    'search_radius': 50,
                    'limit': scrape['limit'],
                    'mode': 'sample',
                    'exact_location': False,
                    'no_experience': scrape.get('no_experience', True),
                    'classifier_type': 'CDL Job Classifier',
                    'frequency': 'Once'  # One-time execution
                }

                # Submit and run immediately
                job = manager.submit_indeed_search(search_params, 'scheduled_config')

                if job.status == 'completed':
                    total_jobs += job.result_count
                    total_quality += job.quality_job_count
                    print(f"      ✅ {job.result_count} jobs ({job.quality_job_count} quality)")
                else:
                    print(f"      ❌ Failed: {job.error_message}")

            results.append({
                'search_terms': scrape['search_terms'],
                'total_jobs': total_jobs,
                'quality_jobs': total_quality,
                'status': 'completed'
            })

            print(f"\n   📊 Total for '{scrape['search_terms']}': {total_jobs} jobs ({total_quality} quality)")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'search_terms': scrape['search_terms'],
                'error': str(e),
                'status': 'failed'
            })

    return {
        'source': 'indeed',
        'scrapes_run': len(scrapes),
        'results': results
    }


def run_driverpulse_scrapes(scrapes: List[Dict]) -> Dict:
    """Run all DriverPulse scrapes from config"""
    print(f"\n{'='*80}")
    print(f"🚛 DRIVERPULSE SCRAPES - {len(scrapes)} configured")
    print(f"{'='*80}\n")

    results = []

    for i, scrape in enumerate(scrapes, 1):
        print(f"\n🔍 DriverPulse Scrape {i}/{len(scrapes)}: {scrape['search_terms']}")
        print(f"   Filter Mode: {scrape.get('filter_mode', 'all_markets')}")

        try:
            from driver_pulse_adapter import DriverPulsePipelineIntegration

            integration = DriverPulsePipelineIntegration()

            filter_settings = {
                'filter_mode': scrape.get('filter_mode', 'all_markets'),
                'classifier_type': 'CDL Job Classifier'
            }

            result = integration.run_driver_pulse_through_pipeline(
                search_terms=scrape['search_terms'],
                filter_settings=filter_settings,
                coach_username='scheduled_config'
            )

            jobs_df = result.get('jobs_df')
            if jobs_df is not None and not jobs_df.empty:
                total_jobs = len(jobs_df)
                quality_jobs = len(jobs_df[jobs_df.get('ai.match', '').isin(['good', 'so-so'])]) if 'ai.match' in jobs_df.columns else 0

                print(f"   ✅ {total_jobs} jobs ({quality_jobs} quality)")

                results.append({
                    'search_terms': scrape['search_terms'],
                    'total_jobs': total_jobs,
                    'quality_jobs': quality_jobs,
                    'status': 'completed'
                })
            else:
                print(f"   ⚠️  No jobs found")
                results.append({
                    'search_terms': scrape['search_terms'],
                    'total_jobs': 0,
                    'quality_jobs': 0,
                    'status': 'completed'
                })

        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'search_terms': scrape['search_terms'],
                'error': str(e),
                'status': 'failed'
            })

    return {
        'source': 'driverpulse',
        'scrapes_run': len(scrapes),
        'results': results
    }


def run_google_scrapes(scrapes: List[Dict]) -> Dict:
    """Run all Google scrapes from config using Outscraper API"""
    import os
    import csv
    import requests
    from supabase_utils import get_client

    print(f"\n{'='*80}")
    print(f"🌐 GOOGLE SCRAPES - {len(scrapes)} configured")
    print(f"{'='*80}\n")

    results = []
    client = get_client()

    for i, scrape in enumerate(scrapes, 1):
        print(f"\n🔍 Google Scrape {i}/{len(scrapes)}")

        try:
            # Load query-to-market mapping
            csv_file = scrape.get('csv_mapping', 'google_query_to_market.csv')

            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                query_mapping = {row['Query']: row['Market'] for row in reader}

            queries = list(query_mapping.keys())
            print(f"   📋 Loaded {len(queries)} city queries from {csv_file}")
            print(f"   🎯 Mapped to {len(set(query_mapping.values()))} markets")

            # Call Outscraper Google Jobs API
            api_key = os.getenv('OUTSCRAPER_API_KEY')
            if not api_key:
                raise Exception("OUTSCRAPER_API_KEY not set")

            url = "https://api.outscraper.cloud/tasks"
            headers = {
                'X-API-KEY': api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                "settings": {"output_extension": "json"},
                "org": "os",
                "service_name": "google_search_jobs_service",
                "est": 10,
                "limit_per_query": scrape.get('limit_per_query', 50),
                "language": "en",
                "title": "",
                "queries": queries,
                "tags": "scheduledgoogle",
                "region": "US"
            }

            print(f"\n   🚀 Submitting {len(queries)} queries to Outscraper...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result_data = response.json()
            task_id = result_data.get('id')

            if task_id:
                print(f"   ✅ Task created: {task_id}")

                # Save to async_job_queue for poller to process
                if client:
                    job_record = {
                        'job_type': 'google_jobs',
                        'status': 'submitted',
                        'request_id': task_id,
                        'search_params': {
                            'csv_mapping': csv_file,
                            'limit_per_query': scrape.get('limit_per_query', 50),
                            'queries_count': len(queries),
                            'markets_count': len(set(query_mapping.values()))
                        },
                        'coach_username': 'scheduled_config',
                        'result_count': 0,
                        'quality_job_count': 0,
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }

                    db_result = client.table('async_job_queue').insert(job_record).execute()
                    job_id = db_result.data[0]['id'] if db_result.data else None
                    print(f"   💾 Saved to async_job_queue (ID: {job_id})")

                print(f"   ⏳ Poller will fetch results when ready")

                results.append({
                    'task_id': task_id,
                    'queries_count': len(queries),
                    'markets_count': len(set(query_mapping.values())),
                    'status': 'submitted'
                })
            else:
                raise Exception(f"No task ID in response: {result_data}")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'error': str(e),
                'status': 'failed'
            })

    return {
        'source': 'google',
        'scrapes_run': len(scrapes),
        'results': results
    }


def main():
    """Main execution - load config and run all scrapes"""
    print(f"\n{'='*80}")
    print(f"🤖 CONFIG-BASED SCHEDULED SCRAPER")
    print(f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*80}\n")

    # Load config (support custom config file for testing)
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'scheduled_scrapes_config.json'

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print(f"📄 Using config file: {config_file}")
    except FileNotFoundError:
        print(f"❌ Config file not found: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}")
        sys.exit(1)

    print(f"📋 Loaded config:")
    print(f"   Indeed scrapes: {len(config.get('indeed_scrapes', []))}")
    print(f"   DriverPulse scrapes: {len(config.get('driverpulse_scrapes', []))}")
    print(f"   Google scrapes: {len(config.get('google_scrapes', []))}")

    all_results = []

    # Run Indeed scrapes
    if config.get('indeed_scrapes'):
        indeed_results = run_indeed_scrapes(config['indeed_scrapes'])
        all_results.append(indeed_results)

    # Run DriverPulse scrapes
    if config.get('driverpulse_scrapes'):
        dp_results = run_driverpulse_scrapes(config['driverpulse_scrapes'])
        all_results.append(dp_results)

    # Run Google scrapes (async - submits to Outscraper)
    if config.get('google_scrapes'):
        google_results = run_google_scrapes(config['google_scrapes'])
        all_results.append(google_results)

    # Print summary
    print(f"\n{'='*80}")
    print(f"✅ SCRAPE RUN COMPLETE")
    print(f"{'='*80}")

    for result in all_results:
        print(f"\n{result['source'].upper()}:")
        print(f"   Scrapes run: {result['scrapes_run']}")

        for scrape_result in result.get('results', []):
            if result['source'] == 'google':
                # Google uses async submission
                if scrape_result['status'] == 'submitted':
                    print(f"   ✅ Task {scrape_result.get('task_id', 'unknown')}: {scrape_result.get('queries_count', 0)} queries ({scrape_result.get('markets_count', 0)} markets) - submitted to Outscraper")
                else:
                    print(f"   ❌ Failed: {scrape_result.get('error', 'Unknown error')}")
            else:
                # Indeed/DriverPulse use sync execution
                if scrape_result['status'] == 'completed':
                    print(f"   ✅ {scrape_result['search_terms']}: {scrape_result.get('total_jobs', 0)} jobs ({scrape_result.get('quality_jobs', 0)} quality)")
                else:
                    print(f"   ❌ {scrape_result['search_terms']}: {scrape_result.get('error', 'Unknown error')}")

    print(f"\n{'='*80}\n")

    # Send email notification if configured
    notification_email = os.getenv('NOTIFICATION_EMAIL')
    if notification_email:
        try:
            from send_scrape_notification import send_scrape_completion_notification

            # Calculate totals
            total_jobs = 0
            quality_jobs = 0
            total_scrapes = 0

            # Build detailed results by source
            indeed_summary = {}
            dp_summary = {}
            google_summary = {}

            for result in all_results:
                source = result['source']
                scrapes_run = result['scrapes_run']
                total_scrapes += scrapes_run

                if source == 'indeed':
                    ind_total = sum(sr.get('total_jobs', 0) for sr in result['results'] if sr['status'] == 'completed')
                    ind_quality = sum(sr.get('quality_jobs', 0) for sr in result['results'] if sr['status'] == 'completed')
                    total_jobs += ind_total
                    quality_jobs += ind_quality
                    indeed_summary = {
                        'total_jobs': ind_total,
                        'quality_jobs': ind_quality,
                        'scrapes_run': scrapes_run
                    }

                elif source == 'driverpulse':
                    dp_total = sum(sr.get('total_jobs', 0) for sr in result['results'] if sr['status'] == 'completed')
                    dp_quality = sum(sr.get('quality_jobs', 0) for sr in result['results'] if sr['status'] == 'completed')
                    total_jobs += dp_total
                    quality_jobs += dp_quality
                    dp_summary = {
                        'total_jobs': dp_total,
                        'quality_jobs': dp_quality,
                        'scrapes_run': scrapes_run
                    }

                elif source == 'google':
                    queries_submitted = sum(sr.get('queries_count', 0) for sr in result['results'] if sr['status'] == 'submitted')
                    google_summary = {
                        'queries_submitted': queries_submitted,
                        'scrapes_run': scrapes_run
                    }

            # Build notification data
            notification_data = {
                'total_jobs': total_jobs,
                'quality_jobs': quality_jobs,
                'scrapes_run': total_scrapes,
                'indeed_results': indeed_summary if indeed_summary else None,
                'driverpulse_results': dp_summary if dp_summary else None,
                'google_results': google_summary if google_summary else None
            }

            # Send notification
            print(f"\n📧 Sending completion notification to {notification_email}...")
            send_scrape_completion_notification("Scheduled", notification_data, notification_email)

        except Exception as e:
            print(f"⚠️  Failed to send email notification: {e}")
            import traceback
            traceback.print_exc()

    return all_results


if __name__ == "__main__":
    import os

    results = main()

    # Exit with error code if any scrapes failed
    failed_count = sum(1 for r in results for sr in r.get('results', []) if sr['status'] == 'failed')
    sys.exit(1 if failed_count > 0 else 0)
