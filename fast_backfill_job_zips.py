#!/usr/bin/env python3
"""
FAST Backfill ZIP codes for existing jobs using location_markets table

Optimized strategy:
1. Process jobs in small batches to avoid timeout
2. Use pagination to chunk through the jobs table
3. Update immediately as we find matches
"""

import sys
from supabase import create_client

def get_client():
    """Get Supabase client from secrets"""
    with open('.streamlit/secrets.toml', 'r') as f:
        secrets = {}
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                secrets[key.strip()] = value.strip().strip('"')

    return create_client(secrets['SUPABASE_URL'], secrets['SUPABASE_ANON_KEY'])


def fast_backfill():
    """Backfill ZIPs in optimized batches"""
    client = get_client()

    # Load location_markets ONCE
    print("🗺️  Loading location_markets table...")
    markets_result = client.table('location_markets').select('location_string, default_zips').execute()

    # Build lookup map: location -> first_zip
    location_map = {}
    for row in markets_result.data:
        location = row['location_string'].lower().strip()
        zips = row.get('default_zips', [])
        if zips:
            location_map[location] = zips[0]  # Use first ZIP

    print(f"📍 Loaded {len(location_map):,} location→ZIP mappings\n")

    # Process in small batches
    batch_size = 1000
    offset = 0
    total_updated = 0
    total_processed = 0

    while True:
        print(f"📦 Fetching batch at offset {offset}...")

        # Get batch of jobs without ZIP
        jobs_result = client.table('jobs') \
            .select('job_id, location') \
            .is_('zip_code', 'null') \
            .range(offset, offset + batch_size - 1) \
            .execute()

        jobs = jobs_result.data

        if not jobs:
            print("✅ No more jobs to process!")
            break

        print(f"   Processing {len(jobs)} jobs...")

        # Update jobs that match
        updated_this_batch = 0
        for job in jobs:
            location = job.get('location', '').lower().strip()

            if location in location_map:
                zip_code = location_map[location]

                # Update immediately
                client.table('jobs').update({
                    'zip_code': zip_code
                }).eq('job_id', job['job_id']).execute()

                updated_this_batch += 1

        total_updated += updated_this_batch
        total_processed += len(jobs)

        print(f"   ✅ Updated {updated_this_batch}/{len(jobs)} jobs in this batch")
        print(f"   📊 Total: {total_updated:,} updated out of {total_processed:,} processed\n")

        # If batch was smaller than batch_size, we're done
        if len(jobs) < batch_size:
            break

        offset += batch_size

    print(f"\n📊 Final Results:")
    print(f"   Total Processed: {total_processed:,}")
    print(f"   Total Updated: {total_updated:,}")

    # Final coverage check
    all_jobs = client.table('jobs').select('job_id, zip_code').execute()
    total = len(all_jobs.data)
    with_zip = sum(1 for job in all_jobs.data if job.get('zip_code'))

    print(f"\n📍 Jobs Table ZIP Coverage:")
    print(f"   Total Jobs: {total:,}")
    print(f"   With ZIP: {with_zip:,} ({with_zip/total*100:.1f}%)")
    print(f"   Without ZIP: {total - with_zip:,} ({(total-with_zip)/total*100:.1f}%)")


if __name__ == "__main__":
    print("🚀 Starting FAST jobs table ZIP backfill...\n")
    fast_backfill()
    print("\n✅ Complete!")
