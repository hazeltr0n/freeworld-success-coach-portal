#!/usr/bin/env python3
"""
Test Streamlit HTML preview functionality with CSV data
"""

import pandas as pd
from pdf.html_pdf_generator import jobs_dataframe_to_dicts, render_jobs_html

def test_streamlit_html_preview():
    """Test HTML preview exactly as it would work in Streamlit"""
    
    print("🧪 Testing Streamlit HTML preview functionality...")
    
    # Load CSV data (using the same CSV as before)
    csv_path = "/workspaces/freeworld-success-coach-portal/FreeWorld_Jobs/Dallas_TX_complete_jobs_20250831_095204.csv"
    df = pd.read_csv(csv_path)
    sample_df = df.head(3)  # Small sample for testing
    
    print(f"📊 Loaded {len(sample_df)} jobs from CSV")
    
    # Map to template format (same as before)
    mapped_data = []
    for _, row in sample_df.iterrows():
        def safe_str(val, default=''):
            if pd.isna(val) or val is None:
                return default
            return str(val)
        
        def safe_bool(val):
            if pd.isna(val) or val is None:
                return False
            return bool(val)
        
        ai_match = safe_str(row.get('ai.match', ''), 'unknown').lower()
        match_badge = ai_match.title() + ' Match' if ai_match != 'unknown' else 'Excellent Match'
        
        mapped_data.append({
            'Title': safe_str(row.get('source.title', ''), 'CDL Driver Position'),
            'Company': safe_str(row.get('source.company', ''), 'Trucking Company'), 
            'City': safe_str(row.get('norm.city', ''), 'Dallas'),
            'State': safe_str(row.get('norm.state', ''), 'TX'),
            'Route': safe_str(row.get('ai.route_type', ''), 'OTR'),
            'MatchBadge': match_badge,
            'FairChance': safe_bool(row.get('ai.fair_chance', False)),
            'Description': safe_str(row.get('norm.description', ''), 'No description available'),
            'ApplyURL': safe_str(row.get('clean_apply_url', '') or row.get('source.apply_url', ''), 'https://example.com'),
            'ShortURL': safe_str(row.get('meta.tracked_url', ''), 'https://fw.ly/test')
        })
    
    df_test = pd.DataFrame(mapped_data)
    
    # Test the exact code path that Streamlit will use
    try:
        print("🔄 Testing jobs_dataframe_to_dicts...")
        jobs = jobs_dataframe_to_dicts(df_test)
        print(f"✅ Converted to {len(jobs)} job dictionaries")
        
        print("🔄 Testing render_jobs_html...")
        agent_params = {
            'location': 'Dallas Test',
            'agent_name': 'Test Agent',
            'agent_uuid': 'test-streamlit-123',
            'coach_username': 'testcoach'
        }
        html = render_jobs_html(jobs, agent_params)
        print(f"✅ Generated HTML ({len(html):,} characters)")
        
        # Save for manual inspection
        with open('out/streamlit_test_preview.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Test some key elements are present
        required_elements = [
            'Dallas Test Jobs Report',  # Title
            'No Experience, Regional Class A Drivers',  # Job title
            'KARIM TRUCKING LLC',  # Company
            'APPLY NOW',  # Button
            'Job 1 of 3',  # Counter
        ]
        
        print(f"\n✅ HTML Content Verification:")
        for element in required_elements:
            if element in html:
                print(f"   ✅ Found: {element}")
            else:
                print(f"   ❌ Missing: {element}")
        
        print(f"\n🎉 Streamlit HTML preview test successful!")
        print(f"📁 Preview saved: out/streamlit_test_preview.html")
        
        # Show first job sample
        print(f"\n📋 Sample job data:")
        sample_job = jobs[0]
        for key, value in sample_job.items():
            if len(str(value)) > 100:
                print(f"   {key}: {str(value)[:100]}...")
            else:
                print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Streamlit HTML preview test failed: {e}")
        return False

if __name__ == '__main__':
    test_streamlit_html_preview()