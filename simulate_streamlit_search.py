#!/usr/bin/env python3
"""
Simulate the exact Streamlit search process for debugging
Uses real agent data from Supabase
"""

import os
import sys
from supabase_utils import supabase_find_agents, get_client

def simulate_streamlit_search():
    """Simulate the exact search process that happens in Streamlit"""
    print("🎯 SIMULATING STREAMLIT SEARCH PROCESS")
    print("=" * 60)
    
    # Check environment (same as Streamlit would)
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    print(f"SUPABASE_URL: {supabase_url[:30] + '...' if supabase_url else 'NOT SET'}")
    print(f"SUPABASE_ANON_KEY: {'SET' if supabase_key else 'NOT SET'}")
    print()
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase environment variables")
        print("⚠️  In Streamlit, these come from st.secrets")
        print("   For this test, you need to set them as environment variables")
        return
    
    # Test client connection
    client = get_client()
    if not client:
        print("❌ Cannot get Supabase client")
        return
    
    print("✅ Supabase client connected")
    print()
    
    # Real data from your Supabase instance (CORRECTED)
    test_agent_uuid = "ef78e371-1929-11ef-937f-de2fe15254ef"  # This is the real UUID!
    test_agent_email = "benjamin+2@freeworld.org"
    test_agent_name = "Benjamin Bechtolsheim"
    
    # First, verify the agent exists in the database
    print("🔍 STEP 1: Verify agent exists in database")
    try:
        result = client.table('agent_profiles').select('*').eq('agent_uuid', test_agent_uuid).execute()
        if result.data and len(result.data) > 0:
            agent_data = result.data[0]
            print(f"✅ Found agent in database:")
            print(f"   UUID: {agent_data.get('agent_uuid')}")
            print(f"   Name: {agent_data.get('agent_name')}")
            print(f"   Email: {agent_data.get('agent_email')}")
            print(f"   Coach: {agent_data.get('coach_username')}")
            print(f"   Active: {agent_data.get('is_active')}")
            coach_username = agent_data.get('coach_username', '')
        else:
            print(f"❌ Agent {test_agent_uuid} not found in database")
            return
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        return
    
    print()
    
    # Test different search scenarios (same as Streamlit app)
    test_cases = [
        ("name", "Benjamin Bechtolsheim", "Search by full name"),
        ("name", "Benjamin", "Search by first name"),
        ("name", "Ben", "Search by partial first name"),  
        ("name", "Bechtolsheim", "Search by last name"),
        ("name", "Bech", "Search by partial last name"),
        ("email", "benjamin+2@freeworld.org", "Search by email (full)"),
        ("email", "benjamin", "Search by email (partial)"),
        ("uuid", "7df25316", "Search by UUID (partial)"),
        ("uuid", test_agent_uuid, "Search by UUID (full)"),
    ]
    
    print("🔍 STEP 2: Test search scenarios (same as Streamlit)")
    for search_type, query, description in test_cases:
        print(f"\n🔎 {description}")
        print(f"   Search type: {search_type}")
        print(f"   Query: '{query}'")
        print(f"   Coach: '{coach_username}'")
        
        # This is the exact same call that Streamlit makes
        print(f"🔍 DEBUG: About to call supabase_find_agents...")
        
        try:
            # EXACT same function call as in app.py
            results = supabase_find_agents(
                query=query,
                coach_username=coach_username,
                by=search_type,
                limit=15
            )
            
            print(f"🔍 DEBUG: Supabase function completed successfully!")
            print(f"🔍 DEBUG: Supabase returned {len(results)} results")
            
            if results:
                print(f"✅ Found {len(results)} agent(s):")
                for result in results:
                    print(f"   - {result.get('name')} ({result.get('uuid')}) [{result.get('source', 'unknown')}]")
            else:
                print("⚠️  No matching agents found")
                
        except Exception as e:
            print(f"❌ Supabase search failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 50)

if __name__ == "__main__":
    # Try to get environment variables from Streamlit secrets format if available
    try:
        # If running in a Streamlit-like environment, this might work
        import streamlit as st
        if hasattr(st, 'secrets'):
            os.environ['SUPABASE_URL'] = st.secrets.get('SUPABASE_URL', '')
            os.environ['SUPABASE_ANON_KEY'] = st.secrets.get('SUPABASE_ANON_KEY', '')
    except:
        pass
    
    simulate_streamlit_search()