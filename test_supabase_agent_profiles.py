#!/usr/bin/env python3
"""
Test script for Supabase agent profiles integration
"""

import os
from datetime import datetime, timezone
from supabase_utils import (
    save_agent_profile_to_supabase,
    load_agent_profiles_from_supabase,
    delete_agent_profile_from_supabase,
    get_client
)
from free_agent_system import encode_agent_params, generate_agent_url

def test_supabase_connection():
    """Test Supabase connection"""
    print("🔗 Testing Supabase Connection")
    print("=" * 50)
    
    client = get_client()
    if client is None:
        print("❌ Supabase client not available")
        print("   Check SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
        return False
    
    print("✅ Supabase client connected successfully")
    return True

def test_agent_profile_operations():
    """Test CRUD operations for agent profiles"""
    print("\n👤 Testing Agent Profile Operations")
    print("=" * 50)
    
    # Sample agent data
    coach_username = "test_coach_profile"
    test_agent = {
        'agent_uuid': '12345-test-uuid-67890',
        'agent_name': 'Test Agent Smith',
        'agent_email': 'test.agent@example.com',
        'agent_city': 'Houston',
        'agent_state': 'TX',
        'location': 'Houston, TX',
        'route_filter': 'local',
        'fair_chance_only': True,
        'max_jobs': 25,
        'experience_level': 'entry'
    }
    
    try:
        # 1. Test Save
        print("\n📝 Testing Save Operation...")
        success, error = save_agent_profile_to_supabase(coach_username, test_agent)
        if success:
            print("✅ Agent profile saved successfully")
        else:
            print(f"❌ Save failed: {error}")
            return False
        
        # 2. Test Load
        print("\n📋 Testing Load Operation...")
        profiles, error = load_agent_profiles_from_supabase(coach_username)
        if error is None:
            print(f"✅ Loaded {len(profiles)} profile(s)")
            if profiles:
                profile = profiles[0]
                print(f"   Agent: {profile['agent_name']}")
                print(f"   UUID: {profile['agent_uuid']}")
                print(f"   Location: {profile['location']}")
                print(f"   Route: {profile['route_filter']}")
                print(f"   Fair Chance: {profile['fair_chance_only']}")
                print(f"   Max Jobs: {profile['max_jobs']}")
                print(f"   Created: {profile.get('created_at', 'N/A')}")
        else:
            print(f"❌ Load failed: {error}")
            return False
        
        # 3. Test Update (save again with different data)
        print("\n🔄 Testing Update Operation...")
        test_agent['location'] = 'Dallas, TX'
        test_agent['max_jobs'] = 50
        success, error = save_agent_profile_to_supabase(coach_username, test_agent)
        if success:
            print("✅ Agent profile updated successfully")
        else:
            print(f"❌ Update failed: {error}")
            return False
        
        # Verify update
        profiles, error = load_agent_profiles_from_supabase(coach_username)
        if error is None and profiles:
            updated_profile = profiles[0]
            print(f"   Updated Location: {updated_profile['location']}")
            print(f"   Updated Max Jobs: {updated_profile['max_jobs']}")
        
        # 4. Test Delete
        print("\n🗑️  Testing Delete Operation...")
        success, error = delete_agent_profile_from_supabase(coach_username, test_agent['agent_uuid'])
        if success:
            print("✅ Agent profile deleted successfully")
        else:
            print(f"❌ Delete failed: {error}")
            return False
        
        # Verify deletion
        profiles, error = load_agent_profiles_from_supabase(coach_username)
        if error is None:
            print(f"   Remaining profiles: {len(profiles)}")
        
        return True
        
    except Exception as e:
        print(f"💥 Test error: {e}")
        return False

def test_url_generation():
    """Test agent URL generation"""
    print("\n🔗 Testing URL Generation")
    print("=" * 50)
    
    test_params = {
        'agent_uuid': '12345-test-uuid-67890',
        'agent_name': 'Test Agent',
        'location': 'Houston',
        'route_filter': 'local',
        'fair_chance_only': True,
        'max_jobs': 25,
        'experience_level': 'entry',
        'coach_username': 'test_coach'
    }
    
    try:
        # Test encoding
        encoded = encode_agent_params(test_params)
        print(f"✅ Encoded params: {encoded[:50]}...")
        
        # Test URL generation
        url = generate_agent_url(test_params['agent_uuid'], test_params)
        print(f"✅ Generated URL: {url}")
        
        # Verify URL structure
        if 'agent_job_feed' in url and 'config=' in url:
            print("✅ URL structure is valid")
            return True
        else:
            print("❌ URL structure is invalid")
            return False
            
    except Exception as e:
        print(f"❌ URL generation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Free Agent Management - Supabase Integration Test")
    print("=" * 60)
    
    # Check environment
    print("🔍 Environment Check:")
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if supabase_url:
        print(f"   ✅ SUPABASE_URL: {supabase_url[:30]}...")
    else:
        print("   ❌ SUPABASE_URL not set")
    
    if supabase_key:
        print(f"   ✅ SUPABASE_ANON_KEY: {supabase_key[:20]}...")
    else:
        print("   ❌ SUPABASE_ANON_KEY not set")
    
    print()
    
    # Run tests
    tests = [
        ("Supabase Connection", test_supabase_connection),
        ("Agent Profile CRUD", test_agent_profile_operations),
        ("URL Generation", test_url_generation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Agent profiles are ready for production.")
        print("   ✅ Supabase storage working")
        print("   ✅ CRUD operations functional")
        print("   ✅ URL generation working")
        print("   🚀 Ready to test in the Streamlit app!")
    else:
        print("\n⚠️  Some tests failed. Check the setup:")
        print("   1. Ensure Supabase environment variables are set")
        print("   2. Run SQL commands in supabase_setup.sql")
        print("   3. Verify agent_profiles table exists and has proper permissions")

if __name__ == "__main__":
    main()