#!/usr/bin/env python3
"""
FreeWorld Success Coach Portal - Comprehensive Test Runner
One-click solution for pre-production testing and validation
"""

import subprocess
import sys
import os
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# Test Configuration
TEST_SUITES = {
    "health_check": {
        "file": "test_health_check.py",
        "description": "Basic application health and connectivity tests",
        "priority": 0,
        "estimated_time": "1-2 minutes"
    },
    "search_paths": {
        "file": "test_search_paths.py",
        "description": "Memory Only and Indeed Fresh Only search paths",
        "priority": 1,
        "estimated_time": "5-10 minutes"
    },
    "classification": {
        "file": "test_classification_accuracy.py",
        "description": "AI classification accuracy and Supabase integration",
        "priority": 2,
        "estimated_time": "8-12 minutes"
    },
    "scheduled_search": {
        "file": "test_scheduled_search.py",
        "description": "Batch search and scheduled processing",
        "priority": 3,
        "estimated_time": "10-15 minutes"
    },
    "link_tracking": {
        "file": "test_link_tracking.py",
        "description": "Link generation and tracking system",
        "priority": 4,
        "estimated_time": "3-5 minutes"
    },
    "agent_portal_links": {
        "file": "test_agent_portal_links.py",
        "description": "Agent portal link compatibility (legacy and new system)",
        "priority": 5,
        "estimated_time": "4-6 minutes"
    }
}

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")

    required_packages = [
        ("playwright", "playwright"),
        ("pytest", "pytest"),
        ("python-dotenv", "dotenv")
    ]

    missing_packages = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install playwright pytest python-dotenv")
        return False

    # Check if Playwright browsers are installed
    try:
        result = subprocess.run(["playwright", "install", "--help"],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Playwright not properly installed")
            print("Install browsers with: playwright install")
            return False
    except FileNotFoundError:
        print("❌ Playwright command not found")
        print("Install with: pip install playwright && playwright install")
        return False

    print("✅ All dependencies satisfied")
    return True

def check_project_structure():
    """Check if we're in the correct project directory"""
    print("🔍 Checking project structure...")

    # Look for the main project directory
    test_dir = os.path.dirname(__file__)
    project_dir = os.path.dirname(os.path.dirname(test_dir))

    required_files = [
        "app.py",
        "pipeline_v3.py",
        "job_scraper.py",
        "supabase_utils.py"
    ]

    missing_files = []
    for file in required_files:
        file_path = os.path.join(project_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)

    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        print(f"📁 Expected in: {project_dir}")
        print("💡 Make sure you're running from the correct directory")
        return False

    print("✅ Project structure verified")
    return True

def load_streamlit_secrets():
    """Load environment variables from .streamlit/secrets.toml"""
    secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".streamlit", "secrets.toml")

    if os.path.exists(secrets_path):
        try:
            import toml
            secrets = toml.load(secrets_path)
            # Handle both flat structure and sectioned structure
            for key, value in secrets.items():
                if isinstance(value, dict):
                    # Handle [secrets] section
                    for subkey, subvalue in value.items():
                        if subkey not in os.environ:
                            os.environ[subkey] = str(subvalue)
                else:
                    # Handle flat keys
                    if key not in os.environ:
                        os.environ[key] = str(value)
            return True
        except ImportError:
            # If toml is not available, try simple parsing
            try:
                with open(secrets_path, 'r') as f:
                    current_section = None
                    for line in f:
                        line = line.strip()
                        if line.startswith('[') and line.endswith(']'):
                            current_section = line[1:-1]
                            continue
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            key = key.strip().strip('"')
                            value = value.strip().strip('"')
                            if key not in os.environ:
                                os.environ[key] = value
                return True
            except Exception as e:
                print(f"⚠️  Could not parse secrets.toml: {e}")
                return False
        except Exception as e:
            print(f"⚠️  Could not load secrets.toml: {e}")
            return False
    return False

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment configuration...")

    # Try to load from .streamlit/secrets.toml first
    load_streamlit_secrets()

    required_env_vars = [
        "OPENAI_API_KEY",
        "OUTSCRAPER_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SHORT_IO_API_KEY",
        "SHORT_DOMAIN"
    ]

    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Check your .streamlit/secrets.toml or .env file")
        return False

    print("✅ Environment configuration complete")
    return True

