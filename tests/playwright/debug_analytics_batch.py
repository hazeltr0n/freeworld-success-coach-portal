#!/usr/bin/env python3
"""
Investigate batch scheduler functionality in Analytics tab
"""
import time
from playwright.sync_api import sync_playwright

def debug_analytics_batch():
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
        time.sleep(3)
        print("✅ Logged in successfully")

        # Click on Analytics tab
        print("\n🔍 Clicking on Analytics tab...")
        analytics_tab = iframe_locator.locator(':text("Analytics")')
        if analytics_tab.count() > 0:
            analytics_tab.first.click()
            time.sleep(2)
            print("✅ Clicked Analytics tab")

            # Look for batch-related content
            print("\n🔍 Looking for batch scheduler elements...")

            # Check for different tab names within Analytics
            analytics_subtabs = [
                "Batch Search", "Scheduled Search", "Create Batch",
                "New Batch", "Schedule", "Queue", "Batch Jobs"
            ]

            found_subtabs = []
            for subtab in analytics_subtabs:
                if iframe_locator.locator(f':text("{subtab}")').count() > 0:
                    found_subtabs.append(subtab)
                    print(f"   ✅ Found subtab: {subtab}")

            if not found_subtabs:
                print("   ❌ No obvious batch subtabs found")

            # Look for Create/New buttons in Analytics
            create_buttons = [
                "Create", "New", "Add", "Schedule", "➕", "+"
            ]

            print("\n🔍 Looking for create/schedule buttons in Analytics:")
            for button_text in create_buttons:
                try:
                    buttons = iframe_locator.locator(f'button:has-text("{button_text}")')
                    count = buttons.count()
                    if count > 0:
                        print(f"   🔘 Button containing '{button_text}': {count} found")
                        for i in range(min(count, 3)):
                            try:
                                full_text = buttons.nth(i).text_content()
                                print(f"      [{i}] '{full_text}'")

                                # Try clicking this button to see what happens
                                if "batch" in full_text.lower() or "create" in full_text.lower() or "schedule" in full_text.lower():
                                    print(f"      → Clicking '{full_text}'...")
                                    buttons.nth(i).click()
                                    time.sleep(2)

                                    # Check what appears after clicking
                                    batch_form_indicators = [
                                        "Location", "Search Terms", "Classifier",
                                        "Job Type", "CDL Traditional", "Career Pathways",
                                        "Save for later", "Schedule", "Create Job"
                                    ]

                                    found_form_elements = []
                                    for indicator in batch_form_indicators:
                                        if iframe_locator.locator(f':text("{indicator}")').count() > 0:
                                            found_form_elements.append(indicator)

                                    if found_form_elements:
                                        print(f"         ✅ After clicking, found form elements: {', '.join(found_form_elements)}")

                                        # Specifically check for classifier selection
                                        classifier_elements = iframe_locator.locator(':text("Job Type")')
                                        if classifier_elements.count() > 0:
                                            print("         🎯 Found 'Job Type' - checking for classifier dropdown...")

                                            # Look for selectbox or dropdown near Job Type
                                            selectboxes = iframe_locator.locator('div[data-testid="selectbox"]')
                                            if selectboxes.count() > 0:
                                                print(f"         ✅ Found {selectboxes.count()} selectbox(es)")

                                                # Click on first selectbox to see options
                                                try:
                                                    selectboxes.first.click()
                                                    time.sleep(1)

                                                    # Check for classifier options
                                                    if iframe_locator.locator(':text("CDL Traditional")').count() > 0:
                                                        print("         ✅ Found 'CDL Traditional' option")
                                                    if iframe_locator.locator(':text("Career Pathways")').count() > 0:
                                                        print("         ✅ Found 'Career Pathways' option")

                                                    if (iframe_locator.locator(':text("CDL Traditional")').count() == 0 and
                                                        iframe_locator.locator(':text("Career Pathways")').count() == 0):
                                                        print("         ❌ Classifier options missing!")

                                                except Exception as e:
                                                    print(f"         💥 Error clicking selectbox: {e}")
                                            else:
                                                print("         ❌ No selectbox found near Job Type")

                                        # Check for Save for Later button
                                        save_buttons = iframe_locator.locator('button:has-text("Save for later")')
                                        if save_buttons.count() > 0:
                                            print("         ✅ Found 'Save for later' button")
                                        else:
                                            save_alt_buttons = iframe_locator.locator('button:has-text("Save for Later")')
                                            if save_alt_buttons.count() > 0:
                                                print("         ✅ Found 'Save for Later' button")
                                            else:
                                                print("         ❌ 'Save for later' button not found")

                                    else:
                                        print(f"         ❌ No batch form elements found after clicking")

                                    break  # Only click the first relevant button

                            except Exception as e:
                                print(f"      💥 Error with button {i}: {e}")
                except Exception as e:
                    print(f"   💥 Error looking for button '{button_text}': {e}")

        else:
            print("❌ Analytics tab not found")

        browser.close()

if __name__ == "__main__":
    debug_analytics_batch()