#!/usr/bin/env python3
"""
ULTRA FAST ZIP population using pgeocode
Downloads US ZIP database once, then instant local lookups
"""

from companies_rollup import get_client
import pgeocode
import pandas as pd

def ultra_fast_populate():
    """Populate ALL ZIPs instantly using pgeocode"""

    print("📥 Loading US ZIP database...")
    nomi = pgeocode.Nominatim('us')
    print("✅ ZIP database loaded")

    client = get_client()
    if not client:
        print("❌ No Supabase client")
        return

    print("\n📊 Fetching locations from location_markets...")
    result = client.table('location_markets').select('id, location_string, location_type, default_zips').execute()

    locations = result.data
    print(f"✅ Found {len(locations)} locations")

    # Filter cities without ZIPs
    to_update = [loc for loc in locations if loc['location_type'] == 'city' and not loc.get('default_zips')]
    print(f"📍 Populating {len(to_update)} cities...")

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

        # Query pgeocode database for this city/state
        query_result = nomi.query_location(city, state)

        if not query_result.empty:
            # Get postal_code from result
            zip_code = str(int(query_result['postal_code'].iloc[0])) if pd.notna(query_result['postal_code'].iloc[0]) else None

            if zip_code:
                # Update location_markets
                client.table('location_markets').update({
                    'default_zips': [zip_code]
                }).eq('id', loc['id']).execute()

                updated_count += 1
                continue

        failed_count += 1

    print(f"\n✅ Updated {updated_count} locations")
    print(f"⚠️  Failed: {failed_count}")

    # Now backfill jobs
    print("\n📊 Backfilling jobs...")
    jobs_result = client.table('jobs').select('job_id, location').is_('zip_code', 'null').execute()
    jobs = jobs_result.data
    print(f"✅ Found {len(jobs)} jobs without ZIPs")

    # Get location_markets for lookup
    locs_result = client.table('location_markets').select('location_string, default_zips').execute()
    location_map = {loc['location_string'].lower(): loc.get('default_zips', []) for loc in locs_result.data}

    to_update_jobs = []

    for job in jobs:
        location = job.get('location', '')

        if ',' in location:
            parts = location.split(',')
            city = parts[0].strip()
            state_part = parts[1].strip()
            state = state_part[:2].upper()

            lookup_key = f"{city}, {state}".lower()

            if lookup_key in location_map and location_map[lookup_key]:
                to_update_jobs.append({
                    'job_id': job['job_id'],
                    'zip_code': location_map[lookup_key][0]
                })

    print(f"📍 Updating {len(to_update_jobs)} jobs...")

    # Batch update
    batch_size = 100
    updated = 0

    for i in range(0, len(to_update_jobs), batch_size):
        batch = to_update_jobs[i:i+batch_size]

        for record in batch:
            client.table('jobs').update({'zip_code': record['zip_code']}).eq('job_id', record['job_id']).execute()
            updated += 1

        print(f"   ✓ Batch {i//batch_size + 1}/{(len(to_update_jobs)-1)//batch_size + 1}")

    print(f"\n✅ Updated {updated} jobs!")

    # Final stats
    result = client.table('jobs').select('zip_code').execute()
    total = len(result.data)
    with_zip = sum(1 for j in result.data if j.get('zip_code'))

    print(f"\n📊 FINAL STATS:")
    print(f"   Total jobs: {total:,}")
    print(f"   With ZIPs: {with_zip:,} ({with_zip/total*100:.1f}%)")
    print(f"   Without ZIPs: {total - with_zip:,}")

if __name__ == "__main__":
    ultra_fast_populate()
