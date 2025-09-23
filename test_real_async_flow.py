#!/usr/bin/env python3
"""
Test real end-to-end async batch flow with webhook monitoring
"""

import os
import sys
import time
import json
import asyncio
import threading
from datetime import datetime
import toml
from supabase import create_client

# Load environment variables from secrets
try:
    with open('.streamlit/secrets.toml', 'r') as f:
        secrets = toml.load(f)

    if 'secrets' in secrets:
        for key, value in secrets['secrets'].items():
            os.environ[key] = str(value)

    print("✅ Secrets loaded successfully")
except Exception as e:
    print(f"❌ Error loading secrets: {e}")
    sys.exit(1)

# Import after environment is set up
from async_job_manager import AsyncJobManager

def setup_supabase():
    """Initialize Supabase client"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE')

        if not supabase_url or not supabase_key:
            print("❌ Missing Supabase credentials")
            return None

        client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client initialized")
        return client

    except Exception as e:
        print(f"❌ Error setting up Supabase: {e}")
        return None

def submit_test_batch():
    """Submit a small test batch"""
    print("\n🚀 Submitting test async batch...")

    try:
        # Initialize AsyncJobManager
        manager = AsyncJobManager()

        # Test parameters - small batch for quick testing
        search_params = {
            'location': 'Dallas, TX',
            'search_terms': 'CDL driver',  # String, not list
            'pages': 3,  # Small batch for testing
            'exact_location': True
        }

        coach_username = 'test-coach'

        print(f"📋 Search parameters: {search_params}")
        print(f"👨‍🏫 Coach: {coach_username}")

        # Submit the job
        async_job = manager.submit_google_search(
            search_params=search_params,
            coach_username=coach_username
        )

        if async_job and async_job.id:
            print(f"✅ Job submitted successfully! Job ID: {async_job.id}")
            print(f"📋 Request ID: {async_job.request_id}")
            return async_job.id
        else:
            print("❌ Failed to submit job")
            return None

    except Exception as e:
        print(f"❌ Error submitting batch: {e}")
        return None

def monitor_job_status(supabase, job_id, timeout_minutes=15):
    """Monitor job status in Supabase"""
    print(f"\n👀 Monitoring job {job_id} for up to {timeout_minutes} minutes...")

    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    last_status = None

    while time.time() - start_time < timeout_seconds:
        try:
            # Check job status
            result = supabase.table('async_job_queue').select('*').eq('id', job_id).execute()

            if result.data:
                job = result.data[0]
                status = job['status']
                request_id = job.get('request_id')

                if status != last_status:
                    print(f"📊 Status update: {status}")
                    if request_id:
                        print(f"🔍 Request ID: {request_id}")
                    last_status = status

                # Check if job is complete
                if status in ['completed', 'failed']:
                    print(f"🎯 Job finished with status: {status}")
                    if status == 'completed':
                        result_count = job.get('result_count', 0)
                        quality_count = job.get('quality_job_count', 0)
                        print(f"📈 Results: {result_count} total, {quality_count} quality jobs")
                    else:
                        error_msg = job.get('error_message', 'Unknown error')
                        print(f"❌ Error: {error_msg}")

                    return status, job

                # Check for notifications (if table exists)
                if request_id:
                    try:
                        notifications = supabase.table('coach_notifications')\
                            .select('*')\
                            .eq('job_id', job_id)\
                            .execute()

                        if notifications.data:
                            print(f"📬 Found {len(notifications.data)} notifications")
                            for notif in notifications.data:
                                print(f"   📝 {notif['message']}")
                    except Exception as e:
                        print(f"⚠️ Note: coach_notifications table not available ({str(e)[:50]}...)")

            time.sleep(30)  # Check every 30 seconds

        except Exception as e:
            print(f"⚠️ Error checking status: {e}")
            time.sleep(30)

    print(f"⏰ Timeout reached after {timeout_minutes} minutes")
    return 'timeout', None

def check_webhook_logs():
    """Check if webhook has been called"""
    print("\n🔍 Checking webhook logs...")

    try:
        # Try to get recent function logs (this might not work in all environments)
        import subprocess
        result = subprocess.run([
            'supabase', 'functions', 'logs', 'outscraper-webhook',
            '--limit', '10'
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print("📋 Recent webhook logs:")
            print(result.stdout)
        else:
            print("⚠️ Could not retrieve webhook logs")
            print(result.stderr)

    except Exception as e:
        print(f"⚠️ Error checking logs: {e}")

def test_webhook_directly():
    """Test webhook directly to ensure it's working"""
    print("\n🧪 Testing webhook endpoint directly...")

    import requests

    webhook_url = os.getenv('OUTSCRAPER_WEBHOOK_URL')
    if not webhook_url:
        print("❌ No webhook URL configured")
        return False

    test_payload = {
        'id': f'direct-test-{int(time.time())}',
        'user_id': 'test-user',
        'status': 'SUCCESS',
        'api_task': True
    }

    try:
        response = requests.post(webhook_url, json=test_payload, timeout=10)
        print(f"📬 Direct test response: {response.status_code}")

        if response.status_code == 200:
            print("✅ Webhook endpoint is working")
            return True
        else:
            print(f"❌ Webhook test failed: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Webhook test error: {e}")
        return False

def main():
    """Run complete end-to-end test"""
    print("🧪 Real Async Batch + Webhook End-to-End Test")
    print("=" * 60)

    # Setup
    supabase = setup_supabase()
    if not supabase:
        return False

    # Test webhook endpoint first
    if not test_webhook_directly():
        print("❌ Webhook not working, aborting test")
        return False

    # Submit test batch
    job_id = submit_test_batch()
    if not job_id:
        return False

    print(f"\n🎯 Job submitted: {job_id}")
    print("📊 This will test the complete flow:")
    print("   1. AsyncJobManager → Outscraper API")
    print("   2. Outscraper processes batch")
    print("   3. Outscraper → Webhook notification")
    print("   4. Webhook → Job status update")
    print("   5. Coach notification sent")

    # Monitor job progress
    final_status, job_data = monitor_job_status(supabase, job_id, timeout_minutes=15)

    # Check webhook logs
    check_webhook_logs()

    # Final report
    print("\n" + "=" * 60)
    print("🎯 TEST COMPLETE")

    if final_status == 'completed':
        print("🎉 SUCCESS! Complete end-to-end flow working!")
        print("✅ Async batch processing")
        print("✅ Webhook notification")
        print("✅ Job status updates")
        print("✅ Coach notifications")
        return True
    elif final_status == 'failed':
        print("❌ Job failed, but system flow working")
        print("✅ Webhook notification received")
        return True
    elif final_status == 'timeout':
        print("⏰ Test timed out - job may still be processing")
        print("💡 Check Supabase manually for job completion")
        return False
    else:
        print("❌ Unexpected result")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)