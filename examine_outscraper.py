#!/usr/bin/env python3

import pandas as pd
import json

# Read the Excel file
file_path = "/Users/freeworld_james/Downloads/Outscraper-20250915150013s8f_fullscrapegoogle (1).xlsx"

try:
    df = pd.read_excel(file_path)
    print(f"✅ Loaded Excel file: {len(df)} rows")
    print(f"📋 Columns: {list(df.columns)}")

    # Show first few rows
    print(f"\n🔍 First 3 rows:")
    for i in range(min(3, len(df))):
        print(f"\nRow {i+1}:")
        for col in df.columns:
            value = df.iloc[i][col]
            if pd.isna(value):
                print(f"  {col}: <EMPTY>")
            elif isinstance(value, str) and len(value) > 100:
                print(f"  {col}: {value[:100]}...")
            else:
                print(f"  {col}: {value}")

    # Look specifically for apply URLs
    print(f"\n🔗 Looking for URL-related columns:")
    url_columns = [col for col in df.columns if 'url' in col.lower() or 'link' in col.lower() or 'apply' in col.lower()]
    print(f"URL columns found: {url_columns}")

    if url_columns:
        for col in url_columns:
            sample_values = df[col].dropna().head(3).tolist()
            print(f"\n{col} samples:")
            for i, val in enumerate(sample_values):
                if isinstance(val, str) and len(val) > 100:
                    print(f"  {i+1}: {val[:100]}...")
                else:
                    print(f"  {i+1}: {val}")

    # Check if there's an apply_urls column with JSON data
    if 'apply_urls' in df.columns:
        print(f"\n🎯 Found apply_urls column!")
        apply_sample = df['apply_urls'].dropna().head(3)
        for i, val in enumerate(apply_sample):
            print(f"\nApply URLs sample {i+1}:")
            print(f"  Raw: {val}")
            try:
                if isinstance(val, str):
                    parsed = json.loads(val)
                    print(f"  Parsed JSON: {parsed}")
                else:
                    print(f"  Type: {type(val)}")
            except:
                print(f"  Not valid JSON")

except Exception as e:
    print(f"❌ Error reading file: {e}")
    import traceback
    traceback.print_exc()