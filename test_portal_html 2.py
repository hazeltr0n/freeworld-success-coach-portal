#!/usr/bin/env python3
"""
Test Free Agent Portal HTML rendering with real data
"""

import pandas as pd
from pdf.html_pdf_generator import jobs_dataframe_to_dicts, render_jobs_html

def test_portal_html_rendering():
    """Test the exact HTML rendering that will be used in the Free Agent Portal"""
    
    print("🧪 Testing Free Agent Portal HTML rendering...")
    
    # Load real CSV data (same as before)
    csv_path = "./repos/freeworld-success-coach-portal/FreeWorld_Jobs/complete_jobs_20250901_000357.csv"
    df = pd.read_csv(csv_path)
    sample_df = df.head(5)  # Portal-sized sample
    
    print(f"📊 Loaded {len(sample_df)} jobs for portal test")
    
    # Map data exactly as the portal does
    mapped_data = []
    location = "Dallas, TX"
    
    for _, row in sample_df.iterrows():
        def safe_str(val, default=''):
            if pd.isna(val) or val is None:
                return default
            return str(val)
        
        def safe_bool(val):
            if pd.isna(val) or val is None:
                return False
            return bool(val)
        
        ai_match = safe_str(row.get('ai.match', ''), 'good').lower()
        match_badge = ai_match.title() + ' Match' if ai_match != 'unknown' else 'Excellent Match'
        
        # Try to get apply URL from multiple sources (same logic as portal)
        apply_url = (safe_str(row.get('meta.tracked_url', '')) or 
                   safe_str(row.get('source.apply_url', '')) or 
                   safe_str(row.get('source.indeed_url', '')) or
                   safe_str(row.get('clean_apply_url', ''), '#'))
        
        mapped_data.append({
            'Title': safe_str(row.get('source.title', ''), 'CDL Driver Position'),
            'Company': safe_str(row.get('source.company', ''), 'Trucking Company'), 
            'City': safe_str(row.get('norm.city', ''), location.split(',')[0] if ',' in location else location),
            'State': safe_str(row.get('norm.state', ''), 'TX'),
            'Route': safe_str(row.get('ai.route_type', ''), 'OTR'),
            'MatchBadge': match_badge,
            'FairChance': safe_bool(row.get('ai.fair_chance', False)),
            'Description': safe_str(row.get('ai.summary', row.get('norm.description', '')), 'Great opportunity for CDL drivers. Contact your career coach for more details.'),
            'ApplyURL': apply_url,
            'ShortURL': safe_str(row.get('meta.tracked_url', ''), f'Apply to {safe_str(row.get("source.company", "Company"))}')
        })
    
    portal_df = pd.DataFrame(mapped_data)
    print(f"🔄 Mapped {len(portal_df)} jobs to portal format")
    
    # Generate HTML using template system (same as portal)
    try:
        jobs = jobs_dataframe_to_dicts(portal_df)
        portal_agent_params = {
            'location': 'Dallas, TX',
            'agent_name': 'Test Free Agent',
            'agent_uuid': 'portal-test-123',
            'coach_username': 'testcoach'
        }
        html = render_jobs_html(jobs, portal_agent_params)
        
        print(f"✅ Generated portal HTML ({len(html):,} characters)")
        
        # Save for inspection
        with open('out/portal_test_preview.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"📁 Portal HTML saved: out/portal_test_preview.html")
        
        # Verify key portal elements
        portal_elements = [
            'Dallas, TX Jobs Report',
            'No Experience, Regional Class A Drivers',
            'KARIM TRUCKING LLC', 
            'APPLY NOW',
            'Job 1 of 5'
        ]
        
        print(f"\n✅ Portal HTML Verification:")
        all_good = True
        for element in portal_elements:
            if element in html:
                print(f"   ✅ Found: {element}")
            else:
                print(f"   ❌ Missing: {element}")
                all_good = False
        
        if all_good:
            print(f"\n🎉 Free Agent Portal HTML rendering test SUCCESSFUL!")
            print(f"🚀 The portal is ready to display beautiful job cards to Free Agents!")
        else:
            print(f"\n⚠️  Some elements missing - check template mapping")
        
        # Show sample job for verification
        print(f"\n📋 Sample portal job:")
        sample_job = jobs[0]
        for key, value in sample_job.items():
            if len(str(value)) > 80:
                print(f"   {key}: {str(value)[:80]}...")
            else:
                print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Portal HTML test failed: {e}")
        return False

if __name__ == '__main__':
    test_portal_html_rendering()