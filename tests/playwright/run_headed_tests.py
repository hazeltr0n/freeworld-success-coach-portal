#!/usr/bin/env python3
"""
Run Playwright tests with visible browser for debugging
"""

import subprocess
import sys
import os
from pathlib import Path

def run_headed_tests():
    """Run tests with visible browser"""

    # Set environment for headed mode
    env = os.environ.copy()
    env["PLAYWRIGHT_HEADED"] = "1"

    # Check if we're in a GUI environment
    if not env.get("DISPLAY"):
        print("🖥️  No DISPLAY found. Installing and using xvfb for virtual display...")

        # Install xvfb if not available
        try:
            subprocess.run(["xvfb-run", "--help"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("📦 Installing xvfb...")
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "xvfb"], check=True)

        # Run with virtual display
        cmd = [
            "xvfb-run",
            "-a",  # Auto servernum
            "--server-args=-screen 0 1920x1080x24",  # Set screen size
            "python", "-m", "pytest",
            "test_health_check.py",
            "-v", "-s",
            "--headed"  # Force headed mode
        ]

        print("🚀 Running tests with virtual display (xvfb)...")
        print("Note: Browser will run but won't be visible in this environment")

    else:
        # Run normally with visible browser
        cmd = [
            "python", "-m", "pytest",
            "test_health_check.py",
            "-v", "-s",
            "--headed"
        ]
        print("🚀 Running tests with visible browser...")

    # Set working directory
    test_dir = Path(__file__).parent

    # Run the tests
    result = subprocess.run(cmd, cwd=test_dir, env=env)

    if result.returncode == 0:
        print("✅ Tests completed successfully!")
    else:
        print("❌ Tests failed or had errors")

    return result.returncode

if __name__ == "__main__":
    sys.exit(run_headed_tests())