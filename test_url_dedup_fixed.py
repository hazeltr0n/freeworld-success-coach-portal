#!/usr/bin/env python3
"""
Test full deduplication pipeline with CORRECT URL dedup (full URL, not domain)
"""
import pandas as pd
import hashlib
import re
from html import unescape
import json

def strip_html(text):
    if pd.isna(text) or text == '':
        return ''
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', str(text))
    text = unescape(text)
    return text.strip()

def generate_job_id(company, location, title):
    content = f'{company.lower().strip()}|{location.lower().strip()}|{title.lower().strip()}'
    return hashlib.md5(content.encode()).hexdigest()

def extract_first_url(url_str):
    """Extract first actual URL from apply_urls field - FULL URL, not just domain"""
    if pd.isna(url_str) or url_str == '':
        return ''
    try:
        # Parse JSON-like structure
        if url_str.startswith('[{'):
            # Clean up the malformed JSON
            cleaned = url_str.replace("'", '"').replace('apply_url:', '"apply_url"')
            urls_list = json.loads(cleaned)
            if urls_list:
                url = urls_list[0].get('apply_url', '')
                # Remove query params for deduplication (utm tracking, etc)
                if '?' in url:
                    url = url.split('?')[0]
                return url
        return ''
    except:
        return ''

def generate_content_hash(description):
    if pd.isna(description) or description == '':
        return 'no_description'
    desc_clean = strip_html(description).lower()[:500]
    for word in ['driver', 'cdl', 'class', 'truck', 'a', 'b', 'the', 'and', 'or', 'our', 'we', 'you', 'your']:
        desc_clean = desc_clean.replace(f' {word} ', ' ')
    desc_clean = ' '.join(desc_clean.split())
    return hashlib.md5(desc_clean.encode()).hexdigest()[:12]

def normalize_title(title):
    if pd.isna(title):
        return ''
    title = title.lower().strip()
    title = re.sub(r'[^\w\s]', '', title)
    return ' '.join(title.split())

print('📄 Loading data...')
df = pd.read_csv('/Users/freeworld_james/Downloads/Outscraper-20251003194911xs95_fullscrapegoogle.csv')
print(f'✅ Total jobs: {len(df):,}')
print()

df['company'] = df['company'].fillna('Unknown')
df['meta.market'] = df['meta.market'].fillna('Unknown')
df['description'] = df['description'].fillna('')
df['title'] = df['title'].fillna('')
df['location'] = df['location'].fillna('')

print('🔧 FULL DEDUPLICATION PIPELINE (CORRECTED URL DEDUP)')
print('=' * 80)
print()

# Stage 1: Job ID dedup
df['job_id'] = df.apply(lambda x: generate_job_id(x['company'], x['location'], x['title']), axis=1)
df['dup_job_id'] = df.duplicated(subset=['job_id'], keep='first')
after_job_id = len(df[~df['dup_job_id']])
print(f'Stage 1 - Job ID:     {len(df):,} → {after_job_id:,} ({df["dup_job_id"].sum():,} removed)')

# Stage 2: R1 dedup
df['title_norm'] = df['title'].apply(normalize_title)
df['r1_key'] = df['company'] + '|' + df['title_norm'] + '|' + df['meta.market']
df['dup_r1'] = False
for key, group in df[~df['dup_job_id']].groupby('r1_key'):
    if len(group) > 1:
        df.loc[group.index[1:], 'dup_r1'] = True
after_r1 = len(df[~df['dup_job_id'] & ~df['dup_r1']])
print(f'Stage 2 - R1:         {after_job_id:,} → {after_r1:,} ({df["dup_r1"].sum():,} removed)')

# Stage 3: URL dedup (FIXED - use FULL URL, not domain)
df['clean_url'] = df['apply_urls'].apply(extract_first_url)
df['dup_url'] = False

# Only dedupe non-empty URLs within unfiltered jobs
unfiltered = ~df['dup_job_id'] & ~df['dup_r1']
has_url = df['clean_url'] != ''

for (url, market), group in df[unfiltered & has_url].groupby(['clean_url', 'meta.market']):
    if len(group) > 1:
        df.loc[group.index[1:], 'dup_url'] = True

after_url = len(df[unfiltered & ~df['dup_url']])
print(f'Stage 3 - URL:        {after_r1:,} → {after_url:,} ({df["dup_url"].sum():,} removed)')

# Stage 4: OLD R2
df['r2_old'] = df['company'] + '|' + df['meta.market']
df['dup_r2_old'] = False
unfiltered_old = ~df['dup_job_id'] & ~df['dup_r1'] & ~df['dup_url']

for key, group in df[unfiltered_old].groupby('r2_old'):
    if len(group) > 1:
        df.loc[group.index[1:], 'dup_r2_old'] = True

after_r2_old = len(df[unfiltered_old & ~df['dup_r2_old']])
print(f'Stage 4 - OLD R2:     {after_url:,} → {after_r2_old:,} ({df["dup_r2_old"].sum():,} removed)')

# Stage 4: NEW R2
df['content_hash'] = df['description'].apply(generate_content_hash)
df['r2_new'] = df['company'] + '|' + df['meta.market'] + '|' + df['content_hash']
df['dup_r2_new'] = False
unfiltered_new = ~df['dup_job_id'] & ~df['dup_r1'] & ~df['dup_url']

for key, group in df[unfiltered_new].groupby('r2_new'):
    if len(group) > 1:
        df.loc[group.index[1:], 'dup_r2_new'] = True

after_r2_new = len(df[unfiltered_new & ~df['dup_r2_new']])
print(f'Stage 4 - NEW R2:     {after_url:,} → {after_r2_new:,} ({df["dup_r2_new"].sum():,} removed)')

print()
print('=' * 80)
print('📊 FINAL RESULTS')
print('=' * 80)
print()

print(f"{'Stage':<30} {'Jobs Remaining':<20} {'Removed':<15}")
print('-' * 80)
print(f"{'Starting:':<30} {len(df):<20,} {'-':<15}")
print(f"{'After Job ID:':<30} {after_job_id:<20,} {df['dup_job_id'].sum():<15,}")
print(f"{'After R1:':<30} {after_r1:<20,} {df['dup_r1'].sum():<15,}")
print(f"{'After URL:':<30} {after_url:<20,} {df['dup_url'].sum():<15,}")
print(f"{'After OLD R2:':<30} {after_r2_old:<20,} {df['dup_r2_old'].sum():<15,}")
print(f"{'After NEW R2:':<30} {after_r2_new:<20,} {df['dup_r2_new'].sum():<15,}")
print()
print('-' * 80)
print(f'OLD R2 keeps: {after_r2_old:,} jobs ({after_r2_old/len(df)*100:.1f}% of original)')
print(f'NEW R2 keeps: {after_r2_new:,} jobs ({after_r2_new/len(df)*100:.1f}% of original)')
print(f'Difference:   +{after_r2_new - after_r2_old:,} jobs (+{(after_r2_new-after_r2_old)/after_r2_old*100:.1f}%)')
print()

# Show URL sample
print()
print('🔍 URL Extraction Sample:')
print('-' * 80)
for i in range(5):
    url = df.iloc[i]['clean_url']
    if url:
        print(f'Row {i}: {url[:100]}...' if len(url) > 100 else f'Row {i}: {url}')
    else:
        print(f'Row {i}: (no URL)')

# Check how many have URLs
print()
print(f'Jobs with URLs: {(df["clean_url"] != "").sum():,} ({(df["clean_url"] != "").sum()/len(df)*100:.1f}%)')
