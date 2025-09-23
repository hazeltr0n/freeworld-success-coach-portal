#!/usr/bin/env python3
"""
Supabase Deduplication Keys Backfill Script

This script downloads existing jobs from Supabase, generates the missing deduplication keys
using the exact same logic as the pipeline, and updates the database with the keys.

This enables instant memory searches immediately without waiting for fresh job runs.
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🚀 Starting Supabase deduplication keys backfill")
    print("=" * 60)
    
    # Try to load Streamlit secrets if running in Streamlit environment
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            os.environ['SUPABASE_URL'] = st.secrets.get('SUPABASE_URL', '')
            os.environ['SUPABASE_ANON_KEY'] = st.secrets.get('SUPABASE_ANON_KEY', '')
            print("✅ Loaded Supabase credentials from Streamlit secrets")
        else:
            print("ℹ️ Not running in Streamlit environment, using environment variables")
    except ImportError:
        print("ℹ️ Streamlit not available, using environment variables")
    except Exception as e:
        print(f"⚠️ Could not load Streamlit secrets: {e}")
    
    # Step 1: Initialize clients
    print("📡 Initializing Supabase client...")
    from supabase_utils import get_client
    supabase_client = get_client()
    
    if not supabase_client:
        print("❌ Failed to initialize Supabase client")
        print("   Check SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
        print("   Or run this script from within the Streamlit app environment")
        return False
    
    print("✅ Supabase client initialized")
    
    # Step 2: Download existing jobs
    days_back = int(input("📅 How many days back to backfill? (default: 7): ") or 7)
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    print(f"📥 Downloading jobs from last {days_back} days (since {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')})")
    
    try:
        # Query recent jobs that don't have deduplication keys yet
        result = supabase_client.table('jobs').select('*').gte(
            'created_at', cutoff_date.isoformat()
        ).is_('rules_duplicate_r1', 'null').execute()
        
        jobs = result.data or []
        print(f"📦 Downloaded {len(jobs)} jobs needing deduplication keys")
        
        if not jobs:
            print("✅ No jobs need backfilling - all jobs already have deduplication keys!")
            return True
            
    except Exception as e:
        print(f"❌ Failed to download jobs: {e}")
        return False
    
    # Step 3: Convert to canonical DataFrame
    print("🔄 Converting to canonical DataFrame format...")
    
    try:
        from supabase_converter import supabase_to_canonical_df
        df = supabase_to_canonical_df(jobs)
        print(f"✅ Converted {len(df)} jobs to canonical format")
        
        if df.empty:
            print("⚠️ No jobs to process")
            return True
            
    except Exception as e:
        print(f"❌ Failed to convert jobs to canonical format: {e}")
        return False
    
    # Step 4: Generate deduplication keys using pipeline logic
    print("🔑 Generating deduplication keys...")
    
    try:
        # Import the pipeline to use its deduplication logic
        from pipeline_v3 import FreeWorldPipelineV3
        
        # Create a minimal pipeline instance just for the deduplication logic
        pipeline = FreeWorldPipelineV3()
        
        # Generate clean URLs (same logic as pipeline)
        print("🔗 Generating clean URLs...")
        df['clean_apply_url'] = df.apply(lambda x: pipeline._extract_clean_url(
            x.get('source.indeed_url', '') or 
            x.get('source.google_url', '') or 
            x.get('source.apply_url', '')
        ), axis=1)
        
        # Ensure we have the required deduplication fields (they should already exist from canonical conversion)
        if 'rules.duplicate_r1' not in df.columns or 'rules.duplicate_r2' not in df.columns:
            print("⚠️ Deduplication keys not found in canonical DataFrame")
            print("   These should have been generated during the original pipeline run")
            print("   Checking what columns we have...")
            dedup_cols = [col for col in df.columns if 'duplicate' in col]
            print(f"   Deduplication columns found: {dedup_cols}")
            
            if not dedup_cols:
                print("❌ No deduplication columns found - cannot proceed")
                print("   The original jobs may need to be reprocessed through the full pipeline")
                return False
        
        # Count how many jobs have keys
        has_r1 = df['rules.duplicate_r1'].notna().sum()
        has_r2 = df['rules.duplicate_r2'].notna().sum()
        has_clean_url = df['clean_apply_url'].notna().sum()
        
        print(f"🔍 Key generation results:")
        print(f"   - R1 keys (company+title+market): {has_r1}/{len(df)}")
        print(f"   - R2 keys (company+location): {has_r2}/{len(df)}")
        print(f"   - Clean URLs: {has_clean_url}/{len(df)}")
        
    except Exception as e:
        print(f"❌ Failed to generate deduplication keys: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Convert back to Supabase format with deduplication keys
    print("📤 Preparing data for Supabase update...")
    
    try:
        from jobs_schema import prepare_for_supabase
        
        # Convert canonical DF back to Supabase format 
        # This will use the SUPABASE_FIELDS mapping we updated
        supabase_df = prepare_for_supabase(df)
        
        print(f"🔍 Supabase DataFrame shape: {supabase_df.shape}")
        print(f"🔍 Deduplication columns in Supabase DF:")
        dedup_cols = [col for col in supabase_df.columns if 'duplicate' in col or 'clean_apply_url' in col or 'job_id_hash' in col]
        for col in dedup_cols:
            non_null = supabase_df[col].notna().sum()
            print(f"   - {col}: {non_null}/{len(supabase_df)} non-null values")
        
        # Convert to records for batch update
        records = supabase_df.to_dict('records')
        
        # Filter out records that don't have job_id (required for updates)
        valid_records = [r for r in records if r.get('job_id')]
        
        print(f"✅ Prepared {len(valid_records)} records for database update")
        
        # Debug: show a sample record
        if valid_records:
            sample = valid_records[0]
            print(f"🔍 Sample record keys: {list(sample.keys())}")
            dedup_keys = {k: v for k, v in sample.items() if 'duplicate' in k or 'clean_apply_url' in k or 'job_id_hash' in k}
            print(f"🔍 Sample deduplication keys: {dedup_keys}")
        
    except Exception as e:
        print(f"❌ Failed to prepare data for Supabase: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 6: Update database using the new deduplication function
    print("💾 Updating database with deduplication keys...")
    
    # Ask for confirmation before making changes
    confirm = input(f"⚠️ About to update {len(valid_records)} jobs in Supabase. Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Operation cancelled by user")
        return False
    
    try:
        # Try using the new batch deduplication function
        print("🔄 Attempting batch update with deduplication...")
        
        # Split into smaller batches to avoid timeouts
        batch_size = 50
        updated_count = 0
        failed_count = 0
        
        for i in range(0, len(valid_records), batch_size):
            batch = valid_records[i:i+batch_size]
            print(f"   Processing batch {i//batch_size + 1}/{(len(valid_records) + batch_size - 1)//batch_size} ({len(batch)} jobs)...")
            
            try:
                # Try the new RPC function first
                result = supabase_client.rpc('batch_insert_jobs_with_dedup', {
                    'p_jobs_data': batch
                }).execute()
                
                if result.data is not None:
                    batch_updated = result.data if isinstance(result.data, int) else len(batch)
                    updated_count += batch_updated
                    print(f"   ✅ Batch completed: {batch_updated} jobs processed")
                else:
                    print(f"   ⚠️ Batch completed but returned null result")
                    updated_count += len(batch)
                    
            except Exception as rpc_error:
                print(f"   ⚠️ RPC function failed: {rpc_error}")
                print(f"   🔄 Falling back to individual upserts...")
                
                # Fallback to individual upserts
                for record in batch:
                    try:
                        supabase_client.table('jobs').upsert(record).execute()
                        updated_count += 1
                    except Exception as upsert_error:
                        print(f"   ❌ Failed to update job {record.get('job_id', 'unknown')}: {upsert_error}")
                        failed_count += 1
        
        print(f"✅ Database update completed!")
        print(f"   - Successfully updated: {updated_count} jobs")
        if failed_count > 0:
            print(f"   - Failed updates: {failed_count} jobs")
        
    except Exception as e:
        print(f"❌ Database update failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 7: Verify the update
    print("🔍 Verifying the update...")
    
    try:
        # Count how many jobs now have deduplication keys
        result = supabase_client.table('jobs').select(
            'job_id', 'rules_duplicate_r1', 'rules_duplicate_r2', 'clean_apply_url', 'job_id_hash'
        ).gte('created_at', cutoff_date.isoformat()).execute()
        
        verification_jobs = result.data or []
        
        with_r1 = sum(1 for job in verification_jobs if job.get('rules_duplicate_r1'))
        with_r2 = sum(1 for job in verification_jobs if job.get('rules_duplicate_r2'))  
        with_clean_url = sum(1 for job in verification_jobs if job.get('clean_apply_url'))
        with_job_hash = sum(1 for job in verification_jobs if job.get('job_id_hash'))
        
        total = len(verification_jobs)
        
        print(f"📊 Verification results:")
        print(f"   - Total jobs in date range: {total}")
        print(f"   - Jobs with R1 keys: {with_r1} ({with_r1/total*100:.1f}%)")
        print(f"   - Jobs with R2 keys: {with_r2} ({with_r2/total*100:.1f}%)")
        print(f"   - Jobs with clean URLs: {with_clean_url} ({with_clean_url/total*100:.1f}%)")
        print(f"   - Jobs with ID hashes: {with_job_hash} ({with_job_hash/total*100:.1f}%)")
        
    except Exception as e:
        print(f"⚠️ Verification failed: {e}")
    
    print("\n🎉 Backfill completed successfully!")
    print("\n📋 Next steps:")
    print("1. Test instant memory search in the app")
    print("2. Verify that duplicate jobs are being removed")
    print("3. Monitor database performance")
    print("4. Consider setting up automatic cleanup of old jobs")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
    print("\n✅ Script completed successfully!")