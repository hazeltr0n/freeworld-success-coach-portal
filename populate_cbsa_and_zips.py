#!/usr/bin/env python3
"""
Populate location_markets with CBSA data and comprehensive ZIP coverage

Uses two CSV files:
1. Free Agents-Employer Dashboard.csv - Maps agent UUIDs to CBSAs (defines FreeWorld markets)
2. ZIP Code Data and Mapping.csv - Maps ZIPs to CBSAs and cities

Workflow:
1. Extract unique CBSAs from Free Agents CSV (these are FreeWorld markets)
2. Map CBSA → FreeWorld Market name using existing market_mapper
3. Add 'cbsa' column to all city entries in location_markets
4. Load all ZIPs from ZIP data CSV
5. Filter ZIPs to only FreeWorld CBSAs
6. Insert/update ZIP entries with cbsa field
"""

import pandas as pd
from companies_rollup import get_client
from market_mapper import MarketMapper

def normalize_cbsa(cbsa_str):
    """Normalize CBSA string for matching (lowercase, strip)"""
    if pd.isna(cbsa_str) or not cbsa_str:
        return None
    return str(cbsa_str).lower().strip()

def main():
    client = get_client()
    mapper = MarketMapper()

    print("=" * 80)
    print("🚀 Populating CBSA Data and Comprehensive ZIP Coverage")
    print("=" * 80)

    # STEP 1: Load FreeWorld CBSAs from Free Agents CSV
    print("\n📍 STEP 1: Loading FreeWorld CBSAs from Free Agents...")
    agents_df = pd.read_csv('/Users/freeworld_james/Downloads/Free Agents-Employer Dashboard.csv')

    # Get unique CBSAs (excluding empty)
    freeworld_cbsas = set()
    for cbsa in agents_df['cbsa'].dropna():
        normalized = normalize_cbsa(cbsa)
        if normalized:
            freeworld_cbsas.add(normalized)

    print(f"   Found {len(freeworld_cbsas)} unique FreeWorld CBSAs")
    print(f"   Sample CBSAs: {list(freeworld_cbsas)[:5]}")

    # STEP 2: Map CBSA → Market using existing cities
    print("\n🗺️  STEP 2: Mapping CBSAs to FreeWorld Markets...")
    cbsa_to_market = {}

    for cbsa in freeworld_cbsas:
        # CBSA format is "City, ST" - same as our city format
        market = mapper.map_market(cbsa)
        if market:
            cbsa_to_market[cbsa] = market
        else:
            # Try without normalization for exact match
            market = mapper.map_market(cbsa.title())
            if market:
                cbsa_to_market[cbsa] = market

    print(f"   Mapped {len(cbsa_to_market)}/{len(freeworld_cbsas)} CBSAs to markets")

    # Show unmapped CBSAs
    unmapped = freeworld_cbsas - set(cbsa_to_market.keys())
    if unmapped:
        print(f"\n   ⚠️  Unmapped CBSAs ({len(unmapped)}):")
        for cbsa in sorted(unmapped)[:10]:
            print(f"      - {cbsa}")

    # STEP 3: Add CBSA column to existing city entries
    print("\n📝 STEP 3: Adding CBSA column to city entries...")

    # First, check if cbsa column exists
    result = client.table('location_markets').select('*').eq('location_type', 'city').limit(1).execute()
    if result.data and 'cbsa' not in result.data[0]:
        print("   Note: 'cbsa' column doesn't exist in schema - will be added on first update")

    # Get all cities
    cities = client.table('location_markets').select('*').eq('location_type', 'city').execute()
    cities_data = cities.data

    updated_cities = 0
    for city in cities_data:
        city_name = city['location_string']
        markets = city.get('markets', [])

        # Try to find matching CBSA
        city_cbsa = None
        for cbsa, market in cbsa_to_market.items():
            if market in markets:
                city_cbsa = cbsa
                break

        if city_cbsa:
            # Update city with CBSA
            try:
                client.table('location_markets').update({
                    'cbsa': city_cbsa
                }).eq('location_string', city_name).eq('location_type', 'city').execute()
                updated_cities += 1

                if updated_cities % 100 == 0:
                    print(f"      Updated {updated_cities} cities...")
            except Exception as e:
                print(f"      ❌ Error updating {city_name}: {e}")

    print(f"   ✅ Updated {updated_cities} cities with CBSA data")

    # STEP 4: Load ZIP data and filter to FreeWorld CBSAs
    print("\n📦 STEP 4: Loading ZIP Code data...")
    zip_df = pd.read_csv('/Users/freeworld_james/Downloads/Copy of ZIP Code Data and Mapping U.S. Locations - ZIP to State, Town, Metro.csv')

    print(f"   Total ZIPs in file: {len(zip_df)}")

    # Normalize CBSA column
    zip_df['cbsa_normalized'] = zip_df['Metro (CBSA)'].apply(normalize_cbsa)

    # Filter to only FreeWorld CBSAs
    freeworld_zips = zip_df[zip_df['cbsa_normalized'].isin(freeworld_cbsas)].copy()

    print(f"   ZIPs in FreeWorld CBSAs: {len(freeworld_zips)}")

    # STEP 5: Prepare ZIP entries for insertion
    print("\n🔢 STEP 5: Preparing ZIP entries...")

    zip_entries = []
    for _, row in freeworld_zips.iterrows():
        zip_code = str(row['ZIP Code']).zfill(5)  # Ensure 5-digit format
        cbsa = row['cbsa_normalized']

        # Get market for this CBSA
        market = cbsa_to_market.get(cbsa)
        if not market:
            continue

        zip_entries.append({
            'location_string': zip_code,
            'location_type': 'zip',
            'cbsa': cbsa,
            'markets': [market]
        })

    print(f"   Prepared {len(zip_entries)} ZIP entries")

    # STEP 6: Check existing ZIPs and insert new ones
    print("\n💾 STEP 6: Inserting ZIP entries...")

    existing_zips = client.table('location_markets').select('location_string').eq('location_type', 'zip').execute()
    existing_zip_set = {row['location_string'] for row in existing_zips.data}

    print(f"   Existing ZIP entries: {len(existing_zip_set)}")

    # Filter to only new ZIPs
    new_zip_entries = [z for z in zip_entries if z['location_string'] not in existing_zip_set]

    print(f"   New ZIP entries to insert: {len(new_zip_entries)}")

    # Insert in batches
    batch_size = 100
    total_inserted = 0

    for i in range(0, len(new_zip_entries), batch_size):
        batch = new_zip_entries[i:i+batch_size]
        try:
            client.table('location_markets').insert(batch).execute()
            total_inserted += len(batch)
            if total_inserted % 1000 == 0:
                print(f"      Inserted {total_inserted}/{len(new_zip_entries)}...")
        except Exception as e:
            print(f"      ❌ Error inserting batch: {e}")

    print(f"   ✅ Inserted {total_inserted} new ZIP entries")

    # STEP 7: Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)

    final_cities = client.table('location_markets').select('*', count='exact').eq('location_type', 'city').execute()
    final_zips = client.table('location_markets').select('*', count='exact').eq('location_type', 'zip').execute()

    print(f"   Total city entries: {final_cities.count}")
    print(f"   Total ZIP entries: {final_zips.count}")
    print(f"   FreeWorld CBSAs: {len(freeworld_cbsas)}")
    print(f"   CBSAs mapped to markets: {len(cbsa_to_market)}")
    print()

if __name__ == "__main__":
    main()
