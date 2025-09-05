"""
Search Bypass System
Checks for recent quality jobs to bypass expensive Indeed scraping
"""
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from job_memory_db import JobMemoryDB
from indeed_link_checker import IndeedLinkChecker

logger = logging.getLogger(__name__)

class SearchBypassSystem:
    """System to bypass Indeed scraping when sufficient recent quality jobs exist"""
    
    def __init__(self):
        self.memory_db = JobMemoryDB()
        self.link_checker = IndeedLinkChecker(delay_between_requests=0.5)
    
    def check_bypass_opportunity(self, location: str, hours_back: int = 24, min_jobs: int = 100) -> Dict:
        """
        Check if we can bypass Indeed scraping due to recent quality jobs
        
        Args:
            location: Search location (e.g., "Dallas, TX")
            hours_back: Hours to look back for recent jobs (default 24)
            min_jobs: Minimum quality jobs needed to bypass (default 100)
            
        Returns:
            Dict with bypass decision and job counts
        """
        logger.info(f"🔍 Checking bypass opportunity for {location} (last {hours_back}h, min {min_jobs} jobs)")
        
        if not self.memory_db.supabase:
            return {
                'can_bypass': False,
                'reason': 'Memory database not available',
                'quality_jobs_found': 0
            }
        
        try:
            # Get recent quality jobs from memory database
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            cutoff_str = cutoff_time.isoformat()
            
            # Query for recent good and so-so jobs in the location
            result = self.memory_db.supabase.table('jobs').select(
                'job_id', 'job_title', 'company', 'location', 'match_level', 
                'apply_url', 'classified_at'
            ).in_(
                'match_level', ['good', 'so-so']
            ).gte('classified_at', cutoff_str).execute()
            
            if not result.data:
                logger.info(f"   No recent quality jobs found for {location}")
                return {
                    'can_bypass': False,
                    'reason': f'No recent quality jobs found in last {hours_back}h',
                    'quality_jobs_found': 0
                }
            
            # Filter by location
            all_jobs_df = pd.DataFrame(result.data)
            location_filtered = self._filter_by_location(all_jobs_df, location)
            
            if location_filtered.empty:
                logger.info(f"   No jobs found for location {location}")
                return {
                    'can_bypass': False,
                    'reason': f'No quality jobs found for {location} in last {hours_back}h',
                    'quality_jobs_found': 0
                }
            
            quality_count = len(location_filtered)
            logger.info(f"   Found {quality_count} recent quality jobs for {location}")
            
            # Check if we have enough jobs to consider bypassing
            if quality_count < min_jobs:
                logger.info(f"   Not enough jobs ({quality_count} < {min_jobs}) to bypass search")
                return {
                    'can_bypass': False,
                    'reason': f'Only {quality_count} quality jobs found (need {min_jobs})',
                    'quality_jobs_found': quality_count,
                    'jobs_df': location_filtered
                }
            
            # We have enough jobs - this is a bypass opportunity
            logger.info(f"✅ Bypass opportunity detected: {quality_count} quality jobs available")
            
            return {
                'can_bypass': True,
                'reason': f'{quality_count} recent quality jobs found - can bypass Indeed search',
                'quality_jobs_found': quality_count,
                'jobs_df': location_filtered,
                'breakdown': location_filtered['match_level'].value_counts().to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error checking bypass opportunity: {e}")
            return {
                'can_bypass': False,
                'reason': f'Error checking memory database: {str(e)}',
                'quality_jobs_found': 0
            }
    
    def execute_bypass_with_link_check(self, jobs_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Execute bypass by filtering jobs with active Indeed links
        
        Args:
            jobs_df: DataFrame with recent quality jobs
            
        Returns:
            Tuple of (active_jobs_df, link_check_results)
        """
        if jobs_df.empty:
            logger.warning("No jobs provided for link checking")
            return pd.DataFrame(), {}
        
        original_count = len(jobs_df)
        logger.info(f"🔗 Checking job links for expiration...")
        logger.info(f"   Note: Only Indeed URLs can be checked - other URLs assumed active")
        
        # Use indeed_job_url if available, otherwise fall back to apply_url  
        url_column = 'indeed_job_url' if 'indeed_job_url' in jobs_df.columns and jobs_df['indeed_job_url'].notna().any() else 'apply_url'
        
        # Filter out jobs without URLs
        jobs_with_urls = jobs_df[jobs_df[url_column].notna() & (jobs_df[url_column] != '')].copy()
        
        if jobs_with_urls.empty:
            logger.warning(f"No jobs have valid URLs in {url_column} column")
            return pd.DataFrame(), {'no_urls': True}
        
        # Check link expiration
        active_jobs_df, check_results = self.link_checker.filter_active_jobs(jobs_with_urls, url_column)
        
        active_count = len(active_jobs_df)
        expired_count = original_count - active_count
        
        results_summary = {
            'original_jobs': original_count,
            'jobs_with_urls': len(jobs_with_urls),
            'active_jobs': active_count,
            'expired_jobs': expired_count,
            'success_rate': (active_count / original_count * 100) if original_count > 0 else 0,
            'check_results': check_results
        }
        
        logger.info(f"📊 Link checking complete:")
        logger.info(f"   Original quality jobs: {original_count}")
        logger.info(f"   Jobs with URLs: {len(jobs_with_urls)}")
        logger.info(f"   Active jobs: {active_count}")
        logger.info(f"   Expired jobs: {expired_count}")
        logger.info(f"   Success rate: {results_summary['success_rate']:.1f}%")
        
        return active_jobs_df, results_summary
    
    def execute_full_bypass(self, location: str, hours_back: int = 24, min_jobs: int = 100) -> Dict:
        """
        Execute complete bypass check including link validation
        
        Args:
            location: Search location
            hours_back: Hours to look back for jobs
            min_jobs: Minimum active jobs needed to bypass
            
        Returns:
            Dict with bypass results and active jobs DataFrame
        """
        logger.info(f"🚀 Executing full bypass check for {location}")
        
        # Step 1: Check if bypass is possible
        bypass_check = self.check_bypass_opportunity(location, hours_back, min_jobs)
        
        if not bypass_check['can_bypass']:
            logger.info(f"❌ Bypass not possible: {bypass_check['reason']}")
            return {
                'bypass_executed': False,
                'reason': bypass_check['reason'],
                'active_jobs_df': pd.DataFrame(),
                'jobs_found': bypass_check.get('quality_jobs_found', 0),
                'cost_saved': 0.0
            }
        
        # Step 2: Check links for expiration
        jobs_df = bypass_check['jobs_df']
        active_jobs_df, link_results = self.execute_bypass_with_link_check(jobs_df)
        
        active_count = len(active_jobs_df)
        
        # Step 3: Determine if we still have enough active jobs
        if active_count < min_jobs:
            logger.info(f"❌ Not enough active jobs after link check ({active_count} < {min_jobs})")
            return {
                'bypass_executed': False,
                'reason': f'Only {active_count} active jobs after link checking (need {min_jobs})',
                'active_jobs_df': active_jobs_df,
                'jobs_found': active_count,
                'link_check_results': link_results,
                'cost_saved': 0.0
            }
        
        # Step 4: Success! We can bypass Indeed scraping
        # Estimate cost saved (rough calculation)
        estimated_scraping_cost = 2.00  # Assume $2 for a full search
        
        logger.info(f"✅ BYPASS SUCCESSFUL! Using {active_count} active quality jobs")
        logger.info(f"💰 Estimated cost saved: ${estimated_scraping_cost:.2f}")
        
        return {
            'bypass_executed': True,
            'reason': f'Found {active_count} active quality jobs - bypassing Indeed search',
            'active_jobs_df': active_jobs_df,
            'jobs_found': active_count,
            'quality_breakdown': active_jobs_df['match_level'].value_counts().to_dict(),
            'link_check_results': link_results,
            'cost_saved': estimated_scraping_cost,
            'hours_back': hours_back
        }
    
    def _filter_by_location(self, df: pd.DataFrame, location: str) -> pd.DataFrame:
        """Filter DataFrame by location with flexible matching"""
        if df.empty or not location:
            return df
        
        # Normalize the target location
        location_lower = location.lower().strip()
        
        # Extract city from location (handle "City, ST" format)
        if ',' in location_lower:
            city = location_lower.split(',')[0].strip()
            state = location_lower.split(',')[1].strip()
        else:
            city = location_lower
            state = ''
        
        # Filter jobs that match the location
        location_mask = df['location'].str.lower().str.contains(city, na=False)
        
        # If we have state info, also try to match that
        if state and len(state) >= 2:
            state_mask = df['location'].str.lower().str.contains(state, na=False)
            location_mask = location_mask | state_mask
        
        return df[location_mask].copy()
    
    def get_bypass_summary(self, location: str) -> Dict:
        """Get summary of bypass opportunities for a location"""
        try:
            # Check different time windows
            windows = [6, 12, 24, 48]
            summary = {
                'location': location,
                'windows': {}
            }
            
            for hours in windows:
                check = self.check_bypass_opportunity(location, hours, min_jobs=50)  # Lower threshold for summary
                summary['windows'][f'{hours}h'] = {
                    'jobs_found': check.get('quality_jobs_found', 0),
                    'can_bypass': check.get('quality_jobs_found', 0) >= 100  # 100 job threshold
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting bypass summary: {e}")
            return {'location': location, 'error': str(e)}