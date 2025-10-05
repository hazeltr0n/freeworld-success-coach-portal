#!/usr/bin/env python3
"""
Test the new HYBRID R2 deduplication (OLD for blacklisted, NEW for legitimate)
"""
import pandas as pd
from canonical_transforms import transform_business_rules
from jobs_schema import build_empty_df, ensure_schema

# Create test data
test_jobs = [
    # Legitimate company (Schneider) - should use NEW R2 (description hash)
    {'source.company': 'Schneider', 'source.title': 'CDL A Driver', 'source.location_raw': 'Phoenix, AZ', 'source.description_raw': 'Drive dry van trailers. Home weekly. Great pay.', 'meta.market': 'Phoenix'},
    {'source.company': 'Schneider', 'source.title': 'CDL Class A Driver', 'source.location_raw': 'Phoenix, AZ', 'source.description_raw': 'Drive dry van trailers. Home weekly. Great pay.', 'meta.market': 'Phoenix'},  # Same description -> deduped
    {'source.company': 'Schneider', 'source.title': 'Flatbed Driver', 'source.location_raw': 'Phoenix, AZ', 'source.description_raw': 'Flatbed hauling. Tarping required. Weekly home time.', 'meta.market': 'Phoenix'},  # Different description -> kept

    # Blacklisted company (Class A Drivers) - should use OLD R2 (company+market only)
    {'source.company': 'Class A Drivers', 'source.title': 'Local CDL Driver', 'source.location_raw': 'Dallas, TX', 'source.description_raw': 'Local routes. Home daily. Competitive pay.', 'meta.market': 'Dallas'},
    {'source.company': 'Class A Drivers', 'source.title': 'CDL A Driver Local', 'source.location_raw': 'Dallas, TX', 'source.description_raw': 'Different description entirely. Different job.', 'meta.market': 'Dallas'},  # Different description but STILL deduped (OLD R2)
    {'source.company': 'Class A Drivers', 'source.title': 'Class A Local Driver', 'source.location_raw': 'Dallas, TX', 'source.description_raw': 'Yet another description.', 'meta.market': 'Dallas'},  # Also deduped (OLD R2)
]

df = pd.DataFrame(test_jobs)

# Add required fields
df = ensure_schema(df)
df['id.source'] = 'test'
df['sys.is_fresh_job'] = True

# Normalize titles and companies
df['norm.title'] = df['source.title'].str.lower().str.strip()
df['norm.company'] = df['source.company']
df['norm.location'] = df['source.location_raw']
df['norm.description'] = df['source.description_raw']

print("🧪 Testing HYBRID R2 Deduplication")
print("=" * 80)
print()
print("Test Data:")
print("-" * 80)
for i, row in df.iterrows():
    print(f"{i+1}. {row['source.company']:20} | {row['source.title']:25} | Market: {row['meta.market']}")
print()

# Apply business rules (which includes deduplication key generation)
df_with_rules = transform_business_rules(df, {})

print()
print("Deduplication Keys Generated:")
print("-" * 80)
for i, row in df_with_rules.iterrows():
    r2_key = row['rules.duplicate_r2']
    company = row['source.company']
    title = row['source.title']
    print(f"{i+1}. {company:20} | R2: {r2_key}")

print()
print("Expected Results:")
print("-" * 80)
print("Schneider (LEGITIMATE - NEW R2):")
print("  Job 1 & 2: Same description -> Same R2 key -> One will be deduped ✓")
print("  Job 3: Different description -> Different R2 key -> Kept ✓")
print()
print("Class A Drivers (BLACKLISTED - OLD R2):")
print("  All 3 jobs: Same company+market -> Same R2 key -> Only 1 kept ✓")
print()

# Check for duplicates
schneider_r2_keys = df_with_rules[df_with_rules['source.company'] == 'Schneider']['rules.duplicate_r2'].tolist()
class_a_r2_keys = df_with_rules[df_with_rules['source.company'] == 'Class A Drivers']['rules.duplicate_r2'].tolist()

print("Actual Results:")
print("-" * 80)
print(f"Schneider R2 keys: {schneider_r2_keys}")
print(f"  Unique keys: {len(set(schneider_r2_keys))} (expect 2)")
print()
print(f"Class A Drivers R2 keys: {class_a_r2_keys}")
print(f"  Unique keys: {len(set(class_a_r2_keys))} (expect 1)")
print()

if len(set(schneider_r2_keys)) == 2 and len(set(class_a_r2_keys)) == 1:
    print("✅ HYBRID R2 TEST PASSED!")
else:
    print("❌ HYBRID R2 TEST FAILED!")
