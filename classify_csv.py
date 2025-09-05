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
        raw_rows.append({
            "title": title,
            "company": company,
            "formattedLocation": location_raw,
            "viewJobLink": apply_url,
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
        
        print("\n💾 Storing to memory (Supabase) with tracking URLs…")
        try:
            pipe._stage8_storage(df_final, push_to_airtable=False)
            print(f"✅ Stored {included or total} classified jobs to memory with tracking URLs")
        except Exception as e:
            print(f"⚠️ Storage failed: {e}")
            return 4
    else:
        print("\n(dry-run) Not storing to memory. Use --store to persist.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
