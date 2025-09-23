#!/usr/bin/env python3
"""
Test script to isolate the routing upgrade issue:
Jobs are not getting upgraded to "included" after AI classification
"""

import pandas as pd
import sys
from pathlib import Path
import os

# Add current directory to path
sys.path.append('.')

# Set dummy environment variables
os.environ['OUTSCRAPER_API_KEY'] = 'dummy'
os.environ['OPENAI_API_KEY'] = 'dummy'

def test_routing_upgrade():
    """Test the routing upgrade logic specifically"""
    
    print("🔍 TESTING ROUTING UPGRADE LOGIC")
    print("=" * 60)
    
    # Create a test DataFrame that simulates jobs after AI classification
    test_data = [
        {
            'id.job': 'test-job-1',
            'source.title': 'CDL Driver',
            'source.company': 'Test Company',
            'source.url': 'https://example.com/job1',
            'ai.match': 'good',
            'ai.reason': 'Good CDL opportunity',
            'ai.route_type': 'Local',
            'rules.is_owner_op': False,
            'rules.is_school_bus': False,
            'rules.is_spam_source': False
        },
        {
            'id.job': 'test-job-2',
            'source.title': 'Truck Driver',
            'source.company': 'Another Company',
            'source.url': 'https://example.com/job2',
            'ai.match': 'so-so',
            'ai.reason': 'Decent opportunity',
            'ai.route_type': 'OTR',
            'rules.is_owner_op': False,
            'rules.is_school_bus': False,
            'rules.is_spam_source': False
        },
        {
            'id.job': 'test-job-3',
            'source.title': 'Bad Job',
            'source.company': 'Spam Company',
            'source.url': 'https://example.com/job3',
            'ai.match': 'bad',
            'ai.reason': 'Not a good fit',
            'ai.route_type': 'Unknown',
            'rules.is_owner_op': False,
            'rules.is_school_bus': False,
            'rules.is_spam_source': False
        },
        {
            'id.job': 'test-job-4',
            'source.title': 'Not Classified Yet',
            'source.company': 'Pending Company',
            'source.url': 'https://example.com/job4',
            'rules.is_owner_op': False,
            'rules.is_school_bus': False,
            'rules.is_spam_source': False
            # No AI classification fields - simulates job that passed business rules but no AI yet
        }
    ]
    
    df_test = pd.DataFrame(test_data)
    
    print(f"✅ Created test DataFrame with {len(df_test)} jobs")
    print(f"   - 1 'good' match")
    print(f"   - 1 'so-so' match") 
    print(f"   - 1 'bad' match")
    print(f"   - 1 unclassified job")
    
    # Test the routing transform directly
    print(f"\n🧭 TESTING transform_routing FUNCTION")
    print("=" * 50)
    
    from canonical_transforms import transform_routing
    
    df_routed = transform_routing(df_test, route_filter='both')
    
    print(f"✅ Routing transform complete")
    
    # Check final status for each job
    for i, (_, job) in enumerate(df_routed.iterrows()):
        job_id = job['id.job']
        ai_match = job.get('ai.match', 'None')
        final_status = job.get('route.final_status', 'None')
        
        print(f"\n🔍 JOB {i+1}: {job_id}")
        print(f"   AI Match: '{ai_match}'")
        print(f"   Final Status: '{final_status}'")
        
        # Check if upgrade logic worked
        if ai_match == 'good':
            expected = 'included: good match'
            if final_status == expected:
                print(f"   ✅ CORRECT: Good job upgraded to included")
            else:
                print(f"   ❌ ERROR: Good job should be '{expected}', got '{final_status}'")
        elif ai_match == 'so-so':
            expected = 'included: so-so match'
            if final_status == expected:
                print(f"   ✅ CORRECT: So-so job upgraded to included")
            else:
                print(f"   ❌ ERROR: So-so job should be '{expected}', got '{final_status}'")
        elif ai_match == 'bad':
            if final_status.startswith('AI classified as bad'):
                print(f"   ✅ CORRECT: Bad job filtered out")
            else:
                print(f"   ❌ ERROR: Bad job should be filtered, got '{final_status}'")
        else:
            if final_status == 'passed_all_filters':
                print(f"   ✅ CORRECT: Unclassified job kept as passed_all_filters")
            else:
                print(f"   ❌ ERROR: Unclassified job should be 'passed_all_filters', got '{final_status}'")
    
    # Summary
    print(f"\n📊 ROUTING SUMMARY")
    print("=" * 30)
    
    if 'route.final_status' in df_routed.columns:
        status_counts = df_routed['route.final_status'].value_counts().to_dict()
        print(f"Final status distribution:")
        for status, count in status_counts.items():
            print(f"   - {status}: {count}")
        
        # Count included jobs
        included_count = sum(1 for status in status_counts.keys() if status.startswith('included'))
        print(f"\n✅ Jobs with 'included' status: {included_count} (should be 2)")
        
        if included_count == 2:
            print(f"🎉 SUCCESS: Routing upgrade logic is working correctly!")
        else:
            print(f"❌ FAILURE: Expected 2 included jobs, got {included_count}")
    else:
        print(f"❌ ERROR: No route.final_status column found!")

if __name__ == "__main__":
    test_routing_upgrade()