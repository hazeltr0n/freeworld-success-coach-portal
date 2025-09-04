#!/usr/bin/env python3
"""
Test HTML generation for PDF templates
Creates HTML preview file for visual verification
"""

import pandas as pd
from pdf.html_pdf_generator import jobs_dataframe_to_dicts, render_jobs_html

def create_sample_jobs():
    """Create sample jobs for testing"""
    jobs_data = [
        {
            'Title': 'CDL-A OTR Driver - $85K/Year',
            'Company': 'Prime Inc',
            'City': 'Houston',
            'State': 'TX', 
            'Route': 'OTR',
            'MatchBadge': 'Excellent Match',
            'FairChance': False,
            'Description': 'Great opportunity for experienced drivers. Home time every 2-3 weeks.',
            'ApplyURL': 'https://jobs.primeinc.com/apply/123',
            'ShortURL': 'https://fw.ly/abc123'
        },
        {
            'Title': 'Local Delivery Driver - Houston Metro',
            'Company': 'FedEx Ground',
            'City': 'Houston', 
            'State': 'TX',
            'Route': 'Local',
            'MatchBadge': 'Good Match',
            'FairChance': True,
            'Description': '''Local delivery routes in Houston metropolitan area. Home daily with weekends off. 
Requirements: Clean CDL-A license, 1+ years experience, ability to lift 70lbs.
Benefits include medical, dental, vision, 401k with company match, paid time off, and performance bonuses.
Routes typically 8-10 hours with consistent daily schedule. Looking for reliable drivers who take pride in customer service.''',
            'ApplyURL': 'https://careers.fedex.com/apply/456',
            'ShortURL': 'https://fw.ly/def456'
        },
        {
            'Title': 'Regional CDL Driver - Dedicated Route',
            'Company': 'Schneider National', 
            'City': 'Houston',
            'State': 'TX',
            'Route': 'Regional',
            'MatchBadge': 'So-So Match',
            'FairChance': False,
            'Description': '''Schneider National is seeking experienced CDL-A drivers for our dedicated regional routes serving the greater Houston and Texas Triangle markets. 
            
This position offers excellent work-life balance with predictable schedules and regular home time. Our drivers typically run 300-500 miles per day on familiar routes with consistent customers.

KEY RESPONSIBILITIES:
• Operate tractor-trailer combinations safely and efficiently
• Complete pre-trip and post-trip inspections per DOT regulations  
• Maintain accurate logs and documentation using electronic logging devices
• Provide excellent customer service at delivery and pickup locations
• Communicate effectively with dispatch and customers
• Follow all company safety policies and procedures

REQUIREMENTS:
• Valid CDL-A license with clean driving record
• Minimum 6 months verifiable tractor-trailer experience
• Ability to pass DOT physical and drug screening
• Strong work ethic and professional attitude
• Excellent communication skills
• Willingness to work flexible schedules including some weekends

BENEFITS PACKAGE:
• Competitive pay: $70,000-$80,000 annually
• Health, dental, and vision insurance
• 401(k) retirement plan with company matching
• Paid time off and holiday pay
• Performance-based bonuses
• Company-provided equipment and fuel cards
• 24/7 roadside assistance and support
• Opportunities for advancement and additional training

Join the Schneider team and become part of a company that values safety, reliability, and driver satisfaction. We provide the support and resources you need to succeed while maintaining the work-life balance that's important to you and your family.''',
            'ApplyURL': 'https://schneiderjobs.com/apply/789',
            'ShortURL': 'https://fw.ly/ghi789'
        }
    ]
    
    return pd.DataFrame(jobs_data)

if __name__ == '__main__':
    # Generate sample jobs
    df = create_sample_jobs()
    print(f"Converting {len(df)} jobs to HTML...")
    
    # Convert to template format
    jobs = jobs_dataframe_to_dicts(df)
    
    # Create agent parameters
    agent_params = {
        'location': 'Houston Test',
        'agent_name': 'John Test Driver',
        'agent_uuid': 'test-123-456',
        'coach_username': 'testcoach'
    }
    
    # Generate HTML
    html = render_jobs_html(jobs, agent_params)
    
    # Save preview file
    preview_path = 'out/test_preview.html'
    with open(preview_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML preview generated: {preview_path}")
    print(f"Open in browser to verify layout and styling")
    
    # Print some template structure info
    print(f"\nTemplate structure:")
    print(f"• Jobs converted: {len(jobs)}")
    print(f"• HTML length: {len(html):,} characters")
    print(f"• Agent params: {agent_params}")