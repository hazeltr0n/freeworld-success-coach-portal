"""
Pipeline v3: Single Canonical Table Architecture - SUPABASE FILTER FIX 2025-09-05
Bulletproof data handling with namespaced fields and full audit trails
MAJOR FIX: Supabase route type filtering now works correctly at database level
"""

import pandas as pd
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import uuid

# Cache refresh marker - September 5, 2025 - Supabase filtering fix
PIPELINE_CACHE_VERSION = "v3.1-supabase-filter-fix-20250905"
import asyncio

# Link tracker for URL shortening
try:
    from link_tracker import LinkTracker
except ImportError:
    try:
        from link_tracker import LinkTracker
    except ImportError:
        LinkTracker = None

# HTML generation for portal
try:
    from pdf.html_pdf_generator import jobs_dataframe_to_dicts, render_jobs_html
except ImportError:
    jobs_dataframe_to_dicts = None
    render_jobs_html = None

# Import existing modules (preserve all functionality) - with fallbacks for Streamlit Cloud
try:
    from job_scraper import FreeWorldJobScraper
    from job_classifier import JobClassifier
    from job_memory_db import JobMemoryDB
    from cost_calculator import CostCalculator
    from fpdf_pdf_generator import generate_fpdf_job_cards
    from simple_bypass_system import SimpleBypassSystem
    from route_classifier import RouteClassifier
    from free_agent_lookup import FreeAgentLookup
    from jobs_schema import (
        build_empty_df, ensure_schema, validate_dataframe, 
        prepare_for_supabase, get_schema_info, SUPABASE_FIELDS
    )
    from canonical_transforms import (
        transform_ingest_outscraper, transform_ingest_google, transform_ingest_memory,
        transform_normalize, transform_business_rules,
        transform_ai_classification, transform_routing,
        apply_market_assignment, apply_tracked_urls,
        merge_dataframes, view_ready_for_ai, view_exportable, view_fresh_quality
    )
    from shared_search import QUERY_LOCATION_OVERRIDES, MARKET_TO_LOCATION
except ImportError:
    # Fallback imports for Streamlit Cloud (all files in same directory)
    from job_scraper import FreeWorldJobScraper
    from job_classifier import JobClassifier
    from job_memory_db import JobMemoryDB
    from cost_calculator import CostCalculator
    from fpdf_pdf_generator import generate_fpdf_job_cards
    from simple_bypass_system import SimpleBypassSystem
    from route_classifier import RouteClassifier
    from jobs_schema import (
        build_empty_df, ensure_schema, validate_dataframe, 
        prepare_for_supabase, get_schema_info, SUPABASE_FIELDS
    )
    from canonical_transforms import (
        transform_ingest_outscraper, transform_ingest_google, transform_ingest_memory,
        transform_normalize, transform_business_rules,
        transform_ai_classification, transform_routing,
        apply_market_assignment, apply_tracked_urls,
        merge_dataframes, view_ready_for_ai, view_exportable, view_fresh_quality
    )
    from shared_search import QUERY_LOCATION_OVERRIDES, MARKET_TO_LOCATION

