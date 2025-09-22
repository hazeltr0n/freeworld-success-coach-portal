#!/usr/bin/env python3
"""
Debug script to find actual navigation tab names in the app
"""
import os
from playwright.sync_api import sync_playwright

def debug_tabs():
    # Set credentials
    os.environ["TEST_ADMIN_USERNAME"] = "james.hazelton"
    os.environ["TEST_ADMIN_PASSWORD"] = "Tbonbass1!"

    from conftest import login_as_admin

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()

        try:
            # Login as admin
            login_as_admin(page)

            # Get iframe
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

            # Get all text content and look for tab-like elements
            print("\n🔍 Searching for navigation elements...")

            # Try different selectors for tabs/navigation
            potential_selectors = [
                'div[data-testid="stSidebar"]',
                'div[data-testid="stTabs"]',
                'button[role="tab"]',
                'div[role="tablist"]',
                'text*="Management"',
                'text*="Dashboard"',
                'text*="Analytics"',
                'text*="Search"',
                'text*="Agent"'
            ]

            for selector in potential_selectors:
                try:
                    elements = iframe_locator.locator(selector)
                    count = elements.count()
                    if count > 0:
                        print(f"✅ Found {count} elements with selector: {selector}")
                        for i in range(min(count, 3)):  # Show first 3
                            try:
                                text = elements.nth(i).text_content()
                                print(f"   Text: '{text}'")
                            except:
                                pass
                except Exception as e:
                    print(f"❌ Selector failed: {selector} - {e}")

            # Get full page text and search for keywords
            print("\n📝 Full page keywords search:")
            try:
                page_text = iframe_locator.locator('body').text_content()

                keywords = ["Agent", "Analytics", "Dashboard", "Search", "Management", "Batch"]
                for keyword in keywords:
                    if keyword in page_text:
                        print(f"✅ Found keyword: {keyword}")
                        # Find surrounding context
                        lines = page_text.split('\n')
                        for i, line in enumerate(lines):
                            if keyword in line:
                                print(f"   Context: '{line.strip()}'")
                                break
                    else:
                        print(f"❌ Keyword not found: {keyword}")

            except Exception as e:
                print(f"❌ Error getting page text: {e}")

            input("Press Enter to close browser...")

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    debug_tabs()