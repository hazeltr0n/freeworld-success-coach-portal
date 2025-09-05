"""
Simplified Search Bypass System
Uses pre-computed link_active status from Supabase background process
Much faster since no real-time link checking needed!
"""
import pandas as pd
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from job_memory_db import JobMemoryDB

logger = logging.getLogger(__name__)

class SimplifiedBypassSystem:
    """Simplified bypass system using pre-computed link status"""
    
    def __init__(self):
        self.memory_db = JobMemoryDB()
    
    def check_bypass_opportunity(self, location: str, hours_back: int = 24, min_jobs: int = 100) -> Dict:
        """
        Check if we can bypass Indeed scraping using pre-validated jobs
        Much faster since link checking is done in background!
        """
        logger.info(f"🔍 Checking bypass opportunity for {location}")
        
        if not self.memory_db.supabase:
            return {'can_bypass': False, 'reason': 'Memory database not available'}
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            cutoff_str = cutoff_time.isoformat()
            
            # Get recent quality jobs with ACTIVE links only
            result = self.memory_db.supabase.table('jobs').select(
                'job_id', 'job_title', 'company', 'location', 'match_level', 
                'apply_url', 'link_active', 'link_checked_at', 'classified_at'
            ).in_(
                'match_level', ['good', 'so-so']
            ).eq(
                'link_active', True  # Only include jobs with verified active links!
            ).gte('classified_at', cutoff_str).execute()
            
            if not result.data:
                return {
                    'can_bypass': False, 
                    'reason': f'No recent quality jobs with active links found',
                    'active_jobs_found': 0
                }
            
            # Filter by location
            all_jobs_df = pd.DataFrame(result.data)
            location_filtered = self._filter_by_location(all_jobs_df, location)
            
            active_job_count = len(location_filtered)
            
            if active_job_count < min_jobs:
                return {
                    'can_bypass': False,
                    'reason': f'Only {active_job_count} active jobs found (need {min_jobs})',
                    'active_jobs_found': active_job_count,
                    'jobs_df': location_filtered
                }
            
            # SUCCESS! We have enough active jobs
            logger.info(f"✅ Bypass viable: {active_job_count} verified active jobs found")
            
            return {
                'can_bypass': True,
                'reason': f'{active_job_count} verified active jobs found',
                'active_jobs_found': active_job_count,
                'jobs_df': location_filtered,
                'quality_breakdown': location_filtered['match_level'].value_counts().to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error checking bypass: {e}")
            return {'can_bypass': False, 'reason': f'Database error: {str(e)}'}
    
    def execute_bypass(self, location: str, mode_info: Dict) -> Dict:
        """
        Execute bypass - much simpler now since links are pre-validated!
        """
        target_jobs = mode_info.get('limit', 100)
        min_bypass_jobs = max(50, target_jobs // 2)
        
        bypass_check = self.check_bypass_opportunity(location, 24, min_bypass_jobs)
        
        if not bypass_check['can_bypass']:
            return {
                'bypass_executed': False,
                'reason': bypass_check['reason'],
                'active_jobs_df': pd.DataFrame()
            }
        
        # SUCCESS! Return pre-validated active jobs
        active_jobs_df = bypass_check['jobs_df']
        
        logger.info(f"🚀 BYPASS EXECUTED!")
        logger.info(f"   Using {len(active_jobs_df)} pre-validated active jobs")
        logger.info(f"   Estimated cost saved: $2.00")
        logger.info(f"   No real-time link checking needed!")
        
        return {
            'bypass_executed': True,
            'reason': f'Using {len(active_jobs_df)} pre-validated active jobs',
            'active_jobs_df': active_jobs_df,
            'jobs_found': len(active_jobs_df),
            'cost_saved': 2.00,
            'link_validation': 'Pre-computed by background process'
        }
    
    def _filter_by_location(self, df: pd.DataFrame, location: str) -> pd.DataFrame:
        """Filter DataFrame by location with flexible matching"""
        if df.empty or not location:
            return df
        
        location_lower = location.lower().strip()
        
        if ',' in location_lower:
            city = location_lower.split(',')[0].strip()
        else:
            city = location_lower
        
        location_mask = df['location'].str.lower().str.contains(city, na=False)
        return df[location_mask].copy()
    
    def get_link_checking_stats(self) -> Dict:
        """Get statistics about background link checking"""
        if not self.memory_db.supabase:
            return {'error': 'Database not available'}
        
        try:
            # Get link checking statistics
            result = self.memory_db.supabase.table('jobs').select(
                'link_active', 'link_checked_at'
            ).not_('link_checked_at', 'is', None).execute()
            
            if not result.data:
                return {'total_checked': 0, 'needs_background_process': True}
            
            df = pd.DataFrame(result.data)
            
            total_checked = len(df)
            active_count = len(df[df['link_active'] == True])
            expired_count = len(df[df['link_active'] == False])
            
            # Check how recent the checks are
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_checks = len(df[pd.to_datetime(df['link_checked_at']) > recent_cutoff])
            
            return {
                'total_checked': total_checked,
                'active_links': active_count,
                'expired_links': expired_count,
                'expiration_rate': expired_count / total_checked * 100 if total_checked > 0 else 0,
                'recent_checks_24h': recent_checks,
                'background_process_working': recent_checks > 0
            }
            
        except Exception as e:
            return {'error': str(e)}