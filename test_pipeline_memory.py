"""
Test if pipeline actually skips classification for cached jobs

We'll run a small search with jobs we KNOW are in memory,
and see if it skips the OpenAI calls
"""

import sys
import pandas as pd
from pipeline_v3 import Pipeline
from supabase_utils import get_client

print("="*80)
print("TESTING IF PIPELINE SKIPS CACHED JOB CLASSIFICATION")
print("="*80)

# Get 10 job IDs that definitely exist in Supabase
print("\n📂 Fetching job IDs that are DEFINITELY in memory...")
supabase = get_client()
result = supabase.table('jobs').select('job_id,job_title,company,location').limit(10).execute()
existing_jobs = result.data

print(f"   Found {len(existing_jobs)} existing jobs:")
for job in existing_jobs[:3]:
    print(f"   - {job['job_id']}: {job['job_title']} @ {job['company']}")
print(f"   ... and {len(existing_jobs)-3} more\n")

# Create a minimal DataFrame with these jobs
job_ids = [job['job_id'] for job in existing_jobs]

# Create test dataframe that looks like it came from ingestion
df = pd.DataFrame([
    {
        'id.job': job['job_id'],
        'source.title': job['job_title'],
        'source.company': job['company'],
        'source.location_raw': job['location'],
        'source.description_raw': 'Test description for memory check',
        'sys.is_fresh_job': True,
        'route.ready_for_ai': True,
        'ai.match': '',  # Empty - should trigger memory lookup
    }
    for job in existing_jobs
])

print(f"📊 Created test DataFrame with {len(df)} jobs\n")
print("🔍 Key question: Will the pipeline...")
print("   A) Find these in memory and SKIP OpenAI classification?")
print("   B) Miss them in memory and RE-CLASSIFY with OpenAI?")
print()

# Create pipeline and run just Stage 5 (AI classification)
print("🚀 Running Stage 5 (AI Classification)...")
print("-" * 80)

pipeline = Pipeline(run_id="memory_test", mode="test")
pipeline.df = df

# Run Stage 5
result_df = pipeline._classify_jobs(force_fresh_classification=False)

print("\n" + "="*80)
print("RESULTS:")
print("="*80)

# Check how many were classified
classified_count = (~result_df['ai.match'].isna() & (result_df['ai.match'] != '')).sum()
print(f"Jobs with ai.match filled: {classified_count}/{len(result_df)}")

# If all jobs have classifications, check if they came from memory
if classified_count == len(result_df):
    print("✅ All jobs have classifications")
    print()
    print("   BUT... did they come from:")
    print("   A) Memory reuse (FAST - what we want)")
    print("   B) Fresh OpenAI calls (SLOW - the bug)")
    print()
    print("   Check the logs above for:")
    print("   - '💾 Memory reuse before classification: saved X/Y jobs'")
    print("   - '🔍 Classifying N fresh jobs...'")
    print()
    print("   If it says 'saved 10/10', memory worked!")
    print("   If it says 'Classifying 10 fresh jobs', memory FAILED!")
else:
    print(f"⚠️ Only {classified_count} jobs classified - something went wrong")
