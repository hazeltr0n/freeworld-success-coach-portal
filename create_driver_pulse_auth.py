#!/usr/bin/env python3
"""
DriverPulse Authentication Script
Run this to create/refresh authentication for DriverPulse scraper
Uses credentials from .streamlit/secrets.toml
"""

import os
import json
from driver_pulse_source import DriverPulseSource

def load_credentials_from_secrets():
    """Load credentials from Streamlit secrets"""
    try:
        import toml
        secrets_path = ".streamlit/secrets.toml"
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            return {
                'email': secrets.get('DRIVER_PULSE_EMAIL'),
                'first_name': secrets.get('DRIVER_PULSE_FIRST_NAME'),
                'last_name': secrets.get('DRIVER_PULSE_LAST_NAME'),
                'phone': secrets.get('DRIVER_PULSE_PHONE'),
                'gmail_client_id': secrets.get('GMAIL_CLIENT_ID'),
                'gmail_client_secret': secrets.get('GMAIL_CLIENT_SECRET')
            }
    except Exception as e:
        print(f"⚠️ Could not load secrets: {e}")
    return None

def setup_gmail_credentials(client_id, client_secret):
    """Create gmail_credentials.json file for 2FA"""
    credentials = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": ["http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }

    with open('gmail_credentials.json', 'w') as f:
        json.dump(credentials, f, indent=2)

    print("✅ Created gmail_credentials.json for 2FA")

def main():
    print("=" * 60)
    print("🔐 DriverPulse Authentication Setup")
    print("=" * 60)
    print()

    # Load credentials from secrets
    print("📂 Loading credentials from .streamlit/secrets.toml...")
    creds = load_credentials_from_secrets()

    if not creds or not all([creds['email'], creds['first_name'], creds['last_name'], creds['phone']]):
        print("❌ Missing credentials in secrets.toml")
        print()
        print("Please add these to .streamlit/secrets.toml:")
        print("  DRIVER_PULSE_EMAIL")
        print("  DRIVER_PULSE_FIRST_NAME")
        print("  DRIVER_PULSE_LAST_NAME")
        print("  DRIVER_PULSE_PHONE")
        return

    print(f"✅ Using credentials for: {creds['email']}")
    print()

    # Setup Gmail credentials for 2FA
    if creds['gmail_client_id'] and creds['gmail_client_secret']:
        setup_gmail_credentials(creds['gmail_client_id'], creds['gmail_client_secret'])
    else:
        print("⚠️ Gmail API credentials not found - 2FA will require manual code entry")

    print()
    print("🚀 Starting authentication process...")
    print("📌 A browser window will open")
    print("📌 2FA code will be handled automatically (if Gmail API is configured)")
    print()

    # Create source and authenticate
    source = DriverPulseSource()

    try:
        success = source.create_new_authentication(
            email=creds['email'],
            first_name=creds['first_name'],
            last_name=creds['last_name'],
            phone=creds['phone']
        )

        if success:
            print()
            print("=" * 60)
            print("✅ Authentication successful!")
            print("=" * 60)
            print()
            print("You can now run the DriverPulse scraper.")
            print()
        else:
            print()
            print("❌ Authentication failed")
            print()

    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        print()
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
