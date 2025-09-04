#!/usr/bin/env python3
"""
Test PDF generation with Bay Area CSV to identify text jumbling
"""

import pandas as pd
from fpdf_pdf_generator import generate_fpdf_job_cards

# Load the Bay Area CSV
df = pd.read_csv('/workspaces/freeworld-success-coach-portal/freeworld_jobs_Bay Area_20250829_061223.csv')

print(f"Loaded {len(df)} jobs from Bay Area CSV")

# Filter to just good and so-so jobs for testing
good_jobs = df[df['ai.match'].isin(['good', 'so-so'])]
print(f"Found {len(good_jobs)} good/so-so jobs")

if len(good_jobs) == 0:
    print("No good/so-so jobs found, using first 3 jobs")
    test_jobs = df.head(3)
else:
    test_jobs = good_jobs.head(3)  # Just test with 3 jobs

print(f"Testing PDF generation with {len(test_jobs)} jobs")

# Test PDF generation
try:
    pdf_path = '/workspaces/freeworld-success-coach-portal/test_pdf_output.pdf'
    pdf_bytes = generate_fpdf_job_cards(
        test_jobs, 
        output_path=pdf_path,
        market="Bay Area",
        coach_name="TestCoach", 
        candidate_name="Benjamin"
    )
    
    if pdf_bytes:
        with open('/workspaces/freeworld-success-coach-portal/test_pdf_output.pdf', 'wb') as f:
            f.write(pdf_bytes)
        print("✅ PDF generated successfully: test_pdf_output.pdf")
    else:
        print("❌ PDF generation failed - no bytes returned")
        
except Exception as e:
    print(f"❌ PDF generation failed: {e}")
    import traceback
    traceback.print_exc()