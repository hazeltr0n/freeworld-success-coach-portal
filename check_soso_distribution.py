#!/usr/bin/env python3
"""
Check the distribution of match_level classifications after recent classifier changes
"""

import os
import sys
import pandas as pd
from supabase import create_client

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    try:
        import streamlit as st
        SUPABASE_URL = st.secrets.get('SUPABASE_URL')
        SUPABASE_ANON_KEY = st.secrets.get('SUPABASE_ANON_KEY')
    except:
        print("❌ Could not load Supabase credentials")
        sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

print("📊 Checking match_level distribution after classifier update...")
print("=" * 80)

# Query last 300 jobs classified recently (after our changes)
result = client.table('jobs').select(
    'job_id, job_title, company, match_level, match_reason, created_at'
).not_.is_('match_level', 'null').order('created_at', desc=True).limit(300).execute()

jobs = result.data
print(f"✅ Retrieved {len(jobs)} recently classified jobs\n")

df = pd.DataFrame(jobs)

# Overall distribution
print("📈 MATCH LEVEL DISTRIBUTION:")
print(df['match_level'].value_counts())
print()

# Calculate percentages
total = len(df)
for level in ['good', 'so-so', 'bad']:
    count = len(df[df['match_level'] == level])
    pct = (count / total * 100) if total > 0 else 0
    print(f"{level:8} {count:4} jobs ({pct:5.1f}%)")

print()
print("=" * 80)

# Show sample of each category
if len(df[df['match_level'] == 'good']) > 0:
    print("\n✅ SAMPLE 'GOOD' JOBS:")
    for idx, (i, job) in enumerate(df[df['match_level'] == 'good'].head(5).iterrows(), 1):
        print(f"{idx}. {job['job_title']} @ {job['company']}")
        print(f"   Reason: {job['match_reason']}")
        print()

if len(df[df['match_level'] == 'so-so']) > 0:
    print("\n⚠️ SAMPLE 'SO-SO' JOBS:")
    for idx, (i, job) in enumerate(df[df['match_level'] == 'so-so'].head(5).iterrows(), 1):
        print(f"{idx}. {job['job_title']} @ {job['company']}")
        print(f"   Reason: {job['match_reason']}")
        print()
else:
    print("\n🚨 NO 'SO-SO' JOBS FOUND!")
    print("   This indicates the classifier is only using 'good' and 'bad' categories")
    print()

if len(df[df['match_level'] == 'bad']) > 0:
    print("\n❌ SAMPLE 'BAD' JOBS:")
    for idx, (i, job) in enumerate(df[df['match_level'] == 'bad'].head(5).iterrows(), 1):
        print(f"{idx}. {job['job_title']} @ {job['company']}")
        print(f"   Reason: {job['match_reason']}")
        print()

print("=" * 80)
print("🔍 DIAGNOSIS:")
print("=" * 80)

soso_count = len(df[df['match_level'] == 'so-so'])
if soso_count == 0:
    print("❌ PROBLEM: Zero 'so-so' classifications found!")
    print()
    print("Possible causes:")
    print("1. Prompt is too binary (only classifying as good or bad)")
    print("2. 'So-so' criteria are too narrow or unclear")
    print("3. LLM is interpreting 'preferred experience' as either good or bad")
    print()
elif soso_count < (total * 0.1):
    print(f"⚠️ WARNING: Only {soso_count} 'so-so' jobs ({soso_count/total*100:.1f}%)")
    print("   Expected at least 10-20% to be 'so-so'")
    print()
else:
    print(f"✅ Healthy distribution: {soso_count} 'so-so' jobs ({soso_count/total*100:.1f}%)")
    print()
