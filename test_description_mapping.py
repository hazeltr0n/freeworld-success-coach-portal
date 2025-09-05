#!/usr/bin/env python3
"""
Test script to isolate description mapping issue in CSV classifier
"""

import pandas as pd
import sys
from pathlib import Path

# Add current directory to path
sys.path.append('.')

def test_description_mapping():
    """Test the description field mapping from CSV through normalization"""
    
    print("🔍 TESTING DESCRIPTION MAPPING")
    print("=" * 50)
    
    # Load CSV sample
    csv_path = Path("Outscraper-20250905004557xs8b_dallas_-_indeed.csv")
    if not csv_path.exists():
        print(f"❌ CSV not found: {csv_path}")
        return
    
    # Load just first few rows
    df_csv = pd.read_csv(csv_path).head(3)
    print(f"✅ Loaded {len(df_csv)} rows from CSV")
    
    # Test the field mapping logic from classify_csv.py
    cols_map = {c.lower(): c for c in df_csv.columns}
    print(f"🔍 Available columns: {list(df_csv.columns)}")
    
    # Test description extraction
    for i, (_, row) in enumerate(df_csv.iterrows()):
        print(f"\n🔍 ROW {i+1} DESCRIPTION TEST:")
        
        # Test the _first function logic from classify_csv.py
        description_fields = ["snippet", "description", "job_description", "jobDescription", "details"]
        description = ""
        
        for field_name in description_fields:
            if field_name.lower() in cols_map:
                actual_col = cols_map[field_name.lower()]
                actual_value = row.get(actual_col, '')
                if pd.notna(actual_value) and str(actual_value).strip():
                    description = str(actual_value).strip()
                    print(f"   ✅ Found description in field '{field_name}' → column '{actual_col}'")
                    print(f"   📄 Length: {len(description)}")
                    print(f"   🔍 Preview: '{description[:100]}...'")
                    break
        
        if not description:
            print(f"   ❌ No description found in fields: {description_fields}")
    
    # Test canonical transform
    print(f"\n🧪 TESTING CANONICAL TRANSFORM")
    print("=" * 50)
    
    from canonical_transforms import transform_ingest_outscraper
    from jobs_schema import ensure_schema
    
    # Create raw rows like classify_csv.py does
    raw_rows = []
    for _, row in df_csv.iterrows():
        raw_row = {
            "title": row.get('title', ''),
            "company": row.get('company', ''),
            "formattedLocation": row.get('formattedLocation', ''),
            "viewJobLink": row.get('viewJobLink', ''),
            "snippet": row.get('snippet', ''),  # This should map to source.description_raw
        }
        raw_rows.append(raw_row)
    
    print(f"✅ Created {len(raw_rows)} raw rows")
    
    # Transform to canonical format
    run_id = "test_123"
    df_canonical = transform_ingest_outscraper(raw_rows, run_id)
    
    print(f"✅ Canonical transform complete: {len(df_canonical)} rows")
    
    # Check source.description_raw field
    if 'source.description_raw' in df_canonical.columns:
        for i in range(min(2, len(df_canonical))):
            desc_raw = df_canonical.iloc[i]['source.description_raw']
            print(f"\n🔍 CANONICAL ROW {i+1}:")
            print(f"   source.description_raw: (len={len(str(desc_raw))})")
            print(f"   Preview: '{str(desc_raw)[:100]}...'")
    else:
        print("❌ source.description_raw column missing!")
        print(f"Available columns: {list(df_canonical.columns)}")
    
    # Test normalization stage
    print(f"\n🧹 TESTING NORMALIZATION STAGE")
    print("=" * 50)
    
    from canonical_transforms import transform_normalize
    
    df_normalized = transform_normalize(df_canonical)
    
    # Check norm.description field
    if 'norm.description' in df_normalized.columns:
        for i in range(min(2, len(df_normalized))):
            desc_norm = df_normalized.iloc[i]['norm.description']
            print(f"\n🔍 NORMALIZED ROW {i+1}:")
            print(f"   norm.description: (len={len(str(desc_norm))})")
            print(f"   Preview: '{str(desc_norm)[:100]}...'")
    else:
        print("❌ norm.description column missing!")
        print(f"Available norm columns: {[col for col in df_normalized.columns if col.startswith('norm.')]}")
    
    print(f"\n✅ Description mapping test complete")

if __name__ == "__main__":
    test_description_mapping()