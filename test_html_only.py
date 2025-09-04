#!/usr/bin/env python3
"""
Test HTML template rendering (no PDF export)
Verifies templates and data mapping work correctly
"""

import pandas as pd
from pdf.html_pdf_generator import jobs_dataframe_to_dicts, render_jobs_html

def test_html_rendering():
    # Sample job data
    jobs_data = [
        {
            'Title': 'CDL-A OTR Driver - $85K/Year',
            'Company': 'Prime Inc',
            'City': 'Houston',
            'State': 'TX', 
            'Route': 'OTR',
            'MatchBadge': 'Excellent Match',
            'FairChance': False,
            'Description': 'Great opportunity for experienced drivers.',
            'ApplyURL': 'https://jobs.primeinc.com/apply/123',
            'ShortURL': 'https://fw.ly/abc123'
        }
    ]
    
    df = pd.DataFrame(jobs_data)
    
    # Test data conversion
    jobs = jobs_dataframe_to_dicts(df)
    print(f"✅ Converted {len(jobs)} jobs to template format")
    print(f"Sample job keys: {list(jobs[0].keys())}")
    
    # Test HTML rendering
    agent_params = {'location': 'Houston Test'}
    html = render_jobs_html(jobs, agent_params)
    
    print(f"✅ Generated HTML ({len(html):,} characters)")
    
    # Check key elements are present
    checks = [
        ('Houston Test Jobs Report', 'Report title'),
        ('CDL-A OTR Driver', 'Job title'),
        ('Prime Inc', 'Company name'), 
        ('Excellent Match', 'Match badge'),
        ('APPLY NOW', 'Apply button'),
        ('Job 1 of 1', 'Job counter'),
        ('https://fw.ly/abc123', 'Short URL')
    ]
    
    print(f"\nTemplate verification:")
    for text, desc in checks:
        if text in html:
            print(f"✅ {desc}: Found")
        else:
            print(f"❌ {desc}: Missing '{text}'")
    
    # Save HTML for manual inspection
    with open('out/template_test.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ HTML template test complete")
    print(f"Preview file: out/template_test.html")

if __name__ == '__main__':
    test_html_rendering()