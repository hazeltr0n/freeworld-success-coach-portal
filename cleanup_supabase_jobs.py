#!/usr/bin/env python3
"""
Supabase Jobs Data Cleanup Script
Cleans up market values and URL fields based on user requirements
"""

import pandas as pd
import numpy as np
import sys
from typing import Dict, Set

def clean_market_values(df: pd.DataFrame) -> pd.DataFrame:
    """Clean up market values according to specifications"""
    print("🧹 Cleaning market values...")
    
    # Define valid markets
    valid_markets = {
        'Houston', 'Dallas', 'Bay Area', 'Stockton', 'Denver', 
        'Las Vegas', 'Newark', 'Phoenix', 'Trenton', 'Inland Empire'
    }
    
    # Custom locations that are allowed
    allowed_custom_locations = {'Austin, TX'}
    
    # Market value mappings
    market_mappings = {
        'Bay Area, CA': 'Bay Area',
        'Austin': 'Austin, TX',  # Standardize Austin entries
        'San Antonio, TX': None,  # Remove - not a valid market
        'Montgomery, AL': None,   # Remove - not a valid market
        'Montgomery': None,       # Remove - not a valid market
        'Lubbock, TX': None,     # Remove - not a valid market
        'Ontario': None,         # Remove - ambiguous
        'Fort Worth, TX': 'Dallas',  # Map Fort Worth to Dallas market
        'Berkeley': 'Bay Area',   # Map Berkeley to Bay Area
        'Los Angeles': 'Inland Empire',  # Map LA to Inland Empire market
    }
    
    # Apply mappings
    original_count = len(df)
    
    # First, apply direct mappings
    for old_market, new_market in market_mappings.items():
        mask = df['market'] == old_market
        if new_market is None:
            # Mark for deletion
            print(f"  📍 Removing {mask.sum()} jobs with invalid market: '{old_market}'")
            df = df[~mask].copy()
        else:
            print(f"  📍 Converting '{old_market}' → '{new_market}' ({mask.sum()} jobs)")
            df.loc[mask, 'market'] = new_market
    
    # Remove jobs with no market (NaN)
    no_market_mask = df['market'].isna()
    no_market_count = no_market_mask.sum()
    if no_market_count > 0:
        print(f"  📍 Removing {no_market_count} jobs with no market value")
        df = df[~no_market_mask].copy()
    
    # Verify all remaining markets are valid
    remaining_markets = set(df['market'].unique())
    valid_all = valid_markets.union(allowed_custom_locations)
    invalid_markets = remaining_markets - valid_all
    
    if invalid_markets:
        print(f"  ⚠️  WARNING: Found unexpected markets: {invalid_markets}")
        for invalid_market in invalid_markets:
            count = (df['market'] == invalid_market).sum()
            print(f"    - '{invalid_market}': {count} jobs")
    
    final_count = len(df)
    removed_count = original_count - final_count
    print(f"  ✅ Market cleanup complete: {removed_count} jobs removed, {final_count} jobs remaining")
    
    return df.reset_index(drop=True)

def consolidate_urls(df: pd.DataFrame) -> pd.DataFrame:
    """Consolidate URLs into apply_url field with fallback chain"""
    print("🔗 Consolidating URLs...")
    
    # Priority chain: apply_url -> indeed_job_url -> clean_apply_url -> google_job_url
    url_fields = ['apply_url', 'indeed_job_url', 'clean_apply_url', 'google_job_url']
    
    # Count current coverage
    print("  📊 Current URL field coverage:")
    for field in url_fields:
        non_empty = df[field].notna() & (df[field] != '')
        print(f"    {field}: {non_empty.sum()}/{len(df)} ({100*non_empty.sum()/len(df):.1f}%)")
    
    # Create consolidated apply_url
    consolidated_url = pd.Series('', index=df.index)
    
    # Apply fallback chain
    for field in url_fields:
        # Fill empty consolidated URLs with values from current field
        mask = (consolidated_url == '') & df[field].notna() & (df[field] != '')
        consolidated_url.loc[mask] = df.loc[mask, field]
        
        filled_count = mask.sum()
        if filled_count > 0:
            print(f"    ✅ Filled {filled_count} URLs from {field}")
    
    # Update apply_url field
    df['apply_url'] = consolidated_url
    
    # Report final coverage
    final_coverage = (df['apply_url'] != '').sum()
    print(f"  🎯 Final URL coverage: {final_coverage}/{len(df)} ({100*final_coverage/len(df):.1f}%)")
    
    # Identify jobs still missing URLs
    missing_urls = df['apply_url'] == ''
    missing_count = missing_urls.sum()
    
    if missing_count > 0:
        print(f"  ⚠️  WARNING: {missing_count} jobs still have no URLs")
        print("    Sample jobs missing URLs:")
        sample_missing = df[missing_urls][['job_id', 'job_title', 'company', 'market']].head(5)
        for _, row in sample_missing.iterrows():
            print(f"      - {row['job_title']} at {row['company']} ({row['market']})")
    
    return df

def generate_cleanup_report(original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> None:
    """Generate a summary report of changes made"""
    print("\n" + "="*60)
    print("📋 CLEANUP SUMMARY REPORT")
    print("="*60)
    
    print(f"Original jobs: {len(original_df)}")
    print(f"Final jobs: {len(cleaned_df)}")
    print(f"Jobs removed: {len(original_df) - len(cleaned_df)}")
    print(f"Retention rate: {100 * len(cleaned_df) / len(original_df):.1f}%")
    
    print("\n📊 Final Market Distribution:")
    market_counts = cleaned_df['market'].value_counts()
    for market, count in market_counts.items():
        percentage = 100 * count / len(cleaned_df)
        print(f"  {market}: {count} jobs ({percentage:.1f}%)")
    
    print("\n🔗 URL Coverage:")
    url_coverage = (cleaned_df['apply_url'] != '').sum()
    print(f"  Jobs with URLs: {url_coverage}/{len(cleaned_df)} ({100*url_coverage/len(cleaned_df):.1f}%)")
    print(f"  Jobs without URLs: {len(cleaned_df) - url_coverage} ({100*(len(cleaned_df) - url_coverage)/len(cleaned_df):.1f}%)")

def main():
    """Main cleanup function"""
    input_file = '/Users/freeworld_james/Downloads/jobs_rows (1).csv'
    output_file = '/Users/freeworld_james/Desktop/freeworld-job-scraper/streamlit-app/jobs_cleaned.csv'
    
    print("🚀 Starting Supabase Jobs Cleanup")
    print(f"📥 Reading: {input_file}")
    
    try:
        # Load the data
        original_df = pd.read_csv(input_file)
        print(f"✅ Loaded {len(original_df)} jobs")
        
        # Make a copy for processing
        df = original_df.copy()
        
        # Step 1: Clean market values
        df = clean_market_values(df)
        
        # Step 2: Consolidate URLs
        df = consolidate_urls(df)
        
        # Step 3: Generate report
        generate_cleanup_report(original_df, df)
        
        # Step 4: Save cleaned data
        print(f"\n💾 Saving cleaned data to: {output_file}")
        df.to_csv(output_file, index=False)
        print("✅ Cleanup complete!")
        
        return df
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        raise

if __name__ == "__main__":
    main()