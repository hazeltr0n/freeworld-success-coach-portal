#!/usr/bin/env python3
"""
Inspect DriverPulse localStorage, sessionStorage, and cookies to find filter params
"""

from driver_pulse_source import DriverPulseSource
from playwright.sync_api import sync_playwright
import json
import time

def inspect_storage():
    """Inspect browser storage for filter parameter hints"""

    print("🔍 DriverPulse Storage & Filter Inspection")
    print("=" * 60)

    source = DriverPulseSource()
    source.load_authentication()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        # Load cookies from auth
        auth_data = None
        try:
            import json
            with open('auth.json', 'r') as f:
                auth_data = json.load(f)
        except:
            print("⚠️ Could not load auth.json - you'll need to login manually")

        if auth_data and auth_data.get('cookies'):
            context.add_cookies(auth_data['cookies'])

        page = context.new_page()

        # Capture network requests
        api_calls = []

        def log_request(request):
            if 'js2php_transfer' in request.url:
                api_calls.append({
                    'url': request.url,
                    'method': request.method,
                    'post_data': request.post_data
                })

        page.on('request', log_request)

        try:
            # Navigate
            print("\n🌐 Loading DriverPulse...")
            page.goto("https://pulse.tenstreet.com", wait_until="networkidle")
            time.sleep(5)

            # Extract localStorage
            print("\n📦 LocalStorage Contents:")
            print("=" * 60)
            local_storage = page.evaluate("() => Object.assign({}, window.localStorage)")
            for key, value in local_storage.items():
                print(f"  {key}: {value[:100] if len(str(value)) > 100 else value}")

            # Extract sessionStorage
            print("\n📦 SessionStorage Contents:")
            print("=" * 60)
            session_storage = page.evaluate("() => Object.assign({}, window.sessionStorage)")
            for key, value in session_storage.items():
                print(f"  {key}: {value[:100] if len(str(value)) > 100 else value}")

            # Try to find filter-related elements
            print("\n🔍 Looking for filter input elements...")
            print("=" * 60)

            # Find experience dropdown
            try:
                exp_dropdown = page.query_selector('[name*="experience"], [id*="experience"], select:has-text("CDL")')
                if exp_dropdown:
                    exp_name = exp_dropdown.get_attribute('name')
                    exp_id = exp_dropdown.get_attribute('id')
                    print(f"  Experience dropdown found:")
                    print(f"    Name: {exp_name}")
                    print(f"    ID: {exp_id}")

                    # Get options
                    options = page.query_selector_all(f'#{exp_id} option') if exp_id else []
                    print(f"    Options:")
                    for opt in options:
                        val = opt.get_attribute('value')
                        text = opt.inner_text()
                        print(f"      value='{val}' → '{text}'")
            except Exception as e:
                print(f"  Could not inspect experience dropdown: {e}")

            # Wait and let user interact
            print("\n⏳ Please interact with the filters in the browser...")
            print("   Change the Experience dropdown and other filters")
            print("   Waiting 60 seconds...")
            time.sleep(60)

            # Check localStorage again after interaction
            print("\n📦 LocalStorage After Interaction:")
            print("=" * 60)
            local_storage_after = page.evaluate("() => Object.assign({}, window.localStorage)")
            for key, value in local_storage_after.items():
                if key not in local_storage or local_storage[key] != value:
                    print(f"  🆕 {key}: {value}")

            # Show captured API calls
            print("\n📡 Captured API Calls:")
            print("=" * 60)
            for call in api_calls:
                print(f"\n{call['method']} {call['url']}")
                if call['post_data']:
                    # Try to parse as form data
                    try:
                        from urllib.parse import parse_qs
                        params = parse_qs(call['post_data'])
                        print("  Parameters:")
                        for k, v in params.items():
                            print(f"    {k}: {v}")
                    except:
                        print(f"  Data: {call['post_data'][:200]}")

            # Save results
            results = {
                'localStorage': local_storage_after,
                'sessionStorage': session_storage,
                'apiCalls': api_calls
            }

            with open('driver_pulse_inspection.json', 'w') as f:
                json.dump(results, f, indent=2)

            print(f"\n💾 Saved inspection results to driver_pulse_inspection.json")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            print("\n🔍 Press Enter to close browser...")
            input()
            browser.close()

if __name__ == "__main__":
    inspect_storage()
