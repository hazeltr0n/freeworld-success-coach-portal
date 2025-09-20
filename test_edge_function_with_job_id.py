#!/usr/bin/env python3
"""
Test edge function with explicit job_id to see database updates
"""

import os
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def test_edge_function_with_job_id():
    """Test edge function with explicit job_id"""

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY")
        return

    supabase = create_client(url, key)
    edge_function_url = f"{url}/functions/v1/job-feedback"

    # Get current state of test_123 job
    print(f"🔍 Checking current state of job test_123...")

    try:
        result = supabase.table('jobs').select('feedback_expired_links, last_expired_feedback_at').eq('job_id', 'test_123').execute()
        if result.data:
            current_job = result.data[0]
            current_expired_links = current_job.get('feedback_expired_links', 0)
            current_timestamp = current_job.get('last_expired_feedback_at')
            print(f"  📊 Current feedback_expired_links: {current_expired_links}")
            print(f"  🕐 Current last_expired_feedback_at: {current_timestamp}")
        else:
            print(f"  ❌ Job test_123 not found")
            return
    except Exception as e:
        print(f"  ❌ Error checking current state: {e}")
        return

    # Test the edge function with explicit job_id
    test_feedback = {
        "candidate_id": "test-candidate-123",
        "job_id": "test_123",  # Explicit job_id
        "job_url": "https://example.com/test-job-123",
        "job_title": "Test CDL Driver Position",
        "company": "Test Trucking Company",
        "feedback_type": "job_expired",
        "location": "Houston, TX",
        "coach": "test.coach"
    }

    print(f"\n🧪 Testing edge function with explicit job_id...")
    print(f"  📝 Payload: {test_feedback}")

    try:
        response = requests.post(
            edge_function_url,
            json=test_feedback,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            timeout=10
        )

        print(f"  📡 Response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Success: {result.get('message', 'No message')}")
        else:
            print(f"  ❌ Error response: {response.text}")

    except Exception as e:
        print(f"  ❌ Request failed: {e}")
        return

    # Check if the database was updated
    print(f"\n🔍 Checking if job test_123 was updated...")

    try:
        result = supabase.table('jobs').select('feedback_expired_links, last_expired_feedback_at').eq('job_id', 'test_123').execute()
        if result.data:
            updated_job = result.data[0]
            new_expired_links = updated_job.get('feedback_expired_links', 0)
            new_timestamp = updated_job.get('last_expired_feedback_at')

            print(f"  📊 New feedback_expired_links: {new_expired_links}")
            print(f"  🕐 New last_expired_feedback_at: {new_timestamp}")

            if new_expired_links > current_expired_links:
                print(f"  ✅ SUCCESS: Counter incremented from {current_expired_links} to {new_expired_links}")
            else:
                print(f"  ❌ FAIL: Counter not incremented (still {new_expired_links})")

            if new_timestamp and new_timestamp != current_timestamp:
                print(f"  ✅ SUCCESS: Timestamp updated")
            else:
                print(f"  ❌ FAIL: Timestamp not updated")
        else:
            print(f"  ❌ Job test_123 not found after update")
    except Exception as e:
        print(f"  ❌ Error checking updated state: {e}")

    # Check the feedback table for the new entry
    print(f"\n📊 Checking feedback table for new entry...")
    try:
        feedback_result = supabase.table('job_feedback').select('*').order('created_at', desc=True).limit(1).execute()
        if feedback_result.data:
            latest_feedback = feedback_result.data[0]
            print(f"  📝 Latest feedback:")
            print(f"    - job_id: {latest_feedback.get('job_id', 'N/A')}")
            print(f"    - feedback_type: {latest_feedback.get('feedback_type', 'N/A')}")
            print(f"    - candidate_id: {latest_feedback.get('candidate_id', 'N/A')}")
            print(f"    - created_at: {latest_feedback.get('created_at', 'N/A')}")
    except Exception as e:
        print(f"  ❌ Error checking feedback table: {e}")

if __name__ == "__main__":
    test_edge_function_with_job_id()