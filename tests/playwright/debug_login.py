#!/usr/bin/env python3
"""
Debug what happens after login
"""
import time
from playwright.sync_api import sync_playwright

def debug_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=1000)
        page = browser.new_page()

        print("🔍 Navigating to QA app...")
        page.goto("https://fwcareertest.streamlit.app")

        # Login
        iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
        iframe_locator.locator('div[data-testid="stApp"]').wait_for()

        iframe_locator.locator('input[placeholder="username"]').wait_for()
        username_input = iframe_locator.locator('input[placeholder="username"]')
        username_input.fill("james.hazelton")

        password_input = iframe_locator.locator('input[type="password"]')
        password_input.fill("Tbonbass1!")

        iframe_locator.locator('button:has-text("Sign In")').click()
        time.sleep(5)
        print("✅ Logged in successfully")

        # Check what text is actually available
        try:
            page_text = iframe_locator.locator('body').text_content()
            print(f"📝 Page text content (first 1000 chars): {page_text[:1000]}...")

            # Look for common elements that might appear
            common_elements = [
                "Search Parameters", "Location", "Search Terms", "Memory Only",
                "Indeed Fresh", "CDL Traditional", "Career Pathways",
                "Analytics", "Queue", "Create", "Run Search", "Dashboard"
            ]

            found_elements = []
            for element in common_elements:
                if element in page_text:
                    found_elements.append(element)

            print(f"✅ Found elements: {found_elements}")

        except Exception as e:
            print(f"💥 Error getting page text: {e}")

        browser.close()

if __name__ == "__main__":
    debug_login()
