#!/usr/bin/env python3
"""
Compare FULL deduplication pipeline: OLD vs NEW R2
Simulates all dedup stages: Job ID, R1, URL, R2
"""
import pandas as pd
import hashlib
import re
from html import unescape
from urllib.parse import urlparse

def strip_html(text):
    """Strip HTML tags"""
    if pd.isna(text) or text == '':
        return ''
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', str(text))
    text = unescape(text)
    return text.strip()

def generate_job_id(company: str, location: str, title: str) -> str:
    """Generate MD5 job ID (like id.job in schema)"""
    content = f"{company.lower().strip()}|{location.lower().strip()}|{title.lower().strip()}"
    return hashlib.md5(content.encode()).hexdigest()

def extract_clean_url(url: str) -> str:
    """Extract domain from URL for deduplication"""
    if pd.isna(url) or url == '':
        return ''
    try:
        # Handle JSON-like apply_urls field
        if url.startswith('[{'):
            import json
            urls_list = json.loads(url.replace("'", '"').replace('apply_url:', 'apply_url'))
            if urls_list:
                url = urls_list[0].get('apply_url', '')

        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Remove www.
        domain = domain.replace('www.', '')
        return domain
    except:
        return ''

def generate_content_hash(description: str) -> str:
    """Generate hash from description content (NEW R2)"""
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

def normalize_title(title: str) -> str:
    """Normalize title for R1 deduplication"""
    if pd.isna(title):
        return ''
    title = title.lower().strip()
    # Remove punctuation
    title = re.sub(r'[^\w\s]', '', title)
    # Normalize whitespace
    return ' '.join(title.split())

print("📄 Loading production data...")
df = pd.read_csv('/Users/freeworld_james/Downloads/Outscraper-20251003194911xs95_fullscrapegoogle.csv')
print(f"✅ Loaded {len(df):,} jobs")
print()

# Clean up fields
df['company'] = df['company'].fillna('Unknown Company')
df['meta.market'] = df['meta.market'].fillna('Unknown Market')
df['description'] = df['description'].fillna('')
df['title'] = df['title'].fillna('')
df['location'] = df['location'].fillna('')

print("🔧 Simulating FULL Deduplication Pipeline")
print("=" * 80)
print()

# Create two dataframes: one for OLD, one for NEW
df_old = df.copy()
df_new = df.copy()

# Both start with same initial count
initial_count = len(df)

print(f"Starting jobs: {initial_count:,}")
print()

# ============================================================================
# STAGE 1: Job ID Deduplication (same for both)
# ============================================================================
print("Stage 1: Job ID Deduplication (id.job = company+location+title)")
print("-" * 80)

df_old['job_id'] = df_old.apply(lambda x: generate_job_id(
    x['company'], x['location'], x['title']
), axis=1)
df_new['job_id'] = df_new.apply(lambda x: generate_job_id(
    x['company'], x['location'], x['title']
), axis=1)

# Mark duplicates
df_old['filtered_job_id'] = df_old.duplicated(subset=['job_id'], keep='first')
df_new['filtered_job_id'] = df_new.duplicated(subset=['job_id'], keep='first')

job_id_dupes = df_old['filtered_job_id'].sum()

df_old_remaining = len(df_old[~df_old['filtered_job_id']])
df_new_remaining = len(df_new[~df_new['filtered_job_id']])

print(f"Duplicates found: {job_id_dupes:,}")
print(f"Remaining: {df_old_remaining:,} (both pipelines identical)")
print()

# ============================================================================
# STAGE 2: R1 Deduplication (company+title+market) (same for both)
# ============================================================================
print("Stage 2: R1 Deduplication (company+title+market)")
print("-" * 80)

df_old['title_normalized'] = df_old['title'].apply(normalize_title)
df_new['title_normalized'] = df_new['title'].apply(normalize_title)

df_old['r1_key'] = df_old['company'] + '|' + df_old['title_normalized'] + '|' + df_old['meta.market']
df_new['r1_key'] = df_new['company'] + '|' + df_new['title_normalized'] + '|' + df_new['meta.market']

