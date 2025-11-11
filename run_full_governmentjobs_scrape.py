#!/usr/bin/env python3
"""
Run FULL GovernmentJobs scrape for all markets and process through pipeline

This does:
1. Scrape ALL markets (10+ locations)
2. Process through entire Pipeline v3.1
3. Upload to Supabase

Usage:
    python3 run_full_governmentjobs_scrape.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check credentials
email = os.getenv('GOVERNMENT_JOBS_EMAIL')
password = os.getenv('GOVERNMENT_JOBS_PASSWORD')

if not email or not password:
    print("❌ Error: Missing credentials")
    print("   Set GOVERNMENT_JOBS_EMAIL and GOVERNMENT_JOBS_PASSWORD in .env")
    sys.exit(1)

print("✅ Credentials found")
print(f"   Email: {email}")

# Import adapter
from governmentjobs_adapter import GovernmentJobsPipelineIntegration

print("\n" + "="*80)
print("🏛️  FULL GOVERNMENTJOBS SCRAPE - ALL MARKETS")
print("="*80)
print()

# Create integration
integration = GovernmentJobsPipelineIntegration()

# Filter settings
filter_settings = {
    'filter_mode': 'all_markets',
    'classifier_type': 'CDL Job Classifier'
}

# Run FULL scrape with ALL markets
print("🚀 Starting FULL scrape...")
print("   Keywords: ['CDL']")
print("   Markets: ALL (will use default 10 markets)")
print("   Max pages: 10 per search (full scrape)")
print()

result = integration.run_governmentjobs_through_pipeline(
    search_terms="CDL",
    filter_settings=filter_settings,
    coach_username="automated_scraper",
    keywords=["CDL"],
    markets=None,  # None = use all default markets
    max_pages_per_search=10  # FULL scrape
)

# Print results
print("\n" + "="*80)
print("🎉 FULL SCRAPE COMPLETE!")
print("="*80)
print(f"Total Jobs Scraped: {result['job_count']}")
print(f"Quality Jobs (good/so-so): {result['quality_job_count']}")
print(f"Run ID: {result['run_id']}")
print("="*80)
