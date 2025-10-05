#!/usr/bin/env python3
"""
Auto-learn city→market mappings from scraped job data

Strategy:
1. Find new cities in jobs table that aren't in location_markets
2. Use ZIP code + radius to determine which market(s) they belong to
3. Add to location_markets table automatically
4. Run this as a cron job or after each scrape session
"""

import requests
from geopy.distance import geodesic
from supabase import create_client

# Market centers (from market search radius.csv)
MARKET_CENTERS = {
    'Dallas': ('75060', 75),
    'Houston': ('77007', 75),
    'Phoenix': ('85009', 75),
    'Denver': ('80218', 75),
    'Las Vegas': ('89107', 75),
    'Stockton': ('95205', 75),
    'Bay Area': ('94501', 75),
    'Inland Empire': ('92324', 75),
    'Trenton': ('07017', 50),
    'Newark': ('08638', 75),
    'Sacramento': ('95814', 75),
    'Rochester': ('14604', 75),
    'Des Moines': ('50309', 75)
}


def get_client():
    """Get Supabase client"""
    with open('.streamlit/secrets.toml', 'r') as f:
        secrets = {}
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                secrets[key.strip()] = value.strip().strip('"')
    return create_client(secrets['SUPABASE_URL'], secrets['SUPABASE_ANON_KEY'])


def get_zip_coordinates(zip_code: str):
    """Get lat/lng for ZIP"""
    try:
        zip_code = str(zip_code).strip().split('-')[0]
        if len(zip_code) != 5:
            return None

        url = f"https://api.zippopotam.us/us/{zip_code}"
        response = requests.get(url, timeout=3)

        if response.status_code == 200:
            data = response.json()
            if 'places' in data and len(data['places']) > 0:
                place = data['places'][0]
                return (float(place['latitude']), float(place['longitude']))
    except:
        pass
    return None


def determine_markets_for_location(location_string: str, job_zip: str = None):
    """Determine which market(s) a location belongs to

    Uses ZIP code proximity to market centers
    """
    if not job_zip:
        return []

    job_coords = get_zip_coordinates(job_zip)
    if not job_coords:
        return []

    matching_markets = []

    for market_name, (market_zip, radius_miles) in MARKET_CENTERS.items():
        market_coords = get_zip_coordinates(market_zip)
        if market_coords:
            try:
                distance = geodesic(job_coords, market_coords).miles
                if distance <= radius_miles:
                    matching_markets.append(market_name)
            except:
                pass

    return matching_markets


def discover_new_cities():
    """Find cities in jobs that aren't in location_markets yet"""
    client = get_client()

    print("🔍 Finding new cities from jobs table...\n")

    # Get all unique location+ZIP combinations from jobs
    jobs_result = client.table('jobs').select('location, zip_code').execute()

    # Get existing locations from location_markets
    markets_result = client.table('location_markets').select('location_string').execute()
    existing_locations = set(row['location_string'].lower().strip() for row in markets_result.data)

    print(f"📊 Existing locations in location_markets: {len(existing_locations)}")

    # Find new locations
    new_locations = {}
    for job in jobs_result.data:
        location = job.get('location', '').lower().strip()
        zip_code = job.get('zip_code', '')

        if location and location not in existing_locations and location not in new_locations:
            new_locations[location] = zip_code

    print(f"🆕 Found {len(new_locations)} NEW locations from jobs\n")

    if not new_locations:
        print("✅ No new locations to add!")
        return

    # Determine markets for each new location
    added = 0
    failed = 0

    for location, zip_code in new_locations.items():
        markets = determine_markets_for_location(location, zip_code)

        if markets:
            print(f"✅ {location} → {markets}")

            # Get ZIPs for this location (use job ZIP + lookup more)
            default_zips = [zip_code] if zip_code else []

            # Insert into location_markets
            try:
                client.table('location_markets').insert({
                    'location_string': location,
                    'location_type': 'city',
                    'markets': markets,
                    'default_zips': default_zips if default_zips else None
                }).execute()
                added += 1
            except Exception as e:
                print(f"   ⚠️  Error adding: {e}")
                failed += 1
        else:
            print(f"❌ {location} → No markets found (ZIP: {zip_code})")
            failed += 1

    print(f"\n📊 Results:")
    print(f"   ✅ Added: {added}")
    print(f"   ❌ Failed: {failed}")

    # Final coverage
    result = client.table('location_markets').select('id').execute()
    total = len(result.data)
    print(f"\n📍 Total locations in library: {total:,}")


if __name__ == "__main__":
    print("🚀 Auto-Learning City→Market Mappings\n")
    discover_new_cities()
    print("\n✅ Complete!")
