#!/usr/bin/env python3
"""
Sniff network traffic while you manually navigate to a specific job
"""

import json
from playwright.sync_api import sync_playwright

print("🎯 Network Sniffer - Navigate to a Specific Job")
print("=" * 80)
print()
print("Instructions:")
print("  1. Browser will open with DriverPulse loaded")
print("  2. Navigate to a specific job posting")
print("  3. All API calls will be captured and logged")
print("  4. Press Ctrl+C when done to see results")
print()
print("=" * 80)

# Storage for captured requests
captured_requests = []
captured_responses = []

def save_captured_data():
    """Save captured data to files"""
    with open('captured_job_requests.json', 'w') as f:
        json.dump(captured_requests, f, indent=2)
    with open('captured_job_responses.json', 'w') as f:
        json.dump(captured_responses, f, indent=2)

def handle_request(request):
    """Capture all requests"""
    url = request.url

    # Only capture tenstreet API calls
    if 'tenstreet.com' in url and ('js2php_transfer' in url or 'api' in url):
        req_data = {
            'url': url,
            'method': request.method,
            'headers': dict(request.headers),
            'post_data': request.post_data if request.method == 'POST' else None
        }
        captured_requests.append(req_data)
        print(f"\n📤 REQUEST: {request.method} {url}")
        if request.post_data:
            print(f"   POST data: {request.post_data[:200]}")

        # Save immediately
        save_captured_data()

def handle_response(response):
    """Capture all responses"""
    url = response.url

    # Only capture tenstreet API calls
    if 'tenstreet.com' in url and ('js2php_transfer' in url or 'api' in url):
        try:
            body = response.body()
            resp_data = {
                'url': url,
                'status': response.status,
                'headers': dict(response.headers),
                'body': body.decode('utf-8') if body else None
            }
            captured_responses.append(resp_data)
            print(f"\n📥 RESPONSE: {response.status} {url}")

            # Try to parse and show JSON
            if body:
                try:
                    json_body = json.loads(body)
                    print(f"   Response preview: {json.dumps(json_body, indent=2)[:500]}")
                except:
                    print(f"   Response (text): {body.decode('utf-8')[:200]}")

            # Save immediately
            save_captured_data()
        except Exception as e:
            print(f"   ⚠️  Could not capture response body: {e}")

with sync_playwright() as p:
    # Load auth cookies
    with open('/Users/freeworld_james/Development/Driver Pulse Scraper/auth.json', 'r') as f:
        auth_data = json.load(f)

    browser = p.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context()

    # Set cookies
    for cookie in auth_data['cookies']:
        context.add_cookies([{
            'name': cookie['name'],
            'value': cookie['value'],
            'domain': cookie['domain'],
            'path': cookie.get('path', '/')
        }])

    page = context.new_page()

    # Set up request/response listeners
    page.on('request', handle_request)
    page.on('response', handle_response)

    # Navigate to DriverPulse
    print("\n🌐 Loading DriverPulse...")
    page.goto('https://pulse.tenstreet.com', wait_until='networkidle')

    print("\n✅ DriverPulse loaded. You can now navigate to a specific job.")
    print("   All API calls will be captured and saved in REAL-TIME.")
    print("   Browser will auto-close after 90 seconds.\n")

    # Keep browser open for 90 seconds
    try:
        page.wait_for_timeout(90000)  # 90 seconds
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping capture...")
    except:
        pass

    browser.close()

# Final save
print("\n\n💾 Final save...")
save_captured_data()
print(f"✅ Saved {len(captured_requests)} requests to: captured_job_requests.json")
print(f"✅ Saved {len(captured_responses)} responses to: captured_job_responses.json")

# Print summary
print("\n\n📊 CAPTURE SUMMARY:")
print("=" * 80)
print(f"Total API calls captured: {len(captured_requests)}")

# Group by API function
api_functions = {}
for req in captured_requests:
    if 'misc_function=' in req['url']:
        func = req['url'].split('misc_function=')[1].split('&')[0]
        api_functions[func] = api_functions.get(func, 0) + 1

if api_functions:
    print("\nAPI functions called:")
    for func, count in api_functions.items():
        print(f"  - {func}: {count} times")

print("\n✅ All data saved. Check the JSON files for details.")
