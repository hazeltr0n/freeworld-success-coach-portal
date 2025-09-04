#!/usr/bin/env python3
"""
Test the exact query being built in supabase_find_agents
"""

from supabase_utils import get_client

def test_exact_query():
    """Test the exact same query logic as supabase_find_agents"""
    print("🔍 TESTING EXACT QUERY LOGIC")
    print("=" * 50)
    
    client = get_client()
    if not client:
        print("❌ Cannot get Supabase client")
        return
    
    # Exact same parameters as the real search
    coach_username = "james.hazelton"
    query = "Benjamin"
    query_lower = query.strip().lower()
    
    print(f"Coach username: '{coach_username}'")
    print(f"Search query: '{query}'")  
    print(f"Query lower: '{query_lower}'")
    print()
    
    try:
        # Step 1: Test base query (just coach filtering)
        print("STEP 1: Base query (coach + active filter only)")
        base_query = client.table('agent_profiles').select(
            'agent_uuid, agent_name, agent_email, agent_city, agent_state, '
            'portal_clicks, last_portal_click, created_at, search_config'
        ).eq('coach_username', coach_username).eq('is_active', True)
        
        base_result = base_query.execute()
        print(f"Base query found: {len(base_result.data or [])} agents for coach '{coach_username}'")
        
        for agent in (base_result.data or []):
            print(f"  - {agent.get('agent_name')} | {agent.get('agent_uuid')}")
        print()
        
        # Step 2: Add name search filter  
        print("STEP 2: Full query (coach + active + name search)")
        full_query = client.table('agent_profiles').select(
            'agent_uuid, agent_name, agent_email, agent_city, agent_state, '
            'portal_clicks, last_portal_click, created_at, search_config'
        ).eq('coach_username', coach_username).eq('is_active', True).ilike('agent_name', f'%{query_lower}%')
        
        full_result = full_query.execute()
        print(f"Full query found: {len(full_result.data or [])} agents")
        
        for agent in (full_result.data or []):
            print(f"  - {agent.get('agent_name')} | {agent.get('agent_uuid')}")
        
        if not full_result.data:
            print("❌ No results from full query!")
            print("This means the name search is failing")
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_exact_query()