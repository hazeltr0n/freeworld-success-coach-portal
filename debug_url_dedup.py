#!/usr/bin/env python3
import pandas as pd
import hashlib
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

df = pd.read_csv('/Users/freeworld_james/Downloads/Outscraper-20251003194911xs95_fullscrapegoogle.csv')

def extract_clean_url(url_str):
    if pd.isna(url_str) or url_str == '':
        return ''
    match = re.search(r'https://[^\"\s]+', url_str)
    if match:
        url = match.group(0).rstrip('\",}]')
        parsed = urlparse(url)
        if parsed.query:
            params = parse_qs(parsed.query, keep_blank_values=True)
            clean_params = {k: v for k, v in params.items() if not k.startswith('utm_')}
            new_query = urlencode(clean_params, doseq=True)
            url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
        return url
    return ''

def generate_job_id(company, location, title):
    content = f'{company.lower().strip()}|{location.lower().strip()}|{title.lower().strip()}'
    return hashlib.md5(content.encode()).hexdigest()

def normalize_title(title):
    if pd.isna(title):
        return ''
    title = title.lower().strip()
    title = re.sub(r'[^\w\s]', '', title)
    return ' '.join(title.split())

df['company'] = df['company'].fillna('Unknown')
df['meta.market'] = df['meta.market'].fillna('Unknown')
df['title'] = df['title'].fillna('')
df['location'] = df['location'].fillna('')

# Apply dedup stages
df['job_id'] = df.apply(lambda x: generate_job_id(x['company'], x['location'], x['title']), axis=1)
df['dup_job_id'] = df.duplicated(subset=['job_id'], keep='first')

df['title_norm'] = df['title'].apply(normalize_title)
df['r1_key'] = df['company'] + '|' + df['title_norm'] + '|' + df['meta.market']
df['dup_r1'] = False
for key, group in df[~df['dup_job_id']].groupby('r1_key'):
    if len(group) > 1:
        df.loc[group.index[1:], 'dup_r1'] = True

# Now check URL dedupe on REMAINING jobs
df['clean_url'] = df['apply_urls'].apply(extract_clean_url)

remaining = df[~df['dup_job_id'] & ~df['dup_r1']]
has_url = remaining['clean_url'] != ''
url_market_counts = remaining[has_url].groupby(['clean_url', 'meta.market']).size()
url_dupes_in_remaining = url_market_counts[url_market_counts > 1]

print(f'After Job ID + R1: {len(remaining):,} jobs remaining')
print(f'URL duplicates in REMAINING jobs: {len(url_dupes_in_remaining)}')
print()

if len(url_dupes_in_remaining) > 0:
    print('URL duplicates that survived Job ID + R1:')
    print(url_dupes_in_remaining.sort_values(ascending=False).head(20))
    print()

    # Count total jobs that would be removed
    total_to_remove = (url_dupes_in_remaining - 1).sum()  # Keep 1 from each group
    print(f'Total jobs URL dedup would remove: {total_to_remove}')
else:
    print('✅ Job ID + R1 already caught all URL duplicates!')
