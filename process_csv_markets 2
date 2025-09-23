#!/usr/bin/env python3
"""
Process CSV Markets through Existing Pipeline
Use existing pipeline infrastructure to classify CSV jobs by market
"""

import os
import sys
import pandas as pd
import argparse
import subprocess
from datetime import datetime

def analyze_csv_markets(csv_path: str):
    """Analyze CSV and show market breakdown"""
    
    df = pd.read_csv(csv_path)
    print(f"📊 CSV Analysis:")
    print(f"   Total jobs: {len(df):,}")
    
    market_counts = df['meta.market'].value_counts()
    print(f"   Markets found: {len(market_counts)}")
    
    market_info = {}
    for market, count in market_counts.items():
        market_info[market] = count
        print(f"      {market}: {count:,} jobs")
    
    return market_info, df

def save_market_csv(df: pd.DataFrame, market: str, output_dir: str) -> str:
    """Save market-specific CSV in format compatible with existing tools"""
    
    market_df = df[df['meta.market'] == market].copy()
    
    # Create simplified CSV with essential fields for classification
    simple_df = pd.DataFrame()
    simple_df['job_id'] = market_df['viewJobLink'].apply(lambda x: str(hash(x))[-8:] if pd.notna(x) else '')
    simple_df['job_title'] = market_df['title'].fillna('')  # Fixed: job_title not title
    simple_df['company'] = market_df['company'].fillna('')  
    simple_df['location'] = market_df['formattedLocation'].fillna('')
    simple_df['job_description'] = market_df['snippet'].fillna('')  # Fixed: job_description not description
    simple_df['apply_url'] = market_df['viewJobLink'].fillna('')
    simple_df['indeed_url'] = market_df['viewJobLink'].fillna('')
    simple_df['source'] = 'outscraper_csv'
    simple_df['market'] = market
    simple_df['scraped_at'] = datetime.now().isoformat()
    
    # Process salary
    salary_parts = []
    for _, row in market_df.iterrows():
        try:
            min_sal = float(row.get('salarySnippet_baseSalary_range_min', 0)) if pd.notna(row.get('salarySnippet_baseSalary_range_min')) else None
            max_sal = float(row.get('salarySnippet_baseSalary_range_max', 0)) if pd.notna(row.get('salarySnippet_baseSalary_range_max')) else None
            unit = str(row.get('salarySnippet_baseSalary_unitOfWork', 'year')).lower() if pd.notna(row.get('salarySnippet_baseSalary_unitOfWork')) else 'year'
            
            if min_sal and max_sal:
                salary_parts.append(f"${min_sal:,.0f} - ${max_sal:,.0f} per {unit}")
            else:
                salary_parts.append('')
        except (ValueError, TypeError):
            salary_parts.append('')
    
    simple_df['salary'] = salary_parts
    
    # Save to output directory  
    os.makedirs(output_dir, exist_ok=True)
    market_slug = market.lower().replace(' ', '_')
    output_file = os.path.join(output_dir, f"{market_slug}_outscraper_import.csv")
    simple_df.to_csv(output_file, index=False)
    
    return output_file

def run_classification_on_csv(csv_file: str, market: str):
    """Run job classification on CSV file using existing classifier"""
    
    print(f"🤖 Classifying {market} jobs from {csv_file}...")
    
    try:
        # Import and use the existing job classifier
        sys.path.append('.')
        from job_classifier import JobClassifier
        
        # Load the CSV
        df = pd.read_csv(csv_file)
        print(f"   📊 Loaded {len(df)} jobs for classification")
        
        # Initialize classifier
        classifier = JobClassifier()
        
        # Classify in batches
        batch_size = 25
        classified_jobs = []
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size].copy()
            print(f"   📝 Classifying batch {i//batch_size + 1}: jobs {i+1}-{min(i+batch_size, len(df))}")
            
            try:
                classified_batch = classifier.classify_jobs(batch)
                classified_jobs.append(classified_batch)
            except Exception as e:
                print(f"      ❌ Batch classification failed: {e}")
                # Add unclassified batch with default values
                batch['match'] = 'error'
                batch['reason'] = f'Classification failed: {str(e)}'
                batch['summary'] = batch['description'].str[:100] + '...'
                classified_jobs.append(batch)
        
        # Combine all classified jobs
        if classified_jobs:
            final_df = pd.concat(classified_jobs, ignore_index=True)
            
            # Save classified results
            output_file = csv_file.replace('.csv', '_classified.csv')
            final_df.to_csv(output_file, index=False)
            
            # Show results
            if 'match' in final_df.columns:
                match_counts = final_df['match'].value_counts()
                print(f"   📊 Classification results: {dict(match_counts)}")
                quality_jobs = len(final_df[final_df['match'].isin(['good', 'so-so'])])
                print(f"   ✅ Quality jobs: {quality_jobs}/{len(final_df)} ({quality_jobs/len(final_df)*100:.1f}%)")
            
            return output_file, final_df
        else:
            print(f"   ❌ No jobs classified successfully")
            return None, None
            
    except Exception as e:
        print(f"   ❌ Classification failed: {e}")
        return None, None

