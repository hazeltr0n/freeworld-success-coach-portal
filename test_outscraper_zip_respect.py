#!/usr/bin/env python3
"""
Test if Outscraper API actually respects ZIP code locations
"""

import os
from outscraper import ApiClient

def test_zip_code_search():
    """Test if Outscraper returns jobs actually in the ZIP we specify"""

    api_key = os.getenv('OUTSCRAPER_API_KEY')
    client = ApiClient(api_key=api_key)

    # Test with a specific Dallas ZIP
    test_zip = "75060"  # Irving, TX - from our radius CSV
    query = "CDL driver"

    print("=" * 80)
    print(f"🧪 Testing Outscraper ZIP Code Respect")
    print("=" * 80)
    print(f"\n🔍 Query: '{query}'")
    print(f"📍 Location: {test_zip}")
    print(f"\n⏳ Calling Outscraper API...\n")

    try:
        results = client.jobs_search(
            query=query,
            location=test_zip,
            limit=20
        )

        if not results or len(results) == 0:
            print("❌ No results returned")
            return

        jobs = results[0] if isinstance(results, list) else results

        print(f"✅ Got {len(jobs)} jobs\n")
        print("📊 Analyzing locations returned:\n")

        # Analyze what locations we actually got
        locations = {}
        for job in jobs:
            location = job.get('jobLocationCity', '') + ', ' + job.get('jobLocationState', '')
            zip_code = job.get('jobLocationZip', 'No ZIP')

            key = f"{location} (ZIP: {zip_code})"
            locations[key] = locations.get(key, 0) + 1

        # Sort by frequency
        for loc, count in sorted(locations.items(), key=lambda x: x[1], reverse=True):
            print(f"   {loc}: {count} jobs")

        # Check how many are actually in the ZIP we requested
        print(f"\n🎯 Jobs in requested ZIP ({test_zip}):")
        matching = [j for j in jobs if str(j.get('jobLocationZip', '')) == test_zip]
        print(f"   {len(matching)}/{len(jobs)} ({len(matching)/len(jobs)*100:.1f}%)")

        # Show sample job locations
        print(f"\n📋 Sample job locations (first 10):")
        for i, job in enumerate(jobs[:10], 1):
            title = job.get('title', 'No title')[:50]
            city = job.get('jobLocationCity', 'Unknown')
            state = job.get('jobLocationState', '')
            zip_code = job.get('jobLocationZip', 'No ZIP')
            print(f"   {i}. {title}")
            print(f"      📍 {city}, {state} {zip_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_zip_code_search()
