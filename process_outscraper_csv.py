#!/usr/bin/env python3
"""
Process Outscraper CSV through Pipeline and Upload to Supabase
Handles multi-market CSV files with meta.market field
"""

import os
import sys
import pandas as pd
import argparse
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.append('.')

def outscraper_to_canonical(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Outscraper CSV format to canonical pipeline format"""
    
    print(f"🔄 Converting {len(df)} Outscraper jobs to canonical format...")
    
    # Create canonical DataFrame with proper field mapping
    canonical_df = pd.DataFrame()
    
    # === SOURCE IDENTIFICATION ===
    canonical_df['id.job'] = df['viewJobLink'].apply(lambda x: str(hash(x))[-8:] if pd.notna(x) else '')
    canonical_df['job_id'] = canonical_df['id.job']  # For classifier compatibility
    canonical_df['id.source'] = 'outscraper'
    canonical_df['id.source_row'] = df.index
    
    # === SOURCE DATA ===
    canonical_df['source.title'] = df['title'].fillna('')
    canonical_df['source.company'] = df['company'].fillna('')
    canonical_df['source.location_raw'] = df['formattedLocation'].fillna('')
    canonical_df['source.description_raw'] = df['snippet'].fillna('')
    canonical_df['source.apply_url'] = df['viewJobLink'].fillna('')
    canonical_df['source.indeed_url'] = df['viewJobLink'].fillna('')  # Same as apply_url for Indeed
    canonical_df['source.google_url'] = ''
    
    # Process salary information
    salary_parts = []
    if 'salarySnippet_baseSalary_range_min' in df.columns:
        min_sal = df['salarySnippet_baseSalary_range_min'].fillna('')
        max_sal = df['salarySnippet_baseSalary_range_max'].fillna('')
        unit = df['salarySnippet_baseSalary_unitOfWork'].fillna('')
        
        for i in df.index:
            try:
                min_val = float(min_sal.iloc[i]) if pd.notna(min_sal.iloc[i]) else None
                max_val = float(max_sal.iloc[i]) if pd.notna(max_sal.iloc[i]) else None
                unit_val = str(unit.iloc[i]).lower() if pd.notna(unit.iloc[i]) else 'year'
                
                if min_val and max_val:
                    salary_parts.append(f"${min_val:,.0f} - ${max_val:,.0f} per {unit_val}")
                else:
                    salary_parts.append('')
            except (ValueError, TypeError):
                salary_parts.append('')
    else:
        salary_parts = [''] * len(df)
    
    canonical_df['source.salary_raw'] = salary_parts
    
    # Convert timestamps
    if 'pubDate' in df.columns:
        canonical_df['source.posted_date'] = pd.to_datetime(df['pubDate'], unit='ms', errors='coerce').dt.strftime('%Y-%m-%d')
    else:
        canonical_df['source.posted_date'] = ''
    
    # === NORMALIZED FIELDS ===
    canonical_df['norm.title'] = canonical_df['source.title']
    canonical_df['norm.company'] = canonical_df['source.company']
    
    # Parse location
    locations = canonical_df['source.location_raw'].str.extract(r'([^,]+),\s*([A-Z]{2})')
    canonical_df['norm.city'] = locations[0].fillna('')
    canonical_df['norm.state'] = locations[1].fillna('')
    canonical_df['norm.location'] = canonical_df['source.location_raw']
    
    # Clean description (remove HTML)
    import re
    canonical_df['norm.description'] = canonical_df['source.description_raw'].apply(
        lambda x: re.sub(r'<[^>]+>', ' ', str(x)).strip() if pd.notna(x) else ''
    )
    
    # Parse salary
    canonical_df['norm.salary_display'] = canonical_df['source.salary_raw']
    canonical_df['norm.salary_min'] = 0.0
    canonical_df['norm.salary_max'] = 0.0
    canonical_df['norm.salary_unit'] = ''
    canonical_df['norm.salary_currency'] = 'USD'
    
    # === BUSINESS RULES (defaults) ===
    canonical_df['rules.is_owner_op'] = False
    canonical_df['rules.is_school_bus'] = False
    canonical_df['rules.has_experience_req'] = False
    canonical_df['rules.experience_years_min'] = 0
    canonical_df['rules.is_spam_source'] = False
    canonical_df['rules.duplicate_r1'] = False
    canonical_df['rules.duplicate_r2'] = False
    canonical_df['rules.collapse_group'] = ''
    
    # === AI CLASSIFICATION (empty - to be filled by pipeline) ===
    canonical_df['ai.match'] = ''
    canonical_df['ai.reason'] = ''
    canonical_df['ai.summary'] = ''
    canonical_df['ai.fair_chance'] = ''
    canonical_df['ai.endorsements'] = ''
    canonical_df['ai.route_type'] = ''
    canonical_df['ai.raw_response'] = ''
    
    # === ROUTING ===
    canonical_df['route.stage'] = 'imported'
    canonical_df['route.final_status'] = 'ready_for_classification'
    canonical_df['route.filtered'] = False
    canonical_df['route.ready_for_ai'] = True
    canonical_df['route.ready_for_export'] = False
    canonical_df['route.error'] = ''
    canonical_df['route.batch_id'] = ''
    
    # === META ===
    canonical_df['meta.market'] = df['meta.market'].fillna('')
    canonical_df['meta.query'] = df['query'].fillna('')
    canonical_df['meta.search_terms'] = 'CDL Driver'  # Default
    canonical_df['meta.tracked_url'] = ''
    canonical_df['meta.airtable_id'] = ''
    
    # === SEARCH PARAMETERS ===
    canonical_df['search.location'] = canonical_df['norm.location']
    canonical_df['search.custom_location'] = ''
    canonical_df['search.route_filter'] = 'both'
    canonical_df['search.mode'] = 'import'
    canonical_df['search.job_limit'] = 1000
    canonical_df['search.radius'] = 50
    canonical_df['search.exact_location'] = False
    canonical_df['search.no_experience'] = True
    canonical_df['search.force_fresh'] = False
    canonical_df['search.memory_only'] = False
    canonical_df['search.business_rules'] = True
    canonical_df['search.deduplication'] = True
    canonical_df['search.experience_filter'] = True
    canonical_df['search.model'] = 'gpt-4o-mini'
    canonical_df['search.batch_size'] = 25
    canonical_df['search.sources'] = 'outscraper'
    canonical_df['search.strategy'] = 'import'
    canonical_df['search.coach_username'] = 'system'
    
    # === AGENT FIELDS (empty) ===
    agent_fields = ['agent.uuid', 'agent.name', 'agent.first_name', 'agent.last_name', 
                   'agent.email', 'agent.phone', 'agent.city', 'agent.state',
                   'agent.coach_name', 'agent.coach_username', 'agent.preferred_route',
                   'agent.experience_years', 'agent.endorsements_held', 'agent.notes',
                   'agent.last_contact', 'agent.status']
    for field in agent_fields:
        canonical_df[field] = ''
    
    # === QA FIELDS ===
    canonical_df['qa.missing_required_fields'] = ''
    canonical_df['qa.flags'] = ''
    canonical_df['qa.last_validated_at'] = ''
    canonical_df['qa.data_quality_score'] = 0.0
    
    # === SYSTEM METADATA ===
    now = datetime.now().isoformat()
    canonical_df['sys.created_at'] = now
    canonical_df['sys.updated_at'] = now
    canonical_df['sys.classified_at'] = ''
    canonical_df['sys.run_id'] = f"csv_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    canonical_df['sys.version'] = 'v1.0.0'
    canonical_df['sys.classification_source'] = ''
    canonical_df['sys.is_fresh_job'] = True
    canonical_df['sys.model'] = ''
    canonical_df['sys.prompt_sha'] = ''
    canonical_df['sys.schema_sha'] = ''
    canonical_df['sys.coach'] = 'system'
    
    # === CLEAN FIELDS ===
    canonical_df['clean_apply_url'] = canonical_df['source.apply_url']
    
    print(f"✅ Converted to canonical format: {len(canonical_df)} jobs with {len(canonical_df.columns)} fields")
    return canonical_df

def process_csv_file(csv_path: str, classify: bool = True, upload: bool = True, 
                    max_jobs_per_market: int = None, sample_markets: list = None):
    """Process Outscraper CSV through pipeline and upload to Supabase"""
    
    print(f"🔍 OUTSCRAPER CSV PROCESSOR")
    print(f"=" * 60)
    
    # Load CSV
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return False
    
    df = pd.read_csv(csv_path)
    print(f"📊 Loaded CSV: {len(df)} jobs")
    
    # Show market breakdown
    market_counts = df['meta.market'].value_counts()
    print(f"📍 Markets found: {len(market_counts)}")
    for market, count in market_counts.items():
        print(f"   {market}: {count} jobs")
    
    # Filter by sample markets if specified
    if sample_markets:
        df = df[df['meta.market'].isin(sample_markets)]
        print(f"🎯 Filtered to sample markets {sample_markets}: {len(df)} jobs")
    
    # Limit jobs per market if specified
    if max_jobs_per_market:
        df = df.groupby('meta.market').head(max_jobs_per_market).reset_index(drop=True)
        print(f"🔢 Limited to {max_jobs_per_market} jobs per market: {len(df)} jobs")
    
    if df.empty:
        print("❌ No jobs to process after filtering")
        return False
    
    # Convert to canonical format
    canonical_df = outscraper_to_canonical(df)
    
    # Run AI classification if requested
    if classify:
        print(f"\n🤖 AI Classification...")
        try:
            from job_classifier import JobClassifier
            classifier = JobClassifier()
            
            # Classify in batches
            batch_size = 25
            for i in range(0, len(canonical_df), batch_size):
                batch = canonical_df.iloc[i:i+batch_size].copy()
                print(f"   Classifying batch {i//batch_size + 1}: jobs {i+1}-{min(i+batch_size, len(canonical_df))}")
                
                classified_batch = classifier.classify_jobs(batch)
                canonical_df.iloc[i:i+batch_size] = classified_batch
                
            print(f"✅ AI Classification complete")
            
            # Show classification results
            if 'ai.match' in canonical_df.columns:
                match_counts = canonical_df['ai.match'].value_counts()
                print(f"📊 Classification results: {dict(match_counts)}")
                
        except Exception as e:
            print(f"❌ AI Classification failed: {e}")
            print("   Continuing without classification...")
    
    # Upload to Supabase if requested
    if upload:
        print(f"\n💾 Supabase Upload...")
        try:
            from job_memory_db import JobMemoryDB
            db = JobMemoryDB()
            
            # Upload in batches
            batch_size = 50
            uploaded = 0
            for i in range(0, len(canonical_df), batch_size):
                batch = canonical_df.iloc[i:i+batch_size]
                print(f"   Uploading batch {i//batch_size + 1}: jobs {i+1}-{min(i+batch_size, len(canonical_df))}")
                
                try:
                    success = db.store_classifications(batch)
                    if success:
                        uploaded += len(batch)
                    else:
                        print(f"   ⚠️ Batch upload failed: store_classifications returned False")
                except Exception as e:
                    print(f"   ⚠️ Batch upload failed: {e}")
                    continue
                    
            print(f"✅ Supabase upload complete: {uploaded}/{len(canonical_df)} jobs uploaded")
            
        except Exception as e:
            print(f"❌ Supabase upload failed: {e}")
            return False
    
    # Save processed CSV for backup
    output_path = f"processed_outscraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    canonical_df.to_csv(output_path, index=False)
    print(f"💾 Saved processed CSV: {output_path}")
    
    print(f"\n✅ Processing complete!")
    return True

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Process Outscraper CSV through pipeline')
    parser.add_argument('csv_path', help='Path to Outscraper CSV file')
    parser.add_argument('--skip-classify', action='store_true', help='Skip AI classification (not recommended)')
    parser.add_argument('--no-upload', action='store_true', help='Skip Supabase upload')
    parser.add_argument('--max-jobs', type=int, help='Max jobs per market (for testing)')
    parser.add_argument('--markets', nargs='*', help='Only process specific markets')
    
    args = parser.parse_args()
    
    success = process_csv_file(
        csv_path=args.csv_path,
        classify=not args.skip_classify,
        upload=not args.no_upload,
        max_jobs_per_market=args.max_jobs,
        sample_markets=args.markets
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()