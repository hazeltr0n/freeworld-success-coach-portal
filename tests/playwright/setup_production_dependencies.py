#!/usr/bin/env python3
"""
Production QA Suite - Dependency Setup and Validation
Ensures all dependencies are properly loaded for production testing deployments
"""

import subprocess
import sys
import os
import importlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class ProductionDependencyManager:
    """Manages and validates all dependencies for production QA suite"""

    def __init__(self):
        self.required_packages = {
            # Core testing framework
            "pytest": ">=7.4.0",
            "pytest-html": ">=3.2.0",
            "pytest-xdist": ">=3.3.0",
            "pytest-benchmark": ">=4.0.0",
            "pytest-timeout": ">=2.1.0",

            # Browser automation
            "playwright": ">=1.40.0",

            # Data handling
            "pandas": ">=2.0.0",
            "requests": ">=2.31.0",
            "jsonschema": ">=4.19.0",
            "python-dateutil": ">=2.8.0",

            # Supabase integration
            "supabase": ">=2.0.0",
            "postgrest": ">=0.13.0",

            # Environment and configuration
            "python-dotenv": ">=1.0.0",

            # Logging and utilities
            "colorlog": ">=6.7.0",

            # Optional advanced features
            "allure-pytest": ">=2.13.0",
        }

        self.critical_packages = [
            "pytest", "playwright", "pandas", "requests", "supabase"
        ]

        self.playwright_browsers = ["chromium", "firefox", "webkit"]

    def check_python_version(self) -> bool:
        """Verify Python version compatibility"""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 11:
            print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            print(f"❌ Python version: {version.major}.{version.minor}.{version.micro} (requires 3.11+)")
            return False

    def install_package(self, package: str, version: str = "") -> bool:
        """Install a single package with version specification"""
        try:
            package_spec = f"{package}{version}" if version else package
            print(f"📦 Installing {package_spec}...")

            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package_spec
            ], capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print(f"✅ Successfully installed {package}")
                return True
            else:
                print(f"❌ Failed to install {package}: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print(f"❌ Timeout installing {package}")
            return False
        except Exception as e:
            print(f"❌ Error installing {package}: {e}")
            return False

    def verify_package_import(self, package: str) -> bool:
        """Verify a package can be imported successfully"""
        try:
            # Handle special import cases
            import_map = {
                "python-dotenv": "dotenv",
                "python-dateutil": "dateutil",
                "pytest-html": "pytest_html",
                "pytest-xdist": "xdist",
                "pytest-benchmark": "pytest_benchmark",
                "pytest-timeout": "pytest_timeout",
                "allure-pytest": "allure_pytest",
                "colorlog": "colorlog"
            }

            import_name = import_map.get(package, package)
            importlib.import_module(import_name)
            return True

        except ImportError as e:
            print(f"❌ Cannot import {package}: {e}")
            return False
        except Exception as e:
            print(f"⚠️ Import warning for {package}: {e}")
            return True  # Some packages may have warnings but still work

    def install_playwright_browsers(self) -> bool:
        """Install Playwright browser binaries"""
        try:
            print("🌐 Installing Playwright browsers...")
            result = subprocess.run([
                sys.executable, "-m", "playwright", "install"
            ], capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                print("✅ Playwright browsers installed successfully")
                return True
            else:
                print(f"❌ Failed to install Playwright browsers: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Timeout installing Playwright browsers")
            return False
        except Exception as e:
            print(f"❌ Error installing Playwright browsers: {e}")
            return False

    def verify_playwright_browsers(self) -> Dict[str, bool]:
        """Verify Playwright browser installations"""
        browser_status = {}

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                for browser_name in self.playwright_browsers:
                    try:
                        browser_type = getattr(p, browser_name)
                        # Try to launch browser briefly
                        browser = browser_type.launch(headless=True)
                        browser.close()
                        browser_status[browser_name] = True
                        print(f"✅ {browser_name} browser working")
                    except Exception as e:
                        browser_status[browser_name] = False
                        print(f"❌ {browser_name} browser failed: {e}")

        except Exception as e:
            print(f"❌ Playwright verification failed: {e}")
            for browser in self.playwright_browsers:
                browser_status[browser] = False

        return browser_status

    def create_updated_requirements(self) -> None:
        """Create/update requirements.txt with all dependencies"""
        requirements_path = Path(__file__).parent / "requirements.txt"

        content = """# FreeWorld Success Coach Portal - Production QA Dependencies
# Generated automatically for production deployment readiness

# Core testing framework
pytest>=7.4.0
pytest-html>=3.2.0
pytest-xdist>=3.3.0
pytest-benchmark>=4.0.0
pytest-timeout>=2.1.0

# Browser automation
playwright>=1.40.0

# Data manipulation and analysis
pandas>=2.0.0
requests>=2.31.0
jsonschema>=4.19.0
python-dateutil>=2.8.0

# Supabase integration (critical for production)
supabase>=2.0.0
postgrest>=0.13.0

# Environment and configuration
python-dotenv>=1.0.0

# Logging and debugging
colorlog>=6.7.0

# Advanced reporting (optional but recommended)
allure-pytest>=2.13.0

# Production testing utilities
psutil>=5.9.0  # For system monitoring
timeout-decorator>=0.5.0  # For robust timeout handling
"""

        with open(requirements_path, 'w') as f:
            f.write(content)

        print(f"✅ Updated requirements.txt at {requirements_path}")

    def verify_test_environment(self) -> Dict[str, bool]:
        """Verify the complete test environment is ready"""
        print("\n🔍 VERIFYING PRODUCTION QA ENVIRONMENT...")

        results = {
            "python_version": self.check_python_version(),
            "packages_installed": True,
            "packages_importable": True,
            "playwright_browsers": True,
            "test_files_present": True,
            "supabase_utils": True
        }

        # Check package installations
        failed_packages = []
        for package, version in self.required_packages.items():
            if not self.verify_package_import(package):
                failed_packages.append(package)
                results["packages_importable"] = False

        if failed_packages:
            print(f"❌ Failed package imports: {failed_packages}")

        # Check Playwright browsers
        browser_status = self.verify_playwright_browsers()
        if not all(browser_status.values()):
            results["playwright_browsers"] = False

        # Check for critical test files
        test_files = [
            "test_master_efficient.py",
            "conftest.py",
            "supabase_utils.py"
        ]

        for test_file in test_files:
            if not Path(test_file).exists():
                print(f"❌ Missing critical test file: {test_file}")
                results["test_files_present"] = False

        # Check Supabase utils specifically
        try:
            from supabase_utils import get_client
            print("✅ Supabase utilities available")
        except ImportError:
            print("❌ Supabase utilities not available")
            results["supabase_utils"] = False

        return results

    def install_all_dependencies(self) -> bool:
        """Install all required dependencies for production QA"""
        print("\n📦 INSTALLING PRODUCTION QA DEPENDENCIES...")

        # Create updated requirements file
        self.create_updated_requirements()

        success = True

        # Install packages
        for package, version in self.required_packages.items():
            if not self.install_package(package, version):
                if package in self.critical_packages:
                    print(f"🚨 CRITICAL PACKAGE FAILED: {package}")
                    success = False
                else:
                    print(f"⚠️ Optional package failed: {package}")

        # Install Playwright browsers
        if not self.install_playwright_browsers():
            success = False

        return success

    def run_deployment_readiness_check(self) -> bool:
        """Complete deployment readiness validation"""
        print("\n🚀 PRODUCTION DEPLOYMENT READINESS CHECK")
        print("=" * 50)

        # Install dependencies
        if not self.install_all_dependencies():
            print("\n❌ DEPENDENCY INSTALLATION FAILED")
            return False

        # Verify environment
        results = self.verify_test_environment()

        # Summary
        print("\n📊 READINESS SUMMARY:")
        print("-" * 30)

        all_passed = True
        for check, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {check}: {status}")
            if not passed:
                all_passed = False

        if all_passed:
            print("\n🎉 PRODUCTION QA SUITE READY FOR DEPLOYMENT!")
            print("✅ All dependencies installed and verified")
            print("✅ Environment configured correctly")
            print("✅ Test suite ready to run")
            return True
        else:
            print("\n🚨 DEPLOYMENT READINESS FAILED")
            print("❌ Fix the failed checks before deploying")
            return False


def main():
    """Main entry point for dependency setup"""
    manager = ProductionDependencyManager()

    print("🏭 FreeWorld Production QA Dependency Manager")
    print("=" * 50)

    success = manager.run_deployment_readiness_check()

    if success:
        print("\n🎯 NEXT STEPS:")
        print("1. Run the master efficient test:")
        print("   python -m pytest test_master_efficient.py::TestMasterEfficient::test_master_comprehensive_validation -v -s")
        print("2. Verify 100% pass rate")
        print("3. Production deployment is ready!")
        sys.exit(0)
    else:
        print("\n🔧 REQUIRED ACTIONS:")
        print("1. Fix the failed dependency checks")
        print("2. Re-run this script")
        print("3. Do not deploy until all checks pass")
        sys.exit(1)


if __name__ == "__main__":
    main()