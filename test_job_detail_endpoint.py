#!/usr/bin/env python3
"""
Test if we can get full job details using job_id
"""

import json
import requests
from driver_pulse_source import DriverPulseSource, DriverPulseConfig

# Create source and authenticate
config = DriverPulseConfig(search_text="CDL driver", location="Dallas, TX", max_companies=3)
source = DriverPulseSource(config)

print("🔐 Loading authentication...")
source.load_authentication()

# Get some jobs first
print("🔍 Getting sample jobs...")
search_results = source.search_companies()
companies = search_results['response']

# Collect some job IDs
test_jobs = []
for company_id, company_data in companies.items():
    if company_id in ['default_companies_selected', 'has_results', 'result_count']:
        continue

    highlighted = company_data.get('highlighted_content', [])
    for job in highlighted[:2]:  # Take first 2 jobs per company
        test_jobs.append({
            'job_id': job.get('job_id'),
            'job_title': job.get('job_title'),
            'company_name': company_data.get('company_name'),
            'company_id': company_id
        })

    if len(test_jobs) >= 5:
        break

print(f"\n📋 Testing {len(test_jobs)} different job detail API calls:")
print("=" * 100)

# Try different API endpoints to get job details
test_functions = [
    "get_job_details",
    "get_job_info",
    "job_details",
    "get_posting_details",
    "get_job_posting",
    "get_pulse_match_posting",
    "get_pulse_match_posting_info",
    "get_job_description",
    "job_info"
]

for i, job in enumerate(test_jobs[:3], 1):  # Test first 3 jobs
    print(f"\n{'='*100}")
    print(f"JOB {i}: {job['job_title']} (ID: {job['job_id']}) at {job['company_name']}")
    print(f"{'='*100}")

    for misc_function in test_functions:
        print(f"\n  Testing: {misc_function}")

        # Try different parameter formats
        param_variations = [
            {"job_id": job['job_id']},
            {"posting_id": job['job_id']},
            {"pulse_match_posting_id": job['job_id']},
            {"result_info[job_id]": job['job_id']},
            {"result_info[posting_id]": job['job_id']},
            {"result_info[company_id]": job['company_id'], "result_info[job_id]": job['job_id']},
        ]

        for params in param_variations:
            try:
                result = source._call_api(misc_function, params)

                if result and result.get('response'):
                    print(f"    ✅ SUCCESS with params: {params}")
                    print(f"    Response keys: {list(result['response'].keys()) if isinstance(result['response'], dict) else 'not a dict'}")

                    # Save successful response
                    with open(f'job_detail_{job["job_id"]}_{misc_function}.json', 'w') as f:
                        json.dump(result, f, indent=2)

                    print(f"    💾 Saved to: job_detail_{job['job_id']}_{misc_function}.json")

                    # Show first 500 chars of response
                    response_str = json.dumps(result['response'], indent=2)
                    print(f"    Preview: {response_str[:500]}")
                    break  # Found working params for this function

            except Exception as e:
                continue  # Silently try next variation

print(f"\n\n{'='*100}")
print("📊 SUMMARY")
print(f"{'='*100}")
print("\nSuccessful API calls have been saved as JSON files.")
print("Check for job_detail_*.json files in the current directory.")

# Also try to see if there's a job listing URL we can construct
print(f"\n\n🔗 Testing Direct Job URLs:")
print("=" * 100)

for job in test_jobs[:3]:
    company_data = None
    for cid, cdata in companies.items():
        if cid == job['company_id']:
            company_data = cdata
            break

    if company_data:
        url_part = company_data.get('url_part')

        # Test different URL patterns
        possible_urls = [
            f"https://intelliapp.driverapponline.com/c/{url_part}?job={job['job_id']}",
            f"https://intelliapp.driverapponline.com/c/{url_part}/job/{job['job_id']}",
            f"https://intelliapp.driverapponline.com/job/{job['job_id']}",
            f"https://pulse.tenstreet.com/job/{job['job_id']}",
            f"https://pulse.tenstreet.com/posting/{job['job_id']}",
        ]

        print(f"\n{job['job_title']} at {job['company_name']}:")
        print(f"  Possible URLs to test manually:")
        for url in possible_urls:
            print(f"    - {url}")
