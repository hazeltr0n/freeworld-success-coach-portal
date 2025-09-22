#!/usr/bin/env python3
"""
Debug page structure for QA app
"""
import time
from playwright.sync_api import sync_playwright

def debug_qa_app():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🔍 Navigating to QA app...")
        page.goto("https://fwcareertest.streamlit.app")

        # Wait a moment for page to load
        time.sleep(5)

        # Take screenshot
        page.screenshot(path="debug_screenshot.png")
        print("📸 Screenshot saved as debug_screenshot.png")

        # Get page title
        title = page.title()
        print(f"📄 Page title: {title}")

        # Get page content
        content = page.content()
        print(f"📝 Page content length: {len(content)} characters")

        # Look for common Streamlit elements
        streamlit_selectors = [
            'div[data-testid="stApp"]',
            'div[data-testid="main"]',
            'div[data-testid="stSidebar"]',
            'div[class*="streamlit"]',
            'div[id*="streamlit"]',
            '.main',
            '.stApp',
            'input[data-testid="textInput"]'
        ]

        print("\n🔍 Checking for Streamlit elements:")
        for selector in streamlit_selectors:
            try:
                elements = page.locator(selector)
                count = elements.count()
                print(f"   {selector}: {count} elements found")
                if count > 0:
                    # Get the first element's details
                    first_element = elements.first
                    if first_element.is_visible():
                        print(f"      → First element is visible")
                    else:
                        print(f"      → First element is NOT visible")
            except Exception as e:
                print(f"   {selector}: Error - {e}")

        # Check if there's any error message on the page
        error_indicators = [
            'text*="error"',
            'text*="Error"',
            'text*="failed"',
            'text*="Failed"',
            'text*="loading"',
            'text*="Loading"'
        ]

        print("\n⚠️ Checking for error indicators:")
        for indicator in error_indicators:
            try:
                elements = page.locator(indicator)
                count = elements.count()
                if count > 0:
                    print(f"   {indicator}: {count} found")
                    for i in range(min(count, 3)):  # Show first 3
                        text = elements.nth(i).text_content()
                        print(f"      → {text[:100]}...")
            except:
                pass

        # Save page source for inspection
        with open("debug_page_source.html", "w") as f:
            f.write(content)
        print("\n💾 Page source saved as debug_page_source.html")

        browser.close()

if __name__ == "__main__":
    debug_qa_app()