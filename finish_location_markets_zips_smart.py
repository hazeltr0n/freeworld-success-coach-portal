#!/usr/bin/env python3
"""
Smart ZIP code population with fallback strategies for edge cases
"""

import requests
import time
from supabase import create_client

# Market center ZIPs as fallback for unmatched locations (from market search radius.csv)
MARKET_CENTER_ZIPS = {
    'dallas': ['75060'],
    'houston': ['77007'],
    'phoenix': ['85009'],
    'denver': ['80218'],
    'las vegas': ['89107'],
    'stockton': ['95205'],
    'bay area': ['94501'],
    'inland empire': ['92324'],
    'trenton': ['07017'],
    'newark': ['08638'],
    'sacramento': ['95814'],  # Not in CSV, using downtown
    'rochester': ['14604'],   # Not in CSV, using downtown
    'des moines': ['50309']   # Not in CSV, using downtown
}

def get_client():
    """Get Supabase client from secrets"""
    with open('.streamlit/secrets.toml', 'r') as f:
        secrets = {}
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                secrets[key.strip()] = value.strip().strip('"')
    return create_client(secrets['SUPABASE_URL'], secrets['SUPABASE_ANON_KEY'])


def clean_city_name(city: str) -> list:
    """Generate variations of city name to try"""
    variations = [city.strip()]

    # Remove "city of" prefix
    if city.lower().startswith('city of '):
        variations.append(city[8:].strip())

    # Remove township/borough suffixes
    for suffix in [' township', ' borough', ' town']:
        if city.lower().endswith(suffix):
            variations.append(city[:-len(suffix)].strip())

    # Try first part of hyphenated names
    if '-' in city:
        variations.append(city.split('-')[0].strip())

    return variations


def get_zips_for_city(city: str, state: str) -> list:
    """Try multiple variations to get ZIPs"""
    variations = clean_city_name(city)

    for variant in variations:
        try:
            url = f"https://api.zippopotam.us/us/{state}/{variant.replace(' ', '%20')}"
            response = requests.get(url, timeout=3)

            if response.status_code == 200:
                data = response.json()
                places = data.get('places', [])
                if places:
                    zips = [place.get('post code', '') for place in places]
                    zips = [z for z in zips if z]
                    if zips:
                        print(f"  ✅ '{city}' → '{variant}' found {len(zips)} ZIPs")
                        return zips
        except:
            pass

        time.sleep(0.05)  # Small delay between variations

    return []


def populate_missing_zips():
    """Populate ZIPs for locations that failed before"""
    client = get_client()

    # Get locations without ZIPs
    print("🔍 Finding locations without ZIP codes...")
    result = client.table('location_markets').select('id, location_string, location_type, markets').is_('default_zips', 'null').execute()
    locations = result.data

    print(f"📋 Found {len(locations):,} locations without ZIPs\n")

    if not locations:
        print("✅ All locations have ZIPs!")
        return

    updated = 0
    failed = 0
    skipped = 0
    fallback_used = 0

    for i, loc in enumerate(locations):
        location_string = loc['location_string']
        location_type = loc['location_type']
        markets = loc.get('markets', [])

        # Only process city type
        if location_type != 'city':
            skipped += 1
            continue

        # Parse "city, st"
        if ',' not in location_string:
            skipped += 1
            continue

        city, state = location_string.split(',', 1)
        city = city.strip()
        state = state.strip()[:2].upper()

        print(f"[{i+1}/{len(locations)}] {location_string}")

        zips = get_zips_for_city(city, state)

        # Fallback: Use market center ZIP
        if not zips and markets:
            for market in markets:
                market_key = market.lower()
                if market_key in MARKET_CENTER_ZIPS:
                    zips = MARKET_CENTER_ZIPS[market_key]
                    print(f"  🎯 Using {market} market center ZIP: {zips[0]}")
                    fallback_used += 1
                    break

        if zips:
            # Update database
            client.table('location_markets').update({
                'default_zips': zips
            }).eq('id', loc['id']).execute()
            updated += 1
        else:
            failed += 1
            print(f"  ❌ No ZIPs found (markets: {markets})")

        # Progress update
        if (i + 1) % 50 == 0:
            print(f"\n📊 Progress: {updated} updated, {failed} failed, {skipped} skipped, {fallback_used} fallbacks\n")

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
    print("🚀 Starting SMART location_markets ZIP population...\n")
    populate_missing_zips()
    print("\n✅ Complete!")
