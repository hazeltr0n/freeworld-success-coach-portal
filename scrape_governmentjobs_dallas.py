#!/usr/bin/env python3
"""
GovernmentJobs.com scraper for Dallas market only
Uses JSON-LD structured data extraction
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from urllib.parse import quote_plus
import html
import pandas as pd
from typing import List, Dict, Optional


async def extract_job_from_jsonld(page, job_url: str) -> Optional[Dict]:
    """
    Navigate to job detail page and extract data from JSON-LD structured data

    Args:
        page: Playwright page object
        job_url: Full URL to job detail page

    Returns:
        Dict with job data or None if extraction fails
    """
    try:
        await page.goto(job_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(2000)

        # Check if we hit a login page (bot detection)
        page_title = await page.title()
        if 'log in' in page_title.lower() or 'login' in page_title.lower():
            print(f"      ⚠️  Hit login page (possible bot detection)")
            return None

        # Extract JSON-LD structured data
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
            print(f"      ❌ No JSON-LD data found")
            return None

        # Parse JSON-LD into clean job data
        job_data = {
            "source.url": job_url,
            "source.platform": "GovernmentJobs",
            "meta.scraped_at": datetime.now().isoformat(),
            "meta.market": "Dallas, TX",
        }

        # Title
        if 'title' in json_ld:
            job_data['source.title'] = json_ld['title']

        # Description (keep HTML, just decode entities)
        if 'description' in json_ld:
            desc_html = json_ld['description']
            desc_html = html.unescape(desc_html)
            job_data['source.description'] = desc_html

        # Employer
        if 'hiringOrganization' in json_ld:
            org = json_ld['hiringOrganization']
            if 'name' in org:
                job_data['source.company'] = org['name']
            if 'sameAs' in org:
                job_data['employer_website'] = org['sameAs']

        # Location
        if 'jobLocation' in json_ld:
            location = json_ld['jobLocation']
            if 'address' in location:
                addr = location['address']
                # Build location string
                location_parts = []
                if 'addressLocality' in addr:
                    location_parts.append(addr['addressLocality'])
                if 'addressRegion' in addr:
                    location_parts.append(addr['addressRegion'])

                if location_parts:
                    job_data['source.location'] = ', '.join(location_parts)

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

                    job_data['salary_min'] = min_val
                    job_data['salary_max'] = max_val
                    job_data['source.salary'] = f"${min_val:,.2f} - ${max_val:,.2f} Annually"

        # Posted Date
        if 'datePosted' in json_ld:
            job_data['source.posted_date'] = json_ld['datePosted']

        # Employment Type
        if 'employmentType' in json_ld:
            job_data['employment_type'] = json_ld['employmentType']

        # Apply URL (use the current page URL)
        job_data['apply_url'] = job_url

        return job_data

    except Exception as e:
        print(f"      ❌ Error extracting job: {str(e)}")
        return None


async def find_job_links_on_page(page) -> List[tuple]:
    """
    Find all job posting links on current search results page

    Uses more specific selectors to avoid navigation/settings links

    Returns:
        List of (url, title) tuples
    """
    job_links = []

    # Try to find job postings using common CSS patterns
    # GovernmentJobs typically uses specific classes or data attributes for job links
    job_selectors = [
        'a[href*="/jobs/"]',  # Links containing /jobs/ in URL
        '.job-link',
        '.jobTitle a',
        '[data-job-id] a',
        'h3.jobtitle a',
        'article a',
        '.search-result a'
    ]

    for selector in job_selectors:
        try:
            links = await page.query_selector_all(selector)
            if links:
                print(f"   Found {len(links)} links using selector: {selector}")
                break
        except:
            continue
    else:
        # Fallback to broader search if specific selectors don't work
        links = await page.query_selector_all('a')

    for link in links:
        try:
            text = await link.inner_text()
            href = await link.get_attribute('href')

            if not text or not href:
                continue

            text = text.strip()

            # Filter out navigation and settings links
            skip_patterns = [
                'privacy', 'login', 'sign in', 'create', 'forgot', 'reset',
                'resources', 'account', 'settings', 'applications', 'status',
                'background', 'membership', 'help', 'support', 'company',
                'terms', 'accessibility', 'javascript:', 'click here',
                'search jobs', 'hide details', 'job details', 'preferences',
                'biometric', 'edge', 'chrome', 'firefox', 'safari'
            ]

            # Must be actual job URL (contains /jobs/ and a number)
            is_job_url = (
                '/jobs/' in href and
                any(char.isdigit() for char in href) and
                'category' not in href.lower()
            )

            # Must have reasonable title length
            has_good_title = 10 < len(text) < 150

            # Must not match skip patterns
            not_navigation = not any(skip.lower() in text.lower() for skip in skip_patterns)

            if is_job_url and has_good_title and not_navigation:
                # Make absolute URL
                if not href.startswith('http'):
                    href = f"https://www.governmentjobs.com{href}"
                job_links.append((href, text))

        except Exception as e:
            continue

    # Deduplicate by URL
    seen_urls = set()
    unique_links = []
    for url, title in job_links:
        if url not in seen_urls:
            seen_urls.add(url)
            unique_links.append((url, title))

    return unique_links


async def login_to_governmentjobs(page, email: str, password: str) -> bool:
    """
    Log in to GovernmentJobs.com

    Args:
        page: Playwright page object
        email: Account email
        password: Account password

    Returns:
        True if login successful, False otherwise
    """
    try:
        print("\n🔐 Logging in to GovernmentJobs.com...")

        # Go to login page
        await page.goto("https://www.governmentjobs.com/", timeout=30000)
        await page.wait_for_timeout(2000)

        # Click "LOG IN" button
        login_button = await page.query_selector('button:has-text("LOG IN")')
        if login_button:
            await login_button.click()
            await page.wait_for_timeout(2000)

        # Fill in email
        email_input = await page.query_selector('input[type="email"], input[name="username"], input[placeholder*="email"]')
        if email_input:
            await email_input.fill(email)
            print(f"   ✓ Entered email")

        # Fill in password
        password_input = await page.query_selector('input[type="password"]')
        if password_input:
            await password_input.fill(password)
            print(f"   ✓ Entered password")

        # Click sign in button
        signin_button = await page.query_selector('button:has-text("Sign In"), button[type="submit"]')
        if signin_button:
            await signin_button.click()
            await page.wait_for_timeout(5000)
            print(f"   ✓ Clicked Sign In")

        # Check if login was successful (look for user menu or profile)
        user_menu = await page.query_selector('a:has-text("Profile"), [aria-label*="User Menu"], a:has-text("User Menu")')
        if user_menu:
            print(f"   ✅ Login successful!")
            return True
        else:
            print(f"   ⚠️  Login status unclear, continuing anyway...")
            return True

    except Exception as e:
        print(f"   ❌ Login error: {str(e)}")
        return False


async def scrape_dallas_cdl_jobs(max_pages: int = 5, headless: bool = False, email: str = None, password: str = None) -> pd.DataFrame:
    """
    Scrape all CDL jobs in Dallas, TX area

    Args:
        max_pages: Maximum number of result pages to scrape (default: 5)
        headless: Run browser in headless mode (default: False for debugging)
        email: GovernmentJobs account email (optional)
        password: GovernmentJobs account password (optional)

    Returns:
        pandas DataFrame with all scraped jobs
    """
    run_id = f"governmentjobs_dallas_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    all_jobs = []

    print(f"\n{'='*80}")
    print(f"🚀 GovernmentJobs.com - Dallas CDL Scraper")
    print(f"{'='*80}")
    print(f"Run ID: {run_id}")
    print(f"Market: Dallas, TX")
    print(f"Keyword: CDL")
    print(f"Max pages: {max_pages}")
    print(f"Authentication: {'Yes' if email else 'No'}")
    print(f"{'='*80}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        try:
            # Login if credentials provided
            if email and password:
                await login_to_governmentjobs(page, email, password)
            # Build search URL
            keyword = "CDL"
            location = "Dallas, TX"
            search_url = f"https://www.governmentjobs.com/jobs?keyword={quote_plus(keyword)}&location={quote_plus(location)}"

            print(f"📍 Loading search results: {search_url}\n")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            # Scrape multiple pages
            for page_num in range(1, max_pages + 1):
                print(f"{'='*80}")
                print(f"📄 Page {page_num}/{max_pages}")
                print(f"{'='*80}")

                # Find job links on current page
                job_links = await find_job_links_on_page(page)

                if not job_links:
                    print(f"⚠️  No job links found on page {page_num}")
                    break

                print(f"✓ Found {len(job_links)} job links\n")

                # Extract data from each job
                for i, (job_url, job_title) in enumerate(job_links, 1):
                    print(f"{i}. {job_title[:70]}")

                    job_data = await extract_job_from_jsonld(page, job_url)
                    if job_data:
                        job_data['meta.run_id'] = run_id
                        job_data['meta.search_terms'] = keyword
                        all_jobs.append(job_data)
                        print(f"   ✅ Extracted")
                    else:
                        print(f"   ❌ Failed")

                    # Rate limiting - increased to avoid bot detection
                    await page.wait_for_timeout(2000)

                print(f"\n📊 Page {page_num} complete: {len([j for j in all_jobs if j.get('meta.run_id') == run_id])} jobs extracted so far\n")

                # Try to go to next page
                if page_num < max_pages:
                    try:
                        # Look for "Next" button or pagination link
                        next_button = await page.query_selector('a:has-text("Next"), a[aria-label="Next"]')
                        if next_button:
                            print(f"🔄 Navigating to page {page_num + 1}...\n")
                            await next_button.click()
                            await page.wait_for_timeout(3000)
                        else:
                            print(f"⚠️  No 'Next' button found, stopping pagination\n")
                            break
                    except Exception as e:
                        print(f"⚠️  Could not navigate to next page: {str(e)}\n")
                        break

            print(f"{'='*80}")
            print(f"📊 SCRAPING COMPLETE")
            print(f"{'='*80}")
            print(f"Total jobs extracted: {len(all_jobs)}")
            print(f"{'='*80}\n")

        finally:
            await browser.close()

    # Convert to DataFrame
    if all_jobs:
        df = pd.DataFrame(all_jobs)

        # Add source row ID
        df['id.source_row'] = range(len(df))

        # Add unique job ID (will be replaced by hash-based ID in pipeline)
        df['id.job'] = df.apply(
            lambda row: f"governmentjobs_{row['id.source_row']}_{run_id}",
            axis=1
        )

        # Add source platform
        df['id.source'] = 'governmentjobs'

        return df
    else:
        print("⚠️  No jobs found")
        return pd.DataFrame()


async def main():
    """
    Main entry point for Dallas scraper
    """
    # Load credentials from environment
    import os
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file

    email = os.getenv('GOVERNMENT_JOBS_EMAIL')
    password = os.getenv('GOVERNMENT_JOBS_PASSWORD')

    # Run scraper with authentication
    df = await scrape_dallas_cdl_jobs(
        max_pages=5,  # Scrape up to 5 pages of results
        headless=False,  # Show browser for debugging
        email=email,
        password=password
    )

    if not df.empty:
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # CSV
        csv_file = f'governmentjobs_dallas_{timestamp}.csv'
        df.to_csv(csv_file, index=False)
        print(f"✅ CSV saved: {csv_file}")

        # JSON
        json_file = f'governmentjobs_dallas_{timestamp}.json'
        df.to_json(json_file, orient='records', indent=2)
        print(f"✅ JSON saved: {json_file}")

        # Summary
        print(f"\n{'='*80}")
        print(f"📋 DATASET SUMMARY")
        print(f"{'='*80}")
        print(f"Total jobs: {len(df)}")
        print(f"\nSample job titles:")
        for title in df['source.title'].head(10).tolist():
            print(f"  • {title}")

        # Field coverage
        print(f"\n📊 Field Coverage:")
        print(f"  Title: {df['source.title'].notna().sum()} / {len(df)}")
        print(f"  Company: {df['source.company'].notna().sum()} / {len(df)}")
        print(f"  Location: {df['source.location'].notna().sum()} / {len(df)}")
        print(f"  Description: {df['source.description'].notna().sum()} / {len(df)}")
        print(f"  Salary: {df['source.salary'].notna().sum()} / {len(df)}")
        print(f"  Posted Date: {df['source.posted_date'].notna().sum()} / {len(df)}")
    else:
        print("❌ No data to save")


if __name__ == "__main__":
    print("Starting GovernmentJobs.com Dallas scraper...")
    asyncio.run(main())
