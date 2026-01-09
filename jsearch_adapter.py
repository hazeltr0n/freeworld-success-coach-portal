"""
JSearch API Adapter for FreeWorld Job Scraper
Provides Google Jobs data via OpenWeb Ninja's JSearch API as alternative to Outscraper

API Documentation: docs/JSEARCH_API.md
"""

import os
import requests
import pandas as pd
from typing import List, Dict, Optional, Any
from datetime import datetime
import hashlib
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Try to load secrets
def _load_secrets():
    """Load secrets from .streamlit/secrets.toml"""
    try:
        import toml
        secrets_path = ".streamlit/secrets.toml"
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            for key, value in secrets.items():
                if key not in os.environ:
                    os.environ[key] = str(value)
    except Exception as e:
        logger.warning(f"Could not load secrets: {e}")

_load_secrets()


class JSearchAdapter:
    """
    Adapter for OpenWeb Ninja's JSearch API
    Provides real-time Google Jobs data with field mapping to canonical schema
    """

    BASE_URL = "https://api.openwebninja.com/jsearch"

    def __init__(self, api_key: str = None):
        """
        Initialize JSearch adapter

        Args:
            api_key: JSearch API key (defaults to JSEARCH_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('JSEARCH_API_KEY')
        if not self.api_key:
            raise ValueError("JSEARCH_API_KEY not found in environment or passed as argument")

        self.headers = {"x-api-key": self.api_key}
        self.timeout = 120  # 2 minute timeout

    def search_jobs(
        self,
        query: str,
        num_pages: int = 10,
        date_posted: str = "week",
        radius_km: int = 80,
        employment_types: str = None,
        job_requirements: str = None,
        country: str = "us",
        page: int = 1
    ) -> List[Dict]:
        """
        Search for jobs using JSearch API

        Args:
            query: Search query (e.g., "CDL Driver Dallas, TX")
            num_pages: Number of pages to return (1-20, each page = 10 jobs max)
            date_posted: Filter by posting date (all, today, 3days, week, month)
            radius_km: Search radius in kilometers (50 miles ≈ 80 km)
            employment_types: Comma-separated: FULLTIME, CONTRACTOR, PARTTIME, INTERN
            job_requirements: Comma-separated: no_experience, no_degree, etc.
            country: Country code (default: us)
            page: Starting page number (1-100)

        Returns:
            List of job dictionaries from JSearch API
        """
        params = {
            "query": query,
            "page": page,
            "num_pages": min(num_pages, 20),  # API max is 20 pages
            "country": country,
            "date_posted": date_posted,
        }

        # Optional parameters
        if radius_km:
            params["radius"] = radius_km
        if employment_types:
            params["employment_types"] = employment_types
        if job_requirements:
            params["job_requirements"] = job_requirements

        logger.info(f"🔍 JSearch API: {query} ({num_pages} pages)")

        try:
            response = requests.get(
                f"{self.BASE_URL}/search",
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            jobs = data.get("data", [])

            logger.info(f"✅ JSearch returned {len(jobs)} jobs")
            return jobs

        except requests.exceptions.Timeout:
            logger.error(f"❌ JSearch API timeout after {self.timeout}s")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ JSearch API error: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ JSearch unexpected error: {e}")
            return []

    def search_jobs_multi_location(
        self,
        search_terms: str,
        locations: List[str],
        num_pages_per_location: int = 10,
        **kwargs
    ) -> List[Dict]:
        """
        Search multiple locations and combine results

        Args:
            search_terms: Job search terms (e.g., "CDL Driver")
            locations: List of locations (e.g., ["Dallas, TX", "Houston, TX"])
            num_pages_per_location: Pages per location search
            **kwargs: Additional search parameters

        Returns:
            Combined list of jobs from all locations
        """
        all_jobs = []

        for location in locations:
            query = f"{search_terms} {location}"
            jobs = self.search_jobs(
                query=query,
                num_pages=num_pages_per_location,
                **kwargs
            )

            # Tag jobs with search location for tracking
            for job in jobs:
                job['_search_location'] = location

            all_jobs.extend(jobs)
            logger.info(f"   {location}: {len(jobs)} jobs")

        logger.info(f"📊 Total: {len(all_jobs)} jobs from {len(locations)} locations")
        return all_jobs

    def get_job_details(self, job_ids: List[str], country: str = "us") -> List[Dict]:
        """
        Get detailed information for specific jobs

        Args:
            job_ids: List of job IDs (max 20 per request)
            country: Country code

        Returns:
            List of detailed job dictionaries
        """
        if not job_ids:
            return []

        # API supports max 20 job IDs per request
        job_ids_str = ",".join(job_ids[:20])

        params = {
            "job_id": job_ids_str,
            "country": country
        }

        try:
            response = requests.get(
                f"{self.BASE_URL}/job-details",
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            return data.get("data", [])

        except Exception as e:
            logger.error(f"❌ JSearch job-details error: {e}")
            return []

    def get_estimated_salary(
        self,
        job_title: str,
        location: str,
        location_type: str = "CITY"
    ) -> Optional[Dict]:
        """
        Get salary estimates for a job title in a location

        Args:
            job_title: Job title (e.g., "CDL Driver")
            location: Location (e.g., "Dallas, TX")
            location_type: ANY, CITY, STATE, COUNTRY

        Returns:
            Salary estimate dictionary or None
        """
        params = {
            "job_title": job_title,
            "location": location,
            "location_type": location_type
        }

        try:
            response = requests.get(
                f"{self.BASE_URL}/estimated-salary",
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("data", [])
            return results[0] if results else None

        except Exception as e:
            logger.error(f"❌ JSearch salary estimate error: {e}")
            return None


def generate_job_id(company: str, location: str, title: str) -> str:
    """Generate unique job ID from key fields"""
    key = f"{company}|{location}|{title}".lower().strip()
    return hashlib.md5(key.encode()).hexdigest()


def transform_jsearch_to_canonical(
    raw_data: List[Dict],
    run_id: str,
    search_location: str = '',
    market: str = ''
) -> pd.DataFrame:
    """
    Transform JSearch API response to canonical DataFrame format

    Args:
        raw_data: List of job dictionaries from JSearch API
        run_id: Unique pipeline run identifier
        search_location: Location used for the search
        market: Market name for meta.market field

    Returns:
        DataFrame in canonical schema format
    """
    from jobs_schema import ensure_schema

    if not raw_data:
        return ensure_schema(pd.DataFrame())

    # Build canonical records
    records = []

    for job in raw_data:
        # Extract salary info
        salary_min = job.get('job_min_salary')
        salary_max = job.get('job_max_salary')
        salary_period = job.get('job_salary_period', '')

        # Build salary display string
        if salary_min and salary_max:
            salary_display = f"${salary_min:,.0f} - ${salary_max:,.0f} / {salary_period}"
        elif salary_min:
            salary_display = f"${salary_min:,.0f} / {salary_period}"
        elif salary_max:
            salary_display = f"${salary_max:,.0f} / {salary_period}"
        else:
            salary_display = ""

        # Build location string
        city = job.get('job_city', '')
        state = job.get('job_state', '')
        location_raw = job.get('job_location', f"{city}, {state}" if city else '')

        # Extract company info
        company = job.get('employer_name', '')
        title = job.get('job_title', '')

        # Generate unique job ID
        job_id = generate_job_id(company, location_raw, title)

        record = {
            # ID fields
            'id.job': job_id,
            'id.source': 'jsearch',
            'id.source_row': len(records),

            # Source fields (raw from API)
            'source.title': title,
            'source.company': company,
            'source.location_raw': location_raw,
            'source.description_raw': job.get('job_description', ''),
            'source.url': job.get('job_apply_link', ''),
            'source.salary_raw': salary_display,
            'source.posted_date': job.get('job_posted_at', ''),

            # Preserve original JSearch fields for reference
            'source.jsearch_job_id': job.get('job_id', ''),
            'source.jsearch_publisher': job.get('job_publisher', ''),

            # Normalized location components
            'norm.city': city,
            'norm.state': state,
            'norm.location': location_raw,

            # Salary normalization
            'norm.salary_min': salary_min,
            'norm.salary_max': salary_max,
            'norm.salary_unit': salary_period.lower() if salary_period else None,
            'norm.salary_display': salary_display,

            # Meta fields
            'meta.market': market or job.get('_search_location', search_location),

            # System fields
            'sys.created_at': datetime.now().isoformat(),
            'sys.updated_at': datetime.now().isoformat(),
            'sys.run_id': run_id,
            'sys.is_fresh_job': True,
            'sys.version': '3.0',

            # Route fields
            'route.stage': 'ingested',
        }

        # Add benefits if available
        if job.get('job_benefits'):
            record['source.benefits'] = ', '.join(job.get('job_benefits', []))

        # Add highlights if available
        highlights = job.get('job_highlights', {})
        if highlights:
            if highlights.get('Qualifications'):
                record['source.qualifications'] = '\n'.join(highlights['Qualifications'])
            if highlights.get('Responsibilities'):
                record['source.responsibilities'] = '\n'.join(highlights['Responsibilities'])
            if highlights.get('Benefits'):
                record['source.benefits_highlights'] = '\n'.join(highlights['Benefits'])

        records.append(record)

    df = pd.DataFrame(records)

    # Ensure schema compliance
    df = ensure_schema(df)

    print(f"✅ JSearch transform complete: {len(df)} jobs")
    print(f"   Publishers: {df['source.jsearch_publisher'].value_counts().head(5).to_dict() if 'source.jsearch_publisher' in df.columns else 'N/A'}")

    return df


def search_jsearch_google_jobs(
    search_terms: str,
    location: str,
    run_id: str,
    num_pages: int = 10,
    radius_miles: int = 50,
    market: str = '',
    date_posted: str = 'week',
    job_requirements: str = None
) -> pd.DataFrame:
    """
    High-level function to search JSearch and return canonical DataFrame

    Args:
        search_terms: Job search terms (e.g., "CDL Driver")
        location: Location (e.g., "Dallas, TX")
        run_id: Pipeline run ID
        num_pages: Number of pages (1-20)
        radius_miles: Search radius in miles (converted to km)
        market: Market name for meta.market
        date_posted: Date filter (all, today, 3days, week, month)
        job_requirements: Optional requirements filter

    Returns:
        DataFrame in canonical schema format
    """
    adapter = JSearchAdapter()

    # Build query
    query = f"{search_terms} {location}"

    # Convert miles to km (roughly)
    radius_km = int(radius_miles * 1.6)

    # Search
    jobs = adapter.search_jobs(
        query=query,
        num_pages=num_pages,
        radius_km=radius_km,
        date_posted=date_posted,
        job_requirements=job_requirements
    )

    # Transform to canonical format
    df = transform_jsearch_to_canonical(
        raw_data=jobs,
        run_id=run_id,
        search_location=location,
        market=market or location.split(',')[0].strip()
    )

    return df


# Test function
if __name__ == "__main__":
    import uuid

    print("🧪 Testing JSearch Adapter")
    print("=" * 50)

    try:
        adapter = JSearchAdapter()
        print(f"✅ API key loaded")

        # Test search
        jobs = adapter.search_jobs(
            query="CDL Driver Dallas, TX",
            num_pages=5,
            date_posted="week",
            radius_km=80
        )

        print(f"\n📊 Search Results: {len(jobs)} jobs")

        if jobs:
            # Show sample
            print("\nSample Jobs:")
            for i, job in enumerate(jobs[:3]):
                print(f"\n{i+1}. {job.get('job_title', 'N/A')}")
                print(f"   Company: {job.get('employer_name', 'N/A')}")
                print(f"   Location: {job.get('job_city', '')}, {job.get('job_state', '')}")
                print(f"   Publisher: {job.get('job_publisher', 'N/A')}")

            # Test transform
            run_id = str(uuid.uuid4())[:8]
            df = transform_jsearch_to_canonical(jobs, run_id, "Dallas, TX", "Dallas")

            print(f"\n📊 Transformed DataFrame: {len(df)} rows, {len(df.columns)} columns")
            print(f"   Columns: {list(df.columns)[:10]}...")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
