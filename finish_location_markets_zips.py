#!/usr/bin/env python3
"""
Finish populating default_zips for location_markets table

Uses zippopotam.us API to get ZIP codes for cities
"""

import requests
import time
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


def populate_location_zips():
    """Populate default_zips for all locations without them"""
    client = get_client()

    # Get locations without default_zips
    print("🔍 Finding locations without ZIP codes...")
    result = client.table('location_markets').select('id, location_string, location_type').is_('default_zips', 'null').execute()
    locations = result.data

    print(f"📋 Found {len(locations):,} locations without ZIPs\n")

    if not locations:
        print("✅ All locations already have ZIPs!")
        return

    updated = 0
    failed = 0
    skipped = 0

    for i, loc in enumerate(locations):
        location_string = loc['location_string']
        location_type = loc['location_type']

        # Only process city type
        if location_type != 'city':
            skipped += 1
            continue

        # Parse "city, st" format
        if ',' not in location_string:
            skipped += 1
            continue

        city, state = location_string.split(',', 1)
        city = city.strip()
        state = state.strip()[:2].upper()

        try:
            url = f"https://api.zippopotam.us/us/{state}/{city.replace(' ', '%20')}"
            response = requests.get(url, timeout=3)

            if response.status_code == 200:
                data = response.json()
                places = data.get('places', [])

                if places:
                    # Get all ZIP codes for this city
                    zips = [place.get('post code', '') for place in places]
                    zips = [z for z in zips if z]  # Remove empty strings

                    if zips:
                        # Update location_markets table
                        client.table('location_markets').update({
                            'default_zips': zips
                        }).eq('id', loc['id']).execute()

                        updated += 1

                        if updated % 50 == 0:
                            print(f"✅ Progress: {updated} updated, {failed} failed, {skipped} skipped ({i+1}/{len(locations)})")
                    else:
                        failed += 1
                else:
                    failed += 1
            else:
                failed += 1

            # Rate limiting (10 req/sec max)
            time.sleep(0.11)

        except Exception as e:
            failed += 1
            if failed % 100 == 0:
                print(f"⚠️  {failed} failures so far...")

    print(f"\n📊 Final Results:")
    print(f"   ✅ Updated: {updated:,}")
    print(f"   ❌ Failed: {failed:,}")
    print(f"   ⏭️  Skipped: {skipped:,}")

    # Final check
    result = client.table('location_markets').select('id, default_zips').execute()
    total = len(result.data)
    with_zips = sum(1 for row in result.data if row.get('default_zips'))

    print(f"\n📍 Location Markets Coverage:")
    print(f"   Total: {total:,}")
    print(f"   With ZIPs: {with_zips:,} ({with_zips/total*100:.1f}%)")
    print(f"   Without ZIPs: {total - with_zips:,} ({(total-with_zips)/total*100:.1f}%)")


if __name__ == "__main__":
    print("🚀 Starting location_markets ZIP population...\n")
    populate_location_zips()
    print("\n✅ Complete!")
