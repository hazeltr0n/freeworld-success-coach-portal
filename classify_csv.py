#!/usr/bin/env python3
"""
Classify an Outscraper CSV via the Pipeline (terminal tool)

Usage examples:

  python tools/classify_csv.py \
    --csv "/Users/you/Downloads/out.csv" \
    --market-source column \
    --market-column meta.market \
    --fallback-market Dallas \
    --store

  python tools/classify_csv.py \
    --csv "/Users/you/Downloads/out.csv" \
    --market-source fixed \
    --fallback-market "Bay Area" \
    --store

Notes
- This mirrors the CSV Classification tab but runs in terminal with verbose logs.
- It stores to Supabase memory when --store is passed; otherwise it does a dry run.
"""

from __future__ import annotations

import argparse
import sys
import re
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# Load Streamlit-style secrets into os.environ when running via Python
try:
    from tools.secrets_loader import load_local_secrets_to_env
    load_local_secrets_to_env()
except Exception:
    pass


def _first(row: pd.Series, cols_map: Dict[str, str], names: List[str], default: str = "") -> str:
    for n in names:
        k = cols_map.get(n.lower())
        if k is not None:
            v = row.get(k)
            if pd.notna(v) and str(v).strip():
                return str(v).strip()
    return default


def _normalize_market(val: str, *, fallback: str, markets: List[str], city_map: Dict[str, str], inverse_map: Dict[str, str]) -> str:
    try:
        s = str(val or '').strip()
        if not s:
            return fallback
        # Exact market match (case-insensitive)
        for m in markets:
            if s.lower() == m.lower():
                return m
        # City, ST -> Market
        if s in inverse_map:
            return inverse_map[s]
        # City-only
        city = s.split(',')[0].strip()
        if city in city_map:
            return city_map[city]
        # Special cases
        if city.lower() == 'berkeley':
            return 'Bay Area'
        if city.lower() == 'ontario':
            return 'Inland Empire'
        # Strip state if present
        if ',' in s:
            return s.split(',')[0].strip()
        return s
    except Exception:
        return fallback


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Classify Outscraper CSV via Pipeline")
    ap.add_argument("--csv", required=True, help="Path to Outscraper CSV")
    ap.add_argument("--market-source", choices=["fixed", "column"], default="column")
    ap.add_argument("--market-column", default="market", help="CSV column containing market names (when market-source=column)")
    ap.add_argument("--fallback-market", default="Dallas", help="Fallback market if unmapped")
    ap.add_argument("--store", action="store_true", help="Store to Supabase memory (default is dry-run)")
    ap.add_argument("--limit", type=int, default=0, help="Optional limit on rows to process for quick tests")
    ap.add_argument("--test-refresh", action="store_true", help="Test smart classification refresh logic (shows memory detection without storing)")
    ap.add_argument("--inspect-pipeline", action="store_true", help="Inspect final DataFrame and pipeline outputs (comprehensive test mode)")
    args = ap.parse_args(argv)

    csv_path = Path(args.csv).expanduser()
    if not csv_path.exists():
        print(f"❌ CSV not found: {csv_path}")
        return 2

    print(f"📥 Reading: {csv_path}")
    df_src = pd.read_csv(csv_path)
    if args.limit and len(df_src) > args.limit:
        df_src = df_src.head(args.limit)
    print(f"✅ Loaded CSV: {len(df_src)} rows, {len(df_src.columns)} columns")

    # Map to raw Outscraper-like dicts
    print("🧭 Mapping CSV → raw rows (title/company/location/url)…")
    cols_map = {c.lower(): c for c in df_src.columns}
    raw_rows: List[Dict[str, Any]] = []
    for _, row in df_src.iterrows():
        title = _first(row, cols_map, ["title", "job_title", "job"], "")
        company = _first(row, cols_map, ["company", "company_name", "employer"], "")
        location_raw = _first(row, cols_map, ["formattedLocation", "location", "city", "job_location"], "")
        apply_url = _first(row, cols_map, ["viewJobLink", "apply_url", "applyUrl", "url", "link"], "")
        description = _first(row, cols_map, ["snippet", "description", "job_description", "jobDescription", "details"], "")
        raw_rows.append({
            "title": title,
            "company": company,
            "formattedLocation": location_raw,
            "viewJobLink": apply_url,
            "snippet": description,  # Use 'snippet' key to match canonical transform expectations
        })
    print(f"✅ Mapped rows: {len(raw_rows)}")

    # Pipeline
    print("🏗️ Initializing pipeline…")
    from pipeline_v3 import FreeWorldPipelineV3
    from canonical_transforms import transform_ingest_outscraper, transform_business_rules
    from jobs_schema import ensure_schema
    from shared_search import MARKET_TO_LOCATION

    pipe = FreeWorldPipelineV3()

    print("📥 Ingesting…")
    df_ing = transform_ingest_outscraper(raw_rows, pipe.run_id) if raw_rows else ensure_schema(pd.DataFrame())
    print(f"✅ Ingested: {len(df_ing)} rows")

    print("🧹 Normalizing…")
    df_norm = pipe._stage2_normalization(df_ing)
    print("✅ Normalized")

    # Market assignment
    std_markets = list(MARKET_TO_LOCATION.keys())
    inverse_map = {v: k for k, v in MARKET_TO_LOCATION.items()}
    cities_map = {v.split(',')[0].strip(): k for k, v in MARKET_TO_LOCATION.items()}

    if args.market_source == "fixed":
        chosen = args.fallback_market
        print(f"🏷️ Assigning fixed market: {chosen}")
        df_rules = pipe._stage3_business_rules(df_norm, chosen)
    else:
        col = args.market_column
        if col not in df_src.columns:
            print(f"❌ Column '{col}' not found in CSV. Available: {list(df_src.columns)[:10]}…")
            return 3
        print(f"🏷️ Mapping markets from CSV column: {col}")

        def _extract_markets(val: str) -> List[str]:
            # Treat as single market per row; normalize to plain name
            m = _normalize_market(val, fallback=args.fallback_market, markets=std_markets, city_map=cities_map, inverse_map=inverse_map)
            return [m]

        mk_lists = df_src[col].apply(_extract_markets)
        df_exp = df_norm.copy()
        df_exp['meta.market'] = mk_lists
        df_exp = df_exp.explode('meta.market')
        df_exp['meta.market'] = df_exp['meta.market'].fillna(args.fallback_market).astype(str)
        print("🔎 Market distribution:", df_exp['meta.market'].value_counts().to_dict())
        df_rules = transform_business_rules(df_exp, filter_settings={})

    print("🧼 Deduplicating…")
    df_dedup = pipe._stage4_deduplication(df_rules)
    print(f"✅ Deduped to {len(df_dedup)} rows")

    print("🤖 Classifying with AI…")
    df_ai = pipe._stage5_ai_classification(df_dedup, force_fresh_classification=True)
    try:
        print("🔎 Match breakdown:", df_ai['ai.match'].value_counts().to_dict())
    except Exception:
        pass

    print("🧭 Deriving route types and routing…")
    df_route = pipe._stage5_5_route_rules(df_ai)
    df_final = pipe._stage6_routing(df_route, 'both')

    # Summary
    total = len(df_final)
    included = int((df_final['route.final_status'].astype(str).str.startswith('included')).sum()) if 'route.final_status' in df_final.columns else 0
    ai_good = int((df_final['ai.match'].astype(str).str.lower() == 'good').sum()) if 'ai.match' in df_final.columns else 0
    ai_soso = int((df_final['ai.match'].astype(str).str.lower() == 'so-so').sum()) if 'ai.match' in df_final.columns else 0
    local_routes = int((df_final['ai.route_type'].astype(str) == 'Local').sum()) if 'ai.route_type' in df_final.columns else 0
    otr_routes = int((df_final['ai.route_type'].astype(str) == 'OTR').sum()) if 'ai.route_type' in df_final.columns else 0

    print("\n=== SUMMARY ===")
    print(f"Total Classified: {total}")
    print(f"Included (quality): {included}")
    print(f"Excellent Matches: {ai_good}")
    print(f"Possible Fits: {ai_soso}")
    print(f"Local Routes: {local_routes}")
    print(f"OTR Routes: {otr_routes}")

    # Test smart classification refresh logic
    if args.test_refresh:
        print("\n🧪 TESTING SMART CLASSIFICATION REFRESH LOGIC")
        print("=" * 60)
        try:
            from job_memory_db import JobMemoryDB
            memory_db = JobMemoryDB()
            
            # Check which jobs already exist in memory
            job_ids = df_final['id.job'].dropna().astype(str).tolist()[:20]  # Test first 20 jobs
            print(f"🔍 Checking {len(job_ids)} job IDs in memory database...")
            
            memory_lookup = memory_db.check_job_memory(job_ids, hours=720)  # 30 days
            
            if memory_lookup:
                print(f"✅ Found {len(memory_lookup)} existing jobs in memory:")
                print("\n📋 EXISTING JOBS DETAILS:")
                for job_id, memory_job in memory_lookup.items():
                    print(f"\n  Job ID: {job_id[:12]}...")
                    print(f"    Title: {memory_job.get('job_title', 'N/A')[:60]}...")
                    print(f"    Company: {memory_job.get('company', 'N/A')}")
                    print(f"    Match: {memory_job.get('match', 'N/A')}")
                    print(f"    Summary: {memory_job.get('summary', 'N/A')[:80]}...")
                    print(f"    Fair Chance: {memory_job.get('fair_chance', 'N/A')}")
                    print(f"    Tracking URL: {memory_job.get('tracked_url', 'None')[:50]}...")
                
                # Show what would happen with smart storage
                print(f"\n🎯 SMART STORAGE SIMULATION:")
                print(f"  📊 Total quality jobs to process: {len(df_final)}")
                
                # Simulate classification source detection  
                memory_job_ids = set(memory_lookup.keys())
                df_jobs_with_ids = df_final[df_final['id.job'].isin(memory_job_ids)]
                df_jobs_without_ids = df_final[~df_final['id.job'].isin(memory_job_ids)]
                
                print(f"  🔄 Jobs that would be REFRESHED (timestamp only): {len(df_jobs_with_ids)}")
                print(f"  🆕 Jobs that would be STORED (full data): {len(df_jobs_without_ids)}")
                
                if len(df_jobs_with_ids) > 0:
                    print(f"\n  🔄 REFRESH SIMULATION (preserving existing data):")
                    for idx, (job_id, memory_job) in enumerate(list(memory_lookup.items())[:3]):
                        print(f"    Job {idx+1}: {job_id[:12]}... -> Keep existing AI data, update timestamp")
                
            else:
                print("ℹ️  No existing jobs found in memory - all would be stored as new")
                
        except Exception as e:
            print(f"❌ Test refresh failed: {e}")
        
        print("\n🧪 Test complete - no data was modified")
        print("(Use --store to actually save data)")
        return 0

    # Inspect complete pipeline outputs
    if args.inspect_pipeline:
        print("\n🔍 COMPREHENSIVE PIPELINE INSPECTION")
        print("=" * 70)
        
        # DataFrame structure analysis
        print(f"📊 FINAL DATAFRAME ANALYSIS:")
        print(f"   Shape: {df_final.shape[0]} rows × {df_final.shape[1]} columns")
        print(f"   Memory usage: {df_final.memory_usage(deep=True).sum() / 1024:.1f} KB")
        
        # Column analysis by category
        column_categories = {
            'source': [col for col in df_final.columns if col.startswith('source.')],
            'norm': [col for col in df_final.columns if col.startswith('norm.')],
            'rules': [col for col in df_final.columns if col.startswith('rules.')],
            'ai': [col for col in df_final.columns if col.startswith('ai.')],
            'route': [col for col in df_final.columns if col.startswith('route.')],
            'meta': [col for col in df_final.columns if col.startswith('meta.')],
            'sys': [col for col in df_final.columns if col.startswith('sys.')],
            'id': [col for col in df_final.columns if col.startswith('id.')],
            'other': [col for col in df_final.columns if not any(col.startswith(prefix + '.') for prefix in ['source', 'norm', 'rules', 'ai', 'route', 'meta', 'sys', 'id'])]
        }
        
        print(f"\n📋 COLUMN BREAKDOWN:")
        for category, cols in column_categories.items():
            if cols:
                print(f"   {category.upper()}: {len(cols)} columns")
                for col in cols[:3]:  # Show first 3
                    sample_val = str(df_final[col].iloc[0])[:50] if len(df_final) > 0 else 'N/A'
                    print(f"      {col}: '{sample_val}{'...' if len(sample_val) >= 50 else ''}'")
                if len(cols) > 3:
                    print(f"      ... and {len(cols) - 3} more columns")
        
        # Critical fields inspection
        critical_fields = [
            'id.job', 'source.title', 'source.company', 'source.url', 
            'ai.match', 'ai.summary', 'ai.route_type', 'ai.fair_chance',
            'meta.tracked_url', 'meta.market', 'route.final_status',
            'sys.is_fresh_job', 'sys.classification_source'
        ]
        
        print(f"\n🎯 CRITICAL FIELDS INSPECTION:")
        missing_critical = []
        for field in critical_fields:
            if field in df_final.columns:
                non_null_count = df_final[field].notna().sum()
                unique_count = df_final[field].nunique()
                sample_values = df_final[field].dropna().head(2).tolist()
                print(f"   ✅ {field}:")
                print(f"      Non-null: {non_null_count}/{len(df_final)} ({non_null_count/len(df_final)*100:.1f}%)")
                print(f"      Unique values: {unique_count}")
                print(f"      Sample: {sample_values}")
            else:
                missing_critical.append(field)
                print(f"   ❌ {field}: MISSING")
        
        if missing_critical:
            print(f"\n⚠️  MISSING CRITICAL FIELDS: {len(missing_critical)}")
            for field in missing_critical:
                print(f"      {field}")
        
        # Data quality analysis
        print(f"\n📈 DATA QUALITY ANALYSIS:")
        if len(df_final) > 0:
            # Job ID uniqueness
            job_ids = df_final.get('id.job', pd.Series())
            if not job_ids.empty:
                unique_jobs = job_ids.nunique()
                total_jobs = len(job_ids)
                print(f"   Job ID uniqueness: {unique_jobs}/{total_jobs} ({unique_jobs/total_jobs*100:.1f}%)")
            
            # URL analysis
            urls = df_final.get('source.url', pd.Series())
            tracked_urls = df_final.get('meta.tracked_url', pd.Series())
            if not urls.empty:
                valid_urls = urls.notna() & urls.str.startswith('http')
                print(f"   Valid source URLs: {valid_urls.sum()}/{len(urls)} ({valid_urls.sum()/len(urls)*100:.1f}%)")
            
            if not tracked_urls.empty:
                has_tracking = tracked_urls.notna() & (tracked_urls != '')
                print(f"   Tracking URLs present: {has_tracking.sum()}/{len(tracked_urls)} ({has_tracking.sum()/len(tracked_urls)*100:.1f}%)")
                
                # Check if tracking URLs are different from original (indicating short links)
                if not urls.empty:
                    different_tracking = (tracked_urls != urls) & tracked_urls.notna() & urls.notna()
                    print(f"   Short links generated: {different_tracking.sum()}/{len(urls)} ({different_tracking.sum()/len(urls)*100:.1f}%)")
            
            # AI classification analysis
            ai_match = df_final.get('ai.match', pd.Series())
            if not ai_match.empty:
                match_counts = ai_match.value_counts()
                print(f"   AI Classifications: {match_counts.to_dict()}")
        
        # Business rules analysis
        print(f"\n🔧 BUSINESS RULES ANALYSIS:")
        rules_cols = [col for col in df_final.columns if col.startswith('rules.')]
        if rules_cols:
            for rule_col in rules_cols:
                if df_final[rule_col].dtype == 'bool':
                    true_count = df_final[rule_col].sum()
                    print(f"   {rule_col}: {true_count}/{len(df_final)} jobs flagged ({true_count/len(df_final)*100:.1f}%)")
        
        # Routing analysis
        print(f"\n🧭 ROUTING ANALYSIS:")
        final_status = df_final.get('route.final_status', pd.Series())
        if not final_status.empty:
            status_counts = final_status.value_counts()
            print(f"   Final status distribution: {status_counts.to_dict()}")
        
        filtered = df_final.get('route.filtered', pd.Series())
        if not filtered.empty:
            filtered_count = filtered.sum() if filtered.dtype == 'bool' else 0
            print(f"   Filtered jobs: {filtered_count}/{len(df_final)} ({filtered_count/len(df_final)*100:.1f}%)")
        
        # Sample job inspection
        if len(df_final) > 0:
            print(f"\n🔍 SAMPLE JOB INSPECTION:")
            sample_job = df_final.iloc[0]
            print(f"   Job ID: {sample_job.get('id.job', 'N/A')}")
            print(f"   Title: {sample_job.get('source.title', 'N/A')}")
            print(f"   Company: {sample_job.get('source.company', 'N/A')}")
            print(f"   Location: {sample_job.get('source.location', 'N/A')}")
            print(f"   Original URL: {sample_job.get('source.url', 'N/A')[:80]}...")
            print(f"   Tracking URL: {sample_job.get('meta.tracked_url', 'N/A')[:80]}...")
            print(f"   AI Match: {sample_job.get('ai.match', 'N/A')}")
            print(f"   AI Summary: {sample_job.get('ai.summary', 'N/A')[:100]}...")
            print(f"   Route Type: {sample_job.get('ai.route_type', 'N/A')}")
            print(f"   Fair Chance: {sample_job.get('ai.fair_chance', 'N/A')}")
            print(f"   Market: {sample_job.get('meta.market', 'N/A')}")
            print(f"   Final Status: {sample_job.get('route.final_status', 'N/A')}")
        
        print(f"\n🔍 Pipeline inspection complete - comprehensive analysis shown above")
        print("(Use --store to actually save data)")
        return 0

    if args.store:
        print("\n🔗 Generating tracking URLs for CSV jobs…")
        try:
            from link_tracker import LinkTracker
            link_tracker = LinkTracker()
            if link_tracker.is_available:
                jobs_without_tracking = df_final[df_final.get('meta.tracked_url', '').fillna('') == '']
                if len(jobs_without_tracking) > 0:
                    print(f"📊 Processing {len(jobs_without_tracking)} jobs without tracking URLs...")
                    
                    for idx, job in jobs_without_tracking.iterrows():
                        original_url = job.get('source.url', '')
                        if original_url:
                            job_title = job.get('source.title', 'CSV Job')[:50]
                            
                            # Create tracking tags
                            tags = ['source:csv-terminal']
                            if job.get('meta.market'):
                                tags.append(f"market:{job.get('meta.market')}")
                            if job.get('ai.match'):
                                tags.append(f"match:{job.get('ai.match')}")
                            if job.get('ai.route_type'):
                                tags.append(f"route:{job.get('ai.route_type')}")
                            
                            tracked_url = link_tracker.create_short_link(
                                original_url,
                                title=f"CSV Terminal: {job_title}",
                                tags=tags
                            )
                            
                            if tracked_url and tracked_url != original_url:
                                df_final.at[idx, 'meta.tracked_url'] = tracked_url
                                print(f"✅ Created tracking URL for {job_title[:30]}...")
                            else:
                                df_final.at[idx, 'meta.tracked_url'] = original_url
                                print(f"⚠️ Using original URL for {job_title[:30]}...")
                    
                    print(f"✅ Generated tracking URLs for {len(jobs_without_tracking)} CSV jobs")
                else:
                    print("ℹ️ All CSV jobs already have tracking URLs")
            else:
                print("⚠️ LinkTracker not available - using original URLs")
                missing_urls = df_final['meta.tracked_url'].fillna('') == ''
                df_final.loc[missing_urls, 'meta.tracked_url'] = df_final.loc[missing_urls, 'source.url']
        except Exception as link_e:
            print(f"⚠️ Link generation failed: {link_e} - using original URLs")
            missing_urls = df_final.get('meta.tracked_url', pd.Series(dtype=str)).fillna('') == ''
            df_final.loc[missing_urls, 'meta.tracked_url'] = df_final.loc[missing_urls, 'source.url']
        
        print("\n💾 Storing ALL classified jobs to memory (Supabase) with tracking URLs…")
        try:
            # For CSV classification, we want to store ALL classified jobs to Supabase
            # regardless of routing filters, so we bypass the view_fresh_quality filter
            # and store the complete DataFrame
            
            # Mark all jobs as fresh for storage (CSV jobs are always considered fresh)
            df_final = df_final.copy()
            df_final['sys.is_fresh_job'] = True
            
            # Directly store to Supabase without filtering by route.final_status
            from job_memory_db import JobMemoryDB
            memory_db = JobMemoryDB()
            
            # Store ALL jobs from CSV - including those with classification errors
            # CSV jobs should be stored regardless of AI classification status
            if len(df_final) > 0:
                success = memory_db.store_classifications(df_final)
                error_count = (df_final.get('ai.match', '') == 'error').sum() if 'ai.match' in df_final.columns else 0
                if success:
                    if error_count > 0:
                        print(f"✅ Stored {len(df_final)} jobs to Supabase ({error_count} had classification errors)")
                    else:
                        print(f"✅ Stored {len(df_final)} classified jobs to Supabase")
                else:
                    print(f"⚠️ Failed to store some jobs to Supabase")
            else:
                print("⚠️ No jobs to store")
                
        except Exception as e:
            print(f"⚠️ Storage failed: {e}")
            return 4
    else:
        print("\n(dry-run) Not storing to memory. Use --store to persist.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
