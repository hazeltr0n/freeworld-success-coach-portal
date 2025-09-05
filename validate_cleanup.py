#!/usr/bin/env python3
"""
Validation script for cleaned Supabase data
Ensures data quality before upload
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Set

def validate_markets(df: pd.DataFrame) -> bool:
    """Validate all market values are correct"""
    print("📍 Validating markets...")
    
    valid_markets = {
        'Houston', 'Dallas', 'Bay Area', 'Stockton', 'Denver', 
        'Las Vegas', 'Newark', 'Phoenix', 'Trenton', 'Inland Empire',
        'Austin, TX'  # Custom location
    }
    
    # Check for any invalid markets
    unique_markets = set(df['market'].unique())
    invalid_markets = unique_markets - valid_markets
    
    if invalid_markets:
        print(f"  ❌ Invalid markets found: {invalid_markets}")
        return False
    
    # Check for missing markets
    null_markets = df['market'].isna().sum()
    if null_markets > 0:
        print(f"  ❌ {null_markets} jobs have no market")
        return False
    
    print(f"  ✅ All {len(unique_markets)} markets are valid")
    for market in sorted(unique_markets):
        count = (df['market'] == market).sum()
        print(f"    {market}: {count} jobs")
    
    return True

def validate_urls(df: pd.DataFrame) -> bool:
    """Validate URL coverage and format"""
    print("🔗 Validating URLs...")
    
    # Check coverage
    has_url = df['apply_url'].notna() & (df['apply_url'] != '')
    url_coverage = has_url.sum()
    
    print(f"  📊 URL coverage: {url_coverage}/{len(df)} ({100*url_coverage/len(df):.1f}%)")
    
    if url_coverage < len(df):
        missing = len(df) - url_coverage
        print(f"  ⚠️ {missing} jobs missing URLs")
        
        # Show sample missing URLs
        no_url_jobs = df[~has_url][['job_title', 'company', 'market']].head(5)
        print("    Sample jobs without URLs:")
        for _, job in no_url_jobs.iterrows():
            print(f"      - {job['job_title']} at {job['company']} ({job['market']})")
    
    # Validate URL format
    if url_coverage > 0:
        urls_with_protocol = df[has_url]['apply_url'].str.startswith(('http://', 'https://'))
        valid_url_count = urls_with_protocol.sum()
        
        print(f"  🌐 Valid URL format: {valid_url_count}/{url_coverage} ({100*valid_url_count/url_coverage:.1f}%)")
        
        if valid_url_count < url_coverage:
            invalid_count = url_coverage - valid_url_count
            print(f"  ⚠️ {invalid_count} URLs missing http/https protocol")
    
    return url_coverage == len(df)  # Require 100% coverage

def validate_essential_fields(df: pd.DataFrame) -> bool:
    """Validate essential fields are present"""
    print("📋 Validating essential fields...")
    
    essential_fields = {
        'job_id': 'Job ID',
        'job_title': 'Job Title', 
        'company': 'Company',
        'location': 'Location',
        'apply_url': 'Apply URL',
        'market': 'Market',
        'match_level': 'Match Level'
    }
    
    all_valid = True
    
    for field, display_name in essential_fields.items():
        if field not in df.columns:
            print(f"  ❌ Missing column: {field}")
            all_valid = False
            continue
            
        null_count = df[field].isna().sum()
        empty_count = (df[field] == '').sum() if df[field].dtype == 'object' else 0
        missing_count = null_count + empty_count
        
        if missing_count > 0:
            print(f"  ⚠️ {display_name}: {missing_count}/{len(df)} missing ({100*missing_count/len(df):.1f}%)")
        else:
            print(f"  ✅ {display_name}: Complete")
    
    return all_valid

def validate_data_integrity(df: pd.DataFrame) -> bool:
    """Validate data integrity"""
    print("🔍 Validating data integrity...")
    
    # Check for duplicate job IDs
    duplicate_ids = df['job_id'].duplicated().sum()
    if duplicate_ids > 0:
        print(f"  ❌ {duplicate_ids} duplicate job IDs found")
        return False
    else:
        print("  ✅ All job IDs are unique")
    
    # Check match levels
    valid_match_levels = {'good', 'so-so', 'bad'}
    invalid_matches = ~df['match_level'].isin(valid_match_levels)
    invalid_match_count = invalid_matches.sum()
    
    if invalid_match_count > 0:
        print(f"  ❌ {invalid_match_count} invalid match levels")
        unique_invalid = df[invalid_matches]['match_level'].unique()
        print(f"    Invalid values: {list(unique_invalid)}")
        return False
    else:
        print("  ✅ All match levels are valid")
    
    return True

def generate_quality_report(df: pd.DataFrame) -> None:
    """Generate data quality report"""
    print("\\n" + "="*50)
    print("📊 DATA QUALITY REPORT")
    print("="*50)
    
    print(f"Total Records: {len(df):,}")
    print()
    
    # Market distribution
    print("📍 Market Distribution:")
    market_dist = df['market'].value_counts()
    for market, count in market_dist.items():
        pct = 100 * count / len(df)
        print(f"  {market}: {count:,} ({pct:.1f}%)")
    print()
    
    # Match level distribution
    print("⭐ Match Level Distribution:")
    match_dist = df['match_level'].value_counts()
    for level, count in match_dist.items():
        pct = 100 * count / len(df)
        print(f"  {level}: {count:,} ({pct:.1f}%)")
    print()
    
    # URL coverage
    url_coverage = (df['apply_url'].notna() & (df['apply_url'] != '')).sum()
    print(f"🔗 URL Coverage: {url_coverage:,}/{len(df):,} ({100*url_coverage/len(df):.1f}%)")
    print()
    
    # Data completeness
    print("📋 Field Completeness:")
    for col in ['job_title', 'company', 'location', 'job_description', 'salary']:
        if col in df.columns:
            complete = df[col].notna().sum()
            pct = 100 * complete / len(df)
            print(f"  {col}: {complete:,}/{len(df):,} ({pct:.1f}%)")

def main():
    """Main validation function"""
    input_file = '/Users/freeworld_james/Desktop/freeworld-job-scraper/streamlit-app/jobs_compliant.csv'
    
    print("🧪 Starting Data Quality Validation")
    print(f"📥 Reading: {input_file}")
    
    try:
        df = pd.read_csv(input_file)
        print(f"✅ Loaded {len(df):,} records")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return False
    
    print("\\n" + "="*50)
    print("🔬 RUNNING VALIDATION TESTS")
    print("="*50)
    
    # Run all validation tests
    validations = [
        validate_markets(df),
        validate_urls(df),
        validate_essential_fields(df),
        validate_data_integrity(df)
    ]
    
    all_passed = all(validations)
    
    print("\\n" + "="*50)
    print("📋 VALIDATION RESULTS")
    print("="*50)
    
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("✅ Data is ready for Supabase upload")
    else:
        print("❌ SOME VALIDATIONS FAILED")
        print("⚠️ Please fix issues before uploading to Supabase")
    
    # Generate quality report regardless
    generate_quality_report(df)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    if success:
        print("\\n✅ Validation completed successfully - data is ready!")
    else:
        print("\\n❌ Validation failed - data needs fixing")