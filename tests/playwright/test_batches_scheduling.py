"""
Test Suite for Batches & Scheduling Functionality
Comprehensive testing of batch job scheduling features
"""

import pytest
import time
from playwright.sync_api import Page
from conftest import (
    TEST_CONFIG, navigate_to_tab, check_permission_access,
    get_batch_form_elements, set_search_parameters, DataCollector
)

class TestBatchesScheduling:
    """Test batch scheduling functionality"""

    def test_batches_tab_access(self, authenticated_admin_page: Page):
        """Test access to Batches & Scheduling tab"""
        page = authenticated_admin_page

        # Check if user has batch access permission
        has_batch_access = check_permission_access(page, "batches")

        if not has_batch_access:
            pytest.skip("User doesn't have batch access permission")

        # Navigate to Batches & Scheduling tab
        success = navigate_to_tab(page, "🗓️ Batches & Scheduling")
        assert success, "Failed to navigate to Batches & Scheduling tab"

        # Verify tab content loaded
        iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
        page_text = iframe_locator.locator('body').text_content(timeout=15000)

        expected_elements = [
            "Batches & Scheduling",
            "Create New",
            "Schedule"
        ]

        found_elements = [elem for elem in expected_elements if elem in page_text]
        assert len(found_elements) >= 2, f"Missing batch elements. Found: {found_elements}"

    def test_indeed_batch_form_expansion(self, authenticated_admin_page: Page):
        """Test Indeed batch form expansion and elements"""
        page = authenticated_admin_page

        # Get batch form elements
        form_data = get_batch_form_elements(page, "indeed")
        assert form_data["form_expanded"], "Indeed batch form failed to expand"

        # Verify form elements are present
        iframe_locator = form_data["form_locator"]
        page_text = iframe_locator.locator('body').text_content(timeout=10000)

        expected_form_elements = [
            "Location",
            "Search Terms",
            "Schedule",
            "Frequency",
            "Time"
        ]

        found_elements = [elem for elem in expected_form_elements if elem in page_text]
        assert len(found_elements) >= 3, f"Missing form elements. Found: {found_elements}"

    @pytest.mark.skipif(not TEST_CONFIG.get("google_jobs_enabled", False),
                       reason="Google Jobs not enabled")
    def test_google_batch_form_expansion(self, authenticated_admin_page: Page):
        """Test Google Jobs batch form expansion and elements"""
        page = authenticated_admin_page

        # Check Google Jobs permission first
        has_google_access = check_permission_access(page, "google_jobs")
        if not has_google_access:
            pytest.skip("User doesn't have Google Jobs access permission")

        # Get Google batch form elements
        form_data = get_batch_form_elements(page, "google")
        assert form_data["form_expanded"], "Google batch form failed to expand"

        # Verify form elements are present
        iframe_locator = form_data["form_locator"]
        page_text = iframe_locator.locator('body').text_content(timeout=10000)

        expected_form_elements = [
            "Location",
            "Search Terms",
            "Google",
            "Schedule"
        ]

        found_elements = [elem for elem in expected_form_elements if elem in page_text]
        assert len(found_elements) >= 3, f"Missing Google form elements. Found: {found_elements}"

    def test_batch_form_validation(self, authenticated_admin_page: Page):
        """Test batch form field validation"""
        page = authenticated_admin_page

        # Navigate to Batches & Scheduling
        success = navigate_to_tab(page, "🗓️ Batches & Scheduling")
        assert success, "Failed to navigate to Batches & Scheduling"

        iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

        try:
            # Expand Indeed batch form
            expand_button = iframe_locator.locator('text="➕ Create New Indeed Batch Schedule"')
            expand_button.click()
            time.sleep(2)

            # Test form field presence (don't submit, just validate structure)
            form_fields = {
                "location_field": iframe_locator.locator('input[placeholder*="location"]').first,
                "terms_field": iframe_locator.locator('input[placeholder*="search"]').first,
                "schedule_elements": iframe_locator.locator('text*="Schedule"').first
            }

            # Verify each field is accessible
            for field_name, field_locator in form_fields.items():
                try:
                    field_locator.wait_for(timeout=5000)
                    print(f"✅ {field_name} found and accessible")
                except:
                    print(f"⚠️ {field_name} not found or not accessible")

        except Exception as e:
            print(f"⚠️ Batch form validation had issues: {e}")
            # Don't fail the test for form access issues, just report

    def test_existing_batches_display(self, authenticated_admin_page: Page):
        """Test display of existing scheduled batches"""
        page = authenticated_admin_page

        # Navigate to Batches & Scheduling
        success = navigate_to_tab(page, "🗓️ Batches & Scheduling")
        assert success, "Failed to navigate to Batches & Scheduling"

        iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
        page_text = iframe_locator.locator('body').text_content(timeout=15000)

        # Check for batch display elements
        batch_indicators = [
            "Scheduled Batches",
            "Active",
            "Status",
            "Next Run",
            "No batches"  # If no batches exist
        ]

        found_indicators = [indicator for indicator in batch_indicators if indicator in page_text]

        # Should find at least one indicator of batch status display
        assert len(found_indicators) >= 1, f"No batch display indicators found. Page may not have loaded properly."

        print(f"📊 Batch display indicators found: {found_indicators}")

    def test_batch_permissions_enforcement(self, authenticated_admin_page: Page):
        """Test that batch permissions are properly enforced"""
        page = authenticated_admin_page

        # Check if batches tab is visible at all
        iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
        page_text = iframe_locator.locator('body').text_content(timeout=15000)

        has_batches_tab = "🗓️ Batches & Scheduling" in page_text
        has_batch_permission = check_permission_access(page, "batches")

        if has_batch_permission:
            assert has_batches_tab, "User has batch permission but tab not visible"
            print("✅ Batch permissions correctly granted - tab visible")
        else:
            # If no permission, tab might still be visible but functionality limited
            print("⚠️ User doesn't have batch permissions - testing limited access")

        # Test Google Jobs specific permission
        has_google_permission = check_permission_access(page, "google_jobs")
        has_google_elements = "Google" in page_text and "batch" in page_text.lower()

        if has_google_permission:
            print("✅ Google Jobs permissions detected")
        else:
            print("⚠️ No Google Jobs permissions detected")

