#!/usr/bin/env python3
"""
Test Manual Refresh Functions
Quick test to verify the manual refresh buttons work correctly
"""

def test_manual_refresh():
    """Test both manual refresh functions"""

    print("🧪 Testing Manual Refresh Functions")
    print("=" * 50)

    try:
        from companies_rollup import get_client
        from free_agents_rollup import get_client as get_fa_client

        # Test Supabase connection
        print("1. Testing Supabase connection...")
        client = get_client()
        fa_client = get_fa_client()

        if not client:
            print("❌ Companies client failed")
            return False

        if not fa_client:
            print("❌ Free agents client failed")
            return False

        print("✅ Supabase clients connected")

        # Test companies refresh function exists
        print("\n2. Testing companies refresh function...")
        try:
            result = client.rpc('scheduled_companies_refresh').execute()
            if result.data:
                print("✅ Companies refresh function exists and executed")
                if isinstance(result.data, dict):
                    success = result.data.get('success', False)
                    companies_updated = result.data.get('companies_updated', 0)
                    print(f"   📊 Result: Success={success}, Companies Updated={companies_updated}")
                else:
                    print(f"   📊 Raw result: {result.data}")
            else:
                print("⚠️  Companies refresh executed but no data returned")
        except Exception as e:
            print(f"❌ Companies refresh failed: {e}")
            return False

        # Test agents refresh function exists
        print("\n3. Testing agents refresh function...")
        try:
            result = client.rpc('scheduled_agents_refresh').execute()
            if result.data:
                print("✅ Agents refresh function exists and executed")
                if isinstance(result.data, dict):
                    success = result.data.get('success', False)
                    agents_updated = result.data.get('agents_updated', 0)
                    print(f"   📊 Result: Success={success}, Agents Updated={agents_updated}")
                else:
                    print(f"   📊 Raw result: {result.data}")
            else:
                print("⚠️  Agents refresh executed but no data returned")
        except Exception as e:
            print(f"❌ Agents refresh failed: {e}")
            return False

        # Test rollup log table exists
        print("\n4. Testing rollup log table...")
        try:
            result = client.table('analytics_rollup_log').select('*').limit(5).execute()
            print(f"✅ Rollup log table exists with {len(result.data)} recent entries")

            if result.data:
                latest = result.data[-1]
                print(f"   📝 Latest log: {latest.get('rollup_type')} at {latest.get('executed_at')}")

        except Exception as e:
            print(f"⚠️  Rollup log table issue: {e}")

        print("\n🎉 Manual refresh test completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Go to your Streamlit app")
        print("   2. Navigate to Companies tab")
        print("   3. Click '⚡ Manual Refresh' button")
        print("   4. Navigate to Free Agents → Analytics tab")
        print("   5. Click '⚡ Manual Refresh' button")
        print("   6. Both should show success messages with update counts")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're in the correct directory")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_manual_refresh()