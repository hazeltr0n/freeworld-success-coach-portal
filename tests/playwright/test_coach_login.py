#!/usr/bin/env python3
"""
Test coach login with correct credentials
"""
import time
import os
from playwright.sync_api import sync_playwright

def test_coach_login():
    # Get credentials from environment variables
    username = os.getenv("TEST_COACH_USERNAME", "test_coach")
    password = os.getenv("TEST_COACH_PASSWORD", "test_password")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=500)
        page = browser.new_page()

        print("🔍 Navigating to QA app...")
        page.goto("https://fwcareertest.streamlit.app")

        # Wait for iframe
        iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')
        iframe_locator.locator('div[data-testid="stApp"]').wait_for()
        print("✅ Found Streamlit app inside iframe")

        # Wait for login form
        iframe_locator.locator('input[placeholder="username"]').wait_for()
        print("✅ Found login form")

        # Enter credentials from environment
        print(f"🔑 Entering coach credentials: {username}")
        username_input = iframe_locator.locator('input[placeholder="username"]')
        username_input.fill(username)

        password_input = iframe_locator.locator('input[type="password"]')
        password_input.fill(password)

        # Click login
        print("🔑 Clicking Sign In...")
        iframe_locator.locator('button:has-text("Sign In")').click()

        # Wait for response
        time.sleep(3)

        # Check for login result
        try:
            # Look for error message
            error_element = iframe_locator.locator(':text("Invalid username or password")')
            if error_element.count() > 0:
                print("❌ Login failed: Invalid credentials")
                return False
            else:
                # Check for success indicators
                success_indicators = [
                    "Search Parameters",
                    "Memory Only",
                    "Indeed Fresh Only",
                    "Batch Search",
                    "Analytics Dashboard"
                ]

                found_indicators = []
                for indicator in success_indicators:
                    if iframe_locator.locator(f':text("{indicator}")').count() > 0:
                        found_indicators.append(indicator)

                if found_indicators:
                    print(f"✅ Login successful! Found: {', '.join(found_indicators)}")

                    # Now check for the batch scheduler issues
                    print("\n🔍 Checking Batch Search functionality...")

                    # Look for Batch Search tab/section
                    try:
                        batch_tab = iframe_locator.locator(':text("Batch Search")')
                        if batch_tab.count() > 0:
                            print("✅ Found Batch Search section")
                            batch_tab.click()
                            time.sleep(2)

                            # Check for classifier selection
                            classifier_indicators = [
                                "Job Type",
                                "CDL Traditional",
                                "Career Pathways",
                                "Classifier"
                            ]

                            found_classifier_options = []
                            for option in classifier_indicators:
                                if iframe_locator.locator(f':text("{option}")').count() > 0:
                                    found_classifier_options.append(option)

                            if found_classifier_options:
                                print(f"✅ Found classifier options: {', '.join(found_classifier_options)}")
                            else:
                                print("❌ Missing classifier selection options in batch scheduler")

                            # Look for save buttons
                            save_buttons = ["Save for later", "Save for Later", "Schedule"]
                            found_save_buttons = []
                            for button in save_buttons:
                                if iframe_locator.locator(f'button:has-text("{button}")').count() > 0:
                                    found_save_buttons.append(button)

                            if found_save_buttons:
                                print(f"✅ Found save buttons: {', '.join(found_save_buttons)}")
                            else:
                                print("❌ Missing save/schedule buttons")

                        else:
                            print("❌ Batch Search section not found")

                    except Exception as e:
                        print(f"💥 Error checking batch functionality: {e}")

                    return True
                else:
                    print("⚠️ Login succeeded but no expected main interface found")
                    return False

        except Exception as e:
            print(f"💥 Error checking login result: {e}")
            return False

        finally:
            browser.close()

if __name__ == "__main__":
    test_coach_login()