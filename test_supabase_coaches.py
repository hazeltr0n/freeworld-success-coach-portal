#!/usr/bin/env python3
"""
Test Supabase coaches integration
"""

import sys
import os

# Add current directory to path
sys.path.append('.')

def test_supabase_coaches():
    print("🗃️ TESTING SUPABASE COACHES INTEGRATION")
    print("=" * 50)
    
    # Test environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    print(f"📝 Environment Check:")
    print(f"  SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
    print(f"  SUPABASE_ANON_KEY: {'✅ Set' if supabase_key else '❌ Missing'}")
    
    if not (supabase_url and supabase_key):
        print("❌ Missing Supabase environment variables!")
        return
    
    # Test Supabase client
    try:
        from supabase_utils import get_client
        client = get_client()
        if client:
            print("✅ Supabase client created successfully")
        else:
            print("❌ Failed to create Supabase client")
            return
    except Exception as e:
        print(f"❌ Supabase client error: {e}")
        return
    
    # Test coaches table
    try:
        from supabase_utils import load_coaches_json
        coaches_data = load_coaches_json()
        print(f"\n📊 Coaches loaded from Supabase: {len(coaches_data)} records")
        
        for username, data in coaches_data.items():
            print(f"  - {username}: {data.get('full_name', 'Unknown')} ({data.get('role', 'Unknown')})")
        
        if not coaches_data:
            print("⚠️ No coaches found in Supabase!")
            print("💡 You may need to:")
            print("   1. Create the 'coaches' table in Supabase")
            print("   2. Add coach records to the table")
            print("   3. Check table permissions")
            
    except Exception as e:
        print(f"❌ Error loading coaches from Supabase: {e}")
        
    # Test table creation/structure
    print(f"\n🔧 Checking coaches table structure...")
    try:
        # Try to get table info
        res = client.table("coaches").select("*").limit(1).execute()
        print("✅ Coaches table exists and is accessible")
        
        if res.data:
            print(f"📋 Sample record structure: {list(res.data[0].keys())}")
        else:
            print("ℹ️ Coaches table exists but is empty")
            
    except Exception as e:
        print(f"❌ Coaches table error: {e}")
        print("💡 You may need to create the coaches table with:")
        print("""
        CREATE TABLE coaches (
            username TEXT PRIMARY KEY,
            data JSONB NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """)

if __name__ == "__main__":
    test_supabase_coaches()