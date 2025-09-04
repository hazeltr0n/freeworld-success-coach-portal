#!/usr/bin/env python3
"""
Test the complete pipeline with known good Google Jobs data
This validates the entire flow from raw JSON to classified results
"""

import os
import json
import pandas as pd
from datetime import datetime
from async_job_manager import AsyncJobManager

def load_test_data():
    """Load sample Google Jobs data"""
    test_file = 'test_data/google_jobs_sample.json'
    
    if not os.path.exists(test_file):
        print(f"❌ Test data file not found: {test_file}")
        return None
    
    with open(test_file, 'r') as f:
        return json.load(f)

def test_google_jobs_processing():
    """Test processing of Google Jobs sample data"""
    print("🧪 Testing Google Jobs Processing Pipeline")
    print("=" * 50)
    
    # Load test data
    test_data = load_test_data()
    if not test_data:
        return False
    
    print(f"✅ Loaded test data with {len(test_data['data'][0])} jobs")
    
    # Initialize manager
    manager = AsyncJobManager()
    
    # Sample search params for test
    search_params = {
        'search_terms': 'CDL driver',
        'location': 'Houston, TX',
        'coach_username': 'test_coach'
    }
    
    try:
        # Test data processing
        print("\n🔄 Processing raw Google Jobs data...")
        jobs_df = manager.process_google_results(test_data['data'], search_params)
        print(f"✅ Converted to DataFrame: {len(jobs_df)} jobs")
        
        # Display sample of processed data
        print("\n📊 Sample processed data:")
        print("Columns:", list(jobs_df.columns))
        
        for i, row in jobs_df.head(3).iterrows():
            print(f"\nJob {i+1}:")
            print(f"  Title: {row.get('source.title', 'N/A')}")
            print(f"  Company: {row.get('source.company', 'N/A')}")
            print(f"  Location: {row.get('source.location', 'N/A')}")
            print(f"  Salary: {row.get('source.salary', 'N/A')}")
            print(f"  Hash: {row.get('sys.hash', 'N/A')[:12]}...")
        
        # Test job classification
        print(f"\n🤖 Testing AI classification...")
        try:
            from jobs_schema import generate_job_id
            from job_classifier import JobClassifier
            
            # Prepare classification data
            classifier = JobClassifier()
            df_cls = pd.DataFrame()
            df_cls['job_title'] = jobs_df.get('source.title', '')
            df_cls['company'] = jobs_df.get('source.company', '')
            df_cls['location'] = jobs_df.get('source.location', '')
            df_cls['job_description'] = jobs_df.get('source.description', '')
            df_cls['job_id'] = df_cls.apply(
                lambda r: generate_job_id(str(r['company']), str(r['location']), str(r['job_title'])), 
                axis=1
            )
            
            # Run classification
            print(f"  Classifying {len(df_cls)} jobs...")
            classified_df = classifier.classify_jobs(df_cls.copy())
            
            # Show classification results
            classification_counts = classified_df['match'].value_counts()
            print(f"✅ Classification complete:")
            for match_type, count in classification_counts.items():
                print(f"  {match_type}: {count} jobs")
            
            # Show sample classifications
            print(f"\n📋 Sample classifications:")
            for i, row in classified_df.head(3).iterrows():
                print(f"\nJob {i+1}: {row['job_title'][:50]}...")
                print(f"  Match: {row['match']}")
                print(f"  Route: {row.get('route_type', 'N/A')}")
                print(f"  Summary: {row['summary'][:100]}...")
            
            # Test quality job filtering
            quality_jobs = classified_df[classified_df['match'].isin(['good', 'so-so'])]
            print(f"\n✅ Quality jobs: {len(quality_jobs)}/{len(classified_df)} ({len(quality_jobs)/len(classified_df)*100:.1f}%)")
            
            return True
            
        except Exception as e:
            print(f"❌ Classification test failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        return False

def test_webhook_integration():
    """Test the webhook processing with sample data"""
    print("\n🔗 Testing Webhook Integration")
    print("=" * 50)
    
    test_data = load_test_data()
    if not test_data:
        return False
    
    try:
        from zapier_webhook_processor import process_zapier_webhook
        
        # Test webhook processing (will show "no job found" since it's test data)
        result = process_zapier_webhook(test_data)
        print(f"✅ Webhook processing result: {result['status']} - {result['message']}")
        return True
        
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")
        return False

def run_complete_pipeline_test():
    """Run the complete pipeline test suite"""
    print("🚀 Complete Pipeline Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    
    tests = [
        ("Google Jobs Processing", test_google_jobs_processing),
        ("Webhook Integration", test_webhook_integration)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 30)
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Pipeline is working correctly.")
    else:
        print(f"\n⚠️  {total-passed} tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == '__main__':
    # Make sure test_data directory exists
    os.makedirs('test_data', exist_ok=True)
    
    # Run tests
    success = run_complete_pipeline_test()
    exit(0 if success else 1)