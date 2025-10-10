"""
UI Discovery Test - Check current UI state and selectors
This test helps us understand what's changed in the UI
"""

import pytest
import time
from playwright.sync_api import Page
from conftest import TEST_CONFIG, login_as_admin


def test_discover_current_ui(page: Page):
    """Discover current UI state and available elements"""
    page.set_default_timeout(TEST_CONFIG["timeout"])

    # Login first
    login_as_admin(page)

    iframe_locator = page.frame_locator('iframe[title="streamlitApp"]')

    print("\n🔍 DISCOVERING CURRENT UI STATE...")
    print("=" * 50)

    # Get all text content to understand current page structure
    try:
        page_text = iframe_locator.locator('body').text_content(timeout=10000)
        print(f"📄 Page contains {len(page_text)} characters of text")

        # Look for key indicators
        key_phrases = [
            "Search Parameters", "Memory Only", "Indeed Fresh",
            "Location", "Search Terms", "Analytics", "Admin Panel",
            "Job Search", "Free Agents", "Coach Analytics"
        ]

        found_phrases = []
        for phrase in key_phrases:
            if phrase in page_text:
                found_phrases.append(phrase)

        print(f"✅ Found key phrases: {found_phrases}")

        # Try to find input elements
        print("\n🔍 SEARCHING FOR INPUT ELEMENTS...")

        # Location input variations
        location_selectors = [
            "input[placeholder*='location']",
            "input[placeholder*='Location']",
            "input[placeholder*='city']",
            "input[placeholder*='City']",
            "input[type='text']"
        ]

        for selector in location_selectors:
            try:
                elements = iframe_locator.locator(selector).all()
                if elements:
                    print(f"✅ Found {len(elements)} elements for: {selector}")
                    # Get placeholder text for the first few
                    for i, elem in enumerate(elements[:3]):
                        try:
                            placeholder = elem.get_attribute('placeholder')
                            print(f"   Element {i}: placeholder='{placeholder}'")
                        except:
                            pass
            except Exception as e:
                print(f"❌ No elements for: {selector}")

        # Search for buttons
        print("\n🔍 SEARCHING FOR BUTTONS...")
        button_texts = ["Memory Only", "Indeed Fresh", "Google Jobs", "Search", "Run"]

        for button_text in button_texts:
            try:
                buttons = iframe_locator.locator(f'button:has-text("{button_text}")').all()
                if buttons:
                    print(f"✅ Found {len(buttons)} buttons with text: '{button_text}'")
            except:
                print(f"❌ No buttons found with text: '{button_text}'")

        # Look for navigation tabs
        print("\n🔍 SEARCHING FOR NAVIGATION...")
        nav_texts = ["🔍 Job Search", "👥 Free Agents", "📊 Coach Analytics", "⚙️ Admin Panel"]

        for nav_text in nav_texts:
            try:
                nav_elements = iframe_locator.locator(f'*:has-text("{nav_text}")').all()
                if nav_elements:
                    print(f"✅ Found {len(nav_elements)} nav elements: '{nav_text}'")
            except:
                print(f"❌ No nav elements found: '{nav_text}'")

        print("\n✅ UI DISCOVERY COMPLETE")

    except Exception as e:
        print(f"❌ UI Discovery failed: {e}")
        raise