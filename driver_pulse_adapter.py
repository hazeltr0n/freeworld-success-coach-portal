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
from market_mapper import MarketMapper

class DriverPulseToPipelineAdapter:
    """Adapter to convert DriverPulse results to pipeline format"""

    def __init__(self, run_id: str = None):
        self.run_id = run_id or f"driver_pulse_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.market_mapper = MarketMapper()

    def _combine_job_content(self, job: Dict) -> str:
        """Combine description, requirements, and benefits into single HTML block

        This creates a structured description with clear sections that AI can parse:
        - Main job description
        - Requirements section (CDL class, experience, endorsements)
        - Benefits section (fair chance info, perks)
        """
        parts = []

        # Main description
        description = job.get('job_description', '')
        if description:
            parts.append(description)

        # Requirements section (CRITICAL for classification)
        requirements = job.get('job_requirements', '')
        if requirements:
            parts.append('<h3>Requirements</h3>')
            parts.append(requirements)

        # Benefits section
        benefits = job.get('job_general_benefits', '')
        if benefits:
            parts.append('<h3>Benefits</h3>')
            parts.append(benefits)

        return '\n\n'.join(parts)

    def _format_salary(self, job: Dict) -> str:
        """Format salary from DriverPulse structured fields"""
        min_pay = job.get('job_min_pay', '')
        max_pay = job.get('job_max_pay', '')
        single_pay = job.get('job_pay', '')
        unit = job.get('job_min_max_pay_unit', '')

        # Handle range
        if min_pay and max_pay:
            return f"${min_pay} - ${max_pay} {unit}"

        # Handle single value
        if single_pay:
            return f"${single_pay} {unit}"

        # Handle min only
        if min_pay:
            return f"${min_pay}+ {unit}"

        return ''

    def _format_location(self, job: Dict) -> str:
        """Format location from DriverPulse geo fields"""
        zip_code = job.get('zip', '')
        state = job.get('state', '')

        if zip_code and state:
            return f"{zip_code}, {state}"
        elif state:
            return state

        return ''

    def _build_application_url(self, job: Dict) -> str:
        """Construct DriverPulse application URL"""
        company_url = job.get('company_url_part', '')
        job_id = job.get('active_job_id', '')

        if company_url and job_id:
            return f"https://pulse.tenstreet.com/{company_url}/job/{job_id}"

        return ''

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

        # Auto-assign market for analytics (use normalized location)
        if 'norm.location' in df.columns:
            df['metadata.market'] = df['norm.location'].apply(self.market_mapper.map_market)

        return df

    def _convert_to_outscraper_format(self, jobs: List[Dict]) -> List[Dict]:
        """Convert DriverPulse job format to Outscraper-compatible format

        ZERO SCHEMA CHANGES: Combines description + requirements + benefits into
        source.description_raw field using HTML sections.
        """
        import json

        outscraper_jobs = []

        for job in jobs:
            outscraper_job = {
                # Basic fields - use new DriverPulse V2 API fields
                'title': job.get('job_title', ''),
                'company': job.get('company_name', ''),

                # COMBINED: description + requirements + benefits
                'snippet': self._combine_job_content(job),

                # FORMATTED: location from zip + state
                'formattedLocation': self._format_location(job),

                # CONSTRUCTED: DriverPulse URL
                'viewJobLink': self._build_application_url(job),

                # Job ID (maps to id.source_row)
                'job_id': job.get('active_job_id', ''),

                # FORMATTED: Salary from structured fields
                'salarySnippet': self._format_salary(job),

                # Date and metadata
                'date_posted': '',  # Not available from DriverPulse API
                'source': 'driver_pulse',

                # Store lat/lng as top-level fields for market mapping
                'latitude': job.get('lat', ''),
                'longitude': job.get('lng', ''),
                'zip_code': job.get('zip', ''),

                # Store DriverPulse metadata as JSON string
                'company_metadata': json.dumps({
                    'driver_pulse_company_id': job.get('company_id', ''),
                    'company_logo': job.get('company_logo', ''),
                    'company_url_part': job.get('company_url_part', ''),
                    'location_type': job.get('location_type', ''),
                    'zip': job.get('zip', ''),
                    'state': job.get('state', ''),
                }),

                # Technical metadata
                'scraped_at': job.get('scraped_at', datetime.now().isoformat()),
                'scraper_version': 'driver_pulse_v2.0',
                'data_source': 'driver_pulse',
                'search_term': job.get('search_term', ''),

                # CRITICAL: Set meta.market directly so it survives ensure_schema()
                'meta.market': job.get('market_scraped', job.get('state', ''))
            }

            # Ensure we have basic required fields
            if not outscraper_job['title']:
                outscraper_job['title'] = 'CDL Driver Position'
            if not outscraper_job['company']:
                outscraper_job['company'] = 'Unknown Company'
            if not outscraper_job['formattedLocation']:
                outscraper_job['formattedLocation'] = 'Unknown Location'

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
            # Don't pass a global market - each job has its own market_scraped field
            df = self.adapter.convert_to_pipeline_format(driver_pulse_results, "")

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

            # Note: meta.market is already set per-row in _convert_to_outscraper_format()
            # and will be preserved through ensure_schema() since it's in the schema

            # Process through pipeline stages (normalization, business rules, AI classification)
            print(f"🧠 Processing through pipeline stages...")
            pipeline = FreeWorldPipelineV3()

            # Run through pipeline stages
            # Pass empty market string since we already set meta.market directly
            df = pipeline._stage2_normalization(df)
            df = pipeline._stage3_business_rules(df, "", filter_settings or {})
            df = pipeline._stage4_deduplication(df)

            # AI Classification (based on user selection)
            classifier_selection = filter_settings.get('classifier_type', 'CDL Job Classifier')

            if classifier_selection == "None (No AI)":
                print(f"⚠️ AI classification skipped (user selected None)")
            elif classifier_selection == "Both (CDL + Pathway)":
                try:
                    df = pipeline._stage5_ai_classification(df, classifier_type="cdl")
                    print(f"✅ CDL classification completed")
                    df = pipeline._stage5_ai_classification(df, classifier_type="pathway")
                    print(f"✅ Pathway classification completed")
                except Exception as e:
                    print(f"⚠️ AI classification error: {e}")
            elif classifier_selection == "Pathway Classifier":
                try:
                    df = pipeline._stage5_ai_classification(df, classifier_type="pathway")
                    print(f"✅ Pathway classification completed")
                except Exception as e:
                    print(f"⚠️ AI classification error: {e}")
            else:  # Default to CDL
                try:
                    df = pipeline._stage5_ai_classification(df, classifier_type="cdl")
                    print(f"✅ CDL classification completed")
                except Exception as e:
                    print(f"⚠️ AI classification error: {e}")

            # Final routing - use empty string since each job has individual market
            df = pipeline._stage6_routing(df, "")

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