#!/usr/bin/env python3
"""
Standalone test script to verify DriverPulse authentication works in headless mode
Does NOT modify any existing code - just tests the flow
"""

import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from driver_pulse_2fa import GmailCodeExtractor
from driver_pulse_secrets import load_auth_data

def test_headless_auth():
    """Test authentication in headless mode using existing secrets"""

    print("=" * 60)
    print("Testing DriverPulse Authentication in HEADLESS Mode")
    print("=" * 60)

    # Load credentials from secrets
    print("\n📋 Loading credentials from secrets...")
    auth_data = load_auth_data()

    if not auth_data:
        print("❌ Could not load auth data from secrets")
        return False

    email = auth_data.get('email', 'freeworldplacement@gmail.com')
    first_name = auth_data.get('first_name', 'Claude')
    last_name = auth_data.get('last_name', 'Anthony')
    phone = auth_data.get('phone', '555-123-4567')

    print(f"   Email: {email}")
    print(f"   Name: {first_name} {last_name}")
    print(f"   Phone: {phone}")

    # Initialize Gmail 2FA
    print("\n📧 Setting up Gmail 2FA automation...")
    gmail_extractor = None
    if os.path.exists('gmail_credentials.json'):
        gmail_extractor = GmailCodeExtractor()
        if gmail_extractor.setup_gmail_api():
            print("   ✅ Gmail API ready - can extract 2FA codes automatically")
        else:
            print("   ❌ Gmail API failed - headless mode won't work")
            return False
    else:
        print("   ❌ gmail_credentials.json not found - headless mode won't work")
        return False

    # Start Playwright in HEADLESS mode
    print("\n🚀 Starting Playwright in HEADLESS mode...")
    print("   (No browser window should appear)")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # HEADLESS MODE
            slow_mo=100
        )
        page = browser.new_page()

        try:
            # Step 1: Navigate to Driver Pulse
            print("\n🌐 Loading Driver Pulse...")
            page.goto("https://pulse.tenstreet.com", wait_until="networkidle")
            time.sleep(3)

            # Step 2: Click Next button
            print("🔘 Clicking Next button...")
            page.click('div[onclick]:has-text("NEXT")')

            # Step 3: Wait for login form
            print("⏳ Waiting for login form...")
            page.wait_for_selector('#login_form', timeout=20000)
            print("   ✅ Login form found")

            # Step 4: Fill the form
            print("📝 Filling login form...")
            page.fill('#fname', first_name)
            page.fill('#lname', last_name)
            page.fill('#email', email)
            page.fill('#phone', phone)

            # Step 5: Submit the form
            print("📤 Submitting login form...")
            page.press('#phone', 'Enter')

            # Step 6: Handle 2FA
            print("⏳ Waiting for 2FA iframe...")
            time.sleep(5)

            try:
                page.wait_for_selector('#check_portal_auth_user_validation_frame', timeout=20000)
                print("   ✅ 2FA iframe found!")

                # Switch to iframe and click Email Me
                iframe = page.frame(name='check_portal_auth_user_validation_frame')
                if iframe:
                    print("🔗 Switched to 2FA iframe")
                    time.sleep(3)

                    # Click Email Me button
                    iframe.click('#email_button')
                    print("   ✅ Clicked 'Email Me' button")
                    print("⏳ Waiting 5 seconds for email to arrive...")
                    time.sleep(5)

                    # Extract 2FA code from Gmail
                    print("📧 Extracting 2FA code from Gmail...")
                    code = gmail_extractor.wait_for_2fa_code(timeout_seconds=120)

                    if code:
                        print(f"   ✅ 2FA code extracted: {code}")

                        # Enter code
                        iframe.fill('#email_check_button_input', str(code))
                        print("   ✅ Entered 2FA code")

                        # Submit code
                        iframe.click('#email_check_button')
                        print("   ✅ Submitted 2FA code")

                        # Wait for completion
                        time.sleep(10)
                    else:
                        print("   ❌ Could not extract 2FA code from Gmail")
                        browser.close()
                        return False

            except Exception as e:
                print(f"   ❌ 2FA step failed: {e}")
                browser.close()
                return False

            # Step 7: Final wait for login completion
            print("⏳ Waiting for final login completion...")
            time.sleep(5)

            # Step 8: Extract portal_user_id
            current_url = page.url
            print(f"📍 Current URL: {current_url}")

            portal_user_id = None
            if "portal_user_id=" in current_url:
                import re
                match = re.search(r'portal_user_id=(\d+)', current_url)
                if match:
                    portal_user_id = match.group(1)
                    print(f"   ✅ Extracted portal_user_id: {portal_user_id}")

            # Try localStorage if not in URL
            if not portal_user_id:
                try:
                    portal_user_id = page.evaluate("localStorage.getItem('portal_user_id')")
                    if portal_user_id:
                        print(f"   ✅ Found portal_user_id in localStorage: {portal_user_id}")
                except:
                    pass

            # Step 9: Save authentication
            print("💾 Saving authentication...")
            auth_state = page.context.storage_state()

            # Convert Playwright cookies to our format
            cookies_data = []
            for cookie in auth_state['cookies']:
                cookies_data.append({
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'domain': cookie['domain'],
                    'path': cookie.get('path', '/'),
                    'secure': cookie.get('secure', False),
                    'httpOnly': cookie.get('httpOnly', False)
                })

            # Save authentication file
            auth_file_data = {
                'cookies': cookies_data,
                'created_at': datetime.now().isoformat(),
                'portal_user_id': portal_user_id,
                'auth_method': 'headless_playwright_with_gmail_2fa'
            }

            with open('auth_headless_test.json', 'w') as f:
                json.dump(auth_file_data, f, indent=2)

            print(f"   ✅ Auth saved to auth_headless_test.json")
            print(f"   User ID: {portal_user_id}")
            print(f"   Cookies: {len(cookies_data)}")

            browser.close()

            print("\n" + "=" * 60)
            print("✅ SUCCESS! Headless authentication worked!")
            print("=" * 60)
            return True

        except Exception as e:
            print(f"\n❌ ERROR during headless authentication:")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()
            browser.close()
            return False

if __name__ == "__main__":
    import sys
    success = test_headless_auth()
    sys.exit(0 if success else 1)
