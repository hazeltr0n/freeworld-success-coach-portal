#!/usr/bin/env python3
"""
Investigate the "Next Job" button on GovernmentJobs job detail pages
This could allow us to navigate between jobs without returning to search results
"""

import asyncio
from playwright.async_api import async_playwright
from urllib.parse import quote_plus

async def inspect_next_button():
    """Check if we can use the Next Job button to navigate efficiently"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("="*80)
        print("🔍 Investigating 'Next Job' Button Navigation")
        print("="*80)

        # Start with a search
        keyword = "CDL"
        location = "Dallas, TX"
        search_url = f"https://www.governmentjobs.com/jobs?keyword={quote_plus(keyword)}&location={quote_plus(location)}"

        print(f"\n📍 Step 1: Loading search results")
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)

        # Get first job link
        print("\n📍 Step 2: Finding first job...")
        all_links = await page.query_selector_all('a')

        first_job_url = None
        for link in all_links:
            try:
                text = await link.inner_text()
                href = await link.get_attribute('href')

                if (text and href and len(text.strip()) > 10 and
                    'category' not in href.lower() and
                    not any(skip in text.lower() for skip in ['privacy', 'login', 'sign'])):
                    if not href.startswith('http'):
                        href = f"https://www.governmentjobs.com{href}"
                    first_job_url = href
                    print(f"   ✓ Found: {text.strip()[:60]}")
                    break
            except:
                continue

        if not first_job_url:
            print("   ❌ No job found")
            await browser.close()
            return

        # Navigate to first job
        print(f"\n📍 Step 3: Opening first job")
        print(f"   URL: {first_job_url}")
        await page.goto(first_job_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(3000)

        # Look for Next Job button
        print("\n📍 Step 4: Looking for 'Next Job' button...")

        # Try various selectors for "Next" button
        next_button_selectors = [
            'a:has-text("Next Job")',
            'button:has-text("Next Job")',
            'a:has-text("Next")',
            'button:has-text("Next")',
            '[aria-label*="Next"]',
            '.next-job',
            '#next-job',
            'a[href*="next"]',
        ]

        next_button = None
        for selector in next_button_selectors:
            try:
                btn = await page.query_selector(selector)
                if btn:
                    text = await btn.inner_text()
                    print(f"   ✓ Found button: '{text}' using selector: {selector}")
                    next_button = btn
                    break
            except:
                continue

        if not next_button:
            print("   ❌ No 'Next Job' button found")
            print("\n   Let me search for all buttons on the page...")

            # List all buttons and links
            buttons = await page.query_selector_all('button, a')
            print(f"\n   Found {len(buttons)} buttons/links:")
            for i, btn in enumerate(buttons[:30]):  # Show first 30
                try:
                    text = await btn.inner_text()
                    tag = await btn.evaluate('el => el.tagName')
                    if text and text.strip():
                        print(f"      {i+1}. [{tag}] {text.strip()[:60]}")
                except:
                    pass

            await browser.close()
            return

        # Test clicking the Next button
        print(f"\n📍 Step 5: Testing 'Next Job' button...")

        # Get current URL before clicking
        current_url = page.url
        print(f"   Current URL: {current_url}")

        # Click the button
        await next_button.click()
        await page.wait_for_timeout(3000)

        # Check new URL
        new_url = page.url
        print(f"   New URL: {new_url}")

        if new_url != current_url:
            print(f"\n   ✅ SUCCESS! Navigation worked!")
            print(f"   We moved from one job to another without going back to search!")

            # Try to extract JSON-LD from new page
            print(f"\n📍 Step 6: Extracting JSON-LD from new page...")
            json_ld = await page.evaluate('''() => {
                const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                for (const script of scripts) {
                    try {
                        const data = JSON.parse(script.textContent);
                        if (data['@type'] === 'JobPosting') {
                            return data;
                        }
                    } catch (e) {}
                }
                return null;
            }''')

            if json_ld:
                print(f"   ✅ JSON-LD extracted successfully!")
                print(f"   Title: {json_ld.get('title', 'N/A')}")

                # Try clicking Next again
                print(f"\n📍 Step 7: Trying to click Next again...")
                next_button2 = await page.query_selector('a:has-text("Next Job"), button:has-text("Next Job"), a:has-text("Next")')
                if next_button2:
                    await next_button2.click()
                    await page.wait_for_timeout(3000)
                    print(f"   ✅ Clicked Next again! URL: {page.url}")
                    print(f"\n   💡 CONCLUSION: We can chain through jobs using Next button!")
                else:
                    print(f"   ⚠️  No Next button found on second page")
            else:
                print(f"   ❌ Could not extract JSON-LD")
        else:
            print(f"\n   ❌ URL didn't change - button might not work as expected")

        print("\n⏳ Keeping browser open for 10 seconds for inspection...")
        await page.wait_for_timeout(10000)

        await browser.close()

if __name__ == "__main__":
    print("Starting Next Job button investigation...")
    asyncio.run(inspect_next_button())
