#!/usr/bin/env python3
"""
Test feedback submission directly to the deployed edge function
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_feedback_submission():
    """Test submitting feedback to the deployed edge function"""

    print("🧪 Testing Feedback Submission to Edge Function")
    print("=" * 50)

    # Use the deployed function URL
    supabase_url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not anon_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY")
        return False

    function_url = f"{supabase_url}/functions/v1/job-feedback"

    # Test different feedback types
    test_cases = [
        {
            "name": "Temporary Negative (job_expired)",
            "data": {
                "candidate_id": "test-agent-123",
                "job_url": "https://indeed.com/test-expired-job",
                "job_title": "Test CDL Driver - Expired",
                "company": "Test Logistics",
                "feedback_type": "job_expired",
                "location": "Dallas, TX",
                "coach": "test_coach"
            }
        },
        {
            "name": "Permanent Negative (requires_experience)",
            "data": {
                "candidate_id": "test-agent-123",
                "job_url": "https://indeed.com/test-experience-job",
                "job_title": "Test CDL Driver - Experience Required",
                "company": "Test Transport",
                "feedback_type": "requires_experience",
                "location": "Dallas, TX",
                "coach": "test_coach"
            }
        },
        {
            "name": "Positive (i_applied_to_this_job)",
            "data": {
                "candidate_id": "test-agent-123",
                "job_url": "https://indeed.com/test-applied-job",
                "job_title": "Test CDL Driver - Applied",
                "company": "Test Freight",
                "feedback_type": "i_applied_to_this_job",
                "location": "Dallas, TX",
                "coach": "test_coach"
            }
        }
    ]

    headers = {
        "Authorization": f"Bearer {anon_key}",
        "Content-Type": "application/json",
        "apikey": anon_key
    }

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ Testing: {test_case['name']}")
        print("-" * 40)

        try:
            response = requests.post(
                function_url,
                json=test_case['data'],
                headers=headers,
                timeout=30
            )

            print(f"  📡 Status: {response.status_code}")

            try:
                result = response.json()
                print(f"  📝 Response: {json.dumps(result, indent=2)}")

                if response.status_code == 200 and result.get('success'):
                    print(f"  ✅ SUCCESS: {result.get('message', 'Feedback processed')}")
                else:
                    print(f"  ⚠️  ISSUE: {result.get('message', 'Unknown error')}")

            except json.JSONDecodeError:
                print(f"  📝 Raw response: {response.text}")

        except requests.exceptions.Timeout:
            print(f"  ⏰ TIMEOUT: Function took too long to respond")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")

    print(f"\n📋 Test Complete")
    print("🔍 Check Supabase Dashboard → Functions → job-feedback → Logs for details")

if __name__ == "__main__":
    test_feedback_submission()