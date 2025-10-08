#!/usr/bin/env python3
"""Debug script to examine ONE actual DriverPulse job"""

from driver_pulse_source import DriverPulseSource
import json

# Create source
source = DriverPulseSource()

# Get first page of companies
companies = source.search_companies('CDL driver')
print(f'✅ Found {len(companies)} companies')

# Get FIRST job from FIRST company
for company_id, company_data in list(companies.items())[:1]:
    print(f'\n📦 Company: {company_data.get("company_name")}')

    for job in company_data.get('jobs', [])[:1]:
        job_id = job.get('active_job_id')
        print(f'🔍 Fetching job ID: {job_id}')

        detail = source.get_job_detail(company_id, job_id, company_data)
        if detail:
            print('\n=== ALL FIELDS IN JOB DETAIL ===')
            for key, value in sorted(detail.items()):
                if isinstance(value, str):
                    preview = value[:100] if len(value) > 100 else value
                else:
                    preview = str(value)[:100]
                print(f'{key}: {preview}')
            break
    break
