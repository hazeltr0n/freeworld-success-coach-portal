#!/usr/bin/env python3
"""
Debug Supabase agent search functionality
"""

import os
from supabase_utils import supabase_find_agents, get_client

def test_supabase_search():
    """Test Supabase agent search with debug info"""
    print("🔍 TESTING SUPABASE AGENT SEARCH")
    print("=" * 50)
    
    # Check environment
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    print(f"SUPABASE_URL: {supabase_url[:30] + '...' if supabase_url else 'NOT SET'}")
    print(f"SUPABASE_ANON_KEY: {'SET' if supabase_key else 'NOT SET'}")
    print()
    
    # Test client connection
    client = get_client()
    if not client:
        print("❌ Cannot get Supabase client")
        return
    
    print("✅ Supabase client connected")
    print()
    
    # Test basic agent_profiles query
    try:
        print("📋 Testing direct agent_profiles query...")
        result = client.table('agent_profiles').select('*').limit(5).execute()
        
        print(f"Total rows found: {len(result.data or [])}")
        if result.data:
            print("Sample agent:")
            agent = result.data[0]
            for key, value in agent.items():
                print(f"  {key}: {value}")
            print()
        else:
            print("❌ No agent profiles found in database")
            return
    except Exception as e:
        print(f"❌ Direct query failed: {e}")
        return
    
    # Test search function with different queries
    test_cases = [
        ("name", "Benjamin"),  # First name
        ("name", "Ben"),       # Partial first name  
        ("name", "Bechtolsheim"),  # Last name
        ("uuid", "59bd7baa"),  # UUID fragment
    ]
    
    for search_type, query in test_cases:
        print(f"🔎 Testing search: {search_type}='{query}'")
        
        try:
            results = supabase_find_agents(
                query=query,
                coach_username="sarah_davis",  # Use a test coach
                by=search_type,
                limit=10
            )
            
            print(f"  Results: {len(results)} found")
            for result in results:
                print(f"    - {result.get('name')} ({result.get('uuid', 'no-uuid')}) [{result.get('source')}]")
            
            if not results:
                print("    ⚠️ No results found")
            print()
            
        except Exception as e:
            print(f"    ❌ Search failed: {e}")
            print()

def test_raw_supabase_queries():
    """Test raw Supabase queries to debug the issue"""
    print("🔧 TESTING RAW SUPABASE QUERIES")
    print("=" * 50)
    
    client = get_client()
    if not client:
        print("❌ No client")
        return
    
    # Test 1: Get all agents
    try:
        print("1. Get all agents:")
        result = client.table('agent_profiles').select('agent_name, agent_uuid, coach_username').execute()
        print(f"   Total agents: {len(result.data or [])}")
        for agent in (result.data or [])[:3]:  # Show first 3
            print(f"   - {agent.get('agent_name')} | {agent.get('coach_username')} | {agent.get('agent_uuid')}")
        print()
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 2: Filter by coach
    try:
        print("2. Filter by coach 'sarah_davis':")
        result = client.table('agent_profiles').select('agent_name, agent_uuid').eq('coach_username', 'sarah_davis').execute()
        print(f"   Sarah's agents: {len(result.data or [])}")
        for agent in (result.data or []):
            print(f"   - {agent.get('agent_name')} | {agent.get('agent_uuid')}")
        print()
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 3: Name search with ilike
    try:
        print("3. Name search with ilike 'Benjamin':")
        result = client.table('agent_profiles').select('agent_name, agent_uuid').ilike('agent_name', '%benjamin%').execute()
        print(f"   Benjamin matches: {len(result.data or [])}")
        for agent in (result.data or []):
            print(f"   - {agent.get('agent_name')} | {agent.get('agent_uuid')}")
        print()
    except Exception as e:
        print(f"   ❌ Failed: {e}")

if __name__ == "__main__":
    test_supabase_search()
    print("\n" + "=" * 50)
    test_raw_supabase_queries()