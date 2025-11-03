#!/usr/bin/env python3
"""
Process Manually Downloaded Google Results
Takes a downloaded Outscraper JSON file and processes it through the pipeline.
"""

import json
import csv
import sys
from datetime import datetime, timezone
from pipeline_v3 import FreeWorldPipelineV3
from canonical_transforms import transform_ingest_google

def process_google_file(json_file: str, csv_mapping: str = 'google_query_to_market.csv'):
    """Process a Google results JSON file through the pipeline"""

    print(f"\n{'='*80}")
    print(f"🌐 MANUAL GOOGLE RESULTS PROCESSOR")
    print(f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*80}\n")

    # Load the JSON file
    print(f"📂 Loading Google results from: {json_file}")
    with open(json_file, 'r') as f:
        results_data = json.load(f)

    # Load query-to-market mapping
    print(f"📋 Loading query→market mapping from: {csv_mapping}")
    with open(csv_mapping, 'r') as f:
        reader = csv.DictReader(f)
        query_to_market = {row['Query']: row['Market'] for row in reader}

    print(f"   ✅ Loaded {len(query_to_market)} query mappings")

    # Process the data
    if isinstance(results_data, list):
        raw_jobs = results_data
    elif isinstance(results_data, dict) and 'data' in results_data:
        raw_jobs = results_data['data']
    else:
        print(f"❌ Unexpected data format")
        return

    print(f"\n📊 Raw results: {len(raw_jobs)} jobs from Outscraper")

    # Map queries to markets
    all_jobs = []
    for job in raw_jobs:
        if isinstance(job, dict):
            query = job.get('query', '')
            market = query_to_market.get(query, 'Unknown')
            job['market'] = market
            all_jobs.append(job)

    print(f"   ✅ Mapped {len(all_jobs)} jobs to markets")

    # Show market distribution
    from collections import Counter
    market_counts = Counter(job['market'] for job in all_jobs)
    print(f"\n📍 Market Distribution:")
    for market, count in sorted(market_counts.items(), key=lambda x: -x[1]):
        print(f"   {market}: {count} jobs")

    # Transform to canonical format
    print(f"\n🔄 Transforming to canonical format...")
    df = transform_ingest_google(all_jobs, 'manual_google_batch', 'manual_processing')

    if df.empty:
        print(f"❌ Transform produced empty DataFrame")
        return

    print(f"   ✅ Transformed {len(df)} jobs")

    # Run through pipeline
    print(f"\n🧠 Processing through pipeline...")
    pipeline = FreeWorldPipelineV3()

    # Stage 2: Normalization
    print(f"   Stage 2: Normalization...")
    df = pipeline._stage2_normalization(df)

    # Stage 3: Business Rules
    print(f"   Stage 3: Business Rules...")
    df = pipeline._stage3_business_rules(df, "", {})

    # Stage 4: Deduplication
    print(f"   Stage 4: Deduplication...")
    df = pipeline._stage4_deduplication(df)
    print(f"      ✅ {len(df)} jobs after deduplication")

    # Stage 5.5: Route Rules
    print(f"   Stage 5.5: Route Rules...")
    df = pipeline._stage5_5_route_rules(df)

    # Stage 5: AI Classification
    print(f"   Stage 5: AI Classification (CDL)...")
    df = pipeline._stage5_ai_classification(df, classifier_type="cdl")

    # Stage 6: Routing
    print(f"   Stage 6: Routing...")
    df = pipeline._stage6_routing(df, "")

    # Stage 7: Link Tracking
    print(f"   Stage 7: Link Tracking...")
    pipeline._stage7_output(
        df=df,
        market="",
        custom_location="",
        generate_pdf=False,
        generate_csv=False,
        generate_html=False,
        force_memory_only=False
    )

    # Stage 8: Storage
    print(f"\n💾 Stage 8: Uploading to Supabase...")
    pipeline._stage8_storage(pipeline.df, push_to_airtable=False)

    # Calculate final metrics
    total_jobs = len(df)
    quality_jobs = len(df[df.get('ai.match', '').isin(['good', 'so-so'])]) if 'ai.match' in df.columns else 0
    uploaded_count = pipeline.supabase_upload_count if hasattr(pipeline, 'supabase_upload_count') else 0

    print(f"\n{'='*80}")
    print(f"✅ PROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"   Total jobs processed: {total_jobs}")
    print(f"   Quality jobs (good/so-so): {quality_jobs}")
    print(f"   Uploaded to Supabase: {uploaded_count}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_manual_google_results.py <json_file> [csv_mapping]")
        sys.exit(1)

    json_file = sys.argv[1]
    csv_mapping = sys.argv[2] if len(sys.argv) > 2 else 'google_query_to_market.csv'

    process_google_file(json_file, csv_mapping)
