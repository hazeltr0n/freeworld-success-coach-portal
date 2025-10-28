#!/usr/bin/env python3
"""Test the integrated market mapper with sample CSV data"""

import pandas as pd
from canonical_transforms import apply_market_assignment
from jobs_schema import ensure_schema

print("=" * 80)
print("TESTING MARKET MAPPER INTEGRATION")
print("=" * 80)

# Create sample job data with ZIP codes (similar to CSV classifier input)
sample_jobs = [
    {
        'norm.title': 'CDL A Driver - Local Routes',
        'norm.company': 'ABC Trucking',
        'norm.location': 'Dallas, TX',
        'norm.zip_code': '75001',  # Dallas ZIP
        'id.job': 'test-job-1'
    },
    {
        'norm.title': 'Warehouse Worker',
        'norm.company': 'XYZ Logistics',
        'norm.location': 'Houston, TX',
        'norm.zip_code': '77001',  # Houston ZIP
        'id.job': 'test-job-2'
    },
    {
        'norm.title': 'OTR Driver',
        'norm.company': 'Interstate Transport',
        'norm.location': 'Phoenix, AZ',
        'norm.zip_code': '85001',  # Phoenix ZIP
        'id.job': 'test-job-3'
    },
    {
        'norm.title': 'Local Delivery Driver',
        'norm.company': 'Quick Delivery',
        'norm.location': 'Las Vegas, NV',
        'norm.zip_code': '89101',  # Las Vegas ZIP
        'id.job': 'test-job-4'
    },
    {
        'norm.title': 'Regional Driver',
        'norm.company': 'Regional Freight',
        'norm.location': 'Newark, NJ',
        'norm.zip_code': '07101',  # Newark ZIP
        'id.job': 'test-job-5'
    }
]

# Create DataFrame and apply schema
df = pd.DataFrame(sample_jobs)
df = ensure_schema(df)

print(f"\n📋 Created {len(df)} sample jobs with ZIP codes:")
for idx, row in df.iterrows():
    print(f"  {idx+1}. {row['norm.location']} (ZIP: {row['norm.zip_code']})")

# Test automatic market mapping (no market parameter provided)
print("\n🗺️  Testing automatic market mapping from ZIP codes...")
print("    (Calling apply_market_assignment with empty market parameter)")

result_df = apply_market_assignment(df, market='', is_custom_location=False)

print(f"\n✅ Market mapping complete!\n")
print("Results:")
print("-" * 80)

for idx, row in result_df.iterrows():
    market = row.get('meta.market', 'NOT SET')
    print(f"{idx+1}. {row['norm.company']}")
    print(f"   Location: {row['norm.location']}")
    print(f"   ZIP Code: {row['norm.zip_code']}")
    print(f"   🎯 Assigned Market: {market}")
    print()

# Count successful mappings
successful_mappings = (result_df['meta.market'] != '').sum()
print("=" * 80)
print(f"Summary: {successful_mappings}/{len(result_df)} jobs successfully mapped to markets")
print("=" * 80)
