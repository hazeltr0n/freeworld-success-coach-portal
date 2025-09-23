#!/usr/bin/env python3
"""
Utility to recover "deleted" (inactive) agent profiles from Supabase.

Agent profiles are soft-deleted by setting is_active=False, not actually removed.
This script can restore them by setting is_active=True.
"""

import os
import sys
from supabase import create_client, Client

def get_supabase_client():
    """Get Supabase client"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        return None
    
    return create_client(url, key)

def show_inactive_agents(coach_username: str):
    """Show all inactive (soft-deleted) agents for a coach"""
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        result = client.table('agent_profiles').select(
            'agent_uuid, agent_name, agent_email, agent_city, agent_state, '
            'search_config, custom_url, is_active, created_at, last_accessed'
        ).eq('coach_username', coach_username).eq('is_active', False).order(
            'created_at', desc=True
        ).execute()
        
        agents = result.data or []
        print(f"\n📋 Found {len(agents)} inactive agents for coach '{coach_username}':")
        
        for i, agent in enumerate(agents, 1):
            print(f"{i}. {agent['agent_name']} (UUID: {agent['agent_uuid']})")
            print(f"   Email: {agent.get('agent_email', 'N/A')}")
            print(f"   Location: {agent.get('agent_city', 'N/A')}, {agent.get('agent_state', 'N/A')}")
            print(f"   Created: {agent['created_at']}")
            print(f"   Search Config: {agent.get('search_config', {})}")
            print()
        
        return agents
        
    except Exception as e:
        print(f"❌ Error fetching inactive agents: {e}")
        return []

def restore_agent(coach_username: str, agent_uuid: str):
    """Restore a soft-deleted agent by setting is_active=True"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        result = client.table('agent_profiles').update({
            'is_active': True,
            'last_accessed': 'NOW()'
        }).eq('coach_username', coach_username).eq('agent_uuid', agent_uuid).execute()
        
        if result.data:
            print(f"✅ Restored agent {agent_uuid}")
            return True
        else:
            print(f"❌ Failed to restore agent {agent_uuid}")
            return False
            
    except Exception as e:
        print(f"❌ Error restoring agent {agent_uuid}: {e}")
        return False

def restore_all_agents(coach_username: str):
    """Restore ALL soft-deleted agents for a coach"""
    client = get_supabase_client()
    if not client:
        return 0
    
    try:
        result = client.table('agent_profiles').update({
            'is_active': True,
            'last_accessed': 'NOW()'
        }).eq('coach_username', coach_username).eq('is_active', False).execute()
        
        count = len(result.data) if result.data else 0
        print(f"✅ Restored {count} agents for coach '{coach_username}'")
        return count
        
    except Exception as e:
        print(f"❌ Error restoring agents: {e}")
        return 0

def main():
    if len(sys.argv) < 2:
        print("Usage: python recover_deleted_agents.py <coach_username> [command]")
        print("Commands:")
        print("  list                    - Show all inactive agents")
        print("  restore <agent_uuid>    - Restore specific agent")
        print("  restore_all            - Restore ALL inactive agents")
        sys.exit(1)
    
    coach_username = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else "list"
    
    if command == "list":
        show_inactive_agents(coach_username)
    
    elif command == "restore" and len(sys.argv) > 3:
        agent_uuid = sys.argv[3]
        restore_agent(coach_username, agent_uuid)
    
    elif command == "restore_all":
        inactive_agents = show_inactive_agents(coach_username)
        if inactive_agents:
            confirm = input(f"\n⚠️  This will restore {len(inactive_agents)} inactive agents. Continue? (y/N): ")
            if confirm.lower() == 'y':
                restore_all_agents(coach_username)
            else:
                print("❌ Cancelled")
        else:
            print("ℹ️  No inactive agents found")
    
    else:
        print("❌ Invalid command. Use: list, restore <uuid>, or restore_all")

if __name__ == "__main__":
    main()