# Only dedupe within non-job-id-filtered jobs
df_old['filtered_r1'] = False
df_new['filtered_r1'] = False

for key, group in df_old[~df_old['filtered_job_id']].groupby('r1_key'):
    if len(group) > 1:
        # Keep first, mark rest as duplicates
        dupes = group.index[1:]
        df_old.loc[dupes, 'filtered_r1'] = True

for key, group in df_new[~df_new['filtered_job_id']].groupby('r1_key'):
    if len(group) > 1:
        dupes = group.index[1:]
        df_new.loc[dupes, 'filtered_r1'] = True

r1_dupes_old = df_old['filtered_r1'].sum()
r1_dupes_new = df_new['filtered_r1'].sum()

df_old_remaining = len(df_old[~df_old['filtered_job_id'] & ~df_old['filtered_r1']])
df_new_remaining = len(df_new[~df_new['filtered_job_id'] & ~df_new['filtered_r1']])

print(f"Duplicates found: {r1_dupes_old:,}")
print(f"Remaining: {df_old_remaining:,} (both pipelines identical)")
print()

# ============================================================================
# STAGE 3: URL Deduplication (same for both)
# ============================================================================
print("Stage 3: URL Deduplication (same URL + market)")
print("-" * 80)

df_old['clean_url'] = df_old['apply_urls'].apply(extract_clean_url)
df_new['clean_url'] = df_new['apply_urls'].apply(extract_clean_url)

df_old['filtered_url'] = False
df_new['filtered_url'] = False

# Only dedupe within non-filtered jobs
unfiltered_old = ~df_old['filtered_job_id'] & ~df_old['filtered_r1']
unfiltered_new = ~df_new['filtered_job_id'] & ~df_new['filtered_r1']

for (url, market), group in df_old[unfiltered_old & (df_old['clean_url'] != '')].groupby(['clean_url', 'meta.market']):
    if len(group) > 1:
        dupes = group.index[1:]
        df_old.loc[dupes, 'filtered_url'] = True

for (url, market), group in df_new[unfiltered_new & (df_new['clean_url'] != '')].groupby(['clean_url', 'meta.market']):
    if len(group) > 1:
        dupes = group.index[1:]
        df_new.loc[dupes, 'filtered_url'] = True

url_dupes_old = df_old['filtered_url'].sum()
url_dupes_new = df_new['filtered_url'].sum()

df_old_remaining = len(df_old[~df_old['filtered_job_id'] & ~df_old['filtered_r1'] & ~df_old['filtered_url']])
df_new_remaining = len(df_new[~df_new['filtered_job_id'] & ~df_new['filtered_r1'] & ~df_new['filtered_url']])

print(f"Duplicates found: {url_dupes_old:,}")
print(f"Remaining: {df_old_remaining:,} (both pipelines identical)")
print()

# ============================================================================
# STAGE 4: R2 Deduplication - THIS IS WHERE THEY DIFFER
# ============================================================================
print("Stage 4: R2 Deduplication")
print("-" * 80)

# OLD R2: company + market only
df_old['r2_key'] = df_old['company'] + '|' + df_old['meta.market']

# NEW R2: company + market + description hash
df_new['content_hash'] = df_new['description'].apply(generate_content_hash)
df_new['r2_key'] = df_new['company'] + '|' + df_new['meta.market'] + '|' + df_new['content_hash']

df_old['filtered_r2'] = False
df_new['filtered_r2'] = False

# Only dedupe within non-filtered jobs
unfiltered_old = ~df_old['filtered_job_id'] & ~df_old['filtered_r1'] & ~df_old['filtered_url']
unfiltered_new = ~df_new['filtered_job_id'] & ~df_new['filtered_r1'] & ~df_new['filtered_url']

for key, group in df_old[unfiltered_old].groupby('r2_key'):
    if len(group) > 1:
        dupes = group.index[1:]
        df_old.loc[dupes, 'filtered_r2'] = True

