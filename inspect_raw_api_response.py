#!/usr/bin/env python3
"""
Inspect RAW API response to see ALL fields returned by DriverPulse
"""

from driver_pulse_source import DriverPulseSource, DriverPulseConfig
import json

def inspect_raw_response():
    """Get raw API response and show all fields"""

    print("🔍 Inspecting RAW DriverPulse API Response")
    print("=" * 60)

    # Create source
    config = DriverPulseConfig(
        search_text="CDL",
        location="Dallas, TX",
        max_companies=2,
        max_jobs_per_company=1
    )

    source = DriverPulseSource(config)
    source.load_authentication()

    # Make raw API call
    print("\n📡 Calling search_carriers API...")
    raw_result = source.search_companies()

    if not raw_result or not raw_result.get('response'):
        print("❌ No results")
        return

    print(f"✅ Got response with {len(raw_result['response'])} items\n")

    # Get first company
    companies = raw_result['response']
    first_company_id = next((k for k in companies.keys() if k not in ['default_companies_selected', 'has_results', 'result_count']), None)

    if not first_company_id:
        print("❌ No companies found")
        return

    first_company = companies[first_company_id]

    print("=" * 60)
    print("COMPANY DATA STRUCTURE")
    print("=" * 60)
    print(f"Company ID: {first_company_id}")
    print(f"Company Name: {first_company.get('company_name', 'Unknown')}")
    print(f"\nAll Company Fields:")
    for key in sorted(first_company.keys()):
        value = first_company[key]
        if isinstance(value, (str, int, float, bool)):
            print(f"  {key}: {value}")
        elif isinstance(value, list):
            print(f"  {key}: [{len(value)} items]")
        elif isinstance(value, dict):
            print(f"  {key}: {{dict with {len(value)} keys}}")
        else:
            print(f"  {key}: {type(value).__name__}")

    # Check highlighted_content
    if first_company.get('highlighted_content'):
        print("\n" + "=" * 60)
        print("JOB DATA STRUCTURE (highlighted_content)")
        print("=" * 60)
        first_job = first_company['highlighted_content'][0]
        print(f"\nAll Job Fields:")
        for key in sorted(first_job.keys()):
            value = first_job[key]
            if isinstance(value, str):
                display = value[:100] + "..." if len(value) > 100 else value
                print(f"  {key}: {display}")
            else:
                print(f"  {key}: {value}")

    # Get company details to see if there are more fields
    print("\n" + "=" * 60)
    print("COMPANY DETAILS API")
    print("=" * 60)
    details = source.get_company_details(first_company_id)

    if details:
        print(f"\nAll Detail Fields:")
        for key in sorted(details.keys()):
            value = details[key]
            if isinstance(value, (str, int, float, bool)):
                display = str(value)[:100] + "..." if len(str(value)) > 100 else value
                print(f"  {key}: {display}")
            elif isinstance(value, list):
                print(f"  {key}: [{len(value)} items]")
                if value and isinstance(value[0], dict):
                    print(f"    First item keys: {list(value[0].keys())}")
            elif isinstance(value, dict):
                print(f"  {key}: {{dict with {len(value)} keys}}")
                print(f"    Keys: {list(value.keys())[:10]}")
            else:
                print(f"  {key}: {type(value).__name__}")

    # Save full response
    output = {
        'company_data': first_company,
        'company_details': details
    }

    with open('raw_driver_pulse_response.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Full response saved to raw_driver_pulse_response.json")

if __name__ == "__main__":
    inspect_raw_response()
