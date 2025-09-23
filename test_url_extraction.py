#!/usr/bin/env python3

import json
import pandas as pd
from canonical_transforms import transform_ingest_google

# Load test data
with open('/Users/freeworld_james/Desktop/freeworld-job-scraper/test_data/google_jobs_sample.json', 'r') as f:
    test_data = json.load(f)

# Extract the jobs data from the nested structure
jobs_data = test_data['data'][0]

print(f"🔍 Raw jobs data: {len(jobs_data)} jobs")
for i, job in enumerate(jobs_data[:2]):
    print(f"  Job {i+1}: {job.get('title', 'NO_TITLE')}")
    print(f"    apply_options: {job.get('apply_options', 'NOT_FOUND')}")
    print(f"    apply_urls: {job.get('apply_urls', 'NOT_FOUND')}")

# Test the canonical transform
try:
    result_df = transform_ingest_google(jobs_data, "test_run_001", "Houston, TX")
    print(f"\n✅ Transform successful: {len(result_df)} rows")

    # Check if source.url was populated
    if 'source.url' in result_df.columns:
        url_count = (result_df['source.url'] != '').sum()
        print(f"📊 Jobs with URLs: {url_count}/{len(result_df)}")

        # Show first few URLs
        for i in range(min(3, len(result_df))):
            url = result_df.iloc[i]['source.url']
            title = result_df.iloc[i].get('source.title', 'NO_TITLE')
            print(f"  Job {i+1} ({title[:30]}...): {url[:60] if url else 'NO_URL'}...")
    else:
        print("❌ source.url column not found")

    print(f"\n📋 Available columns: {list(result_df.columns)}")

except Exception as e:
    print(f"❌ Transform failed: {e}")
    import traceback
    traceback.print_exc()