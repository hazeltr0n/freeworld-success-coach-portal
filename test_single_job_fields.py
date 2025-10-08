#!/usr/bin/env python3
"""Test to see actual fields in ONE DriverPulse job"""

from driver_pulse_source import DriverPulseSource
import json

# Create source and load auth
source = DriverPulseSource()
source.load_authentication()

# Get first page of companies
print('🔍 Searching for companies...')
result = source.search_companies('CDL driver', page_number=1)

if not result or not result.get('response'):
    print('❌ No companies found')
    exit(1)

companies = result['response']

# Get FIRST job from FIRST company
for company_id, company_data in companies.items():
    if company_id in ['has_results', 'result_count', 'default_companies_selected']:
        continue

    print(f'\n📦 Company: {company_data.get("company_name")}')
    print(f'   Company ID: {company_id}')

    # Get highlighted jobs
    highlighted = company_data.get('highlighted_content', [])
    if not highlighted:
        continue

    # Get first job
    first_job = highlighted[0]
    job_id = first_job.get('job_id')

    print(f'\n🔍 Fetching job ID: {job_id}')

    # Call API directly
    full_job_response = source._call_api("get_carrier_active_job_detail", {
        "company_id": company_id,
        "active_job_id": job_id,
        "user_timezone": "America/Chicago"
    })

    if full_job_response and full_job_response.get('response'):
        job_data = full_job_response['response'][0]

        print('\n' + '='*80)
        print('ALL FIELDS IN RAW API RESPONSE')
        print('='*80)

        for key in sorted(job_data.keys()):
            value = job_data[key]
            if isinstance(value, str) and len(value) > 100:
                preview = value[:100] + '...'
            else:
                preview = str(value)
            print(f'{key}: {preview}')

        # Check specific fields we care about
        print('\n' + '='*80)
        print('KEY FIELDS CHECK')
        print('='*80)
        print(f"Has 'job_title': {'job_title' in job_data}")
        print(f"Has 'job_description': {'job_description' in job_data}")
        print(f"Has 'job_requirements': {'job_requirements' in job_data}")
        print(f"Has 'job_general_benefits': {'job_general_benefits' in job_data}")
        print(f"Has 'job_min_pay': {'job_min_pay' in job_data}")
        print(f"Has 'zip': {'zip' in job_data}")
        print(f"Has 'state': {'state' in job_data}")

        # Show actual values
        print('\n' + '='*80)
        print('ACTUAL FIELD VALUES')
        print('='*80)
        print(f"job_title: {job_data.get('job_title', 'MISSING')}")
        print(f"company_name: {job_data.get('company_name', 'MISSING')}")
        print(f"zip: {job_data.get('zip', 'MISSING')}")
        print(f"state: {job_data.get('state', 'MISSING')}")
        print(f"job_min_pay: {job_data.get('job_min_pay', 'MISSING')}")
        print(f"job_max_pay: {job_data.get('job_max_pay', 'MISSING')}")

    break
