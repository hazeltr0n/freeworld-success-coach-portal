#!/usr/bin/env python3
"""
Background processor for async Google Jobs
Should be run periodically (e.g., every 2-3 minutes) to check for completed jobs
"""

import os
import toml
import time
from datetime import datetime, timezone, timedelta
from async_job_manager import AsyncJobManager

def load_secrets():
    """Load Streamlit secrets and set as environment variables"""
    try:
        secrets_path = ".streamlit/secrets.toml"
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            for key, value in secrets.items():
                os.environ[key] = str(value)
            return True
        return False
    except Exception as e:
        print(f"❌ Error loading secrets: {e}")
        return False

def process_pending_jobs():
    """Check all pending jobs and process any that have completed"""
    print(f"🔄 Background Job Processor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if not load_secrets():
        return False
    
    try:
        manager = AsyncJobManager()
        
        # Get all pending jobs
        pending_jobs = manager.get_pending_jobs()
        
        if not pending_jobs:
            print("📋 No pending jobs to process")
            return True
            
        print(f"Found {len(pending_jobs)} pending jobs to check")
        processed_count = 0
        
        for job in pending_jobs:
            if not job.request_id:
                print(f"⚠️  Job {job.id} has no request_id - skipping")
                continue
                
            # Skip very recent jobs (give them at least 2 minutes)
            if job.submitted_at:
                elapsed = datetime.now(timezone.utc) - job.submitted_at
                if elapsed.total_seconds() < 120:  # 2 minutes
                    print(f"⏳ Job {job.id} is recent ({elapsed.total_seconds():.0f}s) - waiting")
                    continue
            
            print(f"🔍 Checking job {job.id} (request: {job.request_id})")
            
            try:
                # Check if Outscraper has results ready
                result = manager.get_async_results(job.request_id)
                
                if result:
                    print(f"✅ Results available for job {job.id} - processing...")
                    manager.process_completed_google_job(job.id)
                    processed_count += 1
                    print(f"🎉 Job {job.id} processed successfully!")
                    
                    # Add a small delay between processing jobs
                    time.sleep(1)
                    
                else:
                    print(f"⏳ Job {job.id} still processing...")
                    
                    # Check if job is taking too long (> 10 minutes)
                    if job.submitted_at:
                        elapsed = datetime.now(timezone.utc) - job.submitted_at
                        if elapsed.total_seconds() > 600:  # 10 minutes
                            print(f"🚨 Job {job.id} has been running for {elapsed.total_seconds()/60:.1f} minutes")
                    
            except Exception as e:
                print(f"❌ Error processing job {job.id}: {e}")
        
        print(f"\n📊 Summary: Processed {processed_count} completed jobs")
        return True
        
    except Exception as e:
        print(f"❌ Error in background processor: {e}")
        return False

def cleanup_old_jobs():
    """Clean up very old pending jobs that might be stuck"""
    try:
        manager = AsyncJobManager()
        pending_jobs = manager.get_pending_jobs()
        current_time = datetime.now(timezone.utc)
        
        for job in pending_jobs:
            if job.submitted_at:
                elapsed = current_time - job.submitted_at
                # If a job has been pending for more than 1 hour, mark it as failed
                if elapsed.total_seconds() > 3600:  # 1 hour
                    print(f"🧹 Cleaning up old job {job.id} (running {elapsed.total_seconds()/3600:.1f} hours)")
                    
                    manager.update_job(job.id, {
                        'status': 'failed',
                        'completed_at': current_time.isoformat(),
                        'error_message': f'Job timed out after {elapsed.total_seconds()/3600:.1f} hours'
                    })
                    
                    manager.notify_coach(
                        job.coach_username,
                        f"❌ Google Jobs search timed out after {elapsed.total_seconds()/3600:.1f} hours. Please try again.",
                        'error',
                        job.id
                    )
                    
    except Exception as e:
        print(f"Warning: Error during cleanup: {e}")

if __name__ == "__main__":
    print("🤖 Async Job Background Processor")
    print("Run this script periodically (every 2-3 minutes) to process completed jobs")
    print()
    
    success = process_pending_jobs()
    
    if success:
        cleanup_old_jobs()
        print(f"\n✅ Background processing completed!")
    else:
        print(f"\n❌ Background processing failed!")
    
    print(f"\n💡 To run automatically, add this to a cron job:")
    print(f"   */3 * * * * cd /path/to/project && python background_job_processor.py")