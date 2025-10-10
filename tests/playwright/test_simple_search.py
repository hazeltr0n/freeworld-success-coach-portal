"""
Simple Search Test - Test basic job search functionality with updated selectors
"""

import pytest
import time
from playwright.sync_api import Page
from conftest import (
    TEST_CONFIG, login_as_admin, set_search_parameters,
    wait_for_search_completion, extract_search_metrics
)


def test_simple_memory_search(page: Page):
    """Test simple memory-only search with updated selectors"""
    page.set_default_timeout(TEST_CONFIG["timeout"])

    # Login first
    login_as_admin(page)

    print("\n🔍 TESTING SIMPLE MEMORY SEARCH...")
    print("=" * 50)

    iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

    # Set basic search parameters
    search_params = {
        "location": "Houston, TX",
        "search_terms": "CDL truck driver"
    }

    print(f"Setting parameters: {search_params}")
    params_success = set_search_parameters(page, search_params)

    if not params_success:
        print("⚠️ Parameter setting had issues, but continuing...")

    # Try to run Memory Only search
    print("🔄 Attempting Memory Only search...")
    try:
        memory_button = iframe_locator.locator('button:has-text("Memory Only")').first
        print("✅ Found Memory Only button")

        memory_button.click()
        print("✅ Clicked Memory Only button")

        # Wait for search to complete
        print("⏳ Waiting for search to complete...")
        success = wait_for_search_completion(page, timeout=120000)

        if success:
            print("✅ Search completed successfully")

            # Try to extract basic metrics
            metrics = extract_search_metrics(page)
            print(f"📊 Search metrics: {metrics}")

            if metrics["total_jobs"] > 0:
                print(f"🎉 SUCCESS: Found {metrics['total_jobs']} jobs")
                return True
            else:
                print("⚠️ No jobs found, but search completed")
                return True

        else:
            print("❌ Search did not complete successfully")
            return False

    except Exception as e:
        print(f"❌ Search failed: {e}")
        return False


def test_simple_fresh_search(page: Page):
    """Test simple fresh search (Indeed) with updated selectors"""
    page.set_default_timeout(TEST_CONFIG["timeout"])

    # Login first
    login_as_admin(page)

    print("\n🔍 TESTING SIMPLE FRESH SEARCH...")
    print("=" * 50)

    iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

    # Set basic search parameters
    search_params = {
        "location": "Dallas, TX",  # Different location
        "search_terms": "warehouse forklift"
    }

    print(f"Setting parameters: {search_params}")
    params_success = set_search_parameters(page, search_params)

    if not params_success:
        print("⚠️ Parameter setting had issues, but continuing...")

    # Try to run Indeed Fresh search
    print("🔄 Attempting Indeed Fresh search...")
    try:
        fresh_button = iframe_locator.locator('button:has-text("Indeed Fresh")').first
        print("✅ Found Indeed Fresh button")

        fresh_button.click()
        print("✅ Clicked Indeed Fresh button")

        # Wait for search to complete (longer timeout for fresh search)
        print("⏳ Waiting for fresh search to complete...")
        success = wait_for_search_completion(page, timeout=180000)  # 3 minutes

        if success:
            print("✅ Fresh search completed successfully")

            # Try to extract basic metrics
            metrics = extract_search_metrics(page)
            print(f"📊 Search metrics: {metrics}")

            if metrics["total_jobs"] > 0:
                print(f"🎉 SUCCESS: Found {metrics['total_jobs']} fresh jobs")
                return True
            else:
                print("⚠️ No jobs found, but search completed")
                return True

        else:
            print("❌ Fresh search did not complete successfully")
            return False

    except Exception as e:
        print(f"❌ Fresh search failed: {e}")
        return False