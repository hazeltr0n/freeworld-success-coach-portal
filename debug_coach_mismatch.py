#!/usr/bin/env python3
"""
Debug the coach username mismatch issue
"""

from supabase_utils import get_client, supabase_find_agents

def debug_coach_mismatch():
    """Debug the coach username filtering issue"""
    print("🎯 DEBUGGING COACH USERNAME MISMATCH")
    print("=" * 50)
    
    # Test data
    agent_uuid = "7df25316-a62c-4057-a00b-176fa5ae839c"
    agent_email = "benjamin+2@freeworld.org"
    coach_username = "james.hazelton"
    
    client = get_client()
    if not client:
        print("❌ Cannot get Supabase client")
        return
    
    print("✅ Supabase client connected")
    print()
    
    # Step 1: Find the Benjamin agent and see what coach it's assigned to
    print("🔍 STEP 1: Check Benjamin's actual coach assignment")
    try:
        result = client.table('agent_profiles').select(
            'agent_uuid, agent_name, agent_email, coach_username, is_active'
        ).eq('agent_uuid', agent_uuid).execute()
        
        if result.data and len(result.data) > 0:
            agent = result.data[0]
            actual_coach = agent.get('coach_username')
            is_active = agent.get('is_active')
            
            print(f"✅ Found Benjamin Bechtolsheim:")
            print(f"   Name: {agent.get('agent_name')}")
            print(f"   UUID: {agent.get('agent_uuid')}")
            print(f"   Email: {agent.get('agent_email')}")
            print(f"   Assigned Coach: '{actual_coach}'")
            print(f"   Is Active: {is_active}")
            print(f"   Search Coach: '{coach_username}'")
            print()
            
            if actual_coach == coach_username:
                print("✅ COACH MATCH: Agent belongs to the searching coach")
            else:
                print("❌ COACH MISMATCH: This is why search returns no results!")
                print(f"   Agent belongs to: '{actual_coach}'")
                print(f"   But searching as: '{coach_username}'")
            print()
            
        else:
            print("❌ Benjamin agent not found by UUID")
            return
            
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        return
    
    # Step 2: Test the actual search function with the correct coach
    print("🔍 STEP 2: Test search function with correct coach")
    
    # Test with the actual coach that owns the agent
    if 'actual_coach' in locals() and actual_coach:
        print(f"Testing search with actual coach: '{actual_coach}'")
        try:
            results = supabase_find_agents(
                query="Benjamin",
                coach_username=actual_coach,
                by="name",
                limit=15
            )
            print(f"   Results with correct coach: {len(results)} found")
            for result in results:
                print(f"   - {result.get('name')} ({result.get('uuid')})")
        except Exception as e:
            print(f"   ❌ Search failed: {e}")
    
    print()
    
    # Test with the wrong coach (what's currently happening)
    print(f"Testing search with wrong coach: '{coach_username}'")
    try:
        results = supabase_find_agents(
            query="Benjamin",
            coach_username=coach_username,
            by="name",
            limit=15
        )
        print(f"   Results with wrong coach: {len(results)} found")
        if not results:
            print("   ❌ No results - this confirms the coach mismatch issue!")
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
    
    print()
    
    # Step 3: Show all agents for james.hazelton
    print(f"🔍 STEP 3: All agents assigned to '{coach_username}'")
    try:
        result = client.table('agent_profiles').select(
            'agent_name, agent_uuid, agent_email'
        ).eq('coach_username', coach_username).eq('is_active', True).execute()
        
        if result.data and len(result.data) > 0:
            print(f"   Found {len(result.data)} agents for {coach_username}:")
            for agent in result.data:
                print(f"   - {agent.get('agent_name')} | {agent.get('agent_uuid')}")
        else:
            print(f"   ❌ No active agents found for coach '{coach_username}'")
            
    except Exception as e:
        print(f"   ❌ Query failed: {e}")

if __name__ == "__main__":
    debug_coach_mismatch()