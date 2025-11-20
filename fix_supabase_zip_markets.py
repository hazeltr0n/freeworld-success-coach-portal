#!/usr/bin/env python3
"""
Fix Supabase jobs that have ZIP codes as market names
Maps them to the correct market based on state/location
"""

from supabase_utils import get_client
from collections import Counter
import re

# ZIP to correct market mapping based on state
ZIP_TO_CORRECT_MARKET = {
    # California
    '93263': 'Inland Empire',   # Bakersfield, CA
    '94203': 'Stockton',        # Sacramento/Stockton area
    '95210': 'Stockton',        # Stockton, CA
    '95820': 'Stockton',        # Sacramento, CA (nearest)

    # Texas
    '79404': 'Dallas',          # Lubbock, TX (closest market)
    '76701': 'Dallas',          # Waco, TX (closest market)

    # New Jersey
    '08016': 'Trenton',         # Burlington Township, NJ

    # Washington - Not in our market area
    '99181': None,              # Spokane, WA - will mark for review
}

def extract_state_from_location(location: str) -> str:
    """Extract state from location string like 'City, ST'"""
    if not location:
        return ''

    match = re.search(r',\s*([A-Z]{2})', location)
    if match:
        return match.group(1)

    # Try end of string
    parts = location.split()
    if parts and len(parts[-1]) == 2:
        return parts[-1]

    return ''

def get_correct_market(zip_code: str, location: str) -> str:
    """Get the correct market for a job with ZIP code as market"""

    # Check explicit mapping first
    if zip_code in ZIP_TO_CORRECT_MARKET:
        return ZIP_TO_CORRECT_MARKET[zip_code]

    # Fall back to state-based assignment
    state = extract_state_from_location(location)

    state_to_market = {
        'TX': 'Dallas',
        'CA': 'Stockton',  # Default California market
        'NJ': 'Newark',
        'AZ': 'Phoenix',
        'CO': 'Denver',
        'NV': 'Las Vegas',
        'PA': 'Newark',     # Nearby NJ market for PA
    }

    return state_to_market.get(state, None)

def main():
    client = get_client()

    print('🔍 Finding jobs with ZIP code markets...')

    # Get all jobs
    result = client.table('jobs').select('job_id, market, location, source, created_at').limit(25000).execute()

    # Filter to ZIP code markets
    zip_market_jobs = []
    for job in result.data:
        market = job.get('market', '')
        if market and market.isdigit() and len(market) == 5:
            zip_market_jobs.append(job)

    print(f'Found {len(zip_market_jobs)} jobs with ZIP code markets')

    # Group by ZIP and calculate fixes
    fixes = []
    no_market = []

    for job in zip_market_jobs:
        zip_code = job.get('market')
        location = job.get('location', '')
        job_id = job.get('job_id')

        correct_market = get_correct_market(zip_code, location)

        if correct_market:
            fixes.append({
                'job_id': job_id,
                'old_market': zip_code,
                'new_market': correct_market,
                'location': location
            })
        else:
            no_market.append(job)

    print(f'\nPlan:')
    print(f'  ✅ Will fix: {len(fixes)} jobs')
    print(f'  ⚠️  No market (out of area): {len(no_market)} jobs')

    if fixes:
        # Group by transition
        transitions = Counter((f['old_market'], f['new_market']) for f in fixes)
        print(f'\nTransitions:')
        for (old, new), count in transitions.most_common():
            print(f'  {old} → {new}: {count} jobs')

    if no_market:
        print(f'\nJobs without a valid market (will skip):')
        for job in no_market[:5]:
            print(f'  Market: {job.get("market")} | Location: {job.get("location")}')

    # Ask confirmation
    response = input(f'\nUpdate {len(fixes)} jobs? (yes/no): ')
    if response.lower() != 'yes':
        print('Aborted')
        return

    # Apply fixes
    print(f'\n📝 Updating {len(fixes)} jobs...')
    updated = 0
    failed = 0

    for fix in fixes:
        try:
            client.table('jobs').update({'market': fix['new_market']}).eq('job_id', fix['job_id']).execute()
            updated += 1
            if updated % 20 == 0:
                print(f'  Progress: {updated}/{len(fixes)}')
        except Exception as e:
            print(f'  ❌ Failed {fix["job_id"]}: {e}')
            failed += 1

    print(f'\n✅ Updated {updated} jobs')
    if failed:
        print(f'❌ Failed: {failed} jobs')

    # Verify
    print(f'\n🔍 Verifying...')
    result = client.table('jobs').select('job_id, market').limit(25000).execute()
    remaining = sum(1 for job in result.data if job.get('market', '').isdigit() and len(job.get('market', '')) == 5)

    if remaining == 0:
        print('✅ No jobs with ZIP code markets remaining!')
    else:
        print(f'⚠️  {remaining} jobs with ZIP code markets remaining')

if __name__ == '__main__':
    main()
