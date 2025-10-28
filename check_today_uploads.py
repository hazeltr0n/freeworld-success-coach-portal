#!/usr/bin/env python3
"""Check jobs uploaded today"""

import os
from datetime import datetime, timedelta
from supabase_utils import get_client

client = get_client()

# Check jobs added in the last 2 hours
two_hours_ago = (datetime.now() - timedelta(hours=2)).isoformat()

result = client.table('jobs').select('*', count='exact').gte('created_at', two_hours_ago).execute()

print(f"📊 Jobs uploaded in last 2 hours: {result.count or 0}")

if result.data and len(result.data) > 0:
    # Show match level breakdown
    from collections import Counter
    match_counts = Counter(job.get('match_level', 'Unknown') for job in result.data)
    print(f"\n📈 Match level breakdown:")
    for level, count in match_counts.most_common():
        print(f"  {level}: {count}")

    # Show first few job IDs
    print(f"\n🔍 Sample job IDs:")
    for job in result.data[:5]:
        print(f"  {job.get('job_id', 'NO ID')[:16]}... | {job.get('match_level', 'NO MATCH')} | {job.get('company', 'NO COMPANY')}")
else:
    print("\n❌ No jobs uploaded in the last 2 hours")
