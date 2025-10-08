#!/usr/bin/env python3
"""
Regenerate zip_market_lookup.py from location_markets table
This is now the source of truth for ZIP → City, ST mappings
"""

from supabase_utils import get_client

print("🔍 Loading ZIPs from location_markets table (source of truth)...")
client = get_client()

# Get all ZIP rows with city_state populated
result = client.table('location_markets').select('location_string, city_state, markets').eq('location_type', 'zip').execute()

zip_to_city_state = {}
zip_to_market = {}

for row in result.data:
    zip_code = row['location_string']
    city_state = row.get('city_state')
    markets = row.get('markets', [])

    if city_state:
        zip_to_city_state[zip_code] = city_state

        # Store first market if available
        if markets and len(markets) > 0:
            zip_to_market[zip_code] = markets[0]

print(f"   ✅ Found {len(zip_to_city_state)} ZIPs with city/state mappings")
print(f"   ✅ Found {len(zip_to_market)} ZIPs with market mappings")

# Write to zip_market_lookup.py
print("\n💾 Writing to zip_market_lookup.py...")
with open('zip_market_lookup.py', 'w') as f:
    f.write('"""Auto-generated ZIP code mappings from location_markets table (source of truth)"""\n\n')

    f.write('ZIP_TO_CITY_STATE = {\n')
    for zip_code, city_state in sorted(zip_to_city_state.items()):
        city_state_escaped = city_state.replace("'", "\\'")

        # Add market comment if available
        if zip_code in zip_to_market:
            f.write(f"    '{zip_code}': '{city_state_escaped}',  # Market: {zip_to_market[zip_code]}\n")
        else:
            f.write(f"    '{zip_code}': '{city_state_escaped}',\n")

    f.write('}\n\n')

    # Add VALID_ZIPS set for fast filtering
    f.write('# All valid ZIPs for filtering (includes both mapped and unmapped)\n')
    f.write('VALID_ZIPS = {\n')

    all_zips = [row['location_string'] for row in result.data]
    for i, zip_code in enumerate(sorted(all_zips)):
        if (i + 1) % 10 == 0:
            f.write(f"    '{zip_code}',\n")
        else:
            f.write(f"    '{zip_code}', ")

        if (i + 1) % 10 == 0:
            f.write('\n')

    f.write('\n}\n')

print(f"✅ Generated zip_market_lookup.py:")
print(f"   - {len(zip_to_city_state)} ZIP → City, ST mappings")
print(f"   - {len(all_zips)} total valid ZIPs for filtering")
print(f"   - Coverage: {len(zip_to_city_state)/len(all_zips)*100:.1f}%")
