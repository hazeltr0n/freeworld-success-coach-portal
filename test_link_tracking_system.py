#!/usr/bin/env python3
"""
Test script to systematically verify the link generation and tracking system.

This tests:
1. Portal link generation from free agents table
2. Job link generation within portals
3. Short.io link creation
4. Click tracking via Supabase edge function

Run with: python test_link_tracking_system.py
"""

import sys
import os
sys.path.append(os.getcwd())

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️ python-dotenv not available, trying manual env loading")
    # Manual .env loading
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print("✅ Manually loaded .env file")

def test_agent_profile_loading():
    """Test loading agent profiles and checking portal URLs"""
    print("=== Testing Agent Profile Loading ===")

    try:
        from free_agent_system import load_agent_profiles
        from user_management import get_coach_manager

        # Use james.hazelton as test coach (known to have agents)
        test_coach = "james.hazelton"
        print(f"🔍 Testing with coach: {test_coach}")

        # Load agents
        agents = load_agent_profiles(test_coach)
        if not agents:
            print(f"❌ No agents found for coach {test_coach}")
            return False

        print(f"✅ Loaded {len(agents)} agents")

        # Check first agent's portal URL
        first_agent = agents[0]
        agent_name = first_agent.get('agent_name', 'Unknown')
        portal_url = first_agent.get('portal_url', '')
        custom_url = first_agent.get('custom_url', '')
        agent_uuid = first_agent.get('agent_uuid', '')

        print(f"\n📋 First Agent: {agent_name}")
        print(f"   UUID: {agent_uuid}")
        print(f"   portal_url: {portal_url}")
        print(f"   custom_url: {custom_url}")

        if not portal_url and not custom_url:
            print("⚠️ No portal URL found - this might be the issue!")
            return False

        # Test dynamic link generation
        from app import generate_dynamic_portal_link
        dynamic_url = generate_dynamic_portal_link(first_agent)
        print(f"   dynamic_url: {dynamic_url}")

        return True

    except Exception as e:
        print(f"❌ Agent profile test failed: {e}")
        return False

def test_short_io_availability():
    """Test if Short.io service is available and working"""
    print("\n=== Testing Short.io Availability ===")

    try:
        from link_tracker import LinkTracker
        tracker = LinkTracker()

        print(f"✅ LinkTracker imported successfully")
        print(f"   is_available: {getattr(tracker, 'is_available', 'MISSING')}")
        print(f"   has create_short_link: {hasattr(tracker, 'create_short_link')}")

        if hasattr(tracker, 'create_short_link') and tracker.is_available:
            # Test creating a short link
            test_url = "https://example.com/test"
            test_tags = ["test:system", "type:verification"]

            short_url = tracker.create_short_link(test_url, title="System Test", tags=test_tags)
            print(f"   test_short_url: {short_url}")

            if short_url and short_url != test_url:
                print("✅ Short.io is working correctly")
                return True
            else:
                print("❌ Short.io returned same URL or failed")
                return False
        else:
            print("❌ Short.io not available or not configured")
            return False

    except Exception as e:
        print(f"❌ Short.io test failed: {e}")
        return False

def test_job_link_generation():
    """Test job link generation within portal"""
    print("\n=== Testing Job Link Generation ===")

    try:
        import pandas as pd
        from free_agent_system import update_job_tracking_for_agent

        # Create test job data
        test_jobs = pd.DataFrame([
            {
                'source.title': 'Test CDL Driver',
                'source.apply_url': 'https://example.com/job1',
                'ai.match': 'good',
                'ai.route_type': 'local',
                'ai.fair_chance': 'not_fair_chance_employer',
                'sys.scraped_at': '2025-09-20T10:00:00Z'
            },
            {
                'source.title': 'Test OTR Driver',
                'source.apply_url': 'https://example.com/job2',
                'ai.match': 'so-so',
                'ai.route_type': 'otr',
                'ai.fair_chance': 'fair_chance_employer',
                'sys.scraped_at': '2025-09-20T11:00:00Z'
            }
        ])

        # Test agent params
        agent_params = {
            'agent_uuid': 'test-uuid-123',
            'agent_name': 'Test Agent',
            'location': 'Houston',
            'coach_username': 'test_coach',
            'match_level': 'good and so-so'
        }

        print(f"🔍 Testing with {len(test_jobs)} jobs")

        # Process jobs through tracking system
        tracked_jobs = update_job_tracking_for_agent(test_jobs, agent_params)

        print(f"✅ Processed {len(tracked_jobs)} jobs")

        # Check if tracking URLs were added
        for idx, job in tracked_jobs.iterrows():
            original_url = job.get('source.apply_url', '')
            tracked_url = job.get('meta.tracked_url', '')
            title = job.get('source.title', '')

            print(f"   Job: {title}")
            print(f"     Original: {original_url}")
            print(f"     Tracked:  {tracked_url}")

            if tracked_url:
                if tracked_url.startswith('https://freeworldjobs.short.gy'):
                    print(f"     ✅ Short.io link created")
                elif tracked_url == original_url:
                    print(f"     ⚠️ Using original URL (Short.io may be unavailable)")
                else:
                    print(f"     ❓ Unknown tracking URL format")
            else:
                print(f"     ❌ No tracking URL generated")

        return len(tracked_jobs) > 0

    except Exception as e:
        print(f"❌ Job link generation test failed: {e}")
        return False

def test_supabase_connection():
    """Test Supabase connection and edge function"""
    print("\n=== Testing Supabase Connection ===")

    try:
        from supabase_utils import get_client

        client = get_client()
        if not client:
            print("❌ Supabase client not available")
            return False

        print("✅ Supabase client connected")

        # Test querying click_events table
        result = client.table('click_events').select('id, clicked_at, candidate_id').limit(1).execute()

        if result.data:
            print(f"✅ click_events table accessible, found {len(result.data)} sample records")
            sample = result.data[0]
            print(f"   Sample record: {sample}")
        else:
            print("⚠️ click_events table empty or inaccessible")

        return True

    except Exception as e:
        print(f"❌ Supabase test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚛 FreeWorld Link Tracking System Test")
    print("=" * 50)

    tests = [
        ("Agent Profile Loading", test_agent_profile_loading),
        ("Short.io Availability", test_short_io_availability),
        ("Job Link Generation", test_job_link_generation),
        ("Supabase Connection", test_supabase_connection)
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")

    total_tests = len(results)
    passed_tests = sum(results.values())

    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 All systems working correctly!")
    else:
        print("⚠️ Some systems need attention")

    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)