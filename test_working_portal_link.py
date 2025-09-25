#!/usr/bin/env python3
"""
Create a working portal link using the SAME method as job links
"""

def create_working_portal_link():
    """Use the exact same create_short_link method that works for jobs"""

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

    # Step 1: Generate the FINAL portal URL (where we want users to end up)
    from free_agent_system import generate_agent_url
    final_portal_url = generate_agent_url(test_agent['agent_uuid'], test_agent)
    print(f"✅ Final Portal URL: {final_portal_url}")

    # Step 2: Use the SAME create_short_link method that works for jobs
    from link_tracker import LinkTracker
    tracker = LinkTracker()

    # Create tags like we do for jobs
    tags = [
        f"agent:{test_agent['agent_uuid']}",
        f"coach:{test_agent['coach_username']}",
        "source:working_portal_test",
        "type:agent_portal"
    ]

    # Use create_short_link (SAME as jobs) instead of separate generate_edge_function_url + update
    working_short_url = tracker.create_short_link(
        original_url=final_portal_url,  # Pass the final portal URL directly
        title=f"Working Portal - {test_agent['agent_name']}",
        tags=tags,
        candidate_id=test_agent['agent_uuid']
    )

    if working_short_url and working_short_url != final_portal_url:
        print(f"✅ SUCCESS! Working portal link: {working_short_url}")
        print(f"\n🎯 WORKING FLOW (same as jobs):")
        print(f"1. User clicks: {working_short_url}")
        print(f"2. Goes through same edge function as job links")
        print(f"3. Redirects to: {final_portal_url}")
        print(f"4. User sees personalized Dallas portal")
        return working_short_url
    else:
        print(f"❌ create_short_link failed or returned same URL")
        print(f"Returned: {working_short_url}")
        return None

if __name__ == "__main__":
    print("🔧 Creating Working Portal Link (Same Method as Jobs)")
    print("=" * 60)
    result = create_working_portal_link()
    if result:
        print(f"\n🎉 SUCCESS! Test this WORKING link: {result}")
    else:
        print(f"\n💥 FAILED - even the job link method doesn't work")