#!/usr/bin/env python3
"""
Scheduled Batch Runner - Executes due batches automatically
Can be triggered by:
1. Supabase Edge Function + pg_cron (production)
2. Cron job directly (backup)
3. Manual execution for testing
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from typing import List, Dict

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_scheduled_batches():
    """Check for and execute any batches that are due to run"""
    from async_job_manager import AsyncJobManager
    from job_memory_db import JobMemoryDB

    print(f"\n{'='*60}")
    print(f"🔄 Scheduled Batch Runner")
    print(f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*60}\n")

    manager = AsyncJobManager()
    memory_db = JobMemoryDB()

    # Get all scheduled jobs
    scheduled_jobs = manager.get_scheduled_jobs()

    if not scheduled_jobs:
        print("📭 No scheduled batches found")
        return {'executed': 0, 'skipped': 0}

    print(f"📋 Found {len(scheduled_jobs)} scheduled batch(es)")

    now = datetime.now(timezone.utc)
    executed_count = 0
    skipped_count = 0

    for job in scheduled_jobs:
        try:
            # Parse scheduled_run_at
            scheduled_run_at = None
            if hasattr(job, 'search_params') and isinstance(job.search_params, dict):
                scheduled_run_at_str = job.search_params.get('scheduled_run_at')
                if scheduled_run_at_str:
                    try:
                        scheduled_run_at = datetime.fromisoformat(scheduled_run_at_str.replace('Z', '+00:00'))
                    except:
                        pass

            # If we couldn't get scheduled_run_at from search_params, skip
            if not scheduled_run_at:
                print(f"⚠️  Batch {job.id}: No scheduled_run_at found, skipping")
                skipped_count += 1
                continue

            # Check if it's time to run
            time_until_run = (scheduled_run_at - now).total_seconds()

            if time_until_run > 0:
                # Not due yet
                hours_until = time_until_run / 3600
                print(f"⏳ Batch {job.id}: Not due yet (runs in {hours_until:.1f} hours)")
                skipped_count += 1
                continue

            # It's time to run!
            print(f"\n🚀 Executing batch {job.id}...")
            print(f"   Coach: {job.coach_username}")
            print(f"   Type: {job.job_type}")
            print(f"   Scheduled: {scheduled_run_at.strftime('%Y-%m-%d %H:%M UTC')}")

            # Execute based on job type
            if job.job_type == 'driver_pulse_jobs' or job.job_type == 'driver_pulse':
                # Execute DriverPulse batch
                result = manager.submit_driver_pulse_search(
                    job.search_params,
                    job.coach_username
                )
                print(f"✅ DriverPulse batch {job.id} executed successfully")

            elif job.job_type == 'google_jobs':
                # Execute Google Jobs batch
                result = manager.submit_google_search(
                    job.search_params,
                    job.coach_username
                )
                print(f"✅ Google Jobs batch {job.id} executed successfully")

            elif job.job_type == 'indeed_jobs':
                # Execute Indeed batch (if you have this method)
                # For now, just log it
                print(f"⚠️  Indeed batch {job.id}: Execution not yet implemented")
                skipped_count += 1
                continue

            else:
                print(f"⚠️  Batch {job.id}: Unknown job type '{job.job_type}'")
                skipped_count += 1
                continue

            executed_count += 1

            # Handle recurring batches - create next run
            frequency = job.search_params.get('frequency', 'Once')
            if frequency != 'Once':
                print(f"🔄 Recurring batch - scheduling next run...")

                # Calculate next run time
                if frequency.lower() == 'daily':
                    next_run = scheduled_run_at + timedelta(days=1)
                elif frequency.lower() == 'weekly':
                    next_run = scheduled_run_at + timedelta(weeks=1)
                else:
                    next_run = scheduled_run_at + timedelta(days=1)

                # Create new scheduled job for next run
                new_params = job.search_params.copy()
                new_params['scheduled_run_at'] = next_run.isoformat()

                try:
                    new_job = manager.create_scheduled_job(new_params, job.coach_username)
                    print(f"📅 Next run scheduled: {next_run.strftime('%Y-%m-%d %H:%M UTC')} (Job #{new_job.id})")
                except Exception as e:
                    print(f"❌ Failed to schedule next run: {e}")

        except Exception as e:
            print(f"❌ Error executing batch {job.id}: {e}")
            import traceback
            traceback.print_exc()
            skipped_count += 1

    print(f"\n{'='*60}")
    print(f"✅ Executed: {executed_count}")
    print(f"⏭️  Skipped: {skipped_count}")
    print(f"{'='*60}\n")

    return {
        'executed': executed_count,
        'skipped': skipped_count,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    result = run_scheduled_batches()
    print(f"\n🎯 Final result: {result}")
