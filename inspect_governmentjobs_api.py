#!/usr/bin/env python3
"""
Inspect GovernmentJobs.com for JavaScript APIs and data endpoints
Similar to how DriverPulse exposes window.__INITIAL_STATE__
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def inspect_api():
    """Look for JavaScript APIs, window objects, and network requests"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Track network requests
        api_requests = []

        async def log_request(request):
            if any(keyword in request.url.lower() for keyword in ['api', 'json', 'graphql', 'search', 'job']):
                api_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers)
                })
                print(f"📡 API Request: {request.method} {request.url}")

        page.on("request", log_request)

        print("="*80)
        print("🔍 Inspecting GovernmentJobs.com JavaScript API")
        print("="*80)

        # Navigate to job detail page
        job_url = "https://www.governmentjobs.com/jobs/4638897-0/youth-program-bus-driver"
        print(f"\n📍 Loading job detail page...")
        print(f"   URL: {job_url}")

        await page.goto(job_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)  # Wait for JavaScript to load

        print("\n🔎 Step 1: Looking for JavaScript window objects...")

        # Check for common API patterns like DriverPulse's window.__INITIAL_STATE__
        window_objects = await page.evaluate('''() => {
            const objects = {};

            // Check for common patterns
            const patterns = [
                '__INITIAL_STATE__',
                '__NEXT_DATA__',
                '__PRELOADED_STATE__',
                'INITIAL_DATA',
                'APP_DATA',
                'window.jobData',
                'window.job',
                'angular',
                'React',
                'Vue'
            ];

            // Check each pattern
            for (const pattern of patterns) {
                try {
                    const value = eval(pattern);
                    if (value !== undefined) {
                        objects[pattern] = typeof value === 'object' ?
                            JSON.stringify(value).substring(0, 200) :
                            String(value).substring(0, 200);
                    }
                } catch (e) {
                    // Pattern doesn't exist
                }
            }

            // List all window properties that might contain data
            const windowProps = [];
            for (const key in window) {
                if (key.startsWith('__') || key.toLowerCase().includes('data') ||
                    key.toLowerCase().includes('state') || key.toLowerCase().includes('job')) {
                    windowProps.push(key);
                }
            }
            objects['windowDataProps'] = windowProps.slice(0, 20);

            return objects;
        }''')

        print("\n  Window Objects Found:")
        for key, value in window_objects.items():
            print(f"    • {key}: {value}")

        print("\n🔎 Step 2: Looking for embedded JSON data in page...")

        # Look for JSON data in script tags
        json_scripts = await page.evaluate('''() => {
            const scripts = Array.from(document.querySelectorAll('script'));
            const jsonData = [];

            for (const script of scripts) {
                const content = script.textContent || script.innerHTML;

                // Look for JSON-like structures
                if (content.includes('{') && (
                    content.includes('"job"') ||
                    content.includes('"title"') ||
                    content.includes('"employer"') ||
                    content.includes('"location"') ||
                    content.includes('application/ld+json')
                )) {
                    jsonData.push({
                        type: script.type || 'text/javascript',
                        preview: content.substring(0, 300)
                    });
                }
            }

            return jsonData;
        }''')

        print(f"\n  Found {len(json_scripts)} script tags with potential JSON data:")
        for i, script in enumerate(json_scripts[:5]):  # Show first 5
            print(f"\n    Script {i+1} ({script['type']}):")
            print(f"    {script['preview'][:150]}...")

        print("\n🔎 Step 3: Checking for structured data (JSON-LD, microdata)...")

        # Look for structured data formats
        structured_data = await page.evaluate('''() => {
            const data = {
                jsonLd: [],
                microdata: [],
                opengraph: []
            };

            // JSON-LD
            const jsonLdScripts = document.querySelectorAll('script[type="application/ld+json"]');
            for (const script of jsonLdScripts) {
                try {
                    data.jsonLd.push(JSON.parse(script.textContent));
                } catch (e) {
                    // Invalid JSON
                }
            }

            // Microdata
            const itemScopes = document.querySelectorAll('[itemscope]');
            data.microdata.push(`Found ${itemScopes.length} itemscope elements`);

            // OpenGraph
            const ogTags = document.querySelectorAll('meta[property^="og:"]');
            for (const tag of ogTags) {
                data.opengraph.push({
                    property: tag.getAttribute('property'),
                    content: tag.getAttribute('content')
                });
            }

            return data;
        }''')

        if structured_data['jsonLd']:
            print("\n  ✅ JSON-LD structured data found!")
            for i, ld in enumerate(structured_data['jsonLd']):
                print(f"\n    JSON-LD {i+1}:")
                print(f"    {json.dumps(ld, indent=2)[:500]}...")

        if structured_data['opengraph']:
            print("\n  ✅ OpenGraph metadata found!")
            for og in structured_data['opengraph'][:5]:
                print(f"    {og['property']}: {og['content']}")

        print("\n🔎 Step 4: Network requests captured:")
        print(f"\n  Found {len(api_requests)} API-related requests:")
        for req in api_requests[:10]:  # Show first 10
            print(f"    {req['method']} {req['url']}")

        print("\n🔎 Step 5: Attempting to extract job data directly from JavaScript...")

        # Try to find the actual job data object
        job_data_js = await page.evaluate('''() => {
            // Try common patterns
            const attempts = [];

            // Pattern 1: Look for data attributes
            const mainContent = document.querySelector('[data-job-id], [data-job]');
            if (mainContent) {
                attempts.push({
                    method: 'data-attributes',
                    found: true,
                    data: mainContent.dataset
                });
            }

            // Pattern 2: Look for React props
            const reactRoot = document.querySelector('[data-reactroot], #root, [id*="react"]');
            if (reactRoot) {
                attempts.push({
                    method: 'react-root',
                    found: true
                });
            }

            // Pattern 3: Check for Vue
            if (typeof Vue !== 'undefined') {
                attempts.push({
                    method: 'vue',
                    found: true
                });
            }

            // Pattern 4: Check for Angular
            const angularElements = document.querySelectorAll('[ng-app], [ng-controller]');
            if (angularElements.length > 0) {
                attempts.push({
                    method: 'angular',
                    found: true,
                    count: angularElements.length
                });
            }

            return attempts;
        }''')

        print("\n  Framework detection:")
        for attempt in job_data_js:
            print(f"    • {attempt['method']}: {attempt}")

        # Save everything to file
        report = {
            'timestamp': datetime.now().isoformat(),
            'url': job_url,
            'window_objects': window_objects,
            'json_scripts_count': len(json_scripts),
            'structured_data': structured_data,
            'api_requests': api_requests,
            'framework_detection': job_data_js
        }

        with open('governmentjobs_api_inspection.json', 'w') as f:
            json.dump(report, f, indent=2)

        print("\n✅ Full report saved to: governmentjobs_api_inspection.json")

        print("\n⏳ Keeping browser open for 5 seconds...")
        await page.wait_for_timeout(5000)

        await browser.close()

if __name__ == "__main__":
    print("Starting GovernmentJobs.com API inspection...")
    asyncio.run(inspect_api())
