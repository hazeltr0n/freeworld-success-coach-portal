#!/usr/bin/env python3
"""
Refresh Gmail OAuth Token

Run this locally to refresh your Gmail token, then copy the contents
of gmail_token.json to GitHub Secrets as DRIVER_PULSE_GMAIL_TOKEN
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

def main():
    if not os.path.exists('gmail_token.json'):
        print("❌ gmail_token.json not found")
        print("   Run the initial OAuth flow first to create it")
        return False

    print("🔍 Loading Gmail token...")
    creds = Credentials.from_authorized_user_file('gmail_token.json')

    if creds.valid:
        print("✅ Token is still valid - no refresh needed")
        return True

    if creds.expired and creds.refresh_token:
        print("🔄 Token expired, refreshing...")
        try:
            creds.refresh(Request())
            print("✅ Token refreshed successfully!")

            # Save refreshed token
            with open('gmail_token.json', 'w') as token:
                token.write(creds.to_json())
            print("💾 Refreshed token saved to gmail_token.json")

            print("\n📋 Next steps:")
            print("1. Copy the contents of gmail_token.json")
            print("2. Go to GitHub repository Settings → Secrets → Actions")
            print("3. Update DRIVER_PULSE_GMAIL_TOKEN with the new token")

            return True

        except Exception as e:
            print(f"❌ Token refresh failed: {e}")
            print("   You may need to re-authenticate from scratch")
            return False
    else:
        print("❌ Token invalid and no refresh_token available")
        print("   You need to re-authenticate from scratch")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
