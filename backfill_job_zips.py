#!/usr/bin/env python3
"""
Backfill ZIP codes for existing jobs using location_markets table

Strategy:
1. Get all jobs without ZIP codes
2. Look up their location in location_markets table
3. Use first default_zip from location_markets
4. Update jobs table in batches
"""

import sys
from supabase import create_client

def get_client():
    """Get Supabase client from secrets"""
    with open('.streamlit/secrets.toml', 'r') as f:
        secrets = {}
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                secrets[key.strip()] = value.strip().strip('"')

    return create_client(secrets['SUPABASE_URL'], secrets['SUPABASE_ANON_KEY'])


def backfill_zips_from_location_markets():
    """Backfill ZIPs using location_markets table"""
    client = get_client()

    print("🔍 Getting jobs without ZIP codes...")
    jobs_result = client.table('jobs').select('job_id, location').is_('zip_code', 'null').execute()
    jobs_without_zip = jobs_result.data

    print(f"📋 Found {len(jobs_without_zip):,} jobs without ZIP codes")

    # Get location_markets data
    print("🗺️  Loading location_markets table...")
    markets_result = client.table('location_markets').select('location_string, default_zips').execute()

    # Build lookup map: location -> [zips]
    location_map = {}
    for row in markets_result.data:
        location = row['location_string'].lower().strip()
        zips = row.get('default_zips', [])
        if zips:
            location_map[location] = zips

    print(f"📍 Loaded {len(location_map):,} location→ZIP mappings")

    # Prepare updates
    updates = []
    no_match = []

    for job in jobs_without_zip:
        location = job.get('location', '').lower().strip()

        if location in location_map:
            zip_code = location_map[location][0]  # Use first ZIP
            updates.append({
                'job_id': job['job_id'],
                'zip_code': zip_code
            })
        else:
            no_match.append(job['job_id'])

    print(f"✅ Can update {len(updates):,} jobs")
    print(f"❌ No match for {len(no_match):,} jobs")

    if not updates:
        print("Nothing to update!")
        return

    # Update in batches
    batch_size = 100
    total_updated = 0

    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]

        for record in batch:
            try:
                client.table('jobs').update({'zip_code': record['zip_code']}).eq('job_id', record['job_id']).execute()
                total_updated += 1
            except Exception as e:
                print(f"⚠️  Error updating {record['job_id']}: {e}")

        if (i + batch_size) % 500 == 0:
            print(f"   Progress: {i + batch_size}/{len(updates)} ({(i+batch_size)/len(updates)*100:.1f}%)")

    print(f"\n✅ Updated {total_updated:,} jobs with ZIP codes")

    # Final check
    print("\n📊 Final ZIP Coverage:")
    result = client.table('jobs').select('zip_code').execute()
    total = len(result.data)
    with_zip = sum(1 for j in result.data if j.get('zip_code'))
    print(f"   Total: {total:,}")
    print(f"   With ZIP: {with_zip:,} ({with_zip/total*100:.1f}%)")
    print(f"   Without ZIP: {total - with_zip:,} ({(total-with_zip)/total*100:.1f}%)")


def backfill_remaining_with_api():
    """Backfill remaining jobs using zippopotam.us API"""
    import requests
    import time

    client = get_client()

    print("\n🌐 Backfilling remaining jobs with API...")
    jobs_result = client.table('jobs').select('job_id, location').is_('zip_code', 'null').execute()
    jobs_without_zip = jobs_result.data

    print(f"📋 Found {len(jobs_without_zip):,} jobs still without ZIP codes")

    if not jobs_without_zip:
        print("✅ All jobs have ZIP codes!")
        return

    updated = 0
    failed = 0

    for i, job in enumerate(jobs_without_zip):
        location = job.get('location', '').strip()

        # Parse "City, ST" format
        if ',' in location:
            city, state = location.split(',', 1)
            city = city.strip()
            state = state.strip()[:2]  # First 2 chars

            try:
                url = f"https://api.zippopotam.us/us/{state}/{city.replace(' ', '%20')}"
                response = requests.get(url, timeout=3)

                if response.status_code == 200:
                    data = response.json()
                    if 'places' in data and len(data['places']) > 0:
                        zip_code = data['places'][0].get('post code', '')

                        if zip_code:
                            client.table('jobs').update({'zip_code': zip_code}).eq('job_id', job['job_id']).execute()
                            updated += 1

                            if updated % 100 == 0:
                                print(f"   Progress: {updated} updated, {failed} failed")
                else:
                    failed += 1

                # Rate limiting
                time.sleep(0.1)

            except Exception as e:
                failed += 1
                if failed % 100 == 0:
                    print(f"   ⚠️  {failed} failures so far")
        else:
            failed += 1

    print(f"\n✅ API backfill complete:")
    print(f"   Updated: {updated:,}")
    print(f"   Failed: {failed:,}")


if __name__ == "__main__":
    print("🚀 Starting ZIP code backfill...\n")

    # Step 1: Use location_markets table (fast)
    backfill_zips_from_location_markets()

    # Step 2: Ask about API backfill
    remaining = input("\n❓ Run API backfill for remaining jobs? (y/n): ")
    if remaining.lower() == 'y':
        backfill_remaining_with_api()

    print("\n✅ Backfill complete!")
