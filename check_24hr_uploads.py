#!/usr/bin/env python3
"""
Check how many jobs have been uploaded to Supabase in the last 24 hours.
"""

import os
import sys
from datetime import datetime, timedelta
from supabase import create_client
import pytz

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

# Get current time in UTC (Supabase stores timestamps in UTC)
now_utc = datetime.now(pytz.UTC)
twenty_four_hours_ago = now_utc - timedelta(hours=24)

print("📊 Checking jobs uploaded in the last 24 hours...")
print("=" * 80)
print(f"Current time (UTC): {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"24 hours ago (UTC): {twenty_four_hours_ago.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print()

# Query jobs created in the last 24 hours
# Using ISO 8601 format for the timestamp filter
cutoff_time = twenty_four_hours_ago.isoformat()

result = client.table('jobs').select('job_id, job_title, company, match_level, created_at', count='exact').gte('created_at', cutoff_time).execute()

jobs_24hr = result.data
total_count = result.count if hasattr(result, 'count') else len(jobs_24hr)

print(f"✅ Total jobs uploaded in last 24 hours: {total_count}")
print()

if total_count > 0:
    # Break down by match level
    import pandas as pd
    df = pd.DataFrame(jobs_24hr)

    print("📈 Breakdown by match level:")
    if 'match_level' in df.columns:
        match_counts = df['match_level'].value_counts()
        for level in ['good', 'so-so', 'bad']:
            count = match_counts.get(level, 0)
            pct = (count / total_count * 100) if total_count > 0 else 0
            print(f"  {level:8} {count:4} jobs ({pct:5.1f}%)")
    print()

    # Show sample of recent uploads
    print("📋 Sample of most recent uploads (last 10):")
    recent = sorted(jobs_24hr, key=lambda x: x['created_at'], reverse=True)[:10]
    for idx, job in enumerate(recent, 1):
        created_time = datetime.fromisoformat(job['created_at'].replace('Z', '+00:00'))
        time_ago = now_utc - created_time
        hours_ago = time_ago.total_seconds() / 3600

        print(f"{idx:2}. {job['job_title'][:50]:<50} @ {job['company'][:30]:<30}")
        print(f"    Match: {job.get('match_level', 'unknown'):6} | {hours_ago:.1f}h ago")
        print()
else:
    print("⚠️ No jobs uploaded in the last 24 hours")

print("=" * 80)
