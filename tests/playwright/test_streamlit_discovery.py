"""
Streamlit-Specific Discovery Test - Find Streamlit widget selectors
"""

import pytest
import time
from playwright.sync_api import Page
from conftest import TEST_CONFIG, login_as_admin, navigate_to_tab


def test_discover_streamlit_widgets(page: Page):
    """Discover Streamlit widget selectors and data-testid attributes"""
    page.set_default_timeout(TEST_CONFIG["timeout"])

    # Login first
    login_as_admin(page)

    iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

    print("\n🔍 DISCOVERING STREAMLIT WIDGETS...")
    print("=" * 50)

    # Navigate to Job Search tab
    navigate_to_tab(page, "🔍 Job Search")
    time.sleep(3)

    # Look for Streamlit-specific attributes
    try:
        # Find elements with data-testid (Streamlit's preferred way)
        testid_elements = iframe_locator.locator('[data-testid]').all()
        print(f"Found {len(testid_elements)} elements with data-testid")

        testid_values = []
        for elem in testid_elements[:10]:  # First 10 only
            try:
                testid = elem.get_attribute('data-testid')
                if testid:
                    testid_values.append(testid)
            except:
                pass

        print(f"Data-testid values: {sorted(set(testid_values))}")

        # Look for Streamlit text_input widgets specifically
        print("\n🔍 SEARCHING FOR TEXT INPUT WIDGETS...")

        # Try different Streamlit text input selectors
        selectors_to_try = [
            '[data-testid="stTextInput"]',
            '[data-testid="textInput"]',
            '[data-baseweb="input"]',
            'div[data-testid*="text"] input',
            'input[type="text"][class*="st-"]'
        ]

        for selector in selectors_to_try:
            try:
                elements = iframe_locator.locator(selector).all()
                if elements:
                    print(f"✅ Found {len(elements)} elements for: {selector}")

                    # Try to interact with first element to understand it
                    first_elem = elements[0]
                    try:
                        value = first_elem.input_value()
                        print(f"   First element value: '{value}'")
                    except:
                        pass

            except Exception as e:
                print(f"❌ Selector failed: {selector} - {e}")

        # Look for labels near inputs to understand context
        print("\n🔍 SEARCHING FOR INPUT LABELS...")

        labels = iframe_locator.locator('label').all()
        print(f"Found {len(labels)} label elements")

        for i, label in enumerate(labels[:10]):  # First 10 labels
            try:
                text = label.text_content()
                if text and len(text) < 50:  # Reasonable length labels only
                    print(f"Label {i}: '{text}'")
            except:
                pass

        # Look for text that might indicate location/search inputs
        print("\n🔍 SEARCHING FOR LOCATION/SEARCH CONTEXT...")

        location_context = iframe_locator.locator('*:has-text("Location")').all()
        search_context = iframe_locator.locator('*:has-text("Search Terms")').all()

        print(f"Found {len(location_context)} elements containing 'Location'")
        print(f"Found {len(search_context)} elements containing 'Search Terms'")

        # Try to find inputs near these context elements
        if location_context:
            print("Trying to find input near Location context...")
            try:
                # Look for input elements near location text
                nearby_input = iframe_locator.locator('*:has-text("Location") + * input, *:has-text("Location") input, *:has-text("Location") >> .. >> input').first
                if nearby_input:
                    print("✅ Found input near Location context")
                    # Try to get its selector info
                    classes = nearby_input.get_attribute('class')
                    print(f"   Classes: {classes}")
            except Exception as e:
                print(f"❌ Failed to find input near Location: {e}")

        if search_context:
            print("Trying to find input near Search Terms context...")
            try:
                # Look for input elements near search terms text
                nearby_input = iframe_locator.locator('*:has-text("Search Terms") + * input, *:has-text("Search Terms") input, *:has-text("Search Terms") >> .. >> input').first
                if nearby_input:
                    print("✅ Found input near Search Terms context")
                    classes = nearby_input.get_attribute('class')
                    print(f"   Classes: {classes}")
            except Exception as e:
                print(f"❌ Failed to find input near Search Terms: {e}")

    except Exception as e:
        print(f"❌ Streamlit discovery failed: {e}")
        raise