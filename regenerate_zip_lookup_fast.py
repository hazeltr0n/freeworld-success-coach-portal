#!/usr/bin/env python3
"""
Generate ZIP_TO_CITY_STATE mappings in 3 steps:
1. Extract existing ZIP → City, State from Supabase jobs
2. Add all ZIPs from market search radius CSV
3. Use API to fill in missing city/state data
"""

import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from supabase_utils import get_client

def fetch_single_zip(zip_code):
    """Fetch city/state for a single ZIP code from API"""
    try:
        url = f"https://ziptasticapi.com/{zip_code}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            city = data.get('city', '')
            state = data.get('state_short', data.get('state', ''))

            if city and state:
                return zip_code, f"{city}, {state}"

        return zip_code, None

    except Exception:
        return zip_code, None

# STEP 1: Extract from Supabase
print("🔍 STEP 1: Extracting ZIP → City, State mappings from Supabase jobs database...")
client = get_client()

result = client.table('jobs').select('zip_code, location').execute()

zip_mappings = {}

for row in result.data:
    zip_code = row.get('zip_code')
    location = row.get('location')

    if zip_code and location:
        zip_code = str(zip_code).zfill(5)

        # If location is in "City, ST" format, use it
        if location and ',' in location and location != 'Unknown Location':
            parts = location.split(',')
            if len(parts) == 2:
                city = parts[0].strip()
                state = parts[1].strip()
                # Only use if state looks like a 2-letter abbreviation
                if len(state) == 2 and state.isupper():
                    if zip_code not in zip_mappings:
                        zip_mappings[zip_code] = location

print(f"   ✅ Extracted {len(zip_mappings)} ZIP mappings from Supabase")

# STEP 2: Add ZIPs from CSV
print("\n🔍 STEP 2: Adding ZIPs from market search radius CSV...")

df = pd.read_csv('/Users/freeworld_james/Downloads/market search radius.csv')

all_zips = set(zip_mappings.keys())

for zips_str in df['All zip codes']:
    zips = str(zips_str).split(',')
    for zip_code in zips:
        zip_code = zip_code.strip().zfill(5)
        all_zips.add(zip_code)

print(f"   ✅ Total unique ZIPs after adding CSV: {len(all_zips)}")
print(f"   Already have city/state for: {len(zip_mappings)}")

# STEP 3: Fetch missing from API
zips_to_fetch = all_zips - set(zip_mappings.keys())

print(f"\n🌐 STEP 3: Fetching {len(zips_to_fetch)} missing ZIPs from API...")

if zips_to_fetch:
    with ThreadPoolExecutor(max_workers=100) as executor:
        future_to_zip = {executor.submit(fetch_single_zip, zip_code): zip_code for zip_code in zips_to_fetch}

        completed = 0
        failed = 0
        for future in as_completed(future_to_zip):
            zip_code, city_state = future.result()
            completed += 1

            if city_state:
                zip_mappings[zip_code] = city_state
            else:
                failed += 1

            if completed % 100 == 0:
                print(f"      Progress: {completed}/{len(zips_to_fetch)} ({failed} failed so far)")

    print(f"\n   ✅ API fetch complete: {len(zips_to_fetch) - failed} succeeded, {failed} failed")

print(f"\n✅ Final result: {len(zip_mappings)} ZIP codes mapped")

# Write to file
print("\n💾 Writing to zip_market_lookup.py...")
with open('zip_market_lookup.py', 'w') as f:
    f.write('"""Auto-generated ZIP code to City, State mappings"""\n')
    f.write('# Sources:\n')
    f.write('# 1. Supabase jobs database (existing location fields)\n')
    f.write('# 2. Market search radius CSV\n')
    f.write('# 3. ziptasticapi.com API\n\n')
    f.write('ZIP_TO_CITY_STATE = {\n')

    for zip_code, city_state in sorted(zip_mappings.items()):
        city_state_escaped = city_state.replace("'", "\\'")
        f.write(f"    '{zip_code}': '{city_state_escaped}',\n")

    f.write('}\n')

print(f"✅ SUCCESS! Generated zip_market_lookup.py with {len(zip_mappings)} mappings")
