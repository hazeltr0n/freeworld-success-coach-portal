#!/usr/bin/env python3
"""
Scheduled USNLX Job Scraper (Concurrent Version)
Runs via GitHub Actions to scrape CDL jobs from US National Labor Exchange

Uses async Playwright to run all 10 markets concurrently, reducing runtime
from 4+ hours to ~30-45 minutes while still fetching full job descriptions.
"""

import os
import sys
import uuid
import time
import asyncio
from datetime import datetime, timezone

# Import USNLX scraper (async version)
from usnlx_scraper import run_concurrent_usnlx_scrape, transform_usnlx_to_canonical

# Import pipeline components
from pipeline_v3 import FreeWorldPipelineV3 as PipelineV3
from canonical_transforms import (
    transform_normalize,
    transform_business_rules,
)
from send_scrape_notification import (
    collect_job_stats_from_dataframe,
    send_detailed_scrape_report,
    send_zero_jobs_alert
)

# USNLX config
SEARCH_QUERIES = ["CDL Driver", "Truck Driver", "Class A Driver"]
SEARCH_RADIUS = 50  # miles
MAX_JOBS_PER_ZIP = 75  # ~5 "More" clicks (15 jobs each)
MAX_CLICKS_PER_ZIP = 5
MAX_CONCURRENT_MARKETS = 5  # Run 5 markets at a time (2 batches)

# Market ZIP codes for USNLX searches
MARKET_ZIPS = {
    'Dallas': ['75201', '75062', '75234'],
    'Houston': ['77002', '77042', '77084'],
    'Phoenix': ['85004', '85032', '85043'],
    'Denver': ['80202', '80221', '80239'],
    'Las Vegas': ['89101', '89119', '89148'],
    'Stockton': ['95202', '95207', '95336'],
    'Bay Area': ['94102', '94538', '94607'],
    'Inland Empire': ['92324', '92376', '92507'],
    'Trenton': ['08608', '08618', '08648'],
    'Newark': ['07102', '07105', '07114'],
}


