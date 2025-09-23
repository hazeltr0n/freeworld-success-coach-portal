#!/usr/bin/env python3
"""
Google Jobs Storage-Only Pipeline
Scrapes Google Jobs and stores directly in Supabase for future memory lookups
NO PDF, NO CSV, NO COMPLEX PIPELINE - Just scrape and store!
"""

import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from job_classifier import JobClassifier
from job_memory_db import JobMemoryDB
from job_filters import JobFilters
import hashlib

load_dotenv()

class GoogleJobsStorage:
    def __init__(self):
        self.api_key = 'NmY3ZWU2ZDY4ZDE3NDE3YWJhNzM2NzJlN2NkMzU5ZmZ8MzQwNWIyYmQ2ZA'  # Google Jobs API key
        self.headers = {'X-API-KEY': self.api_key}
        self.classifier = JobClassifier()
        self.memory_db = JobMemoryDB()
        self.filters = JobFilters()
        
    def scrape_and_store_google_jobs(self, location, search_terms="CDL Driver", limit=100):
        """
        Scrape Google Jobs and store directly in Supabase
        Returns: number of jobs stored
        """
        print(f"🔍 Google Jobs Storage-Only Pipeline")
        print(f"📍 Location: {location}")
        print(f"🔍 Terms: {search_terms}")
        print(f"📊 Limit: {limit}")
        print("=" * 60)
        
        # 1. Scrape Google Jobs
        jobs_df = self._scrape_google_jobs(search_terms, location, limit)
        
        if jobs_df.empty:
            print("❌ No jobs found from Google Jobs API")
            return 0
            
        print(f"✅ Scraped {len(jobs_df)} jobs from Google Jobs API")
        
        # 2. Generate job IDs and basic normalization
        jobs_df = self._normalize_basic_fields(jobs_df, location)
        
        # 3. Check for duplicates against existing Supabase jobs
        jobs_df = self._deduplicate_against_memory(jobs_df)
        
        if jobs_df.empty:
            print("❌ All jobs are duplicates")
            return 0
            
        # 4. Apply business rules filtering
        jobs_df = self._apply_business_rules(jobs_df)
        
        if jobs_df.empty:
            print("❌ All jobs filtered out by business rules")
            return 0
            
        # 5. AI classify jobs
        jobs_df = self._classify_jobs(jobs_df)
        
        # 6. Store in Supabase (only quality jobs)
        quality_jobs = jobs_df[jobs_df['ai.match'].isin(['good', 'so-so'])]
        
        if quality_jobs.empty:
            print("❌ No quality jobs to store")
            return 0
            
        stored_count = self._store_in_supabase(quality_jobs)
        
        print(f"✅ Stored {stored_count} quality jobs in Supabase")
        print("🎯 Google Jobs storage pipeline complete!")
        
        return stored_count
    
    def _scrape_google_jobs(self, search_terms, location, limit):
        """Scrape Google Jobs API with sync call (not async batch)"""
        # Format query like async job manager
        location_formatted = location.replace(',', '').replace('  ', ' ').strip()
        query = f"{search_terms} {location_formatted}"
        
        url = "https://api.outscraper.com/google-search-jobs"  # Correct URL from async manager
        params = {
            'query': query,
            'limit': limit,
            'async': 'false'  # Sync call for immediate results
        }
        
        print(f"📡 Calling Google Jobs API (sync): '{query}'")
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle Outscraper response format
                jobs_data = []
                if isinstance(data, dict) and 'data' in data:
                    # New format: {'id': '...', 'status': 'Success', 'data': [[job1, job2, ...]]}
                    data_array = data['data']
                    if isinstance(data_array, list) and len(data_array) > 0:
                        jobs_data = data_array[0]  # Get the job array from nested structure
                elif isinstance(data, list) and len(data) > 0:
                    # Old format: [{'jobs': [job1, job2, ...]}]
                    first_result = data[0]
                    if isinstance(first_result, dict) and 'jobs' in first_result:
                        jobs_data = first_result['jobs']
                
                print(f"🔍 Found {len(jobs_data)} jobs in response")
                if jobs_data and len(jobs_data) > 0:
                    df = pd.DataFrame(jobs_data)
                    print(f"✅ Google API returned {len(df)} jobs")
                    print(f"🔍 Job fields: {list(df.columns)}")
                    return df
                else:
                    print("⚠️ No jobs found in API response")
            else:
                print(f"❌ Google Jobs API error: {response.status_code}")
                print(f"❌ Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Google Jobs API exception: {e}")
            
        return pd.DataFrame()
    
    def _normalize_basic_fields(self, df, location):
        """Basic field normalization for Google Jobs"""
        print("🧹 Normalizing Google Jobs fields...")
        
        # Generate job IDs
        job_ids = []
        for idx, row in df.iterrows():
            company = str(row.get('company_name', 'Unknown')).strip()
            title = str(row.get('title', 'Job')).strip()
            location_text = str(row.get('location', location)).strip()
            
            # Create consistent ID
            id_text = f"{company}|{location_text}|{title}".lower()
            job_id = hashlib.md5(id_text.encode()).hexdigest()[:8]
            job_ids.append(job_id)
        
        df['job_id'] = job_ids
        
        # Map Google Jobs fields to canonical format that store_classifications expects
        df['id.job'] = df['job_id']  # Use job_id as canonical id
        df['source.title'] = df['title']
        df['source.company'] = df['company']  
        df['source.location_raw'] = df['location']
        df['source.description_raw'] = df['description']
        # Apply URLs are in apply_urls array - get first URL
        df['source.apply_url'] = df.apply(lambda row: row.get('apply_urls', [{}])[0].get('apply_url:', '') if row.get('apply_urls') else '', axis=1)
        df['source.salary_raw'] = ''  # Not in Google Jobs API response
        
        # Additional canonical fields
        df['norm.location'] = location
        df['meta.market'] = location
        df['meta.search_terms'] = f"CDL Driver"
        df['sys.classification_source'] = 'ai_classification'
        df['sys.is_fresh_job'] = True
        
        print(f"✅ Normalized {len(df)} Google Jobs")
        return df
    
    def _classify_jobs(self, df):
        """AI classify Google Jobs"""
        print(f"🤖 AI classifying {len(df)} Google Jobs...")
        
        jobs_for_classification = []
        for idx, row in df.iterrows():
            job_data = {
                'job_id': row['job_id'],
                'job_title': row['source.title'],
                'company': row['source.company'],
                'location': row['source.location_raw'],
                'job_description': row['source.description_raw']
            }
            jobs_for_classification.append(job_data)
        
        # Classify using existing classifier
        classification_results = self.classifier.classify_jobs_in_batches(jobs_for_classification)
        
        # Map results back to DataFrame using canonical field names
        for idx, result in enumerate(classification_results):
            # Use canonical field names that store_classifications expects
            df.loc[idx, 'ai.match'] = result.get('match', 'error')
            df.loc[idx, 'ai.reason'] = result.get('reason', '')
            df.loc[idx, 'ai.summary'] = result.get('summary', '')
            df.loc[idx, 'ai.fair_chance'] = result.get('fair_chance', '')
            df.loc[idx, 'ai.endorsements'] = result.get('endorsements', '')
            df.loc[idx, 'ai.route_type'] = result.get('route_type', 'Unknown')
        
        quality_count = len(df[df['ai.match'].isin(['good', 'so-so'])])
        print(f"✅ AI classified: {quality_count} quality jobs out of {len(df)}")
        
        return df
    
    def _store_in_supabase(self, df):
        """Store quality jobs in Supabase using store_classifications"""
        print(f"💾 Storing {len(df)} quality jobs in Supabase...")
        
        try:
            # Use the existing store_classifications method
            success = self.memory_db.store_classifications(df)
            
            if success:
                print(f"✅ Successfully stored {len(df)} jobs in Supabase")
                return len(df)
            else:
                print(f"❌ Failed to store jobs in Supabase")
                return 0
                
        except Exception as e:
            print(f"❌ Error storing jobs: {e}")
            return 0
    
    def _deduplicate_against_memory(self, df):
        """Remove jobs that already exist in Supabase"""
        print(f"🔄 Checking {len(df)} jobs for duplicates...")
        
        # Use check_job_memory to get existing jobs
        job_ids = df['job_id'].tolist()
        existing_jobs = self.memory_db.check_job_memory(job_ids, hours=168)  # Check 7 days
        
        existing_job_ids = set(existing_jobs.keys())
        if existing_job_ids:
            print(f"🗑️ Removing {len(existing_job_ids)} duplicate jobs")
            df = df[~df['job_id'].isin(existing_job_ids)]
        
        print(f"✅ {len(df)} unique jobs remaining after deduplication")
        return df
    
    def _apply_business_rules(self, df):
        """Apply FreeWorld business rule filters"""
        print(f"📋 Applying business rules to {len(df)} jobs...")
        
        initial_count = len(df)
        
        # Filter out owner-operator jobs
        owner_op_mask = df['source.description_raw'].str.contains('owner.operator|lease.purchase|owner/operator', case=False, na=False)
        df = df[~owner_op_mask]
        owner_op_removed = initial_count - len(df)
        
        # Filter out school bus jobs
        school_bus_mask = df['source.title'].str.contains('school.bus', case=False, na=False) | \
                         df['source.description_raw'].str.contains('school.bus', case=False, na=False)
        df = df[~school_bus_mask]
        school_bus_removed = len(df) - (initial_count - owner_op_removed)
        
        if owner_op_removed > 0:
            print(f"🚫 Filtered {owner_op_removed} owner-operator jobs")
        if school_bus_removed > 0:
            print(f"🚫 Filtered {school_bus_removed} school bus jobs")
            
        print(f"✅ {len(df)} jobs passed business rules")
        return df

def main():
    """Test the Google Jobs storage pipeline - 1 page exact location only"""
    storage = GoogleJobsStorage()
    
    # Test 1 page (10 jobs) exact location only
    location = "Austin, TX"
    print(f"\n{'='*60}")
    stored = storage.scrape_and_store_google_jobs(location, limit=10)  # Test with 10 jobs
    print(f"📊 Result: {stored} jobs stored for {location}")

if __name__ == "__main__":
    main()