#!/usr/bin/env python3
"""
Auto-Deduplication Hook for Pipeline

This script can be called automatically after pipeline uploads to clean up 
duplicates. It's designed to be lightweight and safe for production use.

Usage:
    # Called automatically by pipeline after upload
    python3 auto_dedup_hook.py --market Dallas --auto-clean
    
    # Manual testing
    python3 auto_dedup_hook.py --market Houston --dry-run
"""

import os
import sys
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def auto_cleanup_duplicates(market: str, dry_run: bool = False) -> bool:
    """
    Automatically clean up duplicates for a specific market
    
    Args:
        market: Market name to clean
        dry_run: If True, don't actually delete
        
    Returns:
        Success status
    """
    try:
        from supabase_dedup_cleanup import get_supabase_client, analyze_duplicates, identify_jobs_to_remove, remove_duplicate_jobs
        
        logger.info(f"🧹 Starting auto-cleanup for market: {market}")
        
        # Initialize Supabase
        supabase = get_supabase_client()
        if not supabase:
            logger.error("Failed to initialize Supabase client")
            return False
        
        # Analyze duplicates (only look back 7 days for recent uploads)
        df = analyze_duplicates(supabase, market=market, days_back=7)
        
        if df.empty:
            logger.info("No jobs found to analyze")
            return True
        
        # Identify jobs to remove
        jobs_to_remove = identify_jobs_to_remove(df)
        
        if not jobs_to_remove:
            logger.info("No duplicate jobs found - database is clean!")
            return True
        
        # Remove duplicates
        logger.info(f"Found {len(jobs_to_remove)} duplicate jobs to remove")
        success = remove_duplicate_jobs(supabase, jobs_to_remove, dry_run=dry_run)
        
        if success:
            if dry_run:
                logger.info(f"Dry run complete - {len(jobs_to_remove)} jobs would be removed")
            else:
                logger.info(f"Auto-cleanup complete - {len(jobs_to_remove)} duplicate jobs removed")
        
        return success
        
    except Exception as e:
        logger.error(f"Auto-cleanup failed: {e}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-deduplication hook for pipeline")
    parser.add_argument("--market", required=True, help="Market to clean")
    parser.add_argument("--auto-clean", action="store_true", help="Automatically clean duplicates (production mode)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed without deleting")
    
    args = parser.parse_args()
    
    # Determine mode
    if args.auto_clean and args.dry_run:
        logger.error("Cannot specify both --auto-clean and --dry-run")
        return 1
    
    dry_run = args.dry_run or not args.auto_clean
    
    logger.info(f"Auto-dedup hook starting: market={args.market}, mode={'DRY RUN' if dry_run else 'EXECUTE'}")
    
    success = auto_cleanup_duplicates(args.market, dry_run=dry_run)
    
    if success:
        logger.info("Auto-dedup hook completed successfully")
        return 0
    else:
        logger.error("Auto-dedup hook failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())