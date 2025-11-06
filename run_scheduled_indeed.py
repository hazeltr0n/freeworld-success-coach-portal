#!/usr/bin/env python3
"""
Scheduled Indeed Multi-Market Scraper
Runs Mon/Wed/Fri at 2am Central

10 Markets × 4 Search Terms × 250 jobs = ~10,000 total searches
Uses EXACT same logic as main search page multi-market mode
"""

import sys
from datetime import datetime, timezone
from pipeline_wrapper import StreamlitPipelineWrapper

# Hardcoded configuration
MARKETS = [
    "Dallas",
    "Houston",
    "Phoenix",
    "Trenton",
    "Newark",
    "Denver",
    "Inland Empire",
    "Bay Area",
    "Stockton",
    "Las Vegas"
]

SEARCH_TERMS = [
    "CDL Driver",
    "Class A Driver",
    "Class B Driver",
    "Local CDL Home Daily"
]

JOBS_PER_SEARCH = 500  # Display only - actual limit controlled by mode ('large' = 500)

def main():
    """Run multi-market Indeed searches"""
    print(f"\n{'='*80}")
    print(f"🚛 SCHEDULED INDEED MULTI-MARKET SCRAPER")
    print(f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*80}\n")

    print(f"📍 Markets: {len(MARKETS)}")
    for market in MARKETS:
        print(f"   • {market}")

    print(f"\n🔍 Search Terms: {len(SEARCH_TERMS)}")
    for term in SEARCH_TERMS:
        print(f"   • {term}")

    print(f"\n📊 Configuration:")
    print(f"   Jobs per search: {JOBS_PER_SEARCH}")
    print(f"   Total searches: {len(MARKETS)} markets × {len(SEARCH_TERMS)} terms = {len(MARKETS) * len(SEARCH_TERMS)} searches")
    print(f"   Expected jobs: ~{len(MARKETS) * len(SEARCH_TERMS) * JOBS_PER_SEARCH:,}")

    # Market names only - terminal script handles location mapping internally
    # No need for MARKET_TO_LOCATION map anymore

    # Track overall stats
    total_jobs_found = 0
    total_quality_jobs = 0
    successful_searches = 0
    failed_searches = 0

    # Run searches for each term across all markets
    for search_term in SEARCH_TERMS:
        print(f"\n{'='*80}")
        print(f"🔍 SEARCH TERM: {search_term}")
        print(f"{'='*80}\n")

        for market in MARKETS:
            print(f"   📍 {market}")

            try:
                # Initialize pipeline
                pipeline = StreamlitPipelineWrapper()

                # Build parameters (same as main search page Indeed Fresh Only mode)
                params = {
                    'mode': 'large',  # 500 jobs per search
                    'market': market,  # JUST THE MARKET NAME - terminal script handles location mapping
                    'search_terms': search_term,
                    'search_radius': 50,
                    'exact_location': False,
                    'force_fresh': True,  # Force fresh Indeed search
                    'force_fresh_classification': False,
                    'no_experience': True,  # Entry-level friendly
                    'memory_only': False,
                    'search_sources': {'indeed': True, 'google': False},  # Indeed only
                    'search_strategy': 'fresh_first',
                    'push_to_airtable': False,
                    'generate_pdf': False,
                    'generate_csv': False,
                    'generate_html': False,
                    'candidate_id': '',
                    'candidate_name': '',
                    'coach_username': 'scheduled_indeed'
                }

                # Run the pipeline
                df, metadata = pipeline.run_pipeline(params)

                if metadata.get('success', False) and df is not None and not df.empty:
                    job_count = len(df)
                    quality_count = len(df[df.get('ai.match', '').isin(['good', 'so-so'])]) if 'ai.match' in df.columns else 0

                    total_jobs_found += job_count
                    total_quality_jobs += quality_count
                    successful_searches += 1

                    print(f"      ✅ {job_count} jobs ({quality_count} quality)")
                else:
                    print(f"      ⚠️  No jobs found")
                    failed_searches += 1

            except Exception as e:
                print(f"      ❌ Error: {e}")
                failed_searches += 1
                continue

    # Final summary
    print(f"\n{'='*80}")
    print(f"✅ SCRAPE COMPLETE")
    print(f"{'='*80}")
    print(f"   Successful searches: {successful_searches}/{len(MARKETS) * len(SEARCH_TERMS)}")
    print(f"   Failed searches: {failed_searches}")
    print(f"   Total jobs found: {total_jobs_found:,}")
    print(f"   Quality jobs (good/so-so): {total_quality_jobs:,}")
    print(f"{'='*80}\n")

    # Exit with error code if too many failures
    failure_rate = failed_searches / (len(MARKETS) * len(SEARCH_TERMS))
    if failure_rate > 0.5:
        print(f"⚠️  High failure rate ({failure_rate:.1%}), exiting with error code")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
