#!/usr/bin/env python3
"""
Check URLs in pipeline CSV files
"""
import pandas as pd

csv_file = "/Users/freeworld_james/Desktop/freeworld-job-scraper/streamlit-app/FreeWorld_Jobs/Houston_quality_jobs_20250902_010814.csv"

print(f"📄 Checking URLs in: {csv_file}")

df = pd.read_csv(csv_file)
print(f"📊 Total jobs: {len(df)}")

# Check first few jobs for URL fields
url_fields = ['source.apply_url', 'source.indeed_url', 'meta.tracked_url', 'clean_apply_url']
print(f"\n🔍 First 3 jobs URL status:")

for i in range(min(3, len(df))):
    job = df.iloc[i]
    print(f"\nJob {i+1}: {job.get('source.title', 'NO TITLE')[:30]}...")
    
    for field in url_fields:
        value = str(job.get(field, ''))
        if value and value != 'nan' and len(value) > 10:
            print(f"   ✅ {field}: {value[:60]}...")
        else:
            print(f"   ❌ {field}: EMPTY or '{value}'")