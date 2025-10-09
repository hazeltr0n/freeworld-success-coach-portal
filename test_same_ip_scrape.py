#!/usr/bin/env python3
"""
Test: Create auth and scrape from SAME IP to verify IP mismatch theory
"""

import os
import sys
from driver_pulse_source import DriverPulseSource

# Get credentials from environment or secrets
email = os.getenv("DRIVER_PULSE_EMAIL", "freeworldplacement@gmail.com")
first_name = os.getenv("DRIVER_PULSE_FIRST_NAME", "Claude")
last_name = os.getenv("DRIVER_PULSE_LAST_NAME", "Anthony")
phone = os.getenv("DRIVER_PULSE_PHONE", "555-123-4567")

print("🧪 TEST: Auth + Scrape from SAME IP")
print("=" * 50)

# Step 1: Create fresh auth
print("\n1️⃣ Creating fresh authentication...")
source = DriverPulseSource()
success = source.create_new_authentication(
    email=email,
    first_name=first_name,
    last_name=last_name,
    phone=phone,
    headless=False  # Show browser for manual 2FA
)

if not success:
    print("❌ Auth creation failed")
    sys.exit(1)

print("✅ Auth created successfully")

# Step 2: IMMEDIATELY scrape from same IP
print("\n2️⃣ Scraping jobs (from SAME IP that just created auth)...")
try:
    results = source.search_jobs('CDL driver', max_results=10)
    print(f"✅ SUCCESS! Found {len(results)} jobs")

    if results:
        print("\n📋 First job:")
        job = results[0]
        print(f"   Company: {job.get('company_name', 'N/A')}")
        print(f"   Location: {job.get('location', 'N/A')}")
        print(f"   ID: {job.get('job_id', 'N/A')}")

    print("\n🎉 IP MISMATCH THEORY: DISPROVEN")
    print("   Auth and scraping work from the same IP!")

except Exception as e:
    print(f"❌ FAILED: {e}")
    print("\n⚠️ IP MISMATCH THEORY: LIKELY CORRECT")
    print("   Auth worked but scraping failed from same IP")
    import traceback
    traceback.print_exc()
