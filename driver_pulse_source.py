#!/usr/bin/env python3
"""
Driver Pulse Job Source Module
A complete job scraping module for the FreeWorld job scraper pipeline.

This module provides access to Driver Pulse's job database through their API,
bypassing UI automation for maximum reliability and speed.
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

# Import secrets loader
from driver_pulse_secrets import load_auth_data, save_auth_data

# Playwright for authentication
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Gmail API for 2FA (optional)
try:
    from driver_pulse_2fa import GmailCodeExtractor
    GMAIL_2FA_AVAILABLE = True
except ImportError:
    GMAIL_2FA_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DriverPulseConfig:
    """Configuration for Driver Pulse scraping"""
    search_text: str = "CDL"
    location: str = "Dallas, TX"
    page_number: int = 1
    max_companies: int = 100
    max_jobs_per_company: int = 5
    user_timezone: str = "America/Chicago"

    # Advanced search parameters (discovered from API analysis)
    equipment_type: Optional[str] = None           # "van", "flatbed", "tanker", "hazmat", etc.
    experience_level: Optional[str] = None         # "new", "experienced", "veteran"
    home_time: Optional[str] = None                # "daily", "weekly", "monthly"
    route_type: Optional[str] = None               # "local", "regional", "otr"
    cdl_class: Optional[str] = None                # "A", "B", "C"
    endorsements: Optional[List[str]] = None       # ["hazmat", "passenger", "school_bus"]

    # Salary/compensation filters
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None

    # Company preferences
    company_size: Optional[str] = None             # "small", "medium", "large"
    benefits_required: Optional[List[str]] = None  # ["health", "dental", "401k"]

    # Geographic filters
    radius_miles: int = 50                         # Search radius from location
    exclude_locations: Optional[List[str]] = None  # Locations to exclude

    # Quality filters
    exclude_recruiters: bool = True                # Exclude third-party recruiters
    minimum_rating: Optional[float] = None         # Minimum company rating

    # Authentication files
    auth_file: str = "auth.json"
    cookies_cache: Optional[str] = None

    def to_search_params(self) -> Dict[str, Any]:
        """Convert config to API search parameters"""
        params = {
            "search_text": self.search_text,
            "location": self.location,
            "page_number": self.page_number,
            "user_timezone": self.user_timezone
        }

        # Add optional parameters if specified
        if self.equipment_type:
            params["equipment_type"] = self.equipment_type
        if self.experience_level:
            params["experience_level"] = self.experience_level
        if self.home_time:
            params["home_time"] = self.home_time
        if self.route_type:
            params["route_type"] = self.route_type
        if self.cdl_class:
            params["cdl_class"] = self.cdl_class
        if self.endorsements:
            params["endorsements"] = ",".join(self.endorsements)
        if self.min_salary:
            params["min_salary"] = self.min_salary
        if self.max_salary:
            params["max_salary"] = self.max_salary
        if self.radius_miles != 50:
            params["radius_miles"] = self.radius_miles

        return params

class DriverPulseAuthError(Exception):
    """Raised when authentication fails"""
    pass

class DriverPulseAPIError(Exception):
    """Raised when API calls fail"""
    pass

class DriverPulseSource:
    """
    Driver Pulse job source for FreeWorld pipeline integration.

    This class provides a clean interface to scrape jobs from Driver Pulse
    using their internal API endpoints discovered through network analysis.
    """

    def __init__(self, config: DriverPulseConfig = None):
        self.config = config or DriverPulseConfig()
        self.base_api = "https://pulse.tenstreet.com/global/js2php_transfer.php"
        self.uri_b = "pulse_100"
        self.session = requests.Session()
        self.user_id = None
        self.cookies_loaded = False

        # Set up session headers
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        })

    def load_authentication(self) -> bool:
        """
        Load authentication from saved session file.

        Returns:
            bool: True if authentication loaded successfully

        Raises:
            DriverPulseAuthError: If auth file is missing or invalid
        """
        try:
            # Try to load from secrets first, then fallback to local file
            auth_data = load_auth_data()
            if not auth_data:
                raise DriverPulseAuthError(f"Authentication data not found in secrets or local file: {self.config.auth_file}")

            # Extract cookies and set in session
            cookies = auth_data.get('cookies', [])
            if not cookies:
                raise DriverPulseAuthError("No cookies found in auth file")

            for cookie in cookies:
                self.session.cookies.set(
                    cookie['name'],
                    cookie['value'],
                    domain=cookie.get('domain', '.tenstreet.com')
                )

            # Load portal_user_id from auth data
            self.user_id = auth_data.get('portal_user_id')
            if not self.user_id:
                # Fallback to old field name or extract from test call
                self.user_id = auth_data.get('user_id') or self._extract_user_id()

            self.cookies_loaded = True

            logger.info(f"✅ Authentication loaded successfully. User ID: {self.user_id}")
            return True

        except Exception as e:
            raise DriverPulseAuthError(f"Failed to load authentication: {str(e)}")

    def create_new_authentication(self, email: str, first_name: str, last_name: str, phone: str,
                                gmail_credentials: str = "gmail_credentials.json",
                                headless: bool = None) -> bool:
        """
        Create new authentication session using Playwright login with 2FA support.

        Args:
            email: Login email
            first_name: First name
            last_name: Last name
            phone: Phone number
            gmail_credentials: Path to Gmail API credentials for 2FA
            headless: Run in headless mode (None=auto-detect, True=headless, False=headed)

        Returns:
            bool: True if authentication created successfully

        Raises:
            DriverPulseAuthError: If login fails or Playwright not available
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise DriverPulseAuthError("Playwright not installed. Run: pip install playwright")

        logger.info("🚀 Creating new authentication session...")

        # Initialize Gmail 2FA if available
        gmail_extractor = None
        if GMAIL_2FA_AVAILABLE and os.path.exists(gmail_credentials):
            gmail_extractor = GmailCodeExtractor()
            if gmail_extractor.setup_gmail_api():
                logger.info("✅ Gmail 2FA ready")
            else:
                gmail_extractor = None

        # Auto-detect headless mode: use headless if Gmail 2FA is available
        if headless is None:
            headless = gmail_extractor is not None
            if headless:
                logger.info("🤖 Auto-detected headless mode: Gmail 2FA is available")
            else:
                logger.info("👁️ Auto-detected headed mode: Gmail 2FA not available (manual intervention required)")

        with sync_playwright() as p:
            # Launch browser in headless or headed mode
            # Use system Chrome if available (GitHub Actions), fallback to Chromium
            use_system_chrome = os.environ.get('GITHUB_ACTIONS') == 'true'

            if headless:
                logger.info("🚀 Starting Playwright in HEADLESS mode (no browser window)")
                if use_system_chrome:
                    logger.info("   Using system Chrome (GitHub Actions)")
                    browser = p.chromium.launch(headless=True, slow_mo=100, channel="chrome")
                else:
                    browser = p.chromium.launch(headless=True, slow_mo=100)
            else:
                logger.info("🚀 Starting Playwright in HEADED mode (browser window visible)")
                browser = p.chromium.launch(headless=False, slow_mo=500)
            page = browser.new_page()

            try:
                # Step 1: Navigate to Driver Pulse
                logger.info("🌐 Loading Driver Pulse...")
                page.goto("https://pulse.tenstreet.com", wait_until="networkidle")
                time.sleep(3)

                # Step 2: Click Next button
                logger.info("🔘 Clicking Next button...")
                page.click('div[onclick]:has-text("NEXT")')

                # Step 3: Wait for login form
                logger.info("⏳ Waiting for login form...")
                page.wait_for_selector('#login_form', timeout=20000)

                # Step 4: Fill the form
                logger.info("📝 Filling login form...")
                logger.info(f"Debug: first_name='{first_name}', last_name='{last_name}', email='{email}', phone='{phone}'")

                # Ensure all values are strings
                first_name = str(first_name) if first_name else ""
                last_name = str(last_name) if last_name else ""
                email = str(email) if email else ""
                phone = str(phone) if phone else ""

                # FORCE FILL using JavaScript - bypasses any placeholder/visibility issues
                logger.info("🔧 Force-filling form fields with JavaScript...")
                page.evaluate(f"""
                    document.querySelector('#fname').value = '{first_name}';
                    document.querySelector('#lname').value = '{last_name}';
                    document.querySelector('#email').value = '{email}';
                    document.querySelector('#phone').value = '{phone}';

                    // Trigger input events so JavaScript validation fires
                    ['#fname', '#lname', '#email', '#phone'].forEach(sel => {{
                        const el = document.querySelector(sel);
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }});
                """)
                logger.info("✅ Form fields force-filled with JavaScript")

                # Also try normal fill as backup
                try:
                    page.fill('#fname', first_name)
                    page.fill('#lname', last_name)
                    page.fill('#email', email)
                    page.fill('#phone', phone)
                except Exception as e:
                    logger.warning(f"⚠️ Normal fill failed (but JS fill already succeeded): {e}")

                # Step 5: Submit the form
                logger.info("📤 Submitting login form...")
                page.press('#phone', 'Enter')

                # Step 6: Handle 2FA
                logger.info("⏳ Waiting for 2FA iframe...")
                time.sleep(5)

                try:
                    page.wait_for_selector('#check_portal_auth_user_validation_frame', timeout=20000)
                    logger.info("✅ 2FA iframe found!")

                    # Switch to iframe and click Email Me
                    iframe = page.frame(name='check_portal_auth_user_validation_frame')
                    if iframe:
                        logger.info("🔗 Switched to 2FA iframe")
                        time.sleep(3)

                        # Click Email Me button
                        iframe.click('#email_button')
                        logger.info("✅ Clicked 'Email Me' button")
                        logger.info("⏳ Waiting 5 seconds for email to arrive...")
                        time.sleep(5)

                        # Extract 2FA code from Gmail if available
                        if gmail_extractor:
                            logger.info("📧 Extracting 2FA code from Gmail...")
                            code = gmail_extractor.wait_for_2fa_code(timeout_seconds=120)

                            if code:
                                logger.info(f"✅ 2FA code extracted: {code}")

                                # Enter code
                                code = str(code) if code else ""
                                iframe.fill('#email_check_button_input', code)
                                logger.info("✅ Entered 2FA code")

                                # Submit code
                                iframe.click('#email_check_button')
                                logger.info("✅ Submitted 2FA code")

                                # Wait for completion
                                time.sleep(10)
                            else:
                                logger.error("❌ Could not extract 2FA code from Gmail")
                                return False
                        else:
                            logger.warning("⚠️ Gmail 2FA not available - continuing without it")
                            # Don't fail immediately - DriverPulse might not require 2FA
                            # Just wait and see if login completes
                            time.sleep(15 if headless else 30)

                except Exception as e:
                    logger.warning(f"⚠️ 2FA step failed or not required: {e}")
                    if headless and "Gmail 2FA" in str(e):
                        raise  # Re-raise in headless mode
                    time.sleep(10)

                # Step 8: Final wait for login completion
                logger.info("⏳ Waiting for final login completion...")
                time.sleep(5)

                # Step 8: Extract portal_user_id from URL
                current_url = page.url
                logger.info(f"📍 Current URL: {current_url}")

                # Extract portal_user_id from URL or page content
                portal_user_id = None
                if "portal_user_id=" in current_url:
                    import re
                    match = re.search(r'portal_user_id=(\d+)', current_url)
                    if match:
                        portal_user_id = match.group(1)
                        logger.info(f"✅ Extracted portal_user_id from URL: {portal_user_id}")

                # If not in URL, try to get it from page content or make a test API call
                if not portal_user_id:
                    # Try to find it in the page content or localStorage
                    try:
                        portal_user_id = page.evaluate("localStorage.getItem('portal_user_id')")
                        if portal_user_id:
                            logger.info(f"✅ Found portal_user_id in localStorage: {portal_user_id}")
                    except:
                        pass

                # Step 9: Save authentication
                logger.info("💾 Saving authentication...")
                auth_state = page.context.storage_state()

                # Convert Playwright cookies to our format
                cookies_data = []
                for cookie in auth_state['cookies']:
                    cookies_data.append({
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie['domain'],
                        'path': cookie.get('path', '/'),
                        'secure': cookie.get('secure', False),
                        'httpOnly': cookie.get('httpOnly', False)
                    })

                # Save authentication file
                auth_data = {
                    'cookies': cookies_data,
                    'created_at': datetime.now().isoformat(),
                    'portal_user_id': portal_user_id,
                    'user_info': {
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone': phone
                    }
                }

                # Save auth data (for development - in production use secrets)
                if save_auth_data(auth_data):
                    logger.info(f"✅ Authentication saved to {self.config.auth_file}")
                else:
                    logger.warning(f"⚠️ Failed to save authentication to {self.config.auth_file}")

                # Load the new authentication
                self.load_authentication()

                return True

            except Exception as e:
                logger.error(f"❌ Authentication creation failed: {str(e)}")
                page.screenshot(path="auth_creation_error.png")
                raise DriverPulseAuthError(f"Failed to create authentication: {str(e)}")

            finally:
                browser.close()

    def ensure_authentication(self, email: str, first_name: str, last_name: str, phone: str,
                            gmail_credentials: str = "gmail_credentials.json",
                            headless: bool = None) -> bool:
        """
        Ensure we have valid authentication, creating new if needed.

        Args:
            email: Login email
            first_name: First name
            last_name: Last name
            phone: Phone number
            gmail_credentials: Path to Gmail API credentials for 2FA
            headless: Run in headless mode (None=auto-detect, True=headless, False=headed)

        Returns:
            bool: True if authentication is available
        """
        try:
            # Try to load existing authentication
            return self.load_authentication()
        except DriverPulseAuthError:
            # If that fails, create new authentication
            logger.info("🔄 Creating new authentication session...")
            return self.create_new_authentication(email, first_name, last_name, phone, gmail_credentials, headless)

    def _extract_user_id(self) -> str:
        """Extract user ID from authentication"""
        # Use the portal_user_id from our working session
        return "19880939"

    def _call_api(self, misc_function: str, additional_data: Dict = None) -> Optional[Dict]:
        """
        Make an API call to Driver Pulse endpoints.

        Args:
            misc_function: The API function name
            additional_data: Additional POST data

        Returns:
            Dict: API response data or None if failed

        Raises:
            DriverPulseAPIError: If API call fails
        """
        if not self.cookies_loaded:
            raise DriverPulseAPIError("Authentication not loaded. Call load_authentication() first.")

        # Prepare request data
        base_data = {
            "mode": "mobileapp",
            "misc_function": misc_function,
            "user_timezone": self.config.user_timezone
        }

        if additional_data:
            base_data.update(additional_data)

        # Add user ID if available
        if self.user_id:
            base_data["portal_user_id"] = self.user_id

        # Prepare URL with query parameters
        params = {
            "uri_b": self.uri_b,
            "misc_function": misc_function
        }

        if self.user_id:
            params["portal_user_id"] = self.user_id

        try:
            response = self.session.post(
                self.base_api,
                params=params,
                data=base_data,
                timeout=30
            )

            response.raise_for_status()

            # Parse JSON response
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API call failed for {misc_function}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"   Status: {e.response.status_code}")
                logger.error(f"   Response: {e.response.text[:500]}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON response for {misc_function}: {str(e)}")
            return None

    def search_companies(self,
                        search_text: str = None,
                        page_number: int = None) -> Optional[Dict]:
        """
        Search for companies using Driver Pulse search API.

        Args:
            search_text: Search keywords (default from config)
            page_number: Page number for pagination (default from config)

        Returns:
            Dict: Search results with company data
        """
        search_params = {
            "search_text": search_text or self.config.search_text,
            "page_number": page_number or self.config.page_number,
            "portal_user_id": self.user_id,
            "user_timezone": self.config.user_timezone
        }

        logger.info(f"🔍 Searching companies: '{search_params['search_text']}' (page {page_number})")
        result = self._call_api("search_carriers", search_params)
        logger.info(f"🔍 DEBUG: API returned, result type: {type(result)}, has response: {'response' in result if result else 'None'}")

        # Handle end of results: API returns {'response': False} when no more data
        if result and result.get('response') == False:
            logger.info(f"✅ Reached end of results at page {page_number}")
            return None

        if result and result.get('response'):
            companies = result['response']
            # Extract actual company data (exclude meta keys)
            company_ids = [k for k in companies.keys()
                          if k not in ['default_companies_selected', 'has_results', 'result_count']]

            companies_count = len(company_ids)
            logger.info(f"✅ Found {companies_count} companies on page {page_number}")

            return result
        else:
            logger.error(f"❌ Company search failed on page {page_number}")
            logger.error(f"   Request params: {search_params}")
            logger.error(f"   Result: {result}")
            return None

    def get_company_details(self, company_id: str) -> Optional[Dict]:
        """
        Get detailed information for a specific company.

        Args:
            company_id: The company ID to fetch details for

        Returns:
            Dict: Company details including profile and job info
        """
        detail_params = {
            "result_info[item]": "screen-search_results_detail",
            "result_info[company_id]": company_id,
            "result_info[top_nav_text]": ""
        }

        result = self._call_api("get_search_detail_info", detail_params)

        if result and result.get('response'):
            return result['response']
        else:
            logger.warning(f"⚠️ Could not get details for company {company_id}")
            return None

    def scrape_jobs(self, limit: int = None) -> List[Dict]:
        """
        Main job scraping method. Searches companies and extracts job data.

        Args:
            limit: Maximum number of jobs to return (default from config)

        Returns:
            List[Dict]: List of normalized job dictionaries
        """
        if not self.cookies_loaded:
            self.load_authentication()

        jobs = []
        max_companies = limit or self.config.max_companies

        # Step 1: Search for companies
        search_results = self.search_companies()
        if not search_results:
            logger.error("❌ No search results obtained")
            return []

        companies = search_results['response']
        company_count = 0

        logger.info(f"📋 Processing companies (max: {max_companies})")

        for company_id, company_data in companies.items():
            if company_count >= max_companies:
                break

            # Skip metadata entries
            if company_id in ['default_companies_selected', 'has_results', 'result_count']:
                continue

            company_count += 1
            logger.info(f"🏢 Processing company {company_count}/{max_companies}: {company_data.get('company_name', 'Unknown')}")

            # Get detailed company information
            company_details = self.get_company_details(company_id)

            # Extract jobs from highlighted content
            highlighted_jobs = company_data.get('highlighted_content', [])

            if highlighted_jobs:
                # Process specific jobs found for this company
                for job_info in highlighted_jobs[:self.config.max_jobs_per_company]:
                    job = self._normalize_job_data(
                        job_info,
                        company_data,
                        company_details,
                        company_id
                    )
                    jobs.append(job)
            else:
                # No specific jobs, add the company as a generic driver position
                job = self._normalize_job_data(
                    None,
                    company_data,
                    company_details,
                    company_id
                )
                jobs.append(job)

            # Rate limiting to be respectful
            time.sleep(0.5)

        logger.info(f"✅ Scraped {len(jobs)} jobs from {company_count} companies")
        return jobs

    def _normalize_job_data(self,
                           job_info: Optional[Dict],
                           company_data: Dict,
                           company_details: Optional[Dict],
                           company_id: str,
                           job_details: Optional[Dict] = None) -> Dict:
        """
        Normalize job data to match FreeWorld pipeline schema.

        Args:
            job_info: Specific job information (can be None)
            company_data: Company search result data
            company_details: Detailed company information
            company_id: Company identifier
            job_details: Full job details with ZIP, lat/lng (optional)

        Returns:
            Dict: Normalized job data
        """
        # Extract job title
        if job_info and job_info.get('job_title'):
            title = job_info['job_title']
        else:
            title = "CDL Driver Position"

        # Extract company name
        company_name = company_data.get('company_name', 'Unknown Company')

        # Extract description from multiple sources
        description_parts = []

        if company_details and company_details.get('profile_text'):
            # Clean HTML from profile text
            import re
            profile_text = re.sub(r'<[^>]+>', '', company_details['profile_text'])
            description_parts.append(profile_text)

        if job_info and job_info.get('value'):
            # Clean HTML from job-specific content
            import re
            job_value = re.sub(r'<[^>]+>', '', job_info['value'])
            description_parts.append(job_value)

        description = ' '.join(description_parts).strip() or "CDL driving position available."

        # Build apply URL - use correct intelliapp format
        url_part = company_data.get('url_part')
        if url_part:
            apply_url = f"https://intelliapp.driverapponline.com/c/{url_part}"
        else:
            apply_url = f"https://intelliapp.driverapponline.com/c/company{company_id}"

        # Extract location data from job_details if available (has ZIP, lat/lng)
        job_zip = None
        job_lat = None
        job_lng = None
        job_state = None
        job_location_str = self.config.location  # fallback to config location

        if job_details:
            job_zip = job_details.get('zip')
            job_lat = job_details.get('lat')
            job_lng = job_details.get('lng')
            job_state = job_details.get('state')

            # Build location string from job details if available
            if job_zip and job_state:
                job_location_str = f"{job_zip}, {job_state}"
            elif job_state:
                job_location_str = job_state

        # Build normalized job data matching FreeWorld schema expectations
        normalized_job = {
            # Source identification
            'source_platform': 'driver_pulse',
            'source_url': apply_url,
            'source_title': title,
            'source_company': company_name,
            'source_location': self.config.location,
            'source_description': description,
            'source_salary': None,  # Driver Pulse doesn't expose salary in search
            'source_posted_date': None,  # Not available in search results

            # Normalized fields
            'normalized_title': title,
            'normalized_company': company_name,
            'normalized_location': self.config.location,
            'normalized_salary_min': None,
            'normalized_salary_max': None,

            # Additional Driver Pulse specific data
            'driver_pulse_company_id': company_id,
            'driver_pulse_job_id': job_info.get('job_id') if job_info else None,
            'driver_pulse_logo': company_data.get('logo_link'),
            'driver_pulse_url_part': company_data.get('url_part'),
            'driver_pulse_has_profile': company_details.get('has_profile', False) if company_details else False,

            # Metadata
            'scraped_at': datetime.now().isoformat(),
            'search_terms': self.config.search_text,
            'search_location': self.config.location,
        }

        return normalized_job

    def get_source_info(self) -> Dict:
        """Get information about this job source"""
        return {
            'name': 'Driver Pulse',
            'platform': 'driver_pulse',
            'description': 'CDL driver jobs from Tenstreet Driver Pulse platform',
            'supported_locations': ['All US locations'],
            'supported_job_types': ['CDL Driver', 'Trucking', 'Transportation'],
            'rate_limit': '2 requests per second',
            'requires_auth': True,
            'auth_method': 'session_cookies'
        }

