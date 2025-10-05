#!/usr/bin/env python3
"""
Inspect DriverPulse filter API calls using Playwright
"""

from playwright.sync_api import sync_playwright
import json
import time

def inspect_experience_filter():
    """Monitor network traffic to see how experience filters work"""

    print("🔍 DriverPulse Filter API Inspection")
    print("=" * 60)

    captured_requests = []

    def log_request(request):
        """Log API requests"""
        if 'js2php_transfer' in request.url or 'search' in request.url.lower():
            captured_requests.append({
                'url': request.url,
                'method': request.method,
                'post_data': request.post_data if request.method == 'POST' else None,
                'headers': dict(request.headers)
            })
            print(f"\n📡 API Call: {request.method} {request.url}")
            if request.post_data:
                print(f"   POST Data: {request.post_data[:200]}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Monitor network requests
        page.on('request', log_request)

        try:
            # Navigate to DriverPulse
            print("\n🌐 Loading DriverPulse...")
            page.goto("https://pulse.tenstreet.com", wait_until="networkidle")

            # Click Next
            print("\n🔘 Clicking Next...")
            page.click('div[onclick]:has-text("NEXT")')
            time.sleep(2)

            # Fill login form (you'll need to provide credentials)
            print("\n📝 Please log in manually in the browser window...")
            print("   Then interact with the Experience dropdown to see API calls")
            print("\n⏳ Waiting 120 seconds for you to:")
            print("   1. Complete login")
            print("   2. Change the Experience filter dropdown")
            print("   3. Observe the network calls being logged here")

            # Wait for manual interaction
            time.sleep(120)

            # Save captured requests
            print("\n" + "=" * 60)
            print("📊 CAPTURED API CALLS")
            print("=" * 60)

            for i, req in enumerate(captured_requests, 1):
                print(f"\n{i}. {req['method']} {req['url']}")
                if req['post_data']:
                    print(f"   POST Data: {req['post_data']}")

            # Save to file
            with open('driver_pulse_api_calls.json', 'w') as f:
                json.dump(captured_requests, f, indent=2)

            print(f"\n💾 Saved {len(captured_requests)} API calls to driver_pulse_api_calls.json")

        except Exception as e:
            print(f"❌ Error: {e}")

        finally:
            browser.close()

if __name__ == "__main__":
    inspect_experience_filter()
