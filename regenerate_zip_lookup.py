#!/usr/bin/env python3
"""
Regenerate zip_market_lookup.py from freeworld_cbsa_zips.csv
Maps ALL ZIP codes to "City, ST" format
"""

import pandas as pd

# Read the CSV
df = pd.read_csv('freeworld_cbsa_zips.csv')

# Create ZIP -> "City, ST" mapping
zip_to_city_state = {}

for _, row in df.iterrows():
    zip_code = str(row['ZIP Code']).zfill(5)  # Ensure 5 digits with leading zeros
    city = row['USPS Default City for ZIP']
    state = row['USPS Default State for ZIP']

    if pd.notna(city) and pd.notna(state):
        zip_to_city_state[zip_code] = f"{city}, {state}"

print(f"Generated {len(zip_to_city_state)} ZIP code mappings")

# Write to zip_market_lookup.py
with open('zip_market_lookup.py', 'w') as f:
    f.write('"""Auto-generated ZIP code to City, State mappings from freeworld_cbsa_zips.csv"""\n\n')
    f.write('ZIP_TO_CITY_STATE = {\n')

    for zip_code, city_state in sorted(zip_to_city_state.items()):
        # Escape single quotes in city names
        city_state_escaped = city_state.replace("'", "\\'")
        f.write(f"    '{zip_code}': '{city_state_escaped}',\n")

    f.write('}\n')

print("✅ Generated zip_market_lookup.py")
