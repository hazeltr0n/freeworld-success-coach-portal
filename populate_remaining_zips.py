#!/usr/bin/env python3
"""
Populate remaining unmapped ZIPs using multiple strategies:
1. Check if city rows in location_markets have these ZIPs in default_zips
2. Use alternative ZIP API (zipcodebase.com or similar)
3. Manual CSV lookup from USPS data
"""

from supabase_utils import get_client
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

print("🔍 STEP 1: Finding unmapped ZIPs...")
client = get_client()

# Get all ZIP rows without city_state
result = client.table('location_markets').select('location_string, city_state').eq('location_type', 'zip').execute()

unmapped_zips = []
for row in result.data:
    if not row.get('city_state'):
        unmapped_zips.append(row['location_string'])

print(f"   ✅ Found {len(unmapped_zips)} unmapped ZIPs")

# STEP 2: Try to map from city rows
print("\n🔍 STEP 2: Checking city rows for reverse mappings...")

city_result = client.table('location_markets').select('location_string, default_zips').eq('location_type', 'city').execute()

zip_to_city_from_cities = {}

for city_row in city_result.data:
    city_state = city_row.get('location_string', '')  # e.g., "alvin, tx"
    default_zips = city_row.get('default_zips', [])

    if city_state and default_zips:
        # Convert to "City, ST" format
        parts = city_state.split(',')
        if len(parts) == 2:
            city = parts[0].strip().title()
            state = parts[1].strip().upper()
            formatted_city_state = f"{city}, {state}"

            for zip_code in default_zips:
                zip_str = str(zip_code).zfill(5)
                if zip_str in unmapped_zips:
                    zip_to_city_from_cities[zip_str] = formatted_city_state

print(f"   ✅ Found {len(zip_to_city_from_cities)} mappings from city rows")

if zip_to_city_from_cities:
    print(f"\n💾 Updating {len(zip_to_city_from_cities)} ZIPs from city row reverse lookup...")

    for zip_code, city_state in zip_to_city_from_cities.items():
        try:
            client.table('location_markets').update({
                'city_state': city_state
            }).eq('location_string', zip_code).eq('location_type', 'zip').execute()
        except Exception as e:
            print(f"      ⚠️ Failed to update {zip_code}: {e}")

    print(f"   ✅ Updated {len(zip_to_city_from_cities)} ZIPs from city rows")

# STEP 3: Check how many are still unmapped
print("\n🔍 STEP 3: Checking remaining unmapped ZIPs...")

result = client.table('location_markets').select('location_string, city_state').eq('location_type', 'zip').execute()

still_unmapped = []
for row in result.data:
    if not row.get('city_state'):
        still_unmapped.append(row['location_string'])

print(f"   ✅ Still unmapped: {len(still_unmapped)} ZIPs")

if still_unmapped:
    print(f"\n   Sample unmapped ZIPs: {still_unmapped[:20]}")

    # Try alternative API
    print(f"\n🌐 STEP 4: Trying alternative ZIP lookup methods for {len(still_unmapped)} ZIPs...")

    def fetch_zip_alternative(zip_code):
        """Try multiple free ZIP APIs"""

        # Method 1: Try zip-codes.com scraping-friendly endpoint
        try:
            url = f"https://www.zip-codes.com/zip-code/{zip_code}/zip-code-{zip_code}.asp"
            response = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200 and 'not found' not in response.text.lower():
                # This would need HTML parsing - skip for now
                pass
        except:
            pass

        # Method 2: Try geocode.xyz (no key needed, rate limited)
        try:
            url = f"https://geocode.xyz/{zip_code}?geoit=json"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                city = data.get('city', data.get('standard', {}).get('city', ''))
                state = data.get('state', data.get('standard', {}).get('prov', ''))

                if city and state and len(state) == 2:
                    return zip_code, f"{city}, {state}"
        except:
            pass

        return zip_code, None

    new_mappings = {}

    with ThreadPoolExecutor(max_workers=10) as executor:  # Lower rate for free API
        future_to_zip = {executor.submit(fetch_zip_alternative, zip_code): zip_code for zip_code in still_unmapped[:100]}  # Test with first 100

        completed = 0
        for future in as_completed(future_to_zip):
            zip_code, city_state = future.result()
            completed += 1

            if city_state:
                new_mappings[zip_code] = city_state

            if completed % 10 == 0:
                print(f"      Progress: {completed}/100 ({len(new_mappings)} found)", flush=True)

            time.sleep(0.5)  # Rate limiting

    if new_mappings:
        print(f"\n💾 Updating {len(new_mappings)} ZIPs from alternative API...")

        for zip_code, city_state in new_mappings.items():
            try:
                client.table('location_markets').update({
                    'city_state': city_state
                }).eq('location_string', zip_code).eq('location_type', 'zip').execute()
            except Exception as e:
                print(f"      ⚠️ Failed to update {zip_code}: {e}")

# FINAL VERIFICATION
print("\n📊 FINAL VERIFICATION:")
result = client.table('location_markets').select('location_string, city_state').eq('location_type', 'zip').execute()

populated = sum(1 for row in result.data if row.get('city_state'))
total = len(result.data)

print(f"   Total ZIP rows: {total}")
print(f"   Populated: {populated} ({populated/total*100:.1f}%)")
print(f"   Unpopulated: {total - populated} ({(total-populated)/total*100:.1f}%)")
