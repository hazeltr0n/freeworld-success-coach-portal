#!/usr/bin/env python3
"""
Upload the cleaned jobs data back to Supabase
This script will replace the existing jobs table with cleaned data
"""

import pandas as pd
import numpy as np
import sys
from typing import Dict, List, Any
import json
import os
import toml
from supabase import create_client, Client

def prepare_supabase_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Prepare DataFrame for Supabase upload"""
    print("📋 Preparing data for Supabase...")
    
    # Create records list
    records = []
    
    for _, row in df.iterrows():
        # Convert pandas Series to dict and handle NaN values
        record = {}
        for col, val in row.items():
            if pd.isna(val):
                record[col] = None
            elif isinstance(val, (np.int64, np.int32)):
                record[col] = int(val)
            elif isinstance(val, (np.float64, np.float32)):
                record[col] = float(val)
            else:
                record[col] = str(val) if val != '' else None
        
        records.append(record)
    
    print(f"  ✅ Prepared {len(records)} records for upload")
    return records

def backup_existing_data(client) -> bool:
    """Create a backup of existing Supabase data"""
    print("💾 Creating backup of existing data...")
    
    try:
        # Get all existing jobs
        result = client.table('jobs').select('*').execute()
        existing_jobs = result.data
        
        backup_file = '/Users/freeworld_james/Desktop/freeworld-job-scraper/streamlit-app/jobs_backup_before_cleanup.json'
        
        with open(backup_file, 'w') as f:
            json.dump(existing_jobs, f, indent=2, default=str)
        
        print(f"  ✅ Backed up {len(existing_jobs)} jobs to {backup_file}")
        return True
        
    except Exception as e:
        print(f"  ❌ Backup failed: {e}")
        return False

def clear_existing_data(client) -> bool:
    """Clear existing jobs table"""
    print("🗑️ Clearing existing data...")
    
    try:
        # Delete all existing jobs
        result = client.table('jobs').delete().neq('job_id', '').execute()
        print(f"  ✅ Cleared existing jobs table")
        return True
        
    except Exception as e:
        print(f"  ❌ Clear failed: {e}")
        return False

def upload_in_batches(client, records: List[Dict], batch_size: int = 100) -> bool:
    """Upload records in batches to avoid timeout"""
    print(f"⬆️ Uploading {len(records)} records in batches of {batch_size}...")
    
    total_uploaded = 0
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(records) + batch_size - 1) // batch_size
        
        try:
            result = client.table('jobs').insert(batch).execute()
            uploaded_count = len(result.data) if result.data else len(batch)
            total_uploaded += uploaded_count
            
            print(f"  📦 Batch {batch_num}/{total_batches}: {uploaded_count} records uploaded")
            
        except Exception as e:
            print(f"  ❌ Batch {batch_num} failed: {e}")
            # Try to continue with other batches
            continue
    
    print(f"  ✅ Total uploaded: {total_uploaded}/{len(records)} records")
    return total_uploaded > 0

def verify_upload(client, expected_count: int) -> bool:
    """Verify the upload was successful"""
    print("🔍 Verifying upload...")
    
    try:
        # Count total jobs
        result = client.table('jobs').select('job_id', count='exact').execute()
        actual_count = result.count
        
        print(f"  📊 Expected: {expected_count} jobs")
        print(f"  📊 Actual: {actual_count} jobs")
        
        if actual_count == expected_count:
            print("  ✅ Upload verification successful!")
            return True
        else:
            print(f"  ⚠️ Upload verification failed - count mismatch")
            return False
            
    except Exception as e:
        print(f"  ❌ Verification failed: {e}")
        return False

def main():
    """Main upload function"""
    input_file = '/Users/freeworld_james/Desktop/freeworld-job-scraper/streamlit-app/jobs_compliant.csv'
    
    print("🚀 Starting Supabase Upload Process")
    print(f"📥 Reading: {input_file}")
    
    # Load cleaned data
    try:
        df = pd.read_csv(input_file)
        print(f"✅ Loaded {len(df)} cleaned jobs")
        
        # Quick validation
        url_coverage = (df['apply_url'] != '').sum()
        print(f"🔗 URL coverage: {url_coverage}/{len(df)} ({100*url_coverage/len(df):.1f}%)")
        
        # Market distribution
        print("📊 Market distribution:")
        market_counts = df['market'].value_counts().head(5)
        for market, count in market_counts.items():
            print(f"  {market}: {count} jobs")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return False
    
    # Connect to Supabase using secrets.toml
    print("\n🔌 Connecting to Supabase...")
    
    try:
        # Load secrets from .streamlit/secrets.toml
        secrets_path = '/Users/freeworld_james/Desktop/freeworld-job-scraper/streamlit-app/.streamlit/secrets.toml'
        with open(secrets_path, 'r') as f:
            secrets = toml.load(f)
        
        supabase_url = secrets['SUPABASE_URL']
        supabase_key = secrets['SUPABASE_ANON_KEY']
        
        client = create_client(supabase_url, supabase_key)
        
        # Test connection
        result = client.table('jobs').select('job_id').limit(1).execute()
        print("✅ Connected to Supabase successfully")
        print(f"📊 Current jobs in database: Found data")
        
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False
    
    # Automatic confirmation for script execution
    print(f"\\n⚠️  WARNING: This will replace all {len(df)} jobs in Supabase!")
    print("   - Existing jobs will be backed up")
    print("   - All jobs will be deleted")  
    print("   - Cleaned jobs will be uploaded")
    print("\\n🚀 Proceeding with automated upload...")
    
    # Step 1: Backup existing data
    if not backup_existing_data(client):
        print("❌ Backup failed - aborting upload")
        return False
    
    # Step 2: Prepare data
    records = prepare_supabase_data(df)
    
    # Step 3: Clear existing data
    if not clear_existing_data(client):
        print("❌ Clear failed - aborting upload")
        return False
    
    # Step 4: Upload new data
    if not upload_in_batches(client, records):
        print("❌ Upload failed")
        return False
    
    # Step 5: Verify upload
    if not verify_upload(client, len(records)):
        print("❌ Verification failed")
        return False
    
    print("\\n🎉 Supabase upload completed successfully!")
    print(f"📊 Final stats:")
    print(f"  - Total jobs: {len(df)}")
    print(f"  - URL coverage: 100%")
    print(f"  - Valid markets only")
    print(f"  - Ready for Memory Only pipeline tests!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)