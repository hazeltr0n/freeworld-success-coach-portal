#!/usr/bin/env python3
"""
Seed location_markets table with data from:
1. Existing MarketMapper city mappings (1,376 cities)
2. Production jobs table (tons of real-world location→market pairs)
"""

from market_mapper import MarketMapper
from companies_rollup import get_client
from collections import defaultdict

def seed_from_market_mapper():
    """Seed from existing MarketMapper city mappings"""
    mapper = MarketMapper()

    # Convert market_lookup to location_markets format
    # market_lookup is {location: [markets]} but currently only has single market
    location_data = []

    for location, markets in mapper.market_lookup.items():
        location_data.append({
            'location_string': location.lower().strip(),
            'location_type': 'city',
            'markets': markets if isinstance(markets, list) else [markets],
            'latitude': None,
            'longitude': None
        })

    print(f"📍 Found {len(location_data)} city mappings from MarketMapper")
    return location_data

def seed_from_jobs_table():
    """Seed from production jobs table - capture real-world location→market pairs"""
    client = get_client()
    if not client:
        print("❌ No Supabase client available")
        return []

    # Get all jobs with location and market
    result = client.table('jobs').select('location, normalized_location, market').limit(50000).execute()

    if not result.data:
        print("❌ No jobs data found")
        return []

    print(f"📊 Retrieved {len(result.data)} jobs from database")

    # Build location→markets mapping (supporting multiple markets)
    location_markets = defaultdict(set)

    for row in result.data:
        # Try normalized_location first, fallback to location
        location = row.get('normalized_location') or row.get('location')
        market = row.get('market')

        if location and market:
            location = str(location).strip().lower()
            market = str(market).strip()
            location_markets[location].add(market)

    # Convert to list format
    location_data = []
    for location, markets in location_markets.items():
        location_data.append({
            'location_string': location,
            'location_type': 'city',
            'markets': sorted(list(markets)),  # Sort for consistency
            'latitude': None,
            'longitude': None
        })

    print(f"📍 Found {len(location_data)} unique location→market mappings from jobs")

    # Show examples of multi-market locations
    multi_market = [loc for loc in location_data if len(loc['markets']) > 1]
    if multi_market:
        print(f"✨ Found {len(multi_market)} locations with multiple markets:")
        for loc in multi_market[:10]:
            print(f"   {loc['location_string']}: {loc['markets']}")

    return location_data

def merge_location_data(mapper_data, jobs_data):
    """Merge data from both sources, preferring jobs data for multi-market locations"""
    merged = {}

    # Start with MarketMapper data
    for loc in mapper_data:
        key = loc['location_string']
        merged[key] = loc

    # Merge in jobs data - combine markets if location exists
    for loc in jobs_data:
        key = loc['location_string']
        if key in merged:
            # Combine markets from both sources
            existing_markets = set(merged[key]['markets'])
            new_markets = set(loc['markets'])
            merged[key]['markets'] = sorted(list(existing_markets | new_markets))
        else:
            merged[key] = loc

    return list(merged.values())

def upload_to_supabase(location_data):
    """Upload location data to Supabase location_markets table"""
    client = get_client()
    if not client:
        print("❌ No Supabase client available")
        return False

    print(f"\n📤 Uploading {len(location_data)} location mappings to Supabase...")

    # Batch insert (Supabase handles upsert with UNIQUE constraint)
    batch_size = 500
    success_count = 0

    for i in range(0, len(location_data), batch_size):
        batch = location_data[i:i+batch_size]
        try:
            # Use upsert to handle duplicates gracefully
            result = client.table('location_markets').upsert(batch).execute()
            success_count += len(batch)
            print(f"   ✓ Uploaded batch {i//batch_size + 1}/{(len(location_data)-1)//batch_size + 1}")
        except Exception as e:
            print(f"   ⚠️  Error in batch {i//batch_size + 1}: {e}")

    print(f"\n✅ Successfully uploaded {success_count}/{len(location_data)} location mappings")
    return True

def main():
    print("🚀 Seeding location_markets table\n")

    # Get data from both sources
    mapper_data = seed_from_market_mapper()
    jobs_data = seed_from_jobs_table()

    # Merge the data
    print(f"\n🔀 Merging data from both sources...")
    merged_data = merge_location_data(mapper_data, jobs_data)
    print(f"   Total unique locations: {len(merged_data)}")

    # Show final stats
    multi_market = [loc for loc in merged_data if len(loc['markets']) > 1]
    print(f"   Locations with multiple markets: {len(multi_market)}")

    # Upload to Supabase
    upload_to_supabase(merged_data)

    print("\n🎉 Location markets library seeded successfully!")

if __name__ == "__main__":
    main()
