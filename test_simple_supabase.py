#!/usr/bin/env python3
"""
Test Supabase query using same pattern as working memory search
"""

import os
import sys
try:
    import streamlit as st
    if hasattr(st, 'secrets'):
        os.environ['SUPABASE_URL'] = st.secrets.get('SUPABASE_URL', '')
        os.environ['SUPABASE_ANON_KEY'] = st.secrets.get('SUPABASE_ANON_KEY', '')
except:
    pass

from supabase_utils import get_client

def test_simple_supabase():
    print("🧪 SIMPLE SUPABASE TEST")
    print("=" * 40)
    
    client = get_client()
    if not client:
        print("❌ No client")
        return
        
    print("✅ Got client")
    
    # Test the exact same agent data you provided (CORRECTED)
    coach_username = "james.hazelton"
    agent_uuid = "ef78e371-1929-11ef-937f-de2fe15254ef"  # The real UUID
    agent_name = "benjamin"  # lowercase like in our search
    
    try:
        print("\n1. Direct UUID query:")
        result1 = client.table('agent_profiles').select('*').eq('agent_uuid', agent_uuid).execute()
        print(f"   UUID query: {len(result1.data or [])} results")
        if result1.data:
            agent = result1.data[0]
            print(f"   Found: {agent.get('agent_name')} | coach: {agent.get('coach_username')} | active: {agent.get('is_active')}")
        
        print("\n2. Coach filter query:")
        result2 = client.table('agent_profiles').select('*').eq('coach_username', coach_username).execute()
        print(f"   Coach query: {len(result2.data or [])} results")
        for agent in (result2.data or []):
            print(f"   - {agent.get('agent_name')} | {agent.get('agent_uuid')}")
        
        print("\n3. Name search query (EXACT SAME as supabase_find_agents):")
        # This is EXACTLY what supabase_find_agents does
        base_query = client.table('agent_profiles').select(
            'agent_uuid, agent_name, agent_email, agent_city, agent_state, '
            'portal_clicks, last_portal_click, created_at, search_config'
        ).eq('coach_username', coach_username).eq('is_active', True)
        
        result3 = base_query.ilike('agent_name', f'%{agent_name}%').limit(15).execute()
        print(f"   Name search (exact function call): {len(result3.data or [])} results")
        for agent in (result3.data or []):
            print(f"   - {agent.get('agent_name')} | {agent.get('agent_uuid')}")
            
        print("\n4. Now call the actual supabase_find_agents function:")
        from supabase_utils import supabase_find_agents
        results = supabase_find_agents(
            query="benjamin",
            coach_username="james.hazelton", 
            by="name",
            limit=15
        )
        print(f"   supabase_find_agents results: {len(results)} found")
        for result in results:
            print(f"   - {result.get('name')} | {result.get('uuid')}")
            
        if not results:
            print("   ❌ The function is failing but manual query worked!")
            print("   Let's test other search terms:")
            test_terms = ["Benjamin", "Bechtolsheim", "Ben"]
            for term in test_terms:
                term_results = supabase_find_agents(
                    query=term,
                    coach_username="james.hazelton",
                    by="name", 
                    limit=15
                )
                print(f"   '{term}': {len(term_results)} results")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_supabase()