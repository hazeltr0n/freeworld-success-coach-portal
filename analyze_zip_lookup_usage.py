#!/usr/bin/env python3
"""
Analyze all pipeline files for ZIP lookup usage and identify what needs to be fixed
"""

import os
import re

files_to_check = [
    ('canonical_transforms.py', 'Indeed/Outscraper transforms'),
    ('classify_csv.py', 'CSV Classifier'),
    ('driver_pulse_adapter.py', 'DriverPulse'),
    ('async_job_manager.py', 'Scheduled Batches'),
    ('pipeline_v3.py', 'Main Pipeline')
]

print("🔍 ANALYZING ZIP LOOKUP USAGE ACROSS PIPELINES\n")

for filename, description in files_to_check:
    filepath = f'/Users/freeworld_james/Development/freeworld-master/freeworld-job-scraper-main/{filename}'

    if not os.path.exists(filepath):
        print(f"⚠️  {description} ({filename}): FILE NOT FOUND")
        continue

    with open(filepath, 'r') as f:
        content = f.read()

    print(f"📄 {description} ({filename}):")
    print(f"   Location: {filepath}")

    # Check for various ZIP lookup patterns
    issues = []

    # Check if it imports zip_market_lookup
    if 'from zip_market_lookup import' in content or 'import zip_market_lookup' in content:
        print(f"   ✅ Imports zip_market_lookup")
    else:
        issues.append("❌ Does NOT import zip_market_lookup")

    # Check if it queries location_markets for city rows (now deleted)
    if 'location_markets' in content and "default_zips" in content:
        issues.append("❌ Still queries location_markets for default_zips (city rows deleted!)")

    # Check if it queries location_markets at all
    if "table('location_markets')" in content:
        issues.append("⚠️  Queries location_markets table (should use .py file instead)")

    # Check for ZIP_TO_CITY_STATE usage
    if 'ZIP_TO_CITY_STATE' in content:
        print(f"   ✅ Uses ZIP_TO_CITY_STATE for ZIP→City,ST lookup")

    # Check for VALID_ZIPS usage
    if 'VALID_ZIPS' in content:
        print(f"   ✅ Uses VALID_ZIPS for filtering")

    # Check for market mapping from ZIP
    if 'meta.market' in content or "'market'" in content:
        if 'zip' in content.lower():
            print(f"   ℹ️  Has market field - check if populated from ZIP")

    if issues:
        for issue in issues:
            print(f"   {issue}")

    print()

print("\n📋 REQUIRED FIXES:\n")
print("1. canonical_transforms.py:")
print("   - Remove _load_location_zip_cache() function (queries deleted city rows)")
print("   - Use zip_market_lookup.ZIP_TO_CITY_STATE for reverse lookup (City,ST → ZIP)")
print()
print("2. classify_csv.py:")
print("   - Add market population from ZIP BEFORE deduplication")
print("   - Import zip_market_lookup and use ZIP → market mapping")
print()
print("3. async_job_manager.py:")
print("   - Add ZIP population from City,ST for scheduled batches")
print("   - Use zip_market_lookup for lookups")
print()
print("4. driver_pulse_adapter.py:")
print("   - Replace Supabase queries with zip_market_lookup.py")
print("   - Already mostly done, but verify _load_location_markets() doesn't query DB")
