#!/usr/bin/env python3
"""
Deep dive into ALL available job data from DriverPulse
"""

import json
from driver_pulse_source import DriverPulseSource, DriverPulseConfig

# Create a simple config
config = DriverPulseConfig(
    search_text="CDL driver",
    location="Dallas, TX",
    max_companies=5  # Just 5 companies for deep analysis
)

source = DriverPulseSource(config)

# Load authentication
print("🔐 Loading authentication...")
source.load_authentication()

# Run a search to get raw company data
print("🔍 Searching companies...")
search_results = source.search_companies()

if not search_results or not search_results.get('response'):
    print("❌ No results")
    exit(1)

companies = search_results['response']

print(f"\n🔬 DEEP ANALYSIS - First 5 Companies")
print("=" * 100)

analyzed_companies = []

for company_id, company_data in companies.items():
    if company_id in ['default_companies_selected', 'has_results', 'result_count']:
        continue

    if len(analyzed_companies) >= 5:
        break

    company_name = company_data.get('company_name', 'Unknown')

    print(f"\n{'='*100}")
    print(f"COMPANY: {company_name} (ID: {company_id})")
    print(f"{'='*100}")

    # 1. Show ALL company-level data
    print(f"\n📦 COMPANY-LEVEL DATA (from search_carriers response):")
    print("-" * 100)
    for key, value in company_data.items():
        if key == 'highlighted_content':
            print(f"  {key}: [{len(value)} items - shown separately below]")
        elif isinstance(value, str) and len(value) > 200:
            print(f"  {key}: {value[:200]}...")
        else:
            print(f"  {key}: {value}")

    # 2. Get detailed company info
    print(f"\n🔍 FETCHING DETAILED COMPANY INFO (get_search_detail_info)...")
    print("-" * 100)
    company_details = source.get_company_details(company_id)

    if company_details:
        print(f"✅ Got detailed company info with {len(company_details)} fields:")
        for key, value in company_details.items():
            if isinstance(value, str) and len(value) > 200:
                print(f"  {key}: {value[:200]}...")
            elif isinstance(value, dict):
                print(f"  {key}: {{dict with {len(value)} keys}}")
            elif isinstance(value, list):
                print(f"  {key}: [list with {len(value)} items]")
            else:
                print(f"  {key}: {value}")
    else:
        print(f"❌ No detailed company info available")

    # 3. Analyze highlighted_content (job listings)
    highlighted = company_data.get('highlighted_content', [])

    print(f"\n💼 JOB LISTINGS ({len(highlighted)} jobs in highlighted_content):")
    print("-" * 100)

    for i, job in enumerate(highlighted[:3], 1):  # Show first 3 jobs
        print(f"\n  JOB #{i}:")
        for key, value in job.items():
            if isinstance(value, str) and len(value) > 150:
                print(f"    {key}: {value[:150]}...")
            else:
                print(f"    {key}: {value}")

    if len(highlighted) > 3:
        print(f"\n  ... and {len(highlighted) - 3} more jobs")

    # Store for JSON output
    analyzed_companies.append({
        'company_id': company_id,
        'company_name': company_name,
        'search_data': company_data,
        'detail_data': company_details,
        'job_count': len(highlighted)
    })

# Save full analysis
with open('full_driverpulse_data_analysis.json', 'w') as f:
    json.dump(analyzed_companies, f, indent=2)

print(f"\n\n💾 Full analysis saved to: full_driverpulse_data_analysis.json")

print(f"\n\n📊 SUMMARY OF AVAILABLE DATA:")
print("=" * 100)
print(f"\n1️⃣  SEARCH-LEVEL DATA (search_carriers API):")
print(f"   - company_id")
print(f"   - company_name")
print(f"   - logo_link")
print(f"   - url_part (for application links)")
print(f"   - highlighted_content (array of job matches)")

if analyzed_companies and analyzed_companies[0].get('detail_data'):
    print(f"\n2️⃣  DETAIL-LEVEL DATA (get_search_detail_info API):")
    detail_keys = list(analyzed_companies[0]['detail_data'].keys()) if analyzed_companies[0]['detail_data'] else []
    for key in detail_keys:
        print(f"   - {key}")

print(f"\n3️⃣  JOB-LEVEL DATA (within highlighted_content):")
if analyzed_companies and analyzed_companies[0]['search_data'].get('highlighted_content'):
    job = analyzed_companies[0]['search_data']['highlighted_content'][0]
    for key in job.keys():
        print(f"   - {key}")
