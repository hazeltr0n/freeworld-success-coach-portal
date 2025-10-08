#!/usr/bin/env python3
"""
Test script to fetch raw DriverPulse data and save to CSV
Shows exact field names and values from DriverPulse API
"""

import pandas as pd
from datetime import datetime
from driver_pulse_source import DriverPulseSource, DriverPulseConfig
import streamlit as st

def test_driver_pulse_raw():
    """Fetch DriverPulse jobs and save raw API response to CSV"""

    # Load credentials from Streamlit secrets
    email = st.secrets.get('DRIVER_PULSE_EMAIL')
    first_name = st.secrets.get('DRIVER_PULSE_FIRST_NAME')
    last_name = st.secrets.get('DRIVER_PULSE_LAST_NAME')
    phone = st.secrets.get('DRIVER_PULSE_PHONE')

    if not all([email, first_name, last_name, phone]):
        print("❌ Missing DriverPulse credentials in secrets")
        return

    print("🔐 Authenticating with DriverPulse...")
    config = DriverPulseConfig(search_text="CDL Driver", location="", max_companies=5)
    source = DriverPulseSource(config)

    # Create authentication
    success = source.create_new_authentication(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone
    )

    if not success:
        print("❌ Authentication failed")
        return

    print("✅ Authentication successful")
    print("🔍 Fetching companies...")

    # Paginate through ALL companies
    print("🔍 Paginating through ALL companies...")
    all_companies = {}
    page_num = 1
    max_pages = 13  # DriverPulse API limit

    while page_num <= max_pages:
        result = source.search_companies(search_text="CDL Driver", page_number=page_num)

        if not result or 'response' not in result:
            print(f"   ❌ Page {page_num} failed")
            break

        companies = result['response']
        company_ids = [k for k in companies.keys()
                      if k not in ['default_companies_selected', 'has_results', 'result_count']]

        if not company_ids:
            print(f"   ✅ Reached end at page {page_num}")
            break

        for company_id in company_ids:
            all_companies[company_id] = companies[company_id]

        print(f"   Page {page_num}: +{len(company_ids)} companies (total: {len(all_companies)})")

        has_more = companies.get('has_results', True)
        if not has_more:
            break

        page_num += 1

    print(f"\n✅ Found {len(all_companies)} total companies")

    # Fetch ALL job details (parallel)
    from concurrent.futures import ThreadPoolExecutor, as_completed

    all_jobs = []
    total_job_ids = sum(len(c.get('highlighted_content', [])) for c in all_companies.values())

    print(f"📊 Fetching full details for {total_job_ids} jobs (20 workers in parallel)...")

    def fetch_job_detail(job_info):
        company_id, company_data, job_snippet = job_info
        job_id = job_snippet.get('job_id')
        if not job_id:
            return None

        detail_params = {
            "company_id": company_id,
            "active_job_id": job_id,
            "user_timezone": "America/Chicago"
        }

        result = source._call_api("get_carrier_active_job_detail", detail_params)

        if result and result.get('response') and len(result['response']) > 0:
            full_job = result['response'][0]
            full_job['company_id'] = company_id
            full_job['company_name'] = company_data.get('company_name', 'Unknown')
            full_job['company_logo'] = company_data.get('logo_link')
            full_job['company_url_part'] = company_data.get('url_part')
            return full_job
        return None

    # Build list of jobs to fetch
    jobs_to_fetch = []
    for company_id, company_data in all_companies.items():
        highlighted = company_data.get('highlighted_content', [])
        for job_snippet in highlighted:
            jobs_to_fetch.append((company_id, company_data, job_snippet))

    # Parallel fetch with progress
    processed = 0
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_job_detail, job_info): job_info for job_info in jobs_to_fetch}

        for future in as_completed(futures):
            processed += 1
            job = future.result()
            if job:
                all_jobs.append(job)

            if processed % 100 == 0:
                print(f"   {processed}/{total_job_ids} jobs fetched...", flush=True)

    print(f"\n✅ Fetched {len(all_jobs)} complete jobs")

    if not all_jobs:
        print("❌ No jobs fetched")
        return

    # Convert to DataFrame with ALL fields from DriverPulse
    df = pd.DataFrame(all_jobs)

    # Save to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"driver_pulse_raw_data_{timestamp}.csv"
    df.to_csv(filename, index=False)

    print(f"\n✅ Saved {len(df)} jobs to {filename}")
    print(f"\nColumns in CSV ({len(df.columns)}):")
    for col in sorted(df.columns):
        sample_val = df[col].iloc[0] if len(df) > 0 else ''
        if isinstance(sample_val, str) and len(sample_val) > 50:
            sample_val = sample_val[:50] + '...'
        print(f"  - {col}: {sample_val}")

    # Show ZIP code stats
    zip_count = df['zip'].notna().sum() if 'zip' in df.columns else 0
    print(f"\n📍 ZIP code population: {zip_count}/{len(df)}")

    if 'zip' in df.columns:
        print(f"\nSample ZIPs:")
        for i, zip_val in enumerate(df['zip'].head(10)):
            state = df['state'].iloc[i] if 'state' in df.columns else 'N/A'
            print(f"  {zip_val} ({state})")

if __name__ == "__main__":
    test_driver_pulse_raw()
