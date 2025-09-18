#!/usr/bin/env python3
"""
Test script for pathway badge integration in PDF generator
Tests the new career pathway classification and badge display
"""

import pandas as pd
from fpdf_pdf_generator import FreeWorldJobCardFPDF

def test_pathway_badges():
    """Test pathway badge generation with sample data"""

    # Create sample job data with pathway classifications
    test_jobs = [
        {
            'source.title': 'Dock Worker - CDL Training Program',
            'source.company': 'FreeWorld Logistics',
            'source.location': 'Dallas, TX',
            'source.description': 'Great opportunity to start as dock worker and train for CDL license',
            'ai.match': 'good',
            'ai.summary': 'Excellent entry-level opportunity with clear career progression',
            'ai.fair_chance': 'fair_chance_employer',
            'ai.career_pathway': 'dock_to_driver',
            'ai.training_provided': True,
            'source.url': 'https://example.com/job1'
        },
        {
            'source.title': 'Warehouse Associate - Driver Training Available',
            'source.company': 'ABC Transport',
            'source.location': 'Houston, TX',
            'source.description': 'Warehouse position with opportunity to advance to driving role',
            'ai.match': 'so-so',
            'ai.summary': 'Warehouse role with potential driver advancement path',
            'ai.fair_chance': 'unknown',
            'ai.career_pathway': 'warehouse_to_driver',
            'ai.training_provided': False,
            'source.url': 'https://example.com/job2'
        },
        {
            'source.title': 'CDL Training Program - No Experience Required',
            'source.company': 'Driver Academy',
            'source.location': 'Austin, TX',
            'source.description': 'Comprehensive CDL training program with job placement',
            'ai.match': 'good',
            'ai.summary': 'Full CDL training program for new drivers',
            'ai.fair_chance': 'fair_chance_employer',
            'ai.career_pathway': 'internal_cdl_training',
            'ai.training_provided': True,
            'source.url': 'https://example.com/job3'
        },
        {
            'source.title': 'Logistics Coordinator',
            'source.company': 'Freight Systems Inc',
            'source.location': 'San Antonio, TX',
            'source.description': 'Office logistics role with career advancement opportunities',
            'ai.match': 'so-so',
            'ai.summary': 'Good logistics experience building role',
            'ai.fair_chance': 'no_requirements_mentioned',
            'ai.career_pathway': 'logistics_progression',
            'ai.training_provided': False,
            'source.url': 'https://example.com/job4'
        },
        {
            'source.title': 'Delivery Driver - No CDL Required',
            'source.company': 'Local Delivery Co',
            'source.location': 'Fort Worth, TX',
            'source.description': 'Local delivery routes in company vehicle',
            'ai.match': 'so-so',
            'ai.summary': 'Local driving experience building opportunity',
            'ai.fair_chance': 'unknown',
            'ai.career_pathway': 'non_cdl_driving',
            'ai.training_provided': False,
            'source.url': 'https://example.com/job5'
        }
    ]

    # Convert to DataFrame
    df = pd.DataFrame(test_jobs)

    print("🧪 Testing Pathway Badge Integration")
    print(f"📊 Created {len(df)} test jobs with pathway classifications")

    # Initialize PDF generator
    pdf = FreeWorldJobCardFPDF()

    try:
        # Create test PDF with pathway badges
        pdf.create_title_page(market="Dallas-Fort Worth", job_count=len(df), coach_name="Test Coach")

        # Add jobs to PDF to test badge rendering
        for idx, job in df.iterrows():
            pdf.create_job_card(job.to_dict(), job_number=idx+1, total_jobs=len(df))

        # Save test PDF
        output_file = "test_pathway_badges.pdf"
        pdf.output(output_file)

        print(f"✅ Successfully generated test PDF: {output_file}")
        print("🔍 Check the PDF to verify pathway badges are displayed correctly")

        # Print summary of what should be visible
        print("\n📋 Expected Badge Types:")
        for _, job in df.iterrows():
            pathway = job.get('ai.career_pathway', '')
            match = job.get('ai.match', '')
            fair_chance = job.get('ai.fair_chance', '')

            badges = []
            if match == 'good':
                badges.append("Excellent Match")
            elif match == 'so-so':
                badges.append("Possible Fit")

            if 'fair_chance_employer' in fair_chance:
                badges.append("Fair Chance Employer")

            if pathway == 'dock_to_driver':
                badges.append("DOCK TO DRIVER")
            elif pathway == 'internal_cdl_training':
                badges.append("CDL TRAINING PROVIDED")
            elif pathway == 'warehouse_to_driver':
                badges.append("WAREHOUSE TO DRIVER")
            elif pathway == 'logistics_progression':
                badges.append("LOGISTICS CAREER PATH")
            elif pathway == 'non_cdl_driving':
                badges.append("NON-CDL DRIVING")

            print(f"  {job['source.title']}: {', '.join(badges)}")

        return True

    except Exception as e:
        print(f"❌ Error generating test PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pathway_badges()
    if success:
        print("\n🎉 Pathway badge integration test completed successfully!")
    else:
        print("\n💥 Pathway badge integration test failed!")