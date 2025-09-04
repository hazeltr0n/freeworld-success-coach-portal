#!/usr/bin/env python3
"""
Test deduplication logic with actual CSV data to debug over-filtering
"""

import pandas as pd
import hashlib
from typing import Dict

def generate_dedup_keys_test(row: pd.Series, market: str) -> Dict[str, str]:
    """Generate deduplication keys - same logic as pipeline"""
    # Map CSV fields to what we expect
    company = str(row.get('company', '')).lower().strip()
    title = str(row.get('job_title', '')).lower().strip()
    location = str(row.get('location', '')).lower().strip()
    
    # Round 1: Company + Title + Market (market is vital ingredient!)
    r1_key = f"{company}|{title}|{market.lower()}"
    
    # Round 2: Company + Location (city-based deduplication)
    r2_key = f"{company}|{location}"
    
    print(f"  R1 key: '{r1_key}' -> {hashlib.md5(r1_key.encode()).hexdigest()[:16]}")
    print(f"  R2 key: '{r2_key}' -> {hashlib.md5(r2_key.encode()).hexdigest()[:16]}")
    
    return {
        'rules.duplicate_r1': hashlib.md5(r1_key.encode()).hexdigest()[:16],
        'rules.duplicate_r2': hashlib.md5(r2_key.encode()).hexdigest()[:16]
    }

def test_pipeline_mapping(df):
    """Test the exact field mapping that pipeline uses"""
    print("\n🔧 Testing PIPELINE field mapping (supabase -> canonical):")
    
    # Simulate supabase_converter mapping
    canonical_df = pd.DataFrame(index=range(len(df.head(10))))
    
    # Exact mapping from supabase_converter.py  
    canonical_df['norm.title'] = df.head(10).get('job_title', '')
    canonical_df['norm.company'] = df.head(10).get('company', '')
    canonical_df['norm.location'] = df.head(10).get('location', '')
    canonical_df['meta.market'] = df.head(10).get('market', '')
    
    print(f"📊 After pipeline mapping:")
    for i in range(min(5, len(canonical_df))):
        print(f"  Job #{i+1}:")
        print(f"    norm.company: '{canonical_df.iloc[i]['norm.company']}'")
        print(f"    norm.title: '{canonical_df.iloc[i]['norm.title']}'")  
        print(f"    meta.market: '{canonical_df.iloc[i]['meta.market']}'")
        
        # Test deduplication key generation like pipeline does
        market = canonical_df.iloc[i]['meta.market']
        company = str(canonical_df.iloc[i]['norm.company']).lower().strip()
        title = str(canonical_df.iloc[i]['norm.title']).lower().strip()
        r1_key = f"{company}|{title}|{str(market).lower()}"
        print(f"    R1 key: '{r1_key}'")

def test_deduplication():
    """Test deduplication with actual CSV data"""
    
    print("🧪 Testing deduplication logic with CSV data")
    
    # Load the CSV
    try:
        df = pd.read_csv('/workspaces/freeworld-success-coach-portal/jobs_rows (5).csv')
        print(f"📁 Loaded {len(df)} jobs from CSV")
        print(f"🔍 Columns: {list(df.columns)}")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return
    
    # Test pipeline mapping first
    test_pipeline_mapping(df)
    
    # Take first 50 jobs to test and look for patterns
    test_df = df.head(50).copy()
    
    # Check for empty/problematic fields
    empty_company = test_df[test_df['company'].isna() | (test_df['company'] == '')].shape[0]
    empty_title = test_df[test_df['job_title'].isna() | (test_df['job_title'] == '')].shape[0] 
    empty_market = test_df[test_df['market'].isna() | (test_df['market'] == '')].shape[0]
    
    print(f"🔍 Field completeness in first 50 jobs:")
    print(f"  Empty company: {empty_company}")
    print(f"  Empty job_title: {empty_title}")
    print(f"  Empty market: {empty_market}")
    
    # Test what happens with empty fields
    print(f"\n🧪 Testing empty field scenario:")
    empty_test = pd.Series({'company': '', 'job_title': '', 'market': 'Houston'})
    keys_empty = generate_dedup_keys_test(empty_test, 'Houston')
    print(f"  Empty company+title would create R1 key: '||houston'")
    
    another_empty = pd.Series({'company': '', 'job_title': '', 'market': 'Houston'}) 
    keys_empty2 = generate_dedup_keys_test(another_empty, 'Houston')
    print(f"  Another empty would get SAME hash: {keys_empty['rules.duplicate_r1'] == keys_empty2['rules.duplicate_r1']}")
    
    print(f"\n📊 Testing with first {len(test_df)} jobs:")
    for i, (idx, row) in enumerate(test_df.iterrows()):
        print(f"\n🔍 Job #{i+1}:")
        print(f"  Company: '{row.get('company', 'MISSING')}'")
        print(f"  Title: '{row.get('job_title', 'MISSING')}'") 
        print(f"  Location: '{row.get('location', 'MISSING')}'")
        print(f"  Market: '{row.get('market', 'MISSING')}'")
        
        # Generate dedup keys
        market = row.get('market', 'Unknown')
        keys = generate_dedup_keys_test(row, market)
    
    # Test grouping by R1 keys
    print(f"\n🔄 Testing R1 grouping (company+title+market):")
    
    # Generate all R1 keys
    test_df['r1_key'] = test_df.apply(lambda row: f"{str(row.get('company', '')).lower().strip()}|{str(row.get('job_title', '')).lower().strip()}|{str(row.get('market', '')).lower().strip()}", axis=1)
    test_df['r1_hash'] = test_df['r1_key'].apply(lambda x: hashlib.md5(x.encode()).hexdigest()[:16])
    
    # Check for duplicates
    r1_counts = test_df['r1_hash'].value_counts()
    print(f"📊 R1 key distribution:")
    for hash_val, count in r1_counts.items():
        if count > 1:
            print(f"  Hash {hash_val}: {count} jobs (DUPLICATE!)")
            duplicate_rows = test_df[test_df['r1_hash'] == hash_val]
            for idx, row in duplicate_rows.iterrows():
                print(f"    - {row.get('company', 'N/A')} | {row.get('job_title', 'N/A')} | {row.get('market', 'N/A')}")
        else:
            print(f"  Hash {hash_val}: {count} job (unique)")
    
    # Test R2 grouping
    print(f"\n🔄 Testing R2 grouping (company+location):")
    test_df['r2_key'] = test_df.apply(lambda row: f"{str(row.get('company', '')).lower().strip()}|{str(row.get('location', '')).lower().strip()}", axis=1)
    test_df['r2_hash'] = test_df['r2_key'].apply(lambda x: hashlib.md5(x.encode()).hexdigest()[:16])
    
    r2_counts = test_df['r2_hash'].value_counts()
    print(f"📊 R2 key distribution:")
    for hash_val, count in r2_counts.items():
        if count > 1:
            print(f"  Hash {hash_val}: {count} jobs (DUPLICATE!)")
        else:
            print(f"  Hash {hash_val}: {count} job (unique)")

if __name__ == "__main__":
    test_deduplication()