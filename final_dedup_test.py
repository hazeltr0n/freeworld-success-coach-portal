#!/usr/bin/env python3
import pandas as pd
import hashlib
import re
from html import unescape
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

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

print('Loading...')
df = pd.read_csv('/Users/freeworld_james/Downloads/Outscraper-20251003194911xs95_fullscrapegoogle.csv')

df['company'] = df['company'].fillna('Unknown')
df['meta.market'] = df['meta.market'].fillna('Unknown')
df['description'] = df['description'].fillna('')
df['title'] = df['title'].fillna('')
df['location'] = df['location'].fillna('')

print()
print('FULL DEDUP PIPELINE: Job ID → R1 → URL → R2')
print('=' * 80)

# Job ID
df['job_id'] = df.apply(lambda x: generate_job_id(x['company'], x['location'], x['title']), axis=1)
df['dup_job_id'] = df.duplicated(subset=['job_id'], keep='first')
after_job_id = len(df[~df['dup_job_id']])
print(f'Job ID:    {len(df):>6,} → {after_job_id:>6,} (-{df["dup_job_id"].sum():,})')

# R1
df['title_norm'] = df['title'].apply(normalize_title)
df['r1_key'] = df['company'] + '|' + df['title_norm'] + '|' + df['meta.market']
df['dup_r1'] = False
for key, group in df[~df['dup_job_id']].groupby('r1_key'):
    if len(group) > 1:
        df.loc[group.index[1:], 'dup_r1'] = True
after_r1 = len(df[~df['dup_job_id'] & ~df['dup_r1']])
print(f'R1:        {after_job_id:>6,} → {after_r1:>6,} (-{df["dup_r1"].sum():,})')

# URL
df['clean_url'] = df['apply_urls'].apply(extract_clean_url)
df['dup_url'] = False
unfiltered = ~df['dup_job_id'] & ~df['dup_r1']
has_url = df['clean_url'] != ''

for (url, market), group in df[unfiltered & has_url].groupby(['clean_url', 'meta.market']):
    if len(group) > 1:
        df.loc[group.index[1:], 'dup_url'] = True

after_url = len(df[unfiltered & ~df['dup_url']])
print(f'URL:       {after_r1:>6,} → {after_url:>6,} (-{df["dup_url"].sum():,})')

# OLD R2
df['r2_old'] = df['company'] + '|' + df['meta.market']
df['dup_r2_old'] = False
unfiltered_r2 = ~df['dup_job_id'] & ~df['dup_r1'] & ~df['dup_url']

for key, group in df[unfiltered_r2].groupby('r2_old'):
    if len(group) > 1:
        df.loc[group.index[1:], 'dup_r2_old'] = True

after_r2_old = len(df[unfiltered_r2 & ~df['dup_r2_old']])

# NEW R2
df['content_hash'] = df['description'].apply(generate_content_hash)
df['r2_new'] = df['company'] + '|' + df['meta.market'] + '|' + df['content_hash']
df['dup_r2_new'] = False

for key, group in df[unfiltered_r2].groupby('r2_new'):
    if len(group) > 1:
        df.loc[group.index[1:], 'dup_r2_new'] = True

after_r2_new = len(df[unfiltered_r2 & ~df['dup_r2_new']])

print(f'OLD R2:    {after_url:>6,} → {after_r2_old:>6,} (-{df["dup_r2_old"].sum():,})')
print(f'NEW R2:    {after_url:>6,} → {after_r2_new:>6,} (-{df["dup_r2_new"].sum():,})')
print()
print('=' * 80)
print(f'OLD R2 final: {after_r2_old:,} jobs ({after_r2_old/len(df)*100:.1f}%)')
print(f'NEW R2 final: {after_r2_new:,} jobs ({after_r2_new/len(df)*100:.1f}%)')
print(f'Difference:   +{after_r2_new - after_r2_old:,} jobs (+{(after_r2_new-after_r2_old)/after_r2_old*100:.1f}%)')
