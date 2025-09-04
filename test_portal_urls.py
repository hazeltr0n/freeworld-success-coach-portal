#!/usr/bin/env python3
"""
Test Portal URL Logic - Check what URLs are available for apply buttons
"""

import pandas as pd

def test_portal_urls():
    """Test the exact URL logic from render_job_card"""
    
    # Load the memory jobs
    csv_path = '/Users/freeworld_james/Desktop/freeworld-job-scraper/streamlit-app/FreeWorld_Jobs/Houston_quality_jobs_20250902_010814.csv'
    df = pd.read_csv(csv_path)
    
    print("🔍 PORTAL URL AVAILABILITY TEST")
    print("=" * 60)
    print(f"📊 Testing {len(df)} memory jobs")
    
    # Test first 10 jobs
    test_jobs = df.head(10)
    
    apply_buttons = 0
    no_buttons = 0
    
    print(f"\n📋 URL Availability Check:")
    print(f"{'Job':<4} {'Title':<25} {'Status':<15} {'URL Source':<15}")
    print("-" * 60)
    
    for idx, job in test_jobs.iterrows():
        title = str(job.get('source.title', 'No Title'))[:24]
        
        # EXACT logic from render_job_card (line 366)
        apply_url = (
            job.get('meta.tracked_url') or 
            job.get('source.url', '') or 
            job.get('source.apply_url', '') or 
            job.get('source.indeed_url', '') or 
            job.get('source.google_url', '')
        )
        
        if apply_url:
            apply_buttons += 1
            # Determine which field provided the URL
            if job.get('meta.tracked_url'):
                source = "meta.tracked_url"
            elif job.get('source.url', ''):
                source = "source.url"
            elif job.get('source.apply_url', ''):
                source = "source.apply_url"
            elif job.get('source.indeed_url', ''):
                source = "source.indeed_url"
            else:
                source = "source.google_url"
            
            status = "✅ APPLY BUTTON"
            print(f"{idx:<4} {title:<25} {status:<15} {source:<15}")
        else:
            no_buttons += 1
            status = "❌ NO BUTTON"
            print(f"{idx:<4} {title:<25} {status:<15} {'NONE':<15}")
    
    print("-" * 60)
    print(f"📊 SUMMARY:")
    print(f"   Jobs with apply buttons: {apply_buttons}/{len(test_jobs)} ({apply_buttons/len(test_jobs)*100:.1f}%)")
    print(f"   Jobs without buttons:    {no_buttons}/{len(test_jobs)} ({no_buttons/len(test_jobs)*100:.1f}%)")
    
    if apply_buttons == len(test_jobs):
        print(f"\n✅ CONCLUSION: Portal should show apply buttons on all jobs!")
        print(f"   Problem is likely in the Streamlit rendering, not URL availability.")
    else:
        print(f"\n❌ CONCLUSION: {no_buttons} jobs have no URLs available")
        print(f"   These jobs won't have apply buttons in the portal.")
    
    # Show sample URLs
    print(f"\n🔗 SAMPLE URLS:")
    for idx, job in test_jobs.head(3).iterrows():
        title = str(job.get('source.title', 'No Title'))[:30]
        tracked = job.get('meta.tracked_url', 'NONE')
        apply = job.get('source.apply_url', 'NONE')
        print(f"   Job {idx}: {title}...")
        print(f"      meta.tracked_url: {tracked[:50]}...")
        print(f"      source.apply_url: {apply[:50] if apply != 'NONE' else 'NONE'}...")

if __name__ == "__main__":
    test_portal_urls()