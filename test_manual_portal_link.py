#!/usr/bin/env python3
"""
Manually create a working portal link to bypass the Short.io update issues
"""

def create_manual_portal_link():
    """Create a portal link manually to test the flow"""

    # Test agent data
    test_agent = {
        'agent_uuid': '561de432-5c27-469b-b652-c9589a20b7c6',
        'agent_name': 'Dallas Test Link',
        'location': 'Dallas',
        'route_filter': 'both',
        'fair_chance_only': False,
        'max_jobs': 100,
        'match_level': 'good and so-so',
        'coach_username': 'james.hazelton',
        'show_prepared_for': True,
        'pathway_preferences': ['cdl_pathway']
    }

    # Step 1: Generate encoded URL
    from free_agent_system import generate_agent_url
    encoded_url = generate_agent_url(test_agent['agent_uuid'], test_agent)
    print(f"✅ Step 1 - Encoded URL: {encoded_url}")

    # Step 2: Create NEW Short.io link (not update existing)
    from link_tracker import LinkTracker
    tracker = LinkTracker()

    # Generate edge function URL
    tags = [
        f"agent:{test_agent['agent_uuid']}",
        f"coach:{test_agent['coach_username']}",
        "source:manual_test",
        "type:agent_portal"
    ]

    edge_function_url = tracker.generate_edge_function_url(
        target_url=encoded_url,
        candidate_id=test_agent['agent_uuid'],
        tags=tags
    )

    print(f"✅ Step 2 - Edge Function URL: {edge_function_url}")

    # Step 3: Create brand new Short.io link (don't update existing)
    try:
        new_short_url = tracker._create_shortio_link_internal(
            original_url=edge_function_url,
            title=f"Manual Test Portal - {test_agent['agent_name']}"
        )

        if new_short_url:
            print(f"✅ Step 3 - NEW Short.io URL: {new_short_url}")
            print(f"\n🎯 COMPLETE WORKING FLOW:")
            print(f"1. User clicks: {new_short_url}")
            print(f"2. Short.io redirects to: {edge_function_url}")
            print(f"3. Edge function logs click and redirects to: {encoded_url}")
            print(f"4. User sees personalized Dallas portal")
            return new_short_url
        else:
            print(f"❌ Step 3 - Failed to create new Short.io link")
            return None

    except Exception as e:
        print(f"❌ Error creating manual portal link: {e}")
        return None

if __name__ == "__main__":
    print("🔧 Creating Manual Portal Link Test")
    print("=" * 50)
    result = create_manual_portal_link()
    if result:
        print(f"\n🎉 SUCCESS! Test this link: {result}")
    else:
        print(f"\n💥 FAILED to create working portal link")