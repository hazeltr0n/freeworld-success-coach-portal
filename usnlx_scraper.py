#!/usr/bin/env python3
"""
USNLX Job Scraper for FreeWorld Job Pipeline
Scrapes CDL and trucking jobs from US National Labor Exchange (usnlx.com)

USNLX is a Vue.js/Nuxt site with client-side rendering, requiring Playwright
for browser automation to extract job data.
"""

import os
import re
import json
import time
import hashlib
import logging
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# Playwright for browser automation
try:
    from playwright.sync_api import sync_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class USNLXConfig:
    """Configuration for USNLX scraping"""
    search_query: str = "CDL Driver"
    location: str = "76065"  # ZIP code
    radius_miles: int = 50
    max_pages: int = 10
    headless: bool = True
    timeout_ms: int = 30000
    slow_mo: int = 100


class USNLXScraper:
    """
    Scraper for US National Labor Exchange (usnlx.com)

    USNLX aggregates job postings from state workforce agencies and
    direct employer listings. Good source for CDL and trucking jobs.
    """

    BASE_URL = "https://usnlx.com"
    SEARCH_URL = "https://usnlx.com/jobs/"

    # FreeWorld market ZIP codes (3 per market for good coverage)
    MARKET_ZIPS = {
        'Dallas': ['75201', '75062', '75234'],
        'Houston': ['77002', '77042', '77084'],
        'Phoenix': ['85004', '85032', '85043'],
        'Denver': ['80202', '80221', '80239'],
        'Las Vegas': ['89101', '89119', '89148'],
        'Stockton': ['95202', '95207', '95336'],
        'Bay Area': ['94102', '94538', '94607'],
        'Inland Empire': ['92324', '92376', '92507'],
        'Trenton': ['08608', '08618', '08648'],
        'Newark': ['07102', '07105', '07114'],
    }

    def __init__(self, config: USNLXConfig = None):
        """Initialize USNLX scraper"""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright required. Install with: pip install playwright && playwright install")

        self.config = config or USNLXConfig()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    def _build_search_url(self, query: str, location: str, radius: int) -> str:
        """Build USNLX search URL"""
        # URL encode the query
        encoded_query = query.replace(' ', '+')
        return f"{self.SEARCH_URL}?q={encoded_query}&r={radius}&location={location}"

    def _start_browser(self):
        """Start Playwright browser"""
        if self.browser:
            return

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.config.headless,
            slow_mo=self.config.slow_mo
        )
        self.context = self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        self.page = self.context.new_page()
        logger.info(f"Browser started (headless={self.config.headless})")

    def _stop_browser(self):
        """Stop Playwright browser"""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop()

        self.page = None
        self.context = None
        self.browser = None
        logger.info("Browser stopped")

    def _wait_for_jobs_loaded(self):
        """Wait for job listings to load (Vue.js hydration)"""
        try:
            # Wait for any job listing to appear
            # USNLX uses various selectors - try multiple
            selectors_to_try = [
                '.job',
                '.jobListing-results .job-link',
                '[class*="job"]',
                'a[href*="/job/"]',
            ]

            for selector in selectors_to_try:
                try:
                    self.page.wait_for_selector(selector, timeout=self.config.timeout_ms)
                    logger.info(f"Jobs loaded (selector: {selector})")
                    return True
                except:
                    continue

            # If no specific selector works, just wait for network idle
            logger.warning("No job selectors found, waiting for network idle...")
            self.page.wait_for_load_state('networkidle', timeout=self.config.timeout_ms)
            return True

        except Exception as e:
            logger.error(f"Timeout waiting for jobs to load: {e}")
            return False

    def _extract_jobs_from_page(self) -> List[Dict]:
        """Extract job data from current page using JavaScript"""

        # JavaScript to extract job data from USNLX Vue.js rendered page
        # Structure discovered:
        # - Job links: a[href*="/job/"] with class "flex px-2 py-4"
        # - Title: h2.text-lg.font-bold.text-primary-blue
        # - Company + Location: p.text-base.leading-8 > span (company) + text (location)
        # - Distance: p.text-base.leading-3
        extract_script = """
        () => {
            const jobs = [];

            // Find all job links
            const jobLinks = document.querySelectorAll('a[href*="/job/"]');

            jobLinks.forEach((link, index) => {
                try {
                    const href = link.getAttribute('href') || '';

                    // Skip non-job links (like "POST A JOB")
                    if (!href.includes('/job/') || href === '/postajob/') return;

                    // Extract title from h2
                    const titleEl = link.querySelector('h2');
                    const title = titleEl?.innerText?.trim() || '';

                    // Extract company and location from p.leading-8
                    const infoEl = link.querySelector('p.leading-8');
                    let company = '';
                    let location = '';

                    if (infoEl) {
                        const fullText = infoEl.innerText || '';
                        // Format: "Company Name - City, ST"
                        const parts = fullText.split(' - ');
                        if (parts.length >= 2) {
                            company = parts[0].trim();
                            location = parts.slice(1).join(' - ').trim();
                        } else {
                            company = fullText.trim();
                        }
                    }

                    // Extract distance
                    const distEl = link.querySelector('p.leading-3');
                    const distanceText = distEl?.innerText?.trim() || '';
                    // Parse "Distance: X mi." to get miles
                    const distMatch = distanceText.match(/Distance:\\s*([\\d.]+)/);
                    const distance = distMatch ? parseFloat(distMatch[1]) : null;

                    // Extract job ID from URL
                    // Format: /{city-state}/{title}/{JOB_ID}/job/
                    const urlParts = href.split('/');
                    const jobId = urlParts.length >= 4 ? urlParts[urlParts.length - 3] : '';

                    if (title && href) {
                        jobs.push({
                            title: title,
                            company: company,
                            location: location,
                            distance_miles: distance,
                            url: href.startsWith('http') ? href : 'https://usnlx.com' + href,
                            job_id: jobId,
                            source_index: index
                        });
                    }
                } catch (e) {
                    console.error('Error extracting job:', e);
                }
            });

            return jobs;
        }
        """

        try:
            jobs = self.page.evaluate(extract_script)
            logger.info(f"Extracted {len(jobs)} jobs from page")
            return jobs
        except Exception as e:
            logger.error(f"Error extracting jobs: {e}")
            return []

    def _get_job_details(self, job_url: str) -> Dict:
        """
        Fetch full job details from individual job page

        Args:
            job_url: URL of the job detail page

        Returns:
            Dict with full job details including description
        """
        details = {}

        try:
            self.page.goto(job_url, wait_until='networkidle', timeout=self.config.timeout_ms)
            time.sleep(1)  # Let Vue hydrate

            # Extract job description - content appears after "Apply Now" button
            extract_details_script = """
            () => {
                const body = document.body.innerText || '';
                const details = {};

                // Find content after "Apply Now" button (where job description starts)
                const applyIdx = body.indexOf('Apply Now');
                if (applyIdx > -1) {
                    let content = body.substring(applyIdx + 10);

                    // Remove footer content
                    const footerPatterns = [
                        'POWERED BY',
                        'Privacy Policy',
                        'Terms & Conditions',
                        '© 2026',
                        '© 2025',
                        'Copyright'
                    ];

                    for (const pattern of footerPatterns) {
                        const idx = content.indexOf(pattern);
                        if (idx > 0) {
                            content = content.substring(0, idx);
                            break;
                        }
                    }

                    details.description = content.trim();
                } else {
                    // Fallback: get all body text after nav
                    const navEnd = body.indexOf('FIND JOBS');
                    if (navEnd > -1) {
                        details.description = body.substring(navEnd + 10, navEnd + 5000).trim();
                    } else {
                        details.description = body.substring(0, 5000);
                    }
                }

                // Extract salary if present
                const salaryMatch = body.match(/\\$[\\d,.]+\\s*[-–]?\\s*\\$?[\\d,.]*\\s*\\/?\\s*(hr|hour|week|year|annually)?/i);
                details.salary = salaryMatch ? salaryMatch[0] : '';

                return details;
            }
            """

            details = self.page.evaluate(extract_details_script)
            details['source_url'] = job_url

        except Exception as e:
            logger.warning(f"Error fetching job details from {job_url}: {e}")
            details['source_url'] = job_url
            details['description'] = ''
            details['error'] = str(e)

        return details

    def _has_more_button(self) -> bool:
        """Check if there's a 'More' button to load additional results"""
        try:
            # USNLX uses a "More" button with primary-blue styling
            more_btn = self.page.query_selector('button.bg-primary-blue')
            return more_btn is not None
        except:
            return False

    def _click_more_button(self) -> bool:
        """Click the 'More' button to load additional results"""
        try:
            more_btn = self.page.query_selector('button.bg-primary-blue')
            if more_btn:
                more_btn.click()
                time.sleep(2)  # Wait for Vue to update with new jobs
                return True
            return False
        except Exception as e:
            logger.warning(f"Error clicking More button: {e}")
            return False

    def _get_total_job_count(self) -> Optional[int]:
        """Get total job count from page (e.g., '554 Jobs')"""
        try:
            count_text = self.page.evaluate('''
                () => {
                    const bodyText = document.body.innerText;
                    const match = bodyText.match(/(\\d+)\\s+Jobs/i);
                    return match ? parseInt(match[1]) : null;
                }
            ''')
            return count_text
        except:
            return None

    def search_jobs(
        self,
        query: str = None,
        location: str = None,
        radius: int = None,
        max_jobs: int = None,
        max_clicks: int = None,
        fetch_details: bool = False
    ) -> List[Dict]:
        """
        Search for jobs on USNLX

        USNLX uses a "More" button to load additional results (15 jobs per click).

        Args:
            query: Search query (default: config.search_query)
            location: ZIP code (default: config.location)
            radius: Search radius in miles (default: config.radius_miles)
            max_jobs: Maximum jobs to scrape (default: 150)
            max_clicks: Max "More" button clicks (default: config.max_pages)
            fetch_details: Whether to fetch full job details (slower)

        Returns:
            List of job dictionaries
        """
        query = query or self.config.search_query
        location = location or self.config.location
        radius = radius or self.config.radius_miles
        max_clicks = max_clicks or self.config.max_pages
        max_jobs = max_jobs or 150  # Default max

        try:
            self._start_browser()

            # Build and navigate to search URL
            search_url = self._build_search_url(query, location, radius)
            logger.info(f"Searching: {search_url}")

            self.page.goto(search_url, wait_until='networkidle', timeout=self.config.timeout_ms)
            time.sleep(2)  # Let Vue.js hydrate

            # Check if jobs loaded
            if not self._wait_for_jobs_loaded():
                logger.warning("No jobs found or page failed to load")
                self.page.screenshot(path="usnlx_debug.png")
                return []

            # Get total available jobs
            total_available = self._get_total_job_count()
            if total_available:
                logger.info(f"Total jobs available: {total_available}")

            # Click "More" to load additional jobs
            click_count = 0
            prev_count = 0

            while click_count < max_clicks:
                current_count = len(self.page.query_selector_all('a[href*="/job/"]'))

                if current_count >= max_jobs:
                    logger.info(f"Reached max_jobs limit ({max_jobs})")
                    break

                if current_count == prev_count and click_count > 0:
                    logger.info("No new jobs loaded, stopping")
                    break

                prev_count = current_count

                if self._has_more_button():
                    logger.info(f"Click {click_count + 1}: {current_count} jobs loaded...")
                    if not self._click_more_button():
                        break
                    click_count += 1
                else:
                    logger.info("No more 'More' button found")
                    break

            # Extract all loaded jobs
            all_jobs = self._extract_jobs_from_page()

            # Add metadata
            for job in all_jobs:
                job['search_query'] = query
                job['search_location'] = location
                job['search_radius'] = radius
                job['scraped_at'] = datetime.now().isoformat()

            # Optionally fetch full details for each job
            if fetch_details and all_jobs:
                logger.info(f"Fetching full details for {len(all_jobs)} jobs...")
                for i, job in enumerate(all_jobs):
                    if job.get('url'):
                        details = self._get_job_details(job['url'])
                        job.update(details)
                        logger.info(f"  {i+1}/{len(all_jobs)}: {job.get('title', 'Unknown')[:40]}...")
                        time.sleep(0.5)  # Rate limiting

            logger.info(f"Total jobs scraped: {len(all_jobs)}")
            return all_jobs

        except Exception as e:
            logger.error(f"Search failed: {e}")
            if self.page:
                self.page.screenshot(path="usnlx_error.png")
            raise

        finally:
            self._stop_browser()

    def search_by_market(
        self,
        market: str,
        query: str = "CDL Driver",
        radius: int = 50,
        max_jobs: int = 100,
        max_clicks: int = 5,
        fetch_details: bool = False
    ) -> List[Dict]:
        """
        Search jobs for a FreeWorld market

        Args:
            market: Market name (e.g., "Dallas", "Houston")
            query: Search query
            radius: Search radius in miles
            max_jobs: Max jobs to load per ZIP
            max_clicks: Max "More" button clicks per ZIP
            fetch_details: Whether to fetch full details

        Returns:
            List of jobs for the market
        """
        zips = self.MARKET_ZIPS.get(market, [])
        if not zips:
            logger.warning(f"Unknown market: {market}")
            return []

        all_jobs = {}  # Dict for deduplication

        # Search first 2 ZIPs for efficiency (with radius overlap is fine)
        for zip_code in zips[:2]:
            logger.info(f"Searching {market} ZIP: {zip_code}")

            jobs = self.search_jobs(
                query=query,
                location=zip_code,
                radius=radius,
                max_jobs=max_jobs,
                max_clicks=max_clicks,
                fetch_details=fetch_details
            )

            for job in jobs:
                # Generate unique ID for dedup
                job_id = self._generate_job_id(job)
                if job_id not in all_jobs:
                    job['_market'] = market
                    all_jobs[job_id] = job

        return list(all_jobs.values())

    def search_all_markets(
        self,
        query: str = "CDL Driver",
        markets: List[str] = None,
        radius: int = 50,
        max_jobs_per_market: int = 100,
        max_clicks_per_market: int = 5,
        fetch_details: bool = False
    ) -> Dict[str, List[Dict]]:
        """
        Search all FreeWorld markets

        Args:
            query: Search query
            markets: List of markets (default: all)
            radius: Search radius
            max_jobs_per_market: Max jobs per market
            max_clicks_per_market: Max "More" clicks per ZIP
            fetch_details: Whether to fetch full details

        Returns:
            Dict mapping market name to list of jobs
        """
        if markets is None:
            markets = list(self.MARKET_ZIPS.keys())

        results = {}

        for market in markets:
            logger.info(f"\n{'='*50}")
            logger.info(f"Searching market: {market}")
            logger.info(f"{'='*50}")

            jobs = self.search_by_market(
                market=market,
                query=query,
                radius=radius,
                max_jobs=max_jobs_per_market,
                max_clicks=max_clicks_per_market,
                fetch_details=fetch_details
            )

            results[market] = jobs
            logger.info(f"{market}: {len(jobs)} jobs")

        # Summary
        total = sum(len(jobs) for jobs in results.values())
        logger.info(f"\nTotal: {total} jobs across {len(markets)} markets")

        return results

    def _generate_job_id(self, job: Dict) -> str:
        """Generate unique job ID from key fields"""
        key = f"{job.get('company', '')}|{job.get('location', '')}|{job.get('title', '')}".lower()
        return hashlib.md5(key.encode()).hexdigest()


