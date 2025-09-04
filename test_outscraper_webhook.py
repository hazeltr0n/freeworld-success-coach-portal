#!/usr/bin/env python3
"""
Test Outscraper webhook integration with real API
This will submit a small job and test if the webhook gets called
"""

import os
import time
from async_job_manager import AsyncJobManager

def test_real_outscraper_webhook():
    """Submit a real test job to Outscraper and monitor for webhook"""
    
    print("🧪 Testing Real Outscraper Webhook Integration")
    print("=" * 50)
    
    # Check if webhook URL is configured
    webhook_url = os.getenv('OUTSCRAPER_WEBHOOK_URL', '').strip()
    if not webhook_url or webhook_url == "REPLACE_WITH_YOUR_ZAPIER_WEBHOOK_URL":
        print("❌ Webhook URL not configured!")
        print("Please update OUTSCRAPER_WEBHOOK_URL in your .streamlit/secrets.toml")
        return False
    
    print(f"✅ Webhook URL configured: {webhook_url[:50]}...")
    
    # Initialize manager
    manager = AsyncJobManager()
    
    # Test search parameters (small job)
    search_params = {
        'search_terms': 'CDL driver',
        'location': 'Houston, TX',
        'limit': 10,  # Small test job
        'coach_username': 'test_coach'
    }
    
    try:
        print(f"🚀 Submitting test job to Outscraper...")
        print(f"   Terms: {search_params['search_terms']}")
        print(f"   Location: {search_params['location']}")
        print(f"   Limit: {search_params['limit']} jobs")
        
        # Submit the job
        job = manager.submit_google_search(search_params, 'test_coach')
        
        print(f"✅ Job submitted successfully!")
        print(f"   Job ID: {job.id}")
        print(f"   Request ID: {job.request_id}")
        print(f"   Status: {job.status}")
        
        print(f"\n⏳ Job is processing... This usually takes 1-3 minutes")
        print(f"   Check your email/Zapier for webhook notifications")
        print(f"   You can also monitor the job status manually")
        
        # Monitor job for a few minutes
        print(f"\n🔍 Monitoring job status (will check for 5 minutes)...")
        
        for i in range(30):  # Check for 5 minutes (30 * 10 seconds)
            time.sleep(10)
            
            # Check job status
            current_job = manager.check_job_status(job.id)
            if current_job:
                print(f"   [{i+1}/30] Status: {current_job.status}")
                
                if current_job.status in ['completed', 'processed', 'failed']:
                    print(f"\n🎉 Job finished with status: {current_job.status}")
                    if current_job.status in ['completed', 'processed']:
                        print(f"   Total jobs: {current_job.result_count}")
                        print(f"   Quality jobs: {current_job.quality_job_count}")
                    elif current_job.status == 'failed':
                        print(f"   Error: {current_job.error_message}")
                    break
            else:
                print(f"   [{i+1}/30] Could not check status")
        
        else:
            print(f"\n⏰ Monitoring timed out after 5 minutes")
            print(f"   Job may still be processing - check Zapier for webhook")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == '__main__':
    print("🚨 WARNING: This will submit a real job to Outscraper API")
    print("   This will use API credits (~$0.01)")
    
    confirm = input("Continue with test? (y/N): ")
    if confirm.lower() == 'y':
        test_real_outscraper_webhook()
    else:
        print("Test cancelled")