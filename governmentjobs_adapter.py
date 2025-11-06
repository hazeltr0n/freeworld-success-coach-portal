#!/usr/bin/env python3
"""
GovernmentJobs.com to Pipeline Adapter
Runs GovernmentJobs scraper and pushes results through Pipeline v3.1
"""

import pandas as pd
import asyncio
from datetime import datetime
from typing import Dict, Any
import os

# Import pipeline components
from pipeline_v3 import JobSearchPipeline
from scrape_governmentjobs_production import scrape_all_markets


class GovernmentJobsPipelineIntegration:
    """
    Integration class that runs GovernmentJobs scraper and pushes results through Pipeline v3.1

    Similar to DriverPulse adapter, but simpler since GovernmentJobs data is already clean
    """

    def __init__(self):
        self.run_id = f"governmentjobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def scrape_governmentjobs(
        self,
        keywords: list = None,
        markets: dict = None,
        max_pages_per_search: int = 3,
        headless: bool = True
    ) -> pd.DataFrame:
        """
        Run GovernmentJobs scraper and return DataFrame

        Args:
            keywords: Search keywords (default: ['CDL'])
            markets: Market configuration dict (default: all 10 markets)
            max_pages_per_search: Max pages to scrape per search
            headless: Run browser headlessly

        Returns:
            DataFrame with scraped jobs in pipeline format
        """
        print(f"\n{'='*80}")
        print(f"🏛️  GovernmentJobs.com Scraper Starting")
        print(f"{'='*80}")
        print(f"Run ID: {self.run_id}")
        print(f"Keywords: {keywords or ['CDL']}")
        print(f"Markets: {len(markets) if markets else 10} markets")
        print(f"Max pages: {max_pages_per_search}")
        print(f"{'='*80}\n")

        # Run the scraper
        df = await scrape_all_markets(
            keywords=keywords,
            markets=markets,
            max_pages_per_search=max_pages_per_search,
            headless=headless
        )

        if df.empty:
            print("⚠️  No jobs found from GovernmentJobs scraper")
            return df

        print(f"\n✅ GovernmentJobs scraper complete: {len(df)} jobs")
        return df

    def run_governmentjobs_through_pipeline(
        self,
        search_terms: str = "CDL",
        filter_settings: Dict = None,
        coach_username: str = "",
        keywords: list = None,
        markets: dict = None,
        max_pages_per_search: int = 3
    ) -> Dict[str, Any]:
        """
        Run GovernmentJobs scraper and process through Pipeline v3.1

        This is the main entry point for scheduled runs and integrations

        Args:
            search_terms: Search keywords string (for metadata)
            filter_settings: Pipeline filter settings
            coach_username: Coach attribution
            keywords: List of keywords to search (default: ['CDL'])
            markets: Market configuration (default: all 10)
            max_pages_per_search: Pages to scrape per search

        Returns:
            Dict with:
                - jobs_df: Final processed DataFrame
                - job_count: Total jobs
                - quality_job_count: Good/so-so jobs
                - run_id: Unique run identifier
        """
        # Default filter settings
        if filter_settings is None:
            filter_settings = {
                'filter_mode': 'all_markets',
                'classifier_type': 'CDL Job Classifier'
            }

        # Run scraper
        print(f"\n🚀 Starting GovernmentJobs Pipeline Integration")
        df = asyncio.run(self.scrape_governmentjobs(
            keywords=keywords or ['CDL'],
            markets=markets,
            max_pages_per_search=max_pages_per_search,
            headless=True
        ))

        if df.empty:
            return {
                'jobs_df': df,
                'job_count': 0,
                'quality_job_count': 0,
                'run_id': self.run_id
            }

        # Initialize pipeline
        print(f"\n{'='*80}")
        print(f"🔄 Running Pipeline v3.1")
        print(f"{'='*80}\n")

        pipeline = JobSearchPipeline(
            run_id=self.run_id,
            search_terms=search_terms,
            coach_username=coach_username
        )

        # Stage 1: Ingestion (already done by scraper)
        # The DataFrame from scraper is already in pipeline format
        pipeline.df = df.copy()
        print(f"✅ Stage 1: Ingestion - {len(pipeline.df)} jobs from GovernmentJobs\n")

        # Stage 2: Normalization (already done - GovernmentJobs data is clean)
        print(f"✅ Stage 2: Normalization - GovernmentJobs data pre-normalized\n")

        # Stage 3: Business Rules
        pipeline.df = pipeline._apply_business_rules(pipeline.df)
        print(f"✅ Stage 3: Business Rules - {len(pipeline.df)} jobs passed\n")

        # Stage 4: Deduplication
        initial_count = len(pipeline.df)
        pipeline.df = pipeline._deduplicate_jobs(pipeline.df)
        dedup_removed = initial_count - len(pipeline.df)
        print(f"✅ Stage 4: Deduplication - Removed {dedup_removed} duplicates, {len(pipeline.df)} unique jobs\n")

        # Stage 5: AI Classification
        pipeline.df = pipeline._classify_jobs(
            pipeline.df,
            classifier_type=filter_settings.get('classifier_type', 'CDL Job Classifier')
        )
        print(f"✅ Stage 5: AI Classification - {len(pipeline.df)} jobs classified\n")

        # Stage 6: Routing Logic
        pipeline.df = pipeline._apply_routing_logic(pipeline.df, filter_settings)

        # Count quality jobs (good/so-so)
        quality_count = len(pipeline.df[pipeline.df['ai.match'].isin(['good', 'so-so'])])
        print(f"✅ Stage 6: Routing - {quality_count} quality jobs (good/so-so)\n")

        # Stage 7: Link Tracking (generate tracked URLs)
        pipeline.df = pipeline._generate_tracked_urls(
            pipeline.df,
            coach_username=coach_username
        )
        print(f"✅ Stage 7: Link Tracking - Generated tracked URLs for quality jobs\n")

        # Stage 8: Data Storage (upload to Supabase)
        upload_count = pipeline._store_to_supabase(pipeline.df)
        print(f"✅ Stage 8: Data Storage - Uploaded {upload_count} jobs to Supabase\n")

        print(f"\n{'='*80}")
        print(f"✅ Pipeline Complete!")
        print(f"{'='*80}")
        print(f"Total Jobs: {len(pipeline.df)}")
        print(f"Quality Jobs: {quality_count} (good/so-so)")
        print(f"Uploaded to Supabase: {upload_count}")
        print(f"{'='*80}\n")

        return {
            'jobs_df': pipeline.df,
            'job_count': len(pipeline.df),
            'quality_job_count': quality_count,
            'run_id': self.run_id
        }


# Standalone execution for testing
if __name__ == "__main__":
    import sys

    print("🏛️  GovernmentJobs.com Pipeline Integration Test")

    # Check for credentials
    email = os.getenv('GOVERNMENT_JOBS_EMAIL')
    password = os.getenv('GOVERNMENT_JOBS_PASSWORD')

    if not email or not password:
        print("❌ Error: GOVERNMENT_JOBS_EMAIL and GOVERNMENT_JOBS_PASSWORD must be set")
        sys.exit(1)

    # Run integration
    integration = GovernmentJobsPipelineIntegration()

    filter_settings = {
        'filter_mode': 'all_markets',
        'classifier_type': 'CDL Job Classifier'
    }

    result = integration.run_governmentjobs_through_pipeline(
        search_terms="CDL",
        filter_settings=filter_settings,
        coach_username="automated_scraper",
        keywords=["CDL"],
        max_pages_per_search=2  # Test with 2 pages
    )

    print(f"\n✅ Test Complete!")
    print(f"Jobs: {result['job_count']}")
    print(f"Quality: {result['quality_job_count']}")
    print(f"Run ID: {result['run_id']}")
