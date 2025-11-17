#!/usr/bin/env python3
"""
Deep inspection of GovernmentJobs.com to find API endpoints for search results
Looking for internal APIs that power the search page
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from urllib.parse import quote_plus

async def inspect_search_api():
    """
    Monitor network traffic during search to find API endpoints
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Track ALL network requests
        all_requests = []
        api_requests = []

        async def log_request(request):
            req_info = {
                'url': request.url,
                'method': request.method,
                'resource_type': request.resource_type,
                'headers': dict(request.headers)
            }
            all_requests.append(req_info)

            # Flag potential API calls
            if any(keyword in request.url.lower() for keyword in ['api', 'json', 'search', 'query', 'jobs', 'xhr']):
                api_requests.append(req_info)
                print(f"\n🔍 Potential API: {request.method} {request.url}")
                print(f"   Type: {request.resource_type}")

        async def log_response(response):
            # Only log responses for potential API calls
            if any(keyword in response.url.lower() for keyword in ['api', 'json', 'search', 'query', 'jobs']):
                try:
                    content_type = response.headers.get('content-type', '')
                    print(f"\n📥 Response: {response.url}")
                    print(f"   Status: {response.status}")
                    print(f"   Content-Type: {content_type}")

                    # Try to get response body if it's JSON
                    if 'json' in content_type.lower():
                        try:
                            body = await response.json()
                            print(f"   JSON Preview: {json.dumps(body, indent=2)[:500]}...")
                        except:
                            pass
                except Exception as e:
                    pass

        page.on("request", log_request)
        page.on("response", log_response)

        print("="*80)
        print("🔍 Inspecting GovernmentJobs.com Search API")
        print("="*80)

        # Build search URL
        keyword = "CDL"
        location = "Dallas, TX"
        search_url = f"https://www.governmentjobs.com/jobs?keyword={quote_plus(keyword)}&location={quote_plus(location)}"

        print(f"\n📍 Loading search results: {search_url}\n")

        await page.goto(search_url, wait_until="networkidle", timeout=30000)

        print("\n" + "="*80)
        print("⏸️  Pausing to capture any lazy-loaded API calls...")
        print("="*80)

        # Scroll to trigger any lazy loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)

        # Try clicking "next page" to see if it triggers an API call
        print("\n" + "="*80)
        print("🔄 Looking for pagination API calls...")
        print("="*80)

        try:
            next_button = await page.query_selector('a:has-text("Next"), a[aria-label="Next"]')
            if next_button:
                print("   Found Next button, clicking...")
                await next_button.click()
                await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"   No pagination button found: {e}")

        # Check for any exposed JavaScript objects/functions
        print("\n" + "="*80)
        print("🔎 Checking for exposed JavaScript APIs...")
        print("="*80)

        js_apis = await page.evaluate('''() => {
            const apis = {};

            // Check for common API patterns
            const patterns = [
                'fetch',
                'axios',
                'XMLHttpRequest',
                '__INITIAL_STATE__',
                '__NEXT_DATA__',
                'jobsData',
                'searchData',
                'window.jobs',
                'window.search'
            ];

            // Look for any global functions that might be search-related
            const searchFunctions = [];
            for (const key in window) {
                if (typeof window[key] === 'function' &&
                    (key.toLowerCase().includes('search') ||
                     key.toLowerCase().includes('job') ||
                     key.toLowerCase().includes('fetch'))) {
                    searchFunctions.push(key);
                }
            }
            apis['searchFunctions'] = searchFunctions;

            // Look for data objects
            const dataObjects = [];
            for (const key in window) {
                if (typeof window[key] === 'object' &&
                    window[key] !== null &&
                    (key.toLowerCase().includes('data') ||
                     key.toLowerCase().includes('state'))) {
                    dataObjects.push(key);
                }
            }
            apis['dataObjects'] = dataObjects;

            // Check if there's a React or Vue app
            if (document.querySelector('[data-reactroot]')) {
                apis['framework'] = 'React';
            } else if (document.querySelector('[data-v-]')) {
                apis['framework'] = 'Vue';
            }

            return apis;
        }''')

        print("\n  Exposed JavaScript APIs:")
        print(f"    Framework: {js_apis.get('framework', 'Unknown')}")
        print(f"    Search Functions: {js_apis.get('searchFunctions', [])}")
        print(f"    Data Objects: {js_apis.get('dataObjects', [])}")

        # Look for GraphQL endpoints
        print("\n" + "="*80)
        print("🔎 Checking for GraphQL...")
        print("="*80)

        graphql_requests = [r for r in api_requests if 'graphql' in r['url'].lower()]
        if graphql_requests:
            print(f"   ✅ Found {len(graphql_requests)} GraphQL requests!")
            for req in graphql_requests:
                print(f"      {req['method']} {req['url']}")
        else:
            print("   ❌ No GraphQL endpoints found")

        # Summary
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)
        print(f"\nTotal requests captured: {len(all_requests)}")
        print(f"Potential API requests: {len(api_requests)}")

        print("\n🎯 Top API candidates:")
        for i, req in enumerate(api_requests[:10], 1):
            print(f"\n{i}. {req['method']} {req['url']}")
            print(f"   Resource Type: {req['resource_type']}")

        # Save full report
        report = {
            'timestamp': datetime.now().isoformat(),
            'search_url': search_url,
            'total_requests': len(all_requests),
            'api_requests': api_requests,
            'javascript_apis': js_apis,
            'all_requests': all_requests
        }

        with open('governmentjobs_search_api_inspection.json', 'w') as f:
            json.dump(report, f, indent=2)

        print("\n✅ Full report saved to: governmentjobs_search_api_inspection.json")

        print("\n⏳ Keeping browser open for 10 seconds for manual inspection...")
        await page.wait_for_timeout(10000)

        await browser.close()

if __name__ == "__main__":
    print("Starting GovernmentJobs.com search API inspection...")
    asyncio.run(inspect_search_api())