def start_streamlit_server():
    """Start Streamlit server for testing"""
    print("🚀 Starting Streamlit server...")

    # Check if server is already running
    try:
        import requests
        response = requests.get("http://localhost:8501", timeout=2)
        if response.status_code == 200:
            print("✅ Streamlit server already running")
            return None
    except:
        pass

    # Start new server from the main project directory
    main_project_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    app_path = os.path.join(main_project_dir, "app.py")

    if not os.path.exists(app_path):
        print(f"❌ app.py not found at {app_path}")
        return False

    try:
        # Start Streamlit with explicit configuration
        process = subprocess.Popen(
            [
                "streamlit", "run", app_path,
                "--server.port=8501",
                "--server.headless=true",
                "--server.enableCORS=false",
                "--server.enableXsrfProtection=false",
                "--browser.gatherUsageStats=false"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=main_project_dir,
            env={**os.environ, "STREAMLIT_SERVER_PORT": "8501"}
        )

        # Wait for server to start with longer timeout and better checking
        print("⏳ Waiting for Streamlit server to start...")
        import requests

        for attempt in range(30):  # 30 attempts with 2s intervals = 60s timeout
            try:
                response = requests.get("http://localhost:8501", timeout=2)
                if response.status_code == 200:
                    print("✅ Streamlit server started successfully")
                    time.sleep(2)  # Give it a moment to fully initialize
                    return process
            except:
                pass

            time.sleep(2)

            # Check if process is still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print(f"❌ Streamlit process exited early")
                print(f"📋 STDOUT: {stdout.decode()[:500]}")
                print(f"📋 STDERR: {stderr.decode()[:500]}")
                return False

        print("❌ Streamlit server failed to start within 60 seconds")
        return False

    except Exception as e:
        print(f"❌ Failed to start Streamlit server: {e}")
        return False


def run_test_suite(suite_name: str, verbose: bool = False) -> dict:
    """Run a specific test suite"""
    suite = TEST_SUITES.get(suite_name)
    if not suite:
        return {"status": "error", "message": f"Unknown test suite: {suite_name}"}

    print(f"\n🧪 Running {suite_name} tests...")
    print(f"📋 {suite['description']}")
    print(f"⏱️ Estimated time: {suite['estimated_time']}")

    start_time = time.time()

    # Run pytest with appropriate options
    cmd = [
        "python", "-m", "pytest",
        suite["file"],
        "-v" if verbose else "-q",
        "--tb=short",
        f"--junitxml=reports/{suite_name}_results.xml"
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )

        duration = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ {suite_name} tests PASSED ({duration:.1f}s)")
            return {
                "status": "passed",
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        else:
            print(f"❌ {suite_name} tests FAILED ({duration:.1f}s)")
            return {
                "status": "failed",
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }

    except subprocess.TimeoutExpired:
        print(f"⏰ {suite_name} tests TIMEOUT")
        return {
            "status": "timeout",
            "duration": 1800,
            "message": "Test suite exceeded 30 minute timeout"
        }
    except Exception as e:
        print(f"💥 {suite_name} tests ERROR: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def generate_report(results: dict):
    """Generate comprehensive test report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"reports/test_report_{timestamp}.json"

    # Ensure reports directory exists
    os.makedirs("reports", exist_ok=True)

    # Calculate summary statistics
    total_suites = len(results)
    passed_suites = len([r for r in results.values() if r["status"] == "passed"])
    failed_suites = len([r for r in results.values() if r["status"] == "failed"])
    error_suites = len([r for r in results.values() if r["status"] == "error"])
    timeout_suites = len([r for r in results.values() if r["status"] == "timeout"])

    total_duration = sum(r.get("duration", 0) for r in results.values())

    summary = {
        "test_run_timestamp": timestamp,
        "total_suites": total_suites,
        "passed_suites": passed_suites,
        "failed_suites": failed_suites,
        "error_suites": error_suites,
        "timeout_suites": timeout_suites,
        "success_rate": (passed_suites / total_suites * 100) if total_suites > 0 else 0,
        "total_duration": total_duration,
        "results": results
    }

    # Save JSON report
    with open(report_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print(f"\n📊 TEST SUMMARY")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"📅 Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Total Duration: {total_duration:.1f} seconds")
    print(f"📦 Test Suites: {total_suites}")
    print(f"✅ Passed: {passed_suites}")
    print(f"❌ Failed: {failed_suites}")
    print(f"💥 Errors: {error_suites}")
    print(f"⏰ Timeouts: {timeout_suites}")
    print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
    print(f"📄 Report: {report_file}")

    # Print detailed results
    print(f"\n📋 DETAILED RESULTS")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    for suite_name, result in results.items():
        status_emoji = {
            "passed": "✅",
            "failed": "❌",
            "error": "💥",
            "timeout": "⏰"
        }.get(result["status"], "❓")

        duration = result.get("duration", 0)
        print(f"{status_emoji} {suite_name}: {result['status'].upper()} ({duration:.1f}s)")

        if result["status"] != "passed" and "message" in result:
            print(f"   └─ {result['message']}")

    return summary

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="FreeWorld Success Coach Portal Test Runner")
    parser.add_argument("--suites", nargs="+", choices=list(TEST_SUITES.keys()) + ["all"],
                       default=["all"], help="Test suites to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--skip-env-check", action="store_true", help="Skip environment validation")
    parser.add_argument("--skip-server-start", action="store_true", default=True, help="Skip starting Streamlit server (default: True for QA testing)")

    args = parser.parse_args()

    print("🎯 FreeWorld Success Coach Portal - Test Runner")
    print("="*60)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check project structure
    if not check_project_structure():
        sys.exit(1)

    # Check environment (unless skipped)
    if not args.skip_env_check and not check_environment():
        print("⚠️  Environment check failed. Use --skip-env-check to proceed anyway.")
        sys.exit(1)

    # Start Streamlit server (unless skipped)
    streamlit_process = None
    if not args.skip_server_start:
        streamlit_process = start_streamlit_server()
        if streamlit_process is None:
            # None means server was already running, which is fine
            pass
        elif streamlit_process == False:
            # False means failed to start
            print("⚠️  Could not start Streamlit server.")
            print("💡 Troubleshooting tips:")
            print("   - Ensure you're in the correct directory")
            print("   - Check if app.py exists")
            print("   - Try running manually: streamlit run app.py")
            print("   - Use --skip-server-start if server is already running")
            sys.exit(1)

    try:
        # Determine which suites to run
        if "all" in args.suites:
            suites_to_run = list(TEST_SUITES.keys())
        else:
            suites_to_run = args.suites

        # Sort by priority
        suites_to_run.sort(key=lambda x: TEST_SUITES[x]["priority"])

        print(f"\n🧪 Running {len(suites_to_run)} test suites:")
        for suite in suites_to_run:
            print(f"   {TEST_SUITES[suite]['priority']}. {suite} - {TEST_SUITES[suite]['description']}")

        # Run test suites
        results = {}
        total_start_time = time.time()

        for suite_name in suites_to_run:
            results[suite_name] = run_test_suite(suite_name, args.verbose)

            # Short pause between suites
            if suite_name != suites_to_run[-1]:
                time.sleep(2)

        # Generate final report
        summary = generate_report(results)

        # Determine exit code
        if summary["failed_suites"] == 0 and summary["error_suites"] == 0:
            print(f"\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
            exit_code = 0
        else:
            print(f"\n⚠️  SOME TESTS FAILED - Review report for details")
            exit_code = 1

    except KeyboardInterrupt:
        print(f"\n🛑 Test run interrupted by user")
        exit_code = 130
    except Exception as e:
        print(f"\n💥 Test run failed with error: {e}")
        exit_code = 1
    finally:
        # Clean up Streamlit server
        if streamlit_process:
            print(f"\n🛑 Stopping Streamlit server...")
            streamlit_process.terminate()
            try:
                streamlit_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                streamlit_process.kill()

    sys.exit(exit_code)

if __name__ == "__main__":
    main()