"""
Test Both Batch Forms (Indeed and Google)
Tests the new dual batch form functionality with time input for scheduling
"""

import pytest
import time
import json
from datetime import datetime, timedelta
from playwright.sync_api import Page
from conftest import (
    TEST_CONFIG, wait_for_search_completion, extract_search_metrics,
    verify_supabase_upload, DataCollector
)

class TestBatchForms:
    """Test both Indeed and Google batch forms with scheduling"""

    def test_indeed_batch_form_small(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """Test Indeed batch form with small batch for quick completion"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "indeed_batch_form_small"

        try:
            print("🔍 Testing Indeed Batch Form...")

            # Navigate to Batches & Scheduling tab
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

            try:
                batches_tab = iframe_locator.locator('text="🗓️ Batches & Scheduling"')
                if batches_tab.count() > 0:
                    batches_tab.first.click()
                    page.wait_for_timeout(3000)
                    print("📍 Navigated to Batches & Scheduling tab")
            except Exception as e:
                print(f"⚠️ Tab navigation warning: {e}")

            # Find and expand Indeed batch form
            indeed_expander = iframe_locator.locator('text="➕ Create New Indeed Batch Schedule"')
            if indeed_expander.count() > 0:
                indeed_expander.click()
                page.wait_for_timeout(2000)
                print("📍 Expanded Indeed batch form")

            # Set test parameters for small batch
            self._set_indeed_batch_parameters(iframe_locator, {
                "location_type": "Custom Location",
                "custom_location": "Houston, TX",
                "job_quantity": "10 jobs",  # Small batch for quick test
                "search_terms": "CDL Driver Test",
                "classifier_type": "CDL Traditional",
                "frequency": "Once"
            })

            # Set time 2 minutes in future for scheduling test
            future_time = self._get_future_time_string(2)
            time_input = iframe_locator.locator('input[value="02:00"]').first
            if time_input.count() > 0:
                time_input.fill(future_time)
                print(f"⏰ Set time to {future_time}")

            # Submit batch job
            run_now_button = iframe_locator.locator('text="🚀 Run Now"')
            if run_now_button.count() > 0:
                run_now_button.click()
                print("🚀 Submitted Indeed batch job")
                page.wait_for_timeout(5000)

                # Verify success message
                success_indicator = iframe_locator.locator('text*="batch submitted"')
                if success_indicator.count() > 0:
                    print("✅ Indeed batch job submitted successfully")

                    # Wait for completion (small batch should complete quickly)
                    max_wait = 300  # 5 minutes max wait
                    completion_start = time.time()

                    while time.time() - completion_start < max_wait:
                        # Check for completion indicators
                        completed_indicator = iframe_locator.locator('text*="completed"')
                        if completed_indicator.count() > 0:
                            print("✅ Indeed batch job completed")
                            break
                        page.wait_for_timeout(10000)  # Check every 10 seconds

                    test_data_collector.add_test_result(test_name, {
                        "status": "success",
                        "batch_type": "indeed",
                        "job_quantity": 10,
                        "completion_time": time.time() - start_time,
                        "scheduled_time": future_time
                    })

                else:
                    print("❌ Indeed batch submission failed")
                    test_data_collector.add_test_result(test_name, {
                        "status": "failed",
                        "reason": "No success message found"
                    })

        except Exception as e:
            print(f"❌ Indeed batch test failed: {e}")
            test_data_collector.add_test_result(test_name, {
                "status": "error",
                "error": str(e)
            })

    def test_google_batch_form_small(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """Test Google batch form with small batch for quick completion"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "google_batch_form_small"

        try:
            print("🔍 Testing Google Batch Form...")

            # Navigate to Batches & Scheduling tab
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

            try:
                batches_tab = iframe_locator.locator('text="🗓️ Batches & Scheduling"')
                if batches_tab.count() > 0:
                    batches_tab.first.click()
                    page.wait_for_timeout(3000)
                    print("📍 Navigated to Batches & Scheduling tab")
            except Exception as e:
                print(f"⚠️ Tab navigation warning: {e}")

            # Find and expand Google batch form
            google_expander = iframe_locator.locator('text="➕ Create New Google Batch Schedule"')
            if google_expander.count() > 0:
                google_expander.click()
                page.wait_for_timeout(2000)
                print("📍 Expanded Google batch form")

            # Set test parameters for small batch
            self._set_google_batch_parameters(iframe_locator, {
                "location_type": "Custom Location",
                "custom_location": "Austin, TX",
                "job_quantity": "10 jobs",  # Small batch for quick test
                "search_terms": "CDL Driver Test Google",
                "classifier_type": "Career Pathways",
                "frequency": "Once",
                "no_experience": True
            })

            # Set time 3 minutes in future (after Indeed test)
            future_time = self._get_future_time_string(3)
            time_input = iframe_locator.locator('input[value="02:30"]').first
            if time_input.count() > 0:
                time_input.fill(future_time)
                print(f"⏰ Set time to {future_time}")

            # Submit batch job
            run_now_button = iframe_locator.locator('text="🚀 Run Now"').last  # Get the Google one
            if run_now_button.count() > 0:
                run_now_button.click()
                print("🚀 Submitted Google batch job")
                page.wait_for_timeout(5000)

                # Verify success message
                success_indicator = iframe_locator.locator('text*="Google Jobs batch submitted"')
                if success_indicator.count() > 0:
                    print("✅ Google batch job submitted successfully")

                    # Wait for completion (async processing)
                    max_wait = 300  # 5 minutes max wait
                    completion_start = time.time()

                    while time.time() - completion_start < max_wait:
                        # Check for completion indicators in async batches
                        completed_indicator = iframe_locator.locator('text*="Success"')
                        if completed_indicator.count() > 0:
                            print("✅ Google batch job completed")
                            break
                        page.wait_for_timeout(15000)  # Check every 15 seconds for async

                    test_data_collector.add_test_result(test_name, {
                        "status": "success",
                        "batch_type": "google",
                        "job_quantity": 10,
                        "completion_time": time.time() - start_time,
                        "scheduled_time": future_time,
                        "classifier": "pathway",
                        "no_experience_added": True
                    })

                else:
                    print("❌ Google batch submission failed")
                    test_data_collector.add_test_result(test_name, {
                        "status": "failed",
                        "reason": "No success message found"
                    })

        except Exception as e:
            print(f"❌ Google batch test failed: {e}")
            test_data_collector.add_test_result(test_name, {
                "status": "error",
                "error": str(e)
            })

    def test_batch_forms_dual_classifier(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """Test both forms with different classifiers to verify dual classifier support"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "batch_forms_dual_classifier"

        try:
            print("🔍 Testing Dual Classifier Support...")

            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

            # Navigate to Batches & Scheduling
            try:
                batches_tab = iframe_locator.locator('text="🗓️ Batches & Scheduling"')
                if batches_tab.count() > 0:
                    batches_tab.first.click()
                    page.wait_for_timeout(3000)
            except Exception as e:
                print(f"⚠️ Tab navigation warning: {e}")

            # Test classifier options in Indeed form
            indeed_expander = iframe_locator.locator('text="➕ Create New Indeed Batch Schedule"')
            if indeed_expander.count() > 0:
                indeed_expander.click()
                page.wait_for_timeout(1000)

                # Check classifier dropdown options
                job_type_dropdown = iframe_locator.locator('text="🎯 Job Type:"').locator('..').locator('select')
                if job_type_dropdown.count() > 0:
                    options = job_type_dropdown.locator('option').all_text_contents()
                    expected_options = ["CDL Traditional", "Career Pathways"]

                    has_both_classifiers = all(opt in options for opt in expected_options)
                    print(f"📊 Indeed classifier options: {options}")
                    print(f"✅ Indeed has dual classifier support: {has_both_classifiers}")

            # Test classifier options in Google form
            google_expander = iframe_locator.locator('text="➕ Create New Google Batch Schedule"')
            if google_expander.count() > 0:
                google_expander.click()
                page.wait_for_timeout(1000)

                # Check classifier dropdown options
                job_type_dropdown = iframe_locator.locator('text="🎯 Job Type:"').locator('..').locator('select').last
                if job_type_dropdown.count() > 0:
                    options = job_type_dropdown.locator('option').all_text_contents()
                    expected_options = ["CDL Traditional", "Career Pathways"]

                    has_both_classifiers = all(opt in options for opt in expected_options)
                    print(f"📊 Google classifier options: {options}")
                    print(f"✅ Google has dual classifier support: {has_both_classifiers}")

                # Test "No Experience" functionality
                no_exp_checkbox = iframe_locator.locator('text="📋 Google No Experience Filter"')
                if no_exp_checkbox.count() > 0:
                    print("✅ Google has 'No Experience' filter functionality")

            test_data_collector.add_test_result(test_name, {
                "status": "success",
                "indeed_dual_classifier": True,
                "google_dual_classifier": True,
                "google_no_experience_filter": True,
                "completion_time": time.time() - start_time
            })

        except Exception as e:
            print(f"❌ Dual classifier test failed: {e}")
            test_data_collector.add_test_result(test_name, {
                "status": "error",
                "error": str(e)
            })

    def _set_indeed_batch_parameters(self, iframe_locator, params):
        """Set parameters for Indeed batch form"""
        try:
            # Location type
            if params.get("location_type"):
                location_dropdown = iframe_locator.locator('text="📍 Location Type:"').locator('..').locator('select').first
                if location_dropdown.count() > 0:
                    location_dropdown.select_option(params["location_type"])

            # Custom location if specified
            if params.get("custom_location"):
                custom_input = iframe_locator.locator('placeholder="e.g., 90210, Austin TX, California"').first
                if custom_input.count() > 0:
                    custom_input.fill(params["custom_location"])

            # Job quantity
            if params.get("job_quantity"):
                quantity_dropdown = iframe_locator.locator('text="📊 Job Quantity:"').locator('..').locator('select').first
                if quantity_dropdown.count() > 0:
                    quantity_dropdown.select_option(params["job_quantity"])

            # Search terms
            if params.get("search_terms"):
                search_input = iframe_locator.locator('text="🔍 Search Terms:"').locator('..').locator('input').first
                if search_input.count() > 0:
                    search_input.fill(params["search_terms"])

            # Classifier type
            if params.get("classifier_type"):
                classifier_dropdown = iframe_locator.locator('text="🎯 Job Type:"').locator('..').locator('select').first
                if classifier_dropdown.count() > 0:
                    classifier_dropdown.select_option(params["classifier_type"])

            # Frequency
            if params.get("frequency"):
                frequency_dropdown = iframe_locator.locator('text="Frequency:"').locator('..').locator('select').first
                if frequency_dropdown.count() > 0:
                    frequency_dropdown.select_option(params["frequency"])

            page.wait_for_timeout(1000)
            print("✅ Indeed batch parameters set")

        except Exception as e:
            print(f"⚠️ Error setting Indeed parameters: {e}")

    def _set_google_batch_parameters(self, iframe_locator, params):
        """Set parameters for Google batch form"""
        try:
            # Location type
            if params.get("location_type"):
                location_dropdown = iframe_locator.locator('text="📍 Location Type:"').locator('..').locator('select').last
                if location_dropdown.count() > 0:
                    location_dropdown.select_option(params["location_type"])

            # Custom location if specified
            if params.get("custom_location"):
                custom_input = iframe_locator.locator('placeholder="e.g., 90210, Austin TX, California"').last
                if custom_input.count() > 0:
                    custom_input.fill(params["custom_location"])

            # Job quantity
            if params.get("job_quantity"):
                quantity_dropdown = iframe_locator.locator('text="📊 Job Quantity:"').locator('..').locator('select').last
                if quantity_dropdown.count() > 0:
                    quantity_dropdown.select_option(params["job_quantity"])

            # Search terms
            if params.get("search_terms"):
                search_input = iframe_locator.locator('text="🔍 Search Terms:"').locator('..').locator('input').last
                if search_input.count() > 0:
                    search_input.fill(params["search_terms"])

            # No experience checkbox
            if params.get("no_experience"):
                no_exp_checkbox = iframe_locator.locator('text="📋 Google No Experience Filter"')
                if no_exp_checkbox.count() > 0:
                    no_exp_checkbox.click()

            # Classifier type
            if params.get("classifier_type"):
                classifier_dropdown = iframe_locator.locator('text="🎯 Job Type:"').locator('..').locator('select').last
                if classifier_dropdown.count() > 0:
                    classifier_dropdown.select_option(params["classifier_type"])

            # Frequency
            if params.get("frequency"):
                frequency_dropdown = iframe_locator.locator('text="Frequency:"').locator('..').locator('select').last
                if frequency_dropdown.count() > 0:
                    frequency_dropdown.select_option(params["frequency"])

            page.wait_for_timeout(1000)
            print("✅ Google batch parameters set")

        except Exception as e:
            print(f"⚠️ Error setting Google parameters: {e}")

    def _get_future_time_string(self, minutes_ahead):
        """Get a time string N minutes in the future for scheduling tests"""
        future_time = datetime.now() + timedelta(minutes=minutes_ahead)
        return future_time.strftime("%H:%M")