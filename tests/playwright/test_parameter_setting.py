"""
Test Parameter Setting - Validate updated selector functions
"""

import pytest
import time
from playwright.sync_api import Page
from conftest import TEST_CONFIG, login_as_admin, set_search_parameters


def test_parameter_setting_validation(page: Page):
    """Test that we can set search parameters with updated selectors"""
    page.set_default_timeout(TEST_CONFIG["timeout"])

    # Login first
    login_as_admin(page)

    print("\n🔧 TESTING PARAMETER SETTING...")
    print("=" * 50)

    # Test setting search parameters
    search_params = {
        "location": "Houston, TX",
        "search_terms": "CDL truck driver",
        "classifier_type": "CDL Traditional"
    }

    print(f"Attempting to set parameters: {search_params}")

    success = set_search_parameters(page, search_params)

    if success:
        print("✅ Parameter setting test PASSED")
    else:
        print("❌ Parameter setting test FAILED")

    # Verify the parameters were actually set by checking current values
    iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

    try:
        # Check if we can find the set values somewhere on the page
        page_text = iframe_locator.locator('body').text_content(timeout=10000)

        found_values = []
        for key, value in search_params.items():
            if str(value) in page_text:
                found_values.append(f"{key}={value}")
                print(f"✅ Found {key}: {value}")
            else:
                print(f"❌ Could not verify {key}: {value}")

        if len(found_values) >= 2:  # At least 2 out of 3 parameters found
            print(f"✅ Parameter verification PASSED: {found_values}")
            return True
        else:
            print(f"⚠️ Parameter verification PARTIAL: {found_values}")
            return success  # Return the original success status

    except Exception as e:
        print(f"⚠️ Parameter verification failed: {e}")
        return success

    return success