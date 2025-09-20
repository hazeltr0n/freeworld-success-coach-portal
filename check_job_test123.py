#!/usr/bin/env python3
"""
Check specific job test_123 for feedback updates
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def check_job_test123():
    """Check the specific job test_123 for feedback updates"""

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY")
        return

    supabase = create_client(url, key)

    # Check for job_id = test_123
    print(f"🔍 Looking for job_id = 'test_123'...")

    try:
        result = supabase.table('jobs').select('*').eq('job_id', 'test_123').execute()

        if result.data:
            job = result.data[0]
            print(f"✅ Found job with job_id 'test_123':")
            print(f"  📝 Title: {job.get('job_title', 'N/A')}")
            print(f"  🏢 Company: {job.get('company', 'N/A')}")
            print(f"  🚫 job_flagged: {job.get('job_flagged', 'N/A')}")
            print(f"  ⏰ feedback_expired_links: {job.get('feedback_expired_links', 'N/A')}")
            print(f"  👍 feedback_likes: {job.get('feedback_likes', 'N/A')}")
            print(f"  🕐 last_expired_feedback_at: {job.get('last_expired_feedback_at', 'N/A')}")
            print(f"  📅 created_at: {job.get('created_at', 'N/A')}")
            print(f"  🔗 apply_url: {job.get('apply_url', 'N/A')[:100]}...")
        else:
            print(f"❌ No job found with job_id = 'test_123'")

            # Let's search for partial matches
            print(f"\n🔍 Searching for job_ids containing 'test'...")
            result2 = supabase.table('jobs').select('job_id, job_title, company').ilike('job_id', '%test%').execute()

            if result2.data:
                print(f"📋 Found {len(result2.data)} jobs with 'test' in job_id:")
                for job in result2.data[:5]:  # Show first 5
                    print(f"  - {job.get('job_id', 'N/A')} | {job.get('job_title', 'N/A')[:50]}...")
            else:
                print(f"❌ No jobs found with 'test' in job_id")

    except Exception as e:
        print(f"❌ Error checking job: {e}")

    # Also check recent feedback entries
    print(f"\n📊 Recent feedback entries:")
    try:
        feedback_result = supabase.table('job_feedback').select('*').order('created_at', desc=True).limit(5).execute()

        if feedback_result.data:
            for i, fb in enumerate(feedback_result.data, 1):
                print(f"  {i}. {fb.get('feedback_type', 'N/A')} | job_id: {fb.get('job_id', 'N/A')} | created: {fb.get('created_at', 'N/A')}")
        else:
            print(f"  ❌ No feedback entries found")

    except Exception as e:
        print(f"❌ Error checking feedback: {e}")

if __name__ == "__main__":
    check_job_test123()