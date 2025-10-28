#!/usr/bin/env python3
"""Query Supabase to see what's in Johnny's record"""

import os
from dotenv import load_dotenv
from supabase_utils import get_client

load_dotenv()

client = get_client()

# Query Johnny by UUID
johnny_uuid = "66543fdd-5f28-4c1c-b633-494fad1e5b88"

result = client.table('agent_profiles').select('*').eq('agent_uuid', johnny_uuid).execute()

if result.data:
    import json
    agent = result.data[0]
    print("=" * 60)
    print("JOHNNY HOPKINS RECORD IN SUPABASE")
    print("=" * 60)
    print(json.dumps(agent, indent=2, default=str))
    print("=" * 60)
    print(f"\nKey fields:")
    print(f"  agent_uuid: {agent.get('agent_uuid')}")
    print(f"  agent_name: {agent.get('agent_name')}")
    print(f"  coach_username: {agent.get('coach_username')}")
    print(f"  coach_usernames: {agent.get('coach_usernames')}")
    print(f"  placement_status: {agent.get('placement_status')}")
    print(f"  employment_status: {agent.get('employment_status')}")
    print(f"  is_active: {agent.get('is_active')}")
else:
    print("❌ No agent found with UUID:", johnny_uuid)
