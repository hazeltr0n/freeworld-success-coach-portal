#!/usr/bin/env python3
"""
Scheduled USNLX Job Scraper
Runs via GitHub Actions to scrape CDL jobs from US National Labor Exchange

USNLX aggregates job postings from state workforce agencies and direct employers.
Good source for CDL/trucking jobs across all FreeWorld markets.
"""

import os
import sys
import uuid
import time
from datetime import datetime, timezone

# Import USNLX scraper
from usnlx_scraper import USNLXScraper, USNLXConfig, transform_usnlx_to_canonical

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
DELAY_BETWEEN_SEARCHES = 2  # seconds (browser-based, needs more time)

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


def main():
    """Run USNLX CDL job scraper across all markets"""
    print(f"\n{'='*80}")
    print(f"🏛️ SCHEDULED USNLX JOB SCRAPER")
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

    # Track stats
    all_jobs = {}  # Dict for dedup by generated job ID
    failed_searches = []
    start_time = time.time()

    # =========================================================================
    # SEARCH ALL MARKETS
    # =========================================================================
    print(f"\n{'='*80}")
    print(f"🔍 SEARCHING {total_searches} COMBINATIONS")
    print(f"{'='*80}\n")

    search_count = 0

    # Initialize scraper config
    config = USNLXConfig(
        headless=True,
        timeout_ms=45000,
        slow_mo=50
    )

    for market, zips in MARKET_ZIPS.items():
        print(f"\n🏙️ {market} ({len(zips)} ZIPs):")
        market_jobs_before = len(all_jobs)

        for zip_code in zips:
            for query in SEARCH_QUERIES:
                search_count += 1

                try:
                    scraper = USNLXScraper(config)
                    jobs = scraper.search_jobs(
                        query=query,
                        location=zip_code,
                        radius=SEARCH_RADIUS,
                        max_jobs=MAX_JOBS_PER_ZIP,
                        max_clicks=MAX_CLICKS_PER_ZIP,
                        fetch_details=True  # Fetch full job descriptions for AI classification
                    )

                    new_count = 0
                    for job in jobs:
                        # Generate unique ID from company+location+title
                        job_key = f"{job.get('company', '')}|{job.get('location', '')}|{job.get('title', '')}".lower()
                        import hashlib
                        job_id = hashlib.md5(job_key.encode()).hexdigest()

                        if job_id not in all_jobs:
                            job['_market'] = market
                            job['_search_zip'] = zip_code
                            job['_search_query'] = query
                            job['_job_id'] = job_id
                            all_jobs[job_id] = job
                            new_count += 1

                    if new_count > 0:
                        print(f"   {zip_code} '{query[:15]}': +{new_count} jobs")

                    time.sleep(DELAY_BETWEEN_SEARCHES)

                except Exception as e:
                    failed_searches.append((market, zip_code, query, str(e)))
                    print(f"   {zip_code} '{query[:15]}': ❌ {str(e)[:40]}")

        market_new = len(all_jobs) - market_jobs_before
        print(f"   📊 {market} subtotal: {market_new} unique jobs")

    search_time = time.time() - start_time

    print(f"\n{'='*80}")
    print(f"📊 SEARCH COMPLETE")
    print(f"{'='*80}")
    print(f"   Searches completed: {search_count}")
    print(f"   Failed searches: {len(failed_searches)}")
    print(f"   Unique jobs found: {len(all_jobs)}")
    print(f"   Search time: {search_time:.1f}s ({search_time/60:.1f}m)")

    # =========================================================================
    # PIPELINE PROCESSING
    # =========================================================================
    total_raw_jobs = len(all_jobs)

    if total_raw_jobs == 0:
        print(f"\n❌ No jobs found from USNLX")
        sys.exit(1)

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

        total_quality_jobs = 0
        good_count = 0
        soso_count = 0
        bad_count = 0
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
                'raw_jobs': total_raw_jobs if 'total_raw_jobs' in dir() else 0,
                'after_dedup': 0,
                'classification_errors': 0,
                'storage_error': str(e),
                'markets_searched': list(MARKET_ZIPS.keys()),
                'run_id': run_id if 'run_id' in dir() else 'unknown'
            }
            try:
                send_zero_jobs_alert("USNLX Scheduled", error_details, notification_email)
                print(f"✅ Failure alert sent")
            except Exception as email_err:
                print(f"⚠️ Failed to send alert: {email_err}")

        sys.exit(1)

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
    print(f"")
    print(f"   📊 Results:")
    print(f"      Searches completed: {search_count}")
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
    elif notification_email and total_quality_jobs > 0:
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

    sys.exit(0)


if __name__ == "__main__":
    main()
