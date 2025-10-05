#!/usr/bin/env python3
"""
Deep dive into Schneider jobs to see if they're really unique
"""
import pandas as pd
import hashlib
import re
from html import unescape
from difflib import SequenceMatcher

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

print("📄 Loading data...")
df = pd.read_csv('/Users/freeworld_james/Downloads/Outscraper-20251003194911xs95_fullscrapegoogle.csv')

# Get Schneider jobs in Phoenix
schneider = df[(df['company'] == 'Schneider') & (df['meta.market'] == 'Phoenix')].copy()

print(f"🏢 Schneider - Phoenix")
print("=" * 80)
print(f"Total jobs: {len(schneider)}")
print()

# Generate content hashes
schneider['content_hash'] = schneider['description'].apply(generate_content_hash)

# Group by content hash
hash_groups = schneider.groupby('content_hash')

print(f"Unique content hashes: {hash_groups.ngroups}")
print()

# Show ALL hash groups with details
print("🔍 ALL UNIQUE JOBS:")
print("=" * 80)
print()

for i, (hash_val, group) in enumerate(hash_groups, 1):
    print(f"GROUP {i}: {hash_val} ({len(group)} jobs with identical descriptions)")
    print("-" * 80)

    # Show all titles in this group
    titles = group['title'].unique()
    print(f"Titles ({len(titles)} unique):")
    for title in titles:
        count = len(group[group['title'] == title])
        print(f"  - {title} ({count}x)")

    print()

    # Show first 500 chars of description
    sample_desc = strip_html(group.iloc[0]['description'])
    print("Description preview:")
    print(sample_desc[:500])
    if len(sample_desc) > 500:
        print(f"\n... ({len(sample_desc) - 500} more characters)")

    print()
    print("=" * 80)
    print()

# Now compare descriptions between groups to see how similar they are
print()
print("🔬 SIMILARITY ANALYSIS BETWEEN GROUPS:")
print("=" * 80)
print()

group_list = list(hash_groups)
for i in range(min(5, len(group_list))):
    for j in range(i + 1, min(5, len(group_list))):
        hash_i, jobs_i = group_list[i]
        hash_j, jobs_j = group_list[j]

        desc_i = strip_html(jobs_i.iloc[0]['description'])[:500]
        desc_j = strip_html(jobs_j.iloc[0]['description'])[:500]

        similarity = SequenceMatcher(None, desc_i, desc_j).ratio()

        title_i = jobs_i.iloc[0]['title']
        title_j = jobs_j.iloc[0]['title']

        print(f"Group {i+1} vs Group {j+1}: {similarity*100:.1f}% similar")
        print(f"  '{title_i}' vs '{title_j}'")
        print()

print()
print("📊 SUMMARY:")
print("=" * 80)
print(f"Schneider (Phoenix): {len(schneider)} total job postings")
print(f"Unique descriptions: {hash_groups.ngroups}")
print(f"Spam/duplicates caught: {len(schneider) - hash_groups.ngroups}")
print()

# Calculate average group size
avg_group_size = len(schneider) / hash_groups.ngroups
print(f"Average jobs per unique description: {avg_group_size:.1f}")
print()

if avg_group_size > 2:
    print("⚠️  High duplication - likely title manipulation spam")
elif avg_group_size > 1.5:
    print("⚠️  Moderate duplication - some title variations")
else:
    print("✅ Low duplication - mostly unique jobs")