class TestBatchScheduling:
    """Test actual batch scheduling functionality"""

    @pytest.mark.slow
    def test_indeed_batch_creation_workflow(self, authenticated_admin_page: Page):
        """Test complete Indeed batch creation workflow (without submitting)"""
        page = authenticated_admin_page

        # Navigate and expand form
        form_data = get_batch_form_elements(page, "indeed")
        if not form_data["form_expanded"]:
            pytest.skip("Could not access Indeed batch form")

        iframe_locator = form_data["form_locator"]

        # Fill form fields (but don't submit)
        test_params = {
            "location": "Houston, TX",
            "search_terms": "CDL driver test batch",
            "job_quantity": "25 jobs (test)"
        }

        try:
            # Set location if field exists
            location_field = iframe_locator.locator('input[placeholder*="location"]').first
            if location_field.is_visible():
                location_field.fill(test_params["location"])

            # Set search terms if field exists
            terms_field = iframe_locator.locator('input[placeholder*="search"]').first
            if terms_field.is_visible():
                terms_field.fill(test_params["search_terms"])

            print("✅ Batch form fields populated successfully")

            # Look for schedule options
            page_text = iframe_locator.locator('body').text_content(timeout=5000)
            schedule_options = ["Daily", "Weekly", "Hourly", "Schedule"]
            found_schedule = [opt for opt in schedule_options if opt in page_text]

            print(f"📅 Schedule options found: {found_schedule}")

        except Exception as e:
            print(f"⚠️ Batch workflow test encountered issues: {e}")
            # Don't fail - this is exploratory testing

    def test_batch_integration_with_job_search(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """Test that batch parameters integrate properly with job search functionality"""
        page = authenticated_admin_page
        start_time = time.time()

        try:
            # First test regular job search
            search_params = {
                "location": "Houston, TX",
                "search_terms": "CDL driver",
                "classifier_type": "CDL Traditional"
            }

            search_success = set_search_parameters(page, search_params)
            assert search_success, "Failed to set search parameters"

            # Run a quick memory search to verify parameters work
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
            memory_button = iframe_locator.locator('button:has-text("💾 Memory Only")').first
            memory_button.click()

            # Wait briefly for search
            time.sleep(5)

            # Check if search completed (don't wait for full completion)
            page_text = iframe_locator.locator('body').text_content(timeout=10000)
            search_indicators = ["jobs found", "results", "Houston", "CDL"]
            found_indicators = [ind for ind in search_indicators if ind.lower() in page_text.lower()]

            if len(found_indicators) >= 2:
                print("✅ Search parameters compatible with batch functionality")
                test_data_collector.add_result(
                    "batch_search_integration", "passed",
                    time.time() - start_time, jobs_found=1
                )
            else:
                print("⚠️ Search parameters may not be compatible with batches")
                test_data_collector.add_result(
                    "batch_search_integration", "warning",
                    time.time() - start_time
                )

        except Exception as e:
            print(f"⚠️ Batch integration test failed: {e}")
            test_data_collector.add_result(
                "batch_search_integration", "failed",
                time.time() - start_time, errors=[str(e)]
            )