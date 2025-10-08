#!/usr/bin/env python3
"""
Test script to verify scheduled batch execution works end-to-end.
This simulates what would happen on Streamlit Cloud when batches are due.
"""

import sys
sys.path.insert(0, '.')

from async_job_manager import AsyncJobManager
from datetime import datetime, timezone

def check_and_execute_submitted_batches():
    """Check for batches marked as 'submitted' and execute them"""
    print(f"\n{'='*60}")
    print(f"🔍 Checking for submitted batches...")
    print(f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*60}\n")

    manager = AsyncJobManager()

    # Get all jobs with status='submitted' (marked as ready to run by Edge Function)
    result = manager.supabase_client.table('async_job_queue').select('*').eq('status', 'submitted').execute()

    submitted_jobs = result.data if result.data else []

    if not submitted_jobs:
        print("📭 No submitted batches found")
        return

    print(f"📋 Found {len(submitted_jobs)} submitted batch(es) ready to execute\n")

    for job_data in submitted_jobs:
        job_id = job_data['id']
        job_type = job_data['job_type']
        coach = job_data['coach_username']

        print(f"🚀 Executing batch {job_id}...")
        print(f"   Type: {job_type}")
        print(f"   Coach: {coach}")

        try:
            # Execute based on job type
            if job_type == 'driver_pulse':
                print("   Source: DriverPulse")
                manager.submit_driver_pulse_search(job_data['search_params'], coach)

            elif job_type == 'google_jobs':
                print("   Source: Google Jobs")
                manager.submit_google_search(job_data['search_params'], coach)

            elif job_type == 'indeed_jobs':
                print("   Source: Indeed")
                manager.submit_indeed_search(job_data['search_params'], coach)

            print(f"✅ Batch {job_id} executed successfully\n")

        except Exception as e:
            print(f"❌ Error executing batch {job_id}: {e}\n")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    check_and_execute_submitted_batches()
    print(f"{'='*60}")
    print("✅ Check complete")
    print(f"{'='*60}\n")