def create_driver_pulse_source(search_text: str = "CDL",
                              location: str = "Dallas, TX",
                              max_jobs: int = 100) -> DriverPulseSource:
    """
    Factory function to create a configured Driver Pulse source.

    Args:
        search_text: What to search for
        location: Location to search in
        max_jobs: Maximum number of jobs to return

    Returns:
        DriverPulseSource: Configured source instance
    """
    config = DriverPulseConfig(
        search_text=search_text,
        location=location,
        max_companies=max_jobs,
        max_jobs_per_company=2  # Limit jobs per company to get more variety
    )

    return DriverPulseSource(config)

if __name__ == "__main__":
    # Example usage
    print("🚀 Driver Pulse Source Module Test")
    print("=" * 50)

    # Create source
    source = create_driver_pulse_source(
        search_text="CDL",
        location="Dallas, TX",
        max_jobs=10
    )

    try:
        # Load authentication
        source.load_authentication()

        # Scrape jobs
        jobs = source.scrape_jobs(limit=10)

        print(f"\n✅ Successfully scraped {len(jobs)} jobs")

        # Show sample jobs
        for i, job in enumerate(jobs[:3]):
            print(f"\n📋 Job {i+1}:")
            print(f"   Title: {job['normalized_title']}")
            print(f"   Company: {job['normalized_company']}")
            print(f"   Location: {job['normalized_location']}")
            print(f"   Description: {job['source_description'][:100]}...")
            print(f"   Apply URL: {job['source_url']}")

        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"driver_pulse_jobs_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(jobs, f, indent=2)

        print(f"\n💾 Results saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n🔧 To fix authentication:")
        print("1. Run: node save_auth.js")
        print("2. Complete login and 2FA in the browser")
        print("3. auth.json will be created automatically")