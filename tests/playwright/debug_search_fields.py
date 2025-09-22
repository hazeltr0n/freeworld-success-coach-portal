#!/usr/bin/env python3
"""
Debug script to find actual search field names and selectors
"""
import os
from playwright.sync_api import sync_playwright

def debug_search_fields():
    # Set credentials
    os.environ["TEST_ADMIN_USERNAME"] = "james.hazelton"
    os.environ["TEST_ADMIN_PASSWORD"] = "Tbonbass1!"

    from conftest import login_as_admin

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=500)
        page = browser.new_page()

        try:
            # Login as admin
            login_as_admin(page)

            # Get iframe
            iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

            print("\n🔍 Searching for input fields...")

            # Try to find all input fields
            input_selectors = [
                'input[data-testid="textInput"]',
                'input[type="text"]',
                'input',
                'textarea'
            ]

            for selector in input_selectors:
                try:
                    elements = iframe_locator.locator(selector)
                    count = elements.count()
                    print(f"\n✅ Found {count} elements with selector: {selector}")

                    for i in range(min(count, 5)):  # Show first 5
                        try:
                            element = elements.nth(i)
                            placeholder = element.get_attribute("placeholder")
                            label = element.get_attribute("aria-label")
                            value = element.get_attribute("value")
                            print(f"   Input {i+1}:")
                            print(f"     Placeholder: '{placeholder}'")
                            print(f"     Aria-label: '{label}'")
                            print(f"     Value: '{value}'")
                        except Exception as e:
                            print(f"     Error getting attributes: {e}")
                except Exception as e:
                    print(f"❌ Selector failed: {selector} - {e}")

            # Look for specific text content around inputs
            print("\n📝 Looking for text content around search interface...")
            try:
                page_text = iframe_locator.locator('body').text_content()

                search_keywords = ["Market", "Location", "Search", "Keywords", "Terms", "Job", "Type", "Classifier"]
                for keyword in search_keywords:
                    if keyword in page_text:
                        print(f"✅ Found keyword: {keyword}")
                        # Find surrounding context
                        lines = page_text.split('\n')
                        for i, line in enumerate(lines):
                            if keyword in line:
                                print(f"   Context: '{line.strip()}'")
                                # Show next few lines for context
                                for j in range(1, 3):
                                    if i + j < len(lines):
                                        next_line = lines[i + j].strip()
                                        if next_line:
                                            print(f"   Next: '{next_line}'")
                                break
                    else:
                        print(f"❌ Keyword not found: {keyword}")

            except Exception as e:
                print(f"❌ Error getting page text: {e}")

            # Look for buttons
            print("\n🔘 Searching for buttons...")
            button_selectors = [
                'button',
                '[role="button"]',
                'div[data-testid="stButton"]'
            ]

            for selector in button_selectors:
                try:
                    elements = iframe_locator.locator(selector)
                    count = elements.count()
                    if count > 0:
                        print(f"\n✅ Found {count} buttons with selector: {selector}")
                        for i in range(min(count, 10)):  # Show first 10
                            try:
                                text = elements.nth(i).text_content()
                                if text and text.strip():
                                    print(f"   Button {i+1}: '{text.strip()}'")
                            except:
                                pass
                except Exception as e:
                    print(f"❌ Button selector failed: {selector} - {e}")

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    debug_search_fields()