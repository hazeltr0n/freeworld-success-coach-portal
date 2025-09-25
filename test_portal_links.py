#!/usr/bin/env python3
"""
Test portal link generation to verify the complete flow works
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def test_portal_link_generation():
    """Test the complete portal link generation flow"""
    print("🧪 TESTING PORTAL LINK GENERATION")
    print("=" * 50)

    # Test agent params
    test_agent = {
        'agent_uuid': 'test-agent-12345',
        'agent_name': 'Test Driver Agent',
        'location': 'Houston',
        'route_filter': 'both',
        'fair_chance_only': False,
        'max_jobs': 25,
        'match_level': 'good and so-so',
        'coach_username': 'test.coach'
    }

    try:
        # Test 1: Generate encoded URL
        print("🔗 Test 1: Generate encoded Supabase URL")
        from free_agent_system import generate_agent_url

        encoded_url = generate_agent_url(test_agent['agent_uuid'], test_agent)
        print(f"✅ Encoded URL: {encoded_url[:100]}...")

        # Test 2: Initialize link tracker
        print("\n🔗 Test 2: Initialize Link Tracker")
        from link_tracker import LinkTracker

        tracker = LinkTracker()
        print(f"✅ Link Tracker initialized: {tracker}")

        # Test 3: Generate edge function URL
        print("\n🔗 Test 3: Generate edge function URL")

        tags = [
            f"agent:{test_agent['agent_uuid']}",
            f"coach:{test_agent['coach_username']}",
            "source:portal_test",
            "type:agent_portal"
        ]

        edge_function_url = tracker.generate_edge_function_url(
            target_url=encoded_url,
            candidate_id=test_agent['agent_uuid'],
            tags=tags
        )

        print(f"✅ Edge function URL: {edge_function_url}")

        # Test 4: Create/update Short.io link
        print("\n🔗 Test 4: Create/Update Short.io link")

        custom_url = f"portal-{test_agent['agent_uuid']}"

        success = tracker.update_short_link(
            custom_url,
            edge_function_url,
            title=f"Portal - {test_agent['agent_name']}"
        )

        if success:
            print(f"✅ Short.io link created/updated successfully")
            final_short_url = f"https://{tracker.domain}/{custom_url}"
            print(f"✅ Final portal URL: {final_short_url}")

            print("\n🎯 COMPLETE FLOW:")
            print(f"1. User clicks: {final_short_url}")
            print(f"2. Short.io redirects to: {edge_function_url}")
            print(f"3. Edge function logs click and redirects to: {encoded_url}")
            print(f"4. User sees agent portal with personalized jobs")

            return True
        else:
            print("❌ Short.io link creation failed")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_portal_link_generation()

    if success:
        print("\n🎉 All portal link tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Portal link tests failed!")
        sys.exit(1)