class FreeWorldPipelineV3:
    """
    Single Canonical Table Pipeline with Full Data Integrity
    
    Key Features:
    - Single DataFrame throughout entire pipeline
    - Namespaced fields prevent overwrites
    - Complete audit trail of every operation
    - Views instead of copies for filtering
    - Parquet storage for performance
    - Supabase for paid data only
    """
    
    def __init__(self):
        """Initialize pipeline with all existing modules"""
        
        # Generate unique run ID for this pipeline execution
        self.run_id = f"pipeline_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Initialize custom location flag (defaults to False)
        self._is_custom_location = False
        
        # Initialize all existing modules (preserve functionality)
        self.scraper = FreeWorldJobScraper()
        self.classifier = JobClassifier()
        self.memory_db = JobMemoryDB()
        # Airtable upload disabled: pipeline only writes to Supabase (memory store)
        self.bypass_system = SimpleBypassSystem()
        self.route_classifier = RouteClassifier()
        self.free_agent_lookup = FreeAgentLookup()
        
        # Cost tracking for different sources
        self.google_api_cost = 0.0
        
        # Output directory setup
        self.output_dir = self._get_output_path()
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create parquet storage directory
        self.parquet_dir = os.path.join(self.output_dir, "parquet")
        os.makedirs(self.parquet_dir, exist_ok=True)
        
        # Schema info for provenance
        self.schema_info = get_schema_info()
        
        # Get Free Agent data once during initialization (from environment)
        self.agent_data = self.free_agent_lookup.get_agent_data_from_environment()
        if self.agent_data:
            agent_name = self.agent_data.get('agent.name', 'Unknown Agent')
            print(f"👤 Free Agent integrated: {agent_name}")
        else:
            print("👤 No Free Agent specified (set FREEWORLD_CANDIDATE_ID/NAME for personalization)")
        
        # Initialize query location overrides
        self._query_location_overrides = QUERY_LOCATION_OVERRIDES
        
        print(f"🏗️ Pipeline v3 initialized (run: {self.run_id})")
        print(f"📊 Schema v{self.schema_info['version']} with {self.schema_info['total_fields']} fields")
        
        # Location to Market mapping - convert back from location to Airtable market name
        self._location_to_market = {
            "Houston, TX": "Houston",
            "Dallas, TX": "Dallas",
            "Berkeley, CA": "Bay Area",
            "Stockton, CA": "Stockton", 
            "Denver, CO": "Denver",
            "Las Vegas, NV": "Las Vegas",
            "Newark, NJ": "Newark",
            "Phoenix, AZ": "Phoenix",
            "Trenton, NJ": "Trenton",
            "Ontario, CA": "Inland Empire",
            "San Antonio, TX": "San Antonio",
            "Austin, TX": "Austin"
        }
    
    def _get_output_path(self) -> str:
        """Get output directory path"""
        current_dir = os.getcwd()
        return os.path.join(current_dir, "FreeWorld_Jobs")
    
    def run_memory_only_search(
        self,
        location: str,
        search_terms: str = "CDL Driver No Experience",
        radius: int = 50,
        max_jobs: int = 50,
        match_quality_filter: List[str] = None,
        fair_chance_only: bool = False,
        route_type_filter: List[str] = None,
        experience_level_filter: str = 'Any',
        coach_username: str = "",
        generate_pdf: bool = True,
        generate_csv: bool = True,
        hours: int = 72,
        text_search: bool = False,
        # NUCLEAR FIX: Add Free Agent parameters
        candidate_name: str = "",
        candidate_id: str = "",
        force_link_generation: bool = False
    ) -> Dict[str, Any]:
        """
        Memory-only search with advanced filtering - no API costs.
        Pulls from cached jobs across all sources (Indeed + Google).
        """
        
        print(f"💾 MEMORY-ONLY SEARCH: {location} (max {max_jobs} jobs)")
        print(f"🆔 Run ID: {self.run_id}")
        print("💰 Cost: $0.00 (no API calls)")
        
        # NUCLEAR FIX: Populate agent data from parameters for memory-only search
        if candidate_name or candidate_id or coach_username:
            print(f"🔍 Memory search agent data: candidate='{candidate_name}', coach='{coach_username}'")
            if not self.agent_data:
                self.agent_data = {}
            if candidate_name:
                self.agent_data['agent.name'] = candidate_name
                name_parts = candidate_name.strip().split()
                self.agent_data['agent.first_name'] = name_parts[0] if name_parts else ''
                self.agent_data['agent.last_name'] = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            if candidate_id:
                self.agent_data['agent.uuid'] = candidate_id
            if coach_username:
                self.agent_data['agent.coach_username'] = coach_username
            print(f"✅ Updated agent_data for memory search: {candidate_name} (Coach: {coach_username})")
        
        # Track timing
        start_time = time.time()
        
        # Set default filters
        if match_quality_filter is None:
            match_quality_filter = ['good', 'so-so']
        if route_type_filter is None:
            route_type_filter = ['Local', 'OTR', 'Unknown']
        
        # For memory-only lookups, use the plain market/location string as-is.
        # Mapping to "City, ST" can be too specific and miss Supabase records
        # stored under market names (e.g., "Houston").
        query_location = location
        
        try:
            # Search memory database with filters (Supabase → Canonical preferred)
            print(f"🔍 Searching memory for: {search_terms} in {query_location}")
            print(f"   Filters: quality={match_quality_filter}, fair_chance={fair_chance_only}, routes={route_type_filter}")

            canonical_df = None
            try:
                # Prefer direct canonical memory retrieval via supabase_converter
                from supabase_converter import search_memory_jobs as sb_search
                days_back = max(1, int(hours // 24)) if isinstance(hours, (int, float)) else 3
                
                # Build search parameters dict for canonical DataFrame
                search_params = {
                    'location': location,
                    'route_filter': 'both',  # Default for memory search
                    'mode': 'memory',
                    'job_limit': max_jobs,
                    'radius': radius,
                    'exact_location': False,
                    'no_experience': True,
                    'force_fresh': False,
                    'business_rules': True,
                    'deduplication': True,
                    'experience_filter': True,
                    'model': 'gpt-4o-mini',
                    'batch_size': 25,
                    'sources': 'memory',
                    'strategy': 'balanced',
                    'coach_username': coach_username or ''
                }
                
                # Build agent parameters dict - pass PDF filters to Supabase query level
                agent_params = {
                    'fair_chance_only': fair_chance_only,
                    'route_type_filter': route_type_filter,  # Pass full list for Supabase filtering
                    'match_quality_filter': match_quality_filter
                }
                
                # DEBUG: Log filter parameters being sent to Supabase
                print(f"🔍 PIPELINE DEBUG: Sending filters to Supabase:")
                print(f"   route_type_filter: {route_type_filter}")
                print(f"   match_quality_filter: {match_quality_filter}")
                print(f"   fair_chance_only: {fair_chance_only}")
                print(f"   max_jobs limit: {max_jobs}")
                
                # Speed optimization: Pull only what we need instead of 3x over-fetch
                # Prioritizes most recent jobs that match filters for PDF
                canonical_df = sb_search(query_location, limit=max_jobs, days_back=days_back, 
                                       agent_params=agent_params, search_params=search_params)
                if canonical_df is not None and not canonical_df.empty:
                    print(f"🧠 Retrieved {len(canonical_df)} canonical memory jobs from Supabase")
            except Exception as e:
                print(f"⚠️ Supabase converter path failed: {e}")

            if canonical_df is None or canonical_df.empty:
                # Fallback: use JobMemoryDB and transform to canonical
                memory_jobs = self.memory_db.search_jobs(
                    search_terms=search_terms if text_search else None,
                    location=query_location,
                    radius=radius,
                    limit=max_jobs * 3,
                    hours=hours,
                    text_search=text_search
                )
                if not memory_jobs:
                    print("❌ No jobs found in memory database")
                    import pandas as pd
                    return {
                        'status': 'completed',
                        'jobs_df': pd.DataFrame(),  # Empty DataFrame for no results
                        'bypass_executed': True,  # Still success, just no results
                        'total_jobs': 0,
                        'quality_jobs': 0,
                        'files': {},
                        'timing': {
                            'total_time': time.time() - start_time
                        },
                        'source': 'memory_only'
                    }
                from canonical_transforms import transform_ingest_memory
                canonical_df = transform_ingest_memory(memory_jobs, self.run_id)
            
            print(f"📊 Found {len(canonical_df)} jobs in memory")
            
            # DISABLED AGAIN: Deduplication still causing one job issue  
            # canonical_df = self._stage4_deduplication(canonical_df)
            # print(f"🔄 After deduplication: {len(canonical_df)} jobs remaining")
            print(f"⚠️ Deduplication disabled again - still causing over-filtering")
            
            # Filters now applied at Supabase query level - no post-filtering needed for basic filters
            filtered_df = canonical_df.copy()
            print(f"✅ Using Supabase-level filtering - {len(filtered_df)} pre-filtered jobs retrieved")
            
            # Only keep experience level filter since it's not handled at Supabase level yet
            if experience_level_filter != 'Any' and 'rules.has_experience_req' in filtered_df.columns:
                if experience_level_filter == 'Entry Level':
                    filtered_df = filtered_df[filtered_df['rules.has_experience_req'] == False]
                elif experience_level_filter == 'Experienced':
                    filtered_df = filtered_df[filtered_df['rules.has_experience_req'] == True]
                print(f"   Experience filter ({experience_level_filter}): {len(filtered_df)} jobs after filtering")
            
            # Sort by quality, fair chance, and recency (newest good + fair chance jobs first)
            if 'ai.match' in filtered_df.columns:
                # Create priority score: Good + Fair Chance = highest priority
                def get_priority_score(row):
                    ai_match = str(row.get('ai.match', '')).lower()
                    fair_chance = str(row.get('ai.fair_chance', '')).lower()
                    
                    is_good = ai_match == 'good'
                    is_soso = ai_match == 'so-so'  
                    is_fair = 'fair_chance_employer' in fair_chance or fair_chance in ['true', 'yes', '1']
                    
                    if is_good and is_fair:
                        return 1  # Highest priority
                    elif is_good:
                        return 2
                    elif is_soso and is_fair:
                        return 3
                    elif is_soso:
                        return 4
                    else:
                        return 5  # Lowest priority
                
                filtered_df['_priority'] = filtered_df.apply(get_priority_score, axis=1)
                
                # Sort by priority, then by recency (use created_at or sys.scraped_at)
                time_col = 'sys.created_at' if 'sys.created_at' in filtered_df.columns else 'created_at' if 'created_at' in filtered_df.columns else 'sys.scraped_at'
                if time_col in filtered_df.columns:
                    filtered_df = filtered_df.sort_values(
                        by=['_priority', time_col],
                        ascending=[True, False]  # Lower priority score = higher priority, newest first
                    )
                else:
                    filtered_df = filtered_df.sort_values(by='_priority', ascending=True)
                
                filtered_df.drop(columns=['_priority'], inplace=True)
                print(f"📊 Sorted by priority: newest good + fair chance jobs first")
            
            # Take top N jobs for output
            final_df = filtered_df.head(max_jobs)

            print(f"✅ Final selection: {len(final_df)} jobs for output")

            # Smart link generation for memory searches - generate for jobs without tracking URLs
            print("🔗 Checking memory jobs for missing tracking URLs...")
            try:
                # Ensure meta.tracked_url column exists
                if 'meta.tracked_url' not in final_df.columns:
                    final_df['meta.tracked_url'] = ''
                
                # Find jobs without tracking URLs or with original URLs as placeholders
                jobs_without_tracking = final_df[
                    (final_df['meta.tracked_url'].fillna('') == '') |
                    (final_df['meta.tracked_url'] == final_df['source.url'])
                ]
                
                if len(jobs_without_tracking) > 0 or force_link_generation:
                    from link_tracker import LinkTracker
                    link_tracker = LinkTracker()
                    
                    if force_link_generation:
                        jobs_to_process = final_df
                        print(f"🔗 Force link generation enabled - processing all {len(jobs_to_process)} jobs")
                    else:
                        jobs_to_process = jobs_without_tracking
                        print(f"🔗 Generating tracking URLs for {len(jobs_to_process)} memory jobs without tracking")
                    
                    if link_tracker.is_available:
                        for idx, row in jobs_to_process.iterrows():
                            job_id = row['id.job']
                            original_url = row.get('source.url', '')
                            
                            if original_url and original_url.startswith('http'):
                                # Create meaningful tags for memory jobs
                                tags = ['source:memory']
                                if candidate_id:
                                    tags.append(f"candidate:{candidate_id}")
                                if coach_username:
                                    tags.append(f"coach:{coach_username}")
                                if row.get('meta.market'):
                                    tags.append(f"market:{row.get('meta.market')}")
                                if row.get('ai.match'):
                                    tags.append(f"match:{row.get('ai.match')}")
                                if row.get('ai.route_type'):
                                    tags.append(f"route:{row.get('ai.route_type')}")
                                
                                job_title = row.get('source.title', 'CDL Position')[:50]
                                tracked_url = link_tracker.create_short_link(
                                    original_url,
                                    title=f"Memory: {job_title}",
                                    tags=tags,
                                    candidate_id=candidate_id
                                )
                                
                                if tracked_url and tracked_url != original_url:
                                    final_df.at[idx, 'meta.tracked_url'] = tracked_url
                                    print(f"🔗 Generated tracking URL for {job_id[:8]}")
                                else:
                                    final_df.at[idx, 'meta.tracked_url'] = original_url
                                    print(f"⚠️ Using original URL for {job_id[:8]}")
                        
                        print(f"✅ Link generation complete for memory search")
                        
                        # Update Supabase with new tracking URLs
                        try:
                            tracking_updates = {}
                            for idx, row in jobs_to_process.iterrows():
                                job_id = row.get('id.job')
                                tracked_url = final_df.at[idx, 'meta.tracked_url']
                                if job_id and tracked_url and tracked_url != row.get('source.url', ''):
                                    tracking_updates[job_id] = tracked_url
                            
                            if tracking_updates:
                                success = self.memory_db.update_tracking_urls(tracking_updates)
                                if success:
                                    print(f"✅ Updated {len(tracking_updates)} tracking URLs in Supabase")
                                else:
                                    print(f"⚠️ Failed to update tracking URLs in Supabase")
                        except Exception as update_e:
                            print(f"⚠️ Error updating tracking URLs in Supabase: {update_e}")
                    else:
                        print("⚠️ LinkTracker not available - using original URLs")
                        final_df.loc[jobs_to_process.index, 'meta.tracked_url'] = jobs_to_process['source.url']
                else:
                    print("ℹ️ All memory jobs already have tracking URLs")
                
                # Final fallback - ensure no empty tracking URLs
                missing_urls = final_df['meta.tracked_url'].fillna('') == ''
                if missing_urls.any():
                    final_df.loc[missing_urls, 'meta.tracked_url'] = final_df.loc[missing_urls, 'source.url']
                    print(f"🔄 Fallback: filled {missing_urls.sum()} remaining empty tracking URLs")
                    
            except Exception as e:
                print(f"⚠️ Link generation error: {e}")
                # Emergency fallback
                if 'meta.tracked_url' not in final_df.columns:
                    final_df['meta.tracked_url'] = ''
                missing_urls = final_df['meta.tracked_url'].fillna('') == ''
                final_df.loc[missing_urls, 'meta.tracked_url'] = final_df.loc[missing_urls, 'source.url']

            # Generate outputs
            files = {}

            # Sanctify canonical DF before exporting
            try:
                from jobs_schema import sanctify_dataframe
                final_df = sanctify_dataframe(final_df)
            except Exception:
                pass

            if generate_csv and len(final_df) > 0:
                try:
                    csv_path = self._generate_csv(final_df, final_df, location)
                except Exception:
                    csv_path = self._generate_csv_output(final_df, location, 'memory_only')
                files['csv'] = csv_path
                print(f"📄 CSV exported: {csv_path}")

            if generate_pdf and len(final_df) > 0:
                try:
                    # Pass through known coach/candidate context if available
                    cand_name_param = ''
                    cand_id_param = ''
                    try:
                        cand_name_param = (self.agent_data.get('agent.name') if self.agent_data else '') or os.getenv('FREEWORLD_CANDIDATE_NAME', '')
                        cand_id_param = (self.agent_data.get('agent.uuid') if self.agent_data else '') or os.getenv('FREEWORLD_CANDIDATE_ID', '')
                    except Exception:
                        cand_name_param = os.getenv('FREEWORLD_CANDIDATE_NAME', '')
                        cand_id_param = os.getenv('FREEWORLD_CANDIDATE_ID', '')

                    pdf_path = self._generate_pdf(
                        final_df,
                        location,
                        custom_location="",
                        coach_name=coach_username,
                        coach_username=coach_username,
                        candidate_name=cand_name_param,
                        candidate_id=cand_id_param
                    )
                except Exception:
                    pdf_path = self._generate_pdf_output(final_df, location, coach_username or 'Memory Search')
                files['pdf'] = pdf_path
                print(f"📄 PDF generated: {pdf_path}")
            
            # Track search analytics (no Airtable sync for memory-only)
            # DISABLED: Analytics tracking commented out - table doesn't exist
            # if coach_username:
            #     self._track_memory_search_analytics(
            #         search_terms, query_location, len(final_df), coach_username
            #     )
            
            # NUCLEAR FIX: Populate Free Agent fields in final DataFrame before returning
            if self.agent_data and len(final_df) > 0:
                final_df = self._populate_agent_fields(final_df)
            
            total_time = time.time() - start_time
            
            # Calculate efficiency metrics for Memory Only search  
            memory_efficiency = 100.0  # Memory search is 100% memory efficient
            total_cost = 0.0  # Memory search has no API costs
            cost_per_quality_job = 0.0  # No cost per job for memory search
            
            # Format timing display
            if total_time >= 60:
                minutes = int(total_time // 60)
                seconds = total_time % 60
                print(f"⏱️ Total processing time: {minutes}m {seconds:.1f}s")
            else:
                print(f"⏱️ Total processing time: {total_time:.1f}s")
            print(f"💰 Total cost: ${total_cost:.3f}")
            print(f"💰 Cost per quality job: ${cost_per_quality_job:.3f}")
            print(f"🧠 Memory efficiency: {memory_efficiency:.1f}%")
            
            return {
                'status': 'completed',
                'jobs_df': final_df,  # Return the DataFrame for portal wrapper
                'bypass_executed': True,  # Signal success to wrapper
                'total_jobs': len(canonical_df),
                'filtered_jobs': len(filtered_df),
                'quality_jobs': len(final_df),
                'files': files,
                'timing': {
                    'total_time': total_time
                },
                'source': 'memory_only',
                # Add missing efficiency metrics
                'memory_efficiency': memory_efficiency,
                'total_cost': total_cost,
                'cost_per_quality_job': cost_per_quality_job,
                'filters_applied': {
                    'match_quality': match_quality_filter,
                    'fair_chance_only': fair_chance_only,
                    'route_types': route_type_filter,
                    'experience_level': experience_level_filter
                }
            }
            
        except Exception as e:
            print(f"❌ Memory search failed: {e}")
            return {
                'status': 'error',
                'jobs_df': None,  # No DataFrame for errors
                'bypass_executed': False,  # Signal failure to wrapper
                'error': str(e),
                'total_jobs': 0,
                'quality_jobs': 0,
                'files': {},
                'timing': {
                    'total_time': time.time() - start_time
                },
                'source': 'memory_only'
            }
    
    # DISABLED: Analytics tracking method - table doesn't exist in Supabase schema
    # def _track_memory_search_analytics(self, search_terms: str, location: str, job_count: int, coach: str):
    #     """Track memory search for analytics (Supabase only, no costs)"""
    #     try:
    #         from supabase_utils import get_client
    #         client = get_client()
    #         if client:
    #             analytics_record = {
    #                 'search_type': 'memory_only',
    #                 'search_terms': search_terms,
    #                 'location': location,
    #                 'job_count': job_count,
    #                 'coach': coach,
    #                 'cost': 0.0,
    #                 'timestamp': datetime.now().isoformat(),
    #                 'run_id': self.run_id
    #             }
    #             client.table('search_analytics').insert(analytics_record).execute()
    #     except Exception as e:
    #         print(f"⚠️ Analytics tracking failed: {e}")
    
    def _generate_csv_output(self, df: pd.DataFrame, location: str, source: str) -> str:
        """Generate CSV output file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{location.replace(', ', '_').replace(' ', '_')}_{source}_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Export relevant columns for CSV
        export_cols = [
            'source.title', 'source.company', 'source.location', 'ai.summary',
            'ai.match', 'ai.route_type', 'source.url', 'norm.salary_display'
        ]
        available_cols = [col for col in export_cols if col in df.columns]
        df[available_cols].to_csv(filepath, index=False)
        
        return filepath
    
    def _generate_pdf_output(self, df: pd.DataFrame, location: str, coach_name: str) -> str:
        """Generate PDF output file"""
        try:
            from fpdf_pdf_generator import generate_fpdf_job_cards
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{location.replace(', ', '_').replace(' ', '_')}_memory_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            generate_fpdf_job_cards(
                jobs_df=df,
                output_path=filepath,
                market=location,
                coach_name=coach_name
            )
            
            return filepath
        except Exception as e:
            print(f"⚠️ PDF generation failed: {e}")
            return ""
    
    def run_complete_pipeline(
        self,
        location: str,
        mode_info: Dict[str, Any],
        search_terms: str = "CDL Driver No Experience",
        route_filter: str = "both",
        push_to_airtable: bool = False,
        force_fresh: bool = False,
        force_fresh_classification: bool = False,
        force_memory_only: bool = False,
        force_link_generation: bool = False,
        hardcoded_market: str = None,
        custom_location: str = None,
        generate_pdf: bool = True,
        generate_csv: bool = True,
        generate_html: bool = True, # New parameter
        radius: int = 50,
        no_experience: bool = True,
        filter_settings: Dict[str, bool] = None,
        search_sources: Dict[str, bool] = None,
        search_strategy: str = "balanced",
        coach_name: str = "",
        coach_username: str = "",
        candidate_name: str = "",
        candidate_id: str = ""
    ) -> Dict[str, Any]:
        """
        Execute complete pipeline with single canonical DataFrame
        
        Returns:
            Results dictionary with file paths and statistics
        """
        
        print(f"🚀 PIPELINE V3 START: {location} ({mode_info.get('limit', 0)} jobs)")
        print(f"🆔 Run ID: {self.run_id}")
        
        # Override agent data if provided in params (Streamlit mode)
        if candidate_name or candidate_id or coach_name or coach_username:
            print(f"🔍 Overriding agent data from params: candidate='{candidate_name}', coach='{coach_name}'")
            # Update agent_data with params (overrides environment variables)
            if not self.agent_data:
                self.agent_data = {}
            if candidate_name:
                self.agent_data['agent.name'] = candidate_name
                # Extract first/last name from full name
                name_parts = candidate_name.strip().split()
                self.agent_data['agent.first_name'] = name_parts[0] if name_parts else ''
                self.agent_data['agent.last_name'] = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            if candidate_id:
                self.agent_data['agent.uuid'] = candidate_id
            if coach_name:
                self.agent_data['agent.coach_name'] = coach_name
            if coach_username:
                self.agent_data['agent.coach_username'] = coach_username
            print(f"✅ Updated agent_data with params: {candidate_name} (Coach: {coach_name})")
        
        # Track pipeline timing
        pipeline_start_time = time.time()
        
        # Store custom location flag for market assignment
        self._is_custom_location = custom_location is not None
        
        # Initialize canonical DataFrame
        canonical_df = build_empty_df()
        
        try:
            # STAGE 1: INGESTION
            canonical_df = self._stage1_ingestion(
                canonical_df, location, mode_info, search_terms, 
                route_filter, force_fresh, force_memory_only,
                radius=radius,
                no_experience=no_experience,
                search_sources=search_sources,
                search_strategy=search_strategy
            )
            self._checkpoint_data(canonical_df, "01_ingestion")
            
            # SAFETY: Export CSV after ingestion to prevent job loss
            if not canonical_df.empty:
                ingestion_csv = os.path.join(self.parquet_dir, f"SAFETY_01_ingestion_{self.run_id}.csv")
                canonical_df.to_csv(ingestion_csv, index=False)
                print(f"💾 Safety export: {len(canonical_df)} jobs saved to {os.path.basename(ingestion_csv)}")
            
            # STAGE 2: NORMALIZATION
            canonical_df = self._stage2_normalization(canonical_df)
            self._checkpoint_data(canonical_df, "02_normalization")
            
            # STAGE 3: BUSINESS RULES
            canonical_df = self._stage3_business_rules(canonical_df, hardcoded_market or location, filter_settings)
            self._checkpoint_data(canonical_df, "03_business_rules")
            
            # STAGE 4: DEDUPLICATION
            canonical_df = self._stage4_deduplication(canonical_df, filter_settings=filter_settings)
            self._checkpoint_data(canonical_df, "04_deduplication")
            
            # STAGE 5: AI CLASSIFICATION
            canonical_df = self._stage5_ai_classification(canonical_df, force_fresh_classification)
            self._checkpoint_data(canonical_df, "05_classification")
            
            # SAFETY: Export CSV after classification - CRITICAL for paid jobs!
            if not canonical_df.empty:
                classification_csv = os.path.join(self.parquet_dir, f"SAFETY_05_classified_{self.run_id}.csv")
                canonical_df.to_csv(classification_csv, index=False)
                quality_count = len(canonical_df[canonical_df['ai.match'].isin(['good', 'so-so'])])
                print(f"💾 CRITICAL SAFETY: {len(canonical_df)} total jobs ({quality_count} quality) saved to {os.path.basename(classification_csv)}")
            
            # STAGE 5.5: ROUTE (RULES) - derive route type via rules-based classifier
            canonical_df = self._stage5_5_route_rules(canonical_df)
            self._checkpoint_data(canonical_df, "05_5_route_rules")

            # STAGE 6: ROUTING
            canonical_df = self._stage6_routing(canonical_df, route_filter)
            self._checkpoint_data(canonical_df, "06_routing")
            
            # SAFETY: Export final processed CSV BEFORE output generation
            if not canonical_df.empty:
                final_csv = os.path.join(self.parquet_dir, f"SAFETY_FINAL_{self.run_id}.csv")
                canonical_df.to_csv(final_csv, index=False)
                quality_final = len(canonical_df[canonical_df['ai.match'].isin(['good', 'so-so'])])
                print(f"💾 FINAL SAFETY BACKUP: {len(canonical_df)} jobs ({quality_final} quality) → {os.path.basename(final_csv)}")
            
            # STAGE 7: OUTPUT GENERATION
            results = self._stage7_output(
                canonical_df, hardcoded_market or location, custom_location,
                generate_pdf, generate_csv, generate_html, force_memory_only
            )
            
            # STAGE 8: DATA STORAGE
            self._stage8_storage(canonical_df, push_to_airtable)
            
            # Final checkpoint - complete pipeline state
            self._checkpoint_data(canonical_df, "99_complete")
            
            # Calculate pipeline timing
            pipeline_end_time = time.time()
            processing_time = pipeline_end_time - pipeline_start_time
            
            # Add pipeline statistics to results
            results.update(self._generate_pipeline_stats(canonical_df, mode_info, processing_time))

            # Attach final canonical DataFrame for UI/direct callers
            try:
                results['jobs_df'] = canonical_df
                results['success'] = True
            except Exception:
                pass
            
            print(f"✅ PIPELINE V3 COMPLETE: {results['summary']}")
            # Format processing time as minutes and seconds
            if processing_time >= 60:
                minutes = int(processing_time // 60)
                seconds = processing_time % 60
                print(f"⏱️ Total processing time: {minutes}m {seconds:.1f}s")
            else:
                print(f"⏱️ Total processing time: {processing_time:.1f}s")
            print(f"💰 Total cost: ${results['total_cost']:.3f}")
            print(f"💰 Cost per quality job: ${results['cost_per_quality_job']:.3f}")
            print(f"🧠 Memory efficiency: {results['memory_efficiency']:.1f}%")
            return results
            
        except Exception as e:
            print(f"❌ Pipeline v3 failed: {e}")
            # Save error state for debugging
            self._checkpoint_data(canonical_df, "error")
            raise
    
    def _extract_clean_url(self, url: str) -> str:
        """Extract clean URL for deduplication (remove tracking params)"""
        import pandas as pd
        if pd.isna(url) or not url or url == '':
            return ''
        
        try:
            from urllib.parse import urlparse, parse_qs, urlencode
            
            # For Indeed URLs, extract job key
            if 'indeed.com' in url and 'jk=' in url:
                import re
                match = re.search(r'jk=([a-zA-Z0-9]+)', url)
                if match:
                    return f"indeed_{match.group(1)}"
            
            # For other URLs, use the full path without query params
            parsed = urlparse(url)
            
            # Keep only essential params (like job ID)
            if parsed.query:
                params = parse_qs(parsed.query)
                essential_params = ['jk', 'jobid', 'id', 'job_id']
                clean_params = {k: v for k, v in params.items() 
                               if k.lower() in essential_params}
                
                if clean_params:
                    clean_query = urlencode(clean_params, doseq=True)
                    return f"{parsed.netloc}{parsed.path}?{clean_query}"
            
            # Return netloc + path (without query)
            return f"{parsed.netloc}{parsed.path}"
            
        except Exception:
            # Fallback: return original URL if parsing fails
            return url
    
    def _stage1_ingestion(
        self, 
        df: pd.DataFrame, 
        location: str, 
        mode_info: Dict[str, Any],
        search_terms: str,
        route_filter: str,
        force_fresh: bool,
        force_memory_only: bool,
        radius: int = 50,
        no_experience: bool = True,
        search_sources: Dict[str, bool] = None,
        search_strategy: str = "balanced"
    ) -> pd.DataFrame:
        """Stage 1: Ingest data from APIs and memory database"""
        
        print("📥 STAGE 1: INGESTION")
        
        # Convert market to location format for Indeed scraping ONLY
        # E.g. "Dallas" → "Dallas, TX". Keep custom locations as-is.
        # IMPORTANT: Do not use this converted value for meta.market or storage.
        query_location = MARKET_TO_LOCATION.get(location, location)
        
        # Apply any additional overrides if needed
        final_location = self._query_location_overrides.get(query_location, query_location)
        
        # VALIDATION: Log what we're receiving to catch upstream issues
        print(f"   📍 Pipeline location input: '{location}' (custom: {getattr(self, '_is_custom_location', False)})")
        if final_location != location:
            print(f"   📍 Market to location conversion: {location} → {final_location}")
        
        query_location = final_location
        
        # Smart Credit / Bypass logic: may reduce scraping or fully bypass
        memory_pre_df = build_empty_df()
        scrape_limit_override = None
        if not force_fresh:
            try:
                # Use query_location for Smart Credit location-based lookups
                if force_memory_only:
                    print(f"🔒 INITIATING FORCE MEMORY-ONLY BYPASS for {query_location}")
                    # Force FULL_BYPASS for memory-only searches
                    decision = self.bypass_system.force_full_bypass(query_location, route_filter=route_filter)
                    print(f"🔒 FORCE BYPASS DECISION: {decision.get('bypass_type')} - {decision.get('reason')}")
                else:
                    decision = self.bypass_system.execute_bypass(query_location, mode_info, route_filter=route_filter)
                bypass_type = decision.get('bypass_type')
                # Summarize Smart Credit decision visibly in pipeline logs
                avail = decision.get('jobs_found', 0)
                target = mode_info.get('limit', 0)
                if force_memory_only:
                    print(f"🔒 FORCED MEMORY-ONLY: {bypass_type} | available_quality={avail}")
                else:
                    print(f"🧮 Smart Credit decision: {bypass_type} | available_quality={avail} | target={target}")
                if bypass_type == 'FULL_BYPASS' and decision.get('bypass_executed'):
                    print(f"🚀 BYPASS: Using available quality jobs from memory")
                    jobs_df = decision.get('jobs_df')
                    if jobs_df is not None and not jobs_df.empty:
                        try:
                            breakdown = jobs_df['match'].value_counts().to_dict()
                            good = breakdown.get('good', 0)
                            so_so = breakdown.get('so-so', 0)
                            print(f"   🔎 Memory quality available: {len(jobs_df)} (good={good}, so-so={so_so})")
                        except Exception:
                            print(f"   🔎 Memory quality available: {len(jobs_df)}")
                        memory_jobs = jobs_df.to_dict('records')
                        memory_pre_df = transform_ingest_memory(memory_jobs, self.run_id)
                        print(f"✅ Ingested {len(memory_pre_df)} jobs from memory (FULL BYPASS)")
                        
                        # Populate Free Agent fields for FULL_BYPASS memory jobs
                        if self.agent_data and len(memory_pre_df) > 0:
                            memory_pre_df = self._populate_agent_fields(memory_pre_df)
                        
                        # Apply search context before returning memory-only DataFrame
                        memory_pre_df = self._apply_search_context(
                            memory_pre_df,
                            location=location,
                            final_location=query_location,
                            mode_info=mode_info,
                            search_terms=search_terms,
                            route_filter=route_filter,
                            radius=radius,
                            no_experience=no_experience,
                            force_fresh=force_fresh,
                            force_memory_only=force_memory_only,
                            search_sources=search_sources,
                            search_strategy=search_strategy
                        )
                        # Return memory-only DataFrame - let main pipeline handle files
                        return memory_pre_df
                    else:
                        # No jobs found in memory - return empty DataFrame with context fields
                        empty_df = build_empty_df()
                        empty_df = self._apply_search_context(
                            empty_df,
                            location=location,
                            final_location=query_location,
                            mode_info=mode_info,
                            search_terms=search_terms,
                            route_filter=route_filter,
                            radius=radius,
                            no_experience=no_experience,
                            force_fresh=force_fresh,
                            force_memory_only=force_memory_only,
                            search_sources=search_sources,
                            search_strategy=search_strategy
                        )
                        return empty_df
                elif bypass_type == 'SMART_CREDIT' and decision.get('bypass_executed'):
                    # Prepare memory pre-load and set reduced scrape limit
                    jobs_df = decision.get('jobs_df')
                    if jobs_df is not None and not jobs_df.empty:
                        try:
                            breakdown = jobs_df['match'].value_counts().to_dict()
                            good = breakdown.get('good', 0)
                            so_so = breakdown.get('so-so', 0)
                            print(f"   💡 Smart Credit memory: {len(jobs_df)} (good={good}, so-so={so_so})")
                        except Exception:
                            print(f"   💡 Smart Credit memory: {len(jobs_df)}")
                        memory_jobs = jobs_df.to_dict('records')
                        memory_pre_df = transform_ingest_memory(memory_jobs, self.run_id)
                    scrape_limit_override = max(0, int(decision.get('scrape_jobs_needed', 0)))
                    print(f"   💡 Reducing scrape target to {scrape_limit_override} jobs (from {mode_info.get('limit', 0)})")
                else:
                    # Explicitly log full scraping path when no reduction occurs
                    print(f"   🔎 Smart Credit: no reduction — scraping full target {target} jobs")
            except Exception as e:
                print(f"⚠️ Smart Credit decision failed, continuing with full scraping: {e}")
                import traceback
                traceback.print_exc()
        
        # Regular flow: scrape fresh + get memory
        fresh_jobs = []
        google_jobs = []
        memory_jobs = []
        
        # Set default sources if not provided
        if search_sources is None:
            search_sources = {'indeed': True, 'google': False}  # Default to Indeed only for backwards compatibility
            
        print(f"🔍 Sources enabled: Indeed={search_sources.get('indeed', False)}, Google={search_sources.get('google', False)}")
        
        # Get fresh jobs from enabled sources
        # Determine scrape limit (may be reduced by Smart Credit)
        effective_limit = scrape_limit_override if scrape_limit_override is not None else mode_info['limit']
        
        # Google Jobs API (if enabled)
        self.google_api_cost = 0.0
        if effective_limit > 0 and search_sources.get('google', False):
            print(f"🔍 Searching Google Jobs API for {effective_limit} jobs...")
            try:
                google_result = self.scraper.search_google_jobs_api(
                    search_terms=search_terms,
                    location=query_location, 
                    radius=radius,
                    limit=effective_limit
                )
                google_jobs = google_result['jobs'] if isinstance(google_result, dict) else google_result
                self.google_api_cost = google_result.get('cost', 0.0) if isinstance(google_result, dict) else 0.0
                queries_executed = google_result.get('queries_executed', 1) if isinstance(google_result, dict) else 1
                print(f"✅ Retrieved {len(google_jobs)} jobs from Google (${self.google_api_cost:.3f} for {queries_executed} queries)")
            except Exception as e:
                print(f"⚠️ Google Jobs API failed: {e}")
        
        # Indeed API (if enabled)
        if effective_limit > 0 and search_sources.get('indeed', False):
            print(f"🔍 Searching Indeed API for {effective_limit} jobs...")
            try:
                # Build Indeed URL for search
                encoded_terms = search_terms.replace(' ', '+')
                encoded_location = query_location.replace(' ', '+').replace(',', '%2C')
                indeed_url = f"https://www.indeed.com/jobs?q={encoded_terms}&l={encoded_location}&radius={int(radius)}"
                if no_experience:
                    # Add "no experience" search context. 'sc' param encoding retained from v2
                    indeed_url += "&sc=0kf%3Aattr%28D7S5D%29%3B"
                
                search_params = {
                    'location': query_location,
                    'search_terms': search_terms,
                    'search_indeed': True,  # Enable Indeed search
                    'indeed_url': indeed_url,
                    'radius': radius,
                    'no_experience': no_experience
                }
                
                # Set mode info with proper field names for scraper
                scraper_mode_info = {
                    'indeed_limit': effective_limit,
                    'limit': effective_limit
                }
                
                result = self.scraper.run_full_search(search_params, scraper_mode_info)
                # Handle list of raw Indeed jobs from scraper
                if isinstance(result, list):
                    fresh_jobs = result  # Already raw Indeed jobs
                else:
                    # Fallback for other formats
                    fresh_jobs = result.get('jobs', []) if isinstance(result, dict) else []
                print(f"✅ Retrieved {len(fresh_jobs)} jobs from Indeed")
            except Exception as e:
                print(f"⚠️ Indeed API failed: {e}")
        
        # Combine all fresh jobs
        all_fresh_jobs = fresh_jobs + google_jobs
        print(f"🔄 Combined total: {len(all_fresh_jobs)} fresh jobs")
        
        # Get memory jobs for all sources
        if all_fresh_jobs:
            job_ids = [self._generate_job_id_from_raw(job) for job in all_fresh_jobs]
            memory_lookup = self.memory_db.check_job_memory(job_ids, hours=72)
            
            if memory_lookup:
                memory_jobs = list(memory_lookup.values())
                print(f"✅ Found {len(memory_jobs)} jobs in memory")
                # Print how many of these are quality classifications
                try:
                    matches = [j.get('match') or j.get('match_level') for j in memory_jobs]
                    good = sum(1 for m in matches if m == 'good')
                    so_so = sum(1 for m in matches if m == 'so-so')
                    bad = sum(1 for m in matches if m == 'bad')
                    total_quality = good + so_so
                    print(f"   🔎 Memory classification breakdown: quality={total_quality} (good={good}, so-so={so_so}), bad={bad}")
                except Exception:
                    pass
        
        # Transform and merge data from all sources
        indeed_df = transform_ingest_outscraper(fresh_jobs, self.run_id) if fresh_jobs else build_empty_df()
        google_df = transform_ingest_google(google_jobs, self.run_id) if google_jobs else build_empty_df()
        memory_df = transform_ingest_memory(memory_jobs, self.run_id) if memory_jobs else build_empty_df()
        
        # Include any pre-loaded memory rows from Smart Credit
        if len(memory_pre_df) > 0:
            memory_df = pd.concat([memory_pre_df, memory_df], ignore_index=True) if len(memory_df) > 0 else memory_pre_df
        
        # Merge all dataframes: Indeed, Google, and Memory
        df = indeed_df
        if len(google_df) > 0:
            df = merge_dataframes(df, google_df)
        if len(memory_df) > 0:
            df = merge_dataframes(df, memory_df)
        
        print(f"✅ Total ingested: {len(df)} jobs (Indeed={len(indeed_df)}, Google={len(google_df)}, Memory={len(memory_df)})")
        
        # Populate Free Agent fields after ingestion
        if self.agent_data and len(df) > 0:
            df = self._populate_agent_fields(df)

        # Apply search context to the combined ingestion DataFrame
        df = self._apply_search_context(
            df,
            location=location,
            final_location=query_location,
            mode_info=mode_info,
            search_terms=search_terms,
            route_filter=route_filter,
            radius=radius,
            no_experience=no_experience,
            force_fresh=force_fresh,
            force_memory_only=force_memory_only,
            search_sources=search_sources,
            search_strategy=search_strategy
        )

        return df

    def _apply_search_context(
        self,
        df: pd.DataFrame,
        location: str,
        final_location: str,
        mode_info: Dict[str, Any],
        search_terms: str,
        route_filter: str,
        radius: int,
        no_experience: bool,
        force_fresh: bool,
        force_memory_only: bool,
        search_sources: Dict[str, bool] = None,
        search_strategy: str = "balanced"
    ) -> pd.DataFrame:
        """Populate search.* and meta.* context fields to satisfy schema and analytics."""
        try:
            # Build sources label (comma-separated)
            sources_label = ''
            if isinstance(search_sources, dict):
                enabled = [k for k, v in search_sources.items() if v]
                sources_label = ','.join(enabled)
            # Coach username from env if available
            coach_username = os.getenv('FREEWORLD_COACH_USERNAME', '')
            # Determine job limit from mode
            job_limit = int(mode_info.get('limit', 100) or 100)
            # Assign fields
            fields = {
                'search.location': final_location,
                'search.custom_location': final_location if self._is_custom_location else '',
                'search.route_filter': route_filter,
                'search.mode': str(mode_info.get('mode', 'sample')),
                'search.job_limit': job_limit,
                'search.radius': int(radius or 0),
                'search.exact_location': bool(radius == 0),
                'search.no_experience': bool(no_experience),
                'search.force_fresh': bool(force_fresh),
                'search.memory_only': bool(force_memory_only),
                'search.business_rules': True,
                'search.deduplication': True,
                'search.experience_filter': True,
                'search.model': 'gpt-4o-mini',
                'search.batch_size': 25,
                'search.sources': sources_label,
                'search.strategy': search_strategy,
                'search.coach_username': coach_username,
                'meta.search_terms': search_terms,
                'meta.query': search_terms,
            }
            df = df.assign(**fields)
        except Exception as e:
            print(f"⚠️ Failed to apply search context: {e}")
        return df
    
    def _stage2_normalization(self, df: pd.DataFrame) -> pd.DataFrame:
        """Stage 2: Normalize and clean all job data (both fresh and memory)"""
        print("🧹 STAGE 2: NORMALIZATION")
        total = len(df)
        if total == 0:
            print("✅ No jobs to normalize")
            return df
        # Normalize entire DataFrame to ensure norm.* fields exist for business rules/dedup
        df = transform_normalize(df)
        print(f"✅ Normalized job data and extracted structured fields")
        return df
    
    def _stage3_business_rules(self, df: pd.DataFrame, market: str, filter_settings: Dict[str, bool] = None) -> pd.DataFrame:
        """Stage 3: Apply business rules and generate dedup keys"""
        
        print("📋 STAGE 3: BUSINESS RULES")
        
        # Apply market assignment
        df = apply_market_assignment(df, market, is_custom_location=self._is_custom_location)
        
        # Apply business rules
        df = transform_business_rules(df, filter_settings=filter_settings or {})
        
        # Count rule violations
        rules_stats = {
            'owner_op': (df['rules.is_owner_op'] == True).sum(),
            'school_bus': (df['rules.is_school_bus'] == True).sum(),
            'spam': (df['rules.is_spam_source'] == True).sum()
        }
        
        print(f"✅ Business rules applied:")
        for rule, count in rules_stats.items():
            if count > 0:
                print(f"   🚫 {rule}: {count} jobs")
        
        return df
    
    def _stage4_deduplication(self, df: pd.DataFrame, filter_settings: Dict[str, bool] = None) -> pd.DataFrame:
        """Stage 4: Remove duplicate jobs"""
        if filter_settings is None:
            filter_settings = {'r1_dedup': True, 'r2_dedup': True}
        
        print("🔄 STAGE 4: DEDUPLICATION") 
        
        initial_count = len(df)
        
        # Debug job IDs before deduplication
        job_id_counts = df['id.job'].value_counts()
        unique_job_ids = len(job_id_counts)
        most_common_id = job_id_counts.iloc[0] if len(job_id_counts) > 0 else 0
        print(f"🔍 Dedup Debug: {unique_job_ids} unique job IDs, most common appears {most_common_id} times")
        if most_common_id > 10:  # If any job_id appears more than 10 times, show it
            print(f"🔍 Most common job_id: {job_id_counts.index[0]} (appears {most_common_id} times)")
        
        # Generate clean URLs for deduplication
        print("🔗 Generating clean URLs for deduplication")
        df['clean_apply_url'] = df.apply(lambda x: self._extract_clean_url(
            x.get('source.url', '')
        ), axis=1)
        
        # Remove exact duplicates by job_id (fresh wins over memory)
        df = df.drop_duplicates(subset=['id.job'], keep='last')
        exact_dupes_removed = initial_count - len(df)
        
        # R1 Deduplication (company + title + market)
        r1_dupes_removed = 0
        if filter_settings.get('r1_dedup', True):
            r1_groups = df.groupby('rules.duplicate_r1')
            
            for group_key, group_df in r1_groups:
                if len(group_df) > 1:
                    # Keep one representative, mark others as filtered
                    keep_idx = group_df.index[0]  # Keep first
                    dupe_indices = group_df.index[1:]
                    
                    df.loc[dupe_indices, 'route.final_status'] = 'filtered: R1 collapse (company+title+market)'
                    df.loc[dupe_indices, 'route.filtered'] = True
                    df.loc[dupe_indices, 'route.ready_for_ai'] = False  # Duplicates don't need classification
                    r1_dupes_removed += len(dupe_indices)
        else:
            print("⚠️  R1 deduplication disabled by filter settings")
        
        # R2 Deduplication (company + location - less aggressive than market)
        r2_dupes_removed = 0
        if filter_settings.get('r2_dedup', True):
            r2_groups = df.groupby('rules.duplicate_r2')
            
            for group_key, group_df in r2_groups:
                if len(group_df) > 1:
                    # Only dedupe if not already filtered by R1
                    unfiltered = group_df[group_df['route.filtered'] != True]
                    if len(unfiltered) > 1:
                        keep_idx = unfiltered.index[0]
                        dupe_indices = unfiltered.index[1:]
                        
                        df.loc[dupe_indices, 'route.final_status'] = 'filtered: R2 collapse (company+location)'
                        df.loc[dupe_indices, 'route.filtered'] = True
                        df.loc[dupe_indices, 'route.ready_for_ai'] = False  # Duplicates don't need classification
                        r2_dupes_removed += len(dupe_indices)
        else:
            print("⚠️  R2 deduplication disabled by filter settings")
        
        # URL-based deduplication (NEW - to catch same job from different sources)
        url_dupes_removed = 0
        if filter_settings.get('url_dedup', True):
            # Extract clean URLs for comparison
            df['clean_apply_url'] = df.apply(lambda x: self._extract_clean_url(
                x.get('source.url', '')
            ), axis=1)
            
            # Group by clean URL
            url_groups = df[df['clean_apply_url'] != ''].groupby('clean_apply_url')
            
            for url, group_df in url_groups:
                if len(group_df) > 1:
                    # Only dedupe if not already filtered
                    unfiltered = group_df[group_df['route.filtered'] != True]
                    if len(unfiltered) > 1:
                        # Sort by source preference: Indeed first (richer data)
                        sorted_df = unfiltered.sort_values(['id.source'], key=lambda x: x.map({'indeed': 0, 'google': 1}))
                        
                        keep_idx = sorted_df.index[0]  # Keep Indeed version if available
                        dupe_indices = sorted_df.index[1:]
                        
                        df.loc[dupe_indices, 'route.final_status'] = 'filtered: URL duplicate (same job posting)'
                        df.loc[dupe_indices, 'route.filtered'] = True
                        df.loc[dupe_indices, 'route.ready_for_ai'] = False
                        url_dupes_removed += len(dupe_indices)
        else:
            print("⚠️  URL deduplication disabled by filter settings")
        
        print(f"✅ Deduplication complete:")
        print(f"   🗑️ Exact duplicates: {exact_dupes_removed}")
        print(f"   🗑️ R1 duplicates: {r1_dupes_removed}")
        print(f"   🗑️ R2 duplicates: {r2_dupes_removed}")
        print(f"   🗑️ URL duplicates: {url_dupes_removed}")
        
        # Update stage after deduplication
        try:
            df = df.assign(**{
                'route.stage': 'deduped',
                'sys.updated_at': datetime.now().isoformat()
            })
        except Exception:
            pass
        
        # ACTUALLY REMOVE filtered duplicates from DataFrame (don't just mark them)
        initial_total = len(df)
        df_clean = df[df.get('route.filtered', False) != True]  # Keep only non-filtered jobs
        final_total = len(df_clean)
        actually_removed = initial_total - final_total
        
        if actually_removed > 0:
            print(f"🗑️ REMOVED {actually_removed} filtered duplicate jobs from DataFrame")
        
        return df_clean
    
    def _stage5_ai_classification(self, df: pd.DataFrame, force_fresh_classification: bool = False) -> pd.DataFrame:
        """Stage 5: AI classification of jobs"""
        
        print("🤖 STAGE 5: AI CLASSIFICATION")
        
        # Get jobs that need AI classification
        needs_ai = view_ready_for_ai(df)
        fresh_unclassified = needs_ai[needs_ai['sys.is_fresh_job'] == True]

        # Cost saver: check Supabase memory before classifying to avoid rework
        if force_fresh_classification:
            print("🆕 Force fresh classification enabled - bypassing AI classification cache")
        
        if len(fresh_unclassified) > 0 and not force_fresh_classification:
            try:
                job_ids_to_check = list(fresh_unclassified['id.job'].dropna().astype(str).unique())
                memory_lookup = self.memory_db.check_job_memory(job_ids_to_check, hours=720)  # 30 days window
                if memory_lookup:
                    # Transform memory records and merge to reuse AI fields
                    memory_jobs = list(memory_lookup.values())
                    mem_df = transform_ingest_memory(memory_jobs, self.run_id)
                    before_ai_missing = fresh_unclassified['ai.match'].isna() | (fresh_unclassified['ai.match'] == '')
                    df = merge_dataframes(df, mem_df)
                    # Recompute needs after merge
                    needs_ai = view_ready_for_ai(df)
                    fresh_unclassified = needs_ai[needs_ai['sys.is_fresh_job'] == True]
                    # Report savings
                    remaining = len(fresh_unclassified)
                    total = len(job_ids_to_check)
                    saved = total - remaining
                    print(f"💾 Memory reuse before classification: saved {saved}/{total} jobs from reclassification")
                    # Quality among reused
                    try:
                        reused_ids = set(job_ids_to_check) - set(fresh_unclassified['id.job'].astype(str).tolist())
                        if reused_ids:
                            reused_mask = df['id.job'].astype(str).isin(reused_ids)
                            reused_quality = df.loc[reused_mask, 'ai.match'].value_counts().to_dict()
                            g = reused_quality.get('good', 0)
                            s = reused_quality.get('so-so', 0)
                            b = reused_quality.get('bad', 0)
                            e = reused_quality.get('error', 0)
                            print(f"   Reused AI match breakdown: good={g}, so-so={s}, bad={b}, error={e}")
                    except Exception:
                        pass
            except Exception as e:
                print(f"⚠️ Pre-classification memory check failed: {e}")
        
        if len(fresh_unclassified) == 0:
            print("✅ All jobs already classified")
            return df
        
        print(f"🔍 Classifying {len(fresh_unclassified)} fresh jobs...")
        
        # Prepare jobs for classification
        jobs_for_ai = []
        for _, job in fresh_unclassified.iterrows():
            job_data = {
                'job_id': job['id.job'],
                'job_title': job['source.title'],
                'company': job['source.company'],
                'location': job['source.location_raw'],
                'job_description': job['source.description_raw']
            }
            jobs_for_ai.append(job_data)
        
        # Debug first job to see data quality
        if jobs_for_ai:
            sample = jobs_for_ai[0]
            print(f"🔍 AI Classification Sample Job:")
            print(f"    job_id: '{sample['job_id']}' (len={len(str(sample['job_id']))})")
            print(f"    job_title: '{sample['job_title']}' (len={len(str(sample['job_title']))})")
            print(f"    company: '{sample['company']}' (len={len(str(sample['company']))})")
            print(f"    location: '{sample['location']}' (len={len(str(sample['location']))})")
            desc_preview = str(sample['job_description'])[:100] + "..." if len(str(sample['job_description'])) > 100 else str(sample['job_description'])
            print(f"    job_description: '{desc_preview}' (len={len(str(sample['job_description']))})")
        
        # Run AI classification (using optimized async classifier)
        try:
            ai_results = self.classifier.classify_jobs_in_batches(jobs_for_ai)
            
            # Convert results to lookup dictionary
            ai_lookup = {result['job_id']: result for result in ai_results}
            
            # Apply AI results only to jobs that were classified
            df = transform_ai_classification(df, ai_lookup, job_ids_classified=set(job['job_id'] for job in jobs_for_ai))
            
            # Count classification results
            fresh_results = df[df['sys.is_fresh_job'] == True]['ai.match'].value_counts()
            print(f"✅ AI Classification results:")
            for match_type, count in fresh_results.items():
                print(f"   📊 {match_type}: {count}")
            
        except Exception as e:
            print(f"❌ AI classification failed: {e}")
            # Mark unclassified jobs as errors
            error_mask = (df['sys.is_fresh_job'] == True) & (df['ai.match'].isna() | (df['ai.match'] == ''))
            df.loc[error_mask, 'ai.match'] = 'error'
            df.loc[error_mask, 'ai.reason'] = f'Classification failed: {str(e)}'
            df.loc[error_mask, 'ai.summary'] = 'Job classification encountered an error'
        
        return df
    
    def _stage6_routing(self, df: pd.DataFrame, route_filter: str) -> pd.DataFrame:
        """Stage 6: Apply routing rules and set final status"""
        
        print("🚧 STAGE 6: ROUTING")
        
        # Apply routing transforms
        df = transform_routing(df, route_filter)
        
        # Generate statistics
        status_counts = df['route.final_status'].value_counts()
        included_count = sum(count for status, count in status_counts.items() 
                           if status.startswith('included') or status == 'passed_all_filters')
        filtered_count = sum(count for status, count in status_counts.items() 
                           if status.startswith('filtered'))
        
        print(f"✅ Routing complete:")
        print(f"   ✅ Included: {included_count}")
        print(f"   🚫 Filtered: {filtered_count}")
        
        return df
    
    def _stage7_output(
        self, 
        df: pd.DataFrame, 
        market: str,
        custom_location: str,
        generate_pdf: bool,
        generate_csv: bool,
        generate_html: bool, # New parameter for HTML generation
        force_memory_only: bool = False
    ) -> Dict[str, Any]:
        """Stage 7: Generate output files"""
        
        print("📄 STAGE 7: OUTPUT GENERATION")
        
        results = {
            'files': [],
            'pdf_path': None,
            'csv_path': None,
            'total_jobs': len(df),
            'included_jobs': 0,
            'quality_jobs': 0
        }
        
        # Get exportable jobs (good/so-so quality, ready for export)
        exportable_df = view_exportable(df)
        results['quality_jobs'] = len(exportable_df)

        if len(exportable_df) == 0:
            print("⚠️ No quality jobs to export")
            # Don't return early - still generate CSV with all jobs for debugging
        else:
            print(f"📊 Exporting {len(exportable_df)} quality jobs")
        try:
            match_counts = exportable_df['ai.match'].value_counts().to_dict()
            print(f"   Match breakdown: {match_counts}")
        except Exception:
            pass
        
        # Now mark these jobs as "included" since they're actually being exported
        included_indices = exportable_df.index
        for idx in included_indices:
            if df.loc[idx, 'sys.is_fresh_job']:
                df.loc[idx, 'route.final_status'] = 'included'
            else:
                df.loc[idx, 'route.final_status'] = 'included_from_memory'
        
        results['included_jobs'] = len(exportable_df)
        
        # Generate tracked URLs for ALL quality jobs (includes coach/agent metadata per run)
        # This ensures every run gets fresh tracking links with current context
        quality_jobs_df = exportable_df  # Process all exportable jobs, not just fresh ones
        
        has_tracked_url_col = 'meta.tracked_url' in quality_jobs_df.columns
        quality_urls_empty = (quality_jobs_df['meta.tracked_url'].isna() | (quality_jobs_df['meta.tracked_url'] == '')).all() if has_tracked_url_col else True
        
        # Debug tracked URL status
        if has_tracked_url_col:
            non_null_count = quality_jobs_df['meta.tracked_url'].notna().sum()
            print(f"🔍 Quality jobs with non-null tracked URLs: {non_null_count}")
            if non_null_count > 0:
                print(f"🔍 Sample non-null URLs: {quality_jobs_df['meta.tracked_url'].dropna().head(3).tolist()}")
        
        print(f"🔍 URL Debug: has_tracked_url_col={has_tracked_url_col}, quality_urls_empty={quality_urls_empty}, quality_jobs={len(quality_jobs_df)}")
        
        # Smart link generation: Skip if most jobs already have tracking URLs (speed optimization)
        if len(quality_jobs_df) > 0:
            # Check how many jobs already have tracking URLs
            jobs_with_urls = quality_jobs_df['meta.tracked_url'].notna() & (quality_jobs_df['meta.tracked_url'] != '') & (quality_jobs_df['meta.tracked_url'] != quality_jobs_df.get('source.url', ''))
            existing_url_count = jobs_with_urls.sum() if has_tracked_url_col else 0
            total_jobs = len(quality_jobs_df)
            url_coverage = existing_url_count / total_jobs if total_jobs > 0 else 0
            
            # Skip link generation if >80% of jobs already have tracking URLs (smart memory optimization)
            should_skip_generation = (
                (force_memory_only and not force_link_generation) or  # Original memory-only logic
                (url_coverage >= 0.8)  # New smart optimization: >80% coverage
            )
            
            if should_skip_generation:
                print(f"⚡ SMART LINK OPTIMIZATION: Skipping link generation ({existing_url_count}/{total_jobs} jobs have tracking URLs, {url_coverage:.1%} coverage)")
                print("✅ Using existing tracking URLs from memory (massive speed boost!)")
                
                # Fallback: Fill any missing tracking URLs with original URLs (safety net)
                missing_urls = quality_jobs_df['meta.tracked_url'].isna() | (quality_jobs_df['meta.tracked_url'] == '')
                if missing_urls.any():
                    jobs_need_fallback = missing_urls.sum()
                    print(f"🔄 Filling {jobs_need_fallback} missing tracking URLs with original URLs as fallback")
                    quality_jobs_df.loc[missing_urls, 'meta.tracked_url'] = quality_jobs_df.loc[missing_urls, 'source.url']
                    df.loc[missing_urls, 'meta.tracked_url'] = df.loc[missing_urls, 'source.url']
                    
            else:
                print("🔗 Generating tracked URLs...")
                # Initialize link tracker
                link_tracker = None
                if LinkTracker:
                    try:
                        tracker_instance = LinkTracker()
                        if tracker_instance.is_available:
                            link_tracker = tracker_instance
                            print("✅ LinkTracker initialized successfully")
                        else:
                            print("⚠️ LinkTracker initialization failed or service unavailable, will use original URLs")
                    except Exception as e:
                        print(f"⚠️ LinkTracker initialization error: {e}, will use original URLs")
                else:
                    print("⚠️ LinkTracker class not available, will use original URLs")
                
                url_mapping = {}
                for _, job in quality_jobs_df.iterrows():
                    # Get the best available URL
                    original_url = (
                        job.get('source.url', '') or
                        job.get('clean_apply_url', '')
                    )
                    job_id = job.get('id.job', '')
                    
                    # Debug URL lookup
                    print(f"🔍 Job {job_id[:8]}: URL={original_url[:50]}..." if original_url else f"🔍 Job {job_id[:8]}: NO URL FOUND")
                    
                    if original_url and len(original_url) > 10:
                        if link_tracker:
                            try:
                                # Create shortened tracked URL
                                # Get coach/candidate info from environment (set by Streamlit wrapper or terminal script)
                                # Prefer canonical agent.* fields in the DataFrame; fall back to environment
                                coach_username = (
                                    str(job.get('agent.coach_username') or '').strip()
                                    or os.getenv('FREEWORLD_COACH_USERNAME', 'demo_coach')
                                )
                                candidate_name = (
                                    str(job.get('agent.name') or '').strip()
                                    or os.getenv('FREEWORLD_CANDIDATE_NAME', 'Demo Free Agent')
                                )
                                candidate_id = (
                                    str(job.get('agent.uuid') or '').strip()
                                    or os.getenv('FREEWORLD_CANDIDATE_ID', 'demo_agent_001')
                                )

                                # Prepare tags for Short.io
                                tags = []
                                if coach_username:
                                    tags.append(f"coach:{coach_username}")
                                if candidate_id:
                                    tags.append(f"candidate:{candidate_id}")
                                if candidate_name:
                                    tags.append(f"agent:{candidate_name.replace(' ', '-')}") # Short.io tags prefer dashes
                                if market:
                                    tags.append(f"market:{market}")
                                
                                # Use actual job title for better tracking context
                                job_title_for_tracking = job.get('source.title', f"Job {job_id[:8]}")

                                tracked_url = link_tracker.create_short_link(
                                    original_url,
                                    title=job_title_for_tracking,
                                    tags=tags
                                )
                                if tracked_url and tracked_url != original_url:
                                    url_mapping[job_id] = tracked_url
                                    print(f"✅ Created tracked URL for {job_id[:8]}: {tracked_url}")
                                else:
                                    print(f"❌ Link shortening returned invalid URL for {job_id[:8]}: expected new URL, got {tracked_url}")
                                    url_mapping[job_id] = original_url
                            except Exception as e:
                                print(f"❌ Link shortening failed for {job_id[:8]}: {e}")
                                url_mapping[job_id] = original_url
                        else:
                            print(f"❌ LinkTracker not available for job {job_id[:8]}")
                            url_mapping[job_id] = original_url
                
                # Apply tracked URLs to both main dataframe and quality subset
                df = apply_tracked_urls(df, url_mapping)
                quality_jobs_df = apply_tracked_urls(quality_jobs_df, url_mapping)  # FIX: Update quality_jobs_df too!
                print(f"🔍 Before refiltering: exportable_df had {len(exportable_df)} jobs")
                exportable_df = view_exportable(df)
                print(f"🔍 After refiltering: exportable_df now has {len(exportable_df)} jobs")
                print(f"✅ Generated {len(url_mapping)} tracked URLs for {len(quality_jobs_df)} quality jobs")
                print(f"🔍 Applied tracked URLs to both main df and quality_jobs_df")
        
        # Generate CSV (always generate, even if empty for testing)
        if generate_csv:
            csv_path = self._generate_csv(df, exportable_df, market)
            results['csv_path'] = csv_path
            if csv_path:
                results['files'].append(csv_path)
        
        # Generate PDF
        print(f"🔍 PDF Generation Check: generate_pdf={generate_pdf}, exportable_df_length={len(exportable_df)}")
        if generate_pdf and len(exportable_df) > 0:
            print(f"🎯 Calling _generate_pdf with {len(exportable_df)} jobs")
            # Extract coach/candidate info from DataFrame or environment variables
            import os
            if len(exportable_df) > 0:
                coach_name = exportable_df.get('meta.coach_name', pd.Series()).iloc[0] if 'meta.coach_name' in exportable_df.columns else os.getenv('FREEWORLD_COACH_NAME', '')
                coach_username = exportable_df.get('meta.coach_username', pd.Series()).iloc[0] if 'meta.coach_username' in exportable_df.columns else os.getenv('FREEWORLD_COACH_USERNAME', '')
                # Prefer canonical agent.* fields, then legacy meta.*, then environment
                candidate_name = (
                    exportable_df.get('agent.name', pd.Series()).iloc[0]
                    if 'agent.name' in exportable_df.columns else ''
                ) or (
                    exportable_df.get('meta.candidate_name', pd.Series()).iloc[0]
                    if 'meta.candidate_name' in exportable_df.columns else ''
                ) or os.getenv('FREEWORLD_CANDIDATE_NAME', '')
                candidate_id = (
                    exportable_df.get('agent.uuid', pd.Series()).iloc[0]
                    if 'agent.uuid' in exportable_df.columns else ''
                ) or (
                    exportable_df.get('meta.candidate_id', pd.Series()).iloc[0]
                    if 'meta.candidate_id' in exportable_df.columns else ''
                ) or os.getenv('FREEWORLD_CANDIDATE_ID', '')
            else:
                coach_name = os.getenv('FREEWORLD_COACH_NAME', '')
                coach_username = os.getenv('FREEWORLD_COACH_USERNAME', '')
                candidate_name = os.getenv('FREEWORLD_CANDIDATE_NAME', '')
                candidate_id = os.getenv('FREEWORLD_CANDIDATE_ID', '')
                
            pdf_path = self._generate_pdf(exportable_df, market, custom_location, coach_name, coach_username, candidate_name, candidate_id)
            results['pdf_path'] = pdf_path
            if pdf_path:
                results['files'].append(pdf_path)
        elif generate_pdf:
            print("❌ PDF generation skipped - no exportable jobs")
        else:
            print("ℹ️ PDF generation disabled")

        # Generate HTML Portal
        print(f"🔍 HTML Generation Check: generate_html={generate_html}, exportable_df_length={len(exportable_df)}")
        if generate_html and len(exportable_df) > 0:
            if jobs_dataframe_to_dicts and render_jobs_html:
                try:
                    # Prepare agent parameters for HTML template
                    coach_name = os.getenv('FREEWORLD_COACH_NAME', '')
                    coach_username = os.getenv('FREEWORLD_COACH_USERNAME', '')
                    candidate_name = os.getenv('FREEWORLD_CANDIDATE_NAME', '')
                    candidate_id = os.getenv('FREEWORLD_CANDIDATE_ID', '')

                    agent_params = {
                        'location': market,
                        'agent_name': candidate_name,
                        'agent_uuid': candidate_id,
                        'coach_username': coach_username,
                        'coach_name': coach_name
                    }

                    # Convert DataFrame to list of dicts for HTML template
                    jobs_for_html = jobs_dataframe_to_dicts(exportable_df)

                    # Render HTML
                    html_content = render_jobs_html(jobs_for_html, agent_params)

                    # Save HTML to file
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    html_filename = f"{market.replace(', ', '_').replace(' ', '_')}_portal_{timestamp}.html"
                    html_path = os.path.join(self.output_dir, html_filename)

                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)

                    results['html_path'] = html_path
                    results['files'].append(html_path)
                    print(f"✅ HTML portal generated: {html_path}")
                except Exception as e:
                    print(f"❌ HTML generation failed: {e}")
            else:
                print("⚠️ HTML generation skipped: jobs_dataframe_to_dicts or render_jobs_html not available")
        elif generate_html:
            print("❌ HTML generation skipped - no exportable jobs")
        else:
            print("ℹ️ HTML generation disabled")

        # Add the updated DataFrame with tracked URLs to results
        results['jobs_df'] = df

        return results

    def _stage5_5_route_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """Derive route type using the rules-based RouteClassifier and store in ai.route_type"""
        if len(df) == 0:
            return df
        try:
            # Use normalized text if available, otherwise source
            titles = df.get('norm.title', df.get('source.title', pd.Series([''] * len(df))))
            descs = df.get('norm.description', df.get('source.description_raw', pd.Series([''] * len(df))))
            companies = df.get('norm.company', df.get('source.company', pd.Series([''] * len(df))))
            
            def classify_row(t, d, c):
                try:
                    return self.route_classifier.classify_route_type(t or '', d or '', c or '')
                except Exception:
                    return 'Unknown'
            
            route_series = [
                classify_row(titles.iloc[i] if i < len(titles) else '',
                             descs.iloc[i] if i < len(descs) else '',
                             companies.iloc[i] if i < len(companies) else '')
                for i in range(len(df))
            ]
            df = df.assign(**{'ai.route_type': pd.Series(route_series, index=df.index)})
            return df
        except Exception:
            return df
    
    def _stage8_storage(self, df: pd.DataFrame, push_to_airtable: bool) -> None:
        """Stage 8: Store data in persistent systems"""
        
        print("💾 STAGE 8: DATA STORAGE")
        
        # Separate truly fresh jobs from memory-reused jobs
        fresh_classified = view_fresh_quality(df)
        
        # Split jobs: truly fresh (new classifications) vs reused from memory 
        if len(fresh_classified) > 0:
            # Check which jobs were actually reused from memory (have classification_source = supabase_memory)
            memory_reused_mask = fresh_classified.get('sys.classification_source', '') == 'supabase_memory'
            memory_reused_jobs = fresh_classified[memory_reused_mask] if memory_reused_mask.any() else pd.DataFrame()
            truly_fresh_jobs = fresh_classified[~memory_reused_mask] if memory_reused_mask.any() else fresh_classified
            
            print(f"📊 Job classification breakdown:")
            print(f"   🆕 Truly fresh jobs (new classifications): {len(truly_fresh_jobs)}")
            print(f"   🔄 Memory-reused jobs (existing classifications): {len(memory_reused_jobs)}")
            
            # Store truly fresh jobs with full data
            if len(truly_fresh_jobs) > 0:
                try:
                    supabase_df = prepare_for_supabase(truly_fresh_jobs)
                    print(f"🔍 Fresh jobs Supabase DF shape: {supabase_df.shape}, columns: {len(supabase_df.columns)}")
                    
                    success = self.memory_db.store_classifications(supabase_df)
                    if success:
                        print(f"✅ Stored {len(supabase_df)} truly fresh jobs in Supabase")
                    else:
                        print("⚠️ Fresh job storage failed - check store_classifications method")
                except Exception as e:
                    print(f"❌ Fresh job storage error: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Refresh timestamps for memory-reused jobs (keep existing data intact)
            if len(memory_reused_jobs) > 0:
                try:
                    job_ids_to_refresh = memory_reused_jobs['id.job'].dropna().astype(str).tolist()
                    if job_ids_to_refresh:
                        success = self.memory_db.refresh_existing_jobs(job_ids_to_refresh)
                        if success:
                            print(f"✅ Refreshed timestamps for {len(job_ids_to_refresh)} memory-reused jobs")
                        else:
                            print("⚠️ Failed to refresh memory-reused job timestamps")
                except Exception as e:
                    print(f"❌ Memory job refresh error: {e}")
        else:
            print("ℹ️ No quality jobs to store")
        
        # Airtable upload removed: use Supabase memory store only
        
        print("✅ Data storage complete")
    
    def _generate_csv(self, complete_df: pd.DataFrame, exportable_df: pd.DataFrame, market: str) -> str:
        """Generate CSV exports with logical field ordering"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Quality Jobs CSV - only exportable jobs (good/so-so quality)
        # Include market slug in filename to avoid collisions during multi-market runs
        market_slug = str(market or 'market').replace(', ', '_').replace(' ', '_')
        complete_filename = f"{market_slug}_quality_jobs_{timestamp}.csv"
        complete_path = os.path.join(self.output_dir, complete_filename)
        
        # Define logical column order for better CSV viewing
        # Priority fields first (as requested): title, company, ai.summary, ai.match, ai.reason, fresh/memory, route type, final status
        priority_columns = [
            'source.title',           # Job title
            'source.company',         # Company name  
            'ai.summary',            # AI summary
            'ai.match',              # AI match quality (good/so-so/bad)
            'ai.reason',             # AI reasoning
            'sys.is_fresh_job',      # Memory vs Fresh indicator
            'ai.route_type',         # Route type (Local/OTR/Unknown)
            'route.final_status',    # Final routing status
        ]
        
        # PDF-related fields (all fields used in PDF generation)
        pdf_fields = [
            'source.location_raw',   # Location for PDF
            'ai.fair_chance',        # Fair chance indicator
            'ai.endorsements',       # Required endorsements
            'source.url',            # Single unified URL
            'meta.tracked_url',      # Tracked short URL
        ]
        
        # Core identification and source fields
        core_fields = [
            'id.job',               # Job ID
            'id.source',            # Source identifier
            'id.source_row',        # Source row number
            'source.description_raw', # Raw job description
            'source.salary_raw',    # Raw salary data
            'source.posted_date',   # Posted date
        ]
        
        # Normalized fields
        norm_fields = [
            'norm.title', 'norm.company', 'norm.city', 'norm.state', 'norm.location',
            'norm.description', 'norm.salary_display', 'norm.salary_min', 'norm.salary_max', 
            'norm.salary_unit', 'norm.salary_currency'
        ]
        
        # Business rules and filtering
        rules_fields = [
            'rules.is_owner_op', 'rules.is_school_bus', 'rules.has_experience_req',
            'rules.experience_years_min', 'rules.is_spam_source', 'rules.duplicate_r1', 
            'rules.duplicate_r2', 'rules.collapse_group'
        ]
        
        # Routing and processing status
        route_fields = [
            'route.stage', 'route.filtered', 'route.ready_for_ai', 'route.ready_for_export', 
            'route.error', 'route.batch_id'
        ]
        
        # Remaining AI fields
        remaining_ai_fields = ['ai.raw_response']
        
        # Metadata fields
        meta_fields = [
            'meta.market', 'meta.query', 'meta.search_terms', 'meta.airtable_id'
        ]
        
        # Quality assurance fields
        qa_fields = [
            'qa.missing_required_fields', 'qa.flags', 'qa.last_validated_at', 'qa.data_quality_score'
        ]
        
        # System fields (last)
        sys_fields = [
            'sys.created_at', 'sys.updated_at', 'sys.classified_at', 'sys.run_id',
            'sys.version', 'sys.classification_source', 'sys.model', 'sys.prompt_sha',
            'sys.schema_sha', 'sys.coach'
        ]
        
        # Build complete ordered column list
        ordered_columns = (
            priority_columns + pdf_fields + core_fields + norm_fields + 
            rules_fields + route_fields + remaining_ai_fields + 
            meta_fields + qa_fields + sys_fields
        )
        
        # Filter to only include columns that actually exist in the DataFrame
        existing_columns = [col for col in ordered_columns if col in exportable_df.columns]
        
        # Add any remaining columns that weren't in our ordered list (as fallback)
        remaining_columns = [col for col in exportable_df.columns if col not in existing_columns]
        final_column_order = existing_columns + remaining_columns
        
        # Reorder DataFrame with logical column sequence (using exportable_df - QUALITY JOBS ONLY)
        ordered_df = exportable_df[final_column_order]
        
        # Export with logical ordering
        ordered_df.to_csv(complete_path, index=False)
        print(f"✅ Quality Jobs CSV (exportable only): {complete_path}")
        print(f"📋 Column order: Priority fields → PDF fields → Core → Normalized → Rules → System")
        
        return complete_path
    
    def _generate_pdf(self, exportable_df: pd.DataFrame, market: str, custom_location: str, coach_name: str = '', coach_username: str = '', candidate_name: str = '', candidate_id: str = '') -> Optional[str]:
        """Generate PDF using existing generator"""
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Determine output location
            if custom_location:
                location_folder = os.path.join(self.output_dir, "Custom_Locations", custom_location)
            else:
                location_folder = os.path.join(self.output_dir, market)
            
            os.makedirs(location_folder, exist_ok=True)
            
            # Debug: Check input data
            print(f"🔍 PDF Generation Debug:")
            print(f"  📊 Exportable jobs input: {len(exportable_df)}")
            print(f"  📋 Columns available: {len(exportable_df.columns)}")
            
            # Use canonical DataFrame directly - PDF generator handles field mapping
            pdf_df = exportable_df
            
            print(f"  ✅ PDF DataFrame ready: {len(pdf_df)} jobs (canonical fields)")
            print(f"  📈 Match distribution: {pdf_df['ai.match'].value_counts().to_dict()}")
            
            # Generate PDF
            pdf_filename = f"FreeWorld_Jobs_{market}_{timestamp.replace(':', '.')}.pdf"
            pdf_path = os.path.join(location_folder, pdf_filename)
            
            # Use parameters passed to pipeline instead of environment variables
            generate_fpdf_job_cards(
                pdf_df, 
                pdf_path, 
                market=market,
                coach_name=coach_name,
                coach_username=coach_username,
                candidate_name=candidate_name,
                candidate_id=candidate_id
            )
            
            print(f"✅ PDF generated: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            return None
    
    def generate_pdf_from_canonical(self, df: pd.DataFrame, market_name: str, 
                                   coach_name: str = '', coach_username: str = '',
                                   candidate_name: str = '', candidate_id: str = '') -> Optional[bytes]:
        """Generate PDF from canonical DataFrame and return as bytes for Streamlit download"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create temporary file path
            temp_dir = os.path.join(self.output_dir, "temp_pdfs")
            os.makedirs(temp_dir, exist_ok=True)
            
            pdf_filename = f"FreeWorld_Jobs_{market_name}_{timestamp}.pdf"
            pdf_path = os.path.join(temp_dir, pdf_filename)
            
            print(f"🔍 PDF Generator received: {len(df)} jobs")
            print(f"   Market: '{market_name}' (empty={not market_name})")
            print(f"   Coach: '{coach_name}' (empty={not coach_name})")
            print(f"   Coach Username: '{coach_username}' (empty={not coach_username})")
            print(f"   Candidate: '{candidate_name}' (empty={not candidate_name})")
            print(f"   Candidate ID: '{candidate_id}' (empty={not candidate_id})")
            
            # Extract first names for personalized titles
            if candidate_name and len(candidate_name.split()) > 0:
                agent_first_name = candidate_name.split()[0]
                print(f"   🏷️  Agent first name: '{agent_first_name}' (empty={not agent_first_name})")
            else:
                agent_first_name = ''
            
            if coach_name and len(coach_name.split()) > 0:
                coach_first_name = coach_name.split()[0]
                print(f"   🏷️  Coach first name: '{coach_first_name}' (empty={not coach_first_name})")
                print(f"   🔍  Original coach_name: '{coach_name}'")
                print(f"   🔍  Extracted coach_first_name: '{coach_first_name}'")
            else:
                coach_first_name = ''
            
            # Generate PDF using the fpdf generator
            generate_fpdf_job_cards(
                df, 
                pdf_path, 
                market=market_name,
                coach_name=coach_name,
                coach_username=coach_username,
                candidate_name=candidate_name,
                candidate_id=candidate_id
            )
            
            # Read PDF as bytes
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            
            # Clean up temp file
            try:
                os.remove(pdf_path)
            except:
                pass
            
            print(f"✅ PDF generated successfully: {len(pdf_bytes)} bytes")
            return pdf_bytes
            
        except Exception as e:
            print(f"❌ UI PDF generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_job_id_from_raw(self, raw_job: Dict[str, Any]) -> str:
        """Generate job ID from raw job data"""
        # Handle both Outscraper and Indeed field names
        company = str(raw_job.get('company_name') or raw_job.get('company', '')).lower().strip()
        location = str(raw_job.get('location') or raw_job.get('formattedLocation', '')).lower().strip()
        title = str(raw_job.get('job_title') or raw_job.get('title', '')).lower().strip()
        
        content = f"{company}|{location}|{title}"
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()
    
    def _checkpoint_data(self, df: pd.DataFrame, stage: str) -> None:
        """Save checkpoint data for debugging"""
        
        # Always save checkpoints even for empty data (for testing)
        try:
            checkpoint_path = os.path.join(
                self.parquet_dir, 
                f"{self.run_id}_{stage}.parquet"
            )
            
            # Ensure DataFrame has schema even if empty
            df = ensure_schema(df)
            df.to_parquet(checkpoint_path, index=False)
            try:
                print(f"✅ Checkpoint saved: {checkpoint_path}")
            except Exception:
                pass
            
            # Validate data integrity (temporarily disabled for debugging)
            # validation = validate_dataframe(df)
            # if not validation['valid']:
            #     print(f"⚠️ Stage {stage}: {len(validation['errors'])} validation errors")
            #     # Show first few errors for debugging
            #     for i, error in enumerate(validation['errors'][:3]):
            #         print(f"   Error {i+1}: {error}")
            #     if len(validation['errors']) > 3:
            #         print(f"   ... and {len(validation['errors']) - 3} more errors")
            print(f"✅ Stage {stage}: Validation temporarily disabled for debugging")
            
        except Exception as e:
            try:
                print(f"⚠️ Checkpoint {stage} failed: {e}")
                print(f"ℹ️ Parquet directory: {self.parquet_dir}")
            except Exception:
                pass
    
    def _populate_agent_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Populate agent.* fields in canonical DataFrame from Free Agent data"""
        if not self.agent_data:
            return df
            
        print(f"👤 Populating Free Agent fields for {len(df)} jobs...")
        
        # Add all 15 canonical agent.* fields to every row
        for field, value in self.agent_data.items():
            df[field] = value
            
        agent_name = self.agent_data.get('agent.name', 'Unknown')
        coach_name = self.agent_data.get('agent.coach_name', 'Unknown')
        print(f"✅ Added agent fields: {agent_name} (Coach: {coach_name})")
        
        return df
    
    def _generate_pipeline_stats(self, df: pd.DataFrame, mode_info: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
        """Generate comprehensive pipeline statistics"""
        
        total_jobs = len(df)
        fresh_jobs = (df['sys.is_fresh_job'] == True).sum() if 'sys.is_fresh_job' in df.columns else 0
        memory_jobs = (df['sys.is_fresh_job'] == False).sum() if 'sys.is_fresh_job' in df.columns else 0
        included_jobs = (df['route.final_status'].str.startswith('included')).sum() if 'route.final_status' in df.columns else 0
        quality_jobs = (df['ai.match'].isin(['good', 'so-so'])).sum() if 'ai.match' in df.columns else 0
        
        # Calculate actual cost metrics based on source and fresh vs memory jobs
        cost_calculator = CostCalculator()
        
        # Count jobs by source
        indeed_fresh_jobs = (df['id.source'] == 'indeed').sum() if 'id.source' in df.columns else fresh_jobs
        google_fresh_jobs = (df['id.source'] == 'google').sum() if 'id.source' in df.columns else 0
        
        # Calculate costs by source
        # Indeed: scraping + classification costs for fresh jobs
        indeed_cost = cost_calculator.calculate_cost_bulk(indeed_fresh_jobs) if indeed_fresh_jobs > 0 else 0.0
        
        # Google: actual API cost (based on queries executed) + classification for fresh jobs  
        google_scraping_cost = self.google_api_cost  # Actual cost from queries executed
        google_classification_cost = google_fresh_jobs * cost_calculator.openai_cost_per_job if google_fresh_jobs > 0 else 0.0
        google_cost = google_scraping_cost + google_classification_cost
        
        # Memory jobs only require classification costs (any source)
        memory_classification_cost = memory_jobs * cost_calculator.openai_cost_per_job if memory_jobs > 0 else 0.0
        
        # Total cost combines all sources
        total_cost = indeed_cost + google_cost + memory_classification_cost
        
        # Calculate memory efficiency (percentage of jobs from memory vs fresh scraping)
        memory_efficiency = (memory_jobs / max(1, total_jobs)) * 100 if total_jobs > 0 else 0
        
        # Calculate cost per quality job
        cost_per_quality_job = total_cost / max(1, quality_jobs) if quality_jobs > 0 else 0
        
        # Count route types
        local_routes = (df['ai.route_type'] == 'Local').sum() if 'ai.route_type' in df.columns else 0
        otr_routes = (df['ai.route_type'] == 'OTR').sum() if 'ai.route_type' in df.columns else 0
        unknown_routes = (df['ai.route_type'] == 'Unknown').sum() if 'ai.route_type' in df.columns else 0
        
        stats = {
            # Core job counts
            'total_jobs': total_jobs,
            'total_processed': total_jobs,
            'fresh_jobs': fresh_jobs,
            'memory_jobs': memory_jobs,
            'included_jobs': included_jobs,
            'filtered_jobs': (df['route.filtered'] == True).sum() if 'route.filtered' in df.columns else 0,
            'quality_jobs': quality_jobs,
            
            # AI Classification breakdown
            'ai_good': (df['ai.match'] == 'good').sum() if 'ai.match' in df.columns else 0,
            'ai_so_so': (df['ai.match'] == 'so-so').sum() if 'ai.match' in df.columns else 0,
            'ai_bad': (df['ai.match'] == 'bad').sum() if 'ai.match' in df.columns else 0,
            'ai_errors': (df['ai.match'] == 'error').sum() if 'ai.match' in df.columns else 0,
            
            # Route type breakdown
            'local_routes': local_routes,
            'otr_routes': otr_routes,
            'unknown_routes': unknown_routes,
            
            # Performance metrics
            'processing_time': processing_time,
            'total_cost': total_cost,
            'cost_per_quality_job': cost_per_quality_job,
            'memory_efficiency': memory_efficiency,
            
            # System info
            'run_id': self.run_id,
            'schema_version': self.schema_info['version'],
            'completed_at': datetime.now().isoformat()
        }
        
        # Create summary string
        stats['summary'] = (
            f"{stats['total_processed']} total → "
            f"{stats['quality_jobs']} quality → "
            f"{stats['included_jobs']} included"
        )
        
        return stats
    
    def load_checkpoint(self, stage: str) -> Optional[pd.DataFrame]:
        """Load checkpoint data for debugging"""
        
        checkpoint_path = os.path.join(
            self.parquet_dir,
            f"{self.run_id}_{stage}.parquet"
        )
        
        if os.path.exists(checkpoint_path):
            return pd.read_parquet(checkpoint_path)
        return None

if __name__ == "__main__":
    # Test pipeline v3
    print("🧪 Pipeline v3 Test")
    print("=" * 40)
    
    pipeline = FreeWorldPipelineV3()
    
    # Test with small sample
    test_result = pipeline.run_complete_pipeline(
        location="Test Market",
        mode_info={"limit": 5},
        search_terms="CDL driver",
        generate_pdf=False,
        generate_csv=True
    )
    
    print(f"✅ Test completed: {test_result['summary']}")
    print(f"📁 Files: {test_result['files']}")
