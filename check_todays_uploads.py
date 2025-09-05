#!/usr/bin/env python3
"""
Quick check of today's job uploads to Supabase
"""
import os
from datetime import datetime
from job_memory_db import JobMemoryDB

def check_todays_uploads():
    """Check how many jobs were uploaded to Supabase today"""
    
    db = JobMemoryDB()
    
    # Get today's date in YYYY-MM-DD format
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"📅 Checking uploads for {today}")
    
    try:
        # Query jobs created today
        response = db.supabase.table('jobs').select('*', count='exact').gte('created_at', today).execute()
        
        total_today = response.count
        print(f"📊 Total jobs uploaded today: {total_today:,}")
        
        # If we have jobs, let's look at the first one to understand the schema
        if total_today > 0:
            sample_job = db.supabase.table('jobs').select('*').gte('created_at', today).limit(1).execute()
            if sample_job.data:
                print("\n🔍 Sample job fields:")
                job_fields = list(sample_job.data[0].keys())
                classification_fields = [f for f in job_fields if 'match' in f.lower() or 'classification' in f.lower() or 'ai' in f.lower()]
                market_fields = [f for f in job_fields if 'market' in f.lower() or 'location' in f.lower()]
                
                print(f"   Classification fields: {classification_fields}")
                print(f"   Market fields: {market_fields}")
                
                # Try to get breakdown by any classification field found
                if classification_fields:
                    class_field = classification_fields[0]
                    print(f"\n📊 Using classification field: {class_field}")
                    
                    # Get unique values for this field
                    values = db.supabase.table('jobs').select(class_field).gte('created_at', today).execute()
                    value_counts = {}
                    for job in values.data:
                        val = job.get(class_field, 'Unknown')
                        value_counts[val] = value_counts.get(val, 0) + 1
                    
                    for value, count in sorted(value_counts.items(), key=lambda x: x[1], reverse=True):
                        print(f"   {value}: {count:,} jobs")
                
                # Get market breakdown if field exists  
                if market_fields:
                    market_field = market_fields[0]
                    print(f"\n📍 Markets uploaded today (using {market_field}):")
                    markets = db.supabase.table('jobs').select(market_field).gte('created_at', today).execute()
                    
                    market_counts = {}
                    for job in markets.data:
                        market = job.get(market_field, 'Unknown')
                        market_counts[market] = market_counts.get(market, 0) + 1
                    
                    for market, count in sorted(market_counts.items(), key=lambda x: x[1], reverse=True):
                        print(f"   {market}: {count:,} jobs")
        
    except Exception as e:
        print(f"❌ Error checking uploads: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_todays_uploads()