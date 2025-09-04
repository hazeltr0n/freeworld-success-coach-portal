#!/usr/bin/env python3
"""
Debug Link Flow - Trace link generation from form to mobile portal
"""

import pandas as pd
import os
from datetime import datetime

def debug_csv_data():
    """Check what URL fields exist in the current CSV data"""
    print("=" * 80)
    print("🔍 DEBUGGING CSV DATA")
    print("=" * 80)
    
    csv_files = ['jobs_final.csv', 'jobs_compliant.csv', 'jobs_cleaned.csv']
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            print(f"\n📄 Analyzing {csv_file}:")
            try:
                df = pd.read_csv(csv_file)
                print(f"   Total jobs: {len(df)}")
                
                # Check URL-related columns
                url_columns = [col for col in df.columns if 'url' in col.lower() or 'link' in col.lower() or 'tracked' in col.lower()]
                print(f"   URL columns: {url_columns}")
                
                # Check values for each URL column
                for col in url_columns:
                    non_null = df[col].notna().sum()
                    non_empty = (df[col].notna() & (df[col] != '')).sum()
                    print(f"   {col}: {non_null} non-null, {non_empty} non-empty")
                    
                    # Show sample values
                    if non_empty > 0:
                        sample_vals = df[df[col].notna() & (df[col] != '')][col].head(3).tolist()
                        for i, val in enumerate(sample_vals):
                            val_preview = val[:60] + "..." if len(val) > 60 else val
                            print(f"      Sample {i+1}: {val_preview}")
                
                break  # Use first available CSV
                
            except Exception as e:
                print(f"   Error reading {csv_file}: {e}")
        else:
            print(f"   {csv_file} not found")

def debug_pipeline_output():
    """Check what the pipeline actually generates"""
    print("\n" + "=" * 80)
    print("🔧 DEBUGGING PIPELINE OUTPUT")
    print("=" * 80)
    
    try:
        from pipeline_wrapper import StreamlitPipelineWrapper
        from link_tracker import LinkTracker
        
        print("\n1. Testing LinkTracker directly:")
        tracker = LinkTracker()
        print(f"   Available: {tracker.is_available}")
        print(f"   API Key present: {bool(tracker.api_key)}")
        print(f"   Using Supabase Edge: {getattr(tracker, 'use_supabase_edge_function', False)}")
        
        # Test link creation
        test_url = "https://www.indeed.com/viewjob?jk=test123"
        result = tracker.create_short_link(
            test_url, 
            title="Test CDL Job", 
            tags=["coach:test", "candidate:debug123", "market:houston"]
        )
        print(f"   Test link result: {result[:80]}..." if result and len(result) > 80 else f"   Test link result: {result}")
        print(f"   Is tracking URL: {result != test_url if result else False}")
        
        print("\n2. Testing pipeline with memory-only mode:")
        pipeline = StreamlitPipelineWrapper()
        
        params = {
            'memory_only': True,
            'generate_pdf': False,
            'generate_csv': False,
            'location': 'Houston',
            'location_type': 'markets',
            'coach_username': 'debug_coach',
            'candidate_name': 'Debug Agent',
            'candidate_id': 'debug123',
            'job_limit': 5
        }
        
        df, metadata = pipeline.run_pipeline(params)
        print(f"   Pipeline returned: {len(df)} jobs")
        print(f"   Metadata success: {metadata.get('success', False)}")
        
        if not df.empty:
            # Check URL fields in pipeline output
            url_cols = [col for col in df.columns if 'url' in col.lower() or 'link' in col.lower() or 'tracked' in col.lower()]
            print(f"   Pipeline URL columns: {url_cols}")
            
            # Check first job's URL fields
            first_job = df.iloc[0]
            print(f"   First job URL fields:")
            for col in url_cols:
                value = first_job.get(col, 'MISSING')
                if pd.notna(value) and value != '':
                    val_preview = str(value)[:60] + "..." if len(str(value)) > 60 else str(value)
                    print(f"      {col}: {val_preview}")
                else:
                    print(f"      {col}: EMPTY")
        
    except Exception as e:
        print(f"   Pipeline test error: {e}")
        import traceback
        traceback.print_exc()

def debug_mobile_portal_logic():
    """Check mobile portal URL selection logic"""
    print("\n" + "=" * 80)
    print("📱 DEBUGGING MOBILE PORTAL LOGIC")
    print("=" * 80)
    
    # Simulate a job record from pipeline
    test_jobs = [
        {
            'job_title': 'CDL Driver - Local Routes',
            'company': 'Test Transport',
            'tracked_url': 'https://freeworldjobs.short.gy/abc123',  # Good case
            'meta.tracked_url': 'https://freeworldjobs.short.gy/xyz789',
            'apply_url': 'https://www.indeed.com/viewjob?jk=original123',
            'indeed_job_url': 'https://www.indeed.com/viewjob?jk=indeed456',
            'google_job_url': '',
            'clean_apply_url': 'indeed.com/viewjob?jk=clean789'
        },
        {
            'job_title': 'OTR Driver - Good Pay',
            'company': 'Another Transport',
            'tracked_url': '',  # Empty case
            'meta.tracked_url': '',
            'apply_url': 'https://www.indeed.com/viewjob?jk=original456', 
            'indeed_job_url': 'https://www.indeed.com/viewjob?jk=indeed789',
            'google_job_url': 'https://jobs.google.com/jobview?jk=google123',
            'clean_apply_url': 'indeed.com/viewjob?jk=clean456'
        },
        {
            'job_title': 'Regional Driver Position',
            'company': 'Third Transport',
            'tracked_url': pd.NaN,  # NaN case
            'meta.tracked_url': pd.NaN,
            'apply_url': 'https://company.com/jobs/driver789',
            'indeed_job_url': '',
            'google_job_url': '',
            'clean_apply_url': 'company.com/jobs/driver789'
        }
    ]
    
    print("\n Testing URL fallback logic (from agent_job_feed.py):")
    for i, job in enumerate(test_jobs, 1):
        print(f"\n   Job {i}: {job['job_title']}")
        
        # This is the exact logic from agent_job_feed.py lines 391-400
        apply_url = (
            job.get('tracked_url') or       # New field from instant_memory_search
            job.get('meta.tracked_url') or  # Legacy field from pipeline
            job.get('apply_url') or         # Original apply URL
            job.get('indeed_job_url') or    # Indeed URL  
            job.get('google_job_url') or    # Google Jobs URL
            job.get('clean_apply_url') or   # Cleaned URL
            ""
        )
        
        print(f"      Final apply_url: {apply_url}")
        print(f"      Is tracking URL: {apply_url.startswith('https://freeworldjobs.short.gy') if apply_url else False}")
        
        # Show the fallback chain
        print(f"      Fallback chain:")
        print(f"        tracked_url: {repr(job.get('tracked_url'))}")
        print(f"        meta.tracked_url: {repr(job.get('meta.tracked_url'))}")
        print(f"        apply_url: {repr(job.get('apply_url'))}")
        print(f"        indeed_job_url: {repr(job.get('indeed_job_url'))}")

def main():
    """Run all debug checks"""
    print("🐛 LINK FLOW DEBUG ANALYSIS")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    debug_csv_data()
    debug_pipeline_output()
    debug_mobile_portal_logic()
    
    print("\n" + "=" * 80)
    print("✅ DEBUG ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()