#!/usr/bin/env python3
"""
Debug what's actually inside the QA app iframe
"""
import time
from playwright.sync_api import sync_playwright

def debug_iframe_content():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🔍 Navigating to QA app...")
        page.goto("https://fwcareertest.streamlit.app")

        # Wait for iframe
        iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

        # Wait for Streamlit app inside iframe
        iframe_locator.locator('div[data-testid="stApp"]').wait_for(timeout=30000)
        print("✅ Found Streamlit app inside iframe")

        # Get iframe content
        iframe = page.locator('iframe[title="streamlitApp"]').element_handle()
        iframe_page = iframe.content_frame()

        iframe_content = iframe_page.content()
        print(f"📝 Iframe content length: {len(iframe_content)} characters")

        # Save iframe content
        with open("debug_iframe_content.html", "w") as f:
            f.write(iframe_content)
        print("💾 Iframe content saved as debug_iframe_content.html")

        # Look for input elements specifically
        input_selectors = [
            'input',
            'input[type="text"]',
            'input[type="password"]',
            'input[data-testid="textInput"]',
            'input[placeholder*="sername"]',
            'input[placeholder*="assword"]',
            'div[data-testid="textInput"]',
            'div[class*="input"]'
        ]

        print("\n🔍 Checking for input elements inside iframe:")
        for selector in input_selectors:
            try:
                elements = iframe_locator.locator(selector)
                count = elements.count()
                print(f"   {selector}: {count} elements found")

                if count > 0:
                    for i in range(min(count, 3)):  # Show first 3
                        element = elements.nth(i)
                        try:
                            placeholder = element.get_attribute('placeholder')
                            data_testid = element.get_attribute('data-testid')
                            input_type = element.get_attribute('type')
                            print(f"      [{i}] placeholder='{placeholder}', data-testid='{data_testid}', type='{input_type}'")
                        except:
                            print(f"      [{i}] Could not get attributes")
            except Exception as e:
                print(f"   {selector}: Error - {e}")

        # Look for buttons
        button_selectors = [
            'button',
            'button:has-text("Sign")',
            'button:has-text("Login")',
            'div[data-testid="button"]',
            'div[role="button"]'
        ]

        print("\n🔍 Checking for button elements inside iframe:")
        for selector in button_selectors:
            try:
                elements = iframe_locator.locator(selector)
                count = elements.count()
                print(f"   {selector}: {count} elements found")

                if count > 0:
                    for i in range(min(count, 3)):
                        element = elements.nth(i)
                        try:
                            text = element.text_content()
                            print(f"      [{i}] text='{text[:50]}...'")
                        except:
                            print(f"      [{i}] Could not get text")
            except Exception as e:
                print(f"   {selector}: Error - {e}")

        # Look for any text that might indicate login
        print("\n🔍 Looking for login-related text:")
        login_texts = ["Username", "Password", "Sign In", "Login", "Enter"]
        for text in login_texts:
            try:
                elements = iframe_locator.locator(f'text="{text}"')
                count = elements.count()
                if count > 0:
                    print(f"   Found '{text}': {count} occurrences")
            except:
                pass

        browser.close()

if __name__ == "__main__":
    debug_iframe_content()