#!/usr/bin/env python3
"""
Test the updated DriverPulse adapter with real API data
"""
import json
from driver_pulse_adapter import DriverPulseToPipelineAdapter

# Load real DriverPulse data
print("📄 Loading DriverPulse API data...")
with open('driver_pulse_full_jobs_20251004_014039.json', 'r') as f:
    jobs = json.load(f)

print(f"✅ Loaded {len(jobs)} jobs")
print()

# Test the adapter
adapter = DriverPulseToPipelineAdapter()

# Convert first 3 jobs
test_jobs = jobs[:3]

print("🔄 Testing adapter conversion...")
print("=" * 80)
print()

outscraper_format = adapter._convert_to_outscraper_format(test_jobs)

for i, job in enumerate(outscraper_format, 1):
    print(f"📋 JOB {i}/{len(outscraper_format)}")
    print("-" * 80)
    print(f"Title: {job['title']}")
    print(f"Company: {job['company']}")
    print(f"Location: {job['formattedLocation']}")
    print(f"URL: {job['viewJobLink']}")
    print(f"Salary: {job['salarySnippet']}")
    print(f"Job ID: {job['job_id']}")
    print()
    print("Combined Description Preview:")
    print("-" * 80)
    snippet = job['snippet']
    # Show first 500 chars
    print(snippet[:500])
    if len(snippet) > 500:
        print(f"\n... ({len(snippet) - 500} more characters)")
    print()

    # Check for sections
    has_requirements = '<h3>Requirements</h3>' in snippet
    has_benefits = '<h3>Benefits</h3>' in snippet
    print(f"✅ Has Requirements section: {has_requirements}")
    print(f"✅ Has Benefits section: {has_benefits}")
    print()

    # Show metadata
    metadata = json.loads(job.get('company_metadata', '{}'))
    print("Company Metadata:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    print()
    print("=" * 80)
    print()

print("🎉 Adapter test complete!")
print()
print("📊 VALIDATION:")
print(f"✅ All {len(outscraper_format)} jobs have:")
print(f"  - title field: {all(j.get('title') for j in outscraper_format)}")
print(f"  - company field: {all(j.get('company') for j in outscraper_format)}")
print(f"  - snippet (combined): {all(j.get('snippet') for j in outscraper_format)}")
print(f"  - formattedLocation: {all(j.get('formattedLocation') for j in outscraper_format)}")
print(f"  - viewJobLink: {all(j.get('viewJobLink') for j in outscraper_format)}")
print(f"  - salarySnippet: {all(j.get('salarySnippet') for j in outscraper_format)}")
