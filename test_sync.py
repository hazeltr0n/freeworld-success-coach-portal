#!/usr/bin/env python3
"""
Quick test for Airtable → Supabase sync
"""

import os
import streamlit as st

# Mirror st.secrets into env like main app
try:
    for k, v in (st.secrets or {}).items():
        if isinstance(v, (str, int, float, bool)):
            os.environ.setdefault(k, str(v))
except Exception:
    pass

def test_credentials():
    """Test if required credentials are available"""
    required_vars = [
        'AIRTABLE_API_KEY',
        'AIRTABLE_BASE_ID', 
        'AIRTABLE_TABLE_ID',
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY'
    ]
    
    print("🔍 Checking credentials...")
    missing = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            print(f"❌ Missing: {var}")
        else:
            print(f"✅ Found: {var} (length: {len(str(value))})")
    
    if missing:
        print(f"\n❌ Missing {len(missing)} required variables: {', '.join(missing)}")
        return False
    else:
        print("\n✅ All credentials available!")
        return True

def test_airtable_connection():
    """Test Airtable connection"""
    try:
        from pyairtable import Api
        
        api_key = os.getenv('AIRTABLE_API_KEY')
        base_id = os.getenv('AIRTABLE_BASE_ID')
        table_id = os.getenv('AIRTABLE_TABLE_ID')
        
        print(f"🔍 Testing Airtable connection...")
        print(f"   Base ID: {base_id}")
        print(f"   Table ID: {table_id}")
        
        client = Api(api_key).table(base_id, table_id)
        
        # Try to fetch just one record
        records = list(client.iterate(page_size=1))
        
        if records:
            record = records[0]
            fields = record.get('fields', {})
            print(f"✅ Airtable connected! Sample record:")
            print(f"   Record ID: {record.get('id', 'N/A')}")
            print(f"   Fields: {list(fields.keys())}")
            return True
        else:
            print("⚠️ Airtable connected but no records found")
            return True
            
    except Exception as e:
        print(f"❌ Airtable connection failed: {type(e).__name__}: {str(e)[:100]}")
        return False

def test_supabase_connection():
    """Test Supabase connection"""
    try:
        from supabase_utils import get_client
        
        print(f"🔍 Testing Supabase connection...")
        client = get_client()
        
        if not client:
            print("❌ Supabase client initialization failed")
            return False
        
        # Test connection by checking agent_profiles table
        result = client.table('agent_profiles').select('*').limit(1).execute()
        
        if result:
            print(f"✅ Supabase connected! Found {len(result.data)} sample records")
            if result.data:
                sample = result.data[0]
                print(f"   Sample fields: {list(sample.keys())[:5]}...")
            return True
        else:
            print("❌ Supabase query failed")
            return False
            
    except Exception as e:
        print(f"❌ Supabase connection failed: {type(e).__name__}: {str(e)[:100]}")
        return False

def main():
    print("🚀 Testing Airtable → Supabase Sync Prerequisites\n")
    
    # Test credentials
    creds_ok = test_credentials()
    if not creds_ok:
        return
    
    print("\n" + "="*50)
    
    # Test connections
    airtable_ok = test_airtable_connection()
    print()
    supabase_ok = test_supabase_connection()
    
    print("\n" + "="*50)
    print("📊 SUMMARY:")
    print(f"   Credentials: {'✅' if creds_ok else '❌'}")
    print(f"   Airtable: {'✅' if airtable_ok else '❌'}")
    print(f"   Supabase: {'✅' if supabase_ok else '❌'}")
    
    if creds_ok and airtable_ok and supabase_ok:
        print("\n🎉 All systems ready for sync!")
        print("   Run: python3 airtable_supabase_sync.py --limit 10 --dry-run")
    else:
        print("\n⚠️ Fix issues above before running sync")

if __name__ == '__main__':
    main()