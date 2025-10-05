#!/usr/bin/env python3
"""
FAST ZIP population using uszipcode's built-in database
No API calls - instant lookups from local SQLite database
"""

from companies_rollup import get_client
from uszipcode import SearchEngine

def fast_populate_location_markets():
    """Populate default_zips using local uszipcode database"""

    search = SearchEngine()
    client = get_client()

    if not client:
        print("❌ No Supabase client")
        return

    print("📊 Fetching locations from location_markets...")
    result = client.table('location_markets').select('id, location_string, location_type, default_zips').execute()

    locations = result.data
    print(f"✅ Found {len(locations)} locations")

    # Filter cities without ZIPs
    to_update = [loc for loc in locations if loc['location_type'] == 'city' and not loc.get('default_zips')]
    print(f"📍 Need to populate {len(to_update)} cities")

    updated_count = 0
    failed_count = 0

    for i, loc in enumerate(to_update):
        if (i + 1) % 100 == 0:
            print(f"   Processed {i + 1}/{len(to_update)}...")

        location_string = loc['location_string']  # "city, st"

        if ',' not in location_string:
            failed_count += 1
            continue

        parts = location_string.split(',')
        city = parts[0].strip()
        state = parts[1].strip()

        # Local database lookup - INSTANT!
        results = search.by_city_and_state(city, state)

        if results:
            # Get all ZIPs for this city
            zips = [str(r.zipcode) for r in results if r.zipcode]

            if zips:
                # Update location_markets
                client.table('location_markets').update({
                    'default_zips': zips
                }).eq('id', loc['id']).execute()

                updated_count += 1
                continue

        failed_count += 1

    print(f"\n✅ Updated {updated_count} locations")
    print(f"⚠️  Failed: {failed_count}")

    # Show sample
    result = client.table('location_markets').select('location_string, default_zips').not_.is_('default_zips', 'null').limit(10).execute()
    print(f"\n📋 Sample:")
    for loc in result.data:
        print(f"   {loc['location_string']}: {loc['default_zips'][:3]}...")  # Show first 3 ZIPs

def fast_backfill_jobs():
    """Backfill jobs using location_markets table"""

    client = get_client()

    if not client:
        print("❌ No Supabase client")
        return

    print("\n📊 Fetching jobs without ZIPs...")
    result = client.table('jobs').select('job_id, location').is_('zip_code', 'null').execute()

    jobs = result.data
    print(f"✅ Found {len(jobs)} jobs without ZIPs")

    # Get all location_markets for fast lookup
    locs_result = client.table('location_markets').select('location_string, default_zips').execute()
    location_map = {loc['location_string'].lower(): loc.get('default_zips', []) for loc in locs_result.data}

    to_update = []

    for job in jobs:
        location = job.get('location', '')

        # Try to match location to location_markets
        if ',' in location:
            parts = location.split(',')
            city = parts[0].strip()
            state = parts[1].strip()[:2].upper()

            lookup_key = f"{city}, {state}".lower()

            if lookup_key in location_map and location_map[lookup_key]:
                zip_code = location_map[lookup_key][0]  # Use first ZIP
                to_update.append({
                    'job_id': job['job_id'],
                    'zip_code': zip_code
                })

    print(f"📍 Can update {len(to_update)} jobs with ZIPs")

    # Batch update
    batch_size = 100
    updated = 0

    for i in range(0, len(to_update), batch_size):
        batch = to_update[i:i+batch_size]

        for record in batch:
            client.table('jobs').update({'zip_code': record['zip_code']}).eq('job_id', record['job_id']).execute()
            updated += 1

        print(f"   ✓ Updated batch {i//batch_size + 1}/{(len(to_update)-1)//batch_size + 1}")

    print(f"\n✅ Updated {updated} jobs!")

if __name__ == "__main__":
    print("🚀 FAST ZIP Population\n")
    fast_populate_location_markets()
    fast_backfill_jobs()

    # Final stats
    client = get_client()
    result = client.table('jobs').select('zip_code').execute()
    total = len(result.data)
    with_zip = sum(1 for j in result.data if j.get('zip_code'))

    print(f"\n📊 Final Stats:")
    print(f"   Total jobs: {total:,}")
    print(f"   With ZIPs: {with_zip:,} ({with_zip/total*100:.1f}%)")
