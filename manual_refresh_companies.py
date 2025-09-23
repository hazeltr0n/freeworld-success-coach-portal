#!/usr/bin/env python3
"""
Manual Companies Refresh
Execute the companies analytics refresh function directly
"""

import streamlit as st
from supabase_utils import get_client

def refresh_companies_analytics():
    """Execute the companies analytics refresh function"""
    try:
        client = get_client()
        if not client:
            print("❌ Cannot connect to Supabase")
            return False

        print("🔄 Running companies analytics refresh...")

        # Call the scheduled refresh function
        result = client.rpc('scheduled_companies_refresh').execute()

        if result.data:
            response = result.data
            print(f"✅ Refresh completed: {response}")

            if response.get('success'):
                print(f"📊 Companies updated: {response.get('companies_updated', 0)}")
                print(f"🕐 Completed at: {response.get('timestamp')}")
                return True
            else:
                print(f"❌ Refresh failed: {response.get('error', 'Unknown error')}")
                return False
        else:
            print("❌ No response from refresh function")
            return False

    except Exception as e:
        print(f"❌ Error executing refresh: {e}")
        return False

if __name__ == "__main__":
    print("🏢 Manual Companies Analytics Refresh")
    print("=" * 50)

    success = refresh_companies_analytics()

    if success:
        print("\n✅ Companies analytics refresh completed successfully!")
        print("🌐 Visit http://localhost:8502 to view updated results")
    else:
        print("\n❌ Companies analytics refresh failed!")
        print("Check the logs above for error details")