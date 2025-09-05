#!/usr/bin/env python3
"""Test direct insertion to Supabase"""

import os
from datetime import datetime

# Load environment variables
try:
    from tools.secrets_loader import load_local_secrets_to_env
    load_local_secrets_to_env()
except Exception:
    pass

# Set Supabase credentials
os.environ["SUPABASE_URL"] = "https://yqbdltothngundojuebk.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlxYmRsdG90aG5ndW5kb2p1ZWJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU5Mjk4MzgsImV4cCI6MjA3MTUwNTgzOH0.PrJTCbSpmQYQJRM92KKB2TC2xX88IN2coYZGnVotAG8"

from supabase_utils import get_client

def test_direct_insert():
    """Test direct Supabase insert without pipeline"""
    client = get_client()
    if not client:
        print("❌ Failed to get Supabase client")
        return False
    
    # Create minimal test record matching schema
    test_record = {
        'job_id': 'csv_test_direct_001',
        'job_title': 'Test CSV Direct Insert',
        'company': 'Direct Test Company',
        'location': 'Dallas, TX',
        'job_description': 'This is a test description from CSV direct insert',
        'apply_url': 'https://example.com/test-job',
        'match_level': 'good',
        'match_reason': 'Test classification reason',
        'summary': 'Test job summary from direct insert',
        'fair_chance': 'unknown',
        'endorsements': 'unknown',
        'route_type': 'Local',
        'market': 'Dallas',
        'tracked_url': '',
        'classified_at': datetime.now().isoformat(),
        'classification_source': 'ai_classification',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'indeed_job_url': '',
        'search_query': 'csv test',
        'source': 'csv_test',
        'filter_reason': '',
        'google_job_url': '',
        'rules_duplicate_r1': '',
        'rules_duplicate_r2': '',
        'clean_apply_url': 'https://example.com/test-job',
        'job_id_hash': 'test_hash_001'
    }
    
    print(f"🧪 Testing direct insert with record: {list(test_record.keys())}")
    
    try:
        result = client.table('jobs').insert(test_record).execute()
        if result.data:
            print("✅ Direct insert successful!")
            print(f"   Inserted job_id: {result.data[0]['job_id']}")
            
            # Clean up
            client.table('jobs').delete().eq('job_id', 'csv_test_direct_001').execute()
            print("🧹 Test record cleaned up")
            return True
        else:
            print("❌ Insert returned no data")
            return False
            
    except Exception as e:
        print(f"❌ Direct insert failed: {e}")
        return False

if __name__ == "__main__":
    test_direct_insert()