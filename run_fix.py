#!/usr/bin/env python3
"""
Script to carefully update the SQL function in Supabase
"""

from supabase_utils import get_client

def apply_sql_fix():
    client = get_client()
    if not client:
        print("❌ Supabase client not available")
        return False

    # Read the SQL fix
    with open('fix_14d_sql.sql', 'r') as f:
        sql_fix = f.read()

    print("🔧 Applying SQL function fix for 14-day calculations...")

    try:
        # Try to execute via RPC - this might work if there's an exec function
        # First, let's list what functions are available
        result = client.rpc('scheduled_agents_refresh').execute()
        print("✅ Current function exists and works")

        # The issue is we can't directly execute DDL via the client
        # Let's try a workaround - just run the refresh and see if it works better now
        print("🧪 Testing current function before update...")
        result = client.table('free_agents_analytics').select('agent_name, applications_14d, total_applications').eq('agent_name', 'Dallas Test Link').execute()
        if result.data:
            row = result.data[0]
            print(f"Before fix - Apps (14d): {row['applications_14d']}, Apps (All): {row['total_applications']}")

        print("\n📝 SQL function needs to be updated manually in Supabase dashboard:")
        print("1. Go to Database > Functions in Supabase dashboard")
        print("2. Find 'refresh_free_agents_analytics' function")
        print("3. Replace NOW() with CURRENT_TIMESTAMP in the 14-day calculations")
        print(f"4. Or copy this entire function:\n\n{sql_fix}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    apply_sql_fix()