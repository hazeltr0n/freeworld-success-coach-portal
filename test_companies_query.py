#!/usr/bin/env python3
"""
Test Companies Query - Verify so-so jobs are included
"""

from supabase_utils import get_client
import pandas as pd
from datetime import datetime, timezone, timedelta

def test_companies_query():
    """Test that companies query includes both good and so-so jobs"""
    client = get_client()
    if not client:
        print("❌ Supabase client not available")
        return

    # Get cutoff date (last 365 days to find any so-so jobs)
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()

    print("🔍 Testing companies query logic...")
    print(f"📅 Using cutoff date: {cutoff_date}")

    # First, check if there are any so-so jobs at all in the database
    all_so_so = client.table('jobs').select('match_level, created_at').eq('match_level', 'so-so').limit(10).execute()
    print(f"🔍 Found {len(all_so_so.data or [])} so-so jobs in entire database")

    if all_so_so.data:
        print("Sample so-so job dates:")
        for job in all_so_so.data[:5]:
            date_str = job.get('created_at', 'No date')
            print(f"   - {date_str}")

        # Check if these dates are really in the future
        print(f"\n📅 Current date: {datetime.now(timezone.utc).isoformat()}")
        print(f"📅 Cutoff date: {cutoff_date}")

        # Get so-so jobs without date filter to see them all
        no_filter_result = client.table('jobs').select(
            'company, created_at, match_level'
        ).eq('match_level', 'so-so').limit(50).execute()

        print(f"\n🔍 All so-so jobs without date filter: {len(no_filter_result.data or [])}")
        for job in (no_filter_result.data or [])[:10]:
            print(f"   - {job.get('company', 'Unknown')}: {job.get('created_at', 'No date')}")

    # Test the exact query used in companies rollup
    result = client.table('jobs').select(
        'company, location, job_title, match_level, route_type, fair_chance, salary, created_at, success_coach'
    ).gte('created_at', cutoff_date).in_('match_level', ['good', 'so-so']).execute()

    jobs_data = result.data or []
    print(f"📊 Found {len(jobs_data)} jobs with good/so-so quality")

    if jobs_data:
        df = pd.DataFrame(jobs_data)

        # Analyze match levels
        match_level_counts = df['match_level'].value_counts()
        print("\n📈 Match Level Distribution:")
        for level, count in match_level_counts.items():
            print(f"   {level}: {count} jobs")

        # Check unique companies
        companies = df['company'].nunique()
        print(f"\n🏢 Unique companies: {companies}")

        # Sample companies with so-so jobs
        so_so_jobs = df[df['match_level'] == 'so-so']
        if not so_so_jobs.empty:
            print(f"\n✅ Found {len(so_so_jobs)} so-so jobs from {so_so_jobs['company'].nunique()} companies")
            print("Sample so-so companies:")
            for company in so_so_jobs['company'].unique()[:5]:
                count = len(so_so_jobs[so_so_jobs['company'] == company])
                print(f"   - {company}: {count} so-so jobs")
        else:
            print("\n⚠️ No so-so jobs found!")

        # Test market extraction
        from companies_rollup import extract_market_from_location
        print(f"\n🗺️ Testing market extraction on sample locations:")
        sample_locations = df['location'].dropna().unique()[:10]
        for location in sample_locations:
            market = extract_market_from_location(location)
            print(f"   {location} → {market}")

    else:
        print("❌ No jobs found matching criteria")

if __name__ == "__main__":
    test_companies_query()