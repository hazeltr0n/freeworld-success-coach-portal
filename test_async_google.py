#!/usr/bin/env python3
"""
Test script for async Google Jobs search with minimal parameters
"""

import os
import time
import sys
import toml
from datetime import datetime
from async_job_manager import AsyncJobManager

def load_secrets():
    """Load Streamlit secrets and set as environment variables"""
    try:
        secrets_path = ".streamlit/secrets.toml"
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            for key, value in secrets.items():
                os.environ[key] = str(value)
            print("✅ Secrets loaded successfully")
            return True
        else:
            print("❌ Secrets file not found")
            return False
    except Exception as e:
        print(f"❌ Error loading secrets: {e}")
        return False

def test_minimal_google_search():
    """Test async Google search with minimal parameters"""
    print("🧪 Testing Async Google Jobs Search")
    print("=" * 50)
    
    # Load secrets first
    if not load_secrets():
        return False
    
    # Initialize async job manager
    try:
        manager = AsyncJobManager()
        print("✅ AsyncJobManager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize AsyncJobManager: {e}")
        return False
    
    # Define minimal search parameters
    search_params = {
        'search_terms': 'CDL Driver',
        'location': 'Dallas, TX', 
        'limit': 20,  # Very small batch - should return ~1 page of results
        'coach_username': 'test_user'
    }
    
    print(f"\n📋 Search Parameters:")
    print(f"   Terms: {search_params['search_terms']}")
    print(f"   Location: {search_params['location']}")
    print(f"   Limit: {search_params['limit']}")
    
    # Submit the search
    try:
        print(f"\n🚀 Submitting async Google Jobs search...")
        job = manager.submit_google_search(search_params, 'test_user')
        
        print(f"✅ Search submitted successfully!")
        print(f"   Job ID: {job.id}")
        print(f"   Status: {job.status}")
        print(f"   Request ID: {job.request_id}")
        print(f"   Submitted at: {job.submitted_at}")
        
    except Exception as e:
        print(f"❌ Failed to submit search: {e}")
        return False
    
    # Monitor the job status
    print(f"\n👀 Monitoring job status (will check for 5 minutes)...")
    start_time = time.time()
    max_wait_time = 300  # 5 minutes
    
    while time.time() - start_time < max_wait_time:
        try:
            # Get current job status
            current_jobs = manager.get_pending_jobs('test_user')
            current_job = None
            for pending_job in current_jobs:
                if pending_job.id == job.id:
                    current_job = pending_job
                    break
            
            if current_job:
                print(f"   Status: {current_job.status} | Elapsed: {int(time.time() - start_time)}s")
                
                if current_job.status == 'completed':
                    print(f"✅ Job completed successfully!")
                    print(f"   Total results: {current_job.result_count}")
                    print(f"   Quality jobs: {current_job.quality_job_count}")
                    print(f"   Completed at: {current_job.completed_at}")
                    
                    # Try to get the processed results
                    try:
                        completed_jobs = manager.get_completed_jobs('test_user', limit=1)
                        if completed_jobs and completed_jobs[0].id == job.id:
                            print(f"\n📊 Job found in completed jobs list")
                        
                        # Check notifications
                        notifications = manager.get_coach_notifications('test_user', unread_only=True)
                        print(f"📬 Unread notifications: {len(notifications)}")
                        for notif in notifications[:3]:  # Show first 3
                            print(f"   • {notif.message}")
                            
                    except Exception as e:
                        print(f"⚠️  Could not retrieve completed job details: {e}")
                    
                    return True
                    
                elif current_job.status == 'failed':
                    print(f"❌ Job failed!")
                    print(f"   Error: {current_job.error_message}")
                    return False
                    
            else:
                print(f"⚠️  Job not found in pending jobs")
                
            # Wait before next check
            time.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            print(f"❌ Error checking job status: {e}")
            time.sleep(10)
            continue
    
    print(f"⏰ Timeout reached ({max_wait_time}s) - job may still be processing")
    return False

if __name__ == "__main__":
    success = test_minimal_google_search()
    if success:
        print(f"\n🎉 Test completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 Test failed or timed out")
        sys.exit(1)