#!/usr/bin/env python3
"""
Simple test for async Google Jobs submission
"""

import os
import toml
from async_job_manager import AsyncJobManager

def load_secrets():
    """Load Streamlit secrets and set as environment variables"""
    try:
        secrets_path = ".streamlit/secrets.toml"
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            for key, value in secrets.items():
                os.environ[key] = str(value)
            return True
        else:
            print("❌ Secrets file not found")
            return False
    except Exception as e:
        print(f"❌ Error loading secrets: {e}")
        return False

def test_async_submission():
    """Test just the async submission part"""
    print("🧪 Testing Async Google Jobs Submission")
    print("=" * 50)
    
    # Load secrets first
    if not load_secrets():
        return False
    
    # Initialize async job manager
    try:
        manager = AsyncJobManager()
        print("✅ AsyncJobManager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize AsyncJobManager: {e}")
        return False
    
    # Define minimal search parameters
    search_params = {
        'search_terms': 'CDL Driver',
        'location': 'Dallas, TX', 
        'limit': 20,  # Very small batch
        'coach_username': 'test_user'
    }
    
    print(f"\n📋 Search Parameters:")
    print(f"   Terms: {search_params['search_terms']}")
    print(f"   Location: {search_params['location']}")
    print(f"   Limit: {search_params['limit']}")
    
    # Submit the search
    try:
        print(f"\n🚀 Submitting async Google Jobs search...")
        job = manager.submit_google_search(search_params, 'test_user')
        
        print(f"✅ Search submitted successfully!")
        print(f"   Job ID: {job.id}")
        print(f"   Status: {job.status}")
        print(f"   Request ID: {job.request_id}")
        print(f"   Submitted at: {job.submitted_at}")
        
        print(f"\n📊 Next steps:")
        print(f"   - The job is now processing in the background")
        print(f"   - Outscraper request ID: {job.request_id}")
        print(f"   - Results will be available in 2-3 minutes")
        print(f"   - Check the Supabase async_job_queue table for status updates")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to submit search: {e}")
        return False

if __name__ == "__main__":
    success = test_async_submission()
    if success:
        print(f"\n🎉 Async submission test completed successfully!")
    else:
        print(f"\n💥 Async submission test failed")