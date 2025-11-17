#!/usr/bin/env python3
"""
Scrape GovernmentJobs.com using JSON-LD structured data
Similar approach to DriverPulse - extract embedded JSON instead of DOM scraping
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from urllib.parse import quote_plus
import html
import re

async def scrape_with_jsonld():
    """Scrape jobs using embedded JSON-LD structured data"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("="*80)
        print("🔍 Scraping GovernmentJobs.com using JSON-LD")
        print("="*80)

        # Build search URL
        keyword = "CDL driver"
        location = "Dallas, TX"
        search_url = f"https://www.governmentjobs.com/jobs?keyword={quote_plus(keyword)}&location={quote_plus(location)}"

        print(f"\n📍 Step 1: Loading search results...")
        print(f"   URL: {search_url}")

        await page.goto(search_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        # Find job links
        print("\n🔎 Step 2: Finding job listings...")

        job_links = []
        all_links = await page.query_selector_all('a')

        for link in all_links:
            try:
                text = await link.inner_text()
                href = await link.get_attribute('href')

                if not text or not href:
                    continue

                text = text.strip()

                # Look for job-like titles
                is_job_link = (
                    len(text) > 10 and
                    len(text) < 150 and
                    ('driver' in text.lower() or 'cdl' in text.lower()) and
                    not any(skip in text.lower() for skip in ['privacy', 'login', 'sign', 'create', 'forgot']) and
                    'category[' not in href
                )

                if is_job_link:
                    job_links.append((href, text))
                    print(f"  ✓ Found: {text[:60]}")

                if len(job_links) >= 3:  # Get first 3 jobs
                    break

            except Exception as e:
                continue

        # Filter out category links
        real_job_links = [(url, title) for url, title in job_links if 'category' not in url.lower()]

        if not real_job_links:
            print("\n❌ Could not find any job links!")
            await browser.close()
            return

        print(f"\n✅ Found {len(real_job_links)} real job links")

        # Scrape each job
        all_jobs = []

        for job_url, job_title in real_job_links:
            if not job_url.startswith('http'):
                job_url = f"https://www.governmentjobs.com{job_url}"

            print(f"\n{'='*80}")
            print(f"📄 Scraping: {job_title}")
            print(f"   URL: {job_url}")

            await page.goto(job_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            # Extract JSON-LD structured data
            print("   🔍 Extracting JSON-LD data...")

            json_ld = await page.evaluate('''() => {
                const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                for (const script of scripts) {
                    try {
                        const data = JSON.parse(script.textContent);
                        if (data['@type'] === 'JobPosting') {
                            return data;
                        }
                    } catch (e) {
                        // Invalid JSON, skip
                    }
                }
                return null;
            }''')

            if not json_ld:
                print("   ❌ No JSON-LD data found")
                continue

            print("   ✅ JSON-LD data extracted!")

            # Parse JSON-LD into clean job data
            job_data = {
                "url": job_url,
                "scraped_at": datetime.now().isoformat()
            }

            # Title
            if 'title' in json_ld:
                job_data['title'] = json_ld['title']
                print(f"   ✓ Title: {job_data['title']}")

            # Description (keep HTML, just decode entities)
            if 'description' in json_ld:
                desc_html = json_ld['description']
                # Decode HTML entities (e.g., &#39; -> ')
                desc_html = html.unescape(desc_html)
                job_data['description'] = desc_html
                print(f"   ✓ Description: {len(desc_html)} characters (HTML)")

            # Employer
            if 'hiringOrganization' in json_ld:
                org = json_ld['hiringOrganization']
                if 'name' in org:
                    job_data['employer'] = org['name']
                    print(f"   ✓ Employer: {job_data['employer']}")
                if 'sameAs' in org:
                    job_data['employer_website'] = org['sameAs']

            # Location
            if 'jobLocation' in json_ld:
                location = json_ld['jobLocation']
                if 'address' in location:
                    addr = location['address']
                    # Combine city and state
                    if 'addressLocality' in addr:
                        job_data['location'] = addr['addressLocality']
                        if 'addressRegion' in addr:
                            job_data['location'] += f", {addr['addressRegion']}"
                        print(f"   ✓ Location: {job_data['location']}")

                    # Postal code
                    if 'postalCode' in addr:
                        job_data['postal_code'] = addr['postalCode']

            # Salary
            if 'baseSalary' in json_ld:
                salary = json_ld['baseSalary']
                if 'value' in salary:
                    value = salary['value']
                    if 'minValue' in value and 'maxValue' in value:
                        min_val = value['minValue']
                        max_val = value['maxValue']
                        unit = value.get('unitText', 'YEAR')

                        # Format as currency
                        job_data['salary_min'] = min_val
                        job_data['salary_max'] = max_val
                        job_data['salary_text'] = f"${min_val:,.2f} - ${max_val:,.2f} Annually"
                        print(f"   ✓ Salary: {job_data['salary_text']}")

            # Posted Date
            if 'datePosted' in json_ld:
                job_data['posted_date'] = json_ld['datePosted']
                print(f"   ✓ Posted Date: {job_data['posted_date']}")

            # Employment Type
            if 'employmentType' in json_ld:
                job_data['employment_type'] = json_ld['employmentType']

            # Apply URL (use the current page URL)
            job_data['apply_url'] = job_url

            all_jobs.append(job_data)

        # Summary
        print("\n" + "="*80)
        print(f"📊 SUMMARY: Scraped {len(all_jobs)} jobs")
        print("="*80)

        for i, job in enumerate(all_jobs, 1):
            print(f"\n{i}. {job.get('title', 'N/A')}")
            print(f"   Employer: {job.get('employer', 'N/A')}")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   Salary: {job.get('salary_text', 'N/A')}")
            print(f"   Posted: {job.get('posted_date', 'N/A')}")
            print(f"   Description: {len(job.get('description', ''))} characters")

        # Save to file
        with open('governmentjobs_jsonld_sample.json', 'w') as f:
            json.dump(all_jobs, f, indent=2)

        print("\n✅ Data saved to: governmentjobs_jsonld_sample.json")

        print("\n⏳ Keeping browser open for 3 seconds...")
        await page.wait_for_timeout(3000)

        await browser.close()

if __name__ == "__main__":
    print("Starting GovernmentJobs.com JSON-LD scraper...")
    asyncio.run(scrape_with_jsonld())
