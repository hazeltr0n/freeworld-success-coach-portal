"""
Indeed Link Expiration Checker
Checks Indeed job links to verify they're still active
"""
import requests
import time
import logging
from typing import List, Dict, Tuple
from urllib.parse import urlparse, parse_qs
import re

logger = logging.getLogger(__name__)

class IndeedLinkChecker:
    """Check Indeed job links for expiration"""
    
    def __init__(self, delay_between_requests: float = 1.0):
        """
        Initialize link checker
        
        Args:
            delay_between_requests: Seconds to wait between requests to avoid rate limiting
        """
        self.delay = delay_between_requests
        self.session = requests.Session()
        
        # Set user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def extract_indeed_url(self, apply_url: str) -> str:
        """
        Extract the Indeed job URL from apply URL or redirect chain
        
        Args:
            apply_url: The apply URL (could be Indeed or external)
            
        Returns:
            Indeed job URL if found, otherwise original URL
        """
        if not apply_url or not isinstance(apply_url, str):
            return apply_url
            
        # If it's already an Indeed job URL, return as is
        if 'indeed.com/job' in apply_url or 'indeed.com/viewjob' in apply_url:
            return apply_url
            
        # Try to extract jk (job key) parameter if it's an Indeed apply URL
        parsed_url = urlparse(apply_url)
        if 'indeed.com' in parsed_url.netloc:
            query_params = parse_qs(parsed_url.query)
            if 'jk' in query_params:
                job_key = query_params['jk'][0]
                return f"https://www.indeed.com/viewjob?jk={job_key}"
        
        return apply_url
    
    def check_indeed_link(self, job_url: str) -> Dict:
        """
        Check if an Indeed job link is still active
        
        Args:
            job_url: Indeed job URL to check
            
        Returns:
            Dict with status information
        """
        result = {
            'original_url': job_url,
            'is_active': False,
            'status_code': None,
            'error': None,
            'indeed_url': None,
            'job_key': None
        }
        
        try:
            # Extract Indeed URL if needed
            indeed_url = self.extract_indeed_url(job_url)
            result['indeed_url'] = indeed_url
            
            # Extract job key for reference
            if 'jk=' in indeed_url:
                jk_match = re.search(r'jk=([a-zA-Z0-9]+)', indeed_url)
                if jk_match:
                    result['job_key'] = jk_match.group(1)
            
            # Make request with timeout
            response = self.session.get(indeed_url, timeout=10, allow_redirects=True)
            result['status_code'] = response.status_code
            
            # Check if job is active based on response
            if response.status_code == 200:
                content = response.text.lower()
                
                # Common indicators that job is expired/removed
                expired_indicators = [
                    'this job has expired',
                    'job has been removed',
                    'no longer available',
                    'job posting has expired',
                    'position has been filled',
                    'sorry, this job is no longer available',
                    'job not found',
                    'page not found'
                ]
                
                # Check if any expired indicators are present
                is_expired = any(indicator in content for indicator in expired_indicators)
                
                # Also check for positive indicators that job is active
                active_indicators = [
                    'apply now',
                    'submit application',
                    'job description',
                    'apply on company site'
                ]
                
                has_active_content = any(indicator in content for indicator in active_indicators)
                
                # Job is active if no expired indicators AND has active content
                result['is_active'] = not is_expired and has_active_content
                
                if is_expired:
                    result['error'] = 'Job posting has expired or been removed'
                elif not has_active_content:
                    result['error'] = 'Job content not found - may be expired'
                    
            elif response.status_code == 404:
                result['error'] = 'Job not found (404)'
                result['is_active'] = False
            elif response.status_code == 410:
                result['error'] = 'Job has been removed (410)'
                result['is_active'] = False
            else:
                result['error'] = f'HTTP {response.status_code}'
                result['is_active'] = False
            
        except requests.exceptions.RequestException as e:
            result['error'] = f'Request failed: {str(e)}'
            result['is_active'] = False
        except Exception as e:
            result['error'] = f'Unexpected error: {str(e)}'
            result['is_active'] = False
        
        return result
    
    def check_multiple_links(self, job_urls: List[str], max_concurrent: int = 5) -> List[Dict]:
        """
        Check multiple Indeed job links with rate limiting
        
        Args:
            job_urls: List of job URLs to check
            max_concurrent: Maximum number of concurrent requests (not used currently)
            
        Returns:
            List of check results
        """
        results = []
        total_urls = len(job_urls)
        
        logger.info(f"🔗 Checking {total_urls} Indeed job links for expiration...")
        
        for i, url in enumerate(job_urls, 1):
            if i > 1:
                time.sleep(self.delay)  # Rate limiting
            
            result = self.check_indeed_link(url)
            results.append(result)
            
            # Log progress every 10 jobs
            if i % 10 == 0 or i == total_urls:
                active_count = sum(1 for r in results if r['is_active'])
                logger.info(f"   Progress: {i}/{total_urls} checked, {active_count} active jobs found")
        
        # Summary
        active_count = sum(1 for r in results if r['is_active'])
        expired_count = total_urls - active_count
        
        logger.info(f"✅ Link checking complete:")
        logger.info(f"   Active jobs: {active_count}")
        logger.info(f"   Expired jobs: {expired_count}")
        logger.info(f"   Success rate: {active_count/total_urls*100:.1f}%")
        
        return results
    
    def filter_active_jobs(self, jobs_df, url_column: str = 'apply_url') -> Tuple[object, List[Dict]]:
        """
        Filter DataFrame to only include jobs with active Indeed links
        
        Args:
            jobs_df: DataFrame with job data
            url_column: Column name containing job URLs
            
        Returns:
            Tuple of (filtered_df, check_results)
        """
        if jobs_df.empty or url_column not in jobs_df.columns:
            logger.warning(f"DataFrame is empty or missing {url_column} column")
            return jobs_df, []
        
        # Get unique URLs to avoid duplicate checking
        all_urls = jobs_df[url_column].dropna().unique().tolist()
        
        if not all_urls:
            logger.warning("No URLs found to check")
            return jobs_df, []
        
        # Separate Indeed URLs from other URLs
        indeed_urls = []
        other_urls = []
        
        for url in all_urls:
            if 'indeed.com' in url:
                indeed_urls.append(url)
            else:
                other_urls.append(url)
        
        logger.info(f"📊 URL breakdown: {len(indeed_urls)} Indeed URLs, {len(other_urls)} other URLs")
        logger.info(f"   Will check {len(indeed_urls)} Indeed URLs for expiration")
        if other_urls:
            logger.info(f"   Cannot check {len(other_urls)} non-Indeed URLs - assuming active")
        
        # Check only Indeed URLs
        check_results = []
        if indeed_urls:
            check_results = self.check_multiple_links(indeed_urls)
        
        # Create lookup dict for active URLs
        active_urls = set()
        
        # Add all active Indeed URLs
        for result in check_results:
            if result['is_active']:
                active_urls.add(result['original_url'])
                # Also add the Indeed URL if different
                if result['indeed_url'] and result['indeed_url'] != result['original_url']:
                    active_urls.add(result['indeed_url'])
        
        # Add all non-Indeed URLs (assume they're active since we can't check them)
        active_urls.update(other_urls)
        
        # Filter DataFrame to only include active jobs
        original_count = len(jobs_df)
        filtered_df = jobs_df[jobs_df[url_column].isin(active_urls)].copy()
        filtered_count = len(filtered_df)
        
        # Calculate Indeed-specific stats
        indeed_jobs_count = sum(1 for url in all_urls if 'indeed.com' in url and jobs_df[jobs_df[url_column] == url].index.tolist())
        indeed_active_count = sum(1 for result in check_results if result['is_active'])
        indeed_expired_count = len(indeed_urls) - indeed_active_count
        
        logger.info(f"📊 Job filtering results:")
        logger.info(f"   Original jobs: {original_count}")
        logger.info(f"   Indeed jobs: {len(indeed_urls)} URLs")
        logger.info(f"   Indeed active: {indeed_active_count}")
        logger.info(f"   Indeed expired: {indeed_expired_count}")
        logger.info(f"   Non-Indeed (assumed active): {len(other_urls)}")
        logger.info(f"   Total active jobs: {filtered_count}")
        logger.info(f"   Total removed: {original_count - filtered_count}")
        
        return filtered_df, check_results

    def __del__(self):
        """Clean up session when object is destroyed"""
        if hasattr(self, 'session'):
            self.session.close()