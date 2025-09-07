#!/usr/bin/env python3
"""
Test Supabase table access for debugging batches issue
"""

import sys
import os

# Add current directory to path
sys.path.append('.')

def test_supabase_tables():
    print("🗄️ TESTING SUPABASE TABLE ACCESS")
    print("=" * 50)
    
    # Test Supabase client
    try:
        from supabase_utils import get_client
        client = get_client()
        if not client:
            print("❌ Failed to get Supabase client")
            return
        print("✅ Supabase client created successfully")
    except Exception as e:
        print(f"❌ Supabase client error: {e}")
        return
    
    # Test each table the system uses
    tables_to_test = [
        'coaches',
        'async_job_queue', 
        'coach_notifications',
        'all_scraped_jobs'
    ]
    
    for table_name in tables_to_test:
        print(f"\n📋 Testing table: {table_name}")
        try:
            # Try to select from the table
            result = client.table(table_name).select("*").limit(1).execute()
            print(f"   ✅ Table '{table_name}' accessible")
            if result.data:
                print(f"   📊 Sample record keys: {list(result.data[0].keys())}")
            else:
                print(f"   📊 Table '{table_name}' exists but is empty")
                
        except Exception as e:
            print(f"   ❌ Table '{table_name}' error: {e}")
    
    # Test AsyncJobManager specifically
    print(f"\n🤖 Testing AsyncJobManager...")
    try:
        from async_job_manager import AsyncJobManager
        manager = AsyncJobManager()
        
        if manager.supabase_client:
            print("   ✅ AsyncJobManager has Supabase client")
            
            # Test getting pending jobs
            pending = manager.get_pending_jobs()
            print(f"   📊 Found {len(pending)} pending jobs")
            
            # Test getting completed jobs
            completed = manager.get_completed_jobs("test", limit=1)
            print(f"   📊 Found {len(completed)} completed jobs (test coach)")
            
        else:
            print("   ❌ AsyncJobManager has no Supabase client")
            
    except Exception as e:
        print(f"   ❌ AsyncJobManager error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_supabase_tables()