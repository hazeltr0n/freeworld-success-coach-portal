#!/usr/bin/env python3
"""
DriverPulse to Pipeline Adapter
Converts DriverPulse scraped data to FreeWorld Pipeline v3 format
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from jobs_schema import build_empty_df
from canonical_transforms import transform_ingest_outscraper

class DriverPulseToPipelineAdapter:
    """Adapter to convert DriverPulse results to pipeline format"""

    def __init__(self, run_id: str = None):
        self.run_id = run_id or f"driver_pulse_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def convert_to_pipeline_format(self, driver_pulse_results: Dict[str, Dict[str, List[Dict]]],
                                 search_location: str = "") -> pd.DataFrame:
        """
        Convert DriverPulse results to pipeline-compatible DataFrame

        Args:
            driver_pulse_results: Results from FastMarketScraper.scrape_all_markets_fast()
            search_location: Location used for search (for metadata)

        Returns:
            DataFrame in canonical pipeline format
        """
        # Flatten all jobs from all markets and experience types
        all_jobs = []

        for market, market_data in driver_pulse_results.items():
            for exp_type, jobs in market_data.items():
                for job in jobs:
                    # Add market and experience metadata
                    job['market_scraped'] = market
                    job['experience_type'] = exp_type
                    all_jobs.append(job)

        if not all_jobs:
            return build_empty_df()

        # Convert to Outscraper-compatible format for pipeline ingestion
        outscraper_format = self._convert_to_outscraper_format(all_jobs)

        # Use existing pipeline ingestion transform
        df = transform_ingest_outscraper(outscraper_format, self.run_id, search_location)

        return df

    def _convert_to_outscraper_format(self, jobs: List[Dict]) -> List[Dict]:
        """Convert DriverPulse job format to Outscraper-compatible format"""
        outscraper_jobs = []

        for job in jobs:
            # Map DriverPulse fields to Outscraper format
            # The actual DriverPulse scraper outputs these fields (from driver_pulse_source.py):
            # 'source_title', 'source_company', 'source_description', 'source_url', etc.
            outscraper_job = {
                # Basic job info - map to exact Outscraper field names that pipeline expects
                'title': job.get('source_title', job.get('normalized_title', '')),
                'company': job.get('source_company', job.get('normalized_company', '')),
                'snippet': job.get('source_description', ''),  # This maps to source.description_raw
                'formattedLocation': job.get('source_location', job.get('normalized_location', '')),

                # URLs and IDs - use exact Outscraper field names
                'viewJobLink': job.get('application_url', job.get('source_url', '')),  # This maps to source.url
                'job_id': job.get('driver_pulse_job_id', job.get('job_id', '')),

                # Salary and employment details - use exact Outscraper field names
                'salarySnippet': job.get('salary_info', job.get('source_salary', '')),
                'employment_type': job.get('employment_type', ''),

                # Date and metadata
                'date_posted': job.get('source_posted_date', job.get('date_posted', '')),
                'source': 'driver_pulse',

                # Company details (these may come from metadata added by fast_market_scraper)
                'company_website': job.get('company_website', ''),
                'company_phone': job.get('company_phone', ''),
                'company_address': job.get('company_address', ''),
                'company_rating': job.get('company_rating', ''),

                # DriverPulse specific metadata (added by fast_market_scraper)
                'experience_category': job.get('experience_category', ''),
                'search_keywords': job.get('search_keywords', ''),
                'location_searched': job.get('location_searched', job.get('search_location', '')),
                'market_scraped': job.get('market_scraped', ''),
                'radius_miles': job.get('radius_miles', ''),
                'requirements': job.get('requirements', ''),
                'benefits': job.get('benefits', ''),

                # Technical metadata
                'scraped_at': job.get('scraped_at', datetime.now().isoformat()),
                'scraper_version': job.get('scraper_version', 'driver_pulse_v1.0'),
                'data_source': 'driver_pulse'
            }

            # Ensure we have basic required fields
            if not outscraper_job['title']:
                outscraper_job['title'] = 'CDL Driver Position'
            if not outscraper_job['company']:
                outscraper_job['company'] = 'Unknown Company'
            if not outscraper_job['formattedLocation']:
                outscraper_job['formattedLocation'] = job.get('location_searched', 'Unknown Location')

            outscraper_jobs.append(outscraper_job)

        return outscraper_jobs

    def add_pipeline_metadata(self, df: pd.DataFrame, coach_username: str = "",
                            search_terms: str = "CDL Driver Entry Level") -> pd.DataFrame:
        """Add pipeline-specific metadata to the DataFrame"""
        if df.empty:
            return df

        # Add metadata fields that pipeline expects
        metadata_updates = {
            'meta.coach': coach_username,
            'meta.search_terms': search_terms,
            'meta.data_source': 'driver_pulse',
            'meta.run_id': self.run_id,
            'sys.scraped_at': datetime.now().isoformat(),
            'sys.pipeline_version': 'v3_driver_pulse_adapter'
        }

        for field, value in metadata_updates.items():
            if field not in df.columns:
                df[field] = value
            else:
                df[field] = df[field].fillna(value)

        return df

class DriverPulsePipelineIntegration:
    """Integration helper for running DriverPulse through pipeline"""

    def __init__(self):
        self.adapter = DriverPulseToPipelineAdapter()

    def run_driver_pulse_through_pipeline(self,
                                        radius_miles: int = 50,
                                        coach_username: str = "",
                                        search_terms: str = "CDL Driver Entry Level",
                                        filter_settings: Dict = None,
                                        target_locations: List[str] = None) -> Dict[str, Any]:
        """
        Run DriverPulse scraper and process through pipeline

        Returns:
            Dict with 'jobs_df' and 'metadata' keys like other pipeline sources
        """
        try:
            from fast_market_scraper import FastMarketScraper
            from pipeline_v3 import FreeWorldPipelineV3

            # Run DriverPulse scraper
            scraper = FastMarketScraper(target_locations)
            print(f"🏁 Running DriverPulse fast market scraper...")

            driver_pulse_results = scraper.scrape_all_markets_fast(radius_miles)

            # Convert to pipeline format
            print(f"🔄 Converting to pipeline format...")
            df = self.adapter.convert_to_pipeline_format(driver_pulse_results, "Multi-Market")

            if df.empty:
                return {
                    'jobs_df': df,
                    'metadata': {
                        'success': False,
                        'total_jobs': 0,
                        'error': 'No jobs found from DriverPulse'
                    }
                }

            # Add pipeline metadata
            df = self.adapter.add_pipeline_metadata(df, coach_username, search_terms)

            # Process through pipeline stages (normalization, business rules, AI classification)
            print(f"🧠 Processing through pipeline stages...")
            pipeline = FreeWorldPipelineV3()

            # Run through pipeline stages
            df = pipeline._stage2_normalization(df)
            df = pipeline._stage3_business_rules(df, "Multi-Market", filter_settings or {})
            df = pipeline._stage4_deduplication(df)

            # AI Classification (optional - can be expensive)
            try:
                df = pipeline._stage5_ai_classification(df, classifier_type="cdl")
                print(f"✅ AI classification completed")
            except Exception as e:
                print(f"⚠️ AI classification skipped: {e}")

            # Final routing
            df = pipeline._stage6_routing(df, "Multi-Market")

            # Generate metadata
            total_jobs = len(df)
            quality_jobs = len(df[df.get('ai.match', 'unknown').isin(['good', 'so-so'])]) if 'ai.match' in df.columns else total_jobs

            metadata = {
                'success': True,
                'total_jobs': total_jobs,
                'included_jobs': quality_jobs,
                'data_source': 'driver_pulse',
                'pipeline_version': 'v3_driver_pulse',
                'run_id': self.adapter.run_id,
                'processing_time': 0,  # TODO: Add timing
                'memory_efficiency': 0,  # N/A for fresh scrape
                'total_cost': 0  # DriverPulse is free (after auth)
            }

            return {
                'jobs_df': df,
                'metadata': metadata
            }

        except Exception as e:
            print(f"❌ DriverPulse pipeline integration error: {e}")
            return {
                'jobs_df': build_empty_df(),
                'metadata': {
                    'success': False,
                    'total_jobs': 0,
                    'error': str(e)
                }
            }