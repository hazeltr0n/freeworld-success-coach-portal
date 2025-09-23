#!/usr/bin/env python3
"""
Test the real Outscraper webhook with actual payload format
"""

import requests
import json
import time
from datetime import datetime

def test_webhook_site():
    """Test with webhook.site first to see the payload structure"""
    test_url = "https://webhook.site/f339d7fa-194e-4996-89b0-415e1dc7348e"

    # Real Outscraper payload format
    test_payload = {
        "id": f"test-request-{int(time.time())}",
        "user_id": "test-user-123",
        "status": "SUCCESS",
        "api_task": True,
        "results_location": f"https://api.outscraper.cloud/requests/test-request-{int(time.time())}",
        "quota_usage": [
            {
                "product_name": "Google Maps Data",
                "quantity": 1
            }
        ]
    }

    print("🧪 Testing with webhook.site...")
    print(f"📤 Sending to: {test_url}")
    print(f"📋 Payload: {json.dumps(test_payload, indent=2)}")

    try:
        response = requests.post(test_url, json=test_payload, timeout=10)
        print(f"📬 Response: {response.status_code}")

        if response.status_code == 200:
            print("✅ webhook.site received the payload successfully")
            print("🔗 Check https://webhook.site/#!/view/f339d7fa-194e-4996-89b0-415e1dc7348e to see the request")
            return True
        else:
            print(f"❌ webhook.site returned {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error testing webhook.site: {e}")
        return False

def test_real_supabase_webhook():
    """Test the real Supabase webhook URL"""
    real_url = "https://yqbdltothngundojuebk.functions.supabase.co/outscraper-webhook?token=freeworld2024webhook"

    # Real Outscraper payload format
    test_payload = {
        "id": f"test-request-{int(time.time())}",
        "user_id": "test-user-123",
        "status": "SUCCESS",
        "api_task": True,
        "results_location": f"https://api.outscraper.cloud/requests/test-request-{int(time.time())}",
        "quota_usage": [
            {
                "product_name": "Google Maps Data",
                "quantity": 1
            }
        ]
    }

    print(f"\n🧪 Testing real Supabase webhook...")
    print(f"📤 Sending to: {real_url}")
    print(f"📋 Payload: {json.dumps(test_payload, indent=2)}")

    try:
        response = requests.post(real_url, json=test_payload, timeout=15)
        print(f"📬 Response: {response.status_code}")

        if response.status_code == 200:
            print("✅ Supabase webhook responded successfully")
            try:
                result = response.json()
                print(f"📄 Response body: {json.dumps(result, indent=2)}")
            except:
                print(f"📄 Response text: {response.text}")
            return True
        elif response.status_code == 401:
            print("❌ 401 Unauthorized - Token authentication failed")
            print("🔍 This is the error Outscraper is seeing")
            return False
        elif response.status_code == 404:
            print("❌ 404 Not Found - Function doesn't exist or wrong path")
            return False
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            try:
                print(f"📄 Response: {response.text}")
            except:
                pass
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Function might not exist")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
        return False
    except Exception as e:
        print(f"❌ Error testing Supabase webhook: {e}")
        return False

def analyze_token_issue():
    """Analyze the token authentication issue"""
    print(f"\n🔍 Analyzing token authentication...")

    # The URL has token as query parameter
    url_parts = "https://yqbdltothngundojuebk.functions.supabase.co/outscraper-webhook?token=freeworld2024webhook"

    print("📋 Current webhook URL breakdown:")
    print(f"   Base URL: https://yqbdltothngundojuebk.functions.supabase.co/outscraper-webhook")
    print(f"   Token: freeworld2024webhook (as query parameter)")

    print("\n🎯 Possible issues:")
    print("1. The outscraper-webhook function doesn't exist in Supabase")
    print("2. The function exists but doesn't handle the token parameter correctly")
    print("3. The function expects a different authentication method")
    print("4. The token value is incorrect")

    print("\n💡 Solutions to try:")
    print("1. Create the missing outscraper-webhook Supabase Edge Function")
    print("2. Update the function to properly validate the token parameter")
    print("3. Verify the token matches what the function expects")

def main():
    """Run webhook tests"""
    print("🔍 Real Outscraper Webhook Testing")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Test with webhook.site first
    webhook_site_success = test_webhook_site()

    # Test real Supabase webhook
    supabase_success = test_real_supabase_webhook()

    # Analyze the issue
    analyze_token_issue()

    print("\n" + "=" * 50)
    print("🎯 TEST SUMMARY:")
    print(f"   webhook.site: {'✅ SUCCESS' if webhook_site_success else '❌ FAILED'}")
    print(f"   Supabase webhook: {'✅ SUCCESS' if supabase_success else '❌ FAILED'}")

    if not supabase_success:
        print("\n🚨 ISSUE CONFIRMED: Supabase webhook is failing")
        print("📋 Next steps:")
        print("1. Create the missing outscraper-webhook Edge Function")
        print("2. Deploy it to Supabase")
        print("3. Test again")

    return supabase_success

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)