#!/usr/bin/env python3
"""Check the most recent job upload"""

from supabase_utils import get_client
from datetime import datetime

client = get_client()

# Get the most recent job
result = client.table('jobs').select('*').order('created_at', desc=True).limit(10).execute()

if result.data:
    print("🔍 Most recent job uploads:\n")
    for i, job in enumerate(result.data[:10], 1):
        created = job.get('created_at', 'NO TIMESTAMP')
        match = job.get('match_level', 'NO MATCH')
        company = job.get('company', 'NO COMPANY')[:30]
        job_id = job.get('job_id', 'NO ID')[:16]

        print(f"{i}. {created} | {match:6s} | {company:30s} | {job_id}...")

    # Parse the most recent timestamp
    most_recent = result.data[0].get('created_at')
    print(f"\n📅 Most recent upload: {most_recent}")

    # Calculate time difference
    if most_recent:
        from dateutil import parser
        created_dt = parser.parse(most_recent)
        now = datetime.now(created_dt.tzinfo)
        diff = now - created_dt

        hours = diff.total_seconds() / 3600
        print(f"⏰ Time since last upload: {hours:.1f} hours ago")
else:
    print("❌ No jobs found in database")