for key, group in df_new[unfiltered_new].groupby('r2_key'):
    if len(group) > 1:
        dupes = group.index[1:]
        df_new.loc[dupes, 'filtered_r2'] = True

r2_dupes_old = df_old['filtered_r2'].sum()
r2_dupes_new = df_new['filtered_r2'].sum()

df_old_final = len(df_old[~df_old['filtered_job_id'] & ~df_old['filtered_r1'] & ~df_old['filtered_url'] & ~df_old['filtered_r2']])
df_new_final = len(df_new[~df_new['filtered_job_id'] & ~df_new['filtered_r1'] & ~df_new['filtered_url'] & ~df_new['filtered_r2']])

print(f"OLD R2 (company+market):")
print(f"  Duplicates found: {r2_dupes_old:,}")
print(f"  Final remaining: {df_old_final:,}")
print()
print(f"NEW R2 (company+market+description_hash):")
print(f"  Duplicates found: {r2_dupes_new:,}")
print(f"  Final remaining: {df_new_final:,}")
print()

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print()
print("=" * 80)
print("📊 FINAL COMPARISON")
print("=" * 80)
print()

print(f"{'Stage':<30} {'OLD Pipeline':<20} {'NEW Pipeline':<20}")
print("-" * 80)
print(f"{'Starting jobs:':<30} {initial_count:>19,} {initial_count:>19,}")
print(f"{'After Job ID dedup:':<30} {len(df_old[~df_old['filtered_job_id']]):>19,} {len(df_new[~df_new['filtered_job_id']]):>19,}")
print(f"{'After R1 dedup:':<30} {len(df_old[~df_old['filtered_job_id'] & ~df_old['filtered_r1']]):>19,} {len(df_new[~df_new['filtered_job_id'] & ~df_new['filtered_r1']]):>19,}")
print(f"{'After URL dedup:':<30} {len(df_old[unfiltered_old]):>19,} {len(df_new[unfiltered_new]):>19,}")
print(f"{'After R2 dedup:':<30} {df_old_final:>19,} {df_new_final:>19,}")
print()
print("-" * 80)
print(f"{'Total filtered:':<30} {initial_count - df_old_final:>19,} {initial_count - df_new_final:>19,}")
print(f"{'% of original:':<30} {(df_old_final/initial_count*100):>18.1f}% {(df_new_final/initial_count*100):>18.1f}%")
print()
print(f"{'DIFFERENCE:':<30} {df_new_final - df_old_final:>19,} MORE jobs with NEW R2")
print(f"{'Improvement:':<30} {((df_new_final - df_old_final) / df_old_final * 100):>18.1f}%")
print()
print("=" * 80)

# Show which companies benefit most
print()
print("🏢 TOP COMPANIES THAT BENEFIT FROM NEW R2:")
print("-" * 80)

# Get companies with multiple jobs that made it through to R2
both_at_r2 = (
    (~df_old['filtered_job_id'] & ~df_old['filtered_r1'] & ~df_old['filtered_url']) &
    (~df_new['filtered_job_id'] & ~df_new['filtered_r1'] & ~df_new['filtered_url'])
)

companies_old = df_old[both_at_r2 & ~df_old['filtered_r2']].groupby('company').size()
companies_new = df_new[both_at_r2 & ~df_new['filtered_r2']].groupby('company').size()

comparison = pd.DataFrame({
    'old': companies_old,
    'new': companies_new
}).fillna(0).astype(int)

comparison['gain'] = comparison['new'] - comparison['old']
comparison = comparison[comparison['gain'] > 0].sort_values('gain', ascending=False)

print(f"{'Company':<50} {'OLD':<10} {'NEW':<10} {'Gain':<10}")
print("-" * 80)

for company, row in comparison.head(20).iterrows():
    print(f"{company:<50} {row['old']:<10} {row['new']:<10} +{row['gain']:<9}")
