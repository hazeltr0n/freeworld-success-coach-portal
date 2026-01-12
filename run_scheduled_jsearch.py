#!/usr/bin/env python3
"""
Scheduled JSearch (Google Jobs) Multi-Market Scraper
Runs Tue/Thu/Sat at 2am Central via GitHub Actions

Uses OpenWeb Ninja's JSearch API as Google Jobs source
237 City Queries (from google_query_to_market.csv) × 5 pages = ~10,000 raw jobs
After dedup: ~3,000-4,000 unique jobs

Uses same city queries as Outscraper for consistent coverage.
"""

import os
import sys
import uuid
import time
import csv
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

# JSearch config
PAGES_PER_SEARCH = 5   # 5 pages per city query (50 jobs max per city)
DATE_POSTED = "week"   # Jobs from last 7 days
DELAY_BETWEEN_QUERIES = 0.5  # Half second delay to avoid rate limits

# Path to city queries CSV (same as Outscraper uses)
QUERIES_CSV = "google_query_to_market.csv"


def load_queries_from_csv(csv_path: str) -> list:
    """
    Load search queries from CSV file.
    Returns list of (query, market) tuples.
    """
    queries = []
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                query = row.get('Query', '').strip()
                market = row.get('Market', '').strip()
                if query and market:
                    queries.append((query, market))
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return []

    return queries


def main():
    """Run multi-city JSearch Google Jobs scrapes"""
    print(f"\n{'='*80}")
    print(f"🔍 SCHEDULED JSEARCH (GOOGLE JOBS) MULTI-CITY SCRAPER")
    print(f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*80}\n")

    # Load queries from CSV
    queries = load_queries_from_csv(QUERIES_CSV)
    if not queries:
        print(f"❌ No queries loaded from {QUERIES_CSV}")
        sys.exit(1)

    # Count queries per market
    markets = {}
    for query, market in queries:
        markets[market] = markets.get(market, 0) + 1

    print(f"📍 Loaded {len(queries)} city queries across {len(markets)} markets:")
    for market, count in sorted(markets.items(), key=lambda x: -x[1]):
        print(f"   • {market}: {count} cities")

    print(f"\n📊 Configuration:")
    print(f"   Pages per city: {PAGES_PER_SEARCH} (max 10 jobs/page)")
    print(f"   Date filter: {DATE_POSTED}")
    print(f"   Total API queries: {len(queries)}")
    print(f"   Expected raw jobs: ~{len(queries) * PAGES_PER_SEARCH * 6:,} (assuming 6 jobs/page avg)")
    print(f"   Expected after dedup: ~{int(len(queries) * PAGES_PER_SEARCH * 6 * 0.4):,} (60% dedup rate)")

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
    failed_queries = []

    # Initialize pipeline for classification
    print(f"\n🔧 Initializing Pipeline v3 (run_id: {run_id})...")
    pipeline = PipelineV3()
    pipeline.run_id = run_id

    # Search each city
    print(f"\n{'='*80}")
    print(f"🚀 STARTING JSEARCH SCRAPES ({len(queries)} queries)")
    print(f"{'='*80}\n")

    current_market = None
    market_job_count = 0

    for i, (query, market) in enumerate(queries):
        # Print market header when market changes
        if market != current_market:
            if current_market:
                print(f"   📊 {current_market} subtotal: {market_job_count} jobs\n")
            current_market = market
            market_job_count = 0
            print(f"📍 {market}:")

        try:
            # Search JSearch API
            jobs = adapter.search_jobs(
                query=query,
                num_pages=PAGES_PER_SEARCH,
                date_posted=DATE_POSTED,
            )

            job_count = len(jobs) if jobs else 0
            market_job_count += job_count
            total_raw_jobs += job_count

            # Show progress
            city_name = query.replace("CDL Driver ", "")
            status = f"✅ {job_count}" if job_count > 0 else "⚠️ 0"
            print(f"   [{i+1}/{len(queries)}] {city_name}: {status}")

            if jobs:
                # Transform to canonical format
                df = transform_jsearch_to_canonical(
                    raw_data=jobs,
                    run_id=run_id,
                    search_location=city_name,
                    market=market
                )

                if not df.empty:
                    all_jobs_dfs.append(df)

            # Small delay between queries to avoid rate limits
            if DELAY_BETWEEN_QUERIES > 0:
                time.sleep(DELAY_BETWEEN_QUERIES)

        except Exception as e:
            error_msg = str(e)
            print(f"   [{i+1}/{len(queries)}] {query}: ❌ {error_msg[:50]}")
            failed_queries.append((query, market, error_msg))

            # If we get a 401, the API key might be rate limited - wait longer
            if "401" in error_msg or "Unauthorized" in error_msg:
                print(f"   ⏳ Rate limit? Waiting 5 seconds...")
                time.sleep(5)

    # Print final market subtotal
    if current_market:
        print(f"   📊 {current_market} subtotal: {market_job_count} jobs\n")

    # Report failed queries
    if failed_queries:
        print(f"\n⚠️ Failed queries: {len(failed_queries)}")
        for query, market, error in failed_queries[:5]:
            print(f"   • {query}: {error[:50]}")
        if len(failed_queries) > 5:
            print(f"   ... and {len(failed_queries) - 5} more")

    # Combine all DataFrames
    if not all_jobs_dfs:
        print(f"\n❌ No jobs found from any query")
        sys.exit(1)

    import pandas as pd
    combined_df = pd.concat(all_jobs_dfs, ignore_index=True)
    print(f"\n📊 Combined: {len(combined_df)} raw jobs from {len(queries)} city queries")

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

        # Stage 7: Output (includes URL handling)
        print("📄 Stage 7: Output generation...")
        output_results = pipeline._stage7_output(
            df_routed,
            market='JSearch',
            custom_location='',
            generate_pdf=False,
            generate_csv=False,
            generate_html=False,
            force_memory_only=False
        )
        final_df = pipeline.df  # Get updated df from pipeline
        print(f"   ✅ Output stage complete ({output_results.get('quality_jobs', 0)} quality jobs)")

        # Stage 8: Storage
        print("💾 Stage 8: Storing to Supabase...")
        pipeline._stage8_storage(final_df, push_to_airtable=False)
        upload_count = getattr(pipeline, 'supabase_upload_count', 0)
        print(f"   ✅ Uploaded {upload_count} jobs to Supabase")

    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Final summary
    print(f"\n{'='*80}")
    print(f"✅ JSEARCH SCRAPE COMPLETE")
    print(f"{'='*80}")
    print(f"   Markets: {len(markets)}")
    print(f"   City queries: {len(queries)}")
    print(f"   Failed queries: {len(failed_queries)}")
    print(f"   Raw jobs fetched: {total_raw_jobs:,}")
    print(f"   Jobs after dedup: {total_classified_jobs:,}")
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
        stats['markets_searched'] = list(markets.keys())
        stats['search_terms'] = ['CDL Driver (237 city queries)']

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
