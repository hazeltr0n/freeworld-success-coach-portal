#!/usr/bin/env python3
"""
Analyze what percentage of Outscraper jobs would map to our markets
"""

import pandas as pd
from companies_rollup import get_client

# Load Outscraper scrape
outscraper_df = pd.read_csv('/Users/freeworld_james/Downloads/Outscraper-20251006134552xs28_full_scrape_indeed.csv')

print("=" * 80)
print("📊 Analyzing Outscraper Job Coverage")
print("=" * 80)

print(f"\n📦 Total jobs in Outscraper scrape: {len(outscraper_df)}")

# Build location strings from Outscraper data
def normalize_location(s):
    if pd.isna(s) or not s:
        return None
    return str(s).lower().strip()

outscraper_df['city_normalized'] = outscraper_df['jobLocationCity'].apply(normalize_location)
outscraper_df['state_normalized'] = outscraper_df['jobLocationState'].apply(normalize_location)
outscraper_df['location_key'] = outscraper_df['city_normalized'] + ', ' + outscraper_df['state_normalized']

# Filter valid locations
valid_locations = outscraper_df[outscraper_df['location_key'].notna() & (outscraper_df['location_key'] != ', ')].copy()

print(f"📍 Jobs with valid city/state: {len(valid_locations)}")

# Get unique location keys
unique_locations = set(valid_locations['location_key'].unique())
print(f"🗺️  Unique city/state combinations: {len(unique_locations)}")

# Load location_markets from Supabase
client = get_client()

print("\n🔍 Loading location_markets from Supabase...")
cities_result = client.table('location_markets').select('location_string, markets, location_type').eq('location_type', 'city').execute()
zips_result = client.table('location_markets').select('location_string, markets, location_type').eq('location_type', 'zip').execute()

# Build city→market map
city_to_markets = {}
for row in cities_result.data:
    city_str = row['location_string'].lower().strip()
    markets = row['markets']
    if markets:
        city_to_markets[city_str] = markets

# Build ZIP→market map
zip_to_markets = {}
for row in zips_result.data:
    zip_str = row['location_string'].lower().strip()
    markets = row['markets']
    if markets:
        zip_to_markets[zip_str] = markets

print(f"   Loaded {len(city_to_markets)} city→market mappings")
print(f"   Loaded {len(zip_to_markets)} ZIP→market mappings")

# Check city matches
print("\n🌉 Checking city/state matches...")
city_matched = 0
city_unmatched = 0
city_matched_jobs = 0
city_unmatched_jobs = 0

for location_key in unique_locations:
    jobs_at_location = len(valid_locations[valid_locations['location_key'] == location_key])

    if location_key in city_to_markets:
        city_matched += 1
        city_matched_jobs += jobs_at_location
    else:
        city_unmatched += 1
        city_unmatched_jobs += jobs_at_location

print(f"   ✅ Matched cities: {city_matched}/{len(unique_locations)} ({city_matched/len(unique_locations)*100:.1f}%)")
print(f"   ❌ Unmatched cities: {city_unmatched}/{len(unique_locations)} ({city_unmatched/len(unique_locations)*100:.1f}%)")

print(f"\n📊 Job-level coverage:")
print(f"   ✅ Jobs in matched cities: {city_matched_jobs}/{len(valid_locations)} ({city_matched_jobs/len(valid_locations)*100:.1f}%)")
print(f"   ❌ Jobs in unmatched cities: {city_unmatched_jobs}/{len(valid_locations)} ({city_unmatched_jobs/len(valid_locations)*100:.1f}%)")

# Show sample unmatched cities
print(f"\n🔎 Sample unmatched cities (top 10 by job count):")
unmatched_locs = valid_locations[~valid_locations['location_key'].isin(city_to_markets)]
unmatched_counts = unmatched_locs['location_key'].value_counts().head(10)
for loc, count in unmatched_counts.items():
    print(f"   {loc.title()}: {count} jobs")

# Check if we have ZIPs in the data
if 'jobLocationZip' in outscraper_df.columns:
    print("\n🔢 Checking ZIP code coverage...")
    outscraper_df['zip_normalized'] = outscraper_df['jobLocationZip'].apply(lambda x: str(x).zfill(5) if pd.notna(x) else None)
    valid_zips = outscraper_df[outscraper_df['zip_normalized'].notna()].copy()

    if len(valid_zips) > 0:
        unique_zips = set(valid_zips['zip_normalized'].unique())
        print(f"   Jobs with ZIP codes: {len(valid_zips)}")
        print(f"   Unique ZIPs: {len(unique_zips)}")

        zip_matched = sum(1 for z in unique_zips if z in zip_to_markets)
        print(f"   ✅ Matched ZIPs: {zip_matched}/{len(unique_zips)} ({zip_matched/len(unique_zips)*100:.1f}%)")

print("\n" + "=" * 80)
