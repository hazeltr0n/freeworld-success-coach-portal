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
from pipeline_v3 import FreeWorldPipelineV3
from scrape_governmentjobs_production import scrape_all_markets
from canonical_transforms import transform_ingest_governmentjobs


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

        pipeline = FreeWorldPipelineV3()

        # Stage 1: Ingestion - Use transform function to ensure proper schema
        print(f"📥 Stage 1: Ingestion - Transforming {len(df)} jobs\n")
        jobs_list = df.to_dict('records')
        df = transform_ingest_governmentjobs(jobs_list, self.run_id)
        print(f"✅ Stage 1: Ingestion Complete - {len(df)} jobs\n")

        # Stage 2: Normalization
        df = pipeline._stage2_normalization(df)
        print(f"✅ Stage 2: Normalization - {len(df)} jobs\n")

        # Stage 3: Business Rules
        df = pipeline._stage3_business_rules(df, "", filter_settings)
        print(f"✅ Stage 3: Business Rules - {len(df)} jobs passed\n")

        # Stage 4: Deduplication
        initial_count = len(df)
        df = pipeline._stage4_deduplication(df)
        dedup_removed = initial_count - len(df)
        print(f"✅ Stage 4: Deduplication - Removed {dedup_removed} duplicates, {len(df)} unique jobs\n")

        # Stage 5: AI Classification
        classifier_type = filter_settings.get('classifier_type', 'CDL Job Classifier')

        if classifier_type == "CDL Job Classifier":
            df = pipeline._stage5_ai_classification(df, classifier_type="cdl")
        elif classifier_type == "Pathway Classifier":
            df = pipeline._stage5_ai_classification(df, classifier_type="pathway")
        elif classifier_type == "Both (CDL + Pathway)":
            df = pipeline._stage5_ai_classification(df, classifier_type="cdl")
            df = pipeline._stage5_ai_classification(df, classifier_type="pathway")

        print(f"✅ Stage 5: AI Classification - {len(df)} jobs classified\n")

        # Stage 6: Routing Logic
        df = pipeline._stage6_routing(df, filter_settings)

        # Count quality jobs (good/so-so)
        quality_count = len(df[df['ai.match'].isin(['good', 'so-so'])])
        print(f"✅ Stage 6: Routing - {quality_count} quality jobs (good/so-so)\n")

        # Stage 7: Output Generation (generates tracked URLs and files)
        results = pipeline._stage7_output(
            df,
            market="GovernmentJobs",
            custom_location=None,
            generate_pdf=False,
            generate_csv=False,
            generate_html=False,
            force_memory_only=False,
            show_prepared_for=True
        )

        # Get DataFrame with tracked URLs from results
        df_with_links = results.get('jobs_df', df)
        print(f"✅ Stage 7: Output Generation - Generated tracked URLs for quality jobs\n")

        # Stage 8: Data Storage (upload to Supabase)
        pipeline._stage8_storage(df_with_links, push_to_airtable=False)

        # Count how many jobs were uploaded
        upload_count = len(df_with_links[df_with_links['ai.match'].isin(['good', 'so-so'])])
        print(f"✅ Stage 8: Data Storage - Uploaded {upload_count} jobs to Supabase\n")

        print(f"\n{'='*80}")
        print(f"✅ Pipeline Complete!")
        print(f"{'='*80}")
        print(f"Total Jobs: {len(df_with_links)}")
        print(f"Quality Jobs: {quality_count} (good/so-so)")
        print(f"Uploaded to Supabase: {upload_count}")
        print(f"{'='*80}\n")

        return {
            'jobs_df': df_with_links,
            'job_count': len(df_with_links),
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
