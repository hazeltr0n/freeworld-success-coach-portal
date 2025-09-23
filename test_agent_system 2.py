#!/usr/bin/env python3
"""
Test script for the Free Agent Management System
"""

from free_agent_system import encode_agent_params, decode_agent_params, generate_agent_url

def test_url_encoding():
    """Test the URL encoding and decoding system"""
    print("🧪 Testing URL Encoding/Decoding System")
    print("=" * 50)
    
    # Test parameters
    test_params = {
        'agent_uuid': '59bd7baa-1efb-11ef-937f-de2fe15254ef',
        'agent_name': 'Benjamin Bechtolsheim',
        'location': 'Houston',
        'route_filter': 'local',
        'fair_chance_only': True,
        'max_jobs': 25,
        'experience_level': 'entry',
        'coach_username': 'sarah_davis'
    }
    
    print("📊 Original Parameters:")
    for key, value in test_params.items():
        print(f"  {key}: {value}")
    
    # Test encoding
    encoded = encode_agent_params(test_params)
    print(f"\n🔐 Encoded String: {encoded}")
    print(f"📏 Length: {len(encoded)} characters")
    
    # Test decoding
    decoded = decode_agent_params(encoded)
    print("\n🔓 Decoded Parameters:")
    for key, value in decoded.items():
        print(f"  {key}: {value}")
    
    # Test URL generation
    agent_url = generate_agent_url(test_params['agent_uuid'], test_params)
    print(f"\n🔗 Generated URL:")
    print(f"  {agent_url}")
    
    # Verify accuracy
    print(f"\n✅ Encoding Test: {'PASS' if decoded == test_params else 'FAIL'}")
    
    return decoded == test_params

def test_job_filtering():
    """Test job filtering by experience level"""
    import pandas as pd
    from free_agent_system import filter_jobs_by_experience, prioritize_jobs_for_display
    
    print("\n🧪 Testing Job Filtering System")
    print("=" * 50)
    
    # Create test job data
    test_jobs = pd.DataFrame([
        {'source.title': 'Entry Level CDL Driver', 'ai.match': 'good', 'source.company': 'Good Transport'},
        {'source.title': 'Experienced OTR Driver', 'ai.match': 'bad', 'source.company': 'Pro Logistics'},
        {'source.title': 'Local Delivery Driver', 'ai.match': 'so-so', 'source.company': 'City Express'},
        {'source.title': 'Senior Driver Position', 'ai.match': 'bad', 'source.company': 'Elite Freight'},
        {'source.title': 'No Experience Required', 'ai.match': 'good', 'source.company': 'Starter Logistics'},
    ])
    
    print(f"📊 Original Job Count: {len(test_jobs)}")
    
    # Test entry level filtering
    entry_jobs = filter_jobs_by_experience(test_jobs, 'entry')
    print(f"👶 Entry Level Jobs: {len(entry_jobs)} (good/so-so matches)")
    for _, job in entry_jobs.iterrows():
        print(f"  • {job['source.title']} ({job['ai.match']})")
    
    # Test experienced filtering  
    experienced_jobs = filter_jobs_by_experience(test_jobs, 'experienced')
    print(f"\n👨‍💼 Experienced Jobs: {len(experienced_jobs)} (bad matches)")
    for _, job in experienced_jobs.iterrows():
        print(f"  • {job['source.title']} ({job['ai.match']})")
    
    # Test both filtering
    both_jobs = filter_jobs_by_experience(test_jobs, 'both')
    print(f"\n🎯 All Jobs: {len(both_jobs)}")
    
    # Test prioritization
    prioritized = prioritize_jobs_for_display(test_jobs)
    print(f"\n📈 Prioritized Order:")
    for i, (_, job) in enumerate(prioritized.iterrows(), 1):
        score = job.get('display_priority', 0)
        print(f"  {i}. {job['source.title']} ({job['ai.match']}) - Score: {score}")
    
    return True

if __name__ == "__main__":
    print("🚀 FreeWorld Free Agent Management System Test")
    print("=" * 60)
    
    # Run tests
    url_test = test_url_encoding()
    filter_test = test_job_filtering()
    
    print("\n" + "=" * 60)
    print("📋 Test Results:")
    print(f"  URL Encoding/Decoding: {'✅ PASS' if url_test else '❌ FAIL'}")
    print(f"  Job Filtering: {'✅ PASS' if filter_test else '❌ FAIL'}")
    
    if url_test and filter_test:
        print("\n🎉 All tests passed! The Free Agent Management System is ready.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
    
    print("\n📝 Next Steps:")
    print("  1. Navigate to the Free Agent Management tab in the main app")
    print("  2. Add a test Free Agent using Airtable lookup")
    print("  3. Configure their job search parameters")
    print("  4. Copy and test their custom job feed URL")
    print("  5. Verify mobile-friendly display and click tracking")