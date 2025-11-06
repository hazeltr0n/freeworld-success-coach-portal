#!/usr/bin/env python3
"""
Driver Pulse 2FA Automation using Gmail IMAP (Simple App Password)

This module provides automated 2FA code extraction from Gmail using IMAP.
NO OAuth tokens, NO refresh bullshit - just a simple app password that works forever.
"""

import os
import re
import time
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GmailIMAPCodeExtractor:
    """Extracts 2FA codes from Gmail using IMAP with App Password"""

    def __init__(self,
                 gmail_address: Optional[str] = None,
                 gmail_app_password: Optional[str] = None):
        """
        Initialize Gmail IMAP code extractor.

        Args:
            gmail_address: Gmail email address (defaults to env var GMAIL_ADDRESS)
            gmail_app_password: Gmail app password (defaults to env var GMAIL_APP_PASSWORD)
        """
        self.gmail_address = gmail_address or os.getenv('GMAIL_ADDRESS')
        self.gmail_app_password = gmail_app_password or os.getenv('GMAIL_APP_PASSWORD')

        if not self.gmail_address or not self.gmail_app_password:
            raise ValueError(
                "Gmail credentials not provided. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD env vars "
                "or pass them to constructor."
            )

        self.mail = None

    def connect(self) -> bool:
        """
        Connect to Gmail via IMAP.

        Returns:
            bool: True if connection successful
        """
        try:
            logger.info("📧 Connecting to Gmail via IMAP...")
            self.mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
            self.mail.login(self.gmail_address, self.gmail_app_password)
            logger.info("✅ Connected to Gmail successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Gmail: {e}")
            return False

    def disconnect(self):
        """Disconnect from Gmail"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
                logger.info("📧 Disconnected from Gmail")
            except:
                pass

    def search_2fa_emails(self,
                         sender_filter: str = "noreply@tenstreet.com",
                         subject_filter: str = "Authorization Code",
                         max_age_minutes: int = 10) -> List[bytes]:
        """
        Search for recent 2FA emails.

        Args:
            sender_filter: Email sender to filter by
            subject_filter: Subject keyword to filter by
            max_age_minutes: Maximum age of emails to consider

        Returns:
            List[bytes]: List of email IDs
        """
        if not self.mail:
            if not self.connect():
                return []

        try:
            # Select inbox
            self.mail.select('INBOX')

            # Calculate date for SINCE filter
            since_date = datetime.now() - timedelta(minutes=max_age_minutes)
            date_str = since_date.strftime('%d-%b-%Y')

            # Build IMAP search criteria
            # Search for emails from sender with subject containing keyword, since date, unseen
            search_criteria = f'(FROM "{sender_filter}" SUBJECT "{subject_filter}" SINCE {date_str} UNSEEN)'

            logger.info(f"🔍 Searching Gmail: {search_criteria}")

            # Search emails
            status, messages = self.mail.search(None, search_criteria)

            if status != 'OK':
                logger.error(f"❌ Search failed: {status}")
                return []

            email_ids = messages[0].split()
            logger.info(f"📧 Found {len(email_ids)} matching emails")

            return email_ids

        except Exception as e:
            logger.error(f"❌ Gmail search failed: {e}")
            return []

    def extract_code_from_email(self, email_id: bytes) -> Optional[str]:
        """
        Extract 2FA code from a specific email.

        Args:
            email_id: Email ID from IMAP search

        Returns:
            str: Extracted 2FA code or None
        """
        try:
            # Fetch email
            status, msg_data = self.mail.fetch(email_id, '(RFC822)')

            if status != 'OK':
                logger.error(f"❌ Failed to fetch email {email_id}")
                return None

            # Parse email
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)

            # Extract subject
            subject = email_message['Subject']
            if subject:
                # Decode subject if encoded
                decoded_subject = decode_header(subject)[0]
                if isinstance(decoded_subject[0], bytes):
                    subject = decoded_subject[0].decode(decoded_subject[1] or 'utf-8')
                else:
                    subject = decoded_subject[0]

                logger.info(f"📧 Email subject: {subject}")

                # Look for "Tenstreet Authorization Code - 136323" pattern in subject
                tenstreet_match = re.search(r'Tenstreet Authorization Code\s*-\s*(\d+)', subject, re.IGNORECASE)
                if tenstreet_match:
                    code = tenstreet_match.group(1)
                    logger.info(f"✅ Found Tenstreet code in subject: {code}")

                    # Mark email as read
                    try:
                        self.mail.store(email_id, '+FLAGS', '\\Seen')
                        logger.info("📧 Email marked as read")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not mark email as read: {e}")

                    return code

            # Fallback: Extract from email body
            body_text = self._extract_email_body(email_message)
            if body_text:
                code = self._extract_code_from_text(body_text)
                if code:
                    logger.info(f"✅ Extracted 2FA code from body: {code}")

                    # Mark email as read
                    self.mail.store(email_id, '+FLAGS', '\\Seen')
                    return code

            logger.warning(f"No 2FA code found in email {email_id}")
            return None

        except Exception as e:
            logger.error(f"❌ Code extraction failed: {e}")
            return None

    def _extract_email_body(self, email_message) -> Optional[str]:
        """Extract text body from email message"""
        try:
            body_text = ""

            if email_message.is_multipart():
                # Handle multipart emails
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    # Skip attachments
                    if "attachment" in content_disposition:
                        continue

                    # Get text/plain parts
                    if content_type == "text/plain":
                        try:
                            body_text = part.get_payload(decode=True).decode()
                            break
                        except:
                            continue
            else:
                # Simple email
                try:
                    body_text = email_message.get_payload(decode=True).decode()
                except:
                    pass

            return body_text

        except Exception as e:
            logger.error(f"Error extracting email body: {e}")
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
            email_ids = self.search_2fa_emails(max_age_minutes=15)

            for email_id in email_ids:
                code = self.extract_code_from_email(email_id)
                if code:
                    return code

            # Wait before checking again
            logger.info(f"🔄 No 2FA code yet, checking again in {check_interval}s...")
            time.sleep(check_interval)

        logger.error(f"❌ Timeout waiting for 2FA code")
        return None

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


if __name__ == "__main__":
    # Example usage and testing
    print("🔐 Gmail IMAP 2FA Code Extractor Test")
    print("=" * 50)

    # Test connection
    try:
        with GmailIMAPCodeExtractor() as extractor:
            print("✅ Gmail IMAP connection successful")

            # Search for recent 2FA emails
            email_ids = extractor.search_2fa_emails(max_age_minutes=60)
            print(f"📧 Found {len(email_ids)} recent 2FA emails")

            # Try to extract code from most recent email
            if email_ids:
                code = extractor.extract_code_from_email(email_ids[-1])
                if code:
                    print(f"✅ Extracted code: {code}")
                else:
                    print("❌ Could not extract code")
            else:
                print("ℹ️ No recent 2FA emails found")

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nSetup instructions:")
        print("1. Go to Google Account → Security → 2-Step Verification")
        print("2. Scroll down to 'App passwords'")
        print("3. Generate app password for 'Mail'")
        print("4. Set environment variables:")
        print("   export GMAIL_ADDRESS='your-email@gmail.com'")
        print("   export GMAIL_APP_PASSWORD='xxxx xxxx xxxx xxxx'")
    except Exception as e:
        print(f"❌ Test failed: {e}")

    print(f"\n✅ Test complete")
