#!/usr/bin/env python3
"""
Refresh DriverPulse Authentication and Store in Supabase
Runs in GitHub Actions to keep authentication fresh
"""

print("=" * 60)
print("SCRIPT STARTED")
print("=" * 60)
import sys
sys.stdout.flush()

import os
import json
from datetime import datetime

print("Basic imports successful")
sys.stdout.flush()

try:
    from supabase import create_client, Client
    print("Supabase import successful")
    sys.stdout.flush()
except Exception as e:
    print(f"FAILED to import supabase: {e}")
    sys.stdout.flush()
    sys.exit(1)

try:
    from driver_pulse_source import DriverPulseSource
    print("DriverPulseSource import successful")
    sys.stdout.flush()
except Exception as e:
    print(f"FAILED to import DriverPulseSource: {e}")
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
    sys.exit(1)

def store_auth_in_supabase(auth_data: dict, supabase: Client) -> bool:
    """
    Store DriverPulse auth data in Supabase system_config table

    Args:
        auth_data: Auth data from DriverPulse
        supabase: Supabase client

    Returns:
        bool: True if successful
    """
    try:
        # Convert auth_data to JSON string for storage
        auth_json = json.dumps(auth_data)

        # Upsert to system_config table
        result = supabase.table('system_config').upsert({
            'config_key': 'driver_pulse_auth',
            'config_value': auth_json,
            'updated_at': datetime.now().isoformat()
        }, on_conflict='config_key').execute()

        print(f"✅ Auth stored in Supabase (updated_at: {datetime.now().isoformat()})")
        return True

    except Exception as e:
        print(f"❌ Failed to store auth in Supabase: {str(e)}")
        return False


def refresh_gmail_token_if_needed() -> bool:
    """
    Check and refresh Gmail OAuth token if expired
    Returns True if token is valid/refreshed, False if needs re-authentication
    """
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        if not os.path.exists('gmail_token.json'):
            print("⚠️ No existing Gmail token found")
            return False

        print("🔍 Checking Gmail token validity...")
        creds = Credentials.from_authorized_user_file('gmail_token.json')

        if creds.valid:
            print("✅ Gmail token is still valid")
            return True

        if creds.expired and creds.refresh_token:
            print("🔄 Gmail token expired, refreshing...")
            try:
                creds.refresh(Request())
                print("✅ Gmail token refreshed successfully")

                # Save refreshed token back to file
                with open('gmail_token.json', 'w') as token:
                    token.write(creds.to_json())
                print("💾 Refreshed Gmail token saved")

                return True
            except Exception as refresh_error:
                print(f"❌ Gmail token refresh failed: {refresh_error}")
                return False
        else:
            print("❌ Gmail token invalid and no refresh_token available")
            return False

    except Exception as e:
        print(f"⚠️ Error checking Gmail token: {e}")
        return False


def main():
    """Main entry point for auth refresh"""

    # Get credentials from environment
    email = os.getenv('DRIVER_PULSE_EMAIL')
    first_name = os.getenv('DRIVER_PULSE_FIRST_NAME')
    last_name = os.getenv('DRIVER_PULSE_LAST_NAME')
    phone = os.getenv('DRIVER_PULSE_PHONE')

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')

    # Validate required environment variables
    if not all([email, first_name, last_name, phone]):
        print("❌ Missing DriverPulse credentials in environment")
        sys.exit(1)

    if not all([supabase_url, supabase_key]):
        print("❌ Missing Supabase credentials in environment")
        sys.exit(1)

    print("🚀 Starting DriverPulse authentication refresh...")
    print(f"   Email: '{email}' (len={len(email) if email else 0})")
    print(f"   First Name: '{first_name}' (len={len(first_name) if first_name else 0})")
    print(f"   Last Name: '{last_name}' (len={len(last_name) if last_name else 0})")
    print(f"   Phone: '{phone}' (len={len(phone) if phone else 0})")

    # Refresh Gmail token if needed (auto-refresh using refresh_token)
    if not refresh_gmail_token_if_needed():
        print("⚠️ Gmail token needs manual re-authentication (refresh_token missing/expired)")
        print("   This should only happen once - the refresh_token normally doesn't expire")

    # Initialize DriverPulse source
    source = DriverPulseSource()

    try:
        # Create new authentication using headless mode
        success = source.create_new_authentication(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            gmail_credentials="gmail_credentials.json",
            headless=True
        )

        if not success:
            print("❌ Authentication failed")
            sys.exit(1)

        print("✅ Authentication created successfully")

        # Load the auth data that was just created
        if not os.path.exists('auth.json'):
            print("❌ auth.json not found after authentication")
            sys.exit(1)

        with open('auth.json', 'r') as f:
            auth_data = json.load(f)

        print(f"✅ Auth data loaded ({len(auth_data.get('cookies', []))} cookies)")

        # Connect to Supabase
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")

        # Store auth in Supabase
        if store_auth_in_supabase(auth_data, supabase):
            print("🎉 Auth refresh complete!")
            sys.exit(0)
        else:
            print("❌ Failed to store auth in Supabase")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error during auth refresh: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
