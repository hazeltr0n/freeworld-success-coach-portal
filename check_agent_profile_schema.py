#!/usr/bin/env python3
"""Check agent_profiles table schema"""

import os
from dotenv import load_dotenv
from supabase_utils import get_client

load_dotenv()

client = get_client()

print("=" * 80)
print("CHECKING agent_profiles SCHEMA")
print("=" * 80)

# Get one agent to see what fields exist
agent = client.table('agent_profiles').select('*').limit(1).execute()

if agent.data:
    print("\n✅ Sample agent_profiles record:")
    print(f"\nAvailable fields:")
    for key in sorted(agent.data[0].keys()):
        value = agent.data[0][key]
        # Truncate long values
        if isinstance(value, str) and len(value) > 50:
            value = value[:50] + "..."
        print(f"  {key}: {value}")
else:
    print("\n❌ No agent profiles found")

print("\n" + "=" * 80)
