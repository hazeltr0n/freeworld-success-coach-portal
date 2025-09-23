#!/usr/bin/env python3

import json
import pandas as pd
from canonical_transforms import transform_ingest_google

# Create test data that matches the real Google Outscraper format
test_data = [
    {
        'title': 'Class A CDL Truck Drivers- Hiring New Graduates!',
        'company': 'RecruitCDL',
        'location': 'Trenton, NJ',
        'apply_urls': '[{"apply_url:": "https://www.indeed.com/viewjob?jk=5ebdde572509c9d3", "domain": null, "apply_company": "Indeed"}]',
        'description': 'Job Summary: As a CDL A Recruiting firm we offer full time W-2 opportunities.',
        'salary': '$50,000 - $70,000',
        'posted_date': '2 days ago'
    },
    {
        'title': 'OTR Truck Driver',
        'company': 'Vision Truck Line',
        'location': 'Trenton, NJ',
        'apply_urls': '[{"apply_url:": "https://www.ziprecruiter.com/c/Vision-Truck-Line/Jobs", "domain": null, "apply_company": "ZipRecruiter"}, {"apply_url:": "https://salutemyjob.com/jobs/class-a-cdl-truck-drivers", "domain": "salutemyjob.com", "apply_company": "SaluteMyJob"}]',
        'description': 'Trainee Opening: Yes, straight salary pays for 4 to 6 weeks.',
        'salary': '$1,400 weekly',
        'posted_date': '1 day ago'
    }
]

print(f"🔍 Testing with real Google Outscraper format: {len(test_data)} jobs")

# Test the canonical transform
try:
    result_df = transform_ingest_google(test_data, "test_run_002", "Trenton, NJ")
    print(f"\n✅ Transform successful: {len(result_df)} rows")

    # Check if source.url was populated
    if 'source.url' in result_df.columns:
        url_count = (result_df['source.url'] != '').sum()
        print(f"📊 Jobs with URLs: {url_count}/{len(result_df)}")

        # Show extracted URLs
        for i in range(len(result_df)):
            url = result_df.iloc[i]['source.url']
            title = result_df.iloc[i].get('source.title', 'NO_TITLE')
            print(f"  Job {i+1} ({title[:40]}...): {url[:80] if url else 'NO_URL'}...")
    else:
        print("❌ source.url column not found")

except Exception as e:
    print(f"❌ Transform failed: {e}")
    import traceback
    traceback.print_exc()