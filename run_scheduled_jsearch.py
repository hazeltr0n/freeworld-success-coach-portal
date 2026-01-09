#!/usr/bin/env python3
"""
Scheduled JSearch (Google Jobs) Multi-Market Scraper
Runs Tue/Thu/Sat at 2am Central via GitHub Actions

Uses OpenWeb Ninja's JSearch API as Google Jobs source
12 Markets × 1 Search Term × 20 pages × 50mi radius = ~2,000 jobs total

JSearch's radius actually works, so we only need one query per market.
"""

import os
import sys
import uuid
from datetime import datetime, timezone

# Import JSearch adapter
from jsearch_adapter import JSearchAdapter, transform_jsearch_to_canonical

# Import pipeline components
from pipeline_v3 import FreeWorldPipelineV3 as PipelineV3
from canonical_transforms import (
    transform_normalize,
    transform_business_rules,
    apply_market_assignment
)
from send_scrape_notification import (
    collect_job_stats_from_dataframe,
    send_detailed_scrape_report
)

# Market configuration - same as Indeed for consistency
# TODO: Restore full list after testing
MARKETS = [
    "Dallas, TX",
    # "Houston, TX",
    # "Phoenix, AZ",
    # "Trenton, NJ",
    # "Newark, NJ",
    # "Denver, CO",
    # "Ontario, CA",      # Inland Empire
    # "Berkeley, CA",     # Bay Area
    # "Stockton, CA",
    # "Las Vegas, NV",
    # "San Antonio, TX",
    # "Austin, TX"
]

# Market display names for reports
MARKET_DISPLAY_NAMES = {
    "Dallas, TX": "Dallas",
    "Houston, TX": "Houston",
    "Phoenix, AZ": "Phoenix",
    "Trenton, NJ": "Trenton",
    "Newark, NJ": "Newark",
    "Denver, CO": "Denver",
    "Ontario, CA": "Inland Empire",
    "Berkeley, CA": "Bay Area",
    "Stockton, CA": "Stockton",
    "Las Vegas, NV": "Las Vegas",
    "San Antonio, TX": "San Antonio",
    "Austin, TX": "Austin"
}

# Single search term - JSearch radius actually works, so no need for multiple terms
SEARCH_TERM = "CDL Driver"

# JSearch config
PAGES_PER_SEARCH = 20  # Max allowed by JSearch API (200 jobs max per query)
RADIUS_MILES = 50      # 50 mile radius - JSearch honors this
DATE_POSTED = "week"   # Jobs from last 7 days


