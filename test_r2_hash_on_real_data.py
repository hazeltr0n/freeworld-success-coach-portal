#!/usr/bin/env python3
"""
Test R2 deduplication using description hash on real production data
"""
import pandas as pd
import hashlib
import re
from html import unescape
from collections import defaultdict

def strip_html(text):
    """Strip HTML tags"""
    if pd.isna(text) or text == '':
        return ''
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', str(text))
    text = unescape(text)
    return text.strip()

def generate_content_hash(description: str) -> str:
    """Generate hash from description content"""
    if pd.isna(description) or description == '':
        return 'no_description'

    # Strip HTML
    desc_clean = strip_html(description).lower()[:500]

    # Remove common filler words
    for word in ['driver', 'cdl', 'class', 'truck', 'a', 'b', 'the', 'and', 'or', 'our', 'we', 'you', 'your']:
        desc_clean = desc_clean.replace(f' {word} ', ' ')

    # Normalize whitespace
    desc_clean = ' '.join(desc_clean.split())

    return hashlib.md5(desc_clean.encode()).hexdigest()[:12]

print("📄 Loading production data...")
df = pd.read_csv('/Users/freeworld_james/Downloads/Outscraper-20251003194911xs95_fullscrapegoogle.csv')
print(f"✅ Loaded {len(df):,} jobs")
print()

# Clean up company and market fields
df['company'] = df['company'].fillna('Unknown Company')
df['meta.market'] = df['meta.market'].fillna('Unknown Market')
df['description'] = df['description'].fillna('')

print("🔍 Generating R2 keys...")
print("=" * 80)
print()

# OLD R2 (current implementation)
df['r2_old'] = df['company'] + '|' + df['meta.market']

# NEW R2 (description hash)
df['content_hash'] = df['description'].apply(generate_content_hash)
df['r2_new'] = df['company'] + '|' + df['meta.market'] + '|' + df['content_hash']

# Count unique values
old_unique = df['r2_old'].nunique()
new_unique = df['r2_new'].nunique()

print(f"📊 DEDUPLICATION COMPARISON:")
print("-" * 80)
print(f"Total jobs:              {len(df):,}")
print(f"OLD R2 (company+market): {old_unique:,} unique")
print(f"NEW R2 (company+market+content): {new_unique:,} unique")
print()
print(f"Jobs kept with OLD R2:   {old_unique:,}")
print(f"Jobs kept with NEW R2:   {new_unique:,}")
print(f"Difference:              {new_unique - old_unique:,} MORE jobs preserved")
print()

# Find companies with multiple jobs
print("🏢 COMPANIES WITH MULTIPLE JOBS:")
print("-" * 80)

company_market_counts = df.groupby(['company', 'meta.market']).size().reset_index(name='job_count')
multi_job_companies = company_market_counts[company_market_counts['job_count'] > 1].sort_values('job_count', ascending=False).head(20)

print(f"Found {len(multi_job_companies)} companies with multiple jobs in same market")
print()
print("Top 20 companies:")
for idx, row in multi_job_companies.iterrows():
    company = row['company']
    market = row['meta.market']
    total_jobs = row['job_count']

    # Get subset for this company+market
    subset = df[(df['company'] == company) & (df['meta.market'] == market)]

    # Count unique with new method
    unique_new = subset['r2_new'].nunique()

    reduction = total_jobs - unique_new

    print(f"{company} ({market}): {total_jobs} jobs → {unique_new} unique ({reduction} duplicates)")

print()
print("=" * 80)
print("🔬 DETAILED ANALYSIS: Sample Company")
print("=" * 80)

# Pick a company with lots of jobs
sample_company = multi_job_companies.iloc[0]
company_name = sample_company['company']
market_name = sample_company['meta.market']

print(f"Company: {company_name}")
print(f"Market: {market_name}")
print()

subset = df[(df['company'] == company_name) & (df['meta.market'] == market_name)]

print(f"Total jobs: {len(subset)}")
print()

# Group by content hash
hash_groups = subset.groupby('content_hash')

print(f"Unique content hashes: {hash_groups.ngroups}")
print()

# Show a few groups
print("Sample hash groups:")
for i, (hash_val, group) in enumerate(list(hash_groups)[:5]):
    print(f"\nHash {i+1}: {hash_val} ({len(group)} jobs)")
    for idx, job in group.head(3).iterrows():
        print(f"  - {job['title']}")
    if len(group) > 3:
        print(f"  ... and {len(group) - 3} more")

print()
print("=" * 80)
print("📈 SUMMARY")
print("=" * 80)

dedup_improvement = new_unique - old_unique
percentage_improvement = (dedup_improvement / old_unique) * 100

print(f"OLD R2 would keep:     {old_unique:,} jobs ({(old_unique/len(df)*100):.1f}% of total)")
print(f"NEW R2 would keep:     {new_unique:,} jobs ({(new_unique/len(df)*100):.1f}% of total)")
print(f"Jobs saved from dedup: {dedup_improvement:,} (+{percentage_improvement:.1f}%)")
print()
print("✅ Description hash preserves legitimate job diversity while catching title spam!")
