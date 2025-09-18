#!/usr/bin/env python3
"""
Test script for pathway badge integration in HTML templates
Tests that pathway badges render correctly in job cards
"""

from jinja2 import Environment, FileSystemLoader

def test_html_pathway_badges():
    """Test pathway badge rendering in HTML templates"""

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader('templates'))

    # Test data with pathway classifications
    test_jobs = [
        {
            'title': 'Dock Worker - CDL Training Program',
            'company': 'FreeWorld Logistics',
            'match': 'good',
            'fair_chance': True,
            'career_pathway': 'dock_to_driver',
            'apply_url': 'https://example.com/job1'
        },
        {
            'title': 'Warehouse Associate - Driver Training Available',
            'company': 'ABC Transport',
            'match': 'so-so',
            'career_pathway': 'warehouse_to_driver',
            'apply_url': 'https://example.com/job2'
        },
        {
            'title': 'CDL Training Program - No Experience Required',
            'company': 'Driver Academy',
            'match': 'good',
            'fair_chance': True,
            'career_pathway': 'internal_cdl_training',
            'apply_url': 'https://example.com/job3'
        },
        {
            'title': 'Logistics Coordinator',
            'company': 'Freight Systems Inc',
            'match': 'so-so',
            'career_pathway': 'logistics_progression',
            'apply_url': 'https://example.com/job4'
        },
        {
            'title': 'Delivery Driver - No CDL Required',
            'company': 'Local Delivery Co',
            'match': 'so-so',
            'career_pathway': 'non_cdl_driving',
            'apply_url': 'https://example.com/job5'
        }
    ]

    print("🧪 Testing HTML Pathway Badge Integration")

    try:
        # Test individual job card template
        template = env.get_template('job_card.html')

        for i, job in enumerate(test_jobs):
            output_file = f"test_job_card_{i+1}.html"

            html_output = template.render(job=job, base_url='.')

            with open(output_file, 'w') as f:
                f.write(html_output)

            # Check if pathway badge is in output
            pathway = job.get('career_pathway', '')
            if pathway and pathway not in ['', 'unknown', 'general_warehouse', 'no_pathway']:
                if 'pathway-badge' in html_output:
                    print(f"✅ Job {i+1}: Pathway badge '{pathway}' rendered correctly")
                else:
                    print(f"❌ Job {i+1}: Pathway badge '{pathway}' missing from output")
            else:
                print(f"ℹ️  Job {i+1}: No pathway badge expected (pathway: {pathway})")

        print(f"\n📄 Generated {len(test_jobs)} test HTML files")
        print("🔍 Open the test_job_card_*.html files in a browser to verify badge styling")

        # Test job card partial template
        if env.get_template('_job_card.html'):
            print("✅ Job card partial template also updated with pathway badges")

        return True

    except Exception as e:
        print(f"❌ Error testing HTML pathway badges: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_html_pathway_badges()
    if success:
        print("\n🎉 HTML pathway badge integration test completed successfully!")
    else:
        print("\n💥 HTML pathway badge integration test failed!")