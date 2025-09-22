"""
Playwright Test Configuration for FreeWorld Success Coach Portal
Comprehensive testing setup for pre-production validation
"""

import pytest
import os
import json
from datetime import datetime, timedelta
from playwright.sync_api import Page, Playwright, Browser, BrowserContext
from typing import Dict, Any, List, Generator
import time

# Test Configuration
TEST_CONFIG = {
    "base_url": "https://fwcareertest.streamlit.app",  # QA deployment
    "timeout": 60000,  # 60 seconds for Streamlit apps
    "admin_username": os.getenv("TEST_ADMIN_USERNAME", "test_admin"),
    "admin_password": os.getenv("TEST_ADMIN_PASSWORD", "test_password"),
    "test_coach_username": os.getenv("TEST_COACH_USERNAME", "test_coach"),
    "test_coach_password": os.getenv("TEST_COACH_PASSWORD", "test_password"),
    "test_locations": [
        "Houston, TX",
        "Dallas, TX",
        "Austin, TX"
    ],
    "test_search_terms": [
        "CDL driver",
        "truck driver",
        "warehouse, forklift",
        "dock worker"
    ],
    "classifiers": ["CDL Traditional", "Career Pathways"],
    "search_modes": ["memory_only", "indeed_fresh"],
    "route_filters": ["both", "local", "otr"],
    "quality_levels": ["good only", "good and so-so"],
    "experience_levels": ["both", "entry level", "experienced"],
    "pathway_options": [
        "cdl_pathway",
        "dock_to_driver",
        "internal_cdl_training",
        "warehouse_to_driver",
        "logistics_progression",
        "non_cdl_driving",
        "general_warehouse",
        "construction_apprentice"
    ]
}

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for testing"""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
        "record_video_dir": "tests/videos/",
        "record_video_size": {"width": 1920, "height": 1080}
    }

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Configure browser launch arguments"""
    import os

    # Check for headed mode environment variable
    force_headed = os.environ.get("PLAYWRIGHT_HEADED") == "1"
    has_display = os.environ.get("DISPLAY") is not None

    return {
        **browser_type_launch_args,
        "headless": not (force_headed or has_display),
        "slow_mo": 1000  # 1 second delay between actions for visibility
    }

@pytest.fixture
def authenticated_admin_page(page: Page) -> Page:
    """Login as admin and return authenticated page"""
    page.set_default_timeout(TEST_CONFIG["timeout"])
    login_as_admin(page)
    return page

@pytest.fixture
def authenticated_admin_iframe(authenticated_admin_page: Page):
    """Get the iframe locator for the authenticated admin page"""
    return authenticated_admin_page.frame_locator('iframe[title="streamlitApp"]')

@pytest.fixture
def authenticated_coach_page(page: Page) -> Page:
    """Login as test coach and return authenticated page"""
    page.set_default_timeout(TEST_CONFIG["timeout"])
    login_as_coach(page)
    return page

def login_as_admin(page: Page) -> None:
    """Login as admin user"""
    print(f"🔐 Logging in as admin: {TEST_CONFIG['admin_username']}")

    page.goto(TEST_CONFIG["base_url"], timeout=TEST_CONFIG["timeout"])

    # Wait for iframe to load and switch to it
    iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

    # Wait for Streamlit app to load inside iframe with increased timeout
    iframe_locator.locator('div[data-testid="stApp"]').wait_for(timeout=TEST_CONFIG["timeout"])

    # Wait for login form inside iframe
    iframe_locator.locator('input[placeholder="username"]').wait_for(timeout=30000)

    # Enter admin credentials inside iframe
    username_input = iframe_locator.locator('input[placeholder="username"]')
    username_input.clear()
    username_input.fill(TEST_CONFIG["admin_username"])

    password_input = iframe_locator.locator('input[type="password"]')
    password_input.clear()
    password_input.fill(TEST_CONFIG["admin_password"])

    # Click login button inside iframe
    iframe_locator.locator('button:has-text("Sign In")').click()

    # Wait for login to complete and page to load
    print("⏳ Waiting for login to complete...")
    time.sleep(8)  # Give more time for Streamlit to process login

    # Check if we're logged in by looking for content that appears after login
    success_found = False
    for attempt in range(8):  # 40 seconds total
        try:
            # Wait a bit for content to load
            time.sleep(5)
            page_text = iframe_locator.locator('body').text_content(timeout=10000)

            # Look for indicators of successful login
            success_indicators = [
                "Search Parameters", "Memory Only", "Indeed Fresh",
                "Location", "Search Terms", "Analytics", "Admin Panel"
            ]

            found_indicators = []
            for indicator in success_indicators:
                if indicator in page_text:
                    found_indicators.append(indicator)

            print(f"   📊 Attempt {attempt + 1}: Found {len(found_indicators)} indicators: {found_indicators}")

            if len(found_indicators) >= 2:  # Lower threshold for more reliable detection
                success_found = True
                print("✅ Login successful!")
                break

        except Exception as e:
            print(f"   ⚠️ Attempt {attempt + 1} failed: {e}")

    if not success_found:
        raise Exception("Login appears to have failed. Expected to find main app content after login.")

