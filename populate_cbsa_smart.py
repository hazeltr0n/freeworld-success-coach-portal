#!/usr/bin/env python3
"""
Smart CBSA Population using City→Market Bridge Strategy

Strategy:
1. Load unique FreeWorld CBSAs from Free Agents CSV
2. Load ZIP→City→CBSA mapping from ZIP data CSV
3. Build CBSA→Cities map
4. For each CBSA, find cities within it and map to markets using existing city→market map
5. Assign CBSA to market based on cities (city as bridge)
6. Insert all ZIPs from FreeWorld CBSAs with proper CBSA and market fields
"""

import pandas as pd
from companies_rollup import get_client
from market_mapper import MarketMapper

def normalize_cbsa(cbsa_str):
    """Normalize CBSA string for matching (lowercase, strip)"""
    if pd.isna(cbsa_str) or not cbsa_str:
        return None
    return str(cbsa_str).lower().strip()

def normalize_city(city_str):
    """Normalize city string for matching (lowercase, strip)"""
    if pd.isna(city_str) or not city_str:
        return None
    return str(city_str).lower().strip()

def main():
    client = get_client()
    mapper = MarketMapper()

    print("=" * 80)
    print("🚀 Smart CBSA Population using City→Market Bridge")
    print("=" * 80)

    # STEP 1: Load FreeWorld CBSAs from Free Agents CSV
    print("\n📍 STEP 1: Loading FreeWorld CBSAs...")
    agents_df = pd.read_csv('/Users/freeworld_james/Downloads/Free Agents-Employer Dashboard.csv')

    freeworld_cbsas = set()
    for cbsa in agents_df['cbsa'].dropna():
        normalized = normalize_cbsa(cbsa)
        if normalized:
            freeworld_cbsas.add(normalized)

    print(f"   Found {len(freeworld_cbsas)} unique FreeWorld CBSAs")

    # STEP 2: Load ZIP→City→CBSA mapping from ZIP data CSV
    print("\n📦 STEP 2: Loading ZIP data CSV...")
    zip_df = pd.read_csv('/Users/freeworld_james/Downloads/Copy of ZIP Code Data and Mapping U.S. Locations - ZIP to State, Town, Metro.csv')

    print(f"   Total rows: {len(zip_df)}")

    # Normalize CBSA and City columns
    zip_df['cbsa_normalized'] = zip_df['Metro (CBSA)'].apply(normalize_cbsa)
    zip_df['city_normalized'] = zip_df['USPS Default City for ZIP'].apply(normalize_city)

    # Filter to only FreeWorld CBSAs
    freeworld_zip_df = zip_df[zip_df['cbsa_normalized'].isin(freeworld_cbsas)].copy()

    print(f"   Rows in FreeWorld CBSAs: {len(freeworld_zip_df)}")

    # STEP 3: Build CBSA→Cities mapping
    print("\n🗺️  STEP 3: Building CBSA→Cities map...")
    cbsa_to_cities = {}

    for _, row in freeworld_zip_df.iterrows():
        cbsa = row['cbsa_normalized']
        city = row['city_normalized']
        state = row['State']

        if not cbsa or not city or not state:
            continue

        # Format: "city, st" (same as location_markets format)
        city_state = f"{city}, {state.lower()}"

        if cbsa not in cbsa_to_cities:
            cbsa_to_cities[cbsa] = set()
        cbsa_to_cities[cbsa].add(city_state)

    print(f"   Built map for {len(cbsa_to_cities)} CBSAs")
    print(f"   Sample CBSA→Cities:")
    for cbsa in list(cbsa_to_cities.keys())[:3]:
        cities = list(cbsa_to_cities[cbsa])[:5]
        print(f"      {cbsa}: {cities}")

    # STEP 4: Load existing city→market map from Supabase
    print("\n🏙️  STEP 4: Loading city→market map from Supabase...")
    cities_result = client.table('location_markets').select('location_string, markets').eq('location_type', 'city').execute()

    city_to_markets = {}
    for row in cities_result.data:
        city_str = row['location_string'].lower().strip()
        markets = row['markets']
        if markets:
            city_to_markets[city_str] = markets

    print(f"   Loaded {len(city_to_markets)} city→market mappings")

    # STEP 5: Map CBSA→Market using cities as bridge
    print("\n🌉 STEP 5: Mapping CBSA→Market using City Bridge...")
    cbsa_to_market = {}

    for cbsa, cities in cbsa_to_cities.items():
        # Try each city in this CBSA to find a market match
        for city in cities:
            if city in city_to_markets:
                markets = city_to_markets[city]
                # Use first market (primary market for this city)
                cbsa_to_market[cbsa] = markets[0]
                break

    print(f"   Mapped {len(cbsa_to_market)}/{len(cbsa_to_cities)} CBSAs to markets ({len(cbsa_to_market)/len(cbsa_to_cities)*100:.1f}%)")

    # Show mapping results
    print(f"\n   Sample CBSA→Market mappings:")
    for cbsa, market in list(cbsa_to_market.items())[:10]:
        print(f"      {cbsa} → {market}")

    # Show unmapped CBSAs
    unmapped = set(cbsa_to_cities.keys()) - set(cbsa_to_market.keys())
    if unmapped:
        print(f"\n   ⚠️  Unmapped CBSAs ({len(unmapped)}):")
        for cbsa in sorted(unmapped)[:10]:
            sample_cities = list(cbsa_to_cities[cbsa])[:3]
            print(f"      {cbsa} (cities: {sample_cities})")

    # STEP 6: Update city entries with CBSA
    print("\n📝 STEP 6: Updating city entries with CBSA...")
    print("   (Skipping for now - will do bulk updates later)")

    # NOTE: Individual updates are too slow (thousands of API calls)
    # TODO: Consider batch update approach or skip this step
    updated_cities = 0

    # STEP 7: Prepare ZIP entries
    print("\n🔢 STEP 7: Preparing ZIP entries...")

    zip_entries = []
    for _, row in freeworld_zip_df.iterrows():
        zip_code = str(row['ZIP Code']).zfill(5)
        cbsa = row['cbsa_normalized']

        # Get market for this CBSA
        market = cbsa_to_market.get(cbsa)
        if not market:
            # Skip ZIPs in unmapped CBSAs
            continue

        zip_entries.append({
            'location_string': zip_code,
            'location_type': 'zip',
            'cbsa': cbsa,
            'markets': [market]
        })

    print(f"   Prepared {len(zip_entries)} ZIP entries (from {len(freeworld_zip_df)} total in FreeWorld CBSAs)")

    # STEP 8: Insert ZIP entries
    print("\n💾 STEP 8: Inserting ZIP entries...")

    existing_zips = client.table('location_markets').select('location_string').eq('location_type', 'zip').execute()
    existing_zip_set = {row['location_string'] for row in existing_zips.data}

    print(f"   Existing ZIP entries: {len(existing_zip_set)}")

    # Filter to only new ZIPs
    new_zip_entries = [z for z in zip_entries if z['location_string'] not in existing_zip_set]

    print(f"   New ZIP entries to insert: {len(new_zip_entries)}")

    if new_zip_entries:
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
    else:
        print(f"   No new ZIPs to insert")

    # STEP 9: Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)

    final_cities = client.table('location_markets').select('*', count='exact').eq('location_type', 'city').execute()
    final_zips = client.table('location_markets').select('*', count='exact').eq('location_type', 'zip').execute()

    print(f"   FreeWorld CBSAs: {len(freeworld_cbsas)}")
    print(f"   CBSAs mapped to markets: {len(cbsa_to_market)} ({len(cbsa_to_market)/len(freeworld_cbsas)*100:.1f}%)")
    print(f"   Total city entries: {final_cities.count}")
    print(f"   Total ZIP entries: {final_zips.count}")
    print(f"   ZIPs in FreeWorld CBSAs: {len(freeworld_zip_df)}")
    print(f"   ZIPs with markets: {len(zip_entries)}")
    print()

if __name__ == "__main__":
    main()
