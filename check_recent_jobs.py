#!/usr/bin/env python3
"""Check how many jobs have been added to Supabase in the last 7 days"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase_utils import get_client

load_dotenv()

client = get_client()

print("=" * 80)
print("JOBS ADDED TO SUPABASE - LAST 7 DAYS")
print("=" * 80)

# Calculate the date 7 days ago
seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()

# Query jobs created in the last 7 days
result = client.table('jobs').select('*', count='exact').gte('created_at', seven_days_ago).execute()

total_jobs = result.count if result.count else 0

print(f"\n📊 Total jobs added in last 7 days: {total_jobs:,}")

# Get breakdown by match level
match_breakdown = client.table('jobs').select('match_level', count='exact').gte('created_at', seven_days_ago).execute()

# Count by match level
good_count = client.table('jobs').select('*', count='exact').gte('created_at', seven_days_ago).eq('match_level', 'good').execute().count or 0
so_so_count = client.table('jobs').select('*', count='exact').gte('created_at', seven_days_ago).eq('match_level', 'so-so').execute().count or 0
bad_count = client.table('jobs').select('*', count='exact').gte('created_at', seven_days_ago).eq('match_level', 'bad').execute().count or 0

print(f"\n📈 Breakdown by match level:")
print(f"  ✅ Good: {good_count:,}")
print(f"  ⚠️  So-so: {so_so_count:,}")
print(f"  ❌ Bad: {bad_count:,}")

# Get breakdown by market
print(f"\n🗺️  Breakdown by market:")
markets_result = client.table('jobs').select('market', count='exact').gte('created_at', seven_days_ago).execute()

if markets_result.data:
    from collections import Counter
    market_counts = Counter(job.get('market', 'Unknown') for job in markets_result.data if job.get('market'))

    for market, count in market_counts.most_common(10):
        print(f"  {market}: {count:,}")

# Get daily breakdown
print(f"\n📅 Daily breakdown:")
for i in range(7):
    day_start = (datetime.now() - timedelta(days=i+1)).replace(hour=0, minute=0, second=0).isoformat()
    day_end = (datetime.now() - timedelta(days=i)).replace(hour=0, minute=0, second=0).isoformat()

    day_count = client.table('jobs').select('*', count='exact').gte('created_at', day_start).lt('created_at', day_end).execute().count or 0

    day_date = (datetime.now() - timedelta(days=i+1)).strftime('%Y-%m-%d')
    print(f"  {day_date}: {day_count:,} jobs")

print("\n" + "=" * 80)
