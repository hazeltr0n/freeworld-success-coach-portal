#!/usr/bin/env python3
"""
Manually process stuck async jobs that have results available
"""

import os
import toml
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

def process_stuck_jobs():
    """Process jobs that are stuck but have results available"""
    print("🔧 Processing Stuck Async Jobs")
    print("=" * 50)
    
    if not load_secrets():
        return False
    
    try:
        manager = AsyncJobManager()
        pending_jobs = manager.get_pending_jobs()
        
        for job in pending_jobs:
            if job.request_id:
                print(f"\n📋 Processing Job {job.id}")
                print(f"   Coach: {job.coach_username}")
                print(f"   Request: {job.request_id}")
                print(f"   Location: {job.search_params.get('location', 'Unknown')}")
                
                try:
                    # Check if results are available
                    result = manager.get_async_results(job.request_id)
                    if result:
                        print(f"   ✅ Results available - processing...")
                        
                        # Process the completed job
                        manager.process_completed_google_job(job.id)
                        print(f"   🎉 Job {job.id} processed successfully!")
                        
                    else:
                        print(f"   ⏳ No results available yet")
                        
                except Exception as e:
                    print(f"   ❌ Error processing job {job.id}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = process_stuck_jobs()
    if success:
        print(f"\n🎉 Processing completed!")
        
        # Check status again
        print(f"\n📊 Checking status after processing...")
        os.system("python check_pending_jobs.py")
    else:
        print(f"\n💥 Processing failed")