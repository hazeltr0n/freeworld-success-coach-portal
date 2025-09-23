#!/usr/bin/env python3
"""
Run Supabase Deduplication Functions

Simple script to execute the Supabase deduplication functions from command line.

Usage:
    python3 run_supabase_dedup.py --analyze
    python3 run_supabase_dedup.py --cleanup-all
    python3 run_supabase_dedup.py --cleanup-market Dallas
"""

import argparse
import sys

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

def analyze_duplicates(supabase):
    """Run the analyze_duplicate_jobs function"""
    try:
        print("🔍 Analyzing duplicate jobs...")
        result = supabase.rpc('analyze_duplicate_jobs').execute()
        
        if result.data:
            print(f"📊 Found {len(result.data)} groups with duplicates:")
            print()
            
            total_to_remove = 0
            for row in result.data:
                print(f"Market: {row['market']}")
                print(f"Company: {row['company']}")
                print(f"Total jobs: {row['duplicate_count']}")
                print(f"Jobs to remove: {row['jobs_to_remove']}")
                print(f"Newest job: {row['newest_job_title'][:60]}...")
                print(f"Date range: {row['oldest_classified_at']} → {row['newest_classified_at']}")
                print("-" * 60)
                total_to_remove += row['jobs_to_remove']
            
            print(f"📊 SUMMARY: {total_to_remove} total jobs would be removed")
        else:
            print("✅ No duplicate jobs found!")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

def cleanup_all_duplicates(supabase):
    """Run the cleanup_duplicate_jobs function"""
    try:
        print("🧹 Cleaning up ALL duplicate jobs...")
        print("⚠️  This is DESTRUCTIVE and will DELETE jobs!")
        
        confirm = input("Type 'YES' to confirm cleanup: ")
        if confirm != 'YES':
            print("❌ Cleanup cancelled")
            return False
        
        result = supabase.rpc('cleanup_duplicate_jobs').execute()
        
        if result.data and len(result.data) > 0:
            stats = result.data[0]
            print(f"✅ Cleanup completed:")
            print(f"   Jobs before: {stats['total_jobs_before']}")
            print(f"   Groups with duplicates: {stats['duplicate_groups']}")
            print(f"   Jobs removed: {stats['jobs_removed']}")
            print(f"   Jobs after: {stats['total_jobs_after']}")
        else:
            print("⚠️ Unexpected result from cleanup function")
        
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

def cleanup_market_duplicates(supabase, market):
    """Run the cleanup_market_duplicates function"""
    try:
        print(f"🧹 Cleaning up duplicate jobs for market: {market}")
        print("⚠️  This is DESTRUCTIVE and will DELETE jobs!")
        
        confirm = input(f"Type 'YES' to confirm cleanup for {market}: ")
        if confirm != 'YES':
            print("❌ Cleanup cancelled")
            return False
        
        result = supabase.rpc('cleanup_market_duplicates', {'target_market': market}).execute()
        
        if result.data and len(result.data) > 0:
            stats = result.data[0]
            print(f"✅ Market cleanup completed:")
            print(f"   Market: {market}")
            print(f"   Jobs removed: {stats['jobs_removed']}")
            print(f"   Groups cleaned: {stats['groups_cleaned']}")
        else:
            print("⚠️ Unexpected result from market cleanup function")
        
        return True
        
    except Exception as e:
        print(f"❌ Market cleanup failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run Supabase deduplication functions")
    parser.add_argument("--analyze", action="store_true", help="Analyze duplicate jobs (safe)")
    parser.add_argument("--cleanup-all", action="store_true", help="Clean up ALL duplicate jobs (DESTRUCTIVE)")
    parser.add_argument("--cleanup-market", help="Clean up duplicates for specific market (DESTRUCTIVE)")
    
    args = parser.parse_args()
    
    # Validate arguments
    actions = [args.analyze, args.cleanup_all, bool(args.cleanup_market)]
    if sum(actions) != 1:
        print("❌ Must specify exactly one action: --analyze, --cleanup-all, or --cleanup-market")
        return 1
    
    # Initialize Supabase
    supabase = get_supabase_client()
    if not supabase:
        return 1
    
    print("🗄️  SUPABASE JOB DEDUPLICATION")
    print("=" * 40)
    
    try:
        if args.analyze:
            success = analyze_duplicates(supabase)
        elif args.cleanup_all:
            success = cleanup_all_duplicates(supabase)
        elif args.cleanup_market:
            success = cleanup_market_duplicates(supabase, args.cleanup_market)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())