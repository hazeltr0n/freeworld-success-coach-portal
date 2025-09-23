#!/usr/bin/env python3
"""
Monitor both test jobs to see if Outscraper calls our webhook
"""

import os
import time
import toml
from supabase import create_client
from datetime import datetime

# Load environment variables from secrets
try:
    with open('.streamlit/secrets.toml', 'r') as f:
        secrets = toml.load(f)

    if 'secrets' in secrets:
        for key, value in secrets['secrets'].items():
            os.environ[key] = str(value)
except Exception as e:
    print(f"❌ Error loading secrets: {e}")

def check_jobs():
    """Check both test jobs"""
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE')
    )

    jobs_to_check = [
        {'id': 41, 'desc': 'With token parameter', 'request_id': 'a-4eac0762-59c3-470f-92e8-4dc7db99e75c'},
        {'id': 42, 'desc': 'Without token parameter', 'request_id': 'a-671ee66f-9ca1-4111-9d28-c27ff1847035'}
    ]

    print(f"📊 Status Check - {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 60)

    for job_info in jobs_to_check:
        try:
            result = supabase.table('async_job_queue').select('*').eq('id', job_info['id']).execute()

            if result.data:
                job = result.data[0]
                status = job['status']
                completed_at = job.get('completed_at')
                created_at = job['created_at']

                print(f"Job {job_info['id']} ({job_info['desc']}):")
                print(f"  Status: {status}")
                print(f"  Request: {job_info['request_id']}")
                print(f"  Created: {created_at}")
                if completed_at:
                    print(f"  Completed: {completed_at}")
                    print(f"  🎯 WEBHOOK WAS CALLED!")
                else:
                    print(f"  Completed: Still waiting...")
                print()

        except Exception as e:
            print(f"❌ Error checking job {job_info['id']}: {e}")

def main():
    print("🔍 Monitoring Both Test Jobs for Outscraper Webhook Calls")
    print("=" * 70)
    print("Job 41: Uses webhook WITH token parameter")
    print("Job 42: Uses webhook WITHOUT token parameter")
    print("=" * 70)

    # Check every 30 seconds
    while True:
        check_jobs()
        print("⏳ Waiting 30 seconds for next check...\n")
        time.sleep(30)

if __name__ == '__main__':
    main()