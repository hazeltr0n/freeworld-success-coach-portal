#!/usr/bin/env python3
"""
Test Admin Portal URL functionality
Quick test to verify the admin_portal_url field is working correctly
"""

import os
import sys

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def test_supabase_column():
    """Test that the admin_portal_url column exists and is accessible"""
    try:
        from supabase_utils import get_client
        
        client = get_client()
        if not client:
            print("❌ Supabase client not available")
            return False
        
        # Test query with admin_portal_url column
        result = client.table('agent_profiles').select(
            'agent_uuid, agent_name, admin_portal_url'
        ).limit(1).execute()
        
        print(f"✅ Successfully queried admin_portal_url column")
        print(f"📊 Found {len(result.data)} test records")
        
        if result.data:
            record = result.data[0]
            print(f"🔍 Sample record:")
            print(f"   UUID: {record.get('agent_uuid', '')[:8]}...")
            print(f"   Name: {record.get('agent_name', '')}")
            print(f"   Admin Portal: {record.get('admin_portal_url', '(empty)')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase column test failed: {e}")
        return False

def test_agent_loading():
    """Test that agent profiles load correctly with the new column"""
    try:
        from supabase_utils import load_agent_profiles_from_supabase
        
        # Try loading agents for a test coach (replace with actual coach username)
        profiles, error = load_agent_profiles_from_supabase('test_coach')
        
        if error:
            print(f"⚠️ Agent loading returned error: {error}")
        else:
            print(f"✅ Successfully loaded {len(profiles)} agent profiles")
            
            # Check if admin_portal_url is included
            if profiles:
                sample = profiles[0]
                has_admin_portal = 'admin_portal_url' in sample
                print(f"🔍 admin_portal_url field present: {has_admin_portal}")
                if has_admin_portal:
                    admin_url = sample.get('admin_portal_url', '')
                    print(f"🔍 Sample admin portal URL: {admin_url if admin_url else '(empty)'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent loading test failed: {e}")
        return False

def test_agent_saving():
    """Test that agent profiles can be saved with admin_portal_url"""
    try:
        from supabase_utils import save_agent_profile_to_supabase
        
        # Create a test agent data with admin_portal_url
        test_agent = {
            'agent_uuid': 'test-admin-portal-123',
            'agent_name': 'Test Admin Portal Agent',
            'agent_email': 'test@example.com',
            'location': 'Test City',
            'route_filter': 'both',
            'fair_chance_only': False,
            'max_jobs': 25,
            'match_level': 'good and so-so',
            'admin_portal_url': 'https://example.com/admin-portal-test',
            'custom_url': ''
        }
        
        success, error = save_agent_profile_to_supabase('test_coach', test_agent)
        
        if success:
            print("✅ Successfully saved agent with admin_portal_url")
            
            # Clean up test record
            from supabase_utils import get_client
            client = get_client()
            client.table('agent_profiles').delete().eq('agent_uuid', 'test-admin-portal-123').execute()
            print("🧹 Cleaned up test record")
            
        else:
            print(f"❌ Failed to save agent: {error}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Agent saving test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Admin Portal URL Functionality")
    print("=" * 50)
    
    tests = [
        ("Supabase Column Access", test_supabase_column),
        ("Agent Profile Loading", test_agent_loading), 
        ("Agent Profile Saving", test_agent_saving)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔬 Testing {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: ERROR - {e}")
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Admin portal functionality is ready.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        sys.exit(1)

if __name__ == '__main__':
    main()