#!/usr/bin/env python3
"""
Check what agent data actually exists in Supabase
"""

from supabase_utils import get_client

def check_agent_data():
    """Check what agents are actually in the database"""
    print("📊 CHECKING ACTUAL AGENT DATA IN SUPABASE")
    print("=" * 50)
    
    client = get_client()
    if not client:
        print("❌ Cannot get Supabase client")
        return
    
    print("✅ Supabase client connected")
    print()
    
    # Check all agents in the database
    try:
        print("1. All agents in agent_profiles table:")
        result = client.table('agent_profiles').select('agent_uuid, agent_name, agent_email, coach_username, is_active, created_at').execute()
        
        if result.data and len(result.data) > 0:
            print(f"   Total agents: {len(result.data)}")
            for i, agent in enumerate(result.data, 1):
                print(f"   {i}. {agent.get('agent_name', 'NO NAME')} | {agent.get('agent_uuid', 'NO UUID')}")
                print(f"      Email: {agent.get('agent_email', 'NO EMAIL')}")
                print(f"      Coach: {agent.get('coach_username', 'NO COACH')}")
                print(f"      Active: {agent.get('is_active', 'UNKNOWN')}")
                print(f"      Created: {agent.get('created_at', 'UNKNOWN')}")
                print()
        else:
            print("   ❌ NO AGENTS FOUND in agent_profiles table!")
        
    except Exception as e:
        print(f"   ❌ Query failed: {e}")
    
    print("-" * 50)
    
    # Check if there are any agents with similar UUIDs
    try:
        print("2. Search for agents with UUID containing '7df25316':")
        result = client.table('agent_profiles').select('*').ilike('agent_uuid', '%7df25316%').execute()
        
        if result.data and len(result.data) > 0:
            print(f"   Found {len(result.data)} matching agents:")
            for agent in result.data:
                print(f"   - {agent.get('agent_name')} | {agent.get('agent_uuid')}")
        else:
            print("   No agents found with that UUID pattern")
            
    except Exception as e:
        print(f"   ❌ UUID search failed: {e}")
    
    print("-" * 50)
    
    # Check if there are any agents with similar emails
    try:
        print("3. Search for agents with email containing 'benjamin':")
        result = client.table('agent_profiles').select('*').ilike('agent_email', '%benjamin%').execute()
        
        if result.data and len(result.data) > 0:
            print(f"   Found {len(result.data)} matching agents:")
            for agent in result.data:
                print(f"   - {agent.get('agent_name')} | {agent.get('agent_email')} | {agent.get('agent_uuid')}")
        else:
            print("   No agents found with that email pattern")
            
    except Exception as e:
        print(f"   ❌ Email search failed: {e}")

if __name__ == "__main__":
    check_agent_data()