#!/usr/bin/env python3
"""Generate static ZIP→market lookup file for instant filtering"""

import sys
sys.path.insert(0, '.')
from job_memory_db import JobMemoryDB

# Get client
memory = JobMemoryDB()
client = memory.supabase

# Fetch all ZIPs with markets
result = client.table('location_markets').select('location_string, markets').eq('location_type', 'zip').execute()

# Build lookups
zip_to_markets = {}
for row in result.data:
    zip_code = row['location_string']
    markets = row.get('markets', [])
    zip_to_markets[zip_code] = markets

valid_zips = set(zip_to_markets.keys())

print(f'📍 Loaded {len(valid_zips)} ZIPs from location_markets')

# Write to Python file
with open('zip_market_lookup.py', 'w') as f:
    f.write('"""Auto-generated ZIP to market lookup for instant filtering"""\n\n')
    f.write(f'# Set of all valid ZIPs - {len(valid_zips)} total\n')
    f.write(f'VALID_ZIPS = {repr(valid_zips)}\n\n')
    f.write(f'# Dict mapping ZIP to list of markets - {len(zip_to_markets)} total\n')

    # Write full dict
    import json
    f.write('ZIP_TO_MARKETS = ')
    json.dump(zip_to_markets, f, indent=2)
    f.write('\n')

print(f'✅ Created zip_market_lookup.py')
print(f'   - VALID_ZIPS set: {len(valid_zips)} entries')
print(f'   - ZIP_TO_MARKETS dict: {len(zip_to_markets)} entries')
