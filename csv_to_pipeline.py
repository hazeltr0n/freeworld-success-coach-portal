#!/usr/bin/env python3
"""
CSV to Pipeline Processor
Feed Outscraper CSV through existing Pipeline v3 instead of scraping fresh
"""

import os
import sys
import pandas as pd
import argparse
from datetime import datetime

# Add current directory to path for imports
sys.path.append('.')

def convert_csv_to_pipeline_format(csv_path: str, output_dir: str = "csv_pipeline_input") -> dict:
    """Convert Outscraper CSV to format that Pipeline v3 can process"""
    
    print(f"🔄 Converting CSV to Pipeline format...")
    
    # Load CSV
    df = pd.read_csv(csv_path)
    print(f"📊 Loaded {len(df)} jobs from CSV")
    
    # Show market breakdown
    market_counts = df['meta.market'].value_counts()
    print(f"📍 Markets found: {len(market_counts)}")
    for market, count in market_counts.items():
        print(f"   {market}: {count} jobs")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Group by market and create separate CSV files for each market
    market_files = {}
    
    for market, market_df in df.groupby('meta.market'):
        print(f"📝 Processing {market}: {len(market_df)} jobs")
        
        # Convert to pipeline-compatible format
        pipeline_df = pd.DataFrame()
        
        # Map fields to pipeline expected format - handle both raw and classified CSV formats
        # Check if this is a pre-classified CSV (has canonical schema columns)
        if 'source.title' in market_df.columns:
            # Pre-classified CSV format 
            pipeline_df['job_id'] = market_df['id.job'].fillna('')
            pipeline_df['title'] = market_df['source.title'].fillna('')
            pipeline_df['company'] = market_df['source.company'].fillna('')
            pipeline_df['location'] = market_df['source.location_raw'].fillna('')
            pipeline_df['description'] = market_df['source.description_raw'].fillna('')
            pipeline_df['apply_url'] = market_df['source.url'].fillna('')
            pipeline_df['indeed_url'] = market_df['source.url'].fillna('')
        else:
            # Raw outscraper CSV format
            pipeline_df['job_id'] = market_df['viewJobLink'].apply(lambda x: str(hash(x))[-8:] if pd.notna(x) else '')
            pipeline_df['title'] = market_df['title'].fillna('')
            pipeline_df['company'] = market_df['company'].fillna('')
            pipeline_df['location'] = market_df['formattedLocation'].fillna('')
            pipeline_df['description'] = market_df['snippet'].fillna('')
            pipeline_df['apply_url'] = market_df['viewJobLink'].fillna('')
            pipeline_df['indeed_url'] = market_df['viewJobLink'].fillna('')
        
        # Process salary - handle different input formats
        salary_parts = []
        for _, row in market_df.iterrows():
            try:
                # Try processed salary fields first (from classified CSV)
                if 'source.salary_raw' in market_df.columns and pd.notna(row.get('source.salary_raw')):
                    salary_parts.append(str(row['source.salary_raw']))
                # Fallback to outscraper format
                elif 'salarySnippet_baseSalary_range_min' in market_df.columns:
                    min_sal = float(row.get('salarySnippet_baseSalary_range_min', 0)) if pd.notna(row.get('salarySnippet_baseSalary_range_min')) else None
                    max_sal = float(row.get('salarySnippet_baseSalary_range_max', 0)) if pd.notna(row.get('salarySnippet_baseSalary_range_max')) else None
                    unit = str(row.get('salarySnippet_baseSalary_unitOfWork', 'year')).lower() if pd.notna(row.get('salarySnippet_baseSalary_unitOfWork')) else 'year'
                    
                    if min_sal and max_sal:
                        salary_parts.append(f"${min_sal:,.0f} - ${max_sal:,.0f} per {unit}")
                    else:
                        salary_parts.append('')
                else:
                    salary_parts.append('')
            except (ValueError, TypeError):
                salary_parts.append('')
        
        pipeline_df['salary'] = salary_parts
        
        # Add metadata
        pipeline_df['source'] = 'outscraper'
        pipeline_df['scraped_at'] = datetime.now().isoformat()
        pipeline_df['market'] = market
        
        # Convert timestamps - handle different formats
        if 'source.posted_date' in market_df.columns:
            # Pre-classified CSV format
            pipeline_df['posted_date'] = market_df['source.posted_date'].fillna('')
        elif 'pubDate' in market_df.columns:
            # Raw outscraper format  
            pipeline_df['posted_date'] = pd.to_datetime(market_df['pubDate'], unit='ms', errors='coerce').dt.strftime('%Y-%m-%d')
        else:
            pipeline_df['posted_date'] = ''
        
        # Save market-specific CSV file
        market_slug = market.lower().replace(' ', '_')
        output_file = os.path.join(output_dir, f"{market_slug}_jobs.csv")
        pipeline_df.to_csv(output_file, index=False)
        
        market_files[market] = {
            'file': output_file,
            'jobs': len(pipeline_df),
            'slug': market_slug
        }
        
        print(f"   ✅ Saved {market}: {output_file}")
    
    print(f"✅ Conversion complete: {len(market_files)} market files created")
    return market_files

