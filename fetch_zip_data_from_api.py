#!/usr/bin/env python3
"""
Fetch ZIP code data from API and generate comprehensive ZIP_TO_CITY_STATE mappings
Uses the free ZipCodeAPI or similar service to get accurate city/state data
"""

import requests
import time
from collections import OrderedDict

def fetch_all_zip_codes():
    """
    Fetch ZIP code data from free API sources
    Using ziptastic.com or similar free ZIP code API
    """

    # First, get all ZIPs we currently need
    from supabase_utils import get_client

    # Central market ZIPs
    market_central_zips = {
        'Dallas': '75060',
        'Houston': '77007',
        'Phoenix': '85009',
        'Denver': '80218',
        'Las Vegas': '89107',
        'Stockton': '95205',
        'Bay Area': '94501',
        'Inland Empire': '92324',
        'Trenton': '07017',
        'Newark': '08638'
    }

    client = get_client()

    # Get all unique ZIP codes from DriverPulse jobs
    result = client.table('jobs').select('zip_code').eq('source', 'driver_pulse').execute()

    unique_zips = set()
    for row in result.data:
        zip_code = row.get('zip_code')
        if zip_code:
            unique_zips.add(str(zip_code).zfill(5))

    # Add central market ZIPs
    for zip_code in market_central_zips.values():
        unique_zips.add(zip_code)

    print(f"Found {len(unique_zips)} unique ZIP codes to fetch")

    zip_mappings = {}

    # Use ziptastic.com API (free, no key required)
    for i, zip_code in enumerate(sorted(unique_zips), 1):
        try:
            # Rate limit: 1 request per second
            if i > 1:
                time.sleep(1)

            url = f"https://ziptasticapi.com/{zip_code}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                city = data.get('city', '')
                state = data.get('state_short', data.get('state', ''))

                if city and state:
                    zip_mappings[zip_code] = f"{city}, {state}"
                    print(f"  [{i}/{len(unique_zips)}] {zip_code} -> {city}, {state}")
                else:
                    print(f"  [{i}/{len(unique_zips)}] {zip_code} -> INCOMPLETE DATA")
            else:
                print(f"  [{i}/{len(unique_zips)}] {zip_code} -> API ERROR {response.status_code}")

        except Exception as e:
            print(f"  [{i}/{len(unique_zips)}] {zip_code} -> ERROR: {e}")

    return zip_mappings

def write_zip_lookup_file(zip_mappings):
    """Write the ZIP mappings to zip_market_lookup.py"""

    with open('zip_market_lookup.py', 'w') as f:
        f.write('"""Auto-generated ZIP code to City, State mappings from API"""\n\n')
        f.write('ZIP_TO_CITY_STATE = {\n')

        for zip_code, city_state in sorted(zip_mappings.items()):
            # Escape single quotes in city names
            city_state_escaped = city_state.replace("'", "\\'")
            f.write(f"    '{zip_code}': '{city_state_escaped}',\n")

        f.write('}\n')

    print(f"\n✅ Generated zip_market_lookup.py with {len(zip_mappings)} mappings")

if __name__ == "__main__":
    print("🔍 Fetching ZIP code data from API...")
    zip_mappings = fetch_all_zip_codes()

    if zip_mappings:
        write_zip_lookup_file(zip_mappings)
    else:
        print("❌ No ZIP mappings fetched")