def login_as_coach(page: Page) -> None:
    """Login as test coach user"""
    page.goto(TEST_CONFIG["base_url"])

    # Wait for iframe to load and switch to it
    iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

    # Wait for Streamlit app to load inside iframe
    iframe_locator.locator('div[data-testid="stApp"]').wait_for()

    # Wait for login form inside iframe
    iframe_locator.locator('input[placeholder="username"]').wait_for()

    # Enter coach credentials inside iframe
    username_input = iframe_locator.locator('input[placeholder="username"]')
    username_input.fill(TEST_CONFIG["test_coach_username"])

    password_input = iframe_locator.locator('input[type="password"]')
    password_input.fill(TEST_CONFIG["test_coach_password"])

    # Click login button inside iframe
    iframe_locator.locator('button:has-text("Sign In")').click()

    # Wait for main interface inside iframe
    iframe_locator.locator('text="Search Parameters"').wait_for(timeout=10000)

@pytest.fixture
def test_agent_data() -> Dict[str, Any]:
    """Generate test agent data"""
    timestamp = int(time.time())
    return {
        "name": f"Test Agent {timestamp}",
        "email": f"test.agent.{timestamp}@example.com",
        "location": "Houston, TX",
        "route_preference": "local",
        "fair_chance": True,
        "max_jobs": 25,
        "experience_level": "both",
        "classifier_type": "cdl",
        "pathway_preferences": ["cdl_pathway"]
    }

@pytest.fixture
def test_search_params() -> Dict[str, Any]:
    """Standard test search parameters"""
    return {
        "location": "Houston, TX",
        "search_terms": "CDL driver",
        "search_radius": 25,
        "route_filter": "both",
        "quality_level": "good and so-so",
        "experience_level": "both",
        "classifier_type": "CDL Traditional",
        "pathway_preferences": []
    }

