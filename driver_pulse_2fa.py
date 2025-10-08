#!/usr/bin/env python3
"""
Driver Pulse 2FA Automation using Gmail API

This module provides automated 2FA code extraction from Gmail
for seamless Driver Pulse authentication renewal.
"""

import os
import re
import time
import json
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

# Gmail API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

# Playwright for browser automation
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GmailCodeExtractor:
    """Extracts 2FA codes from Gmail using Gmail API"""

    # Gmail API scopes
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

    def __init__(self,
                 credentials_file: str = "gmail_credentials.json",
                 token_file: str = "gmail_token.json"):
        """
        Initialize Gmail code extractor.

        Args:
            credentials_file: Path to Gmail API credentials JSON
            token_file: Path to store Gmail API token
        """
        if not GMAIL_AVAILABLE:
            raise ImportError("Gmail API libraries not installed. Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None

    def setup_gmail_api(self) -> bool:
        """
        Set up Gmail API authentication.
        Uses GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET from Streamlit secrets,
        or falls back to local credentials file.

        Returns:
            bool: True if setup successful
        """
        try:
            creds = None

            # Try to load existing token from file
            if os.path.exists(self.token_file):
                logger.info(f"📂 Loading existing token from {self.token_file}")
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)

            # Check if token is valid and not expired
            if creds and creds.valid and not creds.expired:
                # Token is good to go - build service and return immediately
                self.service = build('gmail', 'v1', credentials=creds)
                logger.info("✅ Gmail API setup successful (existing valid token)")
                return True

            # Check if token needs refresh
            if creds:
                should_refresh = False
                if not creds.valid:
                    should_refresh = True
                    logger.info("🔄 Token invalid, needs refresh")
                elif creds.expired:
                    should_refresh = True
                    logger.info("🔄 Token expired, needs refresh")

                if should_refresh and creds.refresh_token:
                    logger.info("🔄 Refreshing access token using refresh_token...")
                    try:
                        creds.refresh(Request())
                        logger.info("✅ Token refreshed successfully")

                        # Try to save refreshed token (will fail in GitHub Actions, but that's OK)
                        try:
                            with open(self.token_file, 'w') as token:
                                token.write(creds.to_json())
                            logger.info(f"💾 Refreshed token saved to {self.token_file}")
                        except Exception as save_error:
                            logger.warning(f"⚠️ Could not save refreshed token (expected in GitHub Actions): {save_error}")

                        # Token is now valid - build service and return
                        self.service = build('gmail', 'v1', credentials=creds)
                        logger.info("✅ Gmail API setup successful (after token refresh)")
                        return True

                    except Exception as refresh_error:
                        logger.error(f"❌ Token refresh failed: {refresh_error}")
                        creds = None  # Need to re-authenticate
                elif should_refresh and not creds.refresh_token:
                    logger.warning("⚠️ Token invalid but no refresh token available")
                    creds = None

            # If no valid credentials, need to authenticate
            if not creds or not creds.valid:
                logger.info("🔐 No valid credentials, starting authentication flow...")

                # Try Streamlit secrets for client credentials
                client_config = None
                try:
                    import streamlit as st
                    if hasattr(st, 'secrets') and 'GMAIL_CLIENT_ID' in st.secrets and 'GMAIL_CLIENT_SECRET' in st.secrets:
                        logger.info("🔑 Using Gmail credentials from Streamlit secrets")
                        client_config = {
                            "installed": {
                                "client_id": st.secrets['GMAIL_CLIENT_ID'],
                                "client_secret": st.secrets['GMAIL_CLIENT_SECRET'],
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                                "redirect_uris": ["http://localhost"]
                            }
                        }
                except Exception as e:
                    logger.info(f"ℹ️ Streamlit secrets not available: {e}")

                # Run OAuth flow
                if client_config:
                    flow = InstalledAppFlow.from_client_config(client_config, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                elif os.path.exists(self.credentials_file):
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    logger.error("❌ No credentials available (neither secrets nor credentials file)")
                    return False

                # Save new token
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
                logger.info(f"💾 New token saved to {self.token_file}")

            # Build service
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("✅ Gmail API setup successful")
            return True

        except Exception as e:
            logger.error(f"❌ Gmail API setup failed: {str(e)}")
            return False

    def search_2fa_emails(self,
                         sender_filter: str = "noreply@tenstreet.com",
                         subject_filter: str = "Authorization Code",
                         max_age_minutes: int = 10) -> List[Dict]:
        """
        Search for recent 2FA emails.

        Args:
            sender_filter: Email sender to filter by
            subject_filter: Subject keyword to filter by
            max_age_minutes: Maximum age of emails to consider

        Returns:
            List[Dict]: List of matching email messages
        """
        if not self.service:
            if not self.setup_gmail_api():
                return []

        try:
            # Build search query
            since_date = datetime.now() - timedelta(minutes=max_age_minutes)
            date_str = since_date.strftime('%Y/%m/%d')

            query_parts = [
                f"from:{sender_filter}",
                f"subject:{subject_filter}",
                f"after:{date_str}",
                "is:unread"  # Only unread emails
            ]
            query = " ".join(query_parts)

            logger.info(f"🔍 Searching Gmail: {query}")

            # Search emails
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=10).execute()

            messages = results.get('messages', [])
            logger.info(f"📧 Found {len(messages)} matching emails")

            return messages

        except Exception as e:
            logger.error(f"❌ Gmail search failed: {str(e)}")
            return []

    def extract_code_from_email(self, message_id: str) -> Optional[str]:
        """
        Extract 2FA code from a specific email.

        Args:
            message_id: Gmail message ID

        Returns:
            str: Extracted 2FA code or None
        """
        try:
            # Get email content
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full').execute()

            # First try to extract from subject line (Tenstreet puts code there)
            headers = message['payload'].get('headers', [])
            subject = None
            for header in headers:
                if header['name'].lower() == 'subject':
                    subject = header['value']
                    break

            if subject:
                logger.info(f"📧 Email subject: {subject}")
                # Look for "Tenstreet Authorization Code - 136323" pattern
                tenstreet_match = re.search(r'Tenstreet Authorization Code\s*-\s*(\d+)', subject, re.IGNORECASE)
                if tenstreet_match:
                    code = tenstreet_match.group(1)
                    logger.info(f"✅ Found Tenstreet code in subject: {code}")

                    # Try to mark email as read (skip if insufficient permissions)
                    try:
                        self.service.users().messages().modify(
                            userId='me', id=message_id,
                            body={'removeLabelIds': ['UNREAD']}).execute()
                        logger.info("📧 Email marked as read")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not mark email as read (readonly scope): {e}")

                    return code

            # Fallback: Extract from email body
            body = self._extract_email_body(message)
            if not body:
                logger.warning(f"Could not extract body from email {message_id}")
                return None

            # Extract code using regex patterns
            code = self._extract_code_from_text(body)

            if code:
                logger.info(f"✅ Extracted 2FA code: {code}")

                # Mark email as read
                self.service.users().messages().modify(
                    userId='me', id=message_id,
                    body={'removeLabelIds': ['UNREAD']}).execute()

                return code
            else:
                logger.warning(f"No 2FA code found in email {message_id}")
                return None

        except Exception as e:
            logger.error(f"❌ Code extraction failed: {str(e)}")
            return None

    def _extract_email_body(self, message: Dict) -> Optional[str]:
        """Extract text body from Gmail message"""
        try:
            payload = message['payload']

            # Handle different message structures
            if 'parts' in payload:
                # Multipart message
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body']['data']
                        return base64.urlsafe_b64decode(data).decode('utf-8')
            else:
                # Simple message
                if payload['mimeType'] == 'text/plain':
                    data = payload['body']['data']
                    return base64.urlsafe_b64decode(data).decode('utf-8')

            # Try HTML if plain text not found
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/html':
                        data = part['body']['data']
                        html_content = base64.urlsafe_b64decode(data).decode('utf-8')
                        # Strip HTML tags (basic)
                        import re
                        text_content = re.sub(r'<[^>]+>', '', html_content)
                        return text_content

            return None

        except Exception as e:
            logger.error(f"Error extracting email body: {str(e)}")
            return None

    def _extract_code_from_text(self, text: str) -> Optional[str]:
        """Extract 2FA code from email text using regex patterns"""

        # Common 2FA code patterns
        patterns = [
            r'\b(\d{6})\b',           # 6-digit code
            r'\b(\d{4})\b',           # 4-digit code
            r'\b(\d{8})\b',           # 8-digit code
            r'code[:\s]+(\d+)',       # "code: 123456"
            r'verification[:\s]+(\d+)', # "verification: 123456"
            r'(\d+)\s*is\s+your',     # "123456 is your code"
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return first match that looks like a reasonable 2FA code
                for match in matches:
                    if 4 <= len(match) <= 8:
                        return match

        return None

    def wait_for_2fa_code(self,
                         timeout_seconds: int = 300,
                         check_interval: int = 10) -> Optional[str]:
        """
        Wait for a 2FA code to arrive via email.

        Args:
            timeout_seconds: Maximum time to wait
            check_interval: How often to check for emails

        Returns:
            str: 2FA code or None if timeout
        """
        logger.info(f"⏳ Waiting for 2FA code (timeout: {timeout_seconds}s)")

        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            # Search for new emails
            emails = self.search_2fa_emails(max_age_minutes=15)

            for email in emails:
                code = self.extract_code_from_email(email['id'])
                if code:
                    return code

            # Wait before checking again
            logger.info(f"🔄 No 2FA code yet, checking again in {check_interval}s...")
            time.sleep(check_interval)

        logger.error(f"❌ Timeout waiting for 2FA code")
        return None

class DriverPulse2FAHandler:
    """Complete 2FA handler for Driver Pulse authentication"""

    def __init__(self,
                 gmail_credentials: str = "gmail_credentials.json",
                 auth_file: str = "auth.json"):
        """
        Initialize 2FA handler.

        Args:
            gmail_credentials: Path to Gmail API credentials
            auth_file: Path to Driver Pulse auth file
        """
        self.auth_file = auth_file
        self.gmail_extractor = GmailCodeExtractor(gmail_credentials)

    def is_session_expired(self) -> bool:
        """
        Check if current Driver Pulse session is expired.

        Returns:
            bool: True if session needs renewal
        """
        if not os.path.exists(self.auth_file):
            return True

        # Try a simple API call to test session
        try:
            from driver_pulse_source import DriverPulseSource
            source = DriverPulseSource()
            source.load_authentication()

            # Test with a lightweight API call
            result = source.get_company_details("917")  # Known test company
            return result is None

        except Exception:
            return True

    def perform_2fa_login(self,
                         email: str,
                         first_name: str,
                         last_name: str,
                         phone: str) -> bool:
        """
        Perform complete 2FA login process.

        Args:
            email: Login email
            first_name: First name
            last_name: Last name
            phone: Phone number

        Returns:
            bool: True if login successful
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not installed. Run: pip install playwright")

        logger.info("🚀 Starting automated 2FA login...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=1000)
            context = browser.new_context(viewport=None)
            page = context.new_page()

            try:
                # Step 1: Navigate to Driver Pulse
                logger.info("🌐 Opening Driver Pulse...")
                page.goto("https://pulse.tenstreet.com", wait_until="networkidle")
                time.sleep(3)

                # Step 2: Click Next button
                logger.info("🔘 Clicking Next button...")

                # Try multiple Next button selectors in order of specificity
                next_clicked = False
                next_selectors = [
                    # Most specific - target the blue button by position and style
                    'div[style*="cursor"]:has-text("NEXT")',
                    'div[onclick]:has-text("NEXT")',
                    '*[role="button"]:has-text("NEXT")',

                    # Target by visual characteristics
                    'div[style*="background"]:has-text("NEXT")',
                    'div[style*="blue"]:has-text("NEXT")',

                    # Target by position (blue button should be lower on page)
                    'button:has-text("NEXT")',
                    'a:has-text("NEXT")',

                    # Generic fallback
                    'div:has-text("NEXT")',
                    'text=NEXT'
                ]

                for i, selector in enumerate(next_selectors):
                    try:
                        logger.info(f"🔍 Trying Next selector {i+1}: {selector}")

                        # Find all matching elements
                        elements = page.query_selector_all(selector)
                        logger.info(f"   Found {len(elements)} elements")

                        for j, element in enumerate(elements):
                            if element.is_visible():
                                # Check if this looks like the blue button by position
                                try:
                                    box = element.bounding_box()
                                    if box and box['y'] > 400:  # Blue button is lower on page
                                        logger.info(f"   Clicking element {j+1} at position y={box['y']}")
                                        element.click()
                                        time.sleep(5)  # Wait longer for page transition

                                        # Check if we moved past welcome screen
                                        welcome_still_visible = page.query_selector('text=Welcome to')
                                        if not welcome_still_visible or not welcome_still_visible.is_visible():
                                            logger.info("✅ Next button clicked successfully - welcome screen disappeared")
                                            next_clicked = True
                                            break
                                        else:
                                            logger.warning(f"   Still on welcome screen after click")

                                except Exception as pos_e:
                                    logger.warning(f"   Position check failed: {pos_e}")

                        if next_clicked:
                            break

                    except Exception as e:
                        logger.warning(f"   Selector {selector} failed: {e}")

                if not next_clicked:
                    logger.error("❌ All Next button selectors failed")
                    page.screenshot(path="next_button_failed.png")
                    raise Exception("Could not click Next button")

                # Step 3: Fill login form
                logger.info("📝 Filling login form...")

                # Wait for login form to be visible - look for "Driver Pulse" header first
                try:
                    logger.info("🔍 Looking for Driver Pulse form header...")
                    page.wait_for_selector('text=Driver Pulse', timeout=15000)
                    logger.info("✅ Driver Pulse header found")
                except:
                    logger.warning("⚠️ Driver Pulse header not found, proceeding anyway")

                # Wait for form and fill it - SIMPLE approach that was working
                logger.info("📝 Waiting for form and filling fields...")

                # Wait longer for JavaScript to set placeholders
                logger.info("⏳ Waiting for form JavaScript to load placeholders...")
                time.sleep(5)

                # Wait for form to appear with placeholders set by JavaScript
                try:
                    page.wait_for_selector('input[placeholder="First Name"]', timeout=20000)
                    logger.info("✅ Form detected with placeholders")
                except:
                    # Take screenshot to see current state
                    page.screenshot(path="placeholder_debug.png")
                    logger.warning("⚠️ Placeholders not set yet, trying to fill by position...")

                    # Fallback: fill by input position (1st=first, 2nd=last, 3rd=email, 4th=phone)
                    inputs = page.query_selector_all('input:visible')
                    logger.info(f"Found {len(inputs)} visible inputs, filling by position")

                # Try filling by placeholder first, then fallback to position
                filled_count = 0

                # Method 1: Fill by placeholder (if JavaScript has loaded)
                fields = [
                    ('input[placeholder="First Name"]', first_name, "First Name"),
                    ('input[placeholder="Last Name"]', last_name, "Last Name"),
                    ('input[placeholder="Email"]', email, "Email"),
                    ('input[placeholder="Phone"]', phone, "Phone")
                ]

                for selector, value, field_name in fields:
                    try:
                        page.fill(selector, value)
                        logger.info(f"✅ Filled {field_name}: {value}")
                        filled_count += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Could not fill {field_name} by placeholder: {e}")

                # Method 2: Fallback - fill by position if placeholders didn't work
                if filled_count < 4:
                    logger.info("🔄 Trying to fill by input position...")
                    visible_inputs = page.query_selector_all('input:visible')
                    values = [first_name, last_name, email, phone]

                    for i, value in enumerate(values):
                        if i < len(visible_inputs):
                            try:
                                visible_inputs[i].fill(value)
                                logger.info(f"✅ Filled input {i+1} by position: {value}")
                                filled_count += 1
                            except Exception as e:
                                logger.warning(f"⚠️ Could not fill input {i+1}: {e}")

                logger.info(f"📊 Form filling complete - filled {filled_count}/4 fields")

                # Step 4: Submit login
                logger.info("📤 Submitting login...")
                page.click('button:has-text("LOGIN")')
                time.sleep(5)

                # Step 5: Wait for 2FA prompt
                logger.info("⏳ Waiting for 2FA prompt...")

                # Check if 2FA code input appears
                try:
                    # Wait for 2FA input field (adjust selector as needed)
                    page.wait_for_selector('input[type="text"], input[type="number"]', timeout=30000)
                    logger.info("✅ 2FA prompt detected")
                except:
                    logger.warning("2FA prompt not detected, checking page state...")

                # Step 6: Get 2FA code from Gmail
                logger.info("📧 Waiting for 2FA code via Gmail...")
                code = self.gmail_extractor.wait_for_2fa_code(timeout_seconds=300)

                if not code:
                    logger.error("❌ No 2FA code received")
                    return False

                # Step 7: Enter 2FA code
                logger.info(f"🔐 Entering 2FA code: {code}")

                # Find 2FA input and enter code
                code_inputs = page.query_selector_all('input[type="text"], input[type="number"]')
                for input_field in code_inputs:
                    try:
                        input_field.fill(code)
                        break
                    except:
                        continue

                # Submit 2FA
                submit_buttons = page.query_selector_all('button[type="submit"], button:has-text("Submit"), button:has-text("Verify")')
                for button in submit_buttons:
                    try:
                        button.click()
                        break
                    except:
                        continue

                # Step 8: Wait for successful login
                logger.info("⏳ Waiting for login completion...")
                time.sleep(10)

                # Check for successful login indicators
                current_url = page.url
                if 'dashboard' in current_url.lower() or 'main' in current_url.lower():
                    logger.info("✅ Login successful!")

                    # Save authentication
                    context.storage_state(path=self.auth_file)
                    logger.info(f"💾 Authentication saved to {self.auth_file}")

                    return True
                else:
                    logger.error(f"❌ Login may have failed. Current URL: {current_url}")
                    return False

            except Exception as e:
                logger.error(f"❌ 2FA login failed: {str(e)}")
                return False

            finally:
                time.sleep(5)  # Brief pause before closing
                browser.close()

    def ensure_valid_session(self,
                           email: str,
                           first_name: str,
                           last_name: str,
                           phone: str) -> bool:
        """
        Ensure we have a valid Driver Pulse session, renewing if needed.

        Args:
            email: Login email
            first_name: First name
            last_name: Last name
            phone: Phone number

        Returns:
            bool: True if valid session available
        """
        if not self.is_session_expired():
            logger.info("✅ Session is still valid")
            return True

        logger.info("🔄 Session expired, renewing...")
        return self.perform_2fa_login(email, first_name, last_name, phone)

def create_2fa_handler(gmail_credentials: str = "gmail_credentials.json") -> DriverPulse2FAHandler:
    """
    Factory function to create a 2FA handler.

    Args:
        gmail_credentials: Path to Gmail API credentials

    Returns:
        DriverPulse2FAHandler: Configured handler
    """
    return DriverPulse2FAHandler(gmail_credentials)

if __name__ == "__main__":
    # Example usage and testing
    print("🔐 Driver Pulse 2FA Handler Test")
    print("=" * 50)

    # Test Gmail code extraction
    if GMAIL_AVAILABLE:
        print("📧 Testing Gmail API setup...")
        extractor = GmailCodeExtractor()

        if extractor.setup_gmail_api():
            print("✅ Gmail API ready")

            # Search for recent 2FA emails
            emails = extractor.search_2fa_emails(max_age_minutes=60)
            print(f"📧 Found {len(emails)} recent 2FA emails")

        else:
            print("❌ Gmail API setup failed")
            print("Setup instructions:")
            print("1. Go to Google Cloud Console")
            print("2. Enable Gmail API")
            print("3. Create credentials (OAuth 2.0)")
            print("4. Download as 'gmail_credentials.json'")
    else:
        print("⚠️ Gmail API libraries not installed")
        print("Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

    print(f"\n✅ 2FA handler test complete")