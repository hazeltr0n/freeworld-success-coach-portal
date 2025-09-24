#!/usr/bin/env python3
"""
Updated Test Runner for FreeWorld Success Coach Portal
Runs all updated tests to verify current UI compatibility
"""

import subprocess
import sys
import os
import json
from datetime import datetime

def run_test_suite():
    """Run comprehensive test suite with updated UI elements"""

    print("🚀 FreeWorld Success Coach Portal - Updated Test Suite")
    print("=" * 60)
    print("Testing current UI compatibility and new features")
    print("=" * 60)

    # Test configuration
    test_order = [
        {
            "name": "Health Check",
            "file": "test_health_check.py",
            "description": "Basic system functionality"
        },
        {
            "name": "Coach Login",
            "file": "test_coach_login.py",
            "description": "Authentication system"
        },
        {
            "name": "Batches & Scheduling",
            "file": "test_batches_scheduling.py",
            "description": "New batch scheduling features"
        },
        {
            "name": "Master Efficient Test",
            "file": "test_master_efficient.py::TestMasterEfficient::test_master_comprehensive_validation",
            "description": "Complete system validation"
        },
        {
            "name": "Performance Benchmark",
            "file": "test_master_efficient.py::TestMasterPerformance::test_master_performance_benchmark",
            "description": "System performance validation"
        }
    ]

    # Set environment for headed mode if available
    if os.environ.get("DISPLAY") or os.environ.get("PLAYWRIGHT_HEADED") == "1":
        os.environ["PLAYWRIGHT_HEADED"] = "1"
        print("🖥️ Running in headed mode")
    else:
        print("🔄 Running in headless mode")

    results = []
    total_start_time = datetime.now()

    for test in test_order:
        print(f"\n🧪 Running {test['name']}")
        print(f"   📝 {test['description']}")
        print(f"   📁 {test['file']}")

        start_time = datetime.now()

        # Run pytest with verbose output and timeout
        cmd = [
            sys.executable, "-m", "pytest",
            test['file'],
            "-v", "-s",
            "--tb=short",
            "--timeout=300"  # 5 minute timeout per test
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute overall timeout
                cwd=os.path.dirname(__file__)
            )

            duration = (datetime.now() - start_time).total_seconds()

            if result.returncode == 0:
                print(f"   ✅ PASSED ({duration:.1f}s)")
                status = "PASSED"
            else:
                print(f"   ❌ FAILED ({duration:.1f}s)")
                status = "FAILED"
                print(f"   📋 Error output:\n{result.stderr[:500]}")

            results.append({
                "name": test['name'],
                "file": test['file'],
                "status": status,
                "duration": duration,
                "stdout": result.stdout[:1000],  # First 1000 chars
                "stderr": result.stderr[:1000]   # First 1000 chars
            })

        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"   ⏰ TIMEOUT ({duration:.1f}s)")
            results.append({
                "name": test['name'],
                "file": test['file'],
                "status": "TIMEOUT",
                "duration": duration,
                "error": "Test exceeded timeout limit"
            })

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"   💥 ERROR ({duration:.1f}s): {e}")
            results.append({
                "name": test['name'],
                "file": test['file'],
                "status": "ERROR",
                "duration": duration,
                "error": str(e)
            })

    # Generate summary report
    total_duration = (datetime.now() - total_start_time).total_seconds()

    print("\n" + "=" * 60)
    print("🎯 TEST SUITE SUMMARY")
    print("=" * 60)

    passed = len([r for r in results if r['status'] == 'PASSED'])
    failed = len([r for r in results if r['status'] == 'FAILED'])
    timeout = len([r for r in results if r['status'] == 'TIMEOUT'])
    error = len([r for r in results if r['status'] == 'ERROR'])
    total = len(results)

    print(f"📊 Results: {passed}/{total} passed")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏰ Timeout: {timeout}")
    print(f"💥 Error: {error}")
    print(f"⏱️ Total Duration: {total_duration:.1f}s")
    print(f"🎭 Pass Rate: {(passed/total*100):.1f}%")

    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    for result in results:
        status_emoji = {
            'PASSED': '✅', 'FAILED': '❌',
            'TIMEOUT': '⏰', 'ERROR': '💥'
        }
        print(f"{status_emoji.get(result['status'], '❓')} {result['name']}: {result['status']} ({result['duration']:.1f}s)")

    # Save detailed report
    report = {
        "timestamp": total_start_time.isoformat(),
        "total_duration": total_duration,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "timeout": timeout,
            "error": error,
            "pass_rate": passed/total*100
        },
        "results": results
    }

    report_file = f"reports/updated_tests_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("reports", exist_ok=True)

    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Detailed report saved: {report_file}")

    # Recommendations based on results
    print(f"\n💡 RECOMMENDATIONS:")

    if passed == total:
        print("🎉 All tests passed! UI updates are working correctly.")
        print("✅ Ready to proceed with tutorial generation.")
    elif passed >= total * 0.8:
        print("👍 Most tests passed. Minor issues to address:")
        failed_tests = [r['name'] for r in results if r['status'] != 'PASSED']
        for test in failed_tests:
            print(f"   - Fix issues in {test}")
    else:
        print("⚠️ Significant test failures detected:")
        print("   - Review navigation selectors")
        print("   - Check UI element changes")
        print("   - Verify permissions and access controls")
        failed_tests = [r['name'] for r in results if r['status'] != 'PASSED']
        for test in failed_tests:
            print(f"   - Critical: {test}")

    return passed == total

if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)