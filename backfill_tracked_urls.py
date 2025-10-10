#!/usr/bin/env python3
"""
Backfill tracked URLs for quality jobs that don't have them
"""
import os
import toml
from datetime import datetime, timedelta
from supabase_utils import get_client
from link_tracker import LinkTracker

# Load secrets
secrets_path = ".streamlit/secrets.toml"
if os.path.exists(secrets_path):
    secrets = toml.load(secrets_path)
    for key, value in secrets.items():
        if isinstance(value, (str, int, float, bool)):
            os.environ[key] = str(value)

def backfill_tracked_urls():
    """Find quality jobs without tracked URLs and generate them"""

    print("🔗 Backfilling Tracked URLs for Quality Jobs")
    print("=" * 60)

    # Initialize clients
    client = get_client()
    tracker = LinkTracker()

    if not tracker.is_available:
        print("❌ LinkTracker not available - cannot generate URLs")
        return

    print(f"✅ LinkTracker available (Supabase Edge Function: {tracker.use_supabase_edge_function})")

    # Get today's date
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    print(f"📅 Searching for jobs from today ({today_start})")

    # Query for quality jobs without tracked URLs
    result = client.table('jobs').select(
        'job_id, job_title, company, location, apply_url, match_level, source, success_coach, created_at'
    ).gte('created_at', today_start).in_('match_level', ['good', 'so-so']).execute()

    if not result.data:
        print("✅ No jobs found from today")
        return

    print(f"📊 Found {len(result.data)} quality jobs from today")

    # Filter to only those without tracked URLs
    jobs_without_urls = []
    for job in result.data:
        # Query individual job for tracked_url (some fields may not be in select)
        job_detail = client.table('jobs').select('job_id, tracked_url').eq('job_id', job['job_id']).execute()
        if job_detail.data and not job_detail.data[0].get('tracked_url'):
            jobs_without_urls.append(job)

    print(f"🔍 Found {len(jobs_without_urls)} quality jobs WITHOUT tracked URLs")

    if len(jobs_without_urls) == 0:
        print("✅ All quality jobs already have tracked URLs!")
        return

    print()

    # Generate tracked URLs
    url_updates = {}
    successful = 0
    failed = 0

    for i, job in enumerate(jobs_without_urls, 1):
        job_id = job['job_id']
        original_url = job.get('apply_url', '')
        job_title = job.get('job_title', 'CDL Position')[:50]
        location = job.get('location', 'Unknown')[:30]
        coach = job.get('success_coach', '')
        source = job.get('source', 'unknown')

        if not original_url or len(original_url) < 10:
            print(f"⏭️  [{i}/{len(jobs_without_urls)}] {job_id[:8]}: No valid URL")
            failed += 1
            continue

        # Generate tags
        tags = []
        if coach:
            tags.append(f"coach:{coach}")
        if source:
            tags.append(f"source:{source}")
        tags.append(f"backfill:{datetime.utcnow().strftime('%Y%m%d')}")

        try:
            tracked_url = tracker.create_short_link(
                original_url,
                title=f"{job_title} - {location}",
                tags=tags
            )

            if tracked_url and tracked_url != original_url:
                url_updates[job_id] = tracked_url
                successful += 1
                print(f"✅ [{i}/{len(jobs_without_urls)}] {job_id[:8]}: {tracked_url}")
            else:
                print(f"⚠️  [{i}/{len(jobs_without_urls)}] {job_id[:8]}: Link generation returned original URL")
                failed += 1

        except Exception as e:
            print(f"❌ [{i}/{len(jobs_without_urls)}] {job_id[:8]}: {e}")
            failed += 1

    print()
    print(f"📊 Results: {successful} successful, {failed} failed")

    # Update Supabase
    if url_updates:
        print()
        print(f"💾 Updating {len(url_updates)} tracked URLs in Supabase...")

        updated_count = 0
        for job_id, tracked_url in url_updates.items():
            try:
                client.table('jobs').update({
                    'tracked_url': tracked_url,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('job_id', job_id).execute()
                updated_count += 1
            except Exception as e:
                print(f"❌ Failed to update {job_id[:8]}: {e}")

        print(f"✅ Updated {updated_count}/{len(url_updates)} jobs in Supabase")

    print()
    print("🎉 Backfill complete!")

if __name__ == "__main__":
    backfill_tracked_urls()
