"""
Comprehensive Test Suite - Ultimate Efficiency Test Runner
Runs all functionality tests in optimized comprehensive flows
"""

import pytest
import time
from playwright.sync_api import Page
from conftest import DataCollector

class TestComprehensiveSuite:
    """Ultimate comprehensive test suite - maximum efficiency, maximum coverage"""

    def test_ultimate_comprehensive_validation(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """ULTIMATE TEST: All core functionality validated using the new master efficient approach"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "ultimate_comprehensive_validation"

        try:
            print("🚀 ULTIMATE COMPREHENSIVE VALIDATION STARTING...")
            print("🎯 Using MASTER EFFICIENT approach for maximum speed and coverage")
            print("=" * 60)

            # Import and run the master efficient test
            from test_master_efficient import TestMasterEfficient
            master_tester = TestMasterEfficient()

            print("\n⚡ RUNNING MASTER EFFICIENT TEST...")
            master_tester.test_master_comprehensive_validation(page, test_data_collector)

            print("\n🎉 MASTER EFFICIENT TEST COMPLETED!")
            print("✅ ALL functionality validated in one efficient run")
            print(f"⏱️ Maximum efficiency achieved")

            # If we get here, the master test passed
            test_data_collector.add_result(
                test_name, "passed", time.time() - start_time
            )

            print(f"\n🎉 ULTIMATE COMPREHENSIVE VALIDATION PASSED!")
            print(f"🚀 System is fully validated and ready for production!")

        except Exception as e:
            print(f"\n❌ ULTIMATE COMPREHENSIVE VALIDATION FAILED: {str(e)}")
            test_data_collector.add_result(
                test_name, "failed", time.time() - start_time,
                errors=[str(e)]
            )
            raise

# Performance Benchmark Test
class TestPerformanceBenchmark:
    """Performance benchmark for the comprehensive test suite"""

    def test_performance_benchmark(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """Benchmark test to measure comprehensive suite performance"""
        page = authenticated_admin_page
        start_time = time.time()
        test_name = "performance_benchmark"

        try:
            print("⏱️ PERFORMANCE BENCHMARK STARTING...")

            # Quick basic search to measure baseline performance
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

            try:
                iframe_locator.get_by_label("Navigation").get_by_text("🔍 Job Search").click()
                time.sleep(2)
            except:
                pass

            iframe_locator.locator('button:has-text("💾 Memory Only")').first.click()

            from conftest import wait_for_search_completion, extract_search_metrics

            # Measure search performance
            search_start = time.time()
            success = wait_for_search_completion(page, timeout=60000)
            search_duration = time.time() - search_start

            if success:
                metrics = extract_search_metrics(page)
                jobs_per_second = metrics["total_jobs"] / search_duration if search_duration > 0 else 0

                print(f"⏱️ Performance Metrics:")
                print(f"   Search Duration: {search_duration:.2f} seconds")
                print(f"   Jobs Found: {metrics['total_jobs']}")
                print(f"   Jobs/Second: {jobs_per_second:.2f}")

                # Performance assertions
                assert search_duration < 120, f"Search too slow: {search_duration:.2f}s > 120s"
                assert metrics["total_jobs"] > 0, "No jobs found in performance test"

                test_data_collector.add_result(
                    test_name, "passed", time.time() - start_time,
                    jobs_found=metrics["total_jobs"]
                )

                print(f"✅ Performance Benchmark: PASSED")
            else:
                raise AssertionError("Performance benchmark search failed")

        except Exception as e:
            test_data_collector.add_result(
                test_name, "failed", time.time() - start_time,
                errors=[str(e)]
            )
            raise