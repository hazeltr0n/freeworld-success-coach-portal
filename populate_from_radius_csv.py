#!/usr/bin/env python3
"""
Populate location_markets with ZIPs from radius search CSV
This gives us comprehensive 60-mile radius coverage for all markets
"""

import pandas as pd
from companies_rollup import get_client

def main():
    client = get_client()

    print("=" * 80)
    print("🎯 Populating ZIPs from Radius Search CSV")
    print("=" * 80)

    # Load the radius CSV
    print("\n📦 Loading radius search CSV...")
    df = pd.read_csv('/Users/freeworld_james/Downloads/market search radius.csv')
    print(f"   Loaded {len(df)} markets")

    # Check existing ZIPs
    print("\n🔍 Checking existing ZIPs in location_markets...")
    existing_result = client.table('location_markets').select('location_string').eq('location_type', 'zip').execute()
    existing_zips = {row['location_string'] for row in existing_result.data}
    print(f"   Existing ZIPs: {len(existing_zips)}")

    # Prepare ZIP entries
    print("\n📝 Preparing ZIP entries from radius data...")
    all_zip_entries = []
    total_zips_in_csv = 0

    for _, row in df.iterrows():
        market = row['Market']
        zip_list_str = row['All zip codes']

        # Parse comma-separated ZIP list
        zip_codes = [z.strip() for z in str(zip_list_str).split(',')]
        total_zips_in_csv += len(zip_codes)

        for zip_code in zip_codes:
            # Ensure 5-digit format
            zip_code = zip_code.zfill(5)

            # Skip if already exists
            if zip_code in existing_zips:
                continue

            all_zip_entries.append({
                'location_string': zip_code,
                'location_type': 'zip',
                'markets': [market]
            })

    print(f"   Total ZIPs in CSV: {total_zips_in_csv}")
    print(f"   New ZIPs to insert: {len(all_zip_entries)}")

    # Bulk insert in batches
    if all_zip_entries:
        print("\n💾 Bulk inserting new ZIPs...")
        batch_size = 500
        total_inserted = 0

        for i in range(0, len(all_zip_entries), batch_size):
            batch = all_zip_entries[i:i+batch_size]
            try:
                client.table('location_markets').insert(batch).execute()
                total_inserted += len(batch)
                print(f"      Inserted {total_inserted}/{len(all_zip_entries)}...")
            except Exception as e:
                print(f"      ❌ Error inserting batch: {e}")

        print(f"   ✅ Inserted {total_inserted} new ZIPs")
    else:
        print("   No new ZIPs to insert")

    # Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)

    final_result = client.table('location_markets').select('*', count='exact').eq('location_type', 'zip').execute()
    print(f"   Total ZIPs in location_markets: {final_result.count}")
    print(f"   Markets covered: {len(df)}")
    print()

if __name__ == "__main__":
    main()
