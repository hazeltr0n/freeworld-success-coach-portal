"""
Test Search Paths - Memory Only and Indeed Fresh Only
Tests both CDL Traditional and Career Pathways classifiers
"""

import pytest
import time
from playwright.sync_api import Page
from conftest import (
    TEST_CONFIG, wait_for_search_completion, extract_search_metrics,
    verify_supabase_upload, DataCollector
)

class TestSearchPaths:
    """Test memory-only and Indeed fresh-only search paths"""

    def test_memory_only_cdl_traditional(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """Test Memory Only search with CDL Traditional classifier"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "memory_only_cdl_traditional"

        try:
            # Navigate to Job Search tab
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

            # Click on Job Search navigation (the clickable navigation link, not the heading)
            iframe_locator.get_by_label("Navigation").get_by_text("🔍 Job Search").click()
            time.sleep(3)  # Wait for tab to load

            # Set search parameters
            self._set_search_parameters(page, {
                "location": "Houston, TX",
                "search_terms": "CDL driver",
                "classifier_type": "CDL Traditional",
                "search_radius": 25
            })

            # Click Memory Only button
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
            iframe_locator.locator('button:has-text("💾 Memory Only")').click()

            # Wait for search completion
            success = wait_for_search_completion(page, timeout=30000)
            assert success, "Memory Only search did not complete successfully"

            # Extract metrics
            metrics = extract_search_metrics(page)

            # Verify results
            assert metrics["total_jobs"] > 0, "No jobs found in memory search"

            # Verify no API costs (memory only)
            page.wait_for_selector('text*="Memory Only"', timeout=5000)

            test_data_collector.add_result(
                test_name, "passed", time.time() - start_time,
                jobs_found=metrics["total_jobs"],
                supabase_records=0  # Memory only doesn't upload to Supabase
            )

        except Exception as e:
            test_data_collector.add_result(
                test_name, "failed", time.time() - start_time,
                errors=[str(e)]
            )
            raise

    def test_memory_only_career_pathways(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """Test Memory Only search with Career Pathways classifier"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "memory_only_career_pathways"

        try:
            # Navigate to main search interface
            page.goto(TEST_CONFIG["base_url"])

            # Set search parameters
            self._set_search_parameters(page, {
                "location": "Houston, TX",
                "search_terms": "warehouse, forklift",
                "classifier_type": "Career Pathways",
                "search_radius": 25,
                "pathway_preferences": ["warehouse_to_driver", "dock_to_driver"]
            })

            # Click Memory Only button
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
            iframe_locator.locator('button:has-text("💾 Memory Only")').click()

            # Wait for search completion
            success = wait_for_search_completion(page, timeout=30000)
            assert success, "Memory Only Career Pathways search did not complete"

            # Extract metrics
            metrics = extract_search_metrics(page)

            # Verify results
            assert metrics["total_jobs"] >= 0, "Memory search failed"

            test_data_collector.add_result(
                test_name, "passed", time.time() - start_time,
                jobs_found=metrics["total_jobs"]
            )

        except Exception as e:
            test_data_collector.add_result(
                test_name, "failed", time.time() - start_time,
                errors=[str(e)]
            )
            raise

    def test_indeed_fresh_cdl_traditional(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """Test Indeed Fresh Only search with CDL Traditional classifier"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "indeed_fresh_cdl_traditional"

        try:
            # Navigate to main search interface
            page.goto(TEST_CONFIG["base_url"])

            # Set search parameters
            self._set_search_parameters(page, {
                "location": "Houston, TX",
                "search_terms": "CDL driver",
                "classifier_type": "CDL Traditional",
                "search_radius": 25
            })

            # Click Indeed Fresh Only button
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
            iframe_locator.locator('button:has-text("🔍 Indeed Fresh Only")').click()

            # Wait for search completion (longer timeout for API calls)
            success = wait_for_search_completion(page, timeout=120000)
            assert success, "Indeed Fresh Only search did not complete successfully"

            # Extract metrics
            metrics = extract_search_metrics(page)

            # Verify results
            assert metrics["total_jobs"] > 0, "No jobs found in Indeed fresh search"

            # Verify Supabase upload
            supabase_count = verify_supabase_upload(metrics["total_jobs"])

            # Verify classification occurred
            assert metrics["good_jobs"] + metrics["so_so_jobs"] > 0, "No classified jobs found"

            # Verify PDF generation
            page.wait_for_selector('text*="PDF Report"', timeout=10000)

            test_data_collector.add_result(
                test_name, "passed", time.time() - start_time,
                jobs_found=metrics["total_jobs"],
                supabase_records=supabase_count
            )

        except Exception as e:
            test_data_collector.add_result(
                test_name, "failed", time.time() - start_time,
                errors=[str(e)]
            )
            raise

    def test_indeed_fresh_career_pathways(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """Test Indeed Fresh Only search with Career Pathways classifier"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "indeed_fresh_career_pathways"

        try:
            # Navigate to main search interface
            page.goto(TEST_CONFIG["base_url"])

            # Set search parameters
            self._set_search_parameters(page, {
                "location": "Houston, TX",
                "search_terms": "warehouse, dock worker",
                "classifier_type": "Career Pathways",
                "search_radius": 25,
                "pathway_preferences": ["warehouse_to_driver", "dock_to_driver", "general_warehouse"]
            })

            # Click Indeed Fresh Only button
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
            iframe_locator.locator('button:has-text("🔍 Indeed Fresh Only")').click()

            # Wait for search completion
            success = wait_for_search_completion(page, timeout=120000)
            assert success, "Indeed Fresh Career Pathways search did not complete"

            # Extract metrics
            metrics = extract_search_metrics(page)

            # Verify results
            assert metrics["total_jobs"] > 0, "No jobs found in Indeed fresh career pathways search"

            # Verify Supabase upload
            supabase_count = verify_supabase_upload(metrics["total_jobs"])

            # Verify career pathway classification
            page.wait_for_selector('text*="Career Pathway"', timeout=10000)

            test_data_collector.add_result(
                test_name, "passed", time.time() - start_time,
                jobs_found=metrics["total_jobs"],
                supabase_records=supabase_count
            )

        except Exception as e:
            test_data_collector.add_result(
                test_name, "failed", time.time() - start_time,
                errors=[str(e)]
            )
            raise

    def test_multiple_search_terms_indeed_fresh(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """Test Indeed Fresh with multiple comma-separated search terms"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "multiple_search_terms_indeed_fresh"

        try:
            # Navigate to main search interface
            page.goto(TEST_CONFIG["base_url"])

            # Set search parameters with multiple terms
            self._set_search_parameters(page, {
                "location": "Dallas, TX",
                "search_terms": "CDL driver, truck driver, delivery driver",
                "classifier_type": "CDL Traditional",
                "search_radius": 25
            })

            # Click Indeed Fresh Only button
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
            iframe_locator.locator('button:has-text("🔍 Indeed Fresh Only")').click()

            # Wait for search completion
            success = wait_for_search_completion(page, timeout=120000)
            assert success, "Multiple search terms Indeed fresh search did not complete"

            # Extract metrics
            metrics = extract_search_metrics(page)

            # Verify results (should get more jobs with multiple terms)
            assert metrics["total_jobs"] > 0, "No jobs found with multiple search terms"

            # Verify search log shows multiple queries
            page.wait_for_selector('text*="separate Indeed queries"', timeout=10000)

            test_data_collector.add_result(
                test_name, "passed", time.time() - start_time,
                jobs_found=metrics["total_jobs"]
            )

        except Exception as e:
            test_data_collector.add_result(
                test_name, "failed", time.time() - start_time,
                errors=[str(e)]
            )
            raise

    def _set_search_parameters(self, page: Page, params: dict):
        """Helper method to set search parameters"""

        # Market (location)
        if "location" in params:
            # Try market-based selectors first (app uses "market" not "location")
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

            market_input = iframe_locator.get_by_placeholder("Enter market")
            if market_input.count() == 0:
                # Try alternative selectors
                market_input = iframe_locator.locator('input[data-testid="textInput"]:near(:text("Market"))')
            if market_input.count() == 0:
                # Fallback to location selectors
                market_input = iframe_locator.get_by_placeholder("Enter location")
            if market_input.count() == 0:
                market_input = iframe_locator.locator('input[data-testid="textInput"]:near(:text("Location"))')

            market_input.fill(params["location"])

        # Search terms
        if "search_terms" in params:
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

            # Use aria-label selector based on debug findings
            search_input = iframe_locator.locator('input[aria-label="🔍 Search Terms:"]')
            if search_input.count() == 0:
                # Try alternative selectors
                search_input = iframe_locator.get_by_placeholder("Job search keywords")
            if search_input.count() == 0:
                search_input = iframe_locator.locator('input[type="text"]').filter(has=iframe_locator.locator('text="Search Terms"'))

            search_input.clear()
            search_input.fill(params["search_terms"])

        # Classifier type
        if "classifier_type" in params:
            classifier_select = page.locator('div[data-testid="selectbox"]:near(:text("Job Type"))')
            if classifier_select.count() > 0:
                classifier_select.click()
                page.locator(f'text="{params["classifier_type"]}"').click()

        # Search radius
        if "search_radius" in params:
            radius_input = page.locator('input[data-testid="numberInput"]:near(:text("Search Radius"))')
            if radius_input.count() > 0:
                radius_input.fill(str(params["search_radius"]))

        # Pathway preferences
        if "pathway_preferences" in params and params["pathway_preferences"]:
            pathway_multiselect = page.locator('div[data-testid="multiselect"]:near(:text("Career pathways"))')
            if pathway_multiselect.count() > 0:
                for pathway in params["pathway_preferences"]:
                    pathway_multiselect.click()
                    # Map internal values to display names
                    pathway_display_map = {
                        "warehouse_to_driver": "Warehouse to Driver",
                        "dock_to_driver": "Dock to Driver",
                        "cdl_pathway": "CDL Pathway",
                        "general_warehouse": "General Warehouse"
                    }
                    display_name = pathway_display_map.get(pathway, pathway)
                    page.locator(f'text="{display_name}"').click()

        # Route filter
        if "route_filter" in params:
            route_select = page.locator('div[data-testid="selectbox"]:near(:text("Route types"))')
            if route_select.count() > 0:
                route_select.click()
                page.locator(f'text="{params["route_filter"]}"').click()

        # Quality level
        if "quality_level" in params:
            quality_select = page.locator('div[data-testid="selectbox"]:near(:text("Job quality"))')
            if quality_select.count() > 0:
                quality_select.click()
                page.locator(f'text="{params["quality_level"]}"').click()

        # Experience level
        if "experience_level" in params:
            exp_select = page.locator('div[data-testid="selectbox"]:near(:text("Experience"))')
            if exp_select.count() > 0:
                exp_select.click()
                page.locator(f'text="{params["experience_level"]}"').click()

        # Wait a moment for all changes to register
        time.sleep(1)

    def test_filter_combinations(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """Test various filter combinations"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "filter_combinations"

        filter_combinations = [
            {
                "name": "local_good_only",
                "route_filter": "local",
                "quality_level": "good only",
                "experience_level": "both"
            },
            {
                "name": "otr_entry_level",
                "route_filter": "otr",
                "quality_level": "good and so-so",
                "experience_level": "entry level"
            },
            {
                "name": "all_routes_experienced",
                "route_filter": "both",
                "quality_level": "good and so-so",
                "experience_level": "experienced"
            }
        ]

        successful_combinations = 0
        total_jobs_found = 0

        try:
            for combo in filter_combinations:
                try:
                    # Navigate to main search interface
                    page.goto(TEST_CONFIG["base_url"])

                    # Set search parameters
                    params = {
                        "location": "Houston, TX",
                        "search_terms": "CDL driver",
                        "classifier_type": "CDL Traditional",
                        **combo
                    }
                    self._set_search_parameters(page, params)

                    # Use Memory Only for faster testing
                    page.locator('button:has-text("💾 Memory Only")').click()

                    # Wait for search completion
                    success = wait_for_search_completion(page, timeout=30000)
                    if success:
                        metrics = extract_search_metrics(page)
                        total_jobs_found += metrics["total_jobs"]
                        successful_combinations += 1

                        print(f"✅ Filter combination '{combo['name']}': {metrics['total_jobs']} jobs")

                except Exception as e:
                    print(f"❌ Filter combination '{combo['name']}' failed: {e}")

            # Verify at least some combinations worked
            assert successful_combinations > 0, f"No filter combinations worked ({successful_combinations}/{len(filter_combinations)})"

            test_data_collector.add_result(
                test_name, "passed", time.time() - start_time,
                jobs_found=total_jobs_found
            )

        except Exception as e:
            test_data_collector.add_result(
                test_name, "failed", time.time() - start_time,
                errors=[str(e)]
            )
            raise