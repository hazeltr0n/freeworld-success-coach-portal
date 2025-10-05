#!/usr/bin/env python3
"""
DriverPulse Scraper V2 - Actually gets FULL job data
Uses the get_carrier_active_job_detail endpoint discovered through network sniffing
"""

import json
import time
from datetime import datetime
from typing import List, Dict
from driver_pulse_source import DriverPulseSource, DriverPulseConfig

class DriverPulseScraper:
    """Scraper that gets FULL job details, not just snippets"""

    def __init__(self):
        self.source = None

    def authenticate(self):
        """Load authentication"""
        config = DriverPulseConfig(search_text="CDL", location="Dallas, TX", max_companies=1)
        self.source = DriverPulseSource(config)
        self.source.load_authentication()
        print("✅ Authenticated")

    def search_companies(self, search_term: str, max_companies: int = 100) -> Dict:
        """Search for companies - returns company list with job IDs in highlighted_content"""
        search_params = {
            "search_text": search_term,
            "page_number": 1,
            "portal_user_id": self.source.user_id,
            "user_timezone": "America/Chicago"
        }

        print(f"🔍 Searching for: '{search_term}'")
        result = self.source._call_api("search_carriers", search_params)

        if result and result.get('response'):
            companies = result['response']
            # Filter out metadata
            company_list = {k: v for k, v in companies.items()
                          if k not in ['default_companies_selected', 'has_results', 'result_count']}
            print(f"✅ Found {len(company_list)} companies")
            return company_list
        else:
            print("❌ Search failed")
            return {}

    def get_full_job_details(self, company_id: str, job_id: str) -> Dict:
        """
        Get FULL job details using the get_carrier_active_job_detail endpoint
        This gives us: description, requirements, benefits, salary, location, etc.
        """
        detail_params = {
            "company_id": company_id,
            "active_job_id": job_id,
            "user_timezone": "America/Chicago"
        }

        result = self.source._call_api("get_carrier_active_job_detail", detail_params)

        if result and result.get('response') and len(result['response']) > 0:
            return result['response'][0]  # Returns full job object
        else:
            return None

    def scrape_all_jobs(self, search_term: str = "CDL driver", max_companies: int = 50) -> List[Dict]:
        """
        Main scraping method - gets FULL data for all jobs

        Workflow:
        1. Search companies → get job IDs from highlighted_content
        2. For each job ID → call get_carrier_active_job_detail
        3. Return complete job data
        """
        if not self.source:
            self.authenticate()

        # Step 1: Search for companies
        companies = self.search_companies(search_term, max_companies)

        all_jobs = []
        total_jobs = 0

        # Count total jobs first
        for company_id, company_data in list(companies.items())[:max_companies]:
            highlighted = company_data.get('highlighted_content', [])
            total_jobs += len(highlighted)

        print(f"\n📊 Found {total_jobs} total jobs across {min(len(companies), max_companies)} companies")
        print(f"🔄 Fetching full details for each job...\n")

        processed = 0

        # Step 2: For each company, get full details for each job
        for company_id, company_data in list(companies.items())[:max_companies]:
            company_name = company_data.get('company_name', 'Unknown')
            highlighted = company_data.get('highlighted_content', [])

            if not highlighted:
                continue

            print(f"🏢 {company_name} ({len(highlighted)} jobs)")

            for job_snippet in highlighted:
                job_id = job_snippet.get('job_id')
                if not job_id:
                    continue

                processed += 1

                # Get FULL job details
                full_job = self.get_full_job_details(company_id, job_id)

                if full_job:
                    # Merge with company data
                    full_job['company_id'] = company_id
                    full_job['company_name'] = company_name
                    full_job['company_logo'] = company_data.get('logo_link')
                    full_job['company_url_part'] = company_data.get('url_part')
                    full_job['scraped_at'] = datetime.now().isoformat()
                    full_job['search_term'] = search_term

                    all_jobs.append(full_job)
                    print(f"   ✅ {processed}/{total_jobs}: {full_job.get('job_title', 'Unknown')[:50]}")
                else:
                    print(f"   ⚠️  {processed}/{total_jobs}: Could not fetch job {job_id}")

                # Rate limiting
                time.sleep(0.3)

        print(f"\n✅ Scraped {len(all_jobs)} complete jobs!")
        return all_jobs


if __name__ == "__main__":
    print("🚀 DriverPulse Scraper V2 - Full Job Data")
    print("=" * 80)

    scraper = DriverPulseScraper()
    scraper.authenticate()

    # Scrape jobs
    jobs = scraper.scrape_all_jobs(
        search_term="CDL driver",
        max_companies=10  # Start small to test
    )

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"driver_pulse_full_jobs_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(jobs, f, indent=2)

    print(f"\n💾 Saved {len(jobs)} jobs to: {output_file}")

    # Show sample
    if jobs:
        print("\n📋 Sample Job:")
        print("=" * 80)
        sample = jobs[0]
        print(f"Title: {sample.get('job_title')}")
        print(f"Company: {sample.get('company_name')}")
        print(f"Pay: ${sample.get('job_min_pay')} - ${sample.get('job_max_pay')} {sample.get('job_min_max_pay_unit', '')}")
        print(f"Location: {sample.get('state')}")
        print(f"Description: {sample.get('job_description', '')[:200]}...")
        print(f"Requirements: {sample.get('job_requirements', '')[:200]}...")
        print(f"Benefits: {sample.get('job_general_benefits', '')[:200]}...")
