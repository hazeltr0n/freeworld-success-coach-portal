#!/usr/bin/env python3
"""
Capture the EXACT API call that DriverPulse makes when you change experience filters
"""
from playwright.sync_api import sync_playwright
import json
import time

print("🔍 DriverPulse Experience Filter API Capture")
print("=" * 60)

all_requests = []

def log_request(request):
    """Capture ALL requests"""
    if 'tenstreet.com' in request.url:
        req_data = {
            'url': request.url,
            'method': request.method,
            'post_data': request.post_data if request.method == 'POST' else None,
            'timestamp': time.time()
        }
        all_requests.append(req_data)

        # Print in real-time
        print(f"\n📡 {request.method} {request.url.split('?')[0]}")
        if request.post_data:
            print(f"   POST: {request.post_data[:200]}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()

    # Load auth
    try:
        with open('auth.json', 'r') as f:
            auth_data = json.load(f)
            if auth_data.get('cookies'):
                context.add_cookies(auth_data['cookies'])
    except:
        print("⚠️  No auth - manual login required")

    page = context.new_page()
    page.on('request', log_request)

    try:
        print("\n🌐 Loading DriverPulse...")
        page.goto("https://pulse.tenstreet.com", wait_until="networkidle")
        time.sleep(3)

        print("\n" + "=" * 60)
        print("🎯 PLEASE DO THIS:")
        print("=" * 60)
        print("1. Go to the Search/Jobs page in the app")
        print("2. Click the Experience dropdown")
        print("3. Select 'No CDL'")
        print("4. Wait for results to load")
        print("5. Click Experience dropdown again")
        print("6. Select '(CDL) 0-6 month'")
        print("7. Wait for results to load")
        print("\nI'll capture ALL API calls for the next 5 MINUTES")
        print("=" * 60)

        # Wait 5 minutes for user interaction
        time.sleep(300)

        print("\n" + "=" * 60)
        print(f"📊 CAPTURED {len(all_requests)} API CALLS")
        print("=" * 60)

        # Show all unique endpoint patterns
        endpoints = {}
        for req in all_requests:
            url_parts = req['url'].split('?')
            base = url_parts[0]
            if 'misc_function' in req['url']:
                func = [p for p in url_parts[1].split('&') if 'misc_function' in p][0]
                key = f"{base}?{func}"
            else:
                key = base

            if key not in endpoints:
                endpoints[key] = []
            endpoints[key].append(req)

        print("\nUnique endpoints called:")
        for endpoint, reqs in endpoints.items():
            print(f"\n{endpoint}")
            print(f"  Called {len(reqs)} times")
            if reqs[0]['post_data']:
                print(f"  Sample POST: {reqs[0]['post_data'][:150]}")

        # Save everything
        with open('filter_api_capture.json', 'w') as f:
            json.dump(all_requests, f, indent=2)

        print(f"\n💾 Saved to filter_api_capture.json")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        input("\n🔍 Press Enter to close...")
        browser.close()
