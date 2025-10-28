#!/usr/bin/env python3
"""
Check recent Google jobs in Supabase to verify AI formatting worked
"""

import os
from supabase import create_client

# Get Supabase credentials
try:
    import streamlit as st
    SUPABASE_URL = st.secrets.get('SUPABASE_URL')
    SUPABASE_ANON_KEY = st.secrets.get('SUPABASE_ANON_KEY')
except:
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

print('🔍 Checking recent Google jobs for AI formatting...')
print('=' * 100)

# Get 5 recent Google jobs with good/so-so match
result = client.table('jobs').select(
    'job_id, job_title, company, source, match_level, job_description, created_at'
).eq('source', 'google').in_('match_level', ['good', 'so-so']).order('created_at', desc=True).limit(5).execute()

jobs = result.data

if not jobs:
    print('❌ No recent Google jobs found')
    exit(1)

print(f'✅ Found {len(jobs)} recent Google jobs\n')

for idx, job in enumerate(jobs, 1):
    job_id = job.get('job_id', '')
    title = job.get('job_title', '')
    company = job.get('company', '')
    match_level = job.get('match_level', '')
    desc = job.get('job_description', '')
    created_at = job.get('created_at', '')

    print(f'\n{"="*100}')
    print(f'JOB {idx}: {title[:60]}...')
    print(f'Company: {company}')
    print(f'Match: {match_level}')
    print(f'Source: google ✅')
    print(f'Created: {created_at}')
    print(f'Job ID: {job_id[:20]}...')
    print(f'{"="*100}\n')

    # Check for HTML formatting
    has_html = '<h3>' in desc or '<ul>' in desc or '<li>' in desc or '<p>' in desc

    if has_html:
        print('✅ AI FORMATTING DETECTED!')

        # Count HTML tags
        h3_count = desc.count('<h3>')
        ul_count = desc.count('<ul>')
        li_count = desc.count('<li>')
        p_count = desc.count('<p>')

        print(f'   HTML tags found:')
        print(f'   - <h3> headings: {h3_count}')
        print(f'   - <ul> lists: {ul_count}')
        print(f'   - <li> items: {li_count}')
        print(f'   - <p> paragraphs: {p_count}')
    else:
        print('⚠️ NO HTML FORMATTING (may be plain text or already had HTML)')

    # Show first 500 chars
    print(f'\n📄 DESCRIPTION PREVIEW (first 500 chars):')
    print('-' * 100)
    preview = desc[:500].replace('\n', ' ')
    print(preview)
    print('-' * 100)

print('\n' + '=' * 100)
print('✅ Check complete')
