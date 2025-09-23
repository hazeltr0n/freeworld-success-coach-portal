#!/usr/bin/env python3
"""
Debug Agent Tracking - Test the actual agent job feed flow
"""

import pandas as pd
import sys
sys.path.append('.')

from free_agent_system import update_job_tracking_for_agent

def test_agent_tracking():
    """Test what actually happens in agent job feed"""
    
    # Load the memory jobs (like agent_job_feed does)
    csv_path = '/Users/freeworld_james/Desktop/freeworld-job-scraper/streamlit-app/FreeWorld_Jobs/Houston_quality_jobs_20250902_010814.csv'
    df = pd.read_csv(csv_path)
    
    print("🔍 AGENT TRACKING DEBUG")
    print("=" * 50)
    print(f"📊 Loaded {len(df)} jobs from memory")
    
    # Benjamin's agent params (like agent_job_feed creates)
    agent_params = {
        'agent_uuid': 'ef78e371-1929-11ef-937f-de2fe15254ef',
        'agent_name': 'Benjamin Bechtolsheim',
        'coach_username': 'james.hazelton',
        'location': 'Houston',
        'route_filter': 'both',
        'experience_level': 'both',
        'fair_chance_only': False,
        'max_jobs': 25
    }
    
    # Take first 5 jobs for testing
    test_df = df.head(5).copy()
    
    print("\n1️⃣ BEFORE update_job_tracking_for_agent:")
    for i, job in test_df.iterrows():
        title = job.get('source.title', 'No Title')[:30]
        tracked_url = job.get('meta.tracked_url', 'MISSING')
        apply_url = job.get('source.apply_url', 'MISSING')
        print(f"   Job {i}: {title}...")
        print(f"      meta.tracked_url: {tracked_url[:50]}...")
        print(f"      source.apply_url: {apply_url[:50] if apply_url != 'MISSING' else 'MISSING'}...")
    
    # Call the function that agent_job_feed calls
    print(f"\n2️⃣ CALLING update_job_tracking_for_agent...")
    result_df = update_job_tracking_for_agent(test_df, agent_params)
    
    print(f"\n3️⃣ AFTER update_job_tracking_for_agent:")
    for i, job in result_df.iterrows():
        title = job.get('source.title', 'No Title')[:30]
        tracked_url = job.get('meta.tracked_url', 'MISSING')
        apply_url = job.get('source.apply_url', 'MISSING')
        print(f"   Job {i}: {title}...")
        print(f"      meta.tracked_url: {tracked_url[:50]}...")
        print(f"      source.apply_url: {apply_url[:50] if apply_url != 'MISSING' else 'MISSING'}...")
    
    # Test render_job_card URL logic
    print(f"\n4️⃣ RENDER_JOB_CARD URL LOGIC:")
    for i, job in result_df.iterrows():
        title = job.get('source.title', 'No Title')[:30]
        
        # This is the EXACT logic from render_job_card
        apply_url = job.get('meta.tracked_url') or job.get('source.url', '') or job.get('source.apply_url', '') or job.get('source.indeed_url', '') or job.get('source.google_url', '')
        
        if apply_url:
            print(f"   ✅ Job {i} ({title}...): APPLY BUTTON WORKS")
            print(f"      URL: {apply_url[:60]}...")
        else:
            print(f"   ❌ Job {i} ({title}...): NO APPLY BUTTON")
            print(f"      No URL found in any field")

if __name__ == "__main__":
    test_agent_tracking()