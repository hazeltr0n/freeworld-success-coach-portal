#!/usr/bin/env python3
"""Test the analytics refresh function to debug click activity issue"""

import os
from dotenv import load_dotenv
from supabase_utils import get_client

load_dotenv()

client = get_client()

print("=" * 80)
print("TESTING ANALYTICS REFRESH FUNCTION")
print("=" * 80)

# Call the refresh function
print("\n📊 Calling scheduled_agents_refresh()...")
result = client.rpc('scheduled_agents_refresh').execute()

print(f"\n✅ Result: {result.data}")

# Query the analytics table to see what was created
print("\n📋 Checking free_agents_analytics table for james.hazelton...")
analytics = client.table('free_agents_analytics').select('*').contains('coach_usernames', ['james.hazelton']).execute()

if analytics.data:
    print(f"\n✅ Found {len(analytics.data)} agents for james.hazelton")
    for agent in analytics.data[:3]:  # Show first 3
        print(f"\n  Agent: {agent.get('agent_name')}")
        print(f"    UUID: {agent.get('agent_uuid')}")
        print(f"    coach_username: {agent.get('coach_username')}")
        print(f"    coach_usernames: {agent.get('coach_usernames')}")
        print(f"    total_job_clicks: {agent.get('total_job_clicks')}")
        print(f"    job_clicks_14d: {agent.get('job_clicks_14d')}")
        print(f"    total_applications: {agent.get('total_applications')}")
        print(f"    placement_status: {agent.get('placement_status')}")
        print(f"    employment_status: {agent.get('employment_status')}")
else:
    print("\n❌ No agents found for james.hazelton")

# Check if click_events has data
print("\n🔍 Checking click_events table for recent activity...")
clicks = client.table('click_events').select('*').order('clicked_at', desc=True).limit(5).execute()

if clicks.data:
    print(f"\n✅ Found {len(clicks.data)} recent click events:")
    for click in clicks.data:
        print(f"\n  Clicked: {click.get('clicked_at')}")
        print(f"    Candidate ID: {click.get('candidate_id')}")
        print(f"    Company: {click.get('company')}")
        print(f"    Job Title: {click.get('job_title')}")
else:
    print("\n❌ No click events found")

print("\n" + "=" * 80)