def main():
    """Run multi-market JSearch Google Jobs scrapes"""
    print(f"\n{'='*80}")
    print(f"🔍 SCHEDULED JSEARCH (GOOGLE JOBS) MULTI-MARKET SCRAPER")
    print(f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*80}\n")

    print(f"📍 Markets: {len(MARKETS)}")
    for market in MARKETS:
        display_name = MARKET_DISPLAY_NAMES.get(market, market)
        print(f"   • {display_name} ({market})")

    print(f"\n🔍 Search Term: {SEARCH_TERM}")
    print(f"   (JSearch radius works, so single term per market is sufficient)")

    print(f"\n📊 Configuration:")
    print(f"   Pages per search: {PAGES_PER_SEARCH} (max 10 jobs/page)")
    print(f"   Radius: {RADIUS_MILES} miles")
    print(f"   Date filter: {DATE_POSTED}")
    print(f"   Total searches: {len(MARKETS)} markets × 1 term = {len(MARKETS)}")
    print(f"   Expected jobs: ~{len(MARKETS) * PAGES_PER_SEARCH * 8:,} (assuming 8 jobs/page avg)")

    # Initialize JSearch adapter
    try:
        adapter = JSearchAdapter()
        print(f"\n✅ JSearch API initialized")
    except Exception as e:
        print(f"\n❌ Failed to initialize JSearch: {e}")
        sys.exit(1)

    # Track stats
    total_raw_jobs = 0
    total_classified_jobs = 0
    total_quality_jobs = 0
    all_jobs_dfs = []
    run_id = str(uuid.uuid4())[:8]

    # Initialize pipeline for classification
    print(f"\n🔧 Initializing Pipeline v3 (run_id: {run_id})...")
    pipeline = PipelineV3()
    pipeline.run_id = run_id

    # Search each market (single term per market since radius works)
    print(f"\n{'='*80}")
    print(f"🚀 STARTING JSEARCH SCRAPES")
    print(f"{'='*80}\n")

    for market in MARKETS:
        display_name = MARKET_DISPLAY_NAMES.get(market, market)
        query = f"{SEARCH_TERM} {market}"

        try:
            # Search JSearch API
            jobs = adapter.search_jobs(
                query=query,
                num_pages=PAGES_PER_SEARCH,
                date_posted=DATE_POSTED,
                radius_km=int(RADIUS_MILES * 1.6)  # Convert to km
            )

            if not jobs:
                print(f"📍 {display_name}: ⚠️ 0 jobs")
                continue

            print(f"📍 {display_name}: ✅ {len(jobs)} jobs")
            total_raw_jobs += len(jobs)

            # Transform to canonical format
            df = transform_jsearch_to_canonical(
                raw_data=jobs,
                run_id=run_id,
                search_location=market,
                market=display_name
            )

            if not df.empty:
                all_jobs_dfs.append(df)

        except Exception as e:
            print(f"📍 {display_name}: ❌ Error - {e}")

    # Combine all DataFrames
    if not all_jobs_dfs:
        print(f"\n❌ No jobs found from any market")
        sys.exit(1)

    import pandas as pd
    combined_df = pd.concat(all_jobs_dfs, ignore_index=True)
    print(f"\n📊 Combined: {len(combined_df)} total jobs from all searches")

    # Run through pipeline stages
    print(f"\n{'='*80}")
    print(f"🔄 RUNNING PIPELINE CLASSIFICATION")
    print(f"{'='*80}\n")

    try:
        # Stage 2: Normalization
        print("📐 Stage 2: Normalizing...")
        df_normalized = transform_normalize(combined_df)
        print(f"   ✅ Normalized {len(df_normalized)} jobs")

        # Stage 3: Business Rules
        print("📋 Stage 3: Applying business rules...")
        df_rules = transform_business_rules(df_normalized)
        print(f"   ✅ Applied rules to {len(df_rules)} jobs")

        # Stage 4: Deduplication
        print("🔄 Stage 4: Deduplicating...")
        df_deduped = pipeline._stage4_deduplication(df_rules)
        dedup_removed = len(df_rules) - len(df_deduped[~df_deduped['route.final_status'].str.startswith('filtered:', na=False)])
        print(f"   ✅ Deduplicated (removed ~{dedup_removed} duplicates)")

        # Stage 5: AI Classification
        print("🤖 Stage 5: AI Classification...")
        df_classified = pipeline._stage5_ai_classification(df_deduped)
        total_classified_jobs = len(df_classified)

        # Count quality jobs
        if 'ai.match' in df_classified.columns:
            quality_mask = df_classified['ai.match'].isin(['good', 'so-so'])
            total_quality_jobs = quality_mask.sum()
        print(f"   ✅ Classified {total_classified_jobs} jobs ({total_quality_jobs} quality)")

        # Stage 6: Routing
        print("🎯 Stage 6: Routing...")
        df_routed = pipeline._stage6_routing(df_classified, route_filter='both')
        print(f"   ✅ Routed {len(df_routed)} jobs")

        # Stage 7: Link Tracking
        print("🔗 Stage 7: Generating tracked links...")
        df_tracked = pipeline._stage7_link_tracking(df_routed, coach_username='scheduled_jsearch')
        tracked_count = (df_tracked['meta.tracked_url'].notna() & (df_tracked['meta.tracked_url'] != '')).sum()
        print(f"   ✅ Generated {tracked_count} tracked links")

        # Stage 8: Storage
        print("💾 Stage 8: Storing to Supabase...")
        upload_count = pipeline._stage8_storage(df_tracked)
        print(f"   ✅ Uploaded {upload_count} jobs to Supabase")

        final_df = df_tracked

    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Final summary
    print(f"\n{'='*80}")
    print(f"✅ JSEARCH SCRAPE COMPLETE")
    print(f"{'='*80}")
    print(f"   Markets searched: {len(MARKETS)}")
    print(f"   Search term: {SEARCH_TERM}")
    print(f"   Radius: {RADIUS_MILES} miles")
    print(f"   Total API queries: {len(MARKETS)}")
    print(f"   Raw jobs fetched: {total_raw_jobs:,}")
    print(f"   Jobs classified: {total_classified_jobs:,}")
    print(f"   Quality jobs (good/so-so): {total_quality_jobs:,}")
    print(f"{'='*80}\n")

    # Send notification email if configured
    notification_email = os.getenv('NOTIFICATION_EMAIL')
    if notification_email and total_quality_jobs > 0:
        print(f"📧 Sending scrape report to {notification_email}...")

        # Collect detailed stats from DataFrame
        stats = collect_job_stats_from_dataframe(final_df)

        # Add search configuration info
        stats['source_name'] = 'JSearch (Google Jobs)'
        stats['markets_searched'] = list(MARKET_DISPLAY_NAMES.values())
        stats['search_terms'] = [SEARCH_TERM]

        # Send the report
        try:
            success = send_detailed_scrape_report("JSearch Google Jobs Scheduled", stats, notification_email)
            if success:
                print(f"✅ Scrape report sent successfully")
            else:
                print(f"⚠️  Failed to send scrape report (non-fatal)")
        except Exception as e:
            print(f"⚠️  Error sending scrape report: {e} (non-fatal)")
    elif notification_email:
        print(f"⚠️  Skipping notification - no quality jobs found")
    else:
        print(f"ℹ️  NOTIFICATION_EMAIL not set, skipping scrape report")

    sys.exit(0)


if __name__ == "__main__":
    main()
