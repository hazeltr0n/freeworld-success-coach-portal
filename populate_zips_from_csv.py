#!/usr/bin/env python3
"""
Populate location_markets with all FreeWorld CBSA ZIPs using CSV exports

Uses:
1. freeworld_cbsa_zips.csv - Filtered ZIP data (13,983 ZIPs in FreeWorld CBSAs)
2. location_markets_rows.csv - Full location_markets export from Supabase

Strategy:
- Match ZIP cities to location_markets cities → get Markets
- Group by CBSA → determine CBSA primary market
- Bulk insert all ZIPs with proper CBSA and market fields
"""

import pandas as pd
import json
from companies_rollup import get_client

STATE_ABBR_MAP = {
    'alabama': 'al', 'alaska': 'ak', 'arizona': 'az', 'arkansas': 'ar', 'california': 'ca',
    'colorado': 'co', 'connecticut': 'ct', 'delaware': 'de', 'district of columbia': 'dc',
    'florida': 'fl', 'georgia': 'ga', 'hawaii': 'hi', 'idaho': 'id', 'illinois': 'il',
    'indiana': 'in', 'iowa': 'ia', 'kansas': 'ks', 'kentucky': 'ky', 'louisiana': 'la',
    'maine': 'me', 'maryland': 'md', 'massachusetts': 'ma', 'michigan': 'mi', 'minnesota': 'mn',
    'mississippi': 'ms', 'missouri': 'mo', 'montana': 'mt', 'nebraska': 'ne', 'nevada': 'nv',
    'new hampshire': 'nh', 'new jersey': 'nj', 'new mexico': 'nm', 'new york': 'ny',
    'north carolina': 'nc', 'north dakota': 'nd', 'ohio': 'oh', 'oklahoma': 'ok', 'oregon': 'or',
    'pennsylvania': 'pa', 'rhode island': 'ri', 'south carolina': 'sc', 'south dakota': 'sd',
    'tennessee': 'tn', 'texas': 'tx', 'utah': 'ut', 'vermont': 'vt', 'virginia': 'va',
    'washington': 'wa', 'west virginia': 'wv', 'wisconsin': 'wi', 'wyoming': 'wy'
}

def normalize_location(loc_str):
    """Normalize location string for matching"""
    if pd.isna(loc_str) or not loc_str:
        return None
    return str(loc_str).lower().strip()

def normalize_cbsa_for_matching(cbsa_str):
    """
    Normalize CBSA names to handle variations between Free Agents and ZIP data

    Examples:
    - "Houston-The Woodlands-Sugar Land, TX" → standardized form
    - "Houston-Pasadena-The Woodlands, TX" → same standardized form
    """
    if pd.isna(cbsa_str) or not cbsa_str:
        return None

    cbsa_lower = str(cbsa_str).lower().strip()

    # Extract primary city and state (before first comma)
    parts = cbsa_lower.split(',')
    if len(parts) < 2:
        return cbsa_lower

    metro_part = parts[0].strip()  # e.g., "houston-the woodlands-sugar land"
    state_part = parts[1].strip()   # e.g., "tx"

    # Extract primary city (first part before hyphen)
    primary_city = metro_part.split('-')[0].strip()

    # Return normalized form: "primary_city, state"
    return f"{primary_city}, {state_part}"

