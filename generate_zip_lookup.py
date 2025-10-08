#!/usr/bin/env python3
"""Generate static ZIP→market lookup file for instant filtering"""

import sys
sys.path.insert(0, '.')
from job_memory_db import JobMemoryDB

# Get client
memory = JobMemoryDB()
client = memory.supabase

# Fetch all ZIPs with markets AND city_state
result = client.table('location_markets').select('location_string, markets, city_state').eq('location_type', 'zip').execute()

# Build lookups
zip_to_markets = {}
zip_to_city_state = {}

for row in result.data:
    zip_code = row['location_string']
    markets = row.get('markets', [])
    city_state = row.get('city_state', '')

    zip_to_markets[zip_code] = markets
    if city_state:
        zip_to_city_state[zip_code] = city_state

valid_zips = set(zip_to_markets.keys())

print(f'📍 Loaded {len(valid_zips)} ZIPs from location_markets')
print(f'   - With City, ST mapping: {len(zip_to_city_state)}')

# Write to Python file
with open('zip_market_lookup.py', 'w') as f:
    f.write('"""Auto-generated ZIP code mappings from location_markets table (source of truth)"""\n\n')

    # Write ZIP_TO_CITY_STATE dict with inline market comments
    f.write(f'ZIP_TO_CITY_STATE = {{\n')
    for zip_code in sorted(zip_to_city_state.keys()):
        city_state = zip_to_city_state[zip_code]
        markets = zip_to_markets.get(zip_code, [])
        market_str = ', '.join(markets) if markets else 'No market'
        f.write(f"    {repr(zip_code)}: {repr(city_state)},  # Market: {market_str}\n")
    f.write('}\n\n')

    # Write ZIP_TO_MARKETS dict
    import json
    f.write(f'# Dict mapping ZIP to list of markets - {len(zip_to_markets)} total\n')
    f.write('ZIP_TO_MARKETS = ')
    json.dump(zip_to_markets, f, indent=2)
    f.write('\n\n')

    # Write VALID_ZIPS set
    f.write(f'# Set of all valid ZIPs - {len(valid_zips)} total\n')
    f.write(f'VALID_ZIPS = {{\n')
    # Write in rows of 10 for readability
    zips_list = sorted(valid_zips)
    for i in range(0, len(zips_list), 10):
        batch = zips_list[i:i+10]
        formatted = ',     '.join(repr(z) for z in batch)
        f.write(f'    {formatted},\n')
        if (i + 10) % 100 == 0:
            f.write('\n')  # Extra newline every 100 ZIPs
    f.write('}\n')

print(f'✅ Created zip_market_lookup.py')
print(f'   - ZIP_TO_CITY_STATE dict: {len(zip_to_city_state)} entries')
print(f'   - ZIP_TO_MARKETS dict: {len(zip_to_markets)} entries')
print(f'   - VALID_ZIPS set: {len(valid_zips)} entries')
