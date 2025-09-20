#!/usr/bin/env python3
"""
Test if job test_123 is properly filtered out of memory search
"""

import os
from dotenv import load_dotenv
from supabase_utils import instant_memory_search

load_dotenv()

def test_memory_filtering():
    """Test if expired job test_123 is filtered out"""

    print(f"🧪 Testing Memory Search Filtering for job test_123")
    print("=" * 60)

    try:
        # Run memory search
        results = instant_memory_search(
            location="Houston",  # Use a common location
            hours=168,  # 7 days
            market="Houston"
        )

        print(f"📊 Found {len(results)} jobs total in memory search")

        # Check if test_123 is in the results
        test_job_found = False
        for job in results:
            if job.get('job_id') == 'test_123':
                test_job_found = True
                print(f"❌ PROBLEM: Job test_123 still appears in results!")
                print(f"   - feedback_expired_links: {job.get('feedback_expired_links', 'N/A')}")
                print(f"   - last_expired_feedback_at: {job.get('last_expired_feedback_at', 'N/A')}")
                break

        if not test_job_found:
            print(f"✅ SUCCESS: Job test_123 correctly filtered out of results")

        # Also check if any jobs have expired feedback data
        jobs_with_expired_feedback = []
        for job in results:
            if job.get('feedback_expired_links', 0) > 0:
                jobs_with_expired_feedback.append({
                    'job_id': job.get('job_id', 'unknown')[:8],
                    'expired_links': job.get('feedback_expired_links', 0),
                    'last_expired': job.get('last_expired_feedback_at', 'N/A')
                })

        if jobs_with_expired_feedback:
            print(f"\n📋 Jobs with expired feedback that appear in results:")
            for job in jobs_with_expired_feedback[:5]:  # Show first 5
                print(f"   - {job['job_id']}: {job['expired_links']} expired, last: {job['last_expired']}")

    except Exception as e:
        print(f"❌ Error testing memory filtering: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_memory_filtering()