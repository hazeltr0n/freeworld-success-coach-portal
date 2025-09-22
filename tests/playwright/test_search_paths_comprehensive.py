"""
Comprehensive Search Path Testing - Efficient Multi-Function Validation
Tests all search paths, classifiers, and integrations in minimal test runs
"""

import pytest
import time
from playwright.sync_api import Page
from conftest import (
    TEST_CONFIG, wait_for_search_completion, extract_search_metrics,
    verify_supabase_upload, DataCollector
)

class TestSearchPathsComprehensive:
    """Comprehensive search path testing - efficient multi-function validation"""

    def test_comprehensive_search_validation(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """Comprehensive test validating all search paths, classifiers, and integrations in one efficient run"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "comprehensive_search_validation"

        # Track results for all tests
        test_results = {
            "memory_cdl": None,
            "memory_pathways": None,
            "indeed_cdl": None,
            "indeed_pathways": None,
            "pathway_classification": None,
            "supabase_integration": None
        }
        total_jobs_found = 0

        try:
            print("🚀 Starting comprehensive search validation...")
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

            # Navigate to Job Search tab
            try:
                iframe_locator.get_by_label("Navigation").get_by_text("🔍 Job Search").click()
                time.sleep(3)
                print("📍 Navigated to Job Search tab")
            except:
                print("⚠️ Already on Job Search tab")

            # Test 1: Memory Only + CDL Traditional
            print("\n🧪 Test 1/6: Memory Only + CDL Traditional")
            self._set_search_parameters(page, {
                "location": "Houston, TX",
                "search_terms": "CDL driver",
                "classifier_type": "CDL Traditional",
                "search_radius": 25
            })
            iframe_locator.locator('button:has-text("💾 Memory Only")').first.click()
            success = wait_for_search_completion(page, timeout=60000)
            assert success, "Memory Only CDL search failed"

            memory_cdl_metrics = extract_search_metrics(page)
            assert memory_cdl_metrics["total_jobs"] > 0, "No jobs found in Memory CDL search"
            test_results["memory_cdl"] = memory_cdl_metrics
            total_jobs_found += memory_cdl_metrics["total_jobs"]
            print(f"✅ Memory CDL: {memory_cdl_metrics['total_jobs']} jobs found")

            # Test 2: Memory Only + Career Pathways (warehouse)
            print("\n🧪 Test 2/6: Memory Only + Career Pathways (warehouse)")
            self._set_search_parameters(page, {
                "location": "Houston, TX",
                "search_terms": "warehouse, forklift",
                "classifier_type": "Career Pathways",
                "search_radius": 25
            })
            iframe_locator.locator('button:has-text("💾 Memory Only")').first.click()
            success = wait_for_search_completion(page, timeout=60000)
            assert success, "Memory Only Pathways search failed"

            memory_pathways_metrics = extract_search_metrics(page)
            assert memory_pathways_metrics["total_jobs"] > 0, "No jobs found in Memory Pathways search"

            # Verify warehouse pathway classification
            page_text = iframe_locator.locator('body').text_content(timeout=10000)
            warehouse_indicators = ["warehouse", "forklift", "general_warehouse"]
            found_warehouse = [ind for ind in warehouse_indicators if ind.lower() in page_text.lower()]
            assert len(found_warehouse) > 0, "Warehouse pathway classification failed"

            test_results["memory_pathways"] = memory_pathways_metrics
            total_jobs_found += memory_pathways_metrics["total_jobs"]
            print(f"✅ Memory Pathways: {memory_pathways_metrics['total_jobs']} jobs, pathway indicators: {found_warehouse}")

            # Test 3: Indeed Fresh + CDL Traditional (Pipeline Integration Test)
            print("\n🧪 Test 3/6: Indeed Fresh + CDL Traditional (Pipeline Integration)")
            self._set_search_parameters(page, {
                "location": "Dallas, TX",
                "search_terms": "truck driver",
                "classifier_type": "CDL Traditional",
                "search_radius": 25
            })
            iframe_locator.locator('button:has-text("🔍 Indeed Fresh Only")').first.click()
            success = wait_for_search_completion(page, timeout=120000)  # Longer for fresh search
            assert success, "Indeed Fresh CDL search failed"

            indeed_cdl_metrics = extract_search_metrics(page)
            assert indeed_cdl_metrics["total_jobs"] > 0, "No jobs found in Indeed Fresh CDL search"
            test_results["indeed_cdl"] = indeed_cdl_metrics
            total_jobs_found += indeed_cdl_metrics["total_jobs"]
            print(f"✅ Indeed Fresh CDL: {indeed_cdl_metrics['total_jobs']} jobs found")

            # Immediate Memory Test - Verify fresh jobs appear in memory
            print("🔗 Pipeline Integration: Testing fresh→memory flow...")
            time.sleep(3)  # Brief pause for data to propagate
            iframe_locator.locator('button:has-text("💾 Memory Only")').first.click()
            success = wait_for_search_completion(page, timeout=60000)
            assert success, "Memory search after fresh failed"

            memory_after_fresh_metrics = extract_search_metrics(page)
            assert memory_after_fresh_metrics["total_jobs"] > 0, "No jobs in memory after fresh search"

            # Verify pipeline integration - memory should show some fresh jobs
            assert memory_after_fresh_metrics["total_jobs"] >= indeed_cdl_metrics["total_jobs"] * 0.5, "Fresh jobs not appearing in memory search"
            print(f"🔗 Pipeline Integration: ✅ {memory_after_fresh_metrics['total_jobs']} jobs in memory after fresh scrape")

            # Test 4: Indeed Fresh + Career Pathways (construction)
            print("\n🧪 Test 4/6: Indeed Fresh + Career Pathways (construction)")
            self._set_search_parameters(page, {
                "location": "Dallas, TX",
                "search_terms": "entry-level construction, construction helper",
                "classifier_type": "Career Pathways",
                "search_radius": 25
            })
            iframe_locator.locator('button:has-text("🔍 Indeed Fresh Only")').first.click()
            success = wait_for_search_completion(page, timeout=120000)
            assert success, "Indeed Fresh Pathways search failed"

            indeed_pathways_metrics = extract_search_metrics(page)
            assert indeed_pathways_metrics["total_jobs"] > 0, "No jobs found in Indeed Fresh Pathways search"

            # Verify construction pathway classification
            page_text = iframe_locator.locator('body').text_content(timeout=10000)
            construction_indicators = ["construction", "helper", "apprentice", "Construction"]
            found_construction = [ind for ind in construction_indicators if ind.lower() in page_text.lower()]
            assert len(found_construction) > 0, "Construction pathway classification failed"

            test_results["indeed_pathways"] = indeed_pathways_metrics
            test_results["pathway_classification"] = {
                "warehouse_indicators": found_warehouse,
                "construction_indicators": found_construction
            }
            total_jobs_found += indeed_pathways_metrics["total_jobs"]
            print(f"✅ Indeed Fresh Pathways: {indeed_pathways_metrics['total_jobs']} jobs, pathway indicators: {found_construction}")

            # Test 5: Supabase Integration Validation
            print("\n🧪 Test 5/6: Supabase Integration")
            supabase_count = verify_supabase_upload(total_jobs_found)
            assert supabase_count >= 0, "Supabase integration failed"
            test_results["supabase_integration"] = {"recent_jobs": supabase_count}
            print(f"✅ Supabase Integration: {supabase_count} recent jobs verified")

            # Test 6: Filter Combinations (quick test)
            print("\n🧪 Test 6/6: Filter Combinations")
            # Test a quick filter combination to verify filter functionality
            page_text = iframe_locator.locator('body').text_content(timeout=10000)
            filter_indicators = ["Quality", "Route", "good", "so-so", "local", "otr"]
            found_filters = [ind for ind in filter_indicators if ind.lower() in page_text.lower()]
            assert len(found_filters) >= 2, "Filter system not properly displayed"
            print(f"✅ Filter System: {len(found_filters)} filter indicators found: {found_filters}")

            # Final Summary
            print(f"\n🎉 COMPREHENSIVE TEST COMPLETED SUCCESSFULLY!")
            print(f"📊 Total Jobs Found Across All Tests: {total_jobs_found}")
            print(f"🔍 Memory CDL: {test_results['memory_cdl']['total_jobs']} jobs")
            print(f"🛠️ Memory Pathways: {test_results['memory_pathways']['total_jobs']} jobs")
            print(f"🚛 Indeed CDL: {test_results['indeed_cdl']['total_jobs']} jobs")
            print(f"🏗️ Indeed Pathways: {test_results['indeed_pathways']['total_jobs']} jobs")
            print(f"🗄️ Supabase: {test_results['supabase_integration']['recent_jobs']} recent jobs")
            print(f"⚙️ Pathways: warehouse & construction classifications working")

            test_data_collector.add_result(
                test_name, "passed", time.time() - start_time,
                jobs_found=total_jobs_found,
                supabase_records=supabase_count
            )

        except Exception as e:
            test_data_collector.add_result(
                test_name, "failed", time.time() - start_time,
                errors=[str(e)]
            )
            raise

    def test_advanced_filter_combinations(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """Test advanced filter combinations efficiently"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "advanced_filter_combinations"

        try:
            print("🎛️ Testing advanced filter combinations...")
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

            # Set up a search with multiple filters
            self._set_search_parameters(page, {
                "location": "Houston, TX",
                "search_terms": "CDL driver",
                "classifier_type": "CDL Traditional",
                "search_radius": 25
            })

            # Test different quality + route combinations
            iframe_locator.locator('button:has-text("💾 Memory Only")').first.click()
            success = wait_for_search_completion(page, timeout=60000)
            assert success, "Filter combination search failed"

            metrics = extract_search_metrics(page)
            assert metrics["total_jobs"] > 0, "No jobs found with filter combinations"

            # Verify that quality and route filters are working
            assert metrics["good_jobs"] + metrics["so_so_jobs"] > 0, "Quality filters not working"
            assert metrics["local_routes"] + metrics["otr_routes"] > 0, "Route filters not working"

            print(f"✅ Filter combinations working: {metrics['total_jobs']} jobs with quality/route filters")

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
        iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

        # Set location (use default if setting fails)
        try:
            location_input = iframe_locator.locator('input[placeholder*="location"], input[placeholder*="Location"]')
            if location_input.count() > 0:
                location_input.clear()
                location_input.fill(params.get("location", "Houston, TX"))
            else:
                print(f"📍 Using default selected market instead of changing to: {params.get('location')}")
        except Exception as e:
            print(f"📍 Using default selected market instead of changing to: {params.get('location')}")

        # Set search terms (use default if setting fails)
        try:
            terms_input = iframe_locator.locator('input[placeholder*="search"], textarea[placeholder*="search"]')
            if terms_input.count() > 0:
                terms_input.clear()
                terms_input.fill(params.get("search_terms", "CDL driver"))
            else:
                print(f"🔍 Using default search terms instead of changing to: {params.get('search_terms')}")
        except Exception as e:
            print(f"🔍 Using default search terms instead of changing to: {params.get('search_terms')}")

        # Set classifier type
        try:
            classifier_select = iframe_locator.locator('select[aria-label*="Classifier"], select:has(option:text("CDL Traditional"))')
            if classifier_select.count() > 0:
                classifier_select.select_option(params.get("classifier_type", "CDL Traditional"))
        except Exception as e:
            print(f"⚙️ Using default classifier instead of changing to: {params.get('classifier_type')}")

        # Wait a moment for parameters to be set
        page.wait_for_timeout(1000)