#!/usr/bin/env python3
"""
Check job descriptions from different sources for formatting issues
"""

import os
import sys
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

print('🔍 Checking job descriptions from different sources...')
print('=' * 100)

# Get sample jobs from each source
sources = ['google_jobs', 'driver_pulse', 'indeed']

for source in sources:
    print(f'\n📊 SOURCE: {source.upper()}')
    print('-' * 100)

    # Get 3 recent jobs from this source
    result = client.table('jobs').select(
        'job_id, job_title, company, source, job_description, summary'
    ).eq('source', source).order('created_at', desc=True).limit(3).execute()

    jobs = result.data

    if not jobs:
        print(f'⚠️ No jobs found from {source}')
        continue

    print(f'✅ Found {len(jobs)} jobs from {source}\n')

    for idx, job in enumerate(jobs, 1):
        print(f'\n{"="*100}')
        print(f'JOB {idx}: {job["job_title"][:60]}...')
        print(f'Company: {job["company"]}')
        print(f'Job ID: {job["job_id"][:20]}...')
        print(f'{"="*100}\n')

        # Check description
        desc = job.get('job_description', '')
        summary = job.get('summary', '')

        print(f'📝 DESCRIPTION LENGTH: {len(desc)} chars')
        print(f'📝 SUMMARY LENGTH: {len(summary)} chars\n')

        # Check for HTML tags
        if '<' in desc and '>' in desc:
            print('⚠️ HTML TAGS DETECTED in description')
            # Count common tags
            import re
            tags = re.findall(r'<(\w+)[^>]*>', desc)
            tag_counts = {}
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            print(f'   Tags found: {tag_counts}')

        # Check for special characters
        if '\n' in desc:
            print(f'✓ Newlines: {desc.count(chr(10))} found')
        if '\r' in desc:
            print(f'⚠️ Carriage returns: {desc.count(chr(13))} found')
        if '\t' in desc:
            print(f'⚠️ Tabs: {desc.count(chr(9))} found')

        # Check for very long lines
        lines = desc.split('\n')
        max_line_len = max([len(line) for line in lines]) if lines else 0
        if max_line_len > 200:
            print(f'⚠️ VERY LONG LINE: {max_line_len} chars (might cause horizontal scroll)')

        # Show first 500 chars of description
        print(f'\n📄 DESCRIPTION PREVIEW (first 500 chars):')
        print('-' * 100)
        print(desc[:500].replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t'))
        print('-' * 100)

        # Show summary if exists
        if summary:
            print(f'\n📝 AI SUMMARY PREVIEW (first 300 chars):')
            print('-' * 100)
            print(summary[:300].replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t'))
            print('-' * 100)

        print('\n')

print('\n' + '=' * 100)
print('✅ Formatting check complete')
