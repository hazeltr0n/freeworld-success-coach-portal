#!/usr/bin/env python3
"""
Populate location_markets with ZIP code entries

Takes existing city entries that have default_zips populated
and creates separate location_type='zip' entries for each ZIP
with the same markets as the parent city.

This enables direct ZIP→Market lookups for DriverPulse jobs.
"""

from companies_rollup import get_client

def main():
    client = get_client()

    print("🚀 Populating ZIP entries in location_markets...")

    # Get all city entries that have ZIPs
    print("\n📍 Loading cities with ZIP codes...")
    result = client.table('location_markets').select('*').eq('location_type', 'city').execute()
    cities = result.data

    cities_with_zips = [c for c in cities if c.get('default_zips')]
    print(f"   Found {len(cities_with_zips)} cities with ZIP codes")

    # Extract all ZIP→Market mappings
    zip_market_map = {}
    for city in cities_with_zips:
        city_name = city['location_string']
        markets = city['markets']
        zips = city.get('default_zips', [])

        for zip_code in zips:
            if zip_code not in zip_market_map:
                zip_market_map[zip_code] = set()
            zip_market_map[zip_code].update(markets)

    print(f"\n📊 Extracted {len(zip_market_map)} unique ZIP codes")

    # Check which ZIPs already exist
    print("\n🔍 Checking existing ZIP entries...")
    existing_result = client.table('location_markets').select('location_string').eq('location_type', 'zip').execute()
    existing_zips = {row['location_string'] for row in existing_result.data}
    print(f"   Already have {len(existing_zips)} ZIP entries")

    # Prepare new ZIP entries
    new_zips = []
    for zip_code, markets in zip_market_map.items():
        if zip_code not in existing_zips:
            new_zips.append({
                'location_string': zip_code,
                'location_type': 'zip',
                'markets': list(markets)
            })

    print(f"\n✅ Need to create {len(new_zips)} new ZIP entries")

    if not new_zips:
        print("   Nothing to do!")
        return

    # Insert in batches of 100
    print("\n📝 Inserting ZIP entries...")
    batch_size = 100
    total_inserted = 0

    for i in range(0, len(new_zips), batch_size):
        batch = new_zips[i:i+batch_size]
        try:
            client.table('location_markets').insert(batch).execute()
            total_inserted += len(batch)
            if total_inserted % 500 == 0:
                print(f"   Progress: {total_inserted}/{len(new_zips)}")
        except Exception as e:
            print(f"   ❌ Error inserting batch {i//batch_size + 1}: {e}")

    print(f"\n🎉 Successfully inserted {total_inserted} ZIP entries!")

    # Final count
    final_result = client.table('location_markets').select('*', count='exact').eq('location_type', 'zip').execute()
    print(f"\n📊 Final Stats:")
    print(f"   Total ZIP entries: {final_result.count}")
    print(f"   Total city entries: {len(cities)}")
    print(f"   Coverage: ZIP codes for {len(cities_with_zips)} cities")

if __name__ == "__main__":
    main()
