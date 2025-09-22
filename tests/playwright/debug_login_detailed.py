#!/usr/bin/env python3
"""
Debug script to understand login failure in detail
"""
import os
import sys
from playwright.sync_api import sync_playwright
import time

# Load environment variables from secrets
sys.path.append('.')
from run_tests import load_streamlit_secrets
load_streamlit_secrets()

def debug_login():
    print("🔍 Starting detailed login debug...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=500)  # Headless for codespaces
        page = browser.new_page()

        try:
            # Get credentials
            admin_username = os.getenv("TEST_ADMIN_USERNAME", "james.hazelton")
            admin_password = os.getenv("TEST_ADMIN_PASSWORD", "Tbonbass1!")

            print(f"🔐 Using credentials: {admin_username} / {admin_password[:3]}...")

            # Navigate to app
            print("🌐 Navigating to app...")
            page.goto("https://fwcareertest.streamlit.app")

            # Wait for page to load
            print("⏳ Waiting for page to load...")
            page.wait_for_timeout(5000)

            # Take screenshot of initial page
            page.screenshot(path="debug_initial_page.png")
            print("📸 Screenshot saved: debug_initial_page.png")

            # Look for iframe
            print("🔍 Looking for iframe...")
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

            # Wait for iframe content
            print("⏳ Waiting for iframe content...")
            try:
                iframe_locator.locator('div[data-testid="stApp"]').wait_for(timeout=10000)
                print("✅ Iframe content loaded")
            except Exception as e:
                print(f"❌ Error waiting for iframe: {e}")

            # Take screenshot inside iframe
            try:
                iframe_locator.locator('body').screenshot(path="debug_iframe_content.png")
                print("📸 Iframe screenshot saved: debug_iframe_content.png")
            except Exception as e:
                print(f"❌ Error taking iframe screenshot: {e}")

            # Look for login form
            print("🔍 Looking for login form...")
            try:
                username_input = iframe_locator.locator('input[placeholder="username"]')
                if username_input.count() > 0:
                    print("✅ Found username input")
                    username_input.fill(admin_username)
                    print(f"✅ Entered username: {admin_username}")
                else:
                    print("❌ Username input not found")

                password_input = iframe_locator.locator('input[type="password"]')
                if password_input.count() > 0:
                    print("✅ Found password input")
                    password_input.fill(admin_password)
                    print("✅ Entered password")
                else:
                    print("❌ Password input not found")

                sign_in_button = iframe_locator.locator('button:has-text("Sign In")')
                if sign_in_button.count() > 0:
                    print("✅ Found Sign In button")
                    sign_in_button.click()
                    print("✅ Clicked Sign In button")
                else:
                    print("❌ Sign In button not found")

            except Exception as e:
                print(f"❌ Error during login: {e}")

            # Wait for login to process
            print("⏳ Waiting for login to process...")
            page.wait_for_timeout(10000)

            # Take screenshot after login
            try:
                iframe_locator.locator('body').screenshot(path="debug_after_login.png")
                print("📸 After login screenshot saved: debug_after_login.png")
            except Exception as e:
                print(f"❌ Error taking after login screenshot: {e}")

            # Check for login success indicators
            print("🔍 Checking for login success...")
            try:
                page_text = iframe_locator.locator('body').text_content()

                success_indicators = [
                    "Search Parameters", "Memory Only", "Indeed Fresh",
                    "Location", "Search Terms", "Analytics", "Admin Panel",
                    "Job Search", "Batches", "Free Agents"
                ]

                found_indicators = []
                for indicator in success_indicators:
                    if indicator in page_text:
                        found_indicators.append(indicator)

                print(f"📊 Found {len(found_indicators)} success indicators: {found_indicators}")

                if len(found_indicators) >= 3:
                    print("✅ Login appears successful!")
                else:
                    print("❌ Login may have failed")
                    print("📄 Full page text (first 500 chars):")
                    print(page_text[:500])

            except Exception as e:
                print(f"❌ Error checking page content: {e}")

            # Save final page content for analysis
            print("💾 Saving final page content...")
            with open("debug_final_content.html", "w") as f:
                f.write(page.content())
            print("📄 Content saved to: debug_final_content.html")

        except Exception as e:
            print(f"❌ Major error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    debug_login()