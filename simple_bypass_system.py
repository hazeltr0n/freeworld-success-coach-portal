"""
Simple Search Bypass System
Bypasses Indeed scraping when sufficient recent quality jobs exist
NO link checking - assumes recent jobs are still active
"""
import pandas as pd
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from job_memory_db import JobMemoryDB

logger = logging.getLogger(__name__)

class SimpleBypassSystem:
    """Simple bypass system without link checking complexity"""
    
    def __init__(self):
        self.memory_db = JobMemoryDB()
    
    def check_bypass_opportunity(self, location: str, hours_back: int = 96, min_jobs: int = 100, route_filter: str = "both") -> Dict:
        """
        Check if we can bypass Indeed scraping using recent quality jobs
        Assumes recent jobs are still active (no link checking)
        """
        route_msg = f", route: {route_filter}" if route_filter != "both" else ""
        logger.info(f"🔍 Checking bypass opportunity for {location} (last {hours_back}h, need {min_jobs} jobs{route_msg})")
        
        if not self.memory_db.supabase:
            return {
                'can_bypass': False,
                'reason': 'Memory database not available',
                'jobs_found': 0
            }
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            cutoff_str = cutoff_time.isoformat()
            
            # Get recent quality jobs from memory database for this specific location
            # Extract city name from location for better matching
            location_parts = location.replace(',', '').split()
            city_name = location_parts[0] if location_parts else location
            
            result = self.memory_db.supabase.table('jobs').select(
                'job_id', 'job_title', 'company', 'location', 'job_description', 'match_level', 
                'match_reason', 'apply_url', 'classified_at', 'route_type', 'market',
                'salary', 'fair_chance', 'endorsements',
                'summary'  # CRITICAL: Include summary for complete contract
            ).in_(
                'match_level', ['good', 'so-so']
            ).filter(
                'summary', 'not.is', 'null'  # ONLY return jobs with complete classification data
            ).filter(
                'summary', 'neq', 'nan'  # Exclude string "nan" values (database cleanup needed)
            ).gte('classified_at', cutoff_str).ilike(
                'location', f'%{city_name}%'  # Filter by city name in the database query
            ).limit(100).execute()  # Get up to 100 quality jobs
            
            if not result.data:
                return {
                    'can_bypass': False,
                    'reason': f'No recent quality jobs found in last {hours_back}h',
                    'jobs_found': 0
                }
            
            # Filter by location and ensure contract compliance
            all_jobs_df = pd.DataFrame(result.data)
            
            # CRITICAL: Map Supabase fields to pipeline contract fields
            if not all_jobs_df.empty:
                all_jobs_df = all_jobs_df.rename(columns={
                    'match_level': 'match',         # Pipeline expects 'match'
                    'match_reason': 'reason',       # Pipeline expects 'reason' 
                    # Note: removal_reason not available in Pipeline v3 schema
                })
                
                # Convert string "nan" to actual NaN (database cleanup needed)
                for col in ['match', 'reason', 'summary', 'job_title', 'company']:
                    if col in all_jobs_df.columns:
                        all_jobs_df[col] = all_jobs_df[col].replace('nan', None)
            
            location_filtered = self._filter_by_location(all_jobs_df, location)
            
            # Apply route filtering (exact selection only)
            route_filtered = self._apply_route_filter(location_filtered, route_filter)
            
            jobs_count = len(route_filtered)
            
            # Allow bypass if we're within 1 job of the threshold (close enough)
            if jobs_count < (min_jobs - 1):
                logger.info(f"   Not enough jobs ({jobs_count} < {min_jobs}) to bypass search")
                return {
                    'can_bypass': False,
                    'reason': f'Only {jobs_count} quality jobs found (need {min_jobs})',
                    'jobs_found': jobs_count,
                    'jobs_df': route_filtered
                }
            
            # SUCCESS! We have enough recent quality jobs
            logger.info(f"✅ Bypass opportunity detected: {jobs_count} quality jobs available")
            
            return {
                'can_bypass': True,
                'reason': f'{jobs_count} recent quality jobs found - can bypass Indeed search',
                'jobs_found': jobs_count,
                'jobs_df': route_filtered,
                'quality_breakdown': route_filtered['match'].value_counts().to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error checking bypass opportunity: {e}")
            return {
                'can_bypass': False,
                'reason': f'Database error: {str(e)}',
                'jobs_found': 0
            }
    
    def execute_bypass(self, location: str, mode_info: Dict, route_filter: str = "both") -> Dict:
        """
        Smart Job Credit System: Full Bypass, Smart Credit, or Full Scraping
        """
        target_jobs = mode_info.get('limit', 100)
        
        # Cost per job and quality rate constants
        COST_PER_JOB = 0.001  # $0.001 per job scraped
        QUALITY_RATE = 0.15   # 15% of jobs are quality
        
        expected_quality_jobs = int(target_jobs * QUALITY_RATE)
        
        # Special case: For large searches (1000 jobs), cap at 100 jobs for better UX
        if target_jobs >= 1000:
            min_bypass_jobs = 100
        else:
            min_bypass_jobs = expected_quality_jobs
        
        logger.info(f"🚀 Smart Job Credit Analysis for {location}")
        logger.info(f"   Target scraping: {target_jobs} jobs → Expected quality: {expected_quality_jobs}")
        logger.info(f"   Full bypass threshold: {min_bypass_jobs} quality jobs")
        
        # Get available quality jobs from memory (with route filtering)
        memory_check = self.check_bypass_opportunity(location, hours_back=96, min_jobs=1, route_filter=route_filter)  # Check for any jobs
        available_quality_jobs = memory_check.get('jobs_found', 0)
        
        # Decision Logic: Full Bypass, Smart Credit, or Full Scraping
        if available_quality_jobs >= (min_bypass_jobs - 1):  # Full Bypass (flexible threshold)
            return self._execute_full_bypass(location, target_jobs, expected_quality_jobs, memory_check)
        elif available_quality_jobs >= 3:  # Smart Credit (minimum 3 jobs for efficiency)
            return self._execute_smart_credit(location, target_jobs, expected_quality_jobs, available_quality_jobs, memory_check)
        else:  # Full Scraping
            return self._execute_full_scraping(location, target_jobs, expected_quality_jobs, available_quality_jobs)
    
    def _execute_full_bypass(self, location: str, target_jobs: int, expected_quality_jobs: int, memory_check: Dict) -> Dict:
        """Full Bypass: Skip all scraping, use memory jobs only"""
        jobs_df = memory_check['jobs_df']
        cost_saved = target_jobs * 0.001
        
        logger.info(f"✅ FULL BYPASS EXECUTED!")
        logger.info(f"   Using {len(jobs_df)} recent quality jobs")
        logger.info(f"   Would have scraped {target_jobs} jobs (${target_jobs * 0.001:.3f})")
        logger.info(f"   💰 Cost saved: ${cost_saved:.3f}")
        logger.info(f"   ⚡ Skipping Indeed scraping entirely!")
        
        return {
            'bypass_executed': True,
            'bypass_type': 'FULL_BYPASS',
            'reason': f'Found {len(jobs_df)} recent quality jobs - full bypass',
            'jobs_df': jobs_df,
            'jobs_found': len(jobs_df),
            'scrape_jobs_needed': 0,
            'cost_saved': cost_saved,
            'quality_breakdown': memory_check.get('quality_breakdown', {}),
            'hours_back': 96
        }
    
    def _execute_smart_credit(self, location: str, target_jobs: int, expected_quality_jobs: int, available_quality_jobs: int, memory_check: Dict) -> Dict:
        """Smart Credit: Use memory jobs + reduced scraping"""
        # Calculate how many more quality jobs we need
        quality_jobs_needed = max(0, expected_quality_jobs - available_quality_jobs)
        
        # Calculate reduced scraping amount
        scrape_jobs_needed = int(quality_jobs_needed / 0.15) if quality_jobs_needed > 0 else 0
        scrape_jobs_needed = min(scrape_jobs_needed, target_jobs)  # Cap at target
        
        # Cost calculations
        original_cost = target_jobs * 0.001
        reduced_cost = scrape_jobs_needed * 0.001
        cost_saved = original_cost - reduced_cost
        
        jobs_df = memory_check['jobs_df']
        
        logger.info(f"💡 SMART CREDIT EXECUTED!")
        logger.info(f"   Memory: {available_quality_jobs} quality jobs")
        logger.info(f"   Need: {quality_jobs_needed} more quality jobs")
        logger.info(f"   Scraping: {scrape_jobs_needed} jobs (reduced from {target_jobs})")
        logger.info(f"   💰 Cost: ${reduced_cost:.3f} (saved ${cost_saved:.3f}, {cost_saved/original_cost*100:.1f}% reduction)")
        
        return {
            'bypass_executed': True,
            'bypass_type': 'SMART_CREDIT',
            'reason': f'Using {available_quality_jobs} memory jobs + {scrape_jobs_needed} scraped jobs',
            'jobs_df': jobs_df,
            'jobs_found': available_quality_jobs,
            'scrape_jobs_needed': scrape_jobs_needed,
            'cost_saved': cost_saved,
            'quality_breakdown': memory_check.get('quality_breakdown', {}),
            'hours_back': 96
        }
    
    def _execute_full_scraping(self, location: str, target_jobs: int, expected_quality_jobs: int, available_quality_jobs: int) -> Dict:
        """Full Scraping: Not enough memory jobs, scrape full amount"""
        logger.info(f"🔍 FULL SCRAPING REQUIRED")
        logger.info(f"   Memory: {available_quality_jobs} quality jobs (insufficient)")
        logger.info(f"   Scraping: {target_jobs} jobs as planned")
        logger.info(f"   💰 Cost: ${target_jobs * 0.001:.3f} (no savings)")
        
        return {
            'bypass_executed': False,
            'bypass_type': 'FULL_SCRAPING',
            'reason': f'Only {available_quality_jobs} memory jobs found (need {expected_quality_jobs})',
            'jobs_df': pd.DataFrame(),
            'jobs_found': available_quality_jobs,
            'scrape_jobs_needed': target_jobs,
            'cost_saved': 0.0,
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
        
        filtered_df = df[location_mask].copy()
        
        if len(filtered_df) > 0:
            logger.info(f"   Location filter: {len(df)} → {len(filtered_df)} jobs for '{location}'")
        
        return filtered_df
    
    def _apply_route_filter(self, df: pd.DataFrame, route_filter: str) -> pd.DataFrame:
        """Apply route filtering - only include exactly what's requested"""
        if df.empty or route_filter == "both":
            return df
        
        # Only include exactly what's requested - no auto-inclusion of Unknown
        if route_filter.lower() == "local":
            # Local filter includes only Local jobs
            route_mask = df['route_type'].str.lower().isin(['local'])
        elif route_filter.lower() == "otr":
            # OTR filter includes only OTR jobs  
            route_mask = df['route_type'].str.lower().isin(['otr'])
        elif route_filter.lower() == "unknown":
            # Unknown filter includes only Unknown/empty route jobs
            route_mask = df['route_type'].str.lower().isin(['unknown', '']) | df['route_type'].isna()
        else:
            # Default to showing all jobs if filter not recognized
            return df
        
        filtered_df = df[route_mask].copy()
        
        if len(df) > len(filtered_df):
            logger.info(f"   Route filter ({route_filter}): {len(df)} → {len(filtered_df)} jobs")
        
        return filtered_df
    
    def get_bypass_summary(self, location: str) -> Dict:
        """Get summary of bypass opportunities for different time windows"""
        try:
            windows = [6, 12, 24, 48]
            summary = {
                'location': location,
                'windows': {},
                'timestamp': datetime.now().isoformat()
            }
            
            for hours in windows:
                check = self.check_bypass_opportunity(location, hours, min_jobs=50)  # Lower threshold for summary
                summary['windows'][f'{hours}h'] = {
                    'jobs_found': check.get('jobs_found', 0),
                    'can_bypass_100': check.get('jobs_found', 0) >= 100,  # Can bypass with 100 job threshold
                    'can_bypass_50': check.get('jobs_found', 0) >= 50     # Can bypass with 50 job threshold
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting bypass summary: {e}")
            return {'location': location, 'error': str(e)}
    
    def get_memory_stats(self) -> Dict:
        """Get statistics about the memory database"""
        try:
            stats = self.memory_db.get_memory_stats()
            
            if stats.get('memory_available'):
                # Add bypass-specific stats
                cutoff_24h = datetime.now() - timedelta(hours=24)
                cutoff_str = cutoff_24h.isoformat()
                
                recent_result = self.memory_db.supabase.table('jobs').select(
                    'match_level'
                ).in_('match_level', ['good', 'so-so']).gte('classified_at', cutoff_str).execute()
                
                recent_quality_count = len(recent_result.data) if recent_result.data else 0
                
                stats['recent_quality_jobs_24h'] = recent_quality_count
                stats['bypass_ready'] = recent_quality_count >= 50
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {'memory_available': False, 'error': str(e)}
    
    def force_full_bypass(self, location: str, route_filter: str = "both") -> Dict:
        """
        Force FULL_BYPASS regardless of job counts - for memory-only searches
        Returns all available quality jobs from memory
        """
        logger.info(f"🔒 FORCED FULL BYPASS for {location} (memory-only search)")
        
        if not self.memory_db.supabase:
            return {
                'bypass_executed': False,
                'bypass_type': 'FAILED',
                'reason': 'Memory database not available',
                'jobs_found': 0,
                'jobs_df': pd.DataFrame()
            }
        
        try:
            # Get ALL available quality jobs from memory (up to 96 hours back)
            memory_check = self.check_bypass_opportunity(
                location, 
                hours_back=96, 
                min_jobs=1,  # Accept any number of jobs
                route_filter=route_filter
            )
            
            available_jobs = memory_check.get('jobs_found', 0)
            jobs_df = memory_check.get('jobs_df', pd.DataFrame())
            
            if available_jobs == 0:
                logger.info("⚠️ No quality jobs found in memory - returning empty bypass")
                return {
                    'bypass_executed': True,
                    'bypass_type': 'FULL_BYPASS',
                    'reason': 'No quality jobs available in memory',
                    'jobs_found': 0,
                    'jobs_df': pd.DataFrame(),
                    'scrape_jobs_needed': 0,
                    'cost_saved': 0.0,
                    'quality_breakdown': {},
                    'hours_back': 96
                }
            
            # Force FULL_BYPASS with whatever jobs we have
            logger.info(f"✅ FORCED FULL BYPASS: Using {available_jobs} available quality jobs")
            logger.info(f"   Quality breakdown: {memory_check.get('quality_breakdown', {})}")
            logger.info(f"   ⚡ Skipping ALL scraping (memory-only mode)")
            
            return {
                'bypass_executed': True,
                'bypass_type': 'FULL_BYPASS',
                'reason': f'Memory-only search: using {available_jobs} available quality jobs',
                'jobs_df': jobs_df,
                'jobs_found': available_jobs,
                'scrape_jobs_needed': 0,
                'cost_saved': 1.0,  # Full cost savings since no scraping
                'quality_breakdown': memory_check.get('quality_breakdown', {}),
                'hours_back': 96
            }
            
        except Exception as e:
            logger.error(f"Error in force_full_bypass: {e}")
            return {
                'bypass_executed': False,
                'bypass_type': 'FAILED',
                'reason': f'Database error: {str(e)}',
                'jobs_found': 0,
                'jobs_df': pd.DataFrame()
            }