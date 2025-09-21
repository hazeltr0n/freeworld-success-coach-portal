"""
Health Check Tests - Basic validation that the application is running correctly
"""

import pytest
import time
from playwright.sync_api import Page
from conftest import TEST_CONFIG, DataCollector

class TestHealthCheck:
    """Basic health check tests to validate application functionality"""

    def test_streamlit_app_loads(self, page: Page, test_data_collector: DataCollector):
        """Test that the Streamlit app loads correctly"""
        start_time = time.time()
        test_name = "streamlit_app_loads"

        try:
            # Navigate to Streamlit app
            page.goto(TEST_CONFIG["base_url"])

            # Wait for iframe to load
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

            # Wait for Streamlit to load inside iframe
            iframe_locator.locator('div[data-testid="stApp"]').wait_for(timeout=30000)

            # Check for Streamlit-specific elements
            title = page.title()
            assert "FreeWorld" in title or "Streamlit" in title, f"Unexpected page title: {title}"

            # Look for any visible text indicating the app loaded
            page_content = page.content()
            assert len(page_content) > 1000, "Page content too short - app may not have loaded"

            test_data_collector.add_result(
                test_name, "passed", time.time() - start_time
            )

        except Exception as e:
            test_data_collector.add_result(
                test_name, "failed", time.time() - start_time,
                errors=[str(e)]
            )
            raise

    def test_login_form_exists(self, page: Page, test_data_collector: DataCollector):
        """Test that login form is present"""
        start_time = time.time()
        test_name = "login_form_exists"

        try:
            # Navigate to app
            page.goto(TEST_CONFIG["base_url"])

            # Wait for iframe to load
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

            # Wait for app to load inside iframe
            iframe_locator.locator('div[data-testid="stApp"]').wait_for(timeout=30000)

            # Look for login elements inside iframe
            login_indicators = [
                'input[placeholder="username"]',    # Username input
                'input[type="password"]',           # Password input
                'button:has-text("Sign In")',       # Sign in button
                'text="Username"',                  # Username label
                'text="Password"'                   # Password label
            ]

            found_login_elements = 0
            for indicator in login_indicators:
                try:
                    iframe_locator.locator(indicator).wait_for(timeout=2000)
                    found_login_elements += 1
                except:
                    pass

            assert found_login_elements >= 2, f"Login form not found. Only {found_login_elements} login elements detected"

            test_data_collector.add_result(
                test_name, "passed", time.time() - start_time
            )

        except Exception as e:
            test_data_collector.add_result(
                test_name, "failed", time.time() - start_time,
                errors=[str(e)]
            )
            raise

    def test_admin_login_works(self, page: Page, test_data_collector: DataCollector):
        """Test that admin login functionality works"""
        start_time = time.time()
        test_name = "admin_login_works"

        try:
            # Navigate to app
            page.goto(TEST_CONFIG["base_url"])

            # Wait for iframe and get frame locator
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

            # Wait for login form inside iframe
            iframe_locator.locator('input[placeholder="username"]').wait_for(timeout=30000)

            # Enter admin credentials inside iframe
            username_input = iframe_locator.locator('input[placeholder="username"]')
            username_input.fill(TEST_CONFIG["admin_username"])

            password_input = iframe_locator.locator('input[type="password"]')
            password_input.fill(TEST_CONFIG["admin_password"])

            # Click login inside iframe
            iframe_locator.locator('button:has-text("Sign In")').click()

            # Wait for login to complete and page to load
            time.sleep(5)

            # Check if we're logged in by looking for content that appears after login
            # Give multiple attempts for the page to fully load
            success_found = False
            for attempt in range(6):  # 30 seconds total
                try:
                    page_text = iframe_locator.locator('body').text_content()

                    # Look for indicators of successful login
                    success_indicators = [
                        "Search Parameters", "Memory Only", "Indeed Fresh",
                        "Location", "Search Terms", "Analytics", "Admin Panel"
                    ]

                    found_indicators = []
                    for indicator in success_indicators:
                        if indicator in page_text:
                            found_indicators.append(indicator)

                    if len(found_indicators) >= 3:
                        success_found = True
                        print(f"   ✅ Found {len(found_indicators)} login success indicators: {found_indicators}")
                        break
                    else:
                        print(f"   ⏳ Attempt {attempt + 1}: Found {len(found_indicators)} indicators, waiting...")
                        time.sleep(5)

                except Exception as e:
                    print(f"   ⚠️ Error checking page content: {e}")
                    time.sleep(5)

            assert success_found, f"Login appears to have failed. Expected to find main app content after login."

            test_data_collector.add_result(
                test_name, "passed", time.time() - start_time
            )

        except Exception as e:
            test_data_collector.add_result(
                test_name, "failed", time.time() - start_time,
                errors=[str(e)]
            )
            raise

    def test_main_navigation_tabs(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """Test that main navigation tabs are accessible"""
        start_time = time.time()
        test_name = "main_navigation_tabs"

        try:
            page = authenticated_admin_page
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

            # Check for main tabs inside iframe
            expected_tabs = [
                "Agent Management",
                "Analytics Dashboard",
                "Batch Search"
            ]

            accessible_tabs = 0
            for tab_name in expected_tabs:
                try:
                    # Look for tab inside iframe
                    tab_locator = iframe_locator.locator(f'text="{tab_name}"')
                    if tab_locator.count() > 0:
                        accessible_tabs += 1
                        print(f"✅ Found tab: {tab_name}")
                    else:
                        print(f"⚠️ Tab not found: {tab_name}")
                except:
                    print(f"❌ Error checking tab: {tab_name}")

            # We should find at least some of the main tabs
            assert accessible_tabs >= 1, f"No main navigation tabs found. Expected at least 1, found {accessible_tabs}"

            test_data_collector.add_result(
                test_name, "passed", time.time() - start_time
            )

        except Exception as e:
            test_data_collector.add_result(
                test_name, "failed", time.time() - start_time,
                errors=[str(e)]
            )
            raise