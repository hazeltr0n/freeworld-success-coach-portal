#!/usr/bin/env python3
"""
Fast Market Scraper - Authenticate once, pull all markets quickly
"""

import os
import csv
import json
import time
from datetime import datetime
from typing import List, Dict
from driver_pulse_source import DriverPulseSource, DriverPulseConfig

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class FastMarketScraper:
    """Fast scraper that authenticates once and pulls all markets quickly"""

    def __init__(self, target_locations=None):
        # Default target markets if none provided
        default_markets = [
            "Dallas, TX",
            "Houston, TX",
            "San Bernardino, CA",
            "Stockton, CA",
            "San Francisco, CA",
            "Phoenix, AZ",
            "Denver, CO",
            "Las Vegas, NV",
            "Newark, NJ",
            "Trenton, NJ"
        ]

        # Use provided locations or defaults
        if target_locations:
            self.markets = target_locations if isinstance(target_locations, list) else [target_locations]
        else:
            self.markets = default_markets

        # Entry-level search configurations
        self.experience_configs = {
            "no_cdl": {
                "search_text": "CDL training no experience new driver recent grad student",
                "experience_level": "new",
                "description": "No CDL Required - Training Provided"
            },
            "cdl_school": {
                "search_text": "CDL school graduate recent grad new driver training",
                "experience_level": "new",
                "description": "CDL School Graduates"
            },
            "0_6_months": {
                "search_text": "CDL 0-6 months new driver entry level recent experience",
                "experience_level": "entry",
                "description": "0-6 Months Experience"
            }
        }

    def scrape_all_markets_fast(self, radius_miles: int = 50) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Authenticate once, then quickly scrape all markets
        """
        print(f"🚀 Fast Market Scraper - All {len(self.markets)} Markets")
        print("=" * 60)
        print(f"🎯 Strategy: Fresh auth → Fast headless scraping")
        print(f"📍 Markets: {', '.join(self.markets)}")
        print(f"🔄 Radius: {radius_miles} miles per market")

        # Remove any cached auth to force fresh login (only affects local files, not secrets)
        auth_file = "auth.json"
        if os.path.exists(auth_file):
            os.remove(auth_file)
            print(f"🔄 Removed cached auth for fresh login")

        all_results = {}
        source = None

        # Step 1: Authenticate with first market (headed mode)
        print(f"\n🔐 STEP 1: Authenticating with headed browser...")

        first_config = DriverPulseConfig(
            search_text="CDL",  # Simple search for auth
            location=self.markets[0],
            radius_miles=radius_miles,
            max_companies=1,  # Just need to auth, not scrape yet
            max_jobs_per_company=1
        )

        source = DriverPulseSource(first_config)

        # Force authentication by calling ensure_authentication directly
        print(f"🧪 Testing authentication with {self.markets[0]}...")

        # Get credentials from environment
        credentials = {
            'email': os.getenv('DRIVER_PULSE_EMAIL'),
            'first_name': os.getenv('DRIVER_PULSE_FIRST_NAME'),
            'last_name': os.getenv('DRIVER_PULSE_LAST_NAME'),
            'phone': os.getenv('DRIVER_PULSE_PHONE')
        }

        # Force fresh authentication
        auth_success = source.ensure_authentication(
            email=credentials['email'],
            first_name=credentials['first_name'],
            last_name=credentials['last_name'],
            phone=credentials['phone']
        )

        if not auth_success:
            raise Exception("Authentication failed!")

        # Test with a small scrape
        test_jobs = source.scrape_jobs(limit=5)
        print(f"✅ Authentication successful! ({len(test_jobs)} test jobs found)")

        # Step 2: Now quickly scrape all markets with valid auth
        print(f"\n⚡ STEP 2: Fast headless scraping of all markets...")
        print(f"⏱️  Working quickly before auth expires...")

        start_time = time.time()

        for market_idx, market in enumerate(self.markets, 1):
            print(f"\n📍 Market {market_idx}/{len(self.markets)}: {market}")
            market_results = {}

            for exp_type, config in self.experience_configs.items():
                print(f"   🔍 {config['description'][:30]}...", end=" ")

                # Create config for this specific search
                market_config = DriverPulseConfig(
                    search_text=config['search_text'],
                    location=market,
                    radius_miles=radius_miles,
                    experience_level=config['experience_level'],
                    max_companies=100,
                    max_jobs_per_company=5
                )

                # Create new source with same auth
                market_source = DriverPulseSource(market_config)

                # Try to use existing auth
                try:
                    jobs = market_source.scrape_jobs(limit=500)

                    # Add metadata to jobs
                    for job in jobs:
                        job['experience_category'] = config['description']
                        job['search_keywords'] = config['search_text']
                        job['location_searched'] = market
                        job['radius_miles'] = radius_miles

                    market_results[exp_type] = jobs
                    print(f"{len(jobs)} jobs")

                except Exception as e:
                    print(f"❌ Error: {str(e)[:50]}...")
                    market_results[exp_type] = []

            all_results[market] = market_results

            # Show progress
            elapsed = time.time() - start_time
            total_jobs = sum(len(jobs) for market_data in all_results.values() for jobs in market_data.values())
            print(f"   📊 Market total: {sum(len(jobs) for jobs in market_results.values())} jobs")
            print(f"   ⏱️  Elapsed: {elapsed:.1f}s | Total jobs so far: {total_jobs}")

        # Final summary
        elapsed = time.time() - start_time
        total_jobs = sum(len(jobs) for market_data in all_results.values() for jobs in market_data.values())

        print(f"\n🎉 COMPLETED: {len(self.markets)} markets in {elapsed:.1f} seconds")
        print(f"📊 Total jobs found: {total_jobs}")

        return all_results

    def export_to_csv(self, results: Dict, filename: str = None) -> str:
        """Export results to CSV"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"fast_market_scrape_{timestamp}.csv"

        # Flatten all results
        all_jobs = []
        for market, market_data in results.items():
            for exp_type, jobs in market_data.items():
                for job in jobs:
                    job['market_scraped'] = market
                    all_jobs.append(job)

        if not all_jobs:
            print("❌ No jobs to export")
            return ""

        # CSV columns
        csv_columns = [
            # Job Identification
            'job_id', 'source_job_id', 'source_company_id',

            # Basic Job Info
            'normalized_title', 'source_title', 'normalized_company', 'source_company',
            'normalized_location', 'source_location',

            # Job Details
            'source_description', 'salary_info', 'employment_type', 'date_posted', 'application_url',

            # Experience & Requirements
            'experience_category', 'search_keywords', 'requirements', 'benefits',

            # Location Data
            'location_searched', 'market_scraped', 'radius_miles',

            # Company Information
            'company_website', 'company_phone', 'company_address', 'company_rating',

            # Metadata
            'scraped_at', 'scraper_version', 'data_source'
        ]

        # Write CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns, extrasaction='ignore')
            writer.writeheader()

            for job in all_jobs:
                # Ensure required fields
                job_row = {col: job.get(col, '') for col in csv_columns}

                # Map source_url to application_url
                if not job_row['application_url'] and job.get('source_url'):
                    job_row['application_url'] = job['source_url']

                # Add metadata
                if not job_row['scraped_at']:
                    job_row['scraped_at'] = datetime.now().isoformat()
                if not job_row['scraper_version']:
                    job_row['scraper_version'] = 'fast_market_v1.0'
                if not job_row['data_source']:
                    job_row['data_source'] = 'driver_pulse'

                writer.writerow(job_row)

        print(f"\n💾 CSV Export: {filename}")
        self._show_summary(all_jobs)

        return filename

    def _show_summary(self, jobs: List[Dict]):
        """Show summary statistics"""
        print(f"📊 FINAL SUMMARY")
        print("=" * 40)
        print(f"   Total jobs: {len(jobs)}")

        # By experience category
        exp_breakdown = {}
        for job in jobs:
            cat = job.get('experience_category', 'Unknown')
            exp_breakdown[cat] = exp_breakdown.get(cat, 0) + 1

        print(f"   Experience Categories:")
        for cat, count in exp_breakdown.items():
            print(f"     - {cat}: {count}")

        # By market
        market_breakdown = {}
        for job in jobs:
            market = job.get('location_searched', 'Unknown')
            market_breakdown[market] = market_breakdown.get(market, 0) + 1

        print(f"   Markets:")
        for market, count in sorted(market_breakdown.items()):
            print(f"     - {market}: {count}")

        # Top companies
        companies = {}
        for job in jobs:
            company = job.get('normalized_company', 'Unknown')
            companies[company] = companies.get(company, 0) + 1

        top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10]
        print(f"   Top Companies:")
        for company, count in top_companies:
            print(f"     - {company}: {count}")

def main():
    """Main function"""
    print("🚀 Fast Market Scraper for Entry-Level CDL Jobs")
    print("=" * 60)

    # Check environment variables
    required_vars = ['DRIVER_PULSE_EMAIL', 'DRIVER_PULSE_FIRST_NAME', 'DRIVER_PULSE_LAST_NAME', 'DRIVER_PULSE_PHONE']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f"❌ Missing environment variables: {missing}")
        return

    try:
        scraper = FastMarketScraper()

        # Get radius from env or default
        radius = int(os.getenv('FAST_SCRAPER_RADIUS', '50'))

        # Scrape all markets
        results = scraper.scrape_all_markets_fast(radius)

        # Export to CSV
        csv_file = scraper.export_to_csv(results)

        # Also save JSON backup
        json_file = csv_file.replace('.csv', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"💾 JSON backup: {json_file}")

        print(f"\n🎉 All markets scraped successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()