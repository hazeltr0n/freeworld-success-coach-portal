#!/usr/bin/env python3
"""
Delete all jobs uploaded to Supabase today

Usage:
    python3 delete_todays_jobs.py --confirm
"""

import argparse
import sys
from datetime import datetime, date

# Load environment variables
try:
    from tools.secrets_loader import load_local_secrets_to_env
    load_local_secrets_to_env()
except Exception:
    pass

# Also try loading from streamlit secrets if available
try:
    import streamlit as st
    import os
    if hasattr(st, 'secrets'):
        for key, value in st.secrets.items():
            if isinstance(value, str):
                os.environ[key] = value
except Exception:
    pass

def get_supabase_client():
    """Initialize Supabase client using supabase_utils"""
    try:
        from supabase_utils import get_client
        client = get_client()
        if client is None:
            print("❌ Supabase client is None - check SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        return None

def delete_todays_jobs(supabase, confirm=False):
    """Delete all jobs created today"""
    try:
        # Get today's date
        today = date.today()
        today_str = today.isoformat()
        
        print(f"🗑️  Preparing to delete jobs from {today_str}")
        
        # First, check how many jobs would be deleted
        result = supabase.table('jobs').select('job_id').gte('created_at', today_str).execute()
        job_count = len(result.data) if result.data else 0
        
        if job_count == 0:
            print("✅ No jobs found for today - nothing to delete")
            return True
        
        print(f"📊 Found {job_count} jobs created today ({today_str})")
        
        if not confirm:
            print("⚠️  This is DESTRUCTIVE and will permanently DELETE jobs!")
            print("⚠️  Use --confirm to actually perform the deletion")
            return False
        
        # Delete jobs in batches
        batch_size = 100
        total_deleted = 0
        
        while True:
            # Get a batch of job IDs
            result = supabase.table('jobs').select('job_id').gte('created_at', today_str).limit(batch_size).execute()
            
            if not result.data or len(result.data) == 0:
                break
                
            job_ids = [job['job_id'] for job in result.data]
            
            # Delete the batch
            delete_result = supabase.table('jobs').delete().in_('job_id', job_ids).execute()
            
            if delete_result.data:
                batch_deleted = len(delete_result.data)
                total_deleted += batch_deleted
                print(f"🗑️  Deleted batch: {batch_deleted} jobs")
            else:
                print(f"⚠️  No data returned for batch deletion")
                break
        
        print(f"✅ Successfully deleted {total_deleted} jobs from {today_str}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to delete jobs: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Delete all jobs uploaded to Supabase today")
    parser.add_argument("--confirm", action="store_true", help="Actually perform the deletion (DESTRUCTIVE)")
    
    args = parser.parse_args()
    
    # Initialize Supabase
    supabase = get_supabase_client()
    if not supabase:
        return 1
    
    print("🗑️  DELETE TODAY'S JOBS FROM SUPABASE")
    print("=" * 45)
    
    try:
        success = delete_todays_jobs(supabase, confirm=args.confirm)
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())