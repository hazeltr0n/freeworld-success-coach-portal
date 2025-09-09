#!/usr/bin/env python3
"""Test xhtml2pdf functionality with your HTML template"""

import pandas as pd
from pdf.html_pdf_generator import jobs_dataframe_to_dicts, render_jobs_html
from xhtml2pdf import pisa

# Create test data that matches your DataFrame structure
test_data = {
    'source.title': ['CDL Driver - Local Routes', 'OTR Truck Driver'],
    'source.company': ['FreeWorld Trucking', 'Highway Express'],
    'source.location_raw': ['Atlanta, GA', 'Houston, TX'],
    'norm.city': ['Atlanta', 'Houston'],
    'norm.state': ['GA', 'TX'],
    'ai.match': ['good', 'so-so'],
    'ai.route_type': ['Local', 'OTR'],
    'ai.fair_chance': [True, False],
    'ai.summary': [
        'Great local driving opportunity with competitive pay and excellent benefits. Home daily with weekends off.',
        'Over-the-road position offering travel across multiple states. Requires clean driving record.'
    ]
}

df = pd.DataFrame(test_data)
print(f"Test DataFrame: {len(df)} jobs")

# Convert to job dictionaries using YOUR template system
jobs = jobs_dataframe_to_dicts(df)
print(f"Jobs converted: {len(jobs)} jobs")

# Build agent_params like your system does
agent_params = {
    'location': 'Test Market',
    'agent_name': 'Test Agent',
    'coach_name': 'Test Coach',
    'show_prepared_for': True
}

# Generate HTML using YOUR template system
html = render_jobs_html(jobs, agent_params)
print(f"HTML generated: {len(html)} characters")

# Convert CSS variables for xhtml2pdf compatibility
from pdf_css_converter import convert_css_variables_for_xhtml2pdf
html_converted = convert_css_variables_for_xhtml2pdf(html)
print(f"HTML converted: {len(html_converted)} characters")

# Test xhtml2pdf conversion
output_path = "test_output.pdf"
try:
    with open(output_path, "wb") as result_file:
        pisa_status = pisa.CreatePDF(html_converted, dest=result_file)
    
    if not pisa_status.err:
        print(f"✅ PDF generated successfully: {output_path}")
        import os
        size = os.path.getsize(output_path)
        print(f"   File size: {size} bytes")
    else:
        print(f"❌ PDF generation failed with errors")
        print(f"   Errors: {pisa_status.err}")

except ImportError:
    print("❌ xhtml2pdf not available")
except Exception as e:
    print(f"❌ Error: {e}")