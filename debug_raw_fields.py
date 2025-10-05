#!/usr/bin/env python3
"""
Quick debug - print ALL fields from DriverPulse API response
"""
from driver_pulse_source import DriverPulseSource, DriverPulseConfig
import json

config = DriverPulseConfig(
    search_text="CDL",
    location="Dallas, TX",
    max_companies=2,
    max_jobs_per_company=2
)

source = DriverPulseSource(config)
source.load_authentication()

print("🔍 Fetching raw API response...")
result = source.search_companies()

if result and result.get('response'):
    companies = result['response']

    # Get first real company (not metadata)
    for company_id, company_data in companies.items():
        if company_id in ['default_companies_selected', 'has_results', 'result_count']:
            continue

        print(f"\n{'='*60}")
        print(f"COMPANY: {company_data.get('company_name')}")
        print(f"{'='*60}")
        print(f"\nALL COMPANY FIELDS:")
        for key in sorted(company_data.keys()):
            value = company_data[key]
            if isinstance(value, (str, int, float, bool)):
                print(f"  {key}: {value}")
            elif isinstance(value, list):
                print(f"  {key}: [list with {len(value)} items]")
            elif isinstance(value, dict):
                print(f"  {key}: {{dict with {len(value)} keys}}")

        # Get company details
        company_details = source.get_company_details(company_id)
        if company_details:
            print(f"\n{'='*60}")
            print(f"COMPANY DETAILS FIELDS")
            print(f"{'='*60}")
            for key in sorted(company_details.keys()):
                value = company_details[key]
                if isinstance(value, (str, int, float, bool)):
                    display = str(value)[:100] + "..." if len(str(value)) > 100 else value
                    print(f"  {key}: {display}")
                elif isinstance(value, list):
                    print(f"  {key}: [list with {len(value)} items]")
                elif isinstance(value, dict):
                    print(f"  {key}: {{dict with {len(value)} keys}}")

        # Now look at highlighted_content jobs
        jobs = company_data.get('highlighted_content', [])
        if jobs:
            print(f"\n{'='*60}")
            print(f"JOB FIELDS (highlighted_content)")
            print(f"{'='*60}")
            first_job = jobs[0]
            print(f"\nALL JOB FIELDS:")
            for key in sorted(first_job.keys()):
                value = first_job[key]
                if isinstance(value, str):
                    display = value[:100] + "..." if len(value) > 100 else value
                    print(f"  {key}: {display}")
                else:
                    print(f"  {key}: {value}")

            print(f"\n{'='*60}")
            print("FULL RAW JOB OBJECT:")
            print(f"{'='*60}")
            print(json.dumps(first_job, indent=2))

        break  # Just show first company
else:
    print("❌ No results")
