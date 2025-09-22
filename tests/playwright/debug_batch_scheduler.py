#!/usr/bin/env python3
"""
Debug where the batch scheduler is located in the QA app
"""
import time
from playwright.sync_api import sync_playwright

def debug_batch_scheduler():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=500)
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
        time.sleep(3)
        print("✅ Logged in successfully")

        # Save post-login content
        iframe = page.locator('iframe[title="streamlitApp"]').element_handle()
        iframe_page = iframe.content_frame()
        content = iframe_page.content()

        with open("debug_logged_in_content.html", "w") as f:
            f.write(content)
        print("💾 Logged-in content saved")

        # Look for all possible navigation elements
        print("\n🔍 Looking for navigation elements:")

        nav_terms = [
            "Batch", "Schedule", "Later", "Queue", "Jobs",
            "Agent Management", "Analytics", "Dashboard",
            "Tab", "Menu", "Navigation"
        ]

        found_nav = {}
        for term in nav_terms:
            try:
                elements = iframe_locator.locator(f':text("{term}")')
                count = elements.count()
                if count > 0:
                    found_nav[term] = count
                    print(f"   ✅ {term}: {count} occurrences")

                    # Get some context around these elements
                    for i in range(min(count, 2)):
                        try:
                            text_content = elements.nth(i).text_content()
                            print(f"      [{i}] '{text_content[:50]}...'")
                        except:
                            pass
            except:
                pass

        # Look for buttons that might lead to scheduling
        print("\n🔍 Looking for buttons:")
        button_texts = [
            "Create", "New", "Add", "Schedule", "Batch",
            "Save", "Later", "Queue"
        ]

        for button_text in button_texts:
            try:
                buttons = iframe_locator.locator(f'button:has-text("{button_text}")')
                count = buttons.count()
                if count > 0:
                    print(f"   🔘 Button '{button_text}': {count} found")
                    for i in range(min(count, 2)):
                        try:
                            full_text = buttons.nth(i).text_content()
                            print(f"      [{i}] '{full_text}'")
                        except:
                            pass
            except:
                pass

        # Look for tabs or sections
        print("\n🔍 Looking for tabs/sections:")

        # Try clicking on different areas to see if tabs exist
        possible_tabs = [
            "Agent Management",
            "Analytics Dashboard",
            "Analytics",
            "Dashboard",
            "Settings",
            "Tools",
            "Admin"
        ]

        for tab_name in possible_tabs:
            try:
                tab_element = iframe_locator.locator(f':text("{tab_name}")')
                if tab_element.count() > 0:
                    print(f"   📁 Found potential tab: {tab_name}")

                    # Try clicking on it
                    try:
                        tab_element.first.click()
                        time.sleep(1)

                        # Check if batch-related content appears
                        batch_indicators = ["Schedule", "Batch", "Create", "Queue"]
                        found_after_click = []
                        for indicator in batch_indicators:
                            if iframe_locator.locator(f':text("{indicator}")').count() > 0:
                                found_after_click.append(indicator)

                        if found_after_click:
                            print(f"      ✅ After clicking {tab_name}, found: {', '.join(found_after_click)}")
                        else:
                            print(f"      ❌ No batch content found in {tab_name}")

                    except Exception as e:
                        print(f"      💥 Error clicking {tab_name}: {e}")
            except:
                pass

        browser.close()

if __name__ == "__main__":
    debug_batch_scheduler()