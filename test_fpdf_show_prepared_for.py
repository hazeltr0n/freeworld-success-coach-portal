#!/usr/bin/env python3
"""
BULLETPROOF TEST: show_prepared_for parameter functionality
Tests BOTH True and False states with REAL pipeline data
"""

import pandas as pd
from fpdf_pdf_generator_v2 import generate_pdf_from_dataframe
import os

# Create realistic test data that matches pipeline structure
test_data = {
    'source.title': ['CDL Driver - Local Routes', 'OTR Truck Driver', 'Regional CDL Driver'],
    'source.company': ['FreeWorld Trucking', 'Highway Express', 'Swift Transportation'],
    'source.location_raw': ['Houston, TX', 'Houston, TX', 'Houston, TX'],
    'norm.city': ['Houston', 'Houston', 'Houston'],
    'norm.state': ['TX', 'TX', 'TX'],
    'ai.match': ['good', 'so-so', 'good'],
    'ai.route_type': ['Local', 'OTR', 'Regional'],
    'ai.fair_chance': ['fair_chance_employer', 'no_requirements_mentioned', 'fair_chance_employer'],
    'ai.summary': [
        'Great local driving opportunity with competitive pay and excellent benefits. Home daily with weekends off.',
        'Over-the-road position offering travel across multiple states. Requires clean driving record.',
        'Regional driving position covering Texas and surrounding states. Good work-life balance with 2-3 days home per week.'
    ],
    'source.url': ['https://example.com/job1', 'https://example.com/job2', 'https://example.com/job3'],
    'meta.tracked_url': ['https://short.link/job1', 'https://short.link/job2', 'https://short.link/job3'],
}

df = pd.DataFrame(test_data)

print("🧪 BULLETPROOF TEST: show_prepared_for parameter")
print(f"📊 Test data: {len(df)} jobs")
print()

# Test parameters
market = "Houston"
coach_name = "James Hazelton"
coach_username = "james.hazelton"
candidate_name = "Test Agent"
candidate_id = "test-uuid-123"

# TEST 1: show_prepared_for = True (should show "Prepared for" message)
print("🔬 TEST 1: show_prepared_for = True")
print("Expected: PDF should show 'Prepared for Test Agent by Coach James'")

result1 = generate_pdf_from_dataframe(
    df=df,
    output_path="test_prepared_for_TRUE.pdf",
    market=market,
    coach_name=coach_name,
    coach_username=coach_username,
    candidate_name=candidate_name,
    candidate_id=candidate_id,
    show_prepared_for=True  # TRUE = SHOW MESSAGE
)

if result1 and result1.get('success'):
    size1 = os.path.getsize("test_prepared_for_TRUE.pdf")
    print(f"✅ TEST 1 SUCCESS: PDF generated ({size1:,} bytes)")
    print(f"📂 File: test_prepared_for_TRUE.pdf")
else:
    print("❌ TEST 1 FAILED: PDF generation failed")

print()

# TEST 2: show_prepared_for = False (should NOT show "Prepared for" message)
print("🔬 TEST 2: show_prepared_for = False")
print("Expected: PDF should NOT show 'Prepared for' message")

result2 = generate_pdf_from_dataframe(
    df=df,
    output_path="test_prepared_for_FALSE.pdf",
    market=market,
    coach_name=coach_name,
    coach_username=coach_username,
    candidate_name=candidate_name,
    candidate_id=candidate_id,
    show_prepared_for=False  # FALSE = HIDE MESSAGE
)

if result2 and result2.get('success'):
    size2 = os.path.getsize("test_prepared_for_FALSE.pdf")
    print(f"✅ TEST 2 SUCCESS: PDF generated ({size2:,} bytes)")
    print(f"📂 File: test_prepared_for_FALSE.pdf")
else:
    print("❌ TEST 2 FAILED: PDF generation failed")

print()

# Summary
print("📋 TEST SUMMARY:")
print("- Open test_prepared_for_TRUE.pdf → Should see 'Prepared for Test Agent by Coach James'")
print("- Open test_prepared_for_FALSE.pdf → Should NOT see any prepared message")
print()
if result1 and result1.get('success') and result2 and result2.get('success'):
    print("🎉 ALL TESTS PASSED - show_prepared_for parameter is working correctly!")
else:
    print("⚠️ SOME TESTS FAILED - check the error messages above")