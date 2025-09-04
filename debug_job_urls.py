#!/usr/bin/env python3
"""
Debug job URL fields to see what's available for apply buttons
"""
from job_memory_db import JobMemoryDB
from datetime import datetime

def debug_job_urls():
    """Check URL fields in recent jobs"""
    
    db = JobMemoryDB()
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"🔍 Debugging job URL fields for {today}")
    
    # Get a few recent jobs
    jobs = db.supabase.table('jobs').select('*').gte('created_at', today).limit(5).execute()
    
    if not jobs.data:
        print("❌ No jobs found for today")
        return
    
    for i, job in enumerate(jobs.data[:3]):
        print(f"\n📋 Job {i+1}: {job.get('title', 'NO TITLE')[:30]}...")
        print(f"   Company: {job.get('company', 'NO COMPANY')}")
        
        # Check all URL-related fields
        url_fields = [k for k in job.keys() if 'url' in k.lower() or 'link' in k.lower()]
        print(f"   URL fields available: {url_fields}")
        
        for field in url_fields:
            value = job.get(field, '')
            if value:
                print(f"   ✅ {field}: {value[:70]}...")
            else:
                print(f"   ❌ {field}: EMPTY")
        
        # Check the specific fields our fallback logic uses
        fallback_fields = ['meta.tracked_url', 'source.url', 'source.apply_url', 'source.indeed_url', 'source.google_url']
        print(f"   Fallback chain check:")
        for field in fallback_fields:
            value = job.get(field, '')
            status = "✅" if value else "❌"
            print(f"   {status} {field}: {value[:50] if value else 'EMPTY'}...")

if __name__ == "__main__":
    debug_job_urls()