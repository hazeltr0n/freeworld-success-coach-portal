"""
Airtable integration for uploading job data directly to Airtable bases.
"""
import os
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class AirtableUploader:
    """Handles uploading job data directly to Airtable using the API."""
    
    def __init__(self):
        """Initialize Airtable uploader using environment variables.

        Required env vars:
          - AIRTABLE_API_KEY
          - AIRTABLE_BASE_ID
          - AIRTABLE_JOBS_TABLE_ID (preferred) or AIRTABLE_TABLE_ID (fallback)
        """
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.table_id = os.getenv('AIRTABLE_JOBS_TABLE_ID') or os.getenv('AIRTABLE_TABLE_ID')

        if not all([self.api_key, self.base_id, self.table_id]):
            print("⚠️ Airtable credentials not set (AIRTABLE_API_KEY/BASE_ID/JOBS_TABLE_ID). Running without Airtable upload.")
            self.api = None
            self.table = None
            return

        try:
            from pyairtable import Api
            self.api = Api(self.api_key)
            self.table = self.api.table(self.base_id, self.table_id)
            print(f"✅ Airtable connection initialized (base={self.base_id}, table={self.table_id})")
        except ImportError:
            print("⚠️ pyairtable not installed - pip install pyairtable")
            self.api = None
            self.table = None
        except Exception as e:
            print(f"⚠️ Airtable connection failed: {e}")
            self.api = None
            self.table = None
    
    def _dataframe_to_airtable_records(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert DataFrame to Airtable record format."""
        records = []
        
        # Field mapping for Airtable dropdown compatibility - pipeline should now pass correct format
        market_mapping = {
            'Custom': 'Houston',  # Map to existing market
            'Unknown': 'Houston',
            '': 'Houston',
            'nan': 'Houston',  # Handle NaN values
            # Legacy mappings for any old data
            'San Francisco': 'Bay Area',
            'Los Angeles': 'Inland Empire', 
            'Sacramento': 'Stockton',
            'Ontario': 'Inland Empire',  # Legacy - pipeline should now send "Inland Empire"
            # All core markets should pass through as-is since pipeline sends Airtable format
            'Houston': 'Houston',
            'Dallas': 'Dallas', 
            'Bay Area': 'Bay Area',
            'Stockton': 'Stockton',
            'Denver': 'Denver',
            'Las Vegas': 'Las Vegas',
            'Newark': 'Newark',
            'Phoenix': 'Phoenix',
            'Trenton': 'Trenton',
            'Inland Empire': 'Inland Empire',
            'San Antonio': 'San Antonio',
            'Austin': 'Austin'
        }
        
        fair_chance_mapping = {
            'no_requirements_mentioned': 'No Requirements',
            'fair_chance_employer': 'Fair Chance',
            'background_check_required': 'Background Check',
            'unknown': 'Unknown',
            '': 'Unknown'
        }
        
        endorsements_mapping = {
            'none_required': 'None',
            'hazmat': 'Hazmat',
            'passenger': 'Passenger',
            'school_bus': 'School Bus',
            'unknown': 'Unknown',
            '': 'Unknown'
        }
        
        for _, row in df.iterrows():
            # Apply field mappings with proper NaN handling
            raw_market = row.get('meta.market', row.get('market', ''))
            if pd.isna(raw_market) or raw_market == '' or str(raw_market).lower() == 'nan':
                raw_market = 'Unknown'
            raw_market = str(raw_market)
            
            # Convert new format (Dallas, TX) back to old format (Dallas) for Airtable compatibility
            if ', TX' in raw_market:
                raw_market = raw_market.replace(', TX', '')
            elif ', CA' in raw_market:
                raw_market = raw_market.replace(', CA', '')
            elif ', NV' in raw_market:
                raw_market = raw_market.replace(', NV', '')
            elif ', NJ' in raw_market:
                raw_market = raw_market.replace(', NJ', '')
            elif ', AZ' in raw_market:
                raw_market = raw_market.replace(', AZ', '')
            elif ', CO' in raw_market:
                raw_market = raw_market.replace(', CO', '')
            elif ', OR' in raw_market:
                raw_market = raw_market.replace(', OR', '')
            
            mapped_market = market_mapping.get(raw_market, raw_market)
            
            raw_fair_chance = str(row.get('ai.fair_chance', row.get('fair_chance', 'unknown')))
            mapped_fair_chance = fair_chance_mapping.get(raw_fair_chance, raw_fair_chance)
            
            raw_endorsements = str(row.get('ai.endorsements', row.get('endorsements', 'unknown')))
            mapped_endorsements = endorsements_mapping.get(raw_endorsements, raw_endorsements)
            
            # Map canonical DataFrame fields to Airtable fields (core fields only)
            record = {
                'Title': str(row.get('source.title', row.get('job_title', ''))),
                'Company': str(row.get('source.company', row.get('company', ''))),
                'Location': str(row.get('source.location_raw', row.get('location', ''))),
                'Description': str(row.get('ai.summary', row.get('summary', '')))[:50000],  # AI summary
                'Apply Here': str(row.get('meta.tracked_url', row.get('source.url', ''))),  # Tracked URL first, fallback to consolidated source URL
                'Market': mapped_market,
                'job_id': str(row.get('id.job', row.get('job_id', ''))),
                'match_level': str(row.get('ai.match', row.get('match', ''))),  # Canonical AI field
                'match_reason': str(row.get('ai.reason', row.get('reason', ''))),  # Canonical AI field
                'route_type': str(row.get('ai.route_type', row.get('route_type', ''))),
                # Skip fair_chance_level and endorsements for now - may not exist in Airtable schema
                'apply_urls': str(row.get('source.url', '')),  # Use consolidated source URL
                'Query': str(row.get('meta.query', row.get('query', ''))),
                'salary': str(row.get('source.salary_raw', row.get('salary', ''))),  # Raw salary for Free Agents
                'source': str(row.get('id.source', row.get('source', '')))  # Job source for tracking
                # Note: Detailed salary analysis fields stay in Supabase only
            }
            
            # Only include non-empty records
            if record['Title'] or record['Company']:
                records.append(record)
        
        return records
    
    def _batch_upload_with_retry(self, records: List[Dict[str, Any]], max_retries: int = 3) -> List[Dict]:
        """Upload records in batches with retry logic for rate limiting."""
        if not self.table:
            raise Exception("Airtable not connected")
            
        uploaded_records = []
        
        # Process in batches of 10 (Airtable API limit)
        batch_size = 10
        total_batches = (len(records) + batch_size - 1) // batch_size
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"Uploading batch {batch_num}/{total_batches} ({len(batch)} records)")
            
            for attempt in range(max_retries + 1):
                try:
                    # Upload batch to Airtable
                    result = self.table.batch_create(batch)
                    uploaded_records.extend(result)
                    logger.info(f"Successfully uploaded batch {batch_num}")
                    break
                    
                except Exception as e:
                    if '429' in str(e) and attempt < max_retries:
                        # Rate limited - wait and retry
                        wait_time = (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Failed to upload batch {batch_num}: {e}")
                        if attempt == max_retries:
                            raise
            
            # Brief pause between batches to respect rate limits
            time.sleep(0.2)  # 5 requests per second = 0.2s between requests
        
        return uploaded_records
    
    def _check_existing_jobs(self, job_ids: List[str]) -> List[str]:
        """Check which job IDs already exist in Airtable."""
        if not self.table:
            return []
            
        try:
            # Query Airtable for existing job IDs
            # Use batch queries to handle large lists efficiently
            existing_ids = []
            batch_size = 100  # Airtable query limit
            
            for i in range(0, len(job_ids), batch_size):
                batch_ids = job_ids[i:i + batch_size]
                # Create OR formula for batch
                id_conditions = [f"{{job_id}} = '{job_id}'" for job_id in batch_ids]
                formula = f"OR({', '.join(id_conditions)})"
                
                records = self.table.all(formula=formula, fields=['job_id'])
                existing_ids.extend([record['fields']['job_id'] for record in records])
                
                # Rate limiting
                time.sleep(0.1)
            
            return existing_ids
            
        except Exception as e:
            logger.warning(f"Failed to check existing jobs: {e}")
            return []  # If check fails, proceed with upload (better than failing completely)

    def upload_jobs(self, df: pd.DataFrame, dry_run: bool = False) -> Dict[str, Any]:
        """
        Upload job data to Airtable.
        
        Args:
            df: DataFrame with job data
            dry_run: If True, only validate data without uploading
            
        Returns:
            Dict with upload results and statistics
        """
        if not self.table:
            return {
                'success': False,
                'message': 'Airtable not connected - check credentials',
                'total_jobs': len(df),
                'uploaded_count': 0
            }
            
        logger.info(f"Starting Airtable upload for {len(df)} jobs")
        
        # Check for existing jobs to avoid duplicates
        # Support both canonical format (id.job) and legacy format (job_id)
        job_id_col = None
        if 'id.job' in df.columns:
            job_id_col = 'id.job'
        elif 'job_id' in df.columns:
            job_id_col = 'job_id'
        
        job_ids = df[job_id_col].tolist() if job_id_col else []
        existing_ids = self._check_existing_jobs(job_ids) if job_ids else []
        
        if existing_ids:
            print(f"📋 Found {len(existing_ids)} existing jobs in Airtable, skipping duplicates")
            # Filter out existing jobs
            df_filtered = df[~df[job_id_col].isin(existing_ids)] if job_id_col else df
            print(f"📤 Uploading {len(df_filtered)} new jobs (skipped {len(df) - len(df_filtered)} duplicates)")
        else:
            df_filtered = df
            print(f"📤 No existing jobs found, uploading all {len(df)} jobs")
        
        if len(df_filtered) == 0:
            return {
                'success': True,
                'message': 'All jobs already exist in Airtable',
                'total_jobs': len(df),
                'uploaded_count': 0,
                'skipped_count': len(df)
            }
        
        # Convert DataFrame to Airtable records
        records = self._dataframe_to_airtable_records(df_filtered)
        
        if not records:
            return {
                'success': False,
                'message': 'No valid records to upload',
                'total_jobs': len(df),
                'uploaded_count': 0
            }
        
        if dry_run:
            return {
                'success': True,
                'message': f'Dry run: {len(records)} records ready for upload',
                'total_jobs': len(df),
                'records_ready': len(records)
            }
        
        try:
            # Upload records in batches
            uploaded_records = self._batch_upload_with_retry(records)
            
            logger.info(f"Successfully uploaded {len(uploaded_records)} records to Airtable")
            
            skipped_count = len(df) - len(df_filtered)
            return {
                'success': True,
                'message': f'Successfully uploaded {len(uploaded_records)} jobs to Airtable (skipped {skipped_count} duplicates)',
                'total_jobs': len(df),
                'uploaded_count': len(uploaded_records),
                'skipped_count': skipped_count,
                'uploaded_records': uploaded_records
            }
            
        except Exception as e:
            logger.error(f"Airtable upload failed: {e}")
            return {
                'success': False,
                'message': f'Upload failed: {str(e)}',
                'total_jobs': len(df),
                'uploaded_count': 0,
                'error': str(e)
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the Airtable connection and credentials."""
        if not self.table:
            return {
                'success': False,
                'message': 'Airtable not connected - check credentials'
            }
            
        try:
            # Try to get first few records to test connection
            records = self.table.all(max_records=1)
            return {
                'success': True,
                'message': 'Connection successful',
                'records_found': len(records)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection failed: {str(e)}',
                'error': str(e)
            }
    
    def get_recent_jobs(self, hours: int = 72) -> pd.DataFrame:
        """
        Retrieve jobs from Airtable that were added within the last X hours.
        
        Args:
            hours: Number of hours to look back (default 72)
            
        Returns:
            DataFrame with recent jobs and their classifications
        """
        if not self.table:
            return pd.DataFrame()
            
        try:
            # Calculate cutoff time with proper timezone handling
            from datetime import timezone
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            cutoff_str = cutoff_time.isoformat()
            
            logger.info(f"Retrieving jobs from Airtable added in last {hours} hours...")
            logger.info(f"Cutoff time: {cutoff_str}")
            
            # Get all records (Airtable auto-sorts by creation time, newest first)
            # We'll filter by created time on our end since Airtable's filtering can be complex
            all_records = self.table.all()
            logger.info(f"Total Airtable records: {len(all_records)}")
            
            recent_jobs = []
            for record in all_records:
                created_time = record.get('createdTime', '')
                if created_time:
                    # Proper datetime comparison instead of string comparison
                    try:
                        from dateutil.parser import parse
                        job_created_dt = parse(created_time)
                        if job_created_dt > cutoff_time:
                            job_data = {
                                'airtable_id': record['id'],
                                'job_id': record['fields'].get('job_id', ''),  # Critical for memory lookup
                                'job_title': record['fields'].get('Title', ''),
                                'company': record['fields'].get('Company', ''),
                                'location': record['fields'].get('Location', ''),
                                'job_description': record['fields'].get('Description', ''),
                                'apply_url': record['fields'].get('Apply Here', ''),
                                'apply_urls': record['fields'].get('apply_urls', ''),
                                'match_level': record['fields'].get('match_level', ''),
                                'match_reason': record['fields'].get('match_reason', ''),
                                'route_type': record['fields'].get('route_type', ''),
                                'market': record['fields'].get('Market', ''),
                                'final_status': 'included',  # Assume included if in Airtable
                                'source': 'airtable',
                                'created_time': created_time,
                                'is_verified': record['fields'].get('is_verified', ''),
                                'true_match': record['fields'].get('true_match', ''),
                                'override_match': record['fields'].get('override_match', ''),
                                'override_match_reason': record['fields'].get('override_match_reason', ''),
                                'fair_chance_level': record['fields'].get('fair_chance_level', '')
                                # Note: Removed 'posting_type' field - not present in Airtable schema
                            }
                            
                            # Use job_id from Airtable if available, otherwise generate it
                            if not job_data['job_id'] and job_data['company'] and job_data['location'] and job_data['job_title']:
                                import hashlib
                                base_string = f"{job_data['company'].lower().strip()}|{job_data['location'].lower().strip()}|{job_data['job_title'].lower().strip()}"
                                job_data['job_id'] = hashlib.md5(base_string.encode()).hexdigest()
                            
                            if job_data['job_id']:  # Only add if we have a job_id
                                recent_jobs.append(job_data)
                    except Exception as e:
                        logger.warning(f"Error parsing created time {created_time}: {e}")
                        continue
                else:
                    # Records are sorted by creation time, so we can break early
                    break
            
            df = pd.DataFrame(recent_jobs)
            logger.info(f"Retrieved {len(df)} recent jobs from Airtable")
            
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving recent jobs from Airtable: {e}")
            return pd.DataFrame()
    
    def get_jobs_for_continuity(self, hours: int = 24) -> pd.DataFrame:
        """
        Get jobs from Airtable that should be included for continuity
        (recent jobs that might not be in current scrape).
        
        Args:
            hours: Number of hours to look back for continuity (default 24)
            
        Returns:
            DataFrame with jobs for continuity inclusion
        """
        recent_df = self.get_recent_jobs(hours)
        
        # All jobs in Airtable are considered 'included' for continuity
        # (They wouldn't be in Airtable if they weren't good candidates)
        continuity_jobs = recent_df.copy()
        
        if len(continuity_jobs) > 0:
            logger.info(f"Found {len(continuity_jobs)} jobs for continuity inclusion")
            
        return continuity_jobs
    
    def get_good_jobs_for_count_reduction(self, location: str, hours: int = 72) -> pd.DataFrame:
        """
        Get recent 'good' and 'so-so' jobs from Airtable to reduce scraping needs.
        This is a cost optimization - instead of scraping 1000 fresh jobs,
        we can include recent quality jobs and scrape only the difference.
        
        Args:
            location: Location to filter for (e.g., "Dallas, TX")
            hours: Hours to look back (default 72)
            
        Returns:
            DataFrame with recent good/so-so jobs for this location
        """
        try:
            # Get recent jobs
            recent_df = self.get_recent_jobs(hours)
            
            if recent_df.empty:
                return pd.DataFrame()
            
            # Filter for good and so-so jobs only
            quality_jobs = recent_df[
                recent_df['match_level'].isin(['good', 'so-so'])
            ].copy()
            
            # Filter by location if specified
            if location:
                # Normalize location for matching
                location_normalized = location.lower().strip()
                location_matches = quality_jobs['location'].str.lower().str.contains(
                    location_normalized.split(',')[0].strip(),  # Just city part
                    na=False
                )
                quality_jobs = quality_jobs[location_matches]
            
            if len(quality_jobs) > 0:
                logger.info(f"Found {len(quality_jobs)} recent quality jobs for {location} (last {hours}h)")
                quality_breakdown = quality_jobs['match_level'].value_counts()
                logger.info(f"   Quality breakdown: {quality_breakdown.to_dict()}")
            
            return quality_jobs
            
        except Exception as e:
            logger.error(f"Error getting quality jobs for count reduction: {e}")
            return pd.DataFrame()
    
    def check_job_memory(self, job_ids: List[str], hours: int = 72) -> Dict[str, Dict]:
        """
        Check which job IDs already exist in Airtable and return their classifications.
        
        Args:
            job_ids: List of job IDs to check
            hours: Hours to look back (default 72)
            
        Returns:
            Dict mapping job_id to job data for known jobs
        """
        recent_df = self.get_recent_jobs(hours)
        
        if recent_df.empty:
            return {}
        
        # Find matches
        known_jobs = recent_df[recent_df['job_id'].isin(job_ids)]
        
        # Convert to dictionary for easy lookup
        memory_dict = {}
        for _, job in known_jobs.iterrows():
            memory_dict[job['job_id']] = {
                'job_title': job['job_title'],
                'company': job['company'],
                'location': job['location'],
                'job_description': job['job_description'],
                'apply_url': job['apply_url'],
                'match': job['match_level'],  # Airtable 'match_level' -> our 'match'
                'reason': job['match_reason'],  # Airtable 'match_reason' -> our 'reason'
                'route_type': job['route_type'],
                'market': job['market'],
                'final_status': job['final_status'],
                'source': 'airtable_memory',
                'job_id': job['job_id'],
                'airtable_id': job['airtable_id']
            }
        
        logger.info(f"Found {len(memory_dict)} jobs in Airtable memory out of {len(job_ids)} checked")
        
        return memory_dict
