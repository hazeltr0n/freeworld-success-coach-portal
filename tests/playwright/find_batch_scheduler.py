#!/usr/bin/env python3
"""
Find the batch scheduler functionality
"""
import time
from playwright.sync_api import sync_playwright

def find_batch_scheduler():
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

        # Look specifically for "Batches & Scheduling Access"
        print("\n🔍 Looking for 'Batches & Scheduling Access'...")
        batch_access_elements = iframe_locator.locator(':text("Batches & Scheduling Access")')

        if batch_access_elements.count() > 0:
            print(f"✅ Found {batch_access_elements.count()} 'Batches & Scheduling Access' elements")

            # Try to click on it
            try:
                print("🔄 Clicking on Batches & Scheduling Access...")
                batch_access_elements.first.click()
                time.sleep(3)

                # Now look for batch creation form
                print("\n🔍 Looking for batch creation form...")

                form_elements = [
                    "Location", "Search Terms", "Job Type", "Classifier",
                    "CDL Traditional", "Career Pathways", "Search Radius",
                    "Save for later", "Schedule", "Create"
                ]

                found_elements = {}
                for element in form_elements:
                    count = iframe_locator.locator(f':text("{element}")').count()
                    if count > 0:
                        found_elements[element] = count
                        print(f"   ✅ {element}: {count}")

                if not found_elements:
                    print("   ❌ No batch form elements found")

                    # Maybe it's in a different section - scroll and look again
                    print("\n🔄 Scrolling and looking again...")
                    page.mouse.wheel(0, 1000)  # Scroll down
                    time.sleep(2)

                    for element in form_elements:
                        count = iframe_locator.locator(f':text("{element}")').count()
                        if count > 0:
                            found_elements[element] = count
                            print(f"   ✅ (After scroll) {element}: {count}")

                # Specifically check for classifier dropdown
                if "Job Type" in found_elements:
                    print("\n🎯 Investigating Job Type classifier...")

                    # Look for selectbox near Job Type
                    job_type_element = iframe_locator.locator(':text("Job Type")').first

                    # Try to find selectbox
                    selectboxes = iframe_locator.locator('div[data-testid="selectbox"]')
                    if selectboxes.count() > 0:
                        print(f"   ✅ Found {selectboxes.count()} selectbox(es)")

                        # Click first selectbox
                        try:
                            selectboxes.first.click()
                            time.sleep(1)

                            classifier_options = ["CDL Traditional", "Career Pathways"]
                            found_options = []
                            for option in classifier_options:
                                if iframe_locator.locator(f':text("{option}")').count() > 0:
                                    found_options.append(option)

                            if found_options:
                                print(f"   ✅ Classifier options available: {', '.join(found_options)}")
                            else:
                                print("   ❌ ISSUE: No classifier options found in dropdown!")

                                # Get dropdown content for debugging
                                dropdown_content = selectboxes.first.text_content()
                                print(f"   📝 Dropdown content: '{dropdown_content}'")

                        except Exception as e:
                            print(f"   💥 Error clicking selectbox: {e}")
                    else:
                        print("   ❌ ISSUE: No selectbox found for Job Type!")

                # Check for Save for Later button functionality
                if "Save for later" in found_elements:
                    print("\n🔍 Investigating Save for Later button...")
                    save_button = iframe_locator.locator('button:has-text("Save for later")').first

                    # Don't actually click it, just check if it exists
                    print("   ✅ 'Save for later' button is present")
                    print("   ⚠️ Note: Button may run immediately instead of scheduling (reported issue)")

            except Exception as e:
                print(f"💥 Error clicking Batches & Scheduling Access: {e}")
        else:
            print("❌ 'Batches & Scheduling Access' not found")

            # Look for alternative batch-related elements
            print("\n🔍 Looking for alternative batch elements...")
            alt_batch_terms = [
                "Batch", "Schedule", "Queue", "Create Job", "New Search"
            ]

            for term in alt_batch_terms:
                count = iframe_locator.locator(f':text("{term}")').count()
                if count > 0:
                    print(f"   ✅ Alternative: {term}: {count}")

        browser.close()

if __name__ == "__main__":
    find_batch_scheduler()