def generate_job_id(company: str, location: str, title: str) -> str:
    """Generate unique job ID from key fields"""
    key = f"{company}|{location}|{title}".lower().strip()
    return hashlib.md5(key.encode()).hexdigest()


def transform_usnlx_to_canonical(
    raw_data: List[Dict],
    run_id: str,
    search_location: str = '',
    market: str = ''
) -> pd.DataFrame:
    """
    Transform USNLX scraper output to canonical DataFrame format

    Args:
        raw_data: List of job dictionaries from USNLX scraper
        run_id: Unique pipeline run identifier
        search_location: Location used for the search
        market: Market name for meta.market field

    Returns:
        DataFrame in canonical schema format
    """
    from jobs_schema import ensure_schema

    if not raw_data:
        return ensure_schema(pd.DataFrame())

    records = []

    for job in raw_data:
        # Parse location into components
        location_raw = job.get('location', '')
        city, state, zip_code = '', '', ''

        if location_raw:
            # Try to parse "City, ST" or "City, ST ZIP" format
            parts = location_raw.split(',')
            if len(parts) >= 2:
                city = parts[0].strip()
                state_zip = parts[1].strip().split()
                state = state_zip[0] if state_zip else ''
                zip_code = state_zip[1] if len(state_zip) > 1 else ''
            else:
                city = location_raw

        # Parse salary
        salary_raw = job.get('salary', '')
        salary_min, salary_max, salary_unit = None, None, None

        if salary_raw:
            # Try to extract numbers
            numbers = re.findall(r'[\d,]+\.?\d*', salary_raw)
            if numbers:
                try:
                    salary_min = float(numbers[0].replace(',', ''))
                    if len(numbers) > 1:
                        salary_max = float(numbers[1].replace(',', ''))
                except:
                    pass

            # Determine unit
            salary_lower = salary_raw.lower()
            if 'hour' in salary_lower or '/hr' in salary_lower:
                salary_unit = 'hour'
            elif 'week' in salary_lower:
                salary_unit = 'week'
            elif 'month' in salary_lower:
                salary_unit = 'month'
            elif 'year' in salary_lower or 'annual' in salary_lower or salary_min and salary_min > 1000:
                salary_unit = 'year'

        title = job.get('title', '')
        company = job.get('company', '')

        # Generate unique job ID
        job_id = generate_job_id(company, location_raw, title)

        # Build description
        description = job.get('description', '') or job.get('description_snippet', '')

        record = {
            # ID fields
            'id.job': job_id,
            'id.source': 'usnlx',
            'id.source_row': len(records),

            # Source fields (raw from scraper)
            'source.title': title,
            'source.company': company,
            'source.location_raw': location_raw,
            'source.description_raw': description,
            'source.url': job.get('url', '') or job.get('source_url', ''),
            'source.salary_raw': salary_raw,
            'source.posted_date': job.get('posted_date', ''),

            # Normalized location components
            'norm.city': city,
            'norm.state': state,
            'norm.zip_code': zip_code,
            'norm.location': location_raw,

            # Salary normalization
            'norm.salary_min': salary_min,
            'norm.salary_max': salary_max,
            'norm.salary_unit': salary_unit,

            # Meta fields
            'meta.market': market or job.get('_market', search_location),
            'meta.search_query': job.get('search_query', ''),
            'meta.search_location': job.get('search_location', search_location),

            # System fields
            'sys.created_at': datetime.now().isoformat(),
            'sys.updated_at': datetime.now().isoformat(),
            'sys.run_id': run_id,
            'sys.is_fresh_job': True,
            'sys.version': '3.0',

            # Route fields
            'route.stage': 'ingested',
        }

        records.append(record)

    df = pd.DataFrame(records)

    # Ensure schema compliance
    df = ensure_schema(df)

    logger.info(f"USNLX transform complete: {len(df)} jobs")

    return df


