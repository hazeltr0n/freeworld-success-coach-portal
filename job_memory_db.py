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
        self._init_supabase()
    
    def _init_supabase(self):
        """Initialize Supabase client"""
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
            print("✅ Supabase job memory database connected")
            
        except ImportError:
            print("⚠️ Supabase not installed - pip install supabase")
        except Exception as e:
            print(f"⚠️ Supabase connection failed: {e}")
    
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
            for _, job in jobs_df.iterrows():
                # Skip jobs without complete classification data to avoid constraint violations
                # Try canonical fields first (ai.match, ai.reason, ai.summary), then fallback to legacy field names
                match = job.get('ai.match', job.get('match_level', job.get('match', '')))
                reason = job.get('ai.reason', job.get('match_reason', job.get('reason', '')))
                summary = job.get('ai.summary', job.get('summary', ''))
                
                if not all([match, reason, summary]) or any(x in ['', 'nan', None] for x in [match, reason, summary]):
                    # Skip incomplete classifications to avoid database constraint violations
                    continue
                    
                # Market sanitization: ensure no state abbreviations and map representative cities
                def _sanitize_market(val: str) -> str:
                    try:
                        from shared_search import MARKET_TO_LOCATION
                        std = {m: m for m in MARKET_TO_LOCATION.keys()}
                        inv = {v: k for k, v in MARKET_TO_LOCATION.items()}  # City, ST -> Market
                        city_map = {v.split(',')[0].strip().lower(): k for k, v in MARKET_TO_LOCATION.items()}
                    except Exception:
                        std, inv, city_map = {}, {}, {}
                    s = str(val or '').strip()
                    if not s:
                        return ''
                    if s in std:
                        return s
                    if s in inv:
                        return inv[s]
                    if ',' in s:
                        s = s.split(',')[0].strip()
                    if s.lower() in city_map:
                        return city_map[s.lower()]
                    if s.lower() == 'berkeley':
                        return 'Bay Area'
                    if s.lower() == 'ontario':
                        return 'Inland Empire'
                    return s

                record = {
                    # Core job information (exact Supabase schema) - use canonical fields
                    'job_id': job.get('id.job', job.get('job_id', '')),
                    'job_title': job.get('source.title', job.get('job_title', '')),
                    'company': job.get('source.company', job.get('company', '')),
                    'location': job.get('source.location_raw', job.get('location', '')),
                    'job_description': job.get('source.description_raw', job.get('job_description', ''))[:5000],
                    'apply_url': job.get('source.indeed_url', job.get('apply_url', '')),
                    'salary': job.get('source.salary_raw', job.get('salary', '')),
                    
                    # AI Classification results (use extracted values)
                    'match_level': match,
                    'match_reason': reason,
                    'summary': summary,
                    'fair_chance': job.get('ai.fair_chance', job.get('fair_chance', 'unknown')),
                    'endorsements': job.get('ai.endorsements', job.get('endorsements', 'unknown')),
                    'route_type': job.get('ai.route_type', job.get('route_type', '')),
                    
                    # Organization and tracking
                    'market': _sanitize_market(job.get('meta.market', job.get('market', ''))),
                    'tracked_url': job.get('meta.tracked_url', job.get('tracked_url', '')),
                    
                    # Recall context fields (new)
                    'indeed_job_url': job.get('source.indeed_url', job.get('indeed_job_url', '')),
                    'search_query': job.get('meta.query', job.get('search_query', '')),
                    'source': job.get('id.source', job.get('source', 'outscraper')),
                    'filter_reason': job.get('route.final_status', job.get('filter_reason', '')),
                    
                    # System metadata
                    'classification_source': job.get('classification_source', 'ai_classification'),
                    'classified_at': datetime.now().isoformat(),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    
                    # Deduplication fields for database-level deduplication
                    'rules_duplicate_r1': job.get('rules.duplicate_r1', ''),
                    'rules_duplicate_r2': job.get('rules.duplicate_r2', ''),
                    'clean_apply_url': job.get('clean_apply_url', ''),
                    'job_id_hash': job.get('sys.hash', '')
                }
                
                if record['job_id']:  # Only store if we have a job_id
                    records.append(record)
            
            if not records:
                logger.warning("No valid records to store in memory database")
                return False
            
            # Use batch insert with automatic deduplication
            try:
                result = self.supabase.rpc('batch_insert_jobs_with_dedup', {'p_jobs_data': records}).execute()
                
                if result.data is not None:  # RPC returns count or error
                    count = result.data if isinstance(result.data, int) else len(records)
                    logger.info(f"✅ Stored {count} job classifications with deduplication in memory database")
                    return True
                else:
                    logger.error("Failed to store job classifications with deduplication")
                    return False
                    
            except Exception as rpc_error:
                logger.warning(f"Database deduplication failed, falling back to upsert: {rpc_error}")
                
                # Fallback to traditional upsert if RPC function doesn't exist yet
                result = self.supabase.table('jobs').upsert(records).execute()
                
                if result.data:
                    logger.info(f"✅ Stored {len(result.data)} job classifications in memory database (fallback mode)")
                    return True
                else:
                    logger.error("Failed to store job classifications")
                    return False
                
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
        if not self.supabase or not job_ids:
            return {}
            
        try:
            # Calculate cutoff time
            cutoff_time = datetime.now() - timedelta(hours=hours)
            cutoff_str = cutoff_time.isoformat()
            
            # Query for matching job IDs within time window - ALL classified jobs
            # (Used to avoid re-classifying jobs, regardless of quality)
            result = self.supabase.table('jobs').select('*').in_(
                'job_id', job_ids
            ).gte('classified_at', cutoff_str).execute()
            
            if not result.data:
                return {}
            
            # Convert to lookup dictionary with all comprehensive fields
            memory_dict = {}
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
        if not self.supabase:
            logger.error("❌ Supabase not initialized")
            return []
            
        try:
            # Calculate cutoff time
            cutoff_time = datetime.now() - timedelta(hours=hours)
            cutoff_str = cutoff_time.isoformat()
            
            # Base query for recent jobs - prioritize quality jobs unless text search is enabled
            if text_search:
                # Text-based search across all job qualities
                query = self.supabase.table('jobs').select('*').gte('created_at', cutoff_str)
                
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
                ).gte('created_at', cutoff_str)
            
            # Add location filter if provided
            if location and location.strip():
                location_clean = location.strip().lower()
                query = query.or_(
                    f'location.ilike.%{location_clean}%,'
                    f'normalized_location.ilike.%{location_clean}%,'
                    f'market.ilike.%{location_clean}%'
                )
                
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
