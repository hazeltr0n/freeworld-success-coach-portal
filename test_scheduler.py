#!/usr/bin/env python3
"""
Test Script for Background Job Scheduler
========================================

This script tests the end-to-end scheduled job functionality.
"""

import os
import sys
import time
from datetime import datetime, timezone, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from async_job_manager import AsyncJobManager
from supabase_utils import get_client

def test_create_scheduled_job():
    """Test creating a scheduled job"""
    print("🧪 Testing scheduled job creation...")

    manager = AsyncJobManager()

    # Create a test scheduled job for 2 minutes from now
    test_params = {
        'location': 'Austin, TX',
        'search_terms': 'CDL driver test',
        'limit': 10,
        'job_type': 'indeed_jobs',
        'frequency': 'once',
        'time': '02:00',
        'days': []
    }

    try:
        job = manager.create_scheduled_job(test_params, 'test_coach')
        print(f"✅ Created scheduled job: {job.id}")
        print(f"   Status: {job.status}")
        print(f"   Coach: {job.coach_username}")
        print(f"   Location: {job.search_params['location']}")
        return job.id
    except Exception as e:
        print(f"❌ Failed to create scheduled job: {e}")
        return None

def check_job_status(job_id):
    """Check the status of a specific job"""
    manager = AsyncJobManager()

    try:
        job = manager.check_job_status(job_id)
        if job:
            print(f"📋 Job {job_id} status: {job.status}")
            if job.error_message:
                print(f"   Error: {job.error_message}")
            return job.status
        else:
            print(f"❌ Job {job_id} not found")
            return None
    except Exception as e:
        print(f"❌ Error checking job status: {e}")
        return None

def test_scheduler_detection():
    """Test that the scheduler can detect ready jobs"""
    from background_job_scheduler import BackgroundJobScheduler

    print("🔍 Testing scheduler job detection...")

    try:
        scheduler = BackgroundJobScheduler()
        ready_jobs = scheduler.get_ready_scheduled_jobs()

        print(f"📋 Found {len(ready_jobs)} ready scheduled jobs")
        for job in ready_jobs:
            print(f"   Job {job.id}: {job.job_type} for {job.coach_username}")

        return len(ready_jobs)
    except Exception as e:
        print(f"❌ Error testing scheduler detection: {e}")
        return 0

def test_database_connection():
    """Test basic database connectivity"""
    print("🔌 Testing database connection...")

    try:
        client = get_client()
        if not client:
            print("❌ Supabase client not available")
            return False

        # Try a simple query
        result = client.table('async_job_queue').select('id').limit(1).execute()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 FreeWorld Scheduler Test Suite")
    print("=" * 50)

    # Test 1: Database connection
    if not test_database_connection():
        print("❌ Database connection failed - stopping tests")
        return

    print()

    # Test 2: Scheduler detection
    initial_jobs = test_scheduler_detection()
    print()

    # Test 3: Create scheduled job
    job_id = test_create_scheduled_job()
    if not job_id:
        print("❌ Job creation failed - stopping tests")
        return

    print()

    # Test 4: Verify scheduler can detect the new job
    print("🔍 Checking if scheduler detects new job...")
    time.sleep(1)  # Brief pause
    new_jobs = test_scheduler_detection()

    if new_jobs > initial_jobs:
        print("✅ Scheduler successfully detected new scheduled job!")
    else:
        print("⚠️ Scheduler may not be detecting new jobs properly")

    print()

    # Test 5: Instructions for manual testing
    print("📋 Manual Testing Instructions:")
    print("=" * 30)
    print("1. Run the background scheduler:")
    print("   python background_job_scheduler.py")
    print()
    print("2. In another terminal, check the job status:")
    print(f"   Job ID: {job_id}")
    print()
    print("3. The job should process automatically when ready")
    print("   (Check the scheduler logs for processing activity)")
    print()
    print("4. Verify the job completes:")
    print("   - Status changes to 'completed'")
    print("   - Results appear in Supabase")
    print("   - Coach notification sent")

if __name__ == "__main__":
    main()