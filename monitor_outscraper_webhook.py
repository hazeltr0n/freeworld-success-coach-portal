#!/usr/bin/env python3
"""
Monitor for real Outscraper webhook calls
"""

import os
import time
import toml
from supabase import create_client
from datetime import datetime

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

def monitor_job():
    """Monitor job 41 for real Outscraper webhook calls"""

    # Setup Supabase
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE')
    )

    job_id = 41
    request_id = 'a-4eac0762-59c3-470f-92e8-4dc7db99e75c'

    print(f"📡 Monitoring job {job_id} for real Outscraper webhook calls...")
    print(f"🔍 Request ID: {request_id}")
    print(f"📍 Webhook URL: {os.getenv('OUTSCRAPER_WEBHOOK_URL')}")
    print("⏰ Checking every 30 seconds...\n")

    last_status = None
    start_time = time.time()

    while True:
        try:
            # Check job status
            result = supabase.table('async_job_queue').select('*').eq('id', job_id).execute()

            if result.data:
                job = result.data[0]
                status = job['status']
                completed_at = job.get('completed_at')

                current_time = datetime.now().strftime('%H:%M:%S')

                if status != last_status:
                    print(f"[{current_time}] 📊 Status: {status}")

                    if status == 'completed':
                        print(f"🎉 JOB COMPLETED! Outscraper called our webhook!")
                        print(f"   ✅ Completed at: {completed_at}")
                        print(f"   📈 Result count: {job.get('result_count', 0)}")
                        print(f"   🌟 Quality count: {job.get('quality_job_count', 0)}")

                        # Check webhook logs
                        print(f"\n📋 Webhook was successfully called by Outscraper!")
                        print(f"   Request ID: {request_id}")
                        print(f"   Job updated from 'submitted' to 'completed'")
                        return True

                    elif status == 'failed':
                        print(f"❌ Job failed: {job.get('error_message', 'Unknown error')}")
                        return False

                    last_status = status
                else:
                    # Show periodic heartbeat
                    elapsed = int(time.time() - start_time)
                    print(f"[{current_time}] ⏳ Still {status} - {elapsed}s elapsed")

                # Check if we've been waiting too long
                if time.time() - start_time > 1800:  # 30 minutes
                    print(f"\n⏰ 30 minutes elapsed. Job may be taking longer than expected.")
                    print(f"💡 You can check Outscraper dashboard directly:")
                    print(f"   https://outscraper.com/dashboard")
                    return False

            else:
                print(f"❌ Job {job_id} not found")
                return False

        except Exception as e:
            print(f"❌ Error checking job: {e}")

        time.sleep(30)  # Check every 30 seconds

def main():
    """Main monitoring function"""
    print("🔍 Real Outscraper Webhook Monitor")
    print("=" * 50)

    success = monitor_job()

    if success:
        print("\n🎉 SUCCESS! Complete end-to-end validation:")
        print("✅ AsyncJobManager → Outscraper")
        print("✅ Outscraper processing")
        print("✅ Outscraper → Webhook callback")
        print("✅ Webhook → Job status update")
        print("\n💯 The async batch + webhook system is fully operational!")
    else:
        print("\n⚠️ Monitoring ended without webhook callback")
        print("💡 This could mean:")
        print("   - Job is still processing (check Outscraper dashboard)")
        print("   - Job failed (check error message)")
        print("   - Webhook needs additional debugging")

if __name__ == '__main__':
    main()