def run_pipeline_on_markets(market_files: dict, max_jobs_per_market: int = None, 
                           sample_markets: list = None, use_classification: bool = False):
    """Run Pipeline v3 on each market's CSV file"""
    
    from pipeline_v3 import FreeWorldPipelineV3
    
    print(f"\n🚀 Running Pipeline v3 on markets...")
    
    # Filter markets if specified
    if sample_markets:
        market_files = {k: v for k, v in market_files.items() if k in sample_markets}
        print(f"🎯 Processing sample markets: {list(market_files.keys())}")
    
    pipeline = FreeWorldPipelineV3()
    results = {}
    
    for market, info in market_files.items():
        print(f"\n📍 Processing {market}...")
        
        # Determine job limit
        job_limit = min(info['jobs'], max_jobs_per_market) if max_jobs_per_market else info['jobs']
        mode_info = {'mode': 'import', 'limit': job_limit}
        
        try:
            # Run pipeline with CSV input instead of fresh scraping
            result = pipeline.run_complete_pipeline(
                location=market,
                mode_info=mode_info,
                search_terms="CDL Driver",
                route_filter="both",
                push_to_airtable=False,
                force_fresh=False,
                force_fresh_classification=use_classification,
                force_memory_only=False,  # We want to process the CSV, not use memory
                generate_pdf=True,
                generate_csv=True,
                csv_input_file=info['file']  # Feed our converted CSV
            )
            
            results[market] = result
            print(f"   ✅ {market} pipeline complete")
            
            if result.get('success'):
                print(f"      Total jobs: {result.get('total_jobs', 0)}")
                print(f"      Quality jobs: {result.get('quality_jobs', 0)}")
                if result.get('files'):
                    for file_type, file_path in result.get('files', {}).items():
                        print(f"      {file_type}: {file_path}")
            else:
                print(f"      ❌ Pipeline failed for {market}")
                
        except Exception as e:
            print(f"   ❌ Pipeline error for {market}: {e}")
            results[market] = {'success': False, 'error': str(e)}
    
    return results

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Process Outscraper CSV through Pipeline v3')
    parser.add_argument('csv_path', help='Path to Outscraper CSV file')
    parser.add_argument('--max-jobs', type=int, help='Max jobs per market (for testing)')
    parser.add_argument('--markets', nargs='*', help='Only process specific markets')
    parser.add_argument('--no-classify', action='store_true', help='Skip AI classification')
    parser.add_argument('--output-dir', default='csv_pipeline_input', help='Directory for converted CSV files')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_path):
        print(f"❌ CSV file not found: {args.csv_path}")
        sys.exit(1)
    
    print(f"🔍 CSV TO PIPELINE PROCESSOR")
    print(f"=" * 60)
    print(f"📄 Input CSV: {args.csv_path}")
    print(f"📁 Output directory: {args.output_dir}")
    print(f"🤖 AI Classification: {'Disabled' if args.no_classify else 'Enabled'}")
    if args.max_jobs:
        print(f"🔢 Max jobs per market: {args.max_jobs}")
    if args.markets:
        print(f"🎯 Target markets: {args.markets}")
    print()
    
    # Step 1: Convert CSV to pipeline format
    market_files = convert_csv_to_pipeline_format(args.csv_path, args.output_dir)
    
    # Step 2: Run pipeline on each market
    results = run_pipeline_on_markets(
        market_files=market_files,
        max_jobs_per_market=args.max_jobs,
        sample_markets=args.markets,
        use_classification=not args.no_classify
    )
    
    # Step 3: Summary
    print(f"\n📊 PROCESSING SUMMARY")
    print(f"=" * 60)
    
    successful = 0
    total_jobs_processed = 0
    total_quality_jobs = 0
    
    for market, result in results.items():
        if result.get('success'):
            successful += 1
            total_jobs_processed += result.get('total_jobs', 0)
            total_quality_jobs += result.get('quality_jobs', 0)
            print(f"✅ {market}: {result.get('total_jobs', 0)} jobs → {result.get('quality_jobs', 0)} quality")
        else:
            print(f"❌ {market}: Failed - {result.get('error', 'Unknown error')}")
    
    print(f"\n📈 TOTALS:")
    print(f"   Markets processed: {successful}/{len(results)}")
    print(f"   Total jobs: {total_jobs_processed}")
    print(f"   Quality jobs: {total_quality_jobs}")
    print(f"   Success rate: {successful/len(results)*100:.1f}%")
    
    sys.exit(0 if successful > 0 else 1)

if __name__ == "__main__":
    main()