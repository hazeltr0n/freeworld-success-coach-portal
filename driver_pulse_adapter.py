#!/usr/bin/env python3
"""
DriverPulse to Pipeline Adapter
Converts DriverPulse scraped data to FreeWorld Pipeline v3 format
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from jobs_schema import build_empty_df
from concurrent.futures import ThreadPoolExecutor, as_completed
from canonical_transforms import transform_ingest_outscraper
from market_mapper import MarketMapper

# Import precomputed ZIP lookup for instant filtering and City, ST mapping
try:
    from zip_market_lookup import VALID_ZIPS, ZIP_TO_MARKETS, ZIP_TO_CITY_STATE
    ZIP_LOOKUP_AVAILABLE = True
except ImportError:
    ZIP_LOOKUP_AVAILABLE = False
    VALID_ZIPS = set()
    ZIP_TO_MARKETS = {}
    ZIP_TO_CITY_STATE = {}

class DriverPulseToPipelineAdapter:
    """Adapter to convert DriverPulse results to pipeline format"""

    # State-to-FreeWorld markets mapping (for ident='state' jobs)
    STATE_TO_MARKETS = {
        'TX': ['Dallas', 'Houston'],
        'CA': ['Stockton', 'Bay Area', 'Inland Empire'],
        'NJ': ['Trenton', 'Newark'],
        'AZ': ['Phoenix'],
        'CO': ['Denver'],
        'NV': ['Las Vegas']
    }

    # Central ZIP codes for each FreeWorld market (from market search radius.csv)
    MARKET_CENTRAL_ZIPS = {
        'Dallas': '75060',
        'Houston': '77007',
        'Phoenix': '85009',
        'Denver': '80218',
        'Las Vegas': '89107',
        'Stockton': '95205',
        'Bay Area': '94501',
        'Inland Empire': '92324',
        'Trenton': '07017',
        'Newark': '08638'
    }

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
        if description and str(description).strip():
            parts.append(str(description))

        # Requirements section (CRITICAL for classification)
        requirements = job.get('job_requirements', '')
        if requirements and str(requirements).strip():
            parts.append('<h3>Requirements</h3>')
            parts.append(str(requirements))

        # Benefits section
        benefits = job.get('job_general_benefits', '')
        if benefits and str(benefits).strip():
            parts.append('<h3>Benefits</h3>')
            parts.append(str(benefits))

        return '\n\n'.join(parts) if parts else 'No description available'

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

    def _format_location(self, job: Dict, assigned_zip: str = '') -> str:
        """Format location from DriverPulse geo fields → City, ST

        Args:
            job: Raw DriverPulse job data
            assigned_zip: ZIP code assigned by market logic (for state-level jobs)
        """
        # Use assigned ZIP first (for state-level jobs), then fall back to job's original ZIP
        zip_code = assigned_zip or job.get('zip', '')

        # Use ZIP → City, ST lookup for consistency across app
        if zip_code and ZIP_LOOKUP_AVAILABLE:
            city_state = ZIP_TO_CITY_STATE.get(zip_code)
            if city_state:
                return city_state

        # Fallback to ZIP, State if lookup fails
        state = job.get('state', '')
        if zip_code and state:
            return f"{zip_code}, {state}"
        elif state:
            return state

        return ''

    def _build_application_url(self, job: Dict) -> str:
        """Construct IntelliApp application URL for DriverPulse jobs"""
        # Use company url_part from company data, not company_url_part from job
        url_part = job.get('company_url_part', '')

        if url_part:
            # Build IntelliApp URL with the company's url_part
            return f"https://intelliapp.driverapponline.com/c/{url_part}"

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

        # Override source to DriverPulse (not Indeed/Google)
        df['id.source'] = 'driver_pulse'

        # Skip market mapping for DriverPulse - locations are already ZIP-based
        df['metadata.market'] = 'DriverPulse'

        return df

    def _convert_to_outscraper_format(self, jobs: List[Dict]) -> List[Dict]:
        """Convert DriverPulse job format to Outscraper-compatible format

        Handles ident field logic:
        - ident='zip': Use the job's ZIP code directly
        - ident='state': Create copies of job for ALL FreeWorld markets in that state
        - ident='polygon': Skip (not supported)
        """
        import json

        outscraper_jobs = []

        for job in jobs:
            ident = job.get('ident', 'zip')  # Default to 'zip' if missing

            # Skip polygon jobs - not supported
            if ident == 'polygon':
                continue

            # Handle state-level jobs - create copies for each market in that state
            if ident == 'state':
                # For state-level jobs, the state code is in the 'value' field
                state = job.get('value', '')
                markets = self.STATE_TO_MARKETS.get(state, [])

                if not markets:
                    # State not in our FreeWorld markets - skip
                    continue

                # Create a copy of this job for EACH market in the state
                for market in markets:
                    # Get central ZIP for this market
                    market_zip = self.MARKET_CENTRAL_ZIPS.get(market)

                    if not market_zip:
                        continue  # Skip if we don't have a central ZIP for this market

                    # Create job copy with this market's central ZIP
                    outscraper_job = self._create_outscraper_job(job, market_zip, market)
                    outscraper_jobs.append(outscraper_job)

            # Handle ZIP-based jobs - standard flow
            elif ident == 'zip':
                job_zip = job.get('zip', '')

                if not job_zip:
                    continue  # Skip jobs without ZIP

                # Look up FreeWorld markets for this ZIP
                markets = ZIP_TO_MARKETS.get(str(job_zip), [])

                if not markets:
                    continue  # Skip ZIPs not in our markets

                # Use first market in list
                market = markets[0]

                outscraper_job = self._create_outscraper_job(job, job_zip, market)
                outscraper_jobs.append(outscraper_job)

        return outscraper_jobs

    def _create_outscraper_job(self, job: Dict, zip_code: str, market: str) -> Dict:
        """Create a single Outscraper-format job with given ZIP and market"""
        import json

        outscraper_job = {
            # Basic fields
            'title': job.get('job_title', ''),
            'company': job.get('company_name', ''),

            # COMBINED: description + requirements + benefits
            'snippet': self._combine_job_content(job),

            # FORMATTED: location from assigned ZIP (for state-level jobs)
            'formattedLocation': self._format_location(job, assigned_zip=zip_code),

            # CONSTRUCTED: DriverPulse URL
            'viewJobLink': self._build_application_url(job),

            # Job ID (maps to id.source_row)
            'job_id': job.get('active_job_id', ''),

            # FORMATTED: Salary from structured fields
            'salarySnippet': self._format_salary(job),

            # Date and metadata
            'date_posted': '',
            'source': 'driver_pulse',

            # Store lat/lng as top-level fields
            'latitude': job.get('lat', ''),
            'longitude': job.get('lng', ''),
            'zip_code': zip_code,  # Use the assigned ZIP

            # Store DriverPulse metadata
            'company_metadata': json.dumps({
                'driver_pulse_company_id': job.get('company_id', ''),
                'company_logo': job.get('company_logo', ''),
                'company_url_part': job.get('company_url_part', ''),
                'location_type': job.get('location_type', ''),
                'original_zip': job.get('zip', ''),
                'original_state': job.get('state', ''),
                'ident': job.get('ident', 'zip'),
            }),

            # Technical metadata
            'scraped_at': job.get('scraped_at', datetime.now().isoformat()),
            'scraper_version': 'driver_pulse_v2.0',
            'data_source': 'driver_pulse',
            'search_term': job.get('search_term', ''),

            # CRITICAL: Set meta.market directly
            'meta.market': market
        }

        # Ensure we have basic required fields
        if not outscraper_job['title']:
            outscraper_job['title'] = 'CDL Driver Position'
        if not outscraper_job['company']:
            outscraper_job['company'] = 'Unknown Company'
        if not outscraper_job['formattedLocation']:
            outscraper_job['formattedLocation'] = 'Unknown Location'

        return outscraper_job

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

    def _load_location_markets(self, filter_mode: str, custom_zips: List[str] = None) -> set:
        """
        Load target ZIP codes based on filter mode

        Args:
            filter_mode: "all_markets" or "custom_zips"
            custom_zips: List of custom ZIP codes (if filter_mode = "custom_zips")

        Returns:
            Set of ZIP codes to filter to
        """
        if filter_mode == "custom_zips":
            if not custom_zips:
                return set()
            # Normalize ZIPs to 5 digits
            return {str(z).zfill(5) for z in custom_zips}

        # "all_markets" mode - use precomputed ZIP lookup for instant filtering
        if ZIP_LOOKUP_AVAILABLE:
            print(f"📍 Using precomputed ZIP lookup ({len(VALID_ZIPS)} ZIPs)", flush=True)
            return VALID_ZIPS

        # Fallback to database query if lookup not available
        print("⚠️ Precomputed ZIP lookup not available, querying database...", flush=True)
        try:
            from companies_rollup import get_client
            client = get_client()

            # Get all ZIPs from location_markets table
            zips_result = client.table('location_markets').select('location_string').eq('location_type', 'zip').execute()
            zip_codes = {row['location_string'] for row in zips_result.data}

            print(f"📍 Loaded {len(zip_codes)} ZIPs from location_markets for filtering", flush=True)
            return zip_codes

        except Exception as e:
            print(f"⚠️ Error loading location_markets: {e}", flush=True)
            return set()

    def run_driver_pulse_through_pipeline(self,
                                        radius_miles: int = 50,
                                        coach_username: str = "",
                                        search_terms: str = "CDL Driver Entry Level",
                                        filter_settings: Dict = None,
                                        target_locations: List[str] = None) -> Dict[str, Any]:
        """
        Run DriverPulse scraper and process through pipeline

        NEW APPROACH (v2):
        1. Scrape ALL jobs nationwide (API ignores location parameter)
        2. Filter to target ZIP codes BEFORE AI classification
        3. Run AI classification only on filtered jobs (cost savings)

        Returns:
            Dict with 'jobs_df' and 'metadata' keys like other pipeline sources
        """
        try:
            from driver_pulse_source import DriverPulseSource, DriverPulseConfig
            from pipeline_v3 import FreeWorldPipelineV3

            filter_settings = filter_settings or {}
            filter_mode = filter_settings.get('filter_mode', 'all_markets')
            custom_zips = filter_settings.get('custom_zips', None)

            # Load target ZIP codes for filtering
            target_zips = self._load_location_markets(filter_mode, custom_zips)
            if not target_zips:
                print(f"⚠️ No target ZIPs loaded - will process all jobs")

            # Step 1: Load existing authentication (created by GitHub Actions workflow)
            print(f"🔐 Loading DriverPulse authentication from storage...")

            config = DriverPulseConfig(search_text=search_terms, location="", max_companies=1)
            source = DriverPulseSource(config)

            # Load auth from storage (Supabase > local file)
            success = source.load_authentication()

            if not success:
                raise Exception("Authentication not found. Fresh auth should be created by GitHub Actions workflow first.")

            print(f"🔍 Searching for: '{search_terms}'")
            print(f"📄 Paginating through ALL companies...")

            # Use the source's search_companies method with pagination
            all_companies = {}
            page_num = 1
            max_pages = 13  # Stop at page 13 (page 14+ returns no results)

            while page_num <= max_pages:
                result = source.search_companies(search_text=search_terms, page_number=page_num)

                if not result or 'response' not in result:
                    print(f"   ❌ Page {page_num} failed or returned no response")
                    # Show last few companies from previous page for debugging
                    if all_companies:
                        last_5 = list(all_companies.values())[-5:]
                        print(f"   🔍 Last 5 companies from page {page_num-1}:")
                        for c in last_5:
                            print(f"      - {c.get('company_name', 'Unknown')} (ID: {c.get('company_id', 'N/A')})")
                    break

                companies = result['response']
                company_ids = [k for k in companies.keys()
                              if k not in ['default_companies_selected', 'has_results', 'result_count']]

                if not company_ids:
                    print(f"   ✅ Reached end at page {page_num} (no more companies)")
                    break

                for company_id in company_ids:
                    all_companies[company_id] = companies[company_id]

                print(f"   Page {page_num}: +{len(company_ids)} companies (total: {len(all_companies)})")

                # Show sample companies for debugging page 13 specifically
                if page_num == 13:
                    print(f"   🔍 Last 3 companies on page 13:")
                    page_13_companies = [companies[cid] for cid in company_ids[-3:]]
                    for c in page_13_companies:
                        print(f"      - {c.get('company_name', 'Unknown')} (ID: {c.get('company_id', 'N/A')})")

                has_more = companies.get('has_results', True)
                if not has_more:
                    print(f"   ✅ No more results after page {page_num}")
                    break

                page_num += 1

            print(f"\n🔍 DEBUG: Pagination loop ended at page {page_num}", flush=True)
            print(f"🔍 DEBUG: all_companies type: {type(all_companies)}, count: {len(all_companies)}", flush=True)
            print(f"\n✅ Found {len(all_companies)} total companies", flush=True)

            # Step 2: Get full job details for ALL jobs (PARALLEL)
            all_jobs = []
            print(f"🔍 DEBUG: About to calculate total_job_ids from {len(all_companies)} companies...", flush=True)
            total_job_ids = sum(len(c.get('highlighted_content', [])) for c in all_companies.values())
            print(f"🔍 DEBUG: Calculated total_job_ids = {total_job_ids}", flush=True)
            print(f"📊 Fetching full details for {total_job_ids} jobs (20 workers in parallel)...", flush=True)

            # Helper function for parallel execution
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
                    full_job['scraped_at'] = datetime.now().isoformat()
                    full_job['search_term'] = search_terms
                    return full_job
                return None

            # Build list of jobs to fetch
            jobs_to_fetch = []
            for company_id, company_data in all_companies.items():
                highlighted = company_data.get('highlighted_content', [])
                for job_snippet in highlighted:
                    jobs_to_fetch.append((company_id, company_data, job_snippet))

            # Parallel fetch with progress updates
            processed = 0
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = {executor.submit(fetch_job_detail, job_info): job_info for job_info in jobs_to_fetch}

                for future in as_completed(futures):
                    processed += 1
                    job = future.result()
                    if job:
                        all_jobs.append(job)

                    if processed % 50 == 0:
                        print(f"   {processed}/{total_job_ids} jobs fetched...", flush=True)

            print(f"✅ Fetched {len(all_jobs)} complete jobs", flush=True)

            # Step 3: Convert to Outscraper-compatible format
            # This handles ident logic:
            # - ident='zip': filters to ZIPs in our markets
            # - ident='state': creates copies for all markets in that state
            # - ident='polygon': skips
            print(f"\n🔄 Converting {len(all_jobs)} jobs to Outscraper format (with ident-based filtering)...")
            jobs_before = len(all_jobs)
            outscraper_jobs = self.adapter._convert_to_outscraper_format(all_jobs)
            jobs_after = len(outscraper_jobs)

            print(f"   Before conversion: {jobs_before} jobs")
            print(f"   After conversion: {jobs_after} jobs (includes multi-market copies for state-level jobs)")
            if jobs_before > 0:
                reduction = jobs_before - jobs_after
                if reduction > 0:
                    print(f"   🗑️ Filtered out: {reduction} jobs outside our markets")
                else:
                    expansion = jobs_after - jobs_before
                    print(f"   📋 Expanded: +{expansion} job copies for state-level jobs")

            if not outscraper_jobs:
                return {
                    'jobs_df': build_empty_df(),
                    'metadata': {
                        'success': False,
                        'total_jobs': 0,
                        'error': 'No jobs found in target locations'
                    }
                }

            # Step 5: Convert to pipeline DataFrame
            # NOTE: outscraper_jobs is ALREADY in Outscraper format from line 455
            # So we skip convert_to_pipeline_format() and go directly to transform_ingest_outscraper()
            print(f"\n🔄 Converting {len(outscraper_jobs)} jobs to pipeline format...")
            from canonical_transforms import transform_ingest_outscraper
            df = transform_ingest_outscraper(outscraper_jobs, self.adapter.run_id, "")

            # Override source to DriverPulse (not Indeed/Google)
            df['id.source'] = 'driver_pulse'

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

            # Step 6: Process through pipeline stages (normalization, business rules, AI classification)
            print(f"\n🧠 Processing through pipeline stages...")
            pipeline = FreeWorldPipelineV3()

            # Run through pipeline stages
            df = pipeline._stage2_normalization(df)
            df = pipeline._stage3_business_rules(df, "", filter_settings or {})
            df = pipeline._stage4_deduplication(df)

            print(f"   After deduplication: {len(df)} jobs")

            # Step 6.5: Route classification (BEFORE AI so route_type is available)
            df = pipeline._stage5_5_route_rules(df)
            print(f"   After route classification: {len(df)} jobs")

            # Step 7: AI Classification (based on user selection)
            classifier_selection = filter_settings.get('classifier_type', 'CDL Job Classifier')

            if classifier_selection == "None (No AI)":
                print(f"\n⚠️ AI classification skipped (user selected None)")
            elif classifier_selection == "Both (CDL + Pathway)":
                try:
                    print(f"\n🤖 Running CDL classification...")
                    df = pipeline._stage5_ai_classification(df, classifier_type="cdl")
                    print(f"✅ CDL classification completed")
                    print(f"\n🤖 Running Pathway classification...")
                    df = pipeline._stage5_ai_classification(df, classifier_type="pathway")
                    print(f"✅ Pathway classification completed")
                except Exception as e:
                    print(f"⚠️ AI classification error: {e}")
            elif classifier_selection == "Pathway Classifier":
                try:
                    print(f"\n🤖 Running Pathway classification...")
                    df = pipeline._stage5_ai_classification(df, classifier_type="pathway")
                    print(f"✅ Pathway classification completed")
                except Exception as e:
                    print(f"⚠️ AI classification error: {e}")
            else:  # Default to CDL
                try:
                    print(f"\n🤖 Running CDL classification...")
                    df = pipeline._stage5_ai_classification(df, classifier_type="cdl")
                    print(f"✅ CDL classification completed")
                except Exception as e:
                    print(f"⚠️ AI classification error: {e}")

            # Step 6: Final routing
            df = pipeline._stage6_routing(df, "")

            # Step 7: Link tracking (generate Short.io links)
            # We don't need PDF/CSV/HTML files, just the link tracking
            # Stage 7 updates pipeline.df internally with tracked URLs
            pipeline._stage7_output(
                df=df,
                market="",
                custom_location="",
                generate_pdf=False,
                generate_csv=False,
                generate_html=False,
                force_memory_only=False
            )

            # Step 8: Data storage (upload to Supabase)
            # Use pipeline.df which now has tracked URLs from stage 7
            pipeline._stage8_storage(pipeline.df, push_to_airtable=False)

            # Update our local df reference to match pipeline.df
            df = pipeline.df

            # Generate metadata
            total_jobs = len(df)
            quality_jobs = len(df[df.get('ai.match', 'unknown').isin(['good', 'so-so'])]) if 'ai.match' in df.columns else total_jobs
            uploaded_count = pipeline.supabase_upload_count if hasattr(pipeline, 'supabase_upload_count') else 0

            print(f"\n✅ COMPLETE!")
            print(f"   Total jobs: {total_jobs}")
            print(f"   Quality jobs (good/so-so): {quality_jobs}")
            print(f"   Uploaded to Supabase: {uploaded_count}")

            metadata = {
                'success': True,
                'total_jobs': total_jobs,
                'included_jobs': quality_jobs,
                'data_source': 'driver_pulse',
                'pipeline_version': 'v3.1_driver_pulse_v2',
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
            import traceback
            print(f"❌ DriverPulse pipeline integration error: {e}")
            traceback.print_exc()
            return {
                'jobs_df': build_empty_df(),
                'metadata': {
                    'success': False,
                    'total_jobs': 0,
                    'error': str(e)
                }
            }