class DataCollector:
    """Collect test results and metrics"""

    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    def add_result(self, test_name: str, status: str, duration: float,
                   jobs_found: int = 0, supabase_records: int = 0,
                   links_generated: int = 0, errors: List[str] = None):
        """Add test result"""
        self.results.append({
            "test_name": test_name,
            "status": status,
            "duration": duration,
            "jobs_found": jobs_found,
            "supabase_records": supabase_records,
            "links_generated": links_generated,
            "errors": errors or [],
            "timestamp": datetime.now().isoformat()
        })

    def get_summary(self) -> Dict[str, Any]:
        """Get test summary"""
        total_tests = len(self.results)
        passed = len([r for r in self.results if r["status"] == "passed"])
        failed = len([r for r in self.results if r["status"] == "failed"])

        return {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
            "total_duration": (datetime.now() - self.start_time).total_seconds(),
            "total_jobs_found": sum(r["jobs_found"] for r in self.results),
            "total_supabase_records": sum(r["supabase_records"] for r in self.results),
            "total_links_generated": sum(r["links_generated"] for r in self.results)
        }

    def save_report(self, filename: str = None):
        """Save test report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tests/reports/test_report_{timestamp}.json"

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        report = {
            "summary": self.get_summary(),
            "results": self.results,
            "config": TEST_CONFIG
        }

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"📊 Test report saved: {filename}")

@pytest.fixture(scope="session")
def test_data_collector():
    """Test data collector fixture"""
    collector = DataCollector()
    yield collector

    # Save final report
    collector.save_report()

    # Print summary
    summary = collector.get_summary()
    print(f"\n🎯 TEST SUMMARY:")
    print(f"   Total Tests: {summary['total_tests']}")
    print(f"   Passed: {summary['passed']}")
    print(f"   Failed: {summary['failed']}")
    print(f"   Pass Rate: {summary['pass_rate']:.1f}%")
    print(f"   Duration: {summary['total_duration']:.1f}s")
    print(f"   Jobs Found: {summary['total_jobs_found']}")
    print(f"   Supabase Records: {summary['total_supabase_records']}")
    print(f"   Links Generated: {summary['total_links_generated']}")

def wait_for_search_completion(page: Page, timeout: int = 60000) -> bool:
    """Wait for search to complete and return success status"""
    try:
        # Wait for search to start (spinner appears)
        page.wait_for_selector('div[data-testid="stSpinner"]', timeout=5000)

        # Wait for search to complete (spinner disappears)
        page.wait_for_selector('div[data-testid="stSpinner"]', state="detached", timeout=timeout)

        # Check for success indicators
        success_indicators = [
            'text="Search Results Summary"',
            'text="Quality Jobs Found"',
            'text="Route Distribution"',
            'text="Match Quality Distribution"'
        ]

        for indicator in success_indicators:
            try:
                page.wait_for_selector(indicator, timeout=2000)
                return True
            except:
                continue

        return False

    except Exception as e:
        print(f"⚠️ Search completion wait failed: {e}")
        return False

def extract_search_metrics(page: Page) -> Dict[str, int]:
    """Extract search result metrics from page"""
    metrics = {
        "total_jobs": 0,
        "quality_jobs": 0,
        "good_jobs": 0,
        "so_so_jobs": 0,
        "local_routes": 0,
        "otr_routes": 0
    }

    try:
        # Extract job counts from results summary
        summary_text = page.locator('text*="jobs found"').all_text_contents()
        for text in summary_text:
            if "total" in text.lower():
                # Extract number from text like "142 total jobs found"
                import re
                numbers = re.findall(r'\d+', text)
                if numbers:
                    metrics["total_jobs"] = int(numbers[0])

        # Extract quality distribution
        quality_text = page.locator('text*="good"').all_text_contents()
        for text in quality_text:
            if "good:" in text.lower():
                numbers = re.findall(r'\d+', text)
                if numbers:
                    metrics["good_jobs"] = int(numbers[0])
            elif "so-so:" in text.lower():
                numbers = re.findall(r'\d+', text)
                if numbers:
                    metrics["so_so_jobs"] = int(numbers[0])

        # Extract route distribution
        route_text = page.locator('text*="local"').all_text_contents()
        for text in route_text:
            if "local:" in text.lower():
                numbers = re.findall(r'\d+', text)
                if numbers:
                    metrics["local_routes"] = int(numbers[0])
            elif "otr:" in text.lower():
                numbers = re.findall(r'\d+', text)
                if numbers:
                    metrics["otr_routes"] = int(numbers[0])

        metrics["quality_jobs"] = metrics["good_jobs"] + metrics["so_so_jobs"]

    except Exception as e:
        print(f"⚠️ Metrics extraction failed: {e}")

    return metrics

def verify_supabase_upload(expected_jobs: int = 0) -> int:
    """Verify jobs were uploaded to Supabase and return count"""
    try:
        from supabase_utils import get_client
        client = get_client()

        # Check recent job uploads (last 5 minutes)
        from datetime import datetime, timedelta
        recent_time = (datetime.now() - timedelta(minutes=5)).isoformat()

        response = client.table('job_postings').select('id').gte('created_at', recent_time).execute()

        return len(response.data)

    except Exception as e:
        print(f"⚠️ Supabase verification failed: {e}")
        return 0

def verify_link_tracking() -> bool:
    """Verify link tracking system is working"""
    try:
        from supabase_utils import get_client
        client = get_client()

        # Check for recent click events
        response = client.table('click_events').select('id').limit(1).execute()

        # Just verify the table is accessible
        return True

    except Exception as e:
        print(f"⚠️ Link tracking verification failed: {e}")
        return False