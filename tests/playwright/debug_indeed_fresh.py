#!/usr/bin/env python3
"""
Debug script to understand Indeed Fresh button issues
"""
import os
import sys
from playwright.sync_api import sync_playwright
import time

# Load environment variables from secrets
sys.path.append('.')
from run_tests import load_streamlit_secrets
load_streamlit_secrets()

def debug_indeed_fresh():
    print("🔍 Starting Indeed Fresh button debug...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=500)
        page = browser.new_page()

        try:
            # Get credentials
            admin_username = os.getenv("TEST_ADMIN_USERNAME", "james.hazelton")
            admin_password = os.getenv("TEST_ADMIN_PASSWORD", "Tbonbass1!")

            print(f"🔐 Using credentials: {admin_username}")

            # Navigate and login
            page.goto("https://fwcareertest.streamlit.app")
            page.wait_for_timeout(5000)

            # Login
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
            iframe_locator.locator('div[data-testid="stApp"]').wait_for(timeout=30000)
            iframe_locator.locator('input[placeholder="username"]').wait_for(timeout=30000)

            username_input = iframe_locator.locator('input[placeholder="username"]')
            username_input.fill(admin_username)
            password_input = iframe_locator.locator('input[type="password"]')
            password_input.fill(admin_password)
            iframe_locator.locator('button:has-text("Sign In")').click()

            print("⏳ Waiting for login...")
            time.sleep(10)

            # Check if logged in
            page_text = iframe_locator.locator('body').text_content(timeout=10000)
            if "Job Search" in page_text:
                print("✅ Login successful!")
            else:
                print("❌ Login may have failed")
                return

            # Look for all buttons with "Indeed" in the text
            print("\n🔍 Looking for Indeed buttons...")

            # Try different selectors
            selectors_to_try = [
                'button:has-text("Indeed Fresh Only")',
                'button:has-text("🔍 Indeed Fresh Only")',
                'button:has-text("Indeed Fresh")',
                'button:has-text("Fresh Only")',
                'button[aria-label*="Indeed"]',
                'button[aria-label*="Fresh"]'
            ]

            for selector in selectors_to_try:
                try:
                    buttons = iframe_locator.locator(selector)
                    count = buttons.count()
                    print(f"   Selector '{selector}': Found {count} elements")

                    if count > 0:
                        for i in range(count):
                            button_text = buttons.nth(i).text_content(timeout=5000)
                            print(f"     Button {i+1}: '{button_text}'")
                except Exception as e:
                    print(f"   Selector '{selector}': Error - {e}")

            # Get all button text for analysis
            print("\n📋 All buttons on page:")
            try:
                all_buttons = iframe_locator.locator('button')
                button_count = all_buttons.count()
                print(f"Total buttons found: {button_count}")

                for i in range(min(button_count, 20)):  # Limit to first 20 buttons
                    try:
                        button_text = all_buttons.nth(i).text_content(timeout=2000)
                        print(f"   Button {i+1}: '{button_text}'")
                    except:
                        print(f"   Button {i+1}: <unable to get text>")

            except Exception as e:
                print(f"❌ Error getting button list: {e}")

            # Check page content for Indeed mentions
            print("\n🔍 Checking for 'Indeed' mentions in page text...")
            indeed_mentions = []
            lines = page_text.split('\n')
            for i, line in enumerate(lines):
                if 'indeed' in line.lower() or 'fresh' in line.lower():
                    indeed_mentions.append(f"Line {i}: {line.strip()}")

            if indeed_mentions:
                print("Found mentions:")
                for mention in indeed_mentions[:10]:  # Show first 10
                    print(f"   {mention}")
            else:
                print("No 'Indeed' or 'Fresh' mentions found in page text")

        except Exception as e:
            print(f"❌ Major error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    debug_indeed_fresh()