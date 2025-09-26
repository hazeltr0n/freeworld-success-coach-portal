import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from job_classifier import JobClassifier
from hybrid_memory_classifier import HybridMemoryClassifier
from job_filters import JobFilters
import hashlib
import re

load_dotenv()

class FreeWorldJobScraper:
    def __init__(self):
        self.api_key = os.getenv('OUTSCRAPER_API_KEY')
        if not self.api_key:
            raise ValueError("OUTSCRAPER_API_KEY environment variable not set")
        self.headers = {'X-API-KEY': self.api_key}
        self.classifier = JobClassifier()
        self.hybrid_classifier = HybridMemoryClassifier()  # New hybrid system
        self.filters = JobFilters()
    
    def search_indeed_jobs(self, indeed_url_or_urls, limit=50, location=None, disable_optimization=False):
        """Search Indeed using single URL or multiple URLs with cost optimization"""
        
        # Check for existing quality jobs to reduce scraping costs (unless disabled)
        existing_jobs = pd.DataFrame()
        actual_limit = limit
        
        if disable_optimization:
            print(f"🔄 Getting exactly {limit} fresh job listings")
        
        if location and not disable_optimization:
            print(f"💰 Checking for previously found jobs in {location}...")
            reduction_info = self.hybrid_classifier.get_count_reduction_info(location, limit, hours=72)
            
            if reduction_info.get('reduction_available', False):
                existing_count = reduction_info['existing_jobs']
                jobs_to_scrape = reduction_info['jobs_to_scrape']
                cost_savings = reduction_info['cost_savings']
                
                if existing_count > 0:
                    print(f"   ✅ Found {existing_count} existing quality jobs")
                    print(f"   💵 Reducing scrape from {limit} to {jobs_to_scrape} jobs")
                    print(f"   💰 Cost savings: ${cost_savings:.3f}")
                    
                    existing_jobs = reduction_info['quality_jobs']
                    actual_limit = jobs_to_scrape
                    
                    if actual_limit <= 0:
                        print(f"   🎯 No scraping needed! Using {existing_count} existing jobs")
                        return self._process_existing_airtable_jobs(existing_jobs)
        
        # Handle multiple URLs or single URL
        if isinstance(indeed_url_or_urls, list):
            # Multiple URLs - each URL gets FULL limit, combined in one Outscraper call
            query_urls = indeed_url_or_urls
            num_queries = len(indeed_url_or_urls)

            if num_queries > 1:
                print(f"🔍 Searching {num_queries} Indeed queries, {actual_limit} jobs EACH:")
                for i, url in enumerate(query_urls, 1):
                    # Extract search term from URL for display
                    if 'q=' in url:
                        term = url.split('q=')[1].split('&')[0].replace('+', ' ')
                        print(f"   {i}. {term}: {actual_limit} jobs")

                # Each query gets the specified limit automatically
                effective_limit = actual_limit
                print(f"   📊 API will return up to {actual_limit * num_queries} total jobs ({num_queries} × {actual_limit} each)")
            else:
                effective_limit = actual_limit
                print(f"🔍 Searching single Indeed query for {actual_limit} jobs...")
        else:
            # Single URL (backward compatibility)
            query_urls = indeed_url_or_urls
            effective_limit = actual_limit
            print(f"🔍 Searching Indeed for {actual_limit} jobs...")

        url = "https://api.outscraper.cloud/indeed-search"
        params = {
            'query': query_urls,  # Can be string or list - requests handles both
            'limit': effective_limit,
            'async': 'false'
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            try:
                data = response.json()
            except Exception as json_error:
                print(f"❌ JSON parsing failed: {json_error}")
                print(f"📋 Response headers: {dict(response.headers)}")
                print(f"📋 Response content type: {response.headers.get('content-type', 'Unknown')}")
                print(f"📋 Response encoding: {response.encoding}")
                
                # Try to get raw text to debug
                try:
                    raw_text = response.text[:500] + "..." if len(response.text) > 500 else response.text
                    print(f"📋 Raw response (first 500 chars): {raw_text}")
                except Exception as text_error:
                    print(f"❌ Could not decode response text: {text_error}")
                
                # Return existing jobs if available
                if not existing_jobs.empty:
                    existing_jobs_list = self._process_existing_airtable_jobs(existing_jobs)
                    print(f"📋 Returning {len(existing_jobs_list)} existing jobs (JSON parsing failed)")
                    return existing_jobs_list
                return []
            
            if data.get('data') and len(data['data']) > 0:
                # Handle multiple queries - flatten all results
                all_jobs = []
                for i, query_result in enumerate(data['data']):
                    if isinstance(query_result, list):
                        all_jobs.extend(query_result)
                        print(f"   Query {i+1}: {len(query_result)} jobs")

                jobs = all_jobs
                if isinstance(indeed_url_or_urls, list) and len(indeed_url_or_urls) > 1:
                    num_queries = len(indeed_url_or_urls)
                    expected_total = actual_limit * num_queries  # Each query gets the limit automatically
                    print(f"✅ Found {len(jobs)} total Indeed jobs from {num_queries} queries (requested {actual_limit} × {num_queries} = {expected_total})")
                    if len(jobs) < expected_total * 0.5:  # Allow for some variance in API results
                        print(f"⚠️  API returned fewer jobs than expected ({len(jobs)} < {int(expected_total * 0.5)})")
                        print("   This might be an API limit or search result limit")
                else:
                    print(f"✅ Found {len(jobs)} total Indeed jobs from {len(data['data'])} queries (requested {actual_limit})")
                    if len(jobs) < actual_limit:
                        print(f"⚠️  API returned fewer jobs than requested ({len(jobs)} < {actual_limit})")
                        print("   This might be an API limit or search result limit")
                
                scraped_jobs = self._process_indeed_jobs(jobs)
                
                # Only combine with existing jobs if optimization is NOT disabled
                if not existing_jobs.empty and not disable_optimization:
                    existing_jobs_list = self._process_existing_airtable_jobs(existing_jobs)
                    combined_jobs = existing_jobs_list + scraped_jobs
                    print(f"🔗 Combined {len(existing_jobs_list)} existing + {len(scraped_jobs)} scraped = {len(combined_jobs)} total jobs")
                    return combined_jobs
                else:
                    return scraped_jobs
            else:
                print("❌ No jobs found")
                if data.get('data'):
                    print(f"📊 Data structure: {type(data['data'])}, length: {len(data['data']) if hasattr(data['data'], '__len__') else 'N/A'}")
                
                # Return existing jobs even if scraping failed
                if not existing_jobs.empty:
                    existing_jobs_list = self._process_existing_airtable_jobs(existing_jobs)
                    print(f"📋 Returning {len(existing_jobs_list)} existing jobs (scraping failed)")
                    return existing_jobs_list
                return []
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
            # Return existing jobs even if scraping failed
            if not existing_jobs.empty:
                existing_jobs_list = self._process_existing_airtable_jobs(existing_jobs)
                print(f"📋 Returning {len(existing_jobs_list)} existing jobs (API error)")
                return existing_jobs_list
            return []
    
    def search_google_jobs(self, job_terms, location):
        """Search Google for job postings using targeted approach"""
        # Use Google Jobs search directly - this might be what creates the outscraper files
        search_query = f"{job_terms} {location}"
        
        # Use Google search with job-specific parameters that might match the existing file format
        url = "https://api.outscraper.cloud/google-search-v3"
        params = {
            'query': search_query,
            'region': 'US',
            'language': 'en',
            'pagesPerQuery': 2,  # Get more results
            'async': 'false'
        }
        
        print(f"🔍 Starting Google search for: '{search_query}'")
        
        try:
            # Direct synchronous request to Google search API
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except Exception as json_error:
                    print(f"❌ Google API JSON parsing failed: {json_error}")
                    print(f"📋 Response headers: {dict(response.headers)}")
                    print(f"📋 Response content type: {response.headers.get('content-type', 'Unknown')}")
                    return []
                
                if data.get('data') and len(data['data']) > 0:
                    job_results = data['data'][0]
                    
                    # Handle if data[0] is a list of jobs directly (careers format)
                    if isinstance(job_results, list):
                        jobs = job_results
                        print(f"✅ Found {len(jobs)} Google Career jobs")
                        return self._process_google_career_jobs(jobs)
                    
                    # Handle if it's search results format
                    elif isinstance(job_results, dict) and job_results.get('organic_results'):
                        job_links = job_results['organic_results']
                        print(f"✅ Found {len(job_links)} Google search results")
                        return self._process_google_job_results(job_links)
                    else:
                        print("❌ No job results found in response")
                        print(f"Response structure: {type(job_results)}")
                        if isinstance(job_results, dict):
                            print(f"Available keys: {list(job_results.keys())}")
                        return []
                else:
                    print("❌ No data found in response")
                    return []
                
            else:
                print(f"❌ Google search error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return []
                
        except requests.exceptions.Timeout:
            print("❌ Google search request timed out")
            return []
        except Exception as e:
            print(f"❌ Google search exception: {e}")
            return []
    
    def _process_indeed_jobs(self, raw_jobs):
        """Convert Indeed API response to standard format with comprehensive salary data"""
        processed_jobs = []
        
        for job in raw_jobs:
            # Extract comprehensive salary information
            salary_data = self._extract_comprehensive_salary_data(job.get('salarySnippet', {}))
            
            processed_job = {
                'job_title': job.get('title', ''),
                'company': job.get('company', ''),
                'location': job.get('formattedLocation', ''),
                'job_description': job.get('snippet', ''),
                'apply_url': job.get('viewJobLink', ''),
                'source': 'Indeed'
            }
            
            # Add all salary fields for wage analysis
            processed_job.update(salary_data)
            processed_jobs.append(processed_job)
        
        return processed_jobs
    
    def _extract_comprehensive_salary_data(self, salary_snippet):
        """Extract all salary-related fields from Indeed's salarySnippet for wage analysis"""
        salary_data = {
            # Basic salary text (for backwards compatibility)
            'salary': '',
            
            # Estimated salary fields (Indeed's algorithm)
            'salary_estimated_currency': '',
            'salary_estimated_unit': '',  # YEAR, HOUR, WEEK, etc.
            'salary_estimated_min': '',
            'salary_estimated_max': '',
            
            # Base salary fields (employer-provided)
            'salary_base_currency': '',
            'salary_base_unit': '',  # YEAR, HOUR, WEEK, etc.
            'salary_base_min': '',
            'salary_base_max': '',
            
            # Combined salary display text
            'salary_display_text': ''
        }
        
        if not salary_snippet:
            return salary_data
        
        # Extract estimated salary (Indeed's algorithm estimate)
        if 'estimated' in salary_snippet and salary_snippet['estimated']:
            estimated = salary_snippet['estimated']
            salary_data['salary_estimated_currency'] = estimated.get('currencyCode', '')
            
            if 'baseSalary' in estimated and estimated['baseSalary']:
                base_salary = estimated['baseSalary']
                salary_data['salary_estimated_unit'] = base_salary.get('unitOfWork', '')
                
                if 'range' in base_salary and base_salary['range']:
                    salary_range = base_salary['range']
                    salary_data['salary_estimated_min'] = str(salary_range.get('min', ''))
                    salary_data['salary_estimated_max'] = str(salary_range.get('max', ''))
        
        # Extract base salary (employer-provided)
        if 'baseSalary' in salary_snippet and salary_snippet['baseSalary']:
            base_salary = salary_snippet['baseSalary']
            salary_data['salary_base_unit'] = base_salary.get('unitOfWork', '')
            
            if 'range' in base_salary and base_salary['range']:
                salary_range = base_salary['range']
                salary_data['salary_base_min'] = str(salary_range.get('min', ''))
                salary_data['salary_base_max'] = str(salary_range.get('max', ''))
        
        # Set base currency from snippet level
        salary_data['salary_base_currency'] = salary_snippet.get('currencyCode', '')
        
        # Create display text for human readability
        salary_data['salary_display_text'] = self._format_salary_display_text(salary_data)
        
        # Set backwards-compatible salary field
        salary_data['salary'] = salary_data['salary_display_text']
        
        return salary_data
    
    def _format_salary_display_text(self, salary_data):
        """Create human-readable salary display text from salary data"""
        display_parts = []
        
        # Prioritize employer-provided salary over estimated
        if salary_data['salary_base_min'] and salary_data['salary_base_max']:
            unit = salary_data['salary_base_unit'].lower() if salary_data['salary_base_unit'] else 'year'
            currency = salary_data['salary_base_currency'] if salary_data['salary_base_currency'] else 'USD'
            
            min_val = float(salary_data['salary_base_min']) if salary_data['salary_base_min'] else 0
            max_val = float(salary_data['salary_base_max']) if salary_data['salary_base_max'] else 0
            
            if unit == 'hour':
                display_parts.append(f"${min_val:,.0f}-${max_val:,.0f}/hour")
            elif unit == 'week':
                display_parts.append(f"${min_val:,.0f}-${max_val:,.0f}/week")
            elif unit == 'year':
                display_parts.append(f"${min_val:,.0f}-${max_val:,.0f}/year")
            else:
                display_parts.append(f"${min_val:,.0f}-${max_val:,.0f}/{unit}")
        
        # Add estimated if different or if no base salary
        if salary_data['salary_estimated_min'] and salary_data['salary_estimated_max']:
            unit = salary_data['salary_estimated_unit'].lower() if salary_data['salary_estimated_unit'] else 'year'
            
            min_val = float(salary_data['salary_estimated_min']) if salary_data['salary_estimated_min'] else 0
            max_val = float(salary_data['salary_estimated_max']) if salary_data['salary_estimated_max'] else 0
            
            estimated_text = ""
            if unit == 'hour':
                estimated_text = f"${min_val:,.0f}-${max_val:,.0f}/hour"
            elif unit == 'week':
                estimated_text = f"${min_val:,.0f}-${max_val:,.0f}/week"  
            elif unit == 'year':
                estimated_text = f"${min_val:,.0f}-${max_val:,.0f}/year"
            else:
                estimated_text = f"${min_val:,.0f}-${max_val:,.0f}/{unit}"
            
            # Only add estimated if we don't have base salary or if it's different
            if not display_parts:
                display_parts.append(f"{estimated_text} (estimated)")
            elif estimated_text not in display_parts[0]:
                display_parts.append(f"{estimated_text} (estimated)")
        
        return " | ".join(display_parts) if display_parts else ""
    
    def _process_existing_airtable_jobs(self, airtable_df):
        """Convert Airtable DataFrame to standard job format"""
        processed_jobs = []
        
        for _, row in airtable_df.iterrows():
            processed_job = {
                'job_title': row.get('job_title', ''),
                'company': row.get('company', ''),
                'location': row.get('location', ''),
                'job_description': row.get('job_description', ''),
                'apply_url': row.get('apply_url', ''),
                'salary': '',  # Salary not stored in Airtable currently
                'source': 'Airtable (existing)',
                # Pre-classified data from Airtable
                'match': row.get('match_level', ''),
                'reason': row.get('match_reason', ''),
                'route_type': row.get('route_type', ''),
                'job_id': row.get('job_id', ''),
                'final_status': 'included_cost_optimization'
            }
            processed_jobs.append(processed_job)
        
        return processed_jobs
    
    def _process_google_career_jobs(self, career_jobs):
        """Convert Google Careers API response to standard format"""
        processed_jobs = []
        
        for job in career_jobs:
            # Extract location from the structured locations array
            location = self._extract_google_career_location(job)
            
            processed_job = {
                'job_title': job.get('title', ''),
                'company': job.get('company_name', ''),
                'location': location,
                'job_description': job.get('description', ''),
                'apply_url': job.get('apply_url', ''),
                'salary': self._extract_salary_from_description(job.get('description', '')),
                'source': 'Google Careers'
            }
            processed_jobs.append(processed_job)
        
        return processed_jobs
    
    def _extract_google_career_location(self, job):
        """Extract properly formatted location from Google Careers job"""
        locations = job.get('locations', [])
        
        if not locations:
            return 'Location Not Found'
        
        # Use first location (primary location)
        primary_location = locations[0]
        
        # For US locations, format as "City, ST"
        if primary_location.get('country_code') == 'US':
            city = primary_location.get('city', '')
            state = primary_location.get('country', '')  # This is actually state code for US
            if city and state:
                return f"{city}, {state}"
        
        # For non-US locations, use the display format
        display = primary_location.get('display', '')
        if display:
            return display
        
        # Fallback to building a location string
        city = primary_location.get('city', '')
        if city:
            return city
        
        return 'Location Not Found'
    
    def _extract_salary_from_description(self, description):
        """Try to extract salary information from job description"""
        if not description:
            return ''
        
        # Look for salary patterns in the description
        import re
        salary_patterns = [
            r'\$[\d,]+(?:-\$[\d,]+)?',  # $50,000-$70,000 or $50,000
            r'salary range.*?\$[\d,]+(?:-\$[\d,]+)?',  # salary range is $50,000-$70,000
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ''
    
    def _process_google_job_results(self, search_results):
        """Convert Google search results to standard job format"""
        processed_jobs = []
        
        for result in search_results:
            # Extract job info from Google search results
            processed_job = {
                'job_title': result.get('title', ''),
                'company': self._extract_company_from_google_result(result),
                'location': self._extract_location_from_google_result(result),
                'job_description': result.get('description', ''),
                'apply_url': result.get('link', ''),
                'salary': self._extract_salary_from_description(result.get('description', '')),
                'source': 'Google Search'
            }
            processed_jobs.append(processed_job)
        
        return processed_jobs
    
    def _extract_company_from_google_result(self, result):
        """Try to extract company name from Google search result"""
        title = result.get('title', '')
        
        # Simple heuristics to find company name
        # Look for "at Company" or "Company -" patterns
        
        # Pattern: "Job Title at Company Name"
        at_match = re.search(r' at (.+?) -', title)
        if at_match:
            return at_match.group(1).strip()
        
        # Pattern: "Company Name - Job Title"  
        dash_match = re.search(r'^(.+?) - ', title)
        if dash_match:
            return dash_match.group(1).strip()
        
        # Fallback: use domain name
        link = result.get('link', '')
        if 'indeed.com' in link:
            return 'Indeed Posting'
        elif 'linkedin.com' in link:
            return 'LinkedIn Posting'
        elif 'glassdoor.com' in link:
            return 'Glassdoor Posting'
        elif 'monster.com' in link:
            return 'Monster Posting'
        
        return 'Unknown Company'
    
    def _extract_location_from_google_result(self, result):
        """Try to extract location from Google search result"""
        title = result.get('title', '')
        description = result.get('description', '')
        link = result.get('link', '')
        
        # Enhanced location patterns for job postings
        location_patterns = [
            r'([A-Z][a-z]+,\s*[A-Z]{2})',  # City, ST
            r'([A-Z][a-z]+\s[A-Z][a-z]+,\s*[A-Z]{2})',  # City City, ST
            r'([A-Z][a-z]+,\s*[A-Z][a-z]+)',  # City, State
            r'in\s+([A-Z][a-z]+,?\s*[A-Z]{2})',  # "in Dallas, TX"
            r'(\b[A-Z][a-z]+,?\s*Texas\b)',  # "Dallas, Texas"
            r'(\b[A-Z][a-z]+,?\s*California\b)',  # Handle full state names
            r'(\b[A-Z][a-z]+,?\s*Florida\b)',
            r'(\b[A-Z][a-z]+,?\s*New York\b)',
        ]
        
        # Try title first, then description
        for text in [title, description]:
            for pattern in location_patterns:
                match = re.search(pattern, text)
                if match:
                    location = match.group(1).strip()
                    # Clean up common formatting issues
                    location = re.sub(r',\s*$', '', location)  # Remove trailing comma
                    return location
        
        # Fallback: try to extract from Indeed/LinkedIn URLs
        if 'indeed.com' in link:
            # Indeed URLs often have location in them: /jobs?q=driver&l=Dallas%2C+TX
            url_match = re.search(r'[&?]l=([^&]+)', link)
            if url_match:
                location = url_match.group(1).replace('%2C', ',').replace('+', ' ')
                return location
        
        return 'Location Not Found'
    
    def _generate_job_id(self, company, location, job_title):
        """Generate unique job ID"""
        base_string = f"{str(company).lower().strip()}|{str(location).lower().strip()}|{str(job_title).lower().strip()}"
        return hashlib.md5(base_string.encode()).hexdigest()
    
    def run_full_search(self, search_params, mode_info):
        """Execute raw job search - returns unprocessed Indeed jobs for Pipeline v3"""
        print(f"\n🚛 Starting Indeed Job Scraping...")
        print("=" * 50)
        
        # Search Indeed (if enabled)
        if not search_params.get('search_indeed', False):
            print("⏸️  Indeed search not enabled")
            return []

        # Handle both single URL (indeed_url) and multiple URLs (indeed_urls)
        indeed_queries = search_params.get('indeed_urls') or search_params.get('indeed_url')
        raw_jobs = self._fetch_raw_indeed_jobs(
            indeed_queries,
            mode_info['indeed_limit']
        )
        
        if not raw_jobs:
            print("❌ No jobs found from Indeed")
            return []

        print(f"✅ Retrieved {len(raw_jobs)} raw jobs from Indeed")
        return raw_jobs

    def _fetch_raw_indeed_jobs(self, indeed_url_or_urls, limit):
        """Fetch raw job data from Indeed API without any processing"""

        # Handle multiple URLs or single URL
        if isinstance(indeed_url_or_urls, list):
            # Multiple URLs - pass as list directly to Outscraper API
            query_urls = indeed_url_or_urls
            print(f"🔍 Fetching {limit} raw jobs from {len(indeed_url_or_urls)} Indeed queries...")
        else:
            # Single URL (backward compatibility)
            query_urls = indeed_url_or_urls
            print(f"🔍 Fetching {limit} raw jobs from Indeed API...")

        # Calculate effective limit: multiply by number of queries for multi-market searches
        # For multiple queries, each query gets FULL limit (Outscraper multiplies automatically)
        if isinstance(query_urls, list) and len(query_urls) > 1:
            num_queries = len(query_urls)

            print(f"🔍 Multiple search term queries: {num_queries} URLs × {limit} jobs each:")
            for i, url in enumerate(query_urls, 1):
                # Extract search term from URL for display
                if 'q=' in url:
                    term = url.split('q=')[1].split('&')[0].replace('+', ' ')
                    print(f"   {i}. {term}: {limit} jobs")

            # Each query gets the specified limit automatically
            effective_limit = limit
            print(f"   📊 API will return up to {limit * num_queries} total jobs ({num_queries} × {limit} each)")
        else:
            effective_limit = limit

        url = "https://api.outscraper.cloud/indeed-search"
        params = {
            'query': query_urls,  # Can be string or list - requests handles both
            'limit': effective_limit,
            'async': 'false'
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return []
            
        try:
            data = response.json()
        except Exception as json_error:
            print(f"❌ JSON parsing failed: {json_error}")
            return []
            
        if not (data.get('data') and len(data['data']) > 0):
            print("❌ No job data found in API response")
            return []

        # Handle multiple queries - flatten all results
        all_jobs = []
        for i, query_result in enumerate(data['data']):
            if isinstance(query_result, list):
                all_jobs.extend(query_result)
                print(f"   Raw Query {i+1}: {len(query_result)} jobs")

        jobs = all_jobs
        print(f"✅ API returned {len(jobs)} total raw jobs from {len(data['data'])} queries")
        
        # Return raw Indeed API data without any processing
        return jobs
    
    def search_google_jobs_api(self, search_terms, location, radius=50, limit=100):
        """Search Google Jobs API with radius-based city expansion
        
        When radius=0, searches exact location only (faster, more stable).
        When radius>0, expands to nearby cities (slower, may timeout).
        Now supports comma-separated search terms.
        """
        
        # Handle comma-separated search terms
        search_terms_list = [term.strip() for term in search_terms.split(',') if term.strip()]
        
        if radius == 0:
            # Exact location search - much faster and more stable
            # Format: "CDL Driver Dallas TX" (no comma, matches test script format)
            location_formatted = location.replace(',', '').replace('  ', ' ').strip()
            
            # Create queries for each search term
            queries = []
            for term in search_terms_list:
                queries.append(f"{term} {location_formatted}")
            
            print(f"📍 Using exact location search: '{location_formatted}' (radius=0, stable mode)")
            print(f"🔍 Search terms: {len(search_terms_list)} terms - {', '.join(search_terms_list)}")
        else:
            # Radius-based city expansion (may cause timeouts)
            print(f"⚠️ Using radius expansion mode ({radius}mi) - may be slower or timeout")
            try:
                import pandas as pd
                df = pd.read_csv('market_cities.csv')
            except Exception as e:
                print(f"⚠️ Failed to load market_cities.csv: {e}")
                # Fallback to single location query for each term
                queries = []
                for term in search_terms_list:
                    queries.append(f"{term} {location}")
            else:
                queries = self._build_google_queries(search_terms_list, location, radius, df)
        
        # Calculate pages needed: Google typically returns ~20 jobs per page
        # Use fewer pages for exact location to match working test script behavior
        jobs_per_page = 20
        if radius == 0:
            # Exact location: limit to 2 pages max (nginx gateway timeout prevents more)
            total_pages_needed = min(2, max(1, (limit + jobs_per_page - 1) // jobs_per_page))
        else:
            # Radius expansion: can use more pages
            total_pages_needed = max(1, min(10, (limit + jobs_per_page - 1) // jobs_per_page))
        
        pages_per_query = max(1, total_pages_needed // max(1, len(queries)))
        
        print(f"📊 Target: {limit} jobs → {total_pages_needed} total pages → {pages_per_query} pages per query")
        
        # Google Jobs API call
        url = "https://api.outscraper.cloud/google-search-jobs"
        params = {
            'query': queries,  # Single query or multiple cities
            'pagesPerQuery': pages_per_query,  # Pages based on job limit
            'language': 'en',
            'region': 'US',
            'async': 'false'
        }
        
        # Batch queries to avoid timeout - use smaller batch size for radius expansion
        max_queries_per_batch = 1 if radius == 0 else 10  # Single query for exact location, smaller batches for radius
        if len(queries) > max_queries_per_batch:
            print(f"🔄 Batching {len(queries)} queries into groups of {max_queries_per_batch}")
            query_batches = [queries[i:i + max_queries_per_batch] for i in range(0, len(queries), max_queries_per_batch)]
        else:
            query_batches = [queries]
        
        all_jobs = []
        
        for batch_idx, query_batch in enumerate(query_batches):
            print(f"🌐 Calling Google Jobs API batch {batch_idx + 1}/{len(query_batches)} with {len(query_batch)} queries")
            batch_params = params.copy()
            batch_params['query'] = query_batch
            
            try:
                # Use 5-minute timeout for exact location (testing 50 pages), longer for radius expansion
                timeout = 300 if radius == 0 else 90
                response = requests.get(url, headers=self.headers, params=batch_params, timeout=timeout)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        batch_jobs = []
                        
                        # Google returns nested structure: data[query_index][job_index]
                        for query_results in data.get('data', []):
                            if isinstance(query_results, list):
                                batch_jobs.extend(query_results)
                            elif isinstance(query_results, dict):
                                batch_jobs.append(query_results)
                        
                        all_jobs.extend(batch_jobs)
                        print(f"✅ Batch {batch_idx + 1}: Got {len(batch_jobs)} jobs")
                        
                    except Exception as json_error:
                        print(f"❌ Batch {batch_idx + 1} JSON parsing failed: {json_error}")
                        print(f"📋 Raw response (first 500 chars): {response.text[:500]}")
                        
                else:
                    print(f"❌ Batch {batch_idx + 1} API error: {response.status_code}")
                    print(f"📋 Error response: {response.text[:500]}")
                    
            except requests.exceptions.Timeout:
                print(f"❌ Batch {batch_idx + 1} request timed out")
            except Exception as e:
                print(f"❌ Batch {batch_idx + 1} request failed: {e}")
        
        print(f"✅ Total Google Jobs retrieved: {len(all_jobs)} jobs from {len(queries)} queries")
        
        # Return both jobs and metadata for cost tracking
        return {
            'jobs': all_jobs,
            'queries_executed': len(queries),
            'cost': len(queries) * 0.005  # $0.005 per query
        }
    
    def _build_google_queries(self, search_terms_list, location, radius, df):
        """Build queries based on radius from CSV with multiple search terms"""
        
        # Extract market name (could be "Houston, TX" or just "Houston")
        market_key = location.split(',')[0].strip()
        
        # Filter cities based on radius
        radius_column = f'within_{radius}'
        
        # Get cities for this market within the radius
        market_cities = df[
            (df['market'] == market_key) & 
            (df[radius_column] == True)
        ]
        
        if len(market_cities) == 0:
            print(f"⚠️ No cities found for market '{market_key}' with radius {radius}mi")
            # Fallback: create queries for each search term with the original location
            queries = []
            for term in search_terms_list:
                queries.append(f"{term} {location}")
            return queries
        
        # Build queries: each search term × each city
        queries = []
        for term in search_terms_list:
            for _, row in market_cities.iterrows():
                query = f"{term} {row['city']} {row['state']}"
                queries.append(query)
        
        print(f"📍 Market: {location}, Radius: {radius}mi")
        print(f"🔍 Search terms: {len(search_terms_list)} terms × {len(market_cities)} cities = {len(queries)} queries")
        print(f"   Cities: {', '.join([row['city'] for _, row in market_cities.head(3).iterrows()])}{'...' if len(market_cities) > 3 else ''}")
        
        return queries
    
    def _show_summary(self, df):
        """Show classification summary"""
        print(f"\n📊 Results Summary:")
        print(f"Total jobs processed: {len(df)}")
        
        match_counts = df['match'].value_counts()
        for match_type, count in match_counts.items():
            emoji = "✅" if match_type == "good" else "⚠️" if match_type == "so-so" else "❌"
            print(f"  {emoji} {match_type}: {count}")
        
        # Show good jobs
        good_jobs = df[df['match'] == 'good']
        if len(good_jobs) > 0:
            print(f"\n🎯 Good Jobs for FreeWorld Candidates:")
            for _, job in good_jobs.head(5).iterrows():
                print(f"  • {job['job_title']} at {job['company']}")
                print(f"    Location: {job['location']}")
                print(f"    Reason: {job['reason']}")
                print()