#!/usr/bin/env python3
"""
Debug the exact token validation issue
"""

import requests
import json
import time

def test_with_debug():
    """Test with detailed debugging"""

    # The exact URL from Outscraper
    webhook_url = "https://yqbdltothngundojuebk.functions.supabase.co/outscraper-webhook?token=freeworld2024webhook"

    print("🔍 Debugging webhook token validation...")
    print(f"📍 URL: {webhook_url}")

    # Check what the URL parser sees
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(webhook_url)
    query_params = parse_qs(parsed.query)

    print(f"📋 Parsed URL components:")
    print(f"   Scheme: {parsed.scheme}")
    print(f"   Netloc: {parsed.netloc}")
    print(f"   Path: {parsed.path}")
    print(f"   Query: {parsed.query}")
    print(f"   Query params: {query_params}")

    # First test: Try a simple GET to see if the function responds
    print(f"\n🧪 Test 1: GET request (should return 405)")
    try:
        response = requests.get(webhook_url, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

    # Second test: POST with minimal payload
    print(f"\n🧪 Test 2: POST with minimal payload")
    minimal_payload = {"id": "test-minimal", "status": "SUCCESS"}

    try:
        response = requests.post(webhook_url, json=minimal_payload, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

    # Third test: POST with exact Outscraper format
    print(f"\n🧪 Test 3: POST with Outscraper format")
    outscraper_payload = {
        "id": f"debug-test-{int(time.time())}",
        "user_id": "debug-user",
        "status": "SUCCESS",
        "api_task": True,
        "results_location": "https://api.outscraper.cloud/requests/debug-test",
        "quota_usage": [{"product_name": "Google Maps Data", "quantity": 1}]
    }

    try:
        response = requests.post(webhook_url, json=outscraper_payload, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

    # Fourth test: Try different token formats
    print(f"\n🧪 Test 4: Different token formats")

    # Test with no token
    no_token_url = "https://yqbdltothngundojuebk.functions.supabase.co/outscraper-webhook"
    try:
        response = requests.post(no_token_url, json=minimal_payload, timeout=10)
        print(f"   No token - Status: {response.status_code}")
    except Exception as e:
        print(f"   No token - Error: {e}")

    # Test with wrong token
    wrong_token_url = "https://yqbdltothngundojuebk.functions.supabase.co/outscraper-webhook?token=wrongtoken"
    try:
        response = requests.post(wrong_token_url, json=minimal_payload, timeout=10)
        print(f"   Wrong token - Status: {response.status_code}")
    except Exception as e:
        print(f"   Wrong token - Error: {e}")

    # Test with token as header instead
    print(f"\n🧪 Test 5: Token as header")
    headers = {"Authorization": "Bearer freeworld2024webhook"}
    try:
        response = requests.post(no_token_url, json=minimal_payload, headers=headers, timeout=10)
        print(f"   Header token - Status: {response.status_code}")
    except Exception as e:
        print(f"   Header token - Error: {e}")

def check_function_logs():
    """Check if we can get function logs"""
    print(f"\n📋 Function Deployment Info:")
    print("=" * 50)

    # Check if function is listed
    try:
        import subprocess
        result = subprocess.run(['supabase', 'functions', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Functions list:")
            print(result.stdout)
        else:
            print("❌ Could not list functions")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error checking functions: {e}")

def main():
    """Run all debug tests"""
    print("🐛 Webhook Token Debug Session")
    print("=" * 60)

    test_with_debug()
    check_function_logs()

    print("\n" + "=" * 60)
    print("🎯 DEBUG COMPLETE")
    print("\nIf all tests show 401, the function might need:")
    print("1. Redeployment to clear cache")
    print("2. Environment variable check")
    print("3. Token validation logic review")

if __name__ == '__main__':
    main()