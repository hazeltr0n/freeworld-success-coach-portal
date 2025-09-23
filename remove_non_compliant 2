#!/usr/bin/env python3
"""
Remove all non-compliant jobs from the dataset
Jobs without URLs cannot be used in the pipeline and will be filtered anyway
"""

import pandas as pd
import numpy as np

def remove_non_compliant_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """Remove jobs that don't meet compliance requirements"""
    print("🗑️ Removing non-compliant jobs...")
    
    original_count = len(df)
    
    # Remove jobs without URLs (primary compliance issue)
    has_url = df['apply_url'].notna() & (df['apply_url'] != '')
    compliant_df = df[has_url].copy()
    
    removed_no_url = original_count - len(compliant_df)
    print(f"  📊 Removed {removed_no_url} jobs without URLs")
    
    # Remove jobs without company names (secondary compliance issue)
    has_company = compliant_df['company'].notna() & (compliant_df['company'] != '')
    compliant_df = compliant_df[has_company].copy()
    
    removed_no_company = len(df[has_url]) - len(compliant_df)
    if removed_no_company > 0:
        print(f"  📊 Removed {removed_no_company} additional jobs without company names")
    
    final_count = len(compliant_df)
    total_removed = original_count - final_count
    
    print(f"  ✅ Compliance cleanup complete:")
    print(f"    Original: {original_count:,} jobs")
    print(f"    Final: {final_count:,} jobs")
    print(f"    Removed: {total_removed:,} jobs ({100*total_removed/original_count:.1f}%)")
    print(f"    Retention: {100*final_count/original_count:.1f}%")
    
    return compliant_df.reset_index(drop=True)

def validate_compliance(df: pd.DataFrame) -> bool:
    """Validate that all remaining jobs are compliant"""
    print("✅ Validating compliance...")
    
    # Check URLs
    missing_urls = (df['apply_url'].isna() | (df['apply_url'] == '')).sum()
    if missing_urls > 0:
        print(f"  ❌ {missing_urls} jobs still missing URLs")
        return False
    
    # Check companies
    missing_companies = (df['company'].isna() | (df['company'] == '')).sum()
    if missing_companies > 0:
        print(f"  ❌ {missing_companies} jobs still missing companies")
        return False
    
    # Check essential fields
    for field in ['job_id', 'job_title', 'location', 'market', 'match_level']:
        missing = df[field].isna().sum()
        if missing > 0:
            print(f"  ❌ {missing} jobs missing {field}")
            return False
    
    print("  ✅ All jobs are fully compliant!")
    print(f"    - {len(df):,} jobs with valid URLs")
    print(f"    - {len(df):,} jobs with company names") 
    print(f"    - {len(df):,} jobs with all essential fields")
    
    return True

def generate_compliance_report(df: pd.DataFrame) -> None:
    """Generate final compliance report"""
    print("\n" + "="*60)
    print("📋 FINAL COMPLIANCE REPORT")
    print("="*60)
    
    print(f"✅ Total Compliant Jobs: {len(df):,}")
    print(f"🔗 URL Coverage: 100% ({len(df):,}/{len(df):,})")
    print(f"🏢 Company Coverage: 100% ({len(df):,}/{len(df):,})")
    print()
    
    # Market distribution
    print("📍 Market Distribution (Compliant Jobs Only):")
    market_counts = df['market'].value_counts()
    for market, count in market_counts.items():
        pct = 100 * count / len(df)
        print(f"  {market}: {count:,} jobs ({pct:.1f}%)")
    print()
    
    # Quality distribution
    print("⭐ Quality Distribution:")
    quality_counts = df['match_level'].value_counts()
    for quality, count in quality_counts.items():
        pct = 100 * count / len(df)
        print(f"  {quality}: {count:,} jobs ({pct:.1f}%)")
    print()
    
    print("🚀 Ready for:")
    print("  - Memory Only pipeline (100% URL coverage)")
    print("  - PDF generation (all jobs have URLs)")
    print("  - Link tracking (all URLs validated)")
    print("  - Supabase upload (fully compliant dataset)")

def main():
    """Main function to create compliant dataset"""
    input_file = '/Users/freeworld_james/Desktop/freeworld-job-scraper/streamlit-app/jobs_final.csv'
    output_file = '/Users/freeworld_james/Desktop/freeworld-job-scraper/streamlit-app/jobs_compliant.csv'
    
    print("🎯 Creating Fully Compliant Dataset")
    print(f"📥 Reading: {input_file}")
    
    try:
        # Load data
        df = pd.read_csv(input_file)
        print(f"✅ Loaded {len(df):,} jobs")
        
        # Show current compliance status
        has_url = (df['apply_url'].notna() & (df['apply_url'] != '')).sum()
        print(f"📊 Current URL coverage: {has_url}/{len(df)} ({100*has_url/len(df):.1f}%)")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return False
    
    # Remove non-compliant jobs
    compliant_df = remove_non_compliant_jobs(df)
    
    # Validate compliance
    if not validate_compliance(compliant_df):
        print("❌ Compliance validation failed")
        return False
    
    # Generate report
    generate_compliance_report(compliant_df)
    
    # Save compliant dataset
    print(f"\n💾 Saving compliant dataset to: {output_file}")
    compliant_df.to_csv(output_file, index=False)
    print("✅ Compliant dataset saved!")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 SUCCESS: Fully compliant dataset created!")
        print("📄 All jobs now have URLs and can generate PDFs")
        print("🔗 Ready for Memory Only pipeline testing")
    else:
        print("\n❌ Failed to create compliant dataset")