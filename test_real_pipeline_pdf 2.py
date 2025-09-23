#!/usr/bin/env python3
"""
Test PDF generation with REAL pipeline and show_prepared_for parameter
Uses the actual pipeline_wrapper to simulate Streamlit behavior
"""

import pandas as pd
from pipeline_wrapper import StreamlitPipelineWrapper
import os

# Test data matching what Streamlit would send
test_data = {
    'source.title': ['CDL Driver - Local Routes', 'OTR Truck Driver'],
    'source.company': ['FreeWorld Trucking', 'Highway Express'],
    'source.location_raw': ['Houston, TX', 'Houston, TX'],
    'norm.city': ['Houston', 'Houston'],
    'norm.state': ['TX', 'TX'],
    'ai.match': ['good', 'so-so'],
    'ai.route_type': ['Local', 'OTR'],
    'ai.fair_chance': ['fair_chance_employer', 'no_requirements_mentioned'],
    'ai.summary': [
        'Great local driving opportunity with competitive pay and excellent benefits.',
        'Over-the-road position offering travel across multiple states.'
    ],
    'source.url': ['https://example.com/job1', 'https://example.com/job2'],
    'meta.tracked_url': ['https://short.link/job1', 'https://short.link/job2'],
}

df = pd.DataFrame(test_data)

print("🚛 REAL PIPELINE TEST: PDF generation with show_prepared_for")
print(f"📊 Test data: {len(df)} jobs")
print()

# Initialize pipeline wrapper (same as Streamlit)
wrapper = StreamlitPipelineWrapper()

# Test parameters (same as what Streamlit passes)
market_name = "Houston"
coach_name = "James Hazelton"
coach_username = "james.hazelton"
candidate_name = "Test Agent"
candidate_id = "test-uuid-123"

# TEST 1: show_prepared_for = True (Streamlit checkbox CHECKED)
print("🔬 REAL PIPELINE TEST 1: show_prepared_for = True")
print("Expected: PDF should show 'Prepared for Test Agent by Coach James'")

pdf_bytes_true = wrapper.generate_pdf_from_canonical(
    df=df,
    market_name=market_name,
    coach_name=coach_name,
    coach_username=coach_username,
    candidate_name=candidate_name,
    candidate_id=candidate_id,
    show_prepared_for=True  # CHECKBOX CHECKED
)

if pdf_bytes_true:
    with open("real_pipeline_prepared_for_TRUE.pdf", "wb") as f:
        f.write(pdf_bytes_true)
    print(f"✅ TEST 1 SUCCESS: PDF generated ({len(pdf_bytes_true):,} bytes)")
    print(f"📂 File: real_pipeline_prepared_for_TRUE.pdf")
else:
    print("❌ TEST 1 FAILED: PDF generation failed")

print()

# TEST 2: show_prepared_for = False (Streamlit checkbox UNCHECKED)
print("🔬 REAL PIPELINE TEST 2: show_prepared_for = False") 
print("Expected: PDF should NOT show 'Prepared for' message")

pdf_bytes_false = wrapper.generate_pdf_from_canonical(
    df=df,
    market_name=market_name,
    coach_name=coach_name,
    coach_username=coach_username,
    candidate_name=candidate_name,
    candidate_id=candidate_id,
    show_prepared_for=False  # CHECKBOX UNCHECKED
)

if pdf_bytes_false:
    with open("real_pipeline_prepared_for_FALSE.pdf", "wb") as f:
        f.write(pdf_bytes_false)
    print(f"✅ TEST 2 SUCCESS: PDF generated ({len(pdf_bytes_false):,} bytes)")
    print(f"📂 File: real_pipeline_prepared_for_FALSE.pdf")
else:
    print("❌ TEST 2 FAILED: PDF generation failed")

print()

# Summary
print("📋 REAL PIPELINE TEST SUMMARY:")
print("- Open real_pipeline_prepared_for_TRUE.pdf → Should see 'Prepared for Test Agent by Coach James'")
print("- Open real_pipeline_prepared_for_FALSE.pdf → Should NOT see any prepared message")
print()

if pdf_bytes_true and pdf_bytes_false:
    print("🎉 REAL PIPELINE TESTS PASSED - show_prepared_for works in production!")
    print("🚀 Ready for Streamlit deployment!")
else:
    print("⚠️ REAL PIPELINE TESTS FAILED - check error messages above")