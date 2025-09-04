#!/usr/bin/env python3
"""
Debug Real Agent Link Generation
Test the exact flow that the mobile portal uses with real agent data
"""

import pandas as pd
from datetime import datetime
import json

def load_real_agent_data():
    """Load real agent profiles"""
    try:
        df = pd.read_csv('agent_profiles_real.csv')
        print(f"📋 Loaded {len(df)} real agent profiles")
        
        # Show first agent
        if not df.empty:
            agent = df.iloc[0]
            print(f"   First agent: {agent['agent_name']} ({agent['agent_uuid'][:8]}...)")
            print(f"   Coach: {agent['coach_username']}")
            print(f"   Config: {agent['search_config']}")
            print(f"   Portal URL: {agent['custom_url']}")
            return agent.to_dict()
    except Exception as e:
        print(f"❌ Error loading agent data: {e}")
        return None

def test_memory_pipeline_with_real_agent(agent_data):
    """Test the memory pipeline exactly as the mobile portal does"""
    print("\n🔧 TESTING MEMORY PIPELINE (Real Agent)")
    print("=" * 60)
    
    try:
        from pipeline_wrapper import StreamlitPipelineWrapper
        
        # Parse search config
        search_config = json.loads(agent_data['search_config'])
        
        # Create pipeline params exactly like agent_job_feed.py does
        pipeline_params = {
            'memory_only': True,
            'generate_pdf': False,
            'generate_csv': False,
            'location': search_config.get('location', 'Houston'),
            'location_type': 'markets',
            'markets': search_config.get('location', 'Houston'),
            'search_terms': 'CDL Driver No Experience',
            'coach_username': agent_data['coach_username'],
            'memory_hours': 72,
            'job_limit': search_config.get('max_jobs', 25),
            'route_filter': search_config.get('route_filter', 'both'),
            'fair_chance_only': search_config.get('fair_chance_only', False),
            'candidate_name': agent_data['agent_name'],
            'candidate_id': agent_data['agent_uuid'],
            'ui_direct': True  # use in-process pipeline path
        }
        
        print("Pipeline params:")
        for key, value in pipeline_params.items():
            print(f"   {key}: {value}")
        
        pipeline = StreamlitPipelineWrapper()
        df, metadata = pipeline.run_pipeline(pipeline_params)
        
        print(f"\n📊 Pipeline Results:")
        print(f"   Success: {metadata.get('success', False)}")
        print(f"   Jobs returned: {len(df)}")
        
        if not df.empty:
            # Check URL columns
            url_cols = [col for col in df.columns if 'url' in col.lower() or 'link' in col.lower() or 'tracked' in col.lower()]
            print(f"   URL columns available: {url_cols}")
            
            # Check first 3 jobs
            print(f"\n📄 First 3 jobs URL analysis:")
            for i in range(min(3, len(df))):
                job = df.iloc[i]
                print(f"\n   Job {i+1}: {job.get('job_title', 'NO TITLE')[:40]}...")
                print(f"   Company: {job.get('company', 'NO COMPANY')}")
                
                # Check all URL fields
                for col in url_cols:
                    value = job.get(col, 'MISSING')
                    if pd.notna(value) and str(value).strip() != '':
                        val_preview = str(value)[:60] + "..." if len(str(value)) > 60 else str(value)
                        print(f"      {col}: {val_preview}")
                    else:
                        print(f"      {col}: EMPTY/NULL")
                        
                # Test mobile portal URL fallback logic
                apply_url = (
                    job.get('tracked_url') or       # New field 
                    job.get('meta.tracked_url') or  # Legacy field 
                    job.get('apply_url') or         # Original apply URL
                    job.get('indeed_job_url') or    # Indeed URL  
                    job.get('google_job_url') or    # Google Jobs URL
                    job.get('clean_apply_url') or   # Cleaned URL
                    ""
                )
                
                is_shortened = (
                    apply_url.startswith('https://freeworldjobs.short.gy') or
                    'functions.supabase.co' in apply_url
                ) if apply_url else False
                
                print(f"      🎯 FINAL apply_url: {apply_url[:60]}{'...' if len(apply_url) > 60 else ''}")
                print(f"      🔗 Is tracking URL: {is_shortened}")
        
        return df, metadata
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_manual_link_generation(agent_data):
    """Test manual link generation like the mobile portal fallback does"""
    print("\n🔗 TESTING MANUAL LINK GENERATION")
    print("=" * 60)
    
    try:
        from link_tracker import LinkTracker
        
        tracker = LinkTracker()
        print(f"LinkTracker available: {tracker.is_available}")
        print(f"Using Supabase Edge: {getattr(tracker, 'use_supabase_edge_function', False)}")
        
        # Test URL from the CSV data
        test_urls = [
            "https://www.indeed.com/viewjob?jk=test123",
            "https://workforcenow.adp.com/jobs/apply/test",
            "https://company.hrmdirect.com/employment/view.php?req=123"
        ]
        
        for i, test_url in enumerate(test_urls, 1):
            print(f"\nTest {i}: {test_url}")
            
            tags = [
                f"coach:{agent_data['coach_username']}", 
                f"candidate:{agent_data['agent_uuid']}", 
                f"agent:{agent_data['agent_name'].replace(' ', '-')}",
                f"market:Houston",
                "type:job_application"
            ]
            
            result = tracker.create_short_link(
                test_url,
                title=f"Job: CDL Driver Position",
                tags=tags,
                candidate_id=agent_data['agent_uuid']
            )
            
            print(f"   Result: {result}")
            print(f"   Is tracking URL: {result != test_url if result else False}")
            print(f"   Tags used: {tags}")
            
    except Exception as e:
        print(f"❌ Manual link generation failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🐛 REAL AGENT LINK DEBUG")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load real agent data
    agent_data = load_real_agent_data()
    if not agent_data:
        print("❌ Cannot proceed without agent data")
        return
    
    # Test pipeline (like mobile portal does)
    df, metadata = test_memory_pipeline_with_real_agent(agent_data)
    
    # Test manual link generation (like mobile portal fallback)
    test_manual_link_generation(agent_data)
    
    print("\n" + "=" * 80)
    print("✅ REAL AGENT DEBUG COMPLETE")
    
    # Summary
    if df is not None and not df.empty:
        tracked_count = 0
        total_jobs = len(df)
        
        for _, job in df.iterrows():
            apply_url = (
                job.get('tracked_url') or job.get('meta.tracked_url') or
                job.get('apply_url') or job.get('indeed_job_url') or
                job.get('google_job_url') or job.get('clean_apply_url') or ""
            )
            if apply_url and (apply_url.startswith('https://freeworldjobs.short.gy') or 'functions.supabase.co' in apply_url):
                tracked_count += 1
        
        print(f"📊 SUMMARY: {tracked_count}/{total_jobs} jobs have tracking URLs ({tracked_count/total_jobs*100:.1f}%)")
    else:
        print("📊 SUMMARY: No jobs returned from pipeline")
    
    print("=" * 80)

if __name__ == "__main__":
    main()