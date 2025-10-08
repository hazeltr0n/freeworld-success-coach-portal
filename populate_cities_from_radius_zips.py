#!/usr/bin/env python3
"""
Map cities to markets using the radius-based ZIP codes
This creates comprehensive city→market mappings based on our 60-mile radius ZIPs
"""

import pandas as pd
from companies_rollup import get_client

def normalize_location(s):
    """Normalize location strings for matching"""
    if pd.isna(s) or not s:
        return None
    return str(s).lower().strip()

def main():
    client = get_client()

    print("=" * 80)
    print("🏙️  Mapping Cities from Radius ZIPs")
    print("=" * 80)

    # Load the radius CSV to get all market→ZIP assignments
    print("\n📦 Loading radius search CSV...")
    radius_df = pd.read_csv('/Users/freeworld_james/Downloads/market search radius.csv')
    print(f"   Loaded {len(radius_df)} markets")

    # Build market→ZIPs map
    market_to_zips = {}
    total_zips = 0
    for _, row in radius_df.iterrows():
        market = row['Market']
        zip_list_str = row['All zip codes']
        zip_codes = [z.strip().zfill(5) for z in str(zip_list_str).split(',')]
        market_to_zips[market] = set(zip_codes)
        total_zips += len(zip_codes)

    print(f"   Total ZIPs across all markets: {total_zips}")

    # Load ZIP Code Data CSV to get ZIP→City mappings
    print("\n📍 Loading ZIP Code Data CSV...")
    zip_data_df = pd.read_csv('/Users/freeworld_james/Downloads/Copy of ZIP Code Data and Mapping U.S. Locations - ZIP to State, Town, Metro.csv')
    print(f"   Loaded {len(zip_data_df)} ZIPs with city data")

    # Normalize and prepare ZIP→City map
    zip_data_df['zip_normalized'] = zip_data_df['ZIP Code'].apply(lambda x: str(x).zfill(5) if pd.notna(x) else None)
    zip_data_df['city_normalized'] = zip_data_df['USPS Default City for ZIP'].apply(normalize_location)
    zip_data_df['state_normalized'] = zip_data_df['USPS Default State for ZIP'].apply(normalize_location)

    # Create ZIP→City/State map
    zip_to_city_state = {}
    for _, row in zip_data_df.iterrows():
        zip_code = row['zip_normalized']
        city = row['city_normalized']
        state = row['state_normalized']
        if zip_code and city and state:
            zip_to_city_state[zip_code] = f"{city}, {state}"

    print(f"   Built mapping for {len(zip_to_city_state)} ZIPs→Cities")

    # Check existing city entries in location_markets
    print("\n🔍 Checking existing cities in location_markets...")
    existing_result = client.table('location_markets').select('location_string').eq('location_type', 'city').execute()
    existing_cities = {row['location_string'] for row in existing_result.data}
    print(f"   Existing cities: {len(existing_cities)}")

    # Map cities to markets based on radius ZIPs
    print("\n🗺️  Mapping cities to markets...")
    city_to_markets = {}  # city_state → [markets]

    for market, zips in market_to_zips.items():
        for zip_code in zips:
            if zip_code in zip_to_city_state:
                city_state = zip_to_city_state[zip_code]
                if city_state not in city_to_markets:
                    city_to_markets[city_state] = set()
                city_to_markets[city_state].add(market)

    print(f"   Found {len(city_to_markets)} unique cities across all markets")

    # Prepare city entries for insertion
    print("\n📝 Preparing city entries...")
    city_entries = []
    new_cities = 0

    for city_state, markets in city_to_markets.items():
        # Skip if already exists
        if city_state in existing_cities:
            continue

        city_entries.append({
            'location_string': city_state,
            'location_type': 'city',
            'markets': list(markets)
        })
        new_cities += 1

    print(f"   New cities to insert: {new_cities}")

    # Show sample by market
    print("\n📊 Sample cities by market:")
    multi_market_cities = []
    for market in sorted(market_to_zips.keys()):
        market_cities = [city for city, mkts in city_to_markets.items() if market in mkts]
        print(f"   {market}: {len(market_cities)} cities")
        # Show first 3 as examples
        for city in sorted(market_cities)[:3]:
            markets_for_city = city_to_markets[city]
            if len(markets_for_city) > 1:
                print(f"      - {city.title()} → {sorted(markets_for_city)}")
                multi_market_cities.append((city, markets_for_city))
            else:
                print(f"      - {city.title()}")

    # Show all multi-market cities
    if multi_market_cities:
        print(f"\n🔀 Cities mapped to multiple markets ({len(multi_market_cities)} total):")
        for city, markets in sorted(multi_market_cities, key=lambda x: len(x[1]), reverse=True):
            print(f"   {city.title()} → {sorted(markets)}")

    # Bulk insert in batches
    if city_entries:
        print("\n💾 Bulk inserting new cities...")
        batch_size = 500
        total_inserted = 0

        for i in range(0, len(city_entries), batch_size):
            batch = city_entries[i:i+batch_size]
            try:
                client.table('location_markets').insert(batch).execute()
                total_inserted += len(batch)
                print(f"      Inserted {total_inserted}/{len(city_entries)}...")
            except Exception as e:
                print(f"      ❌ Error inserting batch: {e}")

        print(f"   ✅ Inserted {total_inserted} new cities")
    else:
        print("   No new cities to insert")

    # Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)

    final_city_result = client.table('location_markets').select('*', count='exact').eq('location_type', 'city').execute()
    final_zip_result = client.table('location_markets').select('*', count='exact').eq('location_type', 'zip').execute()

    print(f"   Total cities in location_markets: {final_city_result.count}")
    print(f"   Total ZIPs in location_markets: {final_zip_result.count}")
    print(f"   Markets covered: {len(market_to_zips)}")
    print()

if __name__ == "__main__":
    main()
