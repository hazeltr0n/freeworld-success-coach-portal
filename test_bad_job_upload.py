#!/usr/bin/env python3
"""Test if bad jobs can be uploaded to Supabase"""

import pandas as pd
from dotenv import load_dotenv
from job_memory_db import JobMemoryDB
from jobs_schema import build_empty_df
from jobs_schema import prepare_for_supabase
import uuid

load_dotenv()

# Create a test bad job
test_job = {
    'id.job': f'test_bad_{uuid.uuid4().hex[:8]}',
    'source.title': 'Test Bad Job - Experience Required',
    'source.company': 'Test Company',
    'source.location_raw': 'Houston, TX',
    'norm.title': 'Test Bad Job - Experience Required',
    'norm.company': 'Test Company',
    'norm.location': 'Houston, TX',
    'ai.match': 'bad',
    'ai.reason': 'TEST: Requires 5 years experience',
    'ai.route_type': 'Local',
    'sys.is_fresh_job': True,
    'sys.classification_source': 'ai_classification',
    'route.final_status': 'filtered: AI bad match (experience required)',
    'meta.market': 'Houston'
}

# Create DataFrame
df = build_empty_df()
test_df = pd.DataFrame([test_job])

# Fill missing columns
for col in df.columns:
    if col not in test_df.columns:
        test_df[col] = ''

# Prepare for Supabase
print("🔍 Preparing test bad job for Supabase...")
supabase_df = prepare_for_supabase(test_df)
print(f"✅ Prepared {len(supabase_df)} jobs")
print(f"   Match level: {supabase_df['match_level'].iloc[0]}")
print(f"   Final status: {supabase_df.get('final_status', pd.Series(['N/A'])).iloc[0]}")

# Try to upload
print("\n💾 Attempting to upload bad job to Supabase...")
memory_db = JobMemoryDB()
success = memory_db.store_classifications(supabase_df)

if success:
    print(f"✅ SUCCESS! Bad job uploaded to Supabase")
    print(f"   Job ID: {test_job['id.job']}")
else:
    print(f"❌ FAILED to upload bad job")