def upload_to_supabase(classified_df: pd.DataFrame, market: str):
    """Upload classified jobs to Supabase"""
    
    if classified_df is None or classified_df.empty:
        print(f"   ❌ No classified data to upload for {market}")
        return False
    
    print(f"💾 Uploading {market} to Supabase...")
    
    try:
        from job_memory_db import JobMemoryDB
        db = JobMemoryDB()
        
        # Convert to format expected by Supabase
        supabase_df = classified_df.copy()
        
        # Add required fields for Supabase storage
        supabase_df['classification_source'] = 'csv_import'
        supabase_df['classified_at'] = datetime.now().isoformat()
        supabase_df['coach_username'] = 'csv_import'
        
        # Upload in batches
        batch_size = 50
        uploaded = 0
        
        for i in range(0, len(supabase_df), batch_size):
            batch = supabase_df.iloc[i:i+batch_size]
            print(f"   📤 Uploading batch {i//batch_size + 1}: jobs {i+1}-{min(i+batch_size, len(supabase_df))}")
            
            try:
                success = db.store_classifications(batch)
                if success:
                    uploaded += len(batch)
                    print(f"      ✅ Batch uploaded successfully")
                else:
                    print(f"      ❌ Batch upload failed: store_classifications returned False")
            except Exception as e:
                print(f"      ❌ Batch upload error: {e}")
                continue
        
        print(f"   ✅ Upload complete: {uploaded}/{len(supabase_df)} jobs uploaded to Supabase")
        return uploaded > 0
        
    except Exception as e:
        print(f"   ❌ Supabase upload failed: {e}")
        return False

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Process Outscraper CSV markets through existing pipeline')
    parser.add_argument('csv_path', help='Path to Outscraper CSV file')
    parser.add_argument('--markets', nargs='*', help='Only process specific markets')
    parser.add_argument('--max-jobs', type=int, help='Max jobs per market (for testing)')
    parser.add_argument('--output-dir', default='csv_market_processing', help='Output directory')
    parser.add_argument('--no-upload', action='store_true', help='Skip Supabase upload')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_path):
        print(f"❌ CSV file not found: {args.csv_path}")
        sys.exit(1)
    
    print(f"🔍 CSV MARKET PROCESSOR")
    print(f"=" * 60)
    print(f"📄 Input: {args.csv_path}")
    print(f"📁 Output: {args.output_dir}")
    if args.markets:
        print(f"🎯 Markets: {args.markets}")
    if args.max_jobs:
        print(f"🔢 Max jobs per market: {args.max_jobs}")
    print()
    
    # Step 1: Analyze CSV
    market_info, df = analyze_csv_markets(args.csv_path)
    
    # Step 2: Filter markets if specified
    if args.markets:
        market_info = {k: v for k, v in market_info.items() if k in args.markets}
        df = df[df['meta.market'].isin(args.markets)]
        print(f"🎯 Filtered to markets: {list(market_info.keys())}")
    
    # Step 3: Process each market
    results = {}
    total_processed = 0
    total_uploaded = 0
    
    for market, job_count in market_info.items():
        print(f"\n📍 Processing {market} ({job_count:,} jobs)...")
        
        # Limit jobs if specified
        market_df = df[df['meta.market'] == market]
        if args.max_jobs:
            market_df = market_df.head(args.max_jobs)
            print(f"   🔢 Limited to {len(market_df)} jobs")
        
        # Save market CSV
        csv_file = save_market_csv(df, market, args.output_dir)
        print(f"   💾 Saved: {csv_file}")
        
        # Classify jobs
        classified_file, classified_df = run_classification_on_csv(csv_file, market)
        
        if classified_df is not None:
            total_processed += len(classified_df)
            
            # Upload to Supabase
            if not args.no_upload:
                upload_success = upload_to_supabase(classified_df, market)
                if upload_success:
                    quality_jobs = len(classified_df[classified_df['match'].isin(['good', 'so-so'])])
                    total_uploaded += quality_jobs
            
            results[market] = {
                'success': True,
                'jobs': len(classified_df),
                'classified_file': classified_file
            }
        else:
            results[market] = {
                'success': False,
                'jobs': 0,
                'error': 'Classification failed'
            }
    
    # Step 4: Summary
    print(f"\n📊 PROCESSING SUMMARY")
    print(f"=" * 60)
    
    successful_markets = sum(1 for r in results.values() if r['success'])
    
    for market, result in results.items():
        if result['success']:
            print(f"✅ {market}: {result['jobs']} jobs classified")
            if result.get('classified_file'):
                print(f"   📄 File: {result['classified_file']}")
        else:
            print(f"❌ {market}: {result.get('error', 'Failed')}")
    
    print(f"\n📈 TOTALS:")
    print(f"   Markets processed: {successful_markets}/{len(results)}")
    print(f"   Jobs classified: {total_processed:,}")
    if not args.no_upload:
        print(f"   Jobs uploaded to Supabase: {total_uploaded:,}")
    print(f"   Success rate: {successful_markets/len(results)*100:.1f}%")
    
    sys.exit(0 if successful_markets > 0 else 1)

if __name__ == "__main__":
    main()