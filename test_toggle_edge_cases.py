#!/usr/bin/env python3
"""
Test edge cases that might break the toggle functionality
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

print('🧪 Testing edge cases for toggle functionality...')
print('=' * 100)

# Get sample jobs
result = client.table('jobs').select(
    'job_id, job_title, company, job_description'
).order('created_at', desc=True).limit(5).execute()

jobs = result.data

print(f'✅ Testing {len(jobs)} recent jobs\n')

for idx, job in enumerate(jobs, 1):
    job_id = job.get('job_id', '')
    desc = job.get('job_description', '')

    print(f'\nJOB {idx}: {job["job_title"][:50]}...')
    print(f'Job ID: {job_id[:20]}...')
    print('-' * 100)

    # Check for characters that could break JavaScript/HTML
    issues = []

    # 1. Single quotes in description (breaks onclick='...')
    if "'" in desc:
        count = desc.count("'")
        issues.append(f"⚠️ SINGLE QUOTES: {count} found (could break onclick attributes)")

    # 2. Double quotes (breaks onclick="...")
    if '"' in desc:
        count = desc.count('"')
        issues.append(f"⚠️ DOUBLE QUOTES: {count} found (could break HTML attributes)")

    # 3. Backticks (breaks template literals)
    if '`' in desc:
        count = desc.count('`')
        issues.append(f"⚠️ BACKTICKS: {count} found (could break template literals)")

    # 4. Newlines (need to be converted to <br>)
    if '\n' in desc:
        count = desc.count('\n')
        issues.append(f"✓ NEWLINES: {count} found (will be converted to <br>)")

    # 5. Very long descriptions (>10KB)
    if len(desc) > 10000:
        issues.append(f"⚠️ VERY LONG: {len(desc)} chars (might cause rendering lag)")

    # 6. Special HTML entities
    if '&' in desc:
        # Check if they're proper entities or bare ampersands
        import re
        bare_amps = len(re.findall(r'&(?![a-zA-Z]+;)', desc))
        if bare_amps > 0:
            issues.append(f"⚠️ BARE AMPERSANDS: {bare_amps} found (should be &amp;)")

    # 7. Script tags (security risk)
    if '<script' in desc.lower():
        issues.append(f"🚨 SCRIPT TAGS DETECTED (security risk)")

    # 8. Job ID contains special characters
    if "'" in job_id or '"' in job_id or '`' in job_id:
        issues.append(f"🚨 JOB ID HAS SPECIAL CHARS: {job_id}")

    if issues:
        for issue in issues:
            print(issue)
    else:
        print('✅ No issues found')

print('\n' + '=' * 100)
print('✅ Edge case testing complete')
