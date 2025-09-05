#!/usr/bin/env python3
"""
Backfill missing URLs from backup fields
Uses indeed_job_url and clean_apply_url to fill missing apply_url fields
"""

import pandas as pd
import numpy as np

def backfill_missing_urls(df: pd.DataFrame) -> pd.DataFrame:
    """Backfill missing URLs using available backup fields"""
    print("🔄 Backfilling missing URLs...")
    
    # Track initial state
    initial_missing = (df['apply_url'].isna() | (df['apply_url'] == '')).sum()
    print(f"  📊 Initial missing URLs: {initial_missing}/{len(df)} ({100*initial_missing/len(df):.1f}%)")
    
    # Create mask for jobs missing URLs
    missing_url_mask = df['apply_url'].isna() | (df['apply_url'] == '')
    
    # Strategy 1: Use indeed_job_url
    indeed_available = (
        missing_url_mask & 
        df['indeed_job_url'].notna() & 
        (df['indeed_job_url'] != '')
    )
    
    filled_from_indeed = indeed_available.sum()
    if filled_from_indeed > 0:
        df.loc[indeed_available, 'apply_url'] = df.loc[indeed_available, 'indeed_job_url']
        print(f"    ✅ Filled {filled_from_indeed} URLs from indeed_job_url")
        # Update missing mask
        missing_url_mask = df['apply_url'].isna() | (df['apply_url'] == '')
    
    # Strategy 2: Use clean_apply_url
    clean_available = (
        missing_url_mask & 
        df['clean_apply_url'].notna() & 
        (df['clean_apply_url'] != '')
    )
    
    filled_from_clean = clean_available.sum()
    if filled_from_clean > 0:
        df.loc[clean_available, 'apply_url'] = df.loc[clean_available, 'clean_apply_url']
        print(f"    ✅ Filled {filled_from_clean} URLs from clean_apply_url")
        # Update missing mask
        missing_url_mask = df['apply_url'].isna() | (df['apply_url'] == '')
    
    # Strategy 3: Generate fallback URLs for known patterns
    # For jobs that still don't have URLs, try to construct them
    still_missing = missing_url_mask.sum()
    
    if still_missing > 0:
        print(f"    🔧 Attempting to construct URLs for {still_missing} remaining jobs...")
        
        # Look for patterns in job descriptions or company names that might help
        # For now, we'll mark these as needing manual review
        constructed_count = 0
        
        # Check if there are any URL patterns in job descriptions
        for idx in df[missing_url_mask].index:
            job_desc = df.loc[idx, 'job_description']
            if pd.notna(job_desc) and 'http' in str(job_desc).lower():
                # Try to extract URL from description
                import re
                urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str(job_desc))
                if urls:
                    df.loc[idx, 'apply_url'] = urls[0]
                    constructed_count += 1
        
        if constructed_count > 0:
            print(f"    ✅ Constructed {constructed_count} URLs from job descriptions")
    
    # Final report
    final_missing = (df['apply_url'].isna() | (df['apply_url'] == '')).sum()
    final_coverage = len(df) - final_missing
    
    print(f"  🎯 Final URL coverage: {final_coverage}/{len(df)} ({100*final_coverage/len(df):.1f}%)")
    print(f"  📉 Reduced missing URLs from {initial_missing} to {final_missing} ({initial_missing - final_missing} filled)")
    
    return df

def validate_urls(df: pd.DataFrame) -> pd.DataFrame:
    """Basic URL validation and cleanup"""
    print("🔍 Validating URLs...")
    
    # Clean up URL formatting
    df['apply_url'] = df['apply_url'].astype(str).str.strip()
    
    # Remove 'nan' string values
    df.loc[df['apply_url'] == 'nan', 'apply_url'] = ''
    
    # Basic URL validation
    import re
    url_pattern = re.compile(r'^https?://', re.IGNORECASE)
    
    has_url = (df['apply_url'] != '') & df['apply_url'].notna()
    valid_urls = has_url & df['apply_url'].str.match(url_pattern, na=False)
    invalid_urls = has_url & ~df['apply_url'].str.match(url_pattern, na=False)
    
    invalid_count = invalid_urls.sum()
    
    if invalid_count > 0:
        print(f"  ⚠️  Found {invalid_count} URLs without http/https prefix")
        print("    Sample invalid URLs:")
        sample_invalid = df[invalid_urls]['apply_url'].head(3)
        for url in sample_invalid:
            print(f"      - {url}")
        
        # Fix URLs missing protocol
        df.loc[invalid_urls, 'apply_url'] = 'https://' + df.loc[invalid_urls, 'apply_url']
        print(f"    ✅ Fixed {invalid_count} URLs by adding https:// prefix")
    
    valid_count = (df['apply_url'] != '').sum()
    print(f"  ✅ {valid_count} valid URLs found")
    
    return df

def main():
    """Main backfill function"""
    input_file = '/Users/freeworld_james/Desktop/freeworld-job-scraper/streamlit-app/jobs_cleaned.csv'
    output_file = '/Users/freeworld_james/Desktop/freeworld-job-scraper/streamlit-app/jobs_final.csv'
    
    print("🔄 Starting URL Backfill Process")
    print(f"📥 Reading: {input_file}")
    
    try:
        # Load cleaned data
        df = pd.read_csv(input_file)
        print(f"✅ Loaded {len(df)} cleaned jobs")
        
        # Backfill missing URLs
        df = backfill_missing_urls(df)
        
        # Validate and fix URLs
        df = validate_urls(df)
        
        # Save final result
        print(f"\n💾 Saving final data to: {output_file}")
        df.to_csv(output_file, index=False)
        print("✅ Backfill complete!")
        
        # Final summary
        total_jobs = len(df)
        jobs_with_urls = (df['apply_url'] != '').sum()
        jobs_without_urls = total_jobs - jobs_with_urls
        
        print(f"\n📋 FINAL SUMMARY:")
        print(f"  Total jobs: {total_jobs}")
        print(f"  Jobs with URLs: {jobs_with_urls} ({100*jobs_with_urls/total_jobs:.1f}%)")
        print(f"  Jobs without URLs: {jobs_without_urls} ({100*jobs_without_urls/total_jobs:.1f}%)")
        
        return df
        
    except Exception as e:
        print(f"❌ Error during backfill: {e}")
        raise

if __name__ == "__main__":
    main()