#!/usr/bin/env python3
"""Verify analytics table has the click data after refresh"""

import os
from dotenv import load_dotenv
from supabase_utils import get_client

load_dotenv()

client = get_client()

print("=" * 80)
print("VERIFYING ANALYTICS REFRESH RESULTS")
print("=" * 80)

# Query the analytics table for james.hazelton agents
print("\n📋 Checking free_agents_analytics for james.hazelton...")
analytics = client.table('free_agents_analytics').select('*').contains('coach_usernames', ['james.hazelton']).order('total_job_clicks', desc=True).limit(5).execute()

if analytics.data:
    print(f"\n✅ Found {len(analytics.data)} agents for james.hazelton")
    print("\nTop 5 by click activity:")
    for agent in analytics.data:
        print(f"\n  📊 {agent.get('agent_name')}")
        print(f"      Total Job Clicks: {agent.get('total_job_clicks')}")
        print(f"      Job Clicks (14d): {agent.get('job_clicks_14d')}")
        print(f"      Total Applications: {agent.get('total_applications')}")
        print(f"      Applications (14d): {agent.get('applications_14d')}")
        print(f"      Engagement Score: {agent.get('engagement_score')}")
        print(f"      Activity Level: {agent.get('activity_level')}")
        print(f"      Last Activity: {agent.get('last_activity_at')}")
        print(f"      Coach Usernames: {agent.get('coach_usernames')}")
else:
    print("\n❌ No agents found for james.hazelton")

print("\n" + "=" * 80)
