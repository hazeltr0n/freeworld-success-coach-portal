#!/usr/bin/env python3
"""
Initialize Test Environment
Ensures all dependencies are installed for fresh test environments
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required test dependencies"""
    print("📦 Installing test dependencies...")

    requirements = [
        "pytest>=7.4.0",
        "playwright>=1.40.0",
        "requests>=2.31.0",
        "pandas>=2.0.0",
        "supabase>=2.0.0",
        "python-dotenv>=1.0.0"
    ]

    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install"
        ] + requirements, check=True)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Dependency installation failed: {e}")
        return False

def install_playwright_browsers():
    """Install Playwright browsers"""
    print("🌐 Installing Playwright browsers...")

    try:
        # Install Playwright browsers
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install"
        ], capture_output=True, text=True, timeout=600)

        if result.returncode == 0:
            print("✅ Playwright browsers installed")
            return True
        else:
            print(f"❌ Browser installation failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Browser installation timed out")
        return False
    except Exception as e:
        print(f"❌ Browser installation error: {e}")
        return False

def verify_installation():
    """Verify the installation works"""
    print("🔍 Verifying installation...")

    try:
        # Test Playwright import and browser launch
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()

        print("✅ Installation verified successfully")
        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main initialization function"""
    print("🚀 Initializing Test Environment")
    print("=" * 40)

    success = True

    # Install dependencies
    if not install_dependencies():
        success = False

    # Install browsers
    if success and not install_playwright_browsers():
        success = False

    # Verify installation
    if success and not verify_installation():
        success = False

    if success:
        print("\n🎉 Test environment ready!")
        print("Run tests with: python -m pytest test_master_efficient.py -v -s")
        return 0
    else:
        print("\n❌ Test environment setup failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())