async def run_scraper():
    """Run USNLX CDL job scraper across all markets concurrently"""
    print(f"\n{'='*80}")
    print(f"🏛️ SCHEDULED USNLX JOB SCRAPER (CONCURRENT)")
    print(f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*80}\n")

    run_id = str(uuid.uuid4())[:8]

    # Count total searches
    total_zips = sum(len(zips) for zips in MARKET_ZIPS.values())
    total_searches = total_zips * len(SEARCH_QUERIES)

    print(f"📊 Configuration:")
    print(f"   Run ID: {run_id}")
    print(f"   Search queries: {SEARCH_QUERIES}")
    print(f"   Search radius: {SEARCH_RADIUS} miles")
    print(f"   Markets: {len(MARKET_ZIPS)}")
    print(f"   ZIP codes per market: ~{total_zips // len(MARKET_ZIPS)}")
    print(f"   Total searches: {total_searches}")
    print(f"   Max jobs per ZIP: {MAX_JOBS_PER_ZIP}")
    print(f"   Concurrent markets: {MAX_CONCURRENT_MARKETS}")
    print(f"   Mode: CONCURRENT (async Playwright)")

    start_time = time.time()

    # =========================================================================
    # CONCURRENT MARKET SCRAPING
    # =========================================================================
    print(f"\n{'='*80}")
    print(f"🚀 SCRAPING {len(MARKET_ZIPS)} MARKETS CONCURRENTLY")
    print(f"{'='*80}\n")

    scrape_result = await run_concurrent_usnlx_scrape(
        market_zips=MARKET_ZIPS,
        queries=SEARCH_QUERIES,
        radius=SEARCH_RADIUS,
        max_jobs_per_zip=MAX_JOBS_PER_ZIP,
        max_clicks=MAX_CLICKS_PER_ZIP,
        fetch_details=True,  # Keep full descriptions for AI classification
        max_concurrent_markets=MAX_CONCURRENT_MARKETS
    )

    all_jobs = scrape_result['all_jobs']
    market_stats = scrape_result['market_stats']
    search_time = scrape_result['total_time_seconds']

    print(f"\n{'='*80}")
    print(f"📊 SEARCH COMPLETE")
    print(f"{'='*80}")
    print(f"   Markets processed: {len(market_stats)}")
    print(f"   Unique jobs found: {len(all_jobs)}")
    print(f"   Search time: {search_time:.1f}s ({search_time/60:.1f}m)")

    # Show per-market stats
    print(f"\n   Per-market breakdown:")
    for market, stats in market_stats.items():
        print(f"      {market}: {stats['job_count']} jobs")

    # =========================================================================
    # PIPELINE PROCESSING
    # =========================================================================
    total_raw_jobs = len(all_jobs)

    if total_raw_jobs == 0:
        print(f"\n❌ No jobs found from USNLX")

        # Send alert
        notification_email = os.getenv('NOTIFICATION_EMAIL')
        if notification_email:
            error_details = {
                'raw_jobs': 0,
                'after_dedup': 0,
                'classification_errors': 0,
                'storage_error': 'No jobs found during scraping',
                'markets_searched': list(MARKET_ZIPS.keys()),
                'run_id': run_id
            }
            try:
                send_zero_jobs_alert("USNLX Scheduled", error_details, notification_email)
            except:
                pass

        return 1

    print(f"\n{'='*80}")
    print(f"🔄 RUNNING PIPELINE CLASSIFICATION ({total_raw_jobs} jobs)")
    print(f"{'='*80}\n")

    # Transform to canonical format
    jobs_list = list(all_jobs.values())

    df = transform_usnlx_to_canonical(
        raw_data=jobs_list,
        run_id=run_id,
        search_location='Multi-Market',
        market=''
    )

    # Set market from job's _market field
    for idx in range(len(df)):
        if idx < len(jobs_list):
            job = jobs_list[idx]
            if job.get('_market'):
                df.at[idx, 'meta.market'] = job['_market']

    print(f"📐 Transformed {len(df)} jobs to canonical format")

    # Initialize pipeline
    pipeline = PipelineV3()
    pipeline.run_id = run_id

    # Track these for final summary
    dedup_active = 0
    good_count = 0
    soso_count = 0
    bad_count = 0
    total_quality_jobs = 0
    upload_count = 0
    final_df = None

    try:
        # Stage 2: Normalization
        print("📐 Stage 2: Normalizing...")
        df_normalized = transform_normalize(df)
        print(f"   ✅ Normalized {len(df_normalized)} jobs")

        # Stage 3: Business Rules
        print("📋 Stage 3: Applying business rules...")
        df_rules = transform_business_rules(df_normalized)
        print(f"   ✅ Applied rules to {len(df_rules)} jobs")

        # Stage 4: Deduplication
        print("🔄 Stage 4: Deduplicating...")
        df_deduped = pipeline._stage4_deduplication(df_rules)

        if 'route.final_status' in df_deduped.columns:
            active_mask = ~df_deduped['route.final_status'].str.startswith('filtered:', na=False)
            dedup_active = active_mask.sum()
        else:
            dedup_active = len(df_deduped)
        print(f"   ✅ {dedup_active} unique jobs after deduplication")

        # Stage 5: AI Classification
        print("🤖 Stage 5: AI Classification...")
        df_classified = pipeline._stage5_ai_classification(df_deduped)

        if 'ai.match' in df_classified.columns:
            good_count = (df_classified['ai.match'] == 'good').sum()
            soso_count = (df_classified['ai.match'] == 'so-so').sum()
            bad_count = (df_classified['ai.match'] == 'bad').sum()
            total_quality_jobs = good_count + soso_count
            print(f"   ✅ Classification: {good_count} good, {soso_count} so-so, {bad_count} bad")

        # Stage 6: Routing
        print("🎯 Stage 6: Routing...")
        df_routed = pipeline._stage6_routing(df_classified, route_filter='both')
        print(f"   ✅ Routed {len(df_routed)} jobs")

        # Stage 7: Output (link tracking)
        print("📄 Stage 7: Output generation...")
        output_results = pipeline._stage7_output(
            df_routed,
            market='USNLX',
            custom_location='',
            generate_pdf=False,
            generate_csv=False,
            generate_html=False,
            force_memory_only=False
        )
        final_df = pipeline.df
        print(f"   ✅ Output stage complete")

        # Stage 8: Storage
        print("💾 Stage 8: Storing to Supabase...")
        pipeline._stage8_storage(final_df, push_to_airtable=False)
        upload_count = getattr(pipeline, 'supabase_upload_count', 0)
        print(f"   ✅ Uploaded {upload_count} jobs to Supabase")

    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()

        # Send alert on pipeline failure
        notification_email = os.getenv('NOTIFICATION_EMAIL')
        if notification_email:
            print(f"⚠️ Sending failure alert to {notification_email}...")
            error_details = {
                'raw_jobs': total_raw_jobs,
                'after_dedup': dedup_active,
                'classification_errors': 0,
                'storage_error': str(e),
                'markets_searched': list(MARKET_ZIPS.keys()),
                'run_id': run_id
            }
            try:
                send_zero_jobs_alert("USNLX Scheduled", error_details, notification_email)
                print(f"✅ Failure alert sent")
            except Exception as email_err:
                print(f"⚠️ Failed to send alert: {email_err}")

        return 1

    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    total_time = time.time() - start_time

    print(f"\n{'='*80}")
    print(f"✅ USNLX SCRAPE COMPLETE")
    print(f"{'='*80}")
    print(f"   Source: US National Labor Exchange (usnlx.com)")
    print(f"   Run ID: {run_id}")
    print(f"   Duration: {total_time:.1f}s ({total_time/60:.1f}m)")
    print(f"   Mode: CONCURRENT ({MAX_CONCURRENT_MARKETS} markets at a time)")
    print(f"")
    print(f"   📊 Results:")
    print(f"      Markets processed: {len(market_stats)}")
    print(f"      Raw jobs fetched: {total_raw_jobs:,}")
    print(f"      After dedup: {dedup_active:,}")
    print(f"      Good jobs: {good_count:,}")
    print(f"      So-so jobs: {soso_count:,}")
    print(f"      Quality jobs (good/so-so): {total_quality_jobs:,}")
    print(f"      Uploaded to Supabase: {upload_count:,}")
    print(f"{'='*80}\n")

    # Send notification email
    notification_email = os.getenv('NOTIFICATION_EMAIL')

    # ALERT: Send warning if 0 jobs uploaded to Supabase
    if notification_email and upload_count == 0:
        print(f"⚠️ ALERT: 0 jobs uploaded - sending alert to {notification_email}...")

        error_details = {
            'raw_jobs': total_raw_jobs,
            'after_dedup': dedup_active,
            'classification_errors': 0,
            'storage_error': '',
            'markets_searched': list(MARKET_ZIPS.keys()),
            'run_id': run_id
        }

        try:
            send_zero_jobs_alert("USNLX Scheduled", error_details, notification_email)
            print(f"✅ Zero jobs alert sent")
        except Exception as e:
            print(f"⚠️ Failed to send alert: {e}")

    # Send success report if we have quality jobs
    elif notification_email and total_quality_jobs > 0 and final_df is not None:
        print(f"📧 Sending scrape report to {notification_email}...")

        stats = collect_job_stats_from_dataframe(final_df)
        stats['source_name'] = 'USNLX (US National Labor Exchange)'
        stats['markets_searched'] = list(MARKET_ZIPS.keys())
        stats['search_terms'] = SEARCH_QUERIES

        try:
            success = send_detailed_scrape_report("USNLX Scheduled", stats, notification_email)
            if success:
                print(f"✅ Scrape report sent successfully")
            else:
                print(f"⚠️  Failed to send scrape report (non-fatal)")
        except Exception as e:
            print(f"⚠️  Error sending scrape report: {e} (non-fatal)")

    return 0


def main():
    """Entry point - run async scraper"""
    exit_code = asyncio.run(run_scraper())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
