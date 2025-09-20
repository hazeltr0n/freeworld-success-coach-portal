#!/usr/bin/env python3
"""
Supabase Job Deduplication Cleanup Script

After every upload, creates a key of (market, company) for all jobs and keeps 
only the newest job from each group, removing older duplicates.

Usage:
    python3 supabase_dedup_cleanup.py --market Dallas
    python3 supabase_dedup_cleanup.py --all-markets
    python3 supabase_dedup_cleanup.py --dry-run --market Houston
"""

import os
import argparse
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd

# Load environment variables
try:
    from tools.secrets_loader import load_local_secrets_to_env
    load_local_secrets_to_env()
except Exception:
    pass

def get_supabase_client():
    """Initialize Supabase client"""
    try:
        from supabase_utils import get_client
        return get_client()
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        return None

def analyze_duplicates(supabase, market: str = None, days_back: int = 30) -> pd.DataFrame:
    """
    Analyze duplicate jobs by (market, company) combination
    
    Args:
        supabase: Supabase client
        market: Specific market to analyze (None for all markets)
        days_back: Days to look back for analysis
        
    Returns:
        DataFrame with duplicate analysis
    """
    print(f"🔍 Analyzing duplicates for market: {'ALL' if not market else market}")
    
    # Calculate cutoff date
    cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
    
    # Build query
    query = supabase.table('jobs').select(
        'id, job_id, market, company, job_title, classified_at, created_at, match_level'
    ).gte('classified_at', cutoff_date)
    
    if market:
        query = query.eq('market', market)
    
    # Execute query
    result = query.execute()
    
    if not result.data:
        print("ℹ️  No jobs found in specified criteria")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(result.data)
    print(f"📊 Found {len(df)} total jobs")
    
    # Convert dates to datetime for proper sorting
    df['classified_at'] = pd.to_datetime(df['classified_at'])
    df['created_at'] = pd.to_datetime(df['created_at'])
    
    # Group by (market, company) and analyze duplicates
    df['dedup_key'] = df['market'].str.lower() + '|' + df['company'].str.lower()
    
    # Count jobs per group
    group_counts = df.groupby('dedup_key').size().reset_index(columns=['job_count'])
    duplicates = group_counts[group_counts['job_count'] > 1]
    
    print(f"📈 Duplicate analysis:")
    print(f"   Total unique (market, company) combinations: {len(group_counts)}")
    print(f"   Groups with duplicates: {len(duplicates)}")
    print(f"   Total duplicate jobs to remove: {duplicates['job_count'].sum() - len(duplicates)}")
    
    return df

def identify_jobs_to_remove(df: pd.DataFrame) -> List[str]:
    """
    Identify job IDs to remove (keep newest from each market+company group)
    
    Args:
        df: DataFrame with job data
        
    Returns:
        List of job IDs (database IDs) to remove
    """
    if df.empty:
        return []
    
    jobs_to_remove = []
    
    # Group by (market, company) combination
    for dedup_key, group in df.groupby('dedup_key'):
        if len(group) > 1:
            market, company = dedup_key.split('|')
            print(f"\n🔍 Processing duplicates: {market} | {company}")
            print(f"   Found {len(group)} jobs")
            
            # Sort by classified_at (newest first), then by created_at as tiebreaker
            group_sorted = group.sort_values(['classified_at', 'created_at'], ascending=[False, False])
            
            # Keep the newest job (first after sorting)
            newest_job = group_sorted.iloc[0]
            older_jobs = group_sorted.iloc[1:]
            
            print(f"   ✅ Keeping newest: {newest_job['job_title'][:50]}... (classified: {newest_job['classified_at']})")
            
            # Mark older jobs for removal
            for _, old_job in older_jobs.iterrows():
                jobs_to_remove.append(old_job['id'])  # Use database ID, not job_id
                print(f"   🗑️  Removing older: {old_job['job_title'][:50]}... (classified: {old_job['classified_at']})")
    
    return jobs_to_remove

def remove_duplicate_jobs(supabase, job_ids_to_remove: List[str], dry_run: bool = True) -> bool:
    """
    Remove duplicate jobs from Supabase
    
    Args:
        supabase: Supabase client
        job_ids_to_remove: List of database IDs to remove
        dry_run: If True, don't actually delete
        
    Returns:
        Success status
    """
    if not job_ids_to_remove:
        print("ℹ️  No jobs to remove")
        return True
    
    print(f"\n{'🧪 DRY RUN: Would remove' if dry_run else '🗑️  Removing'} {len(job_ids_to_remove)} duplicate jobs")
    
    if dry_run:
        print("   (Use --execute to actually perform deletions)")
        return True
    
    try:
        # Delete in batches to avoid request limits
        batch_size = 100
        deleted_count = 0
        
        for i in range(0, len(job_ids_to_remove), batch_size):
            batch = job_ids_to_remove[i:i + batch_size]
            
            # Delete batch
            result = supabase.table('jobs').delete().in_('job_id', batch).execute()
            
            if result.data:
                batch_count = len(result.data)
                deleted_count += batch_count
                print(f"   ✅ Deleted {batch_count} jobs (batch {i//batch_size + 1})")
            else:
                print(f"   ⚠️  No results returned for batch {i//batch_size + 1}")
        
        print(f"✅ Successfully removed {deleted_count} duplicate jobs from Supabase")
        return True
        
    except Exception as e:
        print(f"❌ Error removing duplicate jobs: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Supabase job deduplication cleanup")
    parser.add_argument("--market", help="Specific market to clean (e.g., Dallas)")
    parser.add_argument("--all-markets", action="store_true", help="Clean all markets")
    parser.add_argument("--days-back", type=int, default=30, help="Days to look back for analysis (default: 30)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed without deleting")
    parser.add_argument("--execute", action="store_true", help="Actually perform the deletions")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.market and not args.all_markets:
        print("❌ Must specify either --market <name> or --all-markets")
        return 1
    
    if args.market and args.all_markets:
        print("❌ Cannot specify both --market and --all-markets")
        return 1
    
    # Initialize Supabase
    supabase = get_supabase_client()
    if not supabase:
        return 1
    
    print("🧹 SUPABASE JOB DEDUPLICATION CLEANUP")
    print("=" * 50)
    print(f"Market: {'ALL' if args.all_markets else args.market}")
    print(f"Days back: {args.days_back}")
    print(f"Mode: {'DRY RUN' if args.dry_run or not args.execute else 'EXECUTE'}")
    
    try:
        # Analyze duplicates
        df = analyze_duplicates(supabase, 
                              market=None if args.all_markets else args.market,
                              days_back=args.days_back)
        
        if df.empty:
            print("✅ No jobs found to analyze")
            return 0
        
        # Identify jobs to remove
        jobs_to_remove = identify_jobs_to_remove(df)
        
        if not jobs_to_remove:
            print("✅ No duplicate jobs found - database is clean!")
            return 0
        
        # Remove duplicates (dry run by default unless --execute is specified)
        dry_run = args.dry_run or not args.execute
        success = remove_duplicate_jobs(supabase, jobs_to_remove, dry_run=dry_run)
        
        if success:
            if dry_run:
                print(f"\n🧪 Dry run complete - {len(jobs_to_remove)} jobs would be removed")
                print("   Use --execute to perform actual deletions")
            else:
                print(f"\n✅ Cleanup complete - {len(jobs_to_remove)} duplicate jobs removed")
            return 0
        else:
            print("\n❌ Cleanup failed")
            return 1
            
    except Exception as e:
        print(f"❌ Script failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())