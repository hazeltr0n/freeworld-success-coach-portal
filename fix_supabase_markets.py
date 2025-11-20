#!/usr/bin/env python3
"""
Fix incorrectly assigned markets in Supabase jobs table
Moves Texas jobs from Bay Area to Dallas
"""

from supabase_utils import get_client

client = get_client()

print('🔍 Finding Texas jobs incorrectly assigned to Bay Area...')

# Get Bay Area jobs
result = client.table('jobs').select('job_id, market, location, job_title, source').eq('market', 'Bay Area').limit(5000).execute()

bay_area_jobs = result.data
print(f'Total Bay Area jobs: {len(bay_area_jobs)}')

# Filter to Texas locations
texas_jobs = []
for job in bay_area_jobs:
    location = (job.get('location') or '').upper()
    if 'DALLAS' in location or 'FORT WORTH' in location or ', TX' in location:
        texas_jobs.append(job)

print(f'\n🚨 Found {len(texas_jobs)} Texas jobs in Bay Area market')

if not texas_jobs:
    print('Nothing to fix!')
    exit(0)

# Show breakdown
from collections import Counter
sources = Counter(job.get('source', 'unknown') for job in texas_jobs)
print(f'By source: {dict(sources)}')

print('\nSample jobs to be fixed:')
for job in texas_jobs[:5]:
    print(f"  {job.get('job_title', 'N/A')[:50]}")
    print(f"    Location: {job.get('location', 'N/A')}")
    print(f"    Source: {job.get('source', 'N/A')}")

# Ask confirmation
response = input(f'\nUpdate {len(texas_jobs)} jobs from "Bay Area" to "Dallas"? (yes/no): ')
if response.lower() != 'yes':
    print('Aborted')
    exit(0)

# Update in batches
print(f'\n📝 Updating {len(texas_jobs)} jobs...')
updated = 0
failed = 0

for job in texas_jobs:
    try:
        client.table('jobs').update({'market': 'Dallas'}).eq('job_id', job['job_id']).execute()
        updated += 1
        if updated % 10 == 0:
            print(f'  Progress: {updated}/{len(texas_jobs)}')
    except Exception as e:
        print(f'  ❌ Failed to update job_id {job["job_id"]}: {e}')
        failed += 1

print(f'\n✅ Updated {updated} jobs')
if failed:
    print(f'❌ Failed: {failed} jobs')

# Verify
print('\n🔍 Verifying...')
result = client.table('jobs').select('job_id, market, location').eq('market', 'Bay Area').limit(5000).execute()
remaining_texas = sum(1 for job in result.data if 'TX' in (job.get('location') or '').upper())

if remaining_texas == 0:
    print('✅ All Texas jobs moved to Dallas market!')
else:
    print(f'⚠️  Still {remaining_texas} Texas jobs in Bay Area - may need another run')
