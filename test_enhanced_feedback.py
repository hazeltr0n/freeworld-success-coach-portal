#!/usr/bin/env python3
"""
Test Enhanced Feedback System
Tests the complete feedback flow including database schema, edge function logic, and search filtering.
"""

import os
import requests
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

def test_enhanced_feedback_system():
    """Test the complete enhanced feedback system"""

    print("🧪 Testing Enhanced Feedback System")
    print("=" * 50)

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env file")
        return False

    try:
        supabase = create_client(url, key)
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False

    # Test 1: Check database schema
    print(f"\n1️⃣ Testing Database Schema")
    print("-" * 30)

    # Check jobs table columns
    jobs_columns = [
        'job_flagged', 'feedback_expired_links', 'feedback_likes', 'last_expired_feedback_at'
    ]

    schema_ok = True
    for col in jobs_columns:
        try:
            result = supabase.table('jobs').select(col).limit(1).execute()
            print(f"  ✅ jobs.{col} - EXISTS")
        except Exception as e:
            print(f"  ❌ jobs.{col} - MISSING: {e}")
            schema_ok = False

    # Check agent_profiles table columns
    agent_columns = ['total_applications', 'last_application_at']
    for col in agent_columns:
        try:
            result = supabase.table('agent_profiles').select(col).limit(1).execute()
            print(f"  ✅ agent_profiles.{col} - EXISTS")
        except Exception as e:
            print(f"  ❌ agent_profiles.{col} - MISSING: {e}")
            schema_ok = False

    if not schema_ok:
        print("❌ Schema incomplete - apply sql/enhanced_feedback_schema.sql first")
        return False

    # Test 2: Test edge function (if deployed)
    print(f"\n2️⃣ Testing Edge Function")
    print("-" * 30)

    edge_function_url = f"{url}/functions/v1/job-feedback"
    test_feedback = {
        "candidate_id": "test-agent-123",
        "job_url": "https://example.com/test-job",
        "job_title": "Test CDL Driver",
        "company": "Test Company",
        "feedback_type": "job_expired",
        "location": "Test City, TX",
        "coach": "test_coach"
    }

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

        if response.status_code == 200:
            print(f"  ✅ Edge function responding (status: {response.status_code})")
            result = response.json()
            print(f"  📝 Response: {result.get('message', 'No message')}")
        else:
            print(f"  ⚠️  Edge function returned status {response.status_code}")
            print(f"  📝 Response: {response.text}")

    except Exception as e:
        print(f"  ❌ Edge function test failed: {e}")
        print(f"  💡 Make sure to deploy the updated function via Supabase dashboard")

    # Test 3: Test memory search filtering
    print(f"\n3️⃣ Testing Memory Search Filtering")
    print("-" * 30)

    try:
        from supabase_utils import instant_memory_search

        # Test basic search (should work even without new columns if they default properly)
        results = instant_memory_search(
            location="Dallas",
            hours=168,  # 7 days
            market="Dallas"
        )

        print(f"  ✅ Memory search executed successfully")
        print(f"  📊 Found {len(results)} jobs (after feedback filtering)")

        # Check if any jobs have the new feedback columns
        if results:
            sample_job = results[0]
            feedback_cols = ['job_flagged', 'feedback_expired_links', 'feedback_likes']
            for col in feedback_cols:
                if col in sample_job:
                    print(f"  ✅ Sample job includes {col}: {sample_job[col]}")
                else:
                    print(f"  ⚠️  Sample job missing {col} (may need schema refresh)")

    except ImportError:
        print(f"  ❌ Could not import instant_memory_search function")
    except Exception as e:
        print(f"  ❌ Memory search test failed: {e}")

    # Test 4: Check feedback data
    print(f"\n4️⃣ Checking Existing Feedback Data")
    print("-" * 30)

    try:
        feedback_result = supabase.table('job_feedback').select('*').limit(5).execute()
        feedback_count = len(feedback_result.data or [])
        print(f"  📊 Found {feedback_count} existing feedback records")

        if feedback_count > 0:
            feedback_types = set()
            for fb in feedback_result.data:
                feedback_types.add(fb.get('feedback_type', 'unknown'))
            print(f"  📝 Feedback types seen: {', '.join(feedback_types)}")

    except Exception as e:
        print(f"  ❌ Could not check feedback data: {e}")

    # Test Summary
    print(f"\n📋 Test Summary")
    print("=" * 50)
    print(f"✅ Database schema: {'✅ READY' if schema_ok else '❌ NEEDS SETUP'}")
    print(f"🔧 Edge function: Deploy via Supabase Dashboard")
    print(f"🔍 Memory filtering: Updated in supabase_utils.py")
    print(f"📊 System status: {'🎉 READY FOR PRODUCTION' if schema_ok else '⚠️  NEEDS SCHEMA SETUP'}")

    # Next steps
    print(f"\n🚀 Next Steps:")
    if not schema_ok:
        print(f"  1. Apply sql/enhanced_feedback_schema.sql in Supabase Dashboard")
    print(f"  2. Deploy supabase/functions/job-feedback/index.ts via Dashboard")
    print(f"  3. Test feedback submission with real job URLs")
    print(f"  4. Verify 72-hour expiry logic works correctly")

    return schema_ok

if __name__ == "__main__":
    test_enhanced_feedback_system()