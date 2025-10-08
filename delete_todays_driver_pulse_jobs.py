#!/usr/bin/env python3
"""
Delete all DriverPulse jobs uploaded today from Supabase
"""

from datetime import datetime, timezone
from supabase_utils import get_client

def delete_todays_driver_pulse_jobs():
    """Delete all jobs from driver_pulse source uploaded today"""

    client = get_client()
    if not client:
        print("❌ Supabase client not available")
        return

    # Get today's date in ISO format
    today = datetime.now(timezone.utc).date().isoformat()

    print(f"🗑️ Deleting all DriverPulse jobs created today ({today})...")

    try:
        # Query for jobs from driver_pulse source created today
        result = client.table('jobs').select('job_id').eq('source', 'driver_pulse').gte('created_at', today).execute()

        job_ids = [row['job_id'] for row in result.data]
        print(f"   Found {len(job_ids)} DriverPulse jobs to delete")

        if not job_ids:
            print("✅ No DriverPulse jobs to delete")
            return

        # Delete in batches of 100
        batch_size = 100
        total_deleted = 0

        for i in range(0, len(job_ids), batch_size):
            batch = job_ids[i:i + batch_size]
            delete_result = client.table('jobs').delete().in_('job_id', batch).execute()
            total_deleted += len(batch)
            print(f"   Deleted batch {i//batch_size + 1}: {len(batch)} jobs")

        print(f"✅ Deleted {total_deleted} DriverPulse jobs from today")

    except Exception as e:
        print(f"❌ Error deleting jobs: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    delete_todays_driver_pulse_jobs()
