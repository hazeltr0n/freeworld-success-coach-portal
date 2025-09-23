#!/usr/bin/env python3
"""
Polling-based job monitor to replace broken Outscraper webhooks
"""

import os
import time
import toml
import requests
from supabase import create_client
from datetime import datetime

def load_secrets():
    """Load environment variables from secrets"""
    try:
        with open('.streamlit/secrets.toml', 'r') as f:
            secrets = toml.load(f)

        if 'secrets' in secrets:
            for key, value in secrets['secrets'].items():
                os.environ[key] = str(value)
        return True
    except Exception as e:
        print(f"❌ Error loading secrets: {e}")
        return False

def poll_outscraper_jobs():
    """Poll Outscraper for completed jobs and update our database"""

    # Setup
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE')
    )

    api_key = os.getenv('OUTSCRAPER_API_KEY')

    # Get all submitted jobs from our database
    try:
        result = supabase.table('async_job_queue')\
            .select('*')\
            .eq('status', 'submitted')\
            .execute()

        pending_jobs = result.data or []

        if not pending_jobs:
            print("✅ No pending jobs to check")
            return

        print(f"🔍 Checking {len(pending_jobs)} pending jobs...")

        for job in pending_jobs:
            request_id = job.get('request_id')
            if not request_id:
                continue

            # Check status with Outscraper
            try:
                response = requests.get(
                    f'https://api.outscraper.cloud/requests/{request_id}',
                    headers={'X-API-KEY': api_key},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    outscraper_status = data.get('status', 'Unknown')

                    if outscraper_status == 'Success':
                        # Job completed! Update our database
                        print(f"🎉 Job {job['id']} completed on Outscraper")

                        # Count results
                        results = data.get('data', [])
                        result_count = len(results)

                        # Update job status
                        update_result = supabase.table('async_job_queue')\
                            .update({
                                'status': 'completed',
                                'completed_at': datetime.now().isoformat(),
                                'result_count': result_count,
                                'quality_job_count': 0  # Will be updated when results are processed
                            })\
                            .eq('id', job['id'])\
                            .execute()

                        if update_result.data:
                            print(f"✅ Updated job {job['id']} status to completed")

                        # Create notification if coach exists
                        if job.get('coach_username'):
                            try:
                                supabase.table('coach_notifications')\
                                    .insert({
                                        'coach_username': job['coach_username'],
                                        'message': f"✅ Google Jobs search completed! Found {result_count} results for {job.get('search_params', {}).get('location', 'your search')}.",
                                        'notification_type': 'search_complete',
                                        'job_id': job['id'],
                                        'created_at': datetime.now().isoformat()
                                    })\
                                    .execute()
                                print(f"📬 Notification sent to {job['coach_username']}")
                            except Exception as e:
                                print(f"⚠️ Failed to create notification: {e}")

                    elif outscraper_status in ['Failed', 'Error']:
                        # Job failed
                        print(f"❌ Job {job['id']} failed on Outscraper")

                        supabase.table('async_job_queue')\
                            .update({
                                'status': 'failed',
                                'completed_at': datetime.now().isoformat(),
                                'error_message': f'Outscraper job failed with status: {outscraper_status}'
                            })\
                            .eq('id', job['id'])\
                            .execute()

                    else:
                        print(f"⏳ Job {job['id']} still processing: {outscraper_status}")

                else:
                    print(f"⚠️ Error checking job {job['id']}: HTTP {response.status_code}")

            except Exception as e:
                print(f"❌ Error checking job {job['id']}: {e}")

            # Small delay between requests
            time.sleep(1)

    except Exception as e:
        print(f"❌ Error polling jobs: {e}")

def main():
    """Main polling loop"""
    print("🔄 Outscraper Job Polling Monitor Started")
    print("=" * 50)
    print("This replaces broken Outscraper webhooks with reliable polling")
    print()

    if not load_secrets():
        return

    # Poll every 2 minutes
    while True:
        current_time = datetime.now().strftime('%H:%M:%S')
        print(f"[{current_time}] 🔄 Polling for completed jobs...")

        try:
            poll_outscraper_jobs()
        except Exception as e:
            print(f"❌ Polling error: {e}")

        print("⏳ Waiting 2 minutes for next poll...\n")
        time.sleep(120)  # 2 minutes

if __name__ == '__main__':
    main()