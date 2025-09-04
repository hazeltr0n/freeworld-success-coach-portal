#!/usr/bin/env python3
"""
Test harness for HTML/CSS-based PDF generation system
Tests all three backends (FPDF, Playwright, WeasyPrint) with sample data
"""

import pandas as pd
import os
from pdf_generator import generate_pdf
from pathlib import Path

def create_sample_jobs():
    """Create sample jobs for testing - short, medium, and very long descriptions"""
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

def test_all_backends():
    """Test all three PDF backends with sample data"""
    
    # Create output directory
    output_dir = Path('out')
    output_dir.mkdir(exist_ok=True)
    
    # Generate sample jobs
    df = create_sample_jobs()
    print(f"Created sample dataset with {len(df)} jobs")
    print("Job description lengths:", [len(desc) for desc in df['Description']])
    
    # Test parameters
    test_params = {
        'candidate_name': 'John Test Driver',
        'candidate_id': 'test-123-456',
        'coach_username': 'testcoach',
        'route_filter': 'both',
        'experience_level': 'experienced'
    }
    
    # Test all backends
    backends = ['fpdf', 'playwright', 'weasyprint']
    results = {}
    
    for backend in backends:
        output_file = output_dir / f'test_report_{backend}.pdf'
        print(f"\nTesting {backend} backend...")
        
        try:
            result = generate_pdf(
                df, 
                str(output_file), 
                market="Houston Test", 
                backend=backend,
                **test_params
            )
            results[backend] = {'success': True, 'path': result}
            print(f"✅ {backend}: Generated successfully -> {output_file}")
            
        except ImportError as e:
            results[backend] = {'success': False, 'error': f'Missing dependency: {e}'}
            print(f"⚠️  {backend}: Missing dependency - {e}")
            
        except Exception as e:
            results[backend] = {'success': False, 'error': str(e)}
            print(f"❌ {backend}: Failed - {e}")
    
    # Test unknown backend (should raise ValueError)
    print(f"\nTesting invalid backend...")
    try:
        generate_pdf(df, str(output_dir / 'test_invalid.pdf'), backend="invalid")
        print("❌ Invalid backend test: Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Invalid backend test: Correctly raised ValueError - {e}")
    except Exception as e:
        print(f"⚠️  Invalid backend test: Unexpected error - {e}")
    
    # Print summary
    print(f"\n{'='*50}")
    print("TEST RESULTS SUMMARY")
    print(f"{'='*50}")
    
    for backend, result in results.items():
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        print(f"{backend:12} {status}")
        if not result['success']:
            print(f"             Error: {result['error']}")
        
    print(f"\nGenerated files in: {output_dir.absolute()}")
    
    # Visual check instructions
    print(f"\n{'='*50}")
    print("VISUAL CHECK INSTRUCTIONS")
    print(f"{'='*50}")
    print("Please verify the generated PDFs have:")
    print("• One job per page")
    print("• Apply button fixed to the bottom") 
    print("• Header/metadata matching Houston report style")
    print("• Proper 'Job X of Y' and shortlink in footer")
    print("• Descriptions properly formatted (short/medium/long)")

if __name__ == '__main__':
    test_all_backends()