def search_usnlx(
    location: str,
    run_id: str,
    query: str = 'CDL Driver',
    radius: int = 50,
    max_jobs: int = 100,
    max_clicks: int = 5,
    market: str = '',
    fetch_details: bool = False
) -> pd.DataFrame:
    """
    High-level function to search USNLX and return canonical DataFrame

    Args:
        location: ZIP code to search
        run_id: Pipeline run ID
        query: Search query
        radius: Search radius in miles
        max_jobs: Maximum jobs to scrape
        max_clicks: Maximum "More" button clicks
        market: Market name for meta.market
        fetch_details: Whether to fetch full job details

    Returns:
        DataFrame in canonical schema format
    """
    config = USNLXConfig(
        search_query=query,
        location=location,
        radius_miles=radius,
        max_pages=max_clicks
    )

    scraper = USNLXScraper(config)

    jobs = scraper.search_jobs(
        query=query,
        location=location,
        radius=radius,
        max_jobs=max_jobs,
        max_clicks=max_clicks,
        fetch_details=fetch_details
    )

    return transform_usnlx_to_canonical(
        raw_data=jobs,
        run_id=run_id,
        search_location=location,
        market=market
    )


if __name__ == '__main__':
    print("USNLX Job Scraper Test")
    print("=" * 50)

    # Test configuration
    config = USNLXConfig(
        search_query="CDL Driver",
        location="76065",  # Midlothian, TX (Dallas area)
        radius_miles=50,
        max_pages=3,  # Max "More" clicks
        headless=True
    )

    scraper = USNLXScraper(config)

    # Test single search
    print("\n1. Testing single ZIP code search...")
    jobs = scraper.search_jobs(max_jobs=50, max_clicks=3)
    print(f"   Found {len(jobs)} jobs")

    if jobs:
        print("\n   Sample jobs:")
        for i, job in enumerate(jobs[:5]):
            print(f"   {i+1}. {job.get('title', 'N/A')[:40]}")
            print(f"      Company: {job.get('company', 'N/A')}")
            print(f"      Location: {job.get('location', 'N/A')}")
            print(f"      Distance: {job.get('distance_miles', 'N/A')} mi")
            print()

    # Test transform
    print("\n2. Testing canonical transform...")
    df = transform_usnlx_to_canonical(
        raw_data=jobs,
        run_id='test_run',
        market='Dallas'
    )
    print(f"   DataFrame shape: {df.shape}")
    print(f"   Columns: {len(df.columns)}")

    # Show CDL-specific jobs
    if not df.empty:
        cdl_jobs = df[df['source.title'].str.contains('CDL|Driver|Truck', case=False, na=False)]
        print(f"   CDL-related jobs: {len(cdl_jobs)}")

    # Save results
    if not df.empty:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"usnlx_test_{timestamp}.csv"
        df.to_csv(output_file, index=False)
        print(f"\n3. Saved to: {output_file}")

    print("\n" + "=" * 50)
    print("USNLX scraper test complete!")
