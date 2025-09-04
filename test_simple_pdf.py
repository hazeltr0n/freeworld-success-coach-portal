#!/usr/bin/env python3
"""
Test Simple Agent Tracking in PDF Generation
Create one universal link for Benjamin instead of 70 individual ones
"""

import os
import pandas as pd
from simple_agent_tracking import SimpleAgentTracker

def test_simple_pdf_links():
    """Test simple agent tracking approach with PDF data"""
    
    # Load the recent Houston CSV data
    csv_path = "/Users/freeworld_james/Desktop/freeworld-job-scraper/streamlit-app/FreeWorld_Jobs/Houston_quality_jobs_20250902_010814.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    # Load the jobs
    df = pd.read_csv(csv_path)
    print(f"📊 Loaded {len(df)} jobs from CSV")
    
    # Benjamin's info
    agent_uuid = "ef78e371-1929-11ef-937f-de2fe15254ef"
    agent_name = "Benjamin Bechtolsheim"
    coach_username = "james.hazelton"
    
    # Create simple tracker
    tracker = SimpleAgentTracker()
    
    print("\n🎯 SIMPLE AGENT TRACKING TEST")
    print("=" * 50)
    
    # Create ONE universal link for Benjamin
    print("1️⃣ Creating Benjamin's Universal Tracking Link...")
    universal_link = tracker.get_agent_click_link(agent_uuid, agent_name, coach_username)
    print(f"   ✅ Universal Link: {universal_link}")
    
    # Show how this would work for first 5 jobs
    print(f"\n2️⃣ Apply URLs for first 5 jobs (ALL use same universal link):")
    for i in range(min(5, len(df))):
        job = df.iloc[i]
        job_title = job.get('source.title', 'Job')
        
        # Get original job URL (skip meta.tracked_url - we want raw URLs)
        original_url = (
            job.get('source.apply_url', '') or
            job.get('source.indeed_url', '') or 
            job.get('source.google_url', '')
        )
        
        # Create apply URL using universal link
        apply_url = tracker.create_job_apply_url(agent_uuid, original_url, universal_link)
        
        print(f"   Job {i+1}: {job_title[:30]}...")
        print(f"          Apply URL: {apply_url[:80]}...")
    
    print(f"\n3️⃣ Comparison - Current vs Simple:")
    print(f"   Current Complex: 70 jobs = 70 Short.io API calls")
    print(f"   Simple Approach: 70 jobs = 1 Short.io API call")
    print(f"   Cost Reduction: 70x cheaper")
    print(f"   Speed Improvement: 70x faster")
    print(f"   Tracking Granularity: Agent clicks (not per-job)")
    
    print(f"\n4️⃣ Universal Link Details:")
    print(f"   Link: {universal_link}")
    print(f"   Agent: {agent_name} ({agent_uuid[:8]})")
    print(f"   Coach: {coach_username}")
    print(f"   All {len(df)} jobs use this SAME link")
    print(f"   Webhook sees: 'Benjamin clicked' + target job URL")

if __name__ == "__main__":
    test_simple_pdf_links()