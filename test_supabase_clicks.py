#!/usr/bin/env python3
"""
Test script for Supabase click tracking integration
"""

import os
from datetime import datetime, timezone, timedelta
from supabase_utils import get_client, fetch_click_events
from free_agent_system import get_agent_click_stats, get_all_agents_click_stats

def test_supabase_connection():
    """Test basic Supabase connection"""
    print("🔗 Testing Supabase Connection")
    print("=" * 40)
    
    client = get_client()
    if client is None:
        print("❌ Supabase client not available")
        print("   Check SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
        return False
    
    print("✅ Supabase client connected successfully")
    return True

def test_fetch_click_events():
    """Test fetching click events"""
    print("\n📊 Testing Click Events Fetch")
    print("=" * 40)
    
    try:
        events = fetch_click_events(limit=10, since_days=30)
        print(f"📈 Found {len(events)} click events in last 30 days")
        
        if events:
            print("\n📋 Sample Event:")
            event = events[0]
            for key, value in event.items():
                print(f"   {key}: {value}")
        else:
            print("⚠️  No click events found")
            print("   This is normal if you haven't set up the webhook yet")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fetching click events: {e}")
        return False

def test_agent_analytics():
    """Test agent analytics functions"""
    print("\n🎯 Testing Agent Analytics")
    print("=" * 40)
    
    # Test with sample agent UUID
    sample_uuid = "59bd7baa-1efb-11ef-937f-de2fe15254ef"
    
    try:
        # Test individual agent stats
        stats = get_agent_click_stats(sample_uuid, 14)
        print(f"📊 Agent {sample_uuid[:8]}... stats:")
        print(f"   Total clicks (14 days): {stats['total_clicks']}")
        print(f"   Recent clicks (7 days): {stats['recent_clicks']}")
        print(f"   Lookback period: {stats['lookback_days']} days")
        
        # Test coach-level stats
        coach_stats = get_all_agents_click_stats("sarah_davis", 14)
        print(f"\n👨‍🏫 Coach 'sarah_davis' stats:")
        print(f"   Total clicks: {coach_stats['total_clicks']}")
        print(f"   Recent clicks: {coach_stats['recent_clicks']}")
        print(f"   Unique agents: {coach_stats['unique_agents']}")
        print(f"   Avg clicks per agent: {coach_stats['avg_clicks_per_agent']:.1f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing analytics: {e}")
        return False

def test_click_event_insertion():
    """Test inserting a sample click event"""
    print("\n➕ Testing Click Event Insertion")
    print("=" * 40)
    
    client = get_client()
    if client is None:
        print("❌ Cannot test insertion - no Supabase client")
        return False
    
    try:
        # Insert a test click event
        test_event = {
            'candidate_id': '59bd7baa-1efb-11ef-937f-de2fe15254ef',
            'candidate_name': 'Test Agent',
            'coach': 'test_coach',
            'market': 'Houston',
            'route': 'local',
            'match': 'good',
            'fair': 'false',
            'clicked_at': datetime.now(timezone.utc).isoformat(),
            'job_title': 'Test CDL Driver Position',
            'company': 'Test Transport Co',
            'short_id': 'test123'
        }
        
        result = client.table('click_events').insert(test_event).execute()
        
        if result.data:
            print("✅ Test click event inserted successfully")
            print(f"   Event ID: {result.data[0]['id']}")
            
            # Clean up - delete the test event
            client.table('click_events').delete().eq('id', result.data[0]['id']).execute()
            print("🧹 Test event cleaned up")
            return True
        else:
            print("⚠️  Click event insertion returned no data")
            return False
            
    except Exception as e:
        print(f"❌ Error inserting click event: {e}")
        print("   This might mean the click_events table doesn't exist yet")
        print("   Run the SQL commands in supabase_setup.sql first")
        return False

def main():
    """Run all tests"""
    print("🧪 Free Agent Management - Supabase Click Tracking Test")
    print("=" * 60)
    
    # Check environment variables
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
        ("Connection", test_supabase_connection),
        ("Fetch Events", test_fetch_click_events),
        ("Analytics", test_agent_analytics),
        ("Insert Event", test_click_event_insertion)
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
        print("\n🎉 All tests passed! Click tracking is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Check the setup instructions:")
        print("   1. Make sure SUPABASE_URL and SUPABASE_ANON_KEY are set")
        print("   2. Run the SQL commands in supabase_setup.sql")
        print("   3. Set up the Short.io webhook to send clicks to Supabase")

if __name__ == "__main__":
    main()