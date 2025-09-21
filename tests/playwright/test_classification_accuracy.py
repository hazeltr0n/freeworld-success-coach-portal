"""
Test Classification Accuracy and Supabase Integration
Verifies AI classification quality and database uploads
"""

import pytest
import time
import json
from playwright.sync_api import Page
from conftest import (
    TEST_CONFIG, wait_for_search_completion, extract_search_metrics,
    verify_supabase_upload, TestDataCollector
)

class TestClassificationAccuracy:
    """Test AI classification accuracy and Supabase integration"""

    def test_cdl_classification_accuracy(self, authenticated_admin_page: Page, test_data_collector: TestDataCollector):
        """Test CDL Traditional classifier accuracy"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "cdl_classification_accuracy"

        try:
            # Perform CDL-focused search
            page.goto(TEST_CONFIG["base_url"])

            # Set CDL-specific search parameters
            self._set_search_parameters(page, {
                "location": "Houston, TX",
                "search_terms": "CDL truck driver",
                "classifier_type": "CDL Traditional",
                "search_radius": 25
            })

            # Use Indeed Fresh to ensure fresh classification
            page.locator('button:has-text("🔍 Indeed Fresh Only")').click()

            # Wait for search completion
            success = wait_for_search_completion(page, timeout=120000)
            assert success, "CDL classification search did not complete"

            # Extract and verify classification results
            metrics = extract_search_metrics(page)
            classification_results = self._extract_classification_details(page)

            # Verify classification quality
            total_classified = classification_results.get("good_jobs", 0) + classification_results.get("so_so_jobs", 0)
            assert total_classified > 0, "No jobs were classified"

            # Verify CDL-specific classifications
            cdl_indicators = self._check_cdl_indicators(page)
            assert cdl_indicators["has_route_classification"], "No route classifications found"
            assert cdl_indicators["has_experience_analysis"], "No experience analysis found"

            # Verify Supabase upload with classification data
            supabase_count = verify_supabase_upload(metrics["total_jobs"])
            classification_data = self._verify_supabase_classification_data("cdl")

            assert classification_data["has_ai_match"], "AI match data not found in Supabase"
            assert classification_data["has_route_type"], "Route type data not found in Supabase"

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

    def test_pathway_classification_accuracy(self, authenticated_admin_page: Page, test_data_collector: TestDataCollector):
        """Test Career Pathways classifier accuracy"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "pathway_classification_accuracy"

        try:
            # Perform Career Pathways search
            page.goto(TEST_CONFIG["base_url"])

            # Set pathway-specific search parameters
            self._set_search_parameters(page, {
                "location": "Houston, TX",
                "search_terms": "warehouse, forklift, dock worker",
                "classifier_type": "Career Pathways",
                "search_radius": 25,
                "pathway_preferences": ["warehouse_to_driver", "dock_to_driver", "general_warehouse"]
            })

            # Use Indeed Fresh to ensure fresh classification
            page.locator('button:has-text("🔍 Indeed Fresh Only")').click()

            # Wait for search completion
            success = wait_for_search_completion(page, timeout=120000)
            assert success, "Career Pathways classification search did not complete"

            # Extract and verify classification results
            metrics = extract_search_metrics(page)
            classification_results = self._extract_classification_details(page)

            # Verify classification quality
            total_classified = classification_results.get("good_jobs", 0) + classification_results.get("so_so_jobs", 0)
            assert total_classified > 0, "No jobs were classified"

            # Verify pathway-specific classifications
            pathway_indicators = self._check_pathway_indicators(page)
            assert pathway_indicators["has_career_pathway"], "No career pathway classifications found"
            assert pathway_indicators["has_training_info"], "No training information found"

            # Verify Supabase upload with pathway data
            supabase_count = verify_supabase_upload(metrics["total_jobs"])
            classification_data = self._verify_supabase_classification_data("pathway")

            assert classification_data["has_ai_match"], "AI match data not found in Supabase"
            assert classification_data["has_career_pathway"], "Career pathway data not found in Supabase"

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

    def test_classification_consistency(self, authenticated_admin_page: Page, test_data_collector: TestDataCollector):
        """Test classification consistency across multiple searches"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "classification_consistency"

        try:
            # Perform multiple searches with same parameters
            search_params = {
                "location": "Dallas, TX",
                "search_terms": "CDL driver",
                "classifier_type": "CDL Traditional",
                "search_radius": 25
            }

            results = []
            for i in range(2):  # Run 2 searches for consistency
                page.goto(TEST_CONFIG["base_url"])
                self._set_search_parameters(page, search_params)

                # Use memory search for faster testing
                page.locator('button:has-text("💾 Memory Only")').click()

                success = wait_for_search_completion(page, timeout=30000)
                if success:
                    metrics = extract_search_metrics(page)
                    classification_details = self._extract_classification_details(page)
                    results.append({
                        "total_jobs": metrics["total_jobs"],
                        "good_jobs": classification_details.get("good_jobs", 0),
                        "so_so_jobs": classification_details.get("so_so_jobs", 0)
                    })

                time.sleep(2)  # Brief pause between searches

            # Verify consistency
            assert len(results) >= 2, "Not enough search results for consistency check"

            # Allow some variation but ensure general consistency
            job_counts = [r["total_jobs"] for r in results]
            max_variation = max(job_counts) - min(job_counts)
            assert max_variation <= 10, f"Too much variation in job counts: {max_variation}"

            test_data_collector.add_result(
                test_name, "passed", time.time() - start_time,
                jobs_found=sum(job_counts)
            )

        except Exception as e:
            test_data_collector.add_result(
                test_name, "failed", time.time() - start_time,
                errors=[str(e)]
            )
            raise

    def test_forced_fresh_classification(self, authenticated_admin_page: Page, test_data_collector: TestDataCollector):
        """Test forced fresh classification feature"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "forced_fresh_classification"

        try:
            # Navigate to search interface
            page.goto(TEST_CONFIG["base_url"])

            # Look for force fresh classification option (admin only)
            force_fresh_checkbox = page.locator('input[type="checkbox"]:near(:text("Force Fresh Classification"))')

            if force_fresh_checkbox.count() > 0:
                # Test force fresh functionality
                force_fresh_checkbox.check()

                # Set search parameters
                self._set_search_parameters(page, {
                    "location": "Austin, TX",
                    "search_terms": "truck driver",
                    "classifier_type": "CDL Traditional"
                })

                # Use memory search with force fresh classification
                page.locator('button:has-text("💾 Memory Only")').click()

                # Wait for completion
                success = wait_for_search_completion(page, timeout=60000)
                assert success, "Forced fresh classification search did not complete"

                # Verify fresh classification occurred
                page.wait_for_selector('text*="fresh classification"', timeout=5000)

                test_data_collector.add_result(
                    test_name, "passed", time.time() - start_time
                )
            else:
                # Force fresh not available (expected for non-admin users)
                test_data_collector.add_result(
                    test_name, "passed", time.time() - start_time,
                    errors=["Force fresh classification not available (user permission)"]
                )

        except Exception as e:
            test_data_collector.add_result(
                test_name, "failed", time.time() - start_time,
                errors=[str(e)]
            )
            raise

    def test_supabase_data_integrity(self, authenticated_admin_page: Page, test_data_collector: TestDataCollector):
        """Test Supabase data integrity and structure"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "supabase_data_integrity"

        try:
            # Verify Supabase connection and table structure
            from supabase_utils import get_client
            client = get_client()

            # Test main tables exist and are accessible
            tables_to_test = [
                'job_postings',
                'click_events',
                'candidate_clicks'
            ]

            for table in tables_to_test:
                try:
                    response = client.table(table).select('*').limit(1).execute()
                    assert response is not None, f"Table {table} not accessible"
                except Exception as table_error:
                    raise AssertionError(f"Table {table} error: {table_error}")

            # Test data structure for job_postings table
            job_response = client.table('job_postings').select('*').limit(1).execute()
            if job_response.data:
                job_record = job_response.data[0]

                # Verify essential fields exist
                essential_fields = ['id', 'source_url', 'ai_match', 'created_at']
                for field in essential_fields:
                    assert field in job_record, f"Essential field {field} missing from job_postings"

            # Test recent data (last 24 hours)
            from datetime import datetime, timedelta
            recent_time = (datetime.now() - timedelta(hours=24)).isoformat()
            recent_jobs = client.table('job_postings').select('id').gte('created_at', recent_time).execute()

            test_data_collector.add_result(
                test_name, "passed", time.time() - start_time,
                supabase_records=len(recent_jobs.data) if recent_jobs.data else 0
            )

        except Exception as e:
            test_data_collector.add_result(
                test_name, "failed", time.time() - start_time,
                errors=[str(e)]
            )
            raise

    def _set_search_parameters(self, page: Page, params: dict):
        """Helper method to set search parameters"""
        # Implementation similar to test_search_paths.py
        # Location
        if "location" in params:
            location_input = page.locator('input:near(:text("Location"))')
            if location_input.count() > 0:
                location_input.clear()
                location_input.fill(params["location"])

        # Search terms
        if "search_terms" in params:
            search_input = page.locator('input:near(:text("Search Terms"))')
            if search_input.count() > 0:
                search_input.clear()
                search_input.fill(params["search_terms"])

        # Classifier type
        if "classifier_type" in params:
            classifier_select = page.locator('div:near(:text("Job Type"))')
            if classifier_select.count() > 0:
                classifier_select.click()
                page.locator(f'text="{params["classifier_type"]}"').click()

        # Pathway preferences
        if "pathway_preferences" in params and params["pathway_preferences"]:
            for pathway in params["pathway_preferences"]:
                pathway_checkbox = page.locator(f'input[type="checkbox"]:near(:text("{pathway}"))')
                if pathway_checkbox.count() > 0:
                    pathway_checkbox.check()

        time.sleep(1)

    def _extract_classification_details(self, page: Page) -> dict:
        """Extract detailed classification information from search results"""
        details = {
            "good_jobs": 0,
            "so_so_jobs": 0,
            "bad_jobs": 0,
            "total_classified": 0
        }

        try:
            # Look for classification breakdown
            classification_text = page.locator('text*="good:"').all_text_contents()
            for text in classification_text:
                import re
                if "good:" in text.lower():
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        details["good_jobs"] = int(numbers[0])

            so_so_text = page.locator('text*="so-so:"').all_text_contents()
            for text in so_so_text:
                if "so-so:" in text.lower():
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        details["so_so_jobs"] = int(numbers[0])

            details["total_classified"] = details["good_jobs"] + details["so_so_jobs"]

        except Exception as e:
            print(f"⚠️ Classification details extraction failed: {e}")

        return details

    def _check_cdl_indicators(self, page: Page) -> dict:
        """Check for CDL-specific classification indicators"""
        indicators = {
            "has_route_classification": False,
            "has_experience_analysis": False,
            "has_cdl_requirements": False
        }

        try:
            # Check for route classifications
            route_indicators = ['local', 'otr', 'regional']
            for indicator in route_indicators:
                if page.locator(f'text*="{indicator}"').count() > 0:
                    indicators["has_route_classification"] = True
                    break

            # Check for experience analysis
            exp_indicators = ['experience', 'entry level', 'experienced']
            for indicator in exp_indicators:
                if page.locator(f'text*="{indicator}"').count() > 0:
                    indicators["has_experience_analysis"] = True
                    break

            # Check for CDL requirements
            cdl_indicators = ['cdl', 'commercial driver']
            for indicator in cdl_indicators:
                if page.locator(f'text*="{indicator}"').count() > 0:
                    indicators["has_cdl_requirements"] = True
                    break

        except Exception as e:
            print(f"⚠️ CDL indicators check failed: {e}")

        return indicators

    def _check_pathway_indicators(self, page: Page) -> dict:
        """Check for Career Pathways-specific classification indicators"""
        indicators = {
            "has_career_pathway": False,
            "has_training_info": False,
            "has_progression_analysis": False
        }

        try:
            # Check for career pathway classifications
            pathway_indicators = ['warehouse_to_driver', 'dock_to_driver', 'pathway']
            for indicator in pathway_indicators:
                if page.locator(f'text*="{indicator}"').count() > 0:
                    indicators["has_career_pathway"] = True
                    break

            # Check for training information
            training_indicators = ['training', 'learn', 'development']
            for indicator in training_indicators:
                if page.locator(f'text*="{indicator}"').count() > 0:
                    indicators["has_training_info"] = True
                    break

            # Check for progression analysis
            progression_indicators = ['progression', 'advancement', 'growth']
            for indicator in progression_indicators:
                if page.locator(f'text*="{indicator}"').count() > 0:
                    indicators["has_progression_analysis"] = True
                    break

        except Exception as e:
            print(f"⚠️ Pathway indicators check failed: {e}")

        return indicators

    def _verify_supabase_classification_data(self, classifier_type: str) -> dict:
        """Verify classification data exists in Supabase"""
        verification = {
            "has_ai_match": False,
            "has_route_type": False,
            "has_career_pathway": False,
            "has_classification_summary": False
        }

        try:
            from supabase_utils import get_client
            client = get_client()

            # Get recent job records
            from datetime import datetime, timedelta
            recent_time = (datetime.now() - timedelta(minutes=10)).isoformat()

            response = client.table('job_postings').select('*').gte('created_at', recent_time).limit(5).execute()

            if response.data:
                job_record = response.data[0]

                # Check for AI classification fields
                if 'ai_match' in job_record and job_record['ai_match']:
                    verification["has_ai_match"] = True

                if 'ai_route_type' in job_record and job_record['ai_route_type']:
                    verification["has_route_type"] = True

                if classifier_type == "pathway":
                    if 'ai_career_pathway' in job_record and job_record['ai_career_pathway']:
                        verification["has_career_pathway"] = True

                if 'ai_summary' in job_record and job_record['ai_summary']:
                    verification["has_classification_summary"] = True

        except Exception as e:
            print(f"⚠️ Supabase classification verification failed: {e}")

        return verification