#!/usr/bin/env python3
"""
Control test for click tracking pipeline
Tests each component independently to isolate the issue
"""

import requests
import json
import os
from datetime import datetime
import time

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not found, environment variables may not be loaded")

# Test data
TEST_WEBHOOK_URL = "https://yqbdltothngundojuebk.functions.supabase.co/shortio-clicks"
TEST_PAYLOAD = {
    "link": {
        "idString": "test123",
        "shortURL": "https://test.short.gy/test123", 
        "originalURL": "https://indeed.com/test-job",
        "tags": [
            "coach:test_coach",
            "candidate:test-uuid-12345",
            "agent:Test-Agent",
            "market:Houston",
            "route:local",
            "match:good",
            "fair:true"
        ]
    },
    "referrer": "https://example.com",
    "country": "US",
    "userAgent": "Test-Agent/1.0"
}

def test_webhook_endpoint():
    """Test 1: Can we reach the webhook endpoint?"""
    print("🧪 TEST 1: Testing webhook endpoint accessibility")
    print("=" * 60)
    
    try:
        # Test GET request (should return 405 Method Not Allowed)
        response = requests.get(TEST_WEBHOOK_URL, timeout=10)
        print(f"GET request status: {response.status_code}")
        if response.status_code == 405:
            print("✅ Endpoint is accessible (correctly rejects GET)")
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach endpoint: {e}")
        return False
    
    return True

def test_webhook_post():
    """Test 2: Can we POST to the webhook with valid data?"""
    print("\n🧪 TEST 2: Testing webhook POST request")
    print("=" * 60)
    
    try:
        print(f"Posting to: {TEST_WEBHOOK_URL}")
        print(f"Payload: {json.dumps(TEST_PAYLOAD, indent=2)}")
        
        response = requests.post(
            TEST_WEBHOOK_URL, 
            json=TEST_PAYLOAD, 
            timeout=15,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                if response_data.get('success'):
                    print("✅ Webhook POST successful")
                    return True
                else:
                    print(f"⚠️  Webhook returned success=false: {response_data}")
            except:
                print("⚠️  Webhook returned 200 but invalid JSON")
        else:
            print(f"❌ Webhook returned error status: {response.status_code}")
    except Exception as e:
        print(f"❌ POST request failed: {e}")
    
    return False

def test_supabase_direct():
    """Test 3: Can we connect to Supabase directly?"""
    print("\n🧪 TEST 3: Testing direct Supabase connection")
    print("=" * 60)
    
    try:
        from supabase_utils import get_client, fetch_click_events
        
        client = get_client()
        if not client:
            print("❌ Cannot get Supabase client - check environment variables")
            print("Required: SUPABASE_URL, SUPABASE_ANON_KEY")
            return False
        
        print("✅ Supabase client created successfully")
        
        # Try to fetch recent events
        events = fetch_click_events(limit=5, since_days=1)
        print(f"Recent click events: {len(events)}")
        
        if events:
            print("Sample event:")
            print(json.dumps(events[0], indent=2, default=str))
        else:
            print("No recent events found")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def test_manual_database_insert():
    """Test 4: Can we manually insert a click event?"""
    print("\n🧪 TEST 4: Testing manual database insert")
    print("=" * 60)
    
    try:
        from supabase_utils import get_client
        
        client = get_client()
        if not client:
            print("❌ No Supabase client")
            return False
        
        # Manual insert data
        test_event = {
            'clicked_at': datetime.now().isoformat(),
            'candidate_id': 'manual-test-uuid-67890',
            'candidate_name': 'Manual Test Agent',
            'coach': 'manual_test_coach',
            'market': 'Houston',
            'route': 'local',
            'match': 'good',
            'fair': 'true',
            'short_id': 'manual123',
            'user_agent': 'Manual-Test/1.0',
            'original_url': 'https://indeed.com/manual-test',
            'job_title': 'Manual Test Job'
        }
        
        print(f"Inserting test event: {json.dumps(test_event, indent=2)}")
        
        result = client.table('click_events').insert([test_event]).execute()
        
        if result.data:
            print("✅ Manual database insert successful!")
            print(f"Inserted record: {result.data[0]}")
            return True
        else:
            print("❌ Manual insert failed - no data returned")
            
    except Exception as e:
        print(f"❌ Manual database insert failed: {e}")
    
    return False

def check_environment():
    """Check environment variables"""
    print("🔍 ENVIRONMENT CHECK:")
    print("=" * 60)
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:30]}...")
        else:
            print(f"❌ {var}: NOT SET")
    
    print()

def main():
    """Run all control tests"""
    print("🎯 CLICK TRACKING CONTROL TEST")
    print("=" * 60)
    print(f"Testing webhook: {TEST_WEBHOOK_URL}")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Check environment
    check_environment()
    
    # Run tests
    tests = [
        ("Webhook Endpoint Access", test_webhook_endpoint),
        ("Webhook POST Request", test_webhook_post),
        ("Supabase Direct Connection", test_supabase_direct),
        ("Manual Database Insert", test_manual_database_insert)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 CONTROL TEST RESULTS:")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All control tests passed!")
        print("The pipeline components work individually.")
        print("Issue may be in Short.io webhook configuration or link tagging.")
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed.")
        print("Fix the failing components before testing Short.io integration.")

if __name__ == "__main__":
    main()