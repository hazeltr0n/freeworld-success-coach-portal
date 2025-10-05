#!/usr/bin/env python3
"""
Test script to reverse engineer DriverPulse API parameters
"""

import os
import json
from driver_pulse_source import DriverPulseSource, DriverPulseConfig

def test_api_parameters():
    """Test different API parameter combinations to see what's supported"""

    print("🔍 DriverPulse API Parameter Discovery")
    print("=" * 60)

    # Load authentication
    source = DriverPulseSource()

    try:
        source.load_authentication()
        print("✅ Authentication loaded\n")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return

    # Test 1: Baseline search with just search_text
    print("\n" + "=" * 60)
    print("TEST 1: Baseline - Just search_text")
    print("=" * 60)

    baseline_params = {
        "search_text": "CDL driver",
        "page_number": 1,
        "portal_user_id": source.user_id,
        "user_timezone": "America/Chicago"
    }

    print(f"Parameters: {json.dumps(baseline_params, indent=2)}")
    result1 = source._call_api("search_carriers", baseline_params)

    if result1 and result1.get('response'):
        print(f"✅ Found {len(result1['response'])} companies")
        # Show first company for debugging
        first_company = next(iter(result1['response'].values()))
        print(f"Sample company: {first_company.get('company_name', 'Unknown')}")
    else:
        print(f"❌ Search failed")

    # Test 2: Add experience_level parameter
    print("\n" + "=" * 60)
    print("TEST 2: Adding experience_level='new'")
    print("=" * 60)

    exp_level_params = {
        "search_text": "CDL driver",
        "page_number": 1,
        "portal_user_id": source.user_id,
        "user_timezone": "America/Chicago",
        "experience_level": "new"
    }

    print(f"Parameters: {json.dumps(exp_level_params, indent=2)}")
    result2 = source._call_api("search_carriers", exp_level_params)

    if result2 and result2.get('response'):
        print(f"✅ Found {len(result2['response'])} companies")
        print(f"Compare: Baseline had {len(result1['response']) if result1 else 0}, with filter has {len(result2['response'])}")
    else:
        print(f"❌ Search failed")

    # Test 3: Try different experience_level values
    print("\n" + "=" * 60)
    print("TEST 3: Testing different experience_level values")
    print("=" * 60)

    for exp_value in ["new", "entry", "experienced", "veteran", "0", "1", "2"]:
        test_params = {
            "search_text": "CDL driver",
            "page_number": 1,
            "portal_user_id": source.user_id,
            "user_timezone": "America/Chicago",
            "experience_level": exp_value
        }

        result = source._call_api("search_carriers", test_params)
        count = len(result['response']) if result and result.get('response') else 0
        print(f"  experience_level='{exp_value}': {count} companies")

    # Test 4: Try other potential filter parameters
    print("\n" + "=" * 60)
    print("TEST 4: Testing other potential filter parameters")
    print("=" * 60)

    other_params_tests = [
        {"route_type": "local"},
        {"home_time": "daily"},
        {"cdl_required": "false"},
        {"cdl_required": "0"},
        {"training_provided": "true"},
        {"training_provided": "1"},
        {"no_experience": "true"},
        {"no_experience": "1"},
        {"entry_level": "true"},
        {"entry_level": "1"},
    ]

    for extra_params in other_params_tests:
        test_params = {
            "search_text": "CDL driver",
            "page_number": 1,
            "portal_user_id": source.user_id,
            "user_timezone": "America/Chicago",
            **extra_params
        }

        result = source._call_api("search_carriers", test_params)
        count = len(result['response']) if result and result.get('response') else 0
        param_str = json.dumps(extra_params)
        print(f"  {param_str}: {count} companies")

    # Test 5: Inspect the actual response structure
    print("\n" + "=" * 60)
    print("TEST 5: Inspecting response structure for filter hints")
    print("=" * 60)

    if result1 and result1.get('response'):
        # Get a company with jobs
        for company_id, company_data in result1['response'].items():
            if company_id not in ['default_companies_selected', 'has_results', 'result_count']:
                print(f"\nCompany ID: {company_id}")
                print(f"Company Name: {company_data.get('company_name', 'Unknown')}")
                print(f"Keys in company data: {list(company_data.keys())[:20]}")

                # Look for any experience-related fields
                exp_fields = {k: v for k, v in company_data.items()
                             if 'exp' in k.lower() or 'level' in k.lower() or 'training' in k.lower()}
                if exp_fields:
                    print(f"Experience-related fields: {exp_fields}")

                # Check highlighted_content
                if company_data.get('highlighted_content'):
                    print(f"Has {len(company_data['highlighted_content'])} highlighted jobs")
                    first_job = company_data['highlighted_content'][0]
                    print(f"First job keys: {list(first_job.keys())}")

                break

    print("\n" + "=" * 60)
    print("🎯 CONCLUSION")
    print("=" * 60)
    print("Review the results above to determine:")
    print("1. Does experience_level parameter affect results?")
    print("2. Which parameter names actually work?")
    print("3. What are the valid values for each parameter?")
    print("4. Are there experience indicators in the response data we can filter on?")

if __name__ == "__main__":
    test_api_parameters()
