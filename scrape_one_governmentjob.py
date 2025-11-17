#!/usr/bin/env python3
"""
Scrape ONE job from GovernmentJobs.com to understand data structure
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from urllib.parse import quote_plus

async def scrape_one_job():
    """Scrape a single job to understand the data structure"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("="*80)
        print("🔍 Scraping ONE Job from GovernmentJobs.com")
        print("="*80)

        # Build search URL directly (no form submission needed!)
        keyword = "CDL driver"
        location = "Dallas, TX"

        search_url = f"https://www.governmentjobs.com/jobs?keyword={quote_plus(keyword)}&location={quote_plus(location)}"

        print(f"\n📍 Step 1: Loading search results...")
        print(f"   URL: {search_url}")

        await page.goto(search_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)  # Wait for JavaScript to render

        # Take screenshot
        await page.screenshot(path="governmentjobs_results.png")
        print("✅ Screenshot saved: governmentjobs_results.png")

        # Find all job listing links/cards
        print("\n🔎 Step 2: Looking for job listings...")

        # Wait for job results to load
        await page.wait_for_timeout(2000)

        # Try to find job title links - these are the blue linked job titles
        job_links = []

        # Strategy 1: Look for any link that contains common job-related text
        print("  🔍 Strategy 1: Looking for job title links...")
        all_links = await page.query_selector_all('a')
        print(f"  Found {len(all_links)} total links on page")

        for link in all_links:
            try:
                text = await link.inner_text()
                href = await link.get_attribute('href')

                # Skip if no text or href
                if not text or not href:
                    continue

                text = text.strip()

                # Look for job-like titles (contains "driver", has reasonable length, etc.)
                is_job_link = (
                    len(text) > 10 and  # Job titles are usually longer than 10 chars
                    len(text) < 150 and  # But not too long
                    ('driver' in text.lower() or 'cdl' in text.lower()) and  # Contains relevant keywords
                    not any(skip in text.lower() for skip in ['privacy', 'login', 'sign', 'create', 'forgot', 'reset', 'resources']) and  # Skip nav links
                    'category[' not in href  # Skip category filter links
                )

                if is_job_link:
                    job_links.append((href, text))
                    print(f"    ✓ Found: {text[:60]}")

                if len(job_links) >= 5:  # Get first 5 job links
                    break

            except Exception as e:
                continue

        if not job_links:
            print("\n❌ Could not find any job links!")
            print("\nDumping all links with text for debugging:")
            for i, link in enumerate(all_links[:30]):
                try:
                    href = await link.get_attribute('href') or 'N/A'
                    text = await link.inner_text()
                    if text and text.strip():
                        print(f"  {i+1}. {text.strip()[:60]} → {href[:80]}")
                except:
                    pass

            await browser.close()
            return

        # Filter out category links (contain 'category' in URL)
        real_job_links = [(url, title) for url, title in job_links if 'category' not in url.lower()]

        if not real_job_links:
            print("\n❌ All links were category filters!")
            await browser.close()
            return

        # Pick the first REAL job
        first_job_url, first_job_title = real_job_links[0]
        if not first_job_url.startswith('http'):
            first_job_url = f"https://www.governmentjobs.com{first_job_url}"

        print(f"\n✅ Found {len(job_links)} job links!")
        print(f"📄 Opening first job: {first_job_title}")
        print(f"   URL: {first_job_url}")

        # Navigate to job detail page
        print("\n📍 Step 3: Loading job detail page...")
        await page.goto(first_job_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)  # Wait for JavaScript to render

        # Take screenshot
        await page.screenshot(path="governmentjobs_job_detail.png")
        print("✅ Screenshot saved: governmentjobs_job_detail.png")

        # Extract job data
        print("\n📊 Step 4: Extracting job data...")

        job_data = {
            "url": first_job_url,
            "scraped_at": datetime.now().isoformat()
        }

        # Title - use JavaScript to find the FIRST h1 that's not "log in"
        title_value = await page.evaluate('''() => {
            const h1s = Array.from(document.querySelectorAll('h1'));
            for (const h1 of h1s) {
                const text = h1.textContent.trim();
                // Skip "log in" and other non-title text
                if (text && text.toLowerCase() !== 'log in' && text.length > 10) {
                    return text;
                }
            }
            return null;
        }''')

        if title_value:
            job_data['title'] = title_value
            print(f"  ✓ Title: {job_data['title']}")

        # Get all text on page to find labeled fields
        page_text = await page.content()

        # Use JavaScript to get text content of elements next to labels
        # This is more reliable than trying multiple CSS selectors

        # Extract labeled fields using a more robust JavaScript approach
        # Employer
        employer_value = await page.evaluate('''() => {
            const dts = Array.from(document.querySelectorAll('dt'));
            for (const dt of dts) {
                if (dt.textContent.trim() === 'Employer') {
                    let dd = dt.nextElementSibling;
                    while (dd && dd.tagName !== 'DD') {
                        dd = dd.nextElementSibling;
                    }
                    if (dd) {
                        return dd.textContent.trim();
                    }
                }
            }
            return null;
        }''')
        if employer_value:
            job_data['employer'] = employer_value
            print(f"  ✓ Employer: {job_data['employer']}")

        # Location
        location_value = await page.evaluate('''() => {
            const dts = Array.from(document.querySelectorAll('dt'));
            for (const dt of dts) {
                if (dt.textContent.trim() === 'Location') {
                    let dd = dt.nextElementSibling;
                    while (dd && dd.tagName !== 'DD') {
                        dd = dd.nextElementSibling;
                    }
                    if (dd) {
                        return dd.textContent.trim();
                    }
                }
            }
            return null;
        }''')
        if location_value:
            job_data['location'] = location_value
            print(f"  ✓ Location: {job_data['location']}")

        # Salary
        salary_value = await page.evaluate('''() => {
            const dts = Array.from(document.querySelectorAll('dt'));
            for (const dt of dts) {
                if (dt.textContent.trim() === 'Salary') {
                    let dd = dt.nextElementSibling;
                    while (dd && dd.tagName !== 'DD') {
                        dd = dd.nextElementSibling;
                    }
                    if (dd) {
                        return dd.textContent.trim();
                    }
                }
            }
            return null;
        }''')
        if salary_value:
            job_data['salary'] = salary_value
            print(f"  ✓ Salary: {job_data['salary']}")

        # Description - get the FULL description section (everything under the DESCRIPTION tab)
        # Look for the description tab content
        desc_elem = await page.query_selector('[role="tabpanel"]')
        if not desc_elem:
            # Try finding the content div after DESCRIPTION tab
            desc_elem = await page.query_selector('.job-description, [class*="description"]')

        if desc_elem:
            desc_text = await desc_elem.inner_text()
            if desc_text and len(desc_text.strip()) > 50:
                job_data['description'] = desc_text.strip()  # Get FULL description
                print(f"  ✓ Description: {len(job_data['description'])} characters")

        # Opening Date
        opening_date = await page.evaluate('''() => {
            const dts = Array.from(document.querySelectorAll('dt'));
            for (const dt of dts) {
                if (dt.textContent.trim() === 'Opening Date') {
                    let dd = dt.nextElementSibling;
                    while (dd && dd.tagName !== 'DD') {
                        dd = dd.nextElementSibling;
                    }
                    if (dd) {
                        return dd.textContent.trim();
                    }
                }
            }
            return null;
        }''')
        if opening_date:
            job_data['posted_date'] = opening_date
            print(f"  ✓ Posted Date: {job_data['posted_date']}")

        # Closing Date
        closing_date = await page.evaluate('''() => {
            const dts = Array.from(document.querySelectorAll('dt'));
            for (const dt of dts) {
                if (dt.textContent.trim() === 'Closing Date') {
                    let dd = dt.nextElementSibling;
                    while (dd && dd.tagName !== 'DD') {
                        dd = dd.nextElementSibling;
                    }
                    if (dd) {
                        return dd.textContent.trim();
                    }
                }
            }
            return null;
        }''')
        if closing_date:
            job_data['deadline'] = closing_date
            print(f"  ✓ Closing Date: {job_data['deadline']}")

        # Apply Button - look for the green "APPLY" button
        apply_btn = await page.query_selector('a:has-text("APPLY"), button:has-text("APPLY")')
        if apply_btn:
            # The apply URL is typically the current page URL with an apply action
            job_data['apply_url'] = first_job_url
            print(f"  ✓ Apply URL: {job_data['apply_url']}")

        print("\n" + "="*80)
        print("📋 EXTRACTED JOB DATA:")
        print("="*80)
        print(json.dumps(job_data, indent=2))

        # Save to file
        with open('governmentjobs_sample_job.json', 'w') as f:
            json.dump(job_data, f, indent=2)
        print("\n✅ Job data saved to: governmentjobs_sample_job.json")

        print("\n📊 FIELD COVERAGE:")
        print(f"  ✓ Title: {'✅' if 'title' in job_data else '❌'}")
        print(f"  ✓ Employer: {'✅' if 'employer' in job_data else '❌'}")
        print(f"  ✓ Location: {'✅' if 'location' in job_data else '❌'}")
        print(f"  ✓ Salary: {'✅' if 'salary' in job_data else '❌'}")
        print(f"  ✓ Description: {'✅' if 'description' in job_data else '❌'}")
        print(f"  ✓ Posted Date: {'✅' if 'posted_date' in job_data else '❌'}")
        print(f"  ✓ Closing Date: {'✅' if 'deadline' in job_data else '❌'}")
        print(f"  ✓ Apply URL: {'✅' if 'apply_url' in job_data else '❌'}")

        print("\n⏳ Keeping browser open for 5 seconds for inspection...")
        await page.wait_for_timeout(5000)

        await browser.close()

if __name__ == "__main__":
    print("Starting GovernmentJobs.com single job scrape...")
    asyncio.run(scrape_one_job())
