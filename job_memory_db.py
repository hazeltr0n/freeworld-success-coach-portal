"""
Job Memory Database using Supabase
Replaces Airtable for classification memory to reduce API usage
"""
import os
import sys
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

class JobMemoryDB:
    """Supabase-based job classification memory system"""
    
    def __init__(self):
        """Initialize Supabase connection"""
        self.supabase = None
        self._connection_healthy = False
        self._init_supabase()
    
    def _init_supabase(self):
        """Initialize Supabase client using centralized connection"""
        try:
            # Try to use the centralized client first (handles both env vars and Streamlit secrets)
            from supabase_utils import get_client
            self.supabase = get_client()
            
            if self.supabase:
                self._connection_healthy = True
                print("✅ Supabase job memory database connected via centralized client")
                return
                
        except ImportError:
            pass
        
        # Fallback to direct connection for non-Streamlit environments
        try:
            from supabase import create_client, Client
            from dotenv import load_dotenv
            
            # Handle different .env locations for PyInstaller vs development
            if getattr(sys, 'frozen', False):
                # Running in PyInstaller bundle - check multiple possible locations
                bundle_dir = sys._MEIPASS
                resources_dir = os.path.join(os.path.dirname(sys.executable), '..', 'Resources')
                
                possible_paths = [
                    os.path.join(bundle_dir, '.env'),
                    os.path.join(resources_dir, '.env'),
                    os.path.abspath(os.path.join(resources_dir, '.env'))
                ]
                
                env_loaded = False
                for env_path in possible_paths:
                    if os.path.exists(env_path):
                        load_dotenv(env_path)
                        env_loaded = True
                        break
                
                if not env_loaded:
                    # Fallback to loading from current directory
                    load_dotenv()
            else:
                # Running in development
                load_dotenv()
            
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            
            if not all([supabase_url, supabase_key]):
                print("⚠️ Supabase credentials not found - add SUPABASE_URL and SUPABASE_ANON_KEY to .env")
                return
            
            self.supabase: Client = create_client(supabase_url, supabase_key)
            self._connection_healthy = True
            print("✅ Supabase job memory database connected via direct client")
            
        except ImportError:
            print("⚠️ Supabase not installed - pip install supabase")
        except Exception as e:
            print(f"⚠️ Supabase connection failed: {e}")
    
    def _check_and_repair_connection(self) -> bool:
        """Check if connection is healthy and reconnect if needed"""
        if not self.supabase:
            logger.warning("Supabase client not initialized, attempting to reconnect...")
            self._init_supabase()
            return self._connection_healthy
            
        # Quick health check - try a simple query
        try:
            # Test connection with a lightweight query
            result = self.supabase.table('jobs').select('job_id').limit(1).execute()
            self._connection_healthy = True
            return True
        except Exception as e:
            logger.warning(f"Supabase connection unhealthy ({e}), attempting to reconnect...")
            self._connection_healthy = False
            
            # Try to reconnect
            try:
                self._init_supabase()
                if self.supabase:
                    # Test the new connection
                    result = self.supabase.table('jobs').select('job_id').limit(1).execute()
                    self._connection_healthy = True
                    logger.info("✅ Supabase connection restored")
                    return True
            except Exception as reconnect_error:
                logger.error(f"Failed to reconnect to Supabase: {reconnect_error}")
                self._connection_healthy = False
                
        return False
    
    def _clean_nan_values(self, value):
        """Convert NaN values to appropriate defaults for JSON serialization"""
        import pandas as pd
        import numpy as np
        
        if pd.isna(value) or value is None:
            return None
        elif isinstance(value, (int, float)) and (np.isnan(value) or np.isinf(value)):
            return None
        else:
            return value

    def store_classifications(self, jobs_df: pd.DataFrame, enable_qc: bool = True) -> bool:
        """
        Store job classifications in memory database with optional quality control
        
        Args:
            jobs_df: DataFrame with classified jobs
            enable_qc: Whether to run quality control validation before upload
            
        Returns:
            bool: Success status
        """
        if not self.supabase:
            return False
            
        # Optional Quality Control validation
        if enable_qc and len(jobs_df) > 0:
            try:
                from data_quality_control import validate_jobs_for_upload
                validated_df, qc_report = validate_jobs_for_upload(jobs_df, strict_mode=False)
                
                if len(validated_df) < len(jobs_df):
                    rejected_count = len(jobs_df) - len(validated_df)
                    logger.warning(f"QC filtered out {rejected_count} jobs with data quality issues")
                    
                # Use validated data for storage
                jobs_df = validated_df
                logger.info(f"QC validation complete: {len(jobs_df)} jobs ready for upload")
                
            except Exception as qc_error:
                logger.warning(f"QC validation failed, proceeding without validation: {qc_error}")
                
        try:
            # Convert DataFrame to records for Supabase
            records = []
            skipped_jobs = []
            for idx, job in jobs_df.iterrows():
                # IMPORTANT: After prepare_for_supabase(), columns use FLAT names (e.g., 'match_level'), NOT canonical (e.g., 'ai.match')
                job_id = job.get('job_id', f'job_{idx}')
                match = job.get('match_level', '')
                reason = job.get('match_reason', '')
                summary = job.get('summary', '')
                final_status = job.get('filter_reason', '')

                # SIMPLIFIED LOGIC: Upload ANY job with AI classification (good/so-so/bad)
                # This ensures fresh Indeed jobs get stored regardless of routing status
                if match and str(match).strip() and str(match) not in ['', 'nan', 'None', 'null'] and str(match) in ['good', 'so-so', 'bad']:
                    # Debug: Log job being stored
                    logger.debug(f"✅ Storing job {job_id[:8]}... with match='{match}', final_status='{final_status}'")
                    # Provide default values if missing (required by Supabase schema)
                    if not reason or str(reason) in ['', 'nan', 'None', 'null']:
                        reason = final_status or 'No reason provided'
                    if not summary or str(summary) in ['', 'nan', 'None', 'null']:
                        summary = f'Job classified as {match}'
                else:
                    # Skip jobs without valid AI classification
                    logger.debug(f"⏭️ Skipping job {job_id[:8]}... with match='{match}' (no valid AI classification)")
                    skipped_jobs.append({'job_id': job_id, 'final_status': final_status, 'match': str(match), 'reason': 'No valid AI classification', 'summary': str(summary)[:50]})
                    continue
                    
                # Market sanitization: preserve custom locations as-is, normalize known markets
                def _sanitize_market(val: str) -> str:
                    try:
                        from shared_search import MARKET_TO_LOCATION
                        std = {m: m for m in MARKET_TO_LOCATION.keys()}
                        city_map = {v.split(',')[0].strip().lower(): k for k, v in MARKET_TO_LOCATION.items()}
                    except Exception:
                        std, city_map = {}, {}
                    s = str(val or '').strip()
                    if not s:
                        return ''
                    # CRITICAL: Preserve custom locations with commas as-is (e.g., "Austin, TX")
                    # Only normalize if it's a known market name (no comma)
                    if s in std:
                        return s
                    # REMOVED: inv check that was converting "Austin, TX" back to "Austin"
                    # Only look up in city_map if there's NO comma (known market)
                    if ',' not in s:
                        if s.lower() in city_map:
                            return city_map[s.lower()]
                        if s.lower() == 'berkeley':
                            return 'Bay Area'
                        if s.lower() == 'ontario':
                            return 'Inland Empire'
                    # Return as-is (preserves "Austin, TX", "ZIP 12345", "spice girls", etc.)
                    return s

                # Convert all values to strings as expected by RPC function
                def safe_str(val):
                    """Convert value to string, handling None/empty cases"""
                    if val is None or val == '':
                        return ''
                    return str(val)

                # Build record using FLAT Supabase field names (after prepare_for_supabase transformation)
                record = {
                    # Core job information (all TEXT as per RPC function)
                    'job_id': safe_str(job.get('job_id', '')),
                    'job_title': safe_str(job.get('job_title', '')),
                    'company': safe_str(job.get('company', '')),
                    'location': safe_str(job.get('location', '')),
                    'zip_code': safe_str(job.get('zip_code', '')),
                    'job_description': safe_str(job.get('job_description', ''))[:5000],
                    'apply_url': safe_str(job.get('apply_url', '')),
                    'salary': safe_str(job.get('salary', '')),

                    # AI Classification results (all TEXT)
                    'match_level': safe_str(match),
                    'match_reason': safe_str(reason),
                    'summary': safe_str(summary),
                    'fair_chance': safe_str(job.get('fair_chance', 'unknown')),
                    'endorsements': safe_str(job.get('endorsements', 'unknown')),
                    'route_type': safe_str(job.get('route_type', '')),

                    # Career pathway fields (new for pathway classifier)
                    'career_pathway': safe_str(job.get('career_pathway', 'cdl_pathway')),
                    'training_provided': bool(job.get('training_provided', False)),  # BOOLEAN for RPC

                    # Organization and tracking (all TEXT)
                    'market': safe_str(_sanitize_market(job.get('market', ''))),
                    'tracked_url': safe_str(job.get('tracked_url', '')),  # ← CRITICAL FIX!

                    # Recall context fields (all TEXT)
                    'indeed_job_url': safe_str(job.get('indeed_job_url', '')),
                    'search_query': safe_str(job.get('search_query', '')),
                    'source': safe_str(job.get('source', 'outscraper')),
                    'filter_reason': safe_str(job.get('filter_reason', '')),

                    # System metadata (all TEXT)
                    'classification_source': safe_str(job.get('classification_source', 'ai_classification')),
                    'classified_at': datetime.now().isoformat(),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),

                    # Deduplication fields (all TEXT) - these are critical for the RPC function
                    'rules_duplicate_r1': safe_str(job.get('rules_duplicate_r1', '')),
                    'rules_duplicate_r2': safe_str(job.get('rules_duplicate_r2', '')),
                    'rules_duplicate_r3': safe_str(job.get('rules_duplicate_r3', '')),
                    'clean_apply_url': safe_str(job.get('clean_apply_url', '')),
                    'job_id_hash': safe_str(job.get('sys.hash', ''))  # Keep sys.hash (not in SUPABASE_FIELDS)
                }
                
                if record['job_id']:  # Only store if we have a job_id
                    records.append(record)
            
            # Log debug information about processing
            logger.info(f"🔍 SUPABASE UPLOAD DEBUG: Processed {len(jobs_df)} jobs")
            logger.info(f"   - Records created: {len(records)}")
            logger.info(f"   - Jobs skipped: {len(skipped_jobs)}")
            
            if skipped_jobs:
                logger.warning(f"⚠️ Skipped jobs details:")
                for skip in skipped_jobs[:5]:  # Show first 5
                    logger.warning(f"   - {skip['job_id']}: status='{skip['final_status']}', match='{skip['match']}', reason='{skip['reason']}', summary='{skip['summary']}'")
                if len(skipped_jobs) > 5:
                    logger.warning(f"   ... and {len(skipped_jobs)-5} more")
            
            if not records:
                logger.warning("❌ No valid records to store in memory database - all jobs were skipped")
                return False

            # Use batch processing to avoid timeouts with large datasets
            batch_size = 100
            total_stored = 0
            total_batches = (len(records) + batch_size - 1) // batch_size

            logger.info(f"🔄 Processing {len(records)} records in {total_batches} batches of {batch_size}")

            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                batch_num = i // batch_size + 1

                # Debug: Log field mapping for first record in first batch
                if i == 0 and batch:
                    logger.info(f"🔍 FIELD MAPPING DEBUG - First record keys: {list(batch[0].keys())}")
                    logger.info(f"   Sample values:")
                    for key in ['job_id', 'job_title', 'company', 'rules_duplicate_r3', 'match_level']:
                        if key in batch[0]:
                            val = batch[0][key]
                            logger.info(f"   - {key}: '{val}' (type: {type(val).__name__}, len: {len(str(val)) if val else 0})")

                try:
                    # Use RPC for deduplication - no fallback!
                    result = self.supabase.rpc('batch_insert_jobs_with_dedup', {'p_jobs_data': batch}).execute()

                    if result.data is not None:  # RPC returns count or error
                        count = result.data if isinstance(result.data, int) else len(batch)
                        total_stored += count
                        logger.info(f"✅ Stored {count} job classifications (batch {batch_num}/{total_batches}) with deduplication")
                        continue
                    else:
                        logger.error(f"❌ RPC failed for batch {batch_num}: returned no data")
                        return False

                except Exception as rpc_error:
                    logger.error(f"❌ Database deduplication RPC failed for batch {batch_num}: {rpc_error}")
                    logger.error(f"   NO FALLBACK - upload aborted to prevent data corruption")
                    return False

            logger.info(f"✅ Successfully stored {total_stored} total job classifications across {total_batches} batches")
            return True
                
        except Exception as e:
            logger.error(f"Error storing job classifications: {e}")
            return False
    
    def refresh_existing_jobs(self, job_ids: List[str]) -> bool:
        """
        Refresh timestamp for existing jobs to keep them current without changing data
        
        Args:
            job_ids: List of job IDs to refresh
            
        Returns:
            bool: Success status
        """
        if not self.supabase or not job_ids:
            return False
            
        try:
            logger.info(f"🔄 Refreshing timestamps for {len(job_ids)} existing jobs in Supabase")
            
            # Update jobs in batches to avoid request limits
            batch_size = 100
            updated_count = 0
            
            for i in range(0, len(job_ids), batch_size):
                batch = job_ids[i:i + batch_size]
                
                # Prepare minimal update records - only update timestamps
                update_records = []
                for job_id in batch:
                    update_records.append({
                        'id': job_id,
                        'classified_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    })
                
                # Execute batch update
                try:
                    result = self.supabase.table('jobs').upsert(update_records).execute()
                    if result.data:
                        batch_count = len(result.data)
                        updated_count += batch_count
                        logger.info(f"✅ Refreshed {batch_count} job timestamps (batch {i//batch_size + 1})")
                    else:
                        logger.warning(f"⚠️ No results returned for refresh batch {i//batch_size + 1}")
                except Exception as batch_error:
                    logger.error(f"❌ Failed to refresh batch {i//batch_size + 1}: {batch_error}")
                    
            if updated_count > 0:
                logger.info(f"✅ Successfully refreshed timestamps for {updated_count} existing jobs")
                return True
            else:
                logger.warning("⚠️ No job timestamps were refreshed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error refreshing job timestamps: {e}")
            return False

    def update_tracking_urls(self, job_tracking_map: Dict[str, str]) -> bool:
        """
        Update tracking URLs for existing jobs in Supabase
        
        Args:
            job_tracking_map: Dict mapping job_id to tracked_url
            
        Returns:
            bool: Success status
        """
        if not self.supabase or not job_tracking_map:
            return False
            
        try:
            logger.info(f"🔗 Updating tracking URLs for {len(job_tracking_map)} jobs in Supabase")
            
            # Update jobs in batches to avoid request limits
            batch_size = 100
            job_items = list(job_tracking_map.items())
            updated_count = 0
            
            for i in range(0, len(job_items), batch_size):
                batch = job_items[i:i + batch_size]
                
                # Prepare update records
                update_records = []
                for job_id, tracked_url in batch:
                    update_records.append({
                        'id': job_id,
                        'tracked_url': tracked_url,
                        'updated_at': datetime.now().isoformat()
                    })
                
                # Execute batch update
                try:
                    result = self.supabase.table('jobs').upsert(update_records).execute()
                    if result.data:
                        batch_count = len(result.data)
                        updated_count += batch_count
                        logger.info(f"✅ Updated tracking URLs for {batch_count} jobs (batch {i//batch_size + 1})")
                    else:
                        logger.warning(f"⚠️ No results returned for batch {i//batch_size + 1}")
                except Exception as batch_error:
                    logger.error(f"❌ Failed to update batch {i//batch_size + 1}: {batch_error}")
                    
            if updated_count > 0:
                logger.info(f"✅ Successfully updated tracking URLs for {updated_count} jobs in Supabase")
                return True
            else:
                logger.warning("⚠️ No tracking URLs were updated")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating tracking URLs: {e}")
            return False
    
    def check_job_memory(self, job_ids: List[str], hours: int = 168) -> Dict[str, Dict]:
        """
        Check which job IDs already exist in memory database
        
        Args:
            job_ids: List of job IDs to check
            hours: Hours to look back (default 168 = 7 days)
            
        Returns:
            Dict mapping job_id to job data for known jobs
        """
        if not job_ids:
            return {}
            
        # Check and repair connection if needed
        if not self._check_and_repair_connection():
            logger.error("❌ Supabase connection failed and could not be repaired")
            return {}
            
        try:
            # Calculate cutoff time
            cutoff_time = datetime.now() - timedelta(hours=hours)
            cutoff_str = cutoff_time.isoformat()

            # Query for matching job IDs within time window - ALL classified jobs
            # (Used to avoid re-classifying jobs, regardless of quality)
            # IMPORTANT: Batch queries to avoid massive IN clauses that timeout
            memory_dict = {}
            batch_size = 500  # Query 500 job IDs at a time
            total_batches = (len(job_ids) + batch_size - 1) // batch_size

            print(f"🔍 Checking {len(job_ids)} job IDs against Supabase in {total_batches} batches of {batch_size}...")

            for batch_num in range(0, len(job_ids), batch_size):
                batch = job_ids[batch_num:batch_num + batch_size]
                batch_index = (batch_num // batch_size) + 1

                result = self.supabase.table('jobs').select('*').in_(
                    'job_id', batch
                ).gte('classified_at', cutoff_str).execute()

                if result.data:
                    print(f"   Batch {batch_index}/{total_batches}: Found {len(result.data)} existing jobs")

                # Convert to lookup dictionary with all comprehensive fields
                for job in result.data:
                    memory_dict[job['job_id']] = {
                        # Core job information
                        'job_title': job['job_title'],
                        'company': job['company'],
                        'location': job['location'],
                        'job_description': job['job_description'],
                        'job_id': job['job_id'],

                        # Original fields
                        'job_title_original': job.get('job_title_original', ''),
                        'company_original': job.get('company_original', ''),
                        'location_original': job.get('location_original', ''),

                        # Comprehensive salary fields
                        'salary': job.get('salary', ''),
                        'salary_display_text': job.get('salary_display_text', ''),
                        'salary_estimated_currency': job.get('salary_estimated_currency', ''),
                        'salary_estimated_unit': job.get('salary_estimated_unit', ''),
                        'salary_estimated_min': job.get('salary_estimated_min', ''),
                        'salary_estimated_max': job.get('salary_estimated_max', ''),
                        'salary_base_currency': job.get('salary_base_currency', ''),
                        'salary_base_unit': job.get('salary_base_unit', ''),
                        'salary_base_min': job.get('salary_base_min', ''),
                        'salary_base_max': job.get('salary_base_max', ''),

                        # Classification results
                        'match': job['match_level'],
                        'reason': job['match_reason'],
                        'summary': job.get('summary', ''),
                        'route_type': job['route_type'],
                        'fair_chance': job.get('fair_chance', 'unknown'),
                        'endorsements': job.get('endorsements', 'unknown'),

                        # Processing status and metadata
                        'final_status': job.get('filter_reason', ''),  # Map Supabase filter_reason to DataFrame final_status
                        'classification_source': job.get('classification_source', 'memory_database'),

                        # URLs and source tracking
                        'apply_url': job['apply_url'],
                        'indeed_job_url': job.get('indeed_job_url', ''),
                        'source': job.get('source', 'memory_database'),

                        # Search and market data
                        'market': job['market'],
                        'query': job.get('search_query', ''),  # Map search_query to query for DataFrame compatibility
                        'search_query': job.get('search_query', '')
                    }
            
            logger.info(f"Found {len(memory_dict)} jobs in memory database out of {len(job_ids)} checked")
            return memory_dict
            
        except Exception as e:
            # Handle IDNA and other connection-related errors
            if 'idna' in str(e).lower() or 'connection' in str(e).lower() or 'network' in str(e).lower():
                logger.warning(f"Connection-related error in check_job_memory: {e}")
                self._connection_healthy = False
                if self._check_and_repair_connection():
                    logger.info("Retrying check_job_memory after connection repair...")
                    try:
                        # Retry once with repaired connection - using batching
                        cutoff_time = datetime.now() - timedelta(hours=hours)
                        cutoff_str = cutoff_time.isoformat()
                        memory_dict = {}
                        batch_size = 500
                        total_batches = (len(job_ids) + batch_size - 1) // batch_size

                        print(f"🔍 [Retry] Checking {len(job_ids)} job IDs against Supabase in {total_batches} batches...")

                        for batch_num in range(0, len(job_ids), batch_size):
                            batch = job_ids[batch_num:batch_num + batch_size]
                            batch_index = (batch_num // batch_size) + 1

                            result = self.supabase.table('jobs').select('*').in_(
                                'job_id', batch
                            ).gte('classified_at', cutoff_str).execute()

                            if result.data:
                                print(f"   [Retry] Batch {batch_index}/{total_batches}: Found {len(result.data)} existing jobs")
                                for job in result.data:
                                    memory_dict[job['job_id']] = {
                                        'job_id': job['job_id'],
                                        'title': job['title'],
                                        'company': job['company'],
                                        'location': job['location'],
                                        'description': job['description'],
                                        'match_level': job['match_level'],
                                        'ai_reason': job.get('ai_reason', ''),
                                        'ai_summary': job.get('ai_summary', ''),
                                        'fair_chance': job.get('fair_chance', 'no_requirements_mentioned'),
                                        'endorsements': job.get('endorsements', 'none_required'),
                                        'route_type': job.get('route_type', ''),
                                        'market': job['market'],
                                        'query': job.get('search_query', ''),
                                        'search_query': job.get('search_query', '')
                                    }

                        logger.info(f"Found {len(memory_dict)} jobs in memory database out of {len(job_ids)} checked (after reconnection)")
                        return memory_dict
                    except Exception as retry_error:
                        logger.error(f"Retry failed after connection repair in check_job_memory: {retry_error}")
                        
            logger.error(f"Error checking job memory: {e}")
            return {}
    
    def search_jobs(self, search_terms: str = None, location: str = None, radius: int = 50, limit: int = 100, hours: int = 72, text_search: bool = False) -> List[Dict]:
        """
        Search for jobs in memory database - prioritizes location-based quality job retrieval
        
        Args:
            search_terms: Optional search terms to filter by (only used if text_search=True)
            location: Location to filter by
            radius: Radius in miles (not currently implemented for Supabase)
            limit: Maximum number of jobs to return
            hours: Hours to look back (default 72)
            text_search: If True, filters by search terms; if False, gets all quality jobs from location
            
        Returns:
            List of job dictionaries matching the criteria, ordered by freshness
        """
        # Check and repair connection if needed
        if not self._check_and_repair_connection():
            logger.error("❌ Supabase connection failed and could not be repaired")
            return []
            
        try:
            # Calculate cutoff time
            cutoff_time = datetime.now() - timedelta(hours=hours)
            cutoff_str = cutoff_time.isoformat()
            
            # Base query for recent jobs - prioritize quality jobs unless text search is enabled
            if text_search:
                # Text-based search across all job qualities
                query = self.supabase.table('jobs').select('*').gte('updated_at', cutoff_str)

                # Add search terms filter
                if search_terms and search_terms.strip():
                    terms = search_terms.strip().lower()
                    query = query.or_(
                        f'title.ilike.%{terms}%,'
                        f'description.ilike.%{terms}%,'
                        f'normalized_title.ilike.%{terms}%'
                    )
            else:
                # Default behavior: get quality jobs from location (like original)
                query = self.supabase.table('jobs').select('*').in_(
                    'match_level', ['good', 'so-so']
                ).gte('updated_at', cutoff_str)
            
            # Add location filter if provided
            # FIX: Use .eq() for market exact match instead of .ilike() to handle commas in location names
            if location and location.strip():
                location_clean = location.strip()
                # Try exact market match first (handles "Austin, TX" perfectly)
                try:
                    query = query.eq('market', location_clean)
                except Exception as e:
                    print(f"⚠️ Exact market match failed: {e}, trying fuzzy search")
                    # Fallback to case-insensitive partial match (but avoid OR with commas)
                    location_lower = location_clean.lower()
                    query = query.ilike('market', f'%{location_lower}%')
                
            # Order by freshness (newest first) and limit
            query = query.order('created_at', desc=True).limit(limit)
            
            # Execute query
            result = query.execute()
            
            if result.data:
                search_type = "text search" if text_search else "quality jobs"
                logger.info(f"Found {len(result.data)} {search_type} in '{location}' (last {hours}h)")
                return result.data
            else:
                search_type = "text search" if text_search else "quality jobs"
                logger.info(f"No {search_type} found in '{location}' (last {hours}h)")
                return []
                
        except Exception as e:
            # Handle IDNA and other connection-related errors by attempting reconnection
            if 'idna' in str(e).lower() or 'connection' in str(e).lower() or 'network' in str(e).lower():
                logger.warning(f"Connection-related error detected: {e}")
                self._connection_healthy = False
                if self._check_and_repair_connection():
                    logger.info("Retrying query after connection repair...")
                    # Retry once with the repaired connection
                    try:
                        # Recalculate cutoff and rebuild query
                        cutoff_time = datetime.now() - timedelta(hours=hours)
                        cutoff_str = cutoff_time.isoformat()
                        
                        if text_search:
                            query = self.supabase.table('jobs').select('*').gte('updated_at', cutoff_str)
                            if search_terms and search_terms.strip():
                                terms = search_terms.strip().lower()
                                query = query.or_(
                                    f'title.ilike.%{terms}%,'
                                    f'description.ilike.%{terms}%,'
                                    f'normalized_title.ilike.%{terms}%'
                                )
                        else:
                            query = self.supabase.table('jobs').select('*').in_(
                                'match_level', ['good', 'so-so']
                            ).gte('updated_at', cutoff_str)
                        
                        # FIX: Use .eq() for market exact match instead of .ilike() to handle commas
                        if location and location.strip():
                            location_clean = location.strip()
                            # Exact market match (handles "Austin, TX" perfectly)
                            try:
                                query = query.eq('market', location_clean)
                            except Exception as e:
                                print(f"⚠️ Exact market match failed: {e}")
                                location_lower = location_clean.lower()
                                query = query.ilike('market', f'%{location_lower}%')
                            
                        query = query.order('created_at', desc=True).limit(limit)
                        result = query.execute()
                        
                        if result.data:
                            search_type = "text search" if text_search else "quality jobs"
                            logger.info(f"Found {len(result.data)} {search_type} in '{location}' (last {hours}h) after reconnection")
                            return result.data
                        else:
                            return []
                            
                    except Exception as retry_error:
                        logger.error(f"Retry failed after connection repair: {retry_error}")
                        
            logger.error(f"Error searching jobs in memory database: {e}")
            return []

    def get_quality_jobs_for_count_reduction(self, location: str, hours: int = 72) -> pd.DataFrame:
        """
        Get recent 'good' and 'so-so' jobs to reduce scraping needs
        
        Args:
            location: Location to filter for (e.g., "Dallas, TX")
            hours: Hours to look back (default 72)
            
        Returns:
            DataFrame with recent quality jobs
        """
        if not self.supabase:
            return pd.DataFrame()
            
        try:
            # Calculate cutoff time
            cutoff_time = datetime.now() - timedelta(hours=hours)
            cutoff_str = cutoff_time.isoformat()
            
            # Query for quality jobs in location
            result = self.supabase.table('jobs').select('*').in_(
                'match_level', ['good', 'so-so']
            ).gte('classified_at', cutoff_str).execute()
            
            if not result.data:
                return pd.DataFrame()
            
            # Convert to DataFrame and ensure contract compliance
            df = pd.DataFrame(result.data)
            
            # CRITICAL: Map Supabase fields to pipeline contract fields
            if not df.empty:
                df = df.rename(columns={
                    'match_level': 'match',      # Pipeline expects 'match'
                    'match_reason': 'reason'     # Pipeline expects 'reason' 
                })
            
            # Filter by location if specified
            if location and len(df) > 0:
                location_normalized = location.lower().strip()
                city_part = location_normalized.split(',')[0].strip()
                
                # Filter jobs that contain the city in their location
                location_matches = df['location'].str.lower().str.contains(city_part, na=False)
                df = df[location_matches]
            
            if len(df) > 0:
                logger.info(f"Found {len(df)} quality jobs for {location} in memory database (last {hours}h)")
                quality_breakdown = df['match'].value_counts()
                logger.info(f"   Quality breakdown: {quality_breakdown.to_dict()}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting quality jobs for count reduction: {e}")
            return pd.DataFrame()
    
    def cleanup_old_records(self, days: int = 7) -> bool:
        """
        Clean up old job classifications to save space
        
        Args:
            days: Delete records older than this many days
            
        Returns:
            bool: Success status
        """
        if not self.supabase:
            return False
            
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_time.isoformat()
            
            # Delete old records
            result = self.supabase.table('jobs').delete().lt(
                'classified_at', cutoff_str
            ).execute()
            
            deleted_count = len(result.data) if result.data else 0
            if deleted_count > 0:
                logger.info(f"🧹 Cleaned up {deleted_count} old job records (older than {days} days)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")
            return False
    
    def get_memory_stats(self) -> Dict:
        """Get statistics about memory database usage"""
        if not self.supabase:
            return {'memory_available': False}
            
        try:
            # Get total record count
            result = self.supabase.table('jobs').select('job_id', count='exact').execute()
            total_count = result.count if hasattr(result, 'count') else 0
            
            # Get recent record count (last 7 days)
            cutoff_time = datetime.now() - timedelta(days=7)
            cutoff_str = cutoff_time.isoformat()
            
            recent_result = self.supabase.table('jobs').select('job_id', count='exact').gte(
                'classified_at', cutoff_str
            ).execute()
            recent_count = recent_result.count if hasattr(recent_result, 'count') else 0
            
            return {
                'memory_available': True,
                'total_records': total_count,
                'recent_records': recent_count,
                'estimated_size_mb': total_count * 2.5 / 1000  # ~2.5KB per record
            }
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {'memory_available': False, 'error': str(e)}
    
    def query_jobs_by_run_id(self, run_id: str) -> pd.DataFrame:
        """Query all jobs for a specific batch run_id"""
        if not self.supabase:
            logger.error("Supabase not connected")
            return pd.DataFrame()

        try:
            # Query jobs table for this run_id
            result = self.supabase.table('jobs').select('*').eq('run_id', run_id).execute()

            if not result.data:
                logger.warning(f"No jobs found for run_id: {run_id}")
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(result.data)
            logger.info(f"✅ Retrieved {len(df)} jobs for run_id: {run_id}")
            return df

        except Exception as e:
            logger.error(f"Failed to query jobs by run_id {run_id}: {e}")
            return pd.DataFrame()

    def test_connection(self) -> Dict:
        """Test the database connection"""
        if not self.supabase:
            return {
                'success': False,
                'message': 'Supabase not connected - check credentials'
            }

        try:
            # Try a simple query to test connection
            result = self.supabase.table('jobs').select('job_id').limit(1).execute()

            return {
                'success': True,
                'message': 'Memory database connection successful',
                'records_found': len(result.data) if result.data else 0
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Connection failed: {str(e)}',
                'error': str(e)
            }
