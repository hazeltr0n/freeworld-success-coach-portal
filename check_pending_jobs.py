#!/usr/bin/env python3
"""
Check status of pending async jobs
"""

import os
import toml
from datetime import datetime, timezone
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
        else:
            print("❌ Secrets file not found")
            return False
    except Exception as e:
        print(f"❌ Error loading secrets: {e}")
        return False

def check_all_pending_jobs():
    """Check all pending jobs and their status"""
    print("🔍 Checking All Pending Async Jobs")
    print("=" * 60)
    
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
    
    # Get all pending jobs
    try:
        pending_jobs = manager.get_pending_jobs()  # Get all, not filtered by user
        
        if not pending_jobs:
            print("📋 No pending jobs found")
            return True
            
        print(f"Found {len(pending_jobs)} pending jobs:")
        print()
        
        current_time = datetime.now(timezone.utc)
        
        for i, job in enumerate(pending_jobs, 1):
            print(f"--- Job {i} ---")
            print(f"ID: {job.id}")
            print(f"Coach: {job.coach_username}")
            print(f"Type: {job.job_type}")
            print(f"Status: {job.status}")
            print(f"Request ID: {job.request_id}")
            
            # Search parameters
            search_params = job.search_params or {}
            print(f"Search Terms: {search_params.get('search_terms', 'Unknown')}")
            print(f"Location: {search_params.get('location', 'Unknown')}")
            print(f"Limit: {search_params.get('limit', 'Unknown')}")
            
            # Time analysis
            if job.submitted_at:
                elapsed = current_time - job.submitted_at
                total_minutes = elapsed.total_seconds() / 60
                hours = int(total_minutes // 60)
                minutes = int(total_minutes % 60)
                
                print(f"Submitted: {job.submitted_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print(f"Running Time: {hours}h {minutes}m")
                
                # Flag long-running jobs
                if total_minutes > 10:
                    print(f"🚨 LONG RUNNING: {total_minutes:.1f} minutes (normal: 2-3 minutes)")
                elif total_minutes > 5:
                    print(f"⚠️ SLOW: {total_minutes:.1f} minutes")
                else:
                    print(f"✅ Normal: {total_minutes:.1f} minutes")
            else:
                print("Submitted: Unknown")
            
            print(f"Created: {job.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking pending jobs: {e}")
        return False

def check_outscraper_status():
    """Check the status directly with Outscraper API"""
    print("\n🌐 Checking Outscraper API Status")
    print("=" * 40)
    
    try:
        manager = AsyncJobManager()
        pending_jobs = manager.get_pending_jobs()
        
        for job in pending_jobs:
            if job.request_id:
                print(f"\nChecking Outscraper status for request: {job.request_id}")
                try:
                    result = manager.get_async_results(job.request_id)
                    if result:
                        print(f"✅ Outscraper has results ready for job {job.id}")
                        print(f"Result type: {type(result)}")
                        if isinstance(result, list):
                            print(f"Result count: {len(result)} items")
                    else:
                        print(f"⏳ Outscraper still processing request {job.request_id}")
                except Exception as e:
                    print(f"❌ Error checking Outscraper for {job.request_id}: {e}")
    except Exception as e:
        print(f"❌ Error checking Outscraper status: {e}")

if __name__ == "__main__":
    print("🧪 Async Job Status Checker")
    print("=" * 60)
    
    success = check_all_pending_jobs()
    if success:
        check_outscraper_status()
        print("\n🎉 Status check completed!")
    else:
        print("\n💥 Status check failed")