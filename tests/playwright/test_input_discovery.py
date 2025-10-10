"""
Input Field Discovery Test - Find exact selectors for form inputs
"""

import pytest
import time
from playwright.sync_api import Page
from conftest import TEST_CONFIG, login_as_admin, navigate_to_tab


def test_discover_job_search_inputs(page: Page):
    """Discover exact input field selectors in Job Search tab"""
    page.set_default_timeout(TEST_CONFIG["timeout"])

    # Login first
    login_as_admin(page)

    iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

    print("\n🔍 DISCOVERING JOB SEARCH INPUT FIELDS...")
    print("=" * 50)

    # Navigate to Job Search tab
    nav_success = navigate_to_tab(page, "🔍 Job Search")
    print(f"Navigation result: {nav_success}")

    time.sleep(3)  # Let page load

    # Get all input elements and their attributes
    try:
        inputs = iframe_locator.locator('input').all()
        print(f"Found {len(inputs)} total input elements")

        for i, input_elem in enumerate(inputs):
            try:
                input_type = input_elem.get_attribute('type') or 'text'
                placeholder = input_elem.get_attribute('placeholder') or 'None'
                name = input_elem.get_attribute('name') or 'None'
                id_attr = input_elem.get_attribute('id') or 'None'
                class_attr = input_elem.get_attribute('class') or 'None'

                print(f"Input {i}:")
                print(f"  Type: {input_type}")
                print(f"  Placeholder: {placeholder}")
                print(f"  Name: {name}")
                print(f"  ID: {id_attr}")
                print(f"  Class: {class_attr}")
                print()

            except Exception as e:
                print(f"Error reading input {i}: {e}")

        # Look specifically for text areas too
        textareas = iframe_locator.locator('textarea').all()
        print(f"Found {len(textareas)} textarea elements")

        for i, textarea in enumerate(textareas):
            try:
                placeholder = textarea.get_attribute('placeholder') or 'None'
                name = textarea.get_attribute('name') or 'None'

                print(f"Textarea {i}:")
                print(f"  Placeholder: {placeholder}")
                print(f"  Name: {name}")
                print()

            except Exception as e:
                print(f"Error reading textarea {i}: {e}")

        # Look for specific search-related elements
        print("🔍 SEARCHING FOR SEARCH PARAMETERS SECTION...")

        # Try to find the search parameters area
        search_sections = iframe_locator.locator('*:has-text("Search Parameters")').all()
        print(f"Found {len(search_sections)} 'Search Parameters' sections")

        # Look for selectbox elements (Streamlit uses select elements)
        selects = iframe_locator.locator('select').all()
        print(f"Found {len(selects)} select elements")

        for i, select in enumerate(selects):
            try:
                name = select.get_attribute('name') or 'None'
                print(f"Select {i}: name={name}")

                # Get options
                options = select.locator('option').all()
                print(f"  Has {len(options)} options")

            except Exception as e:
                print(f"Error reading select {i}: {e}")

    except Exception as e:
        print(f"❌ Input discovery failed: {e}")
        raise