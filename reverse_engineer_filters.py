#!/usr/bin/env python3
"""
Reverse engineer how DriverPulse experience filters actually work
"""

from playwright.sync_api import sync_playwright
import json
import time
from urllib.parse import parse_qs, unquote

def capture_filter_requests():
    """Capture actual API requests when changing experience filters"""

    print("🔍 Reverse Engineering DriverPulse Experience Filters")
    print("=" * 60)

    all_requests = []

    def log_request(request):
        """Capture ALL requests with POST data"""
        if request.method == 'POST' and request.post_data:
            all_requests.append({
                'url': request.url,
                'post_data': request.post_data,
                'timestamp': time.time()
            })

            # Print in real-time
            print(f"\n📡 {request.url}")
            print(f"   Data: {request.post_data[:300]}")

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
            print("⚠️  No auth found - manual login required")

        page = context.new_page()
        page.on('request', log_request)

        try:
            # Navigate
            print("\n🌐 Loading DriverPulse...")
            page.goto("https://pulse.tenstreet.com", wait_until="networkidle")
            time.sleep(3)

            # Get localStorage before any changes
            print("\n📦 Initial localStorage:")
            initial_storage = page.evaluate("() => Object.assign({}, window.localStorage)")
            for key, value in initial_storage.items():
                if 'filter' in key.lower() or 'preference' in key.lower() or 'experience' in key.lower():
                    print(f"  {key}: {value[:200] if len(str(value)) > 200 else value}")

            print("\n" + "=" * 60)
            print("🎯 INSTRUCTIONS:")
            print("=" * 60)
            print("1. Click on the Experience dropdown")
            print("2. Select 'No CDL'")
            print("3. Wait 5 seconds")
            print("4. Select '(CDL) 0-6 month'")
            print("5. Wait 5 seconds")
            print("6. I'll capture all API calls")
            print("\nWaiting 5 minutes (300 seconds)...")
            print("=" * 60)

            time.sleep(300)

            # Get localStorage after changes
            print("\n📦 Final localStorage:")
            final_storage = page.evaluate("() => Object.assign({}, window.localStorage)")
            for key, value in final_storage.items():
                if 'filter' in key.lower() or 'preference' in key.lower() or 'experience' in key.lower():
                    if key not in initial_storage or initial_storage[key] != value:
                        print(f"  🆕 {key}: {value[:200] if len(str(value)) > 200 else value}")

            # Analyze captured requests
            print("\n" + "=" * 60)
            print("📊 CAPTURED API CALLS")
            print("=" * 60)

            for i, req in enumerate(all_requests, 1):
                print(f"\n{i}. {req['url']}")

                # Try to parse as form data
                try:
                    params = parse_qs(req['post_data'])
                    print("  Parsed parameters:")
                    for k, v in params.items():
                        # Decode URL-encoded values
                        decoded_v = [unquote(x) for x in v]
                        print(f"    {k}: {decoded_v}")
                except:
                    print(f"  Raw: {req['post_data'][:500]}")

            # Save everything
            results = {
                'initial_storage': initial_storage,
                'final_storage': final_storage,
                'api_calls': all_requests
            }

            with open('filter_reverse_engineering.json', 'w') as f:
                json.dump(results, f, indent=2)

            print(f"\n💾 Saved to filter_reverse_engineering.json")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            input("\n🔍 Press Enter to close...")
            browser.close()

if __name__ == "__main__":
    capture_filter_requests()
