#!/usr/bin/env python3
"""
Production GovernmentJobs.com scraper using JSON-LD structured data
Covers all 10 markets with pagination and DataFrame output compatible with pipeline v3.1
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from urllib.parse import quote_plus
import html
import pandas as pd
from typing import List, Dict, Optional
import time

# 10 markets configuration
MARKETS = {
    "Dallas, TX": {"zip_code": "75201", "radius": 50},
    "Houston, TX": {"zip_code": "77002", "radius": 50},
    "Trenton, NJ": {"zip_code": "08608", "radius": 50},
    "Newark, NJ": {"zip_code": "07102", "radius": 50},
    "Las Vegas, NV": {"zip_code": "89101", "radius": 50},
    "San Francisco, CA": {"zip_code": "94102", "radius": 50},  # Bay Area
    "Stockton, CA": {"zip_code": "95202", "radius": 50},
    "Riverside, CA": {"zip_code": "92501", "radius": 50},  # Inland Empire
    "Phoenix, AZ": {"zip_code": "85003", "radius": 50},
    "Denver, CO": {"zip_code": "80202", "radius": 50},
}

# Search keywords for CDL/Transportation jobs
KEYWORDS = [
    "CDL",
]


async def extract_job_from_jsonld(page, job_url: str, job_title: str, market: str, keyword: str, run_id: str) -> Optional[Dict]:
    """
    Navigate to job detail page and extract data from JSON-LD structured data

    Args:
        page: Playwright page object
        job_url: Full URL to job detail page
        job_title: Job title from search results
        market: Market name (e.g., "Dallas, TX")
        keyword: Search keyword used
        run_id: Unique run identifier

    Returns:
        Dict with job data or None if extraction fails
    """
    try:
        await page.goto(job_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(2000)

        # Check if we hit a login page (bot detection)
        page_title = await page.title()
        if 'log in' in page_title.lower() or 'login' in page_title.lower():
            print(f"      ⚠️  Hit login page (possible bot detection) - URL: {job_url}")
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
            "meta.run_id": run_id,
            "meta.search_terms": keyword,
            "meta.market": market,
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


async def scrape_market_keyword(browser, market: str, keyword: str, run_id: str, max_pages: int = 3) -> List[Dict]:
    """
    Scrape all jobs for a specific market and keyword combination

    Args:
        browser: Playwright browser instance
        market: Market name (e.g., "Dallas, TX")
        keyword: Search keyword (e.g., "CDL driver")
        run_id: Unique run identifier
        max_pages: Maximum number of result pages to scrape (default 3)

    Returns:
        List of job data dictionaries
    """
    page = await browser.new_page()
    all_jobs = []

    try:
        print(f"\n{'='*80}")
        print(f"🔍 Scraping: {market} - '{keyword}'")
        print(f"{'='*80}")

        # Build search URL
        search_url = f"https://www.governmentjobs.com/jobs?keyword={quote_plus(keyword)}&location={quote_plus(market)}"

        print(f"   📍 Loading search results: {search_url}")
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)

        # Scrape multiple pages
        for page_num in range(1, max_pages + 1):
            print(f"\n   📄 Page {page_num}/{max_pages}")

            # Find job links on current page
            job_links = await find_job_links_on_page(page)

            if not job_links:
                print(f"      ⚠️  No job links found on page {page_num}")
                break

            print(f"      ✓ Found {len(job_links)} job links")

            # Extract data from each job
            for i, (job_url, job_title) in enumerate(job_links[:20], 1):  # Limit to 20 per page
                print(f"      {i}. {job_title[:60]}")

                job_data = await extract_job_from_jsonld(page, job_url, job_title, market, keyword, run_id)
                if job_data:
                    all_jobs.append(job_data)
                    print(f"         ✅ Extracted")

                # Rate limiting - increased to avoid bot detection
                await page.wait_for_timeout(2000)

            # Try to go to next page
            if page_num < max_pages:
                try:
                    # Look for "Next" button or pagination link
                    next_button = await page.query_selector('a:has-text("Next"), a[aria-label="Next"]')
                    if next_button:
                        await next_button.click()
                        await page.wait_for_timeout(3000)
                    else:
                        print(f"      ⚠️  No 'Next' button found, stopping pagination")
                        break
                except Exception as e:
                    print(f"      ⚠️  Could not navigate to next page: {str(e)}")
                    break

        print(f"\n   ✅ Total jobs extracted: {len(all_jobs)}")

    except Exception as e:
        print(f"\n   ❌ Error scraping {market} - {keyword}: {str(e)}")

    finally:
        await page.close()

    return all_jobs


async def scrape_all_markets(
    keywords: List[str] = None,
    markets: Dict[str, Dict] = None,
    max_pages_per_search: int = 3,
    headless: bool = True
) -> pd.DataFrame:
    """
    Production scraper for all markets and keywords

    Args:
        keywords: List of search keywords (default: KEYWORDS constant)
        markets: Market configuration dict (default: MARKETS constant)
        max_pages_per_search: Maximum pages to scrape per search (default: 3)
        headless: Run browser in headless mode (default: True)

    Returns:
        pandas DataFrame with all scraped jobs
    """
    if keywords is None:
        keywords = KEYWORDS
    if markets is None:
        markets = MARKETS

    run_id = f"governmentjobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    all_jobs = []

    print(f"\n{'='*80}")
    print(f"🚀 GovernmentJobs.com Production Scraper")
    print(f"{'='*80}")
    print(f"Run ID: {run_id}")
    print(f"Markets: {len(markets)}")
    print(f"Keywords: {len(keywords)}")
    print(f"Max pages per search: {max_pages_per_search}")
    print(f"{'='*80}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)

        try:
            # Scrape each market-keyword combination
            for market_name in markets.keys():
                for keyword in keywords:
                    jobs = await scrape_market_keyword(
                        browser,
                        market_name,
                        keyword,
                        run_id,
                        max_pages=max_pages_per_search
                    )
                    all_jobs.extend(jobs)

                    # Rate limiting between searches
                    await asyncio.sleep(2)

            print(f"\n{'='*80}")
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
    Main entry point for production scraper
    """
    # Run scraper with test configuration (fewer pages, visible browser)
    df = await scrape_all_markets(
        keywords=["CDL"],  # Test with just "CDL"
        max_pages_per_search=2,  # Test with 2 pages per search
        headless=False  # Show browser for debugging
    )

    if not df.empty:
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # CSV
        csv_file = f'governmentjobs_production_{timestamp}.csv'
        df.to_csv(csv_file, index=False)
        print(f"✅ CSV saved: {csv_file}")

        # JSON
        json_file = f'governmentjobs_production_{timestamp}.json'
        df.to_json(json_file, orient='records', indent=2)
        print(f"✅ JSON saved: {json_file}")

        # Summary
        print(f"\n{'='*80}")
        print(f"📋 DATASET SUMMARY")
        print(f"{'='*80}")
        print(f"Total jobs: {len(df)}")
        print(f"\nJobs by market:")
        print(df['meta.market'].value_counts())
        print(f"\nJobs by keyword:")
        print(df['meta.search_terms'].value_counts())
        print(f"\nSample job titles:")
        print(df['source.title'].head(10).tolist())
    else:
        print("❌ No data to save")


if __name__ == "__main__":
    print("Starting GovernmentJobs.com production scraper...")
    asyncio.run(main())
