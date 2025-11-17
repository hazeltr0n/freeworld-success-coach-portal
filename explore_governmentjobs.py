#!/usr/bin/env python3
"""
Explore GovernmentJobs.com site structure using Playwright
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def explore_governmentjobs():
    """Explore the GovernmentJobs.com website structure"""

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set to False to watch
        page = await browser.new_page()

        print("="*80)
        print("🔍 Exploring GovernmentJobs.com")
        print("="*80)

        # Visit homepage
        print("\n📍 Step 1: Loading homepage...")
        await page.goto("https://www.governmentjobs.com", wait_until="networkidle")
        await page.wait_for_timeout(2000)  # Wait 2 seconds

        # Take screenshot
        await page.screenshot(path="governmentjobs_homepage.png")
        print("✅ Screenshot saved: governmentjobs_homepage.png")

        # Examine page structure
        print("\n📋 Step 2: Examining page structure...")

        # Check for search form
        search_inputs = await page.query_selector_all('input[type="text"]')
        print(f"Found {len(search_inputs)} text input fields")

        # Look for search/filter elements
        buttons = await page.query_selector_all('button')
        print(f"Found {len(buttons)} buttons")

        links = await page.query_selector_all('a')
        print(f"Found {len(links)} links")

        # Try to find job search functionality
        print("\n🔎 Step 3: Looking for job search elements...")

        # Common search patterns
        search_selectors = [
            'input[placeholder*="search" i]',
            'input[name*="keyword" i]',
            'input[name*="location" i]',
            'input[id*="search" i]',
            '.search-input',
            '#search',
            '[data-search]'
        ]

        for selector in search_selectors:
            element = await page.query_selector(selector)
            if element:
                value = await element.get_attribute('placeholder') or await element.get_attribute('name') or await element.get_attribute('id')
                print(f"  ✓ Found: {selector} → {value}")

        # Try searching for "CDL driver" in Dallas
        print("\n🚛 Step 4: Attempting sample search (CDL driver in Dallas, TX)...")

        # Method 1: Try to find and fill keyword input
        keyword_input = await page.query_selector('input[placeholder*="keyword" i], input[name*="keyword" i], input[placeholder*="search" i]')
        location_input = await page.query_selector('input[placeholder*="location" i], input[name*="location" i], input[placeholder*="city" i]')

        if keyword_input and location_input:
            print("  ✓ Found keyword and location inputs")
            await keyword_input.fill("CDL driver")
            await location_input.fill("Dallas, TX")
            await page.wait_for_timeout(1000)

            # Try to find and click search button
            search_button = await page.query_selector('button[type="submit"], button:has-text("Search"), input[type="submit"]')
            if search_button:
                print("  ✓ Found search button, clicking...")
                await search_button.click()
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(2000)

                # Take screenshot of results
                await page.screenshot(path="governmentjobs_search_results.png")
                print("  ✅ Screenshot saved: governmentjobs_search_results.png")

                # Analyze results page
                print("\n📊 Step 5: Analyzing search results...")

                # Look for job listings
                job_cards = await page.query_selector_all('.job, .job-listing, [class*="job-card"], [data-job]')
                print(f"  Found {len(job_cards)} potential job cards")

                # Look for job titles
                job_titles = await page.query_selector_all('h2, h3, .job-title, [class*="title"]')
                print(f"  Found {len(job_titles)} potential job titles")

                # Extract a few sample job titles
                print("\n  📋 Sample job titles:")
                for i, title_elem in enumerate(job_titles[:5]):
                    try:
                        text = await title_elem.inner_text()
                        if text and len(text.strip()) > 0:
                            print(f"    {i+1}. {text.strip()[:80]}")
                    except:
                        pass

                # Look for pagination
                pagination = await page.query_selector_all('[class*="pagination"], [class*="pager"], .next, [aria-label*="next"]')
                print(f"\n  Found {len(pagination)} pagination elements")

                # Check current URL
                current_url = page.url
                print(f"\n  📍 Current URL: {current_url}")

            else:
                print("  ❌ Could not find search button")
                print("  Available buttons:")
                buttons = await page.query_selector_all('button')
                for i, button in enumerate(buttons[:10]):
                    text = await button.inner_text()
                    print(f"    {i+1}. {text.strip()}")
        else:
            print("  ❌ Could not find keyword or location inputs")
            print("\n  Available input fields:")
            inputs = await page.query_selector_all('input')
            for i, inp in enumerate(inputs[:10]):
                placeholder = await inp.get_attribute('placeholder') or 'N/A'
                name = await inp.get_attribute('name') or 'N/A'
                input_type = await inp.get_attribute('type') or 'N/A'
                print(f"    {i+1}. Type: {input_type}, Name: {name}, Placeholder: {placeholder}")

        # Check for any APIs or data endpoints
        print("\n🔌 Step 6: Checking for API endpoints...")
        print("  (Monitoring network requests...)")

        # Get page HTML for analysis
        html_content = await page.content()

        # Look for JSON data in page
        if 'application/json' in html_content or 'window.__INITIAL_STATE__' in html_content:
            print("  ✓ Found JSON data in page source")

        # Check for API calls
        if '/api/' in html_content or '/search' in html_content:
            print("  ✓ Found potential API endpoints in page source")

        print("\n✅ Exploration complete!")
        print("\nScreenshots saved:")
        print("  1. governmentjobs_homepage.png")
        print("  2. governmentjobs_search_results.png")

        # Keep browser open for 5 seconds to review
        print("\n⏳ Keeping browser open for 5 seconds for manual inspection...")
        await page.wait_for_timeout(5000)

        await browser.close()

if __name__ == "__main__":
    print("Starting GovernmentJobs.com exploration...")
    asyncio.run(explore_governmentjobs())