def main():
    client = get_client()

    print("=" * 80)
    print("🚀 Populating ZIPs from CSV Exports with Normalized CBSA Matching")
    print("=" * 80)

    # STEP 1: Load CSVs
    print("\n📦 STEP 1: Loading CSV files...")

    # Load Free Agents to get FreeWorld CBSAs
    agents_df = pd.read_csv('/Users/freeworld_james/Downloads/Free Agents-Employer Dashboard.csv')

    # Normalize Free Agents CBSAs
    freeworld_cbsas_raw = set(agents_df['cbsa'].dropna())
    freeworld_cbsas_normalized = {normalize_cbsa_for_matching(cbsa) for cbsa in freeworld_cbsas_raw if normalize_cbsa_for_matching(cbsa)}

    print(f"   Found {len(freeworld_cbsas_raw)} unique FreeWorld CBSAs from Free Agents")
    print(f"   Normalized to {len(freeworld_cbsas_normalized)} unique CBSA keys")

    # Load all ZIP data
    zip_df = pd.read_csv('/Users/freeworld_james/Downloads/Copy of ZIP Code Data and Mapping U.S. Locations - ZIP to State, Town, Metro.csv')
    print(f"   Loaded {len(zip_df)} total ZIP rows from ZIP Code Data CSV")

    # Normalize ZIP data CBSAs and filter to FreeWorld CBSAs
    zip_df['cbsa_normalized'] = zip_df['Metro (CBSA)'].apply(normalize_cbsa_for_matching)
    zip_df['cbsa_original'] = zip_df['Metro (CBSA)'].apply(normalize_location)

    freeworld_zip_df = zip_df[zip_df['cbsa_normalized'].isin(freeworld_cbsas_normalized)].copy()
    print(f"   Filtered to {len(freeworld_zip_df)} ZIPs in FreeWorld CBSAs (using normalized matching)")

    loc_df = pd.read_csv('/Users/freeworld_james/Downloads/location_markets_rows.csv')
    print(f"   Loaded {len(loc_df)} rows from location_markets_rows.csv")

    # STEP 2: Build city→market map from location_markets
    print("\n🗺️  STEP 2: Building city→market map...")

    city_to_markets = {}
    for _, row in loc_df[loc_df['location_type'] == 'city'].iterrows():
        city = normalize_location(row['location_string'])
        if city:
            # Parse markets JSON array
            try:
                markets = json.loads(row['markets'].replace("'", '"'))
                if markets:
                    city_to_markets[city] = markets
            except:
                pass

    print(f"   Built map for {len(city_to_markets)} cities")

    # STEP 3: Build CBSA→Cities map
    print("\n🗺️  STEP 3: Building CBSA→Cities map from ZIP data...")

    freeworld_zip_df['city_normalized'] = freeworld_zip_df['USPS Default City for ZIP'].apply(normalize_location)
    freeworld_zip_df['state_abbr'] = freeworld_zip_df['State'].apply(lambda x: STATE_ABBR_MAP.get(normalize_location(x), ''))
    freeworld_zip_df['city_state'] = freeworld_zip_df['city_normalized'] + ', ' + freeworld_zip_df['state_abbr']

    # Group cities by CBSA (normalized for matching)
    cbsa_to_cities = {}
    for _, row in freeworld_zip_df.iterrows():
        cbsa = row['cbsa_normalized']
        city_state = row['city_state']
        if cbsa and city_state:
            if cbsa not in cbsa_to_cities:
                cbsa_to_cities[cbsa] = set()
            cbsa_to_cities[cbsa].add(city_state)

    print(f"   Built map for {len(cbsa_to_cities)} CBSAs")

    # STEP 4: Map CBSA→Market using city bridge
    print("\n🌉 STEP 4: Mapping CBSA→Market using city bridge...")
    print("   Strategy: If ANY city in a CBSA matches a market, ALL ZIPs in that CBSA get that market")

    cbsa_to_market = {}
    for cbsa, cities in cbsa_to_cities.items():
        # Try to find ANY city in this CBSA that matches a market
        for city in cities:
            if city in city_to_markets:
                markets = city_to_markets[city]
                # Use primary market (first one)
                cbsa_to_market[cbsa] = markets[0]
                break

    print(f"   Mapped {len(cbsa_to_market)}/{len(cbsa_to_cities)} CBSAs to markets ({len(cbsa_to_market)/len(cbsa_to_cities)*100:.1f}%)")

    print(f"\n   Sample CBSA→Market:")
    for cbsa, market in list(cbsa_to_market.items())[:10]:
        cities_sample = list(cbsa_to_cities[cbsa])[:3]
        print(f"      {cbsa} → {market} (cities: {cities_sample})")

    # STEP 5: Prepare ZIP entries - ALL ZIPs in mapped CBSAs
    print("\n🔢 STEP 5: Preparing ZIP entries for ALL ZIPs in mapped CBSAs...")

    zip_entries = []
    for _, row in freeworld_zip_df.iterrows():
        zip_code = str(row['ZIP Code']).zfill(5)
        cbsa_norm = row['cbsa_normalized']  # Normalized for matching
        cbsa_orig = row['cbsa_original']     # Original for storage

        # Only include ZIPs whose CBSA mapped to a market
        if cbsa_norm in cbsa_to_market:
            market = cbsa_to_market[cbsa_norm]

            zip_entries.append({
                'location_string': zip_code,
                'location_type': 'zip',
                'cbsa': cbsa_orig,  # Store original CBSA name
                'markets': [market]  # Single market from CBSA mapping
            })

    print(f"   Prepared {len(zip_entries)} ZIP entries from {len(freeworld_zip_df)} total FreeWorld ZIPs")

    # STEP 6: Check existing ZIPs
    print("\n💾 STEP 6: Checking existing ZIPs...")

    existing_zips_result = client.table('location_markets').select('location_string').eq('location_type', 'zip').execute()
    existing_zips = {row['location_string'] for row in existing_zips_result.data}

    print(f"   Existing ZIPs in database: {len(existing_zips)}")

    # Filter to new ZIPs only
    new_zip_entries = [z for z in zip_entries if z['location_string'] not in existing_zips]

    print(f"   New ZIPs to insert: {len(new_zip_entries)}")

    # STEP 7: Bulk insert
    print("\n📝 STEP 7: Bulk inserting ZIPs...")

    if new_zip_entries:
        batch_size = 500
        total_inserted = 0

        for i in range(0, len(new_zip_entries), batch_size):
            batch = new_zip_entries[i:i+batch_size]
            try:
                client.table('location_markets').insert(batch).execute()
                total_inserted += len(batch)
                print(f"      Inserted {total_inserted}/{len(new_zip_entries)}...")
            except Exception as e:
                print(f"      ❌ Error inserting batch: {e}")

        print(f"   ✅ Inserted {total_inserted} new ZIPs")
    else:
        print(f"   No new ZIPs to insert")

    # STEP 8: Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)

    final_zips = client.table('location_markets').select('*', count='exact').eq('location_type', 'zip').execute()

    print(f"   Total ZIP entries in database: {final_zips.count}")
    print(f"   FreeWorld ZIPs in mapped CBSAs: {len(zip_entries)}/{len(freeworld_zip_df)} ({len(zip_entries)/len(freeworld_zip_df)*100:.1f}%)")
    print(f"   FreeWorld CBSAs (normalized): {len(freeworld_cbsas_normalized)}")
    print(f"   FreeWorld CBSAs mapped to markets: {len(cbsa_to_market)}/{len(cbsa_to_cities)} ({len(cbsa_to_market)/len(cbsa_to_cities)*100:.1f}%)")

    # Show major market verification
    print(f"\n   Major Market CBSA Verification:")
    major_markets = ['houston, tx', 'dallas, tx', 'phoenix, az', 'denver, co', 'las vegas, nv', 'san antonio, tx']
    for market_key in major_markets:
        if market_key in cbsa_to_market:
            print(f"      ✅ {market_key.title()} → {cbsa_to_market[market_key]}")
        else:
            print(f"      ❌ {market_key.title()} → NOT MAPPED")
    print()

if __name__ == "__main__":
    main()
