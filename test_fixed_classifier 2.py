#!/usr/bin/env python3
"""
Test the fixed job classifier on previously bad classifications from Bay Area jobs.
This will show the improvement from the balanced prompt vs over-conservative prompt.
"""

import pandas as pd
import sys
import os

# Add current directory to path so we can import from job_classifier
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from job_classifier import JobClassifier

def test_fixed_classifier():
    print("🧪 Testing Fixed Job Classifier")
    print("=" * 50)
    
    # Read the previously problematic Bay Area results
    try:
        df = pd.read_csv('/workspaces/freeworld-success-coach-portal/freeworld_jobs_Bay Area_20250829_130755.csv', 
                         on_bad_lines='skip', low_memory=False)
        print(f"📊 Loaded {len(df)} jobs from previous Bay Area run")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return

    # Filter to jobs that were previously classified as "bad"
    if 'ai.match' not in df.columns:
        print("❌ No ai.match column found in CSV")
        return
        
    bad_jobs = df[df['ai.match'] == 'bad'].copy()
    print(f"🎯 Found {len(bad_jobs)} jobs previously classified as 'bad'")
    
    if len(bad_jobs) == 0:
        print("✅ No bad jobs to retest!")
        return
    
    # Test the full set of bad jobs
    test_jobs = bad_jobs.copy()
    print(f"🧪 Testing {len(test_jobs)} jobs with fixed classifier...")
    
    # Prepare jobs for classifier
    jobs_list = []
    for _, row in test_jobs.iterrows():
        # Extract job data for classifier
        job_data = {
            'job_id': str(row.get('id.job', f'test_{len(jobs_list)}')),
            'job_title': str(row.get('source.title', 'Unknown Title')),
            'company': str(row.get('source.company', 'Unknown Company')), 
            'location': str(row.get('source.location_raw', 'Unknown Location')),
            'job_description': str(row.get('source.description_raw', 'No description'))
        }
        jobs_list.append(job_data)
    
    # Initialize fixed classifier and test
    classifier = JobClassifier()
    
    print(f"\n🚀 Running classification on {len(jobs_list)} jobs...")
    try:
        results = classifier.classify_jobs_in_batches(jobs_list, batch_size=20)
        print(f"✅ Classification completed: {len(results)} results")
    except Exception as e:
        print(f"❌ Classification failed: {e}")
        return
    
    # Analyze results
    print(f"\n📈 RESULTS COMPARISON:")
    print("=" * 60)
    
    good_count = sum(1 for r in results if r['match'] == 'good')
    so_so_count = sum(1 for r in results if r['match'] == 'so-so') 
    bad_count = sum(1 for r in results if r['match'] == 'bad')
    error_count = sum(1 for r in results if r['match'] == 'error')
    
    print(f"🟢 GOOD:   {good_count:2d}/{len(results)} ({good_count/len(results)*100:.1f}%)")
    print(f"🟡 SO-SO:  {so_so_count:2d}/{len(results)} ({so_so_count/len(results)*100:.1f}%)")
    print(f"🔴 BAD:    {bad_count:2d}/{len(results)} ({bad_count/len(results)*100:.1f}%)")
    print(f"⚠️  ERROR:  {error_count:2d}/{len(results)} ({error_count/len(results)*100:.1f}%)")
    
    success_rate = (good_count + so_so_count) / len(results) * 100
    print(f"\n🎯 SUCCESS RATE: {success_rate:.1f}% (was 0% when all were 'bad')")
    
    print(f"\n📋 DETAILED RESULTS:")
    print("=" * 80)
    
    for i, result in enumerate(results):
        job = jobs_list[i]
        old_reason = test_jobs.iloc[i].get('ai.reason', 'No reason')[:60]
        
        print(f"\n{i+1}. {job['job_title'][:50]}")
        print(f"   Company: {job['company'][:30]}")
        print(f"   OLD: bad - {old_reason}...")
        print(f"   NEW: {result['match']} - {result['reason'][:60]}...")
        
        if result['match'] in ['good', 'so-so']:
            print(f"   ✅ IMPROVED! (bad → {result['match']})")
        elif result['match'] == 'bad':
            print(f"   ⚠️  Still bad - may be legitimately bad")
        else:
            print(f"   ❌ Error in processing")

if __name__ == "__main__":
    test_fixed_classifier()