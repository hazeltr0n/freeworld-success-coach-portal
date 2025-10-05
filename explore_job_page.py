#!/usr/bin/env python3
"""
Use Playwright to navigate to actual job pages and see what data is available
"""

import json
import time
from playwright.sync_api import sync_playwright
from driver_pulse_source import DriverPulseSource, DriverPulseConfig

# First, get some sample jobs
config = DriverPulseConfig(search_text="CDL driver", location="Dallas, TX", max_companies=5)
source = DriverPulseSource(config)

print("🔐 Loading authentication...")
source.load_authentication()

print("🔍 Getting sample jobs...")
search_results = source.search_companies()
companies = search_results['response']

# Collect sample jobs with their URLs
sample_jobs = []
for company_id, company_data in companies.items():
    if company_id in ['default_companies_selected', 'has_results', 'result_count']:
        continue

    url_part = company_data.get('url_part')
    highlighted = company_data.get('highlighted_content', [])

    for job in highlighted[:2]:  # 2 jobs per company
        sample_jobs.append({
            'job_id': job.get('job_id'),
            'job_title': job.get('job_title'),
            'company_name': company_data.get('company_name'),
            'company_id': company_id,
            'url_part': url_part,
            'apply_url': f"https://intelliapp.driverapponline.com/c/{url_part}" if url_part else None
        })

    if len(sample_jobs) >= 3:
        break

print(f"\n🔬 Exploring {len(sample_jobs)} job pages with Playwright:")
print("=" * 100)

with sync_playwright() as p:
    # Load auth cookies
    with open('/Users/freeworld_james/Development/Driver Pulse Scraper/auth.json', 'r') as f:
        auth_data = json.load(f)

    browser = p.chromium.launch(headless=False, slow_mo=1000)
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

    for i, job in enumerate(sample_jobs, 1):
        print(f"\n{'='*100}")
        print(f"JOB {i}: {job['job_title']} at {job['company_name']}")
        print(f"{'='*100}")
        print(f"Job ID: {job['job_id']}")
        print(f"Company ID: {job['company_id']}")
        print(f"URL: {job['apply_url']}")

        # Try to navigate to the job application page
        try:
            print(f"\n📍 Navigating to: {job['apply_url']}")
            page.goto(job['apply_url'], wait_until='networkidle', timeout=15000)
            time.sleep(3)

            # Get the page title
            title = page.title()
            print(f"   Page title: {title}")

            # Check if we can find the specific job
            print(f"\n🔍 Looking for job on page...")

            # Try to find job listing elements
            job_elements = page.query_selector_all('[class*="job"], [class*="posting"], [class*="position"]')
            print(f"   Found {len(job_elements)} potential job elements")

            # Check for job ID in page content
            page_content = page.content()
            if str(job['job_id']) in page_content:
                print(f"   ✅ Job ID {job['job_id']} found in page content")
            else:
                print(f"   ❌ Job ID {job['job_id']} NOT found in page")

            # Look for job title
            if job['job_title'] in page_content:
                print(f"   ✅ Job title found in page")
            else:
                print(f"   ⚠️  Job title not found (might be listed differently)")

            # Extract any visible text that might be job descriptions
            job_desc_selectors = [
                'div[class*="description"]',
                'div[class*="details"]',
                'div[class*="job"]',
                'p[class*="description"]',
                '.job-description',
                '.posting-description'
            ]

            for selector in job_desc_selectors:
                elements = page.query_selector_all(selector)
                if elements:
                    print(f"   Found {len(elements)} elements matching: {selector}")

            # Take a screenshot
            screenshot_path = f'job_page_{job["job_id"]}.png'
            page.screenshot(path=screenshot_path)
            print(f"   📸 Screenshot saved: {screenshot_path}")

            # Save page HTML for inspection
            html_path = f'job_page_{job["job_id"]}.html'
            with open(html_path, 'w') as f:
                f.write(page_content)
            print(f"   💾 HTML saved: {html_path}")

            print(f"\n⏸️  Pausing 5 seconds to inspect page...")
            time.sleep(5)

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n\n⏸️  Keeping browser open for 30 seconds for manual inspection...")
    time.sleep(30)
    browser.close()

print(f"\n✅ Exploration complete. Check the job_page_*.html files and screenshots.")
