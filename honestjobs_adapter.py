"""
HonestJobs API Adapter for FreeWorld Job Scraper
Scrapes fair-chance employment jobs from HonestJobs.com

HonestJobs is specifically designed for justice-impacted individuals,
making it a perfect source for FreeWorld's mission.

API Endpoint: https://api.honestjobs.com/api/1.0/jobPost/SearchAnonymous
"""

import os
import httpx
import pandas as pd
from typing import List, Dict, Optional, Any
from datetime import datetime
import hashlib
import logging

# Configure logging
logger = logging.getLogger(__name__)


class HonestJobsAdapter:
    """
    Adapter for HonestJobs.com API
    Provides fair-chance job postings specifically for justice-impacted individuals
    """

    BASE_URL = "https://api.honestjobs.com/api/1.0"

    # Default coordinates for major FreeWorld markets
    MARKET_COORDINATES = {
        'Dallas': {'lat': 32.7767, 'lng': -96.7970},
        'Houston': {'lat': 29.7604, 'lng': -95.3698},
        'Phoenix': {'lat': 33.4484, 'lng': -112.0740},
        'Denver': {'lat': 39.7392, 'lng': -104.9903},
        'Las Vegas': {'lat': 36.1699, 'lng': -115.1398},
        'Stockton': {'lat': 37.9577, 'lng': -121.2908},
        'Bay Area': {'lat': 37.7749, 'lng': -122.4194},
        'Inland Empire': {'lat': 34.0635, 'lng': -117.6509},
        'Trenton': {'lat': 40.2206, 'lng': -74.7597},
        'Newark': {'lat': 40.7357, 'lng': -74.1724},
    }

    def __init__(self, timeout: int = 60):
        """
        Initialize HonestJobs adapter

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://app.honestjobs.com',
            'Referer': 'https://app.honestjobs.com/',
            'User-Agent': 'FreeWorld-JobScraper/1.0'
        }

    def search_jobs(
        self,
        location: str,
        keywords: str = '',
        radius: int = 50,
        latitude: float = None,
        longitude: float = None,
        page: int = 0,
        results_per_page: int = 50,
        honest_jobs_only: bool = False,
        sort_logic: str = 'featured'
    ) -> Dict[str, Any]:
        """
        Search for jobs using HonestJobs SearchAnonymous API

        Args:
            location: Location string (e.g., "Houston, TX")
            keywords: Job search keywords (e.g., "CDL driver")
            radius: Search radius in miles
            latitude: Latitude for search center (optional)
            longitude: Longitude for search center (optional)
            page: Page number (0-indexed)
            results_per_page: Number of results per page (max ~50)
            honest_jobs_only: Filter to only HonestJobs verified employers
            sort_logic: Sort order - 'featured' or 'passcheck'

        Returns:
            API response dictionary with 'result' list of jobs
        """
        payload = {
            'honestJobsOnly': honest_jobs_only,
            'startingPage': page,
            'resultsPerPage': results_per_page,
            'jobSeekerId': '',
            'keywords': keywords,
            'location': location,
            'radius': radius,
            'latitude': latitude or 0,
            'longitude': longitude or 0,
            'sortLogic': sort_logic
        }

        logger.info(f"🔍 HonestJobs API: {keywords or 'all jobs'} in {location} (radius: {radius}mi, page: {page})")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.BASE_URL}/jobPost/SearchAnonymous",
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()

                data = response.json()
                jobs = data.get('result', [])

                logger.info(f"✅ HonestJobs returned {len(jobs)} jobs")
                return data

        except httpx.TimeoutException:
            logger.error(f"❌ HonestJobs API timeout after {self.timeout}s")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HonestJobs API HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ HonestJobs API error: {e}")
            raise

    def search_all_pages(
        self,
        location: str,
        keywords: str = '',
        radius: int = 50,
        latitude: float = None,
        longitude: float = None,
        max_pages: int = 10,
        results_per_page: int = 50,
        honest_jobs_only: bool = False
    ) -> List[Dict]:
        """
        Search all pages and return combined job list

        Args:
            location: Location string (e.g., "Houston, TX")
            keywords: Job search keywords
            radius: Search radius in miles
            latitude: Latitude for search center
            longitude: Longitude for search center
            max_pages: Maximum pages to fetch
            results_per_page: Results per page
            honest_jobs_only: Filter to verified employers only

        Returns:
            Combined list of all jobs across pages
        """
        all_jobs = []
        page = 0

        while page < max_pages:
            result = self.search_jobs(
                location=location,
                keywords=keywords,
                radius=radius,
                latitude=latitude,
                longitude=longitude,
                page=page,
                results_per_page=results_per_page,
                honest_jobs_only=honest_jobs_only
            )

            jobs = result.get('result', [])
            if not jobs:
                # No more results
                break

            all_jobs.extend(jobs)
            page += 1

            # If we got fewer than requested, we're done
            if len(jobs) < results_per_page:
                break

        logger.info(f"📊 HonestJobs total: {len(all_jobs)} jobs from {page} pages")
        return all_jobs

    def search_by_market(
        self,
        market: str,
        keywords: str = '',
        radius: int = 50,
        max_pages: int = 10,
        **kwargs
    ) -> List[Dict]:
        """
        Search by FreeWorld market name using pre-configured coordinates

        Args:
            market: FreeWorld market name (e.g., "Houston", "Dallas")
            keywords: Job search keywords
            radius: Search radius in miles
            max_pages: Maximum pages to fetch
            **kwargs: Additional search parameters

        Returns:
            List of jobs for the market
        """
        coords = self.MARKET_COORDINATES.get(market)
        if not coords:
            logger.warning(f"Unknown market '{market}', using location string only")
            location = f"{market}, TX"  # Default to TX
            lat, lng = None, None
        else:
            # Build location string from market name
            state_map = {
                'Dallas': 'TX', 'Houston': 'TX', 'Phoenix': 'AZ',
                'Denver': 'CO', 'Las Vegas': 'NV', 'Stockton': 'CA',
                'Bay Area': 'CA', 'Inland Empire': 'CA',
                'Trenton': 'NJ', 'Newark': 'NJ'
            }
            state = state_map.get(market, 'TX')
            location = f"{market}, {state}"
            lat, lng = coords['lat'], coords['lng']

        jobs = self.search_all_pages(
            location=location,
            keywords=keywords,
            radius=radius,
            latitude=lat,
            longitude=lng,
            max_pages=max_pages,
            **kwargs
        )

        # Tag jobs with market
        for job in jobs:
            job['_market'] = market

        return jobs

    def search_multi_market(
        self,
        markets: List[str],
        keywords: str = '',
        radius: int = 50,
        max_pages_per_market: int = 5,
        **kwargs
    ) -> List[Dict]:
        """
        Search multiple FreeWorld markets

        Args:
            markets: List of market names
            keywords: Job search keywords
            radius: Search radius in miles
            max_pages_per_market: Max pages per market
            **kwargs: Additional search parameters

        Returns:
            Combined list of jobs from all markets
        """
        all_jobs = []

        for market in markets:
            logger.info(f"🏙️ Searching market: {market}")
            jobs = self.search_by_market(
                market=market,
                keywords=keywords,
                radius=radius,
                max_pages=max_pages_per_market,
                **kwargs
            )
            all_jobs.extend(jobs)
            logger.info(f"   {market}: {len(jobs)} jobs")

        logger.info(f"📊 Total: {len(all_jobs)} jobs from {len(markets)} markets")
        return all_jobs

    def scrape_full_site(
        self,
        max_pages: int = 50,
        results_per_page: int = 50,
        keywords: str = ''
    ) -> List[Dict]:
        """
        Scrape ALL jobs from HonestJobs.com nationwide

        This method fetches all jobs without location filtering,
        which is useful for building a complete fair-chance job database.

        Args:
            max_pages: Maximum pages to fetch (safety limit)
            results_per_page: Results per page
            keywords: Optional keyword filter

        Returns:
            List of all jobs on the platform
        """
        all_jobs = []
        page = 0

        logger.info(f"🌐 Scraping full HonestJobs site (keywords: '{keywords or 'none'}')...")

        while page < max_pages:
            payload = {
                'honestJobsOnly': False,
                'startingPage': page,
                'resultsPerPage': results_per_page,
                'jobSeekerId': '',
                'keywords': keywords,
                'location': '',  # No location filter
                'radius': 0,
                'latitude': 0,
                'longitude': 0,
                'sortLogic': 'featured'
            }

            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.BASE_URL}/jobPost/SearchAnonymous",
                        json=payload,
                        headers=self.headers
                    )
                    response.raise_for_status()

                    data = response.json()
                    jobs = data.get('result', [])

                    if not jobs:
                        logger.info(f"   Page {page}: Empty - end of results")
                        break

                    all_jobs.extend(jobs)
                    logger.info(f"   Page {page}: {len(jobs)} jobs (total: {len(all_jobs)})")
                    page += 1

                    # If we got fewer than requested, we're done
                    if len(jobs) < results_per_page:
                        break

            except Exception as e:
                logger.error(f"   Page {page}: Error - {e}")
                break

        logger.info(f"✅ Full site scrape complete: {len(all_jobs)} total jobs")
        return all_jobs

    def scrape_cdl_jobs(
        self,
        max_pages: int = 20,
        results_per_page: int = 50
    ) -> List[Dict]:
        """
        Scrape all CDL/trucking jobs from HonestJobs.com

        Convenience method that searches for common CDL-related keywords.

        Returns:
            List of CDL-related jobs
        """
        # CDL-related search terms
        search_terms = [
            'CDL driver',
            'truck driver',
            'delivery driver',
            'forklift',
            'warehouse',
            'logistics',
        ]

        return self._scrape_with_keywords(
            keywords=search_terms,
            max_pages=max_pages,
            results_per_page=results_per_page
        )

    def scrape_entire_site(
        self,
        max_pages_per_keyword: int = 10,
        results_per_page: int = 50
    ) -> List[Dict]:
        """
        Scrape ALL jobs from HonestJobs.com using comprehensive keyword coverage.

        Since there's no employer list API, this uses multiple keywords to
        discover all available jobs across all employers.

        Returns:
            List of all unique jobs on the platform
        """
        # Comprehensive keywords to discover all job types
        search_terms = [
            # Transportation/Driving
            'CDL', 'driver', 'truck', 'delivery', 'transportation',
            # Warehouse/Logistics
            'warehouse', 'forklift', 'logistics', 'shipping', 'receiving',
            # Manufacturing
            'manufacturing', 'production', 'assembly', 'operator', 'machine',
            # Maintenance/Technical
            'maintenance', 'mechanic', 'technician', 'electrical', 'HVAC',
            # General labor
            'labor', 'construction', 'landscaping', 'cleaning', 'sanitation',
            # Other common fair-chance jobs
            'food service', 'cook', 'dishwasher', 'customer service', 'retail',
            # Catch-all terms
            'associate', 'helper', 'entry level', 'no experience',
        ]

        return self._scrape_with_keywords(
            keywords=search_terms,
            max_pages=max_pages_per_keyword,
            results_per_page=results_per_page
        )

    def _scrape_with_keywords(
        self,
        keywords: List[str],
        max_pages: int = 10,
        results_per_page: int = 50
    ) -> List[Dict]:
        """
        Internal method to scrape jobs using multiple keywords with deduplication.

        Args:
            keywords: List of search terms
            max_pages: Max pages per keyword
            results_per_page: Results per page

        Returns:
            Deduplicated list of jobs
        """
        all_jobs = {}  # Use dict for dedup by job ID
        employers_found = set()

        logger.info(f"🔍 Scraping with {len(keywords)} keywords...")

        for term in keywords:
            jobs = self.scrape_full_site(
                max_pages=max_pages,
                results_per_page=results_per_page,
                keywords=term
            )

            new_jobs = 0
            for job in jobs:
                job_id = job.get('id')
                if job_id and job_id not in all_jobs:
                    all_jobs[job_id] = job
                    new_jobs += 1
                    employers_found.add(job.get('companyName', 'Unknown'))

            if new_jobs > 0:
                logger.info(f"   '{term}': +{new_jobs} new jobs")

        logger.info(f"📊 Total: {len(all_jobs)} unique jobs from {len(employers_found)} employers")
        return list(all_jobs.values())

    def get_employer_summary(self, jobs: List[Dict] = None) -> Dict[str, Dict]:
        """
        Get summary of all employers from job data.

        Args:
            jobs: Optional list of jobs. If None, scrapes full site first.

        Returns:
            Dict mapping employer ID to employer info with job counts
        """
        if jobs is None:
            jobs = self.scrape_entire_site()

        employers = {}
        for job in jobs:
            emp_id = job.get('employerId')
            emp_name = job.get('companyName')
            employer_data = job.get('employer', {})

            if emp_id not in employers:
                employers[emp_id] = {
                    'id': emp_id,
                    'name': emp_name,
                    'industry': employer_data.get('industryName', ''),
                    'is_verified_fair_chance': employer_data.get('isVerifiedFairChance', False),
                    'job_count': 0,
                    'verified_hires': 0,
                }

            employers[emp_id]['job_count'] += 1
            employers[emp_id]['verified_hires'] = max(
                employers[emp_id]['verified_hires'],
                job.get('organizationVerifiedHires', 0)
            )

        return employers

    # Known employer IDs discovered via keyword searches
    # These are verified real employer IDs from HonestJobs API
    KNOWN_EMPLOYERS = {
        'ARAMARK': '96198735-3734-4c19-9c99-93bd3d2ab590',
        'Acosta Group': '51b23ff3-9fdf-4fdf-a3aa-152c2d2c1aee',
        'Aerotek': 'd30115ac-c120-4608-9e92-49ca643ec914',
        'Allied Universal': 'b4d050b0-2d5e-44ed-bcc3-51b0a57cba4b',
        'Amazon': 'a126edc1-8f05-43f0-86cb-8317bc2c41db',
        'Bob Barker Company': 'a03d3e07-d8e9-4a6e-9cfd-92a7dcfd9caa',
        'BrightView': 'edb02d7f-4850-4670-8a61-22212db3341e',
        'BrightView Landscapes LLC': '5272a8a7-f501-42fd-9bce-61cada7290c9',
        'Burlington': 'a9599de6-1e28-40b4-9a7f-374468fac05e',
        'Cardinal Health': '1eea7c02-9612-49c2-8154-6062356f5e09',
        'Caterpillar': '76383d66-fc68-4270-9a3a-ae73232168ce',
        'Champion Home Builders': '5ee8f599-1eb4-4b5a-85d9-e7138112c09d',
        'Cintas': '9b63976d-4c05-4069-8ca9-2eaae0fa359c',
        'Conduent': '1bb4b595-33d7-4dfb-8695-abbed1049e91',
        'DHL Express': 'b085b613-e428-4007-84e0-da22dc0de14e',
        'Eaton Corporation': '45e88bec-0f29-4d25-8725-fc1596b6f95c',
        'Fortrex': '532ecdbf-2b66-4208-9c98-15137e32b4d1',
        'Hilton': 'b69bf583-4051-4cf8-a11c-05fec65674b0',
        'IDEX': '33c072fa-59e6-4112-a03d-36829d44d775',
        'JBS Carriers': '4aa3479d-13b1-4d09-a92b-8b17891a345c',
        'KeHE Distributors': '482122d3-3246-48ee-9aac-d53b9aa786cd',
        'Koch Industries': '5776a273-5a9a-49a5-b9fd-7644717e54ce',
        'LSI Staffing': '461d9967-a62a-40b3-be2f-5d220c17e5ba',
        'ManpowerGroup': '24552a7a-b03c-4266-8f52-1debf7a7c70d',
        'Nestle USA': 'ffca381c-704c-4be8-95d1-6b42772dfdd1',
        'Pilot Company': '442adcde-c5df-4171-8421-04d33e32c322',
        'Radial': '57d33a3b-52f0-47b8-b340-456cba086344',
        'Robert Half': 'aafa548a-635d-4479-a312-cd1906864ee4',
        'Schneider': 'b2dabba2-032d-4486-ac4f-028f3f8cdbb1',
        'Starbucks': 'faa5b2ed-1189-4880-bed1-0051b57e4e2e',
        'Sysco': '627bcb16-950f-434a-8d85-91414b667145',
        'U-Haul': '373acb73-54bf-49a0-82a9-d6eb751b4596',
        'Valet Living': '21ccbf64-72b3-429c-991a-4fea63d3af00',
        'WM': '85d053b7-f949-4e15-8bb9-8291f01f66cc',
        'Walmart': '88323fae-15da-4957-aa29-b5620be28515',
        'WestRock': '963a9c19-2d78-488d-bc2a-5db8b12b0786',
        'White Cap': 'c7bbf4da-7d87-4290-bb66-873b2f4fe368',
    }

    # FreeWorld market ZIP codes for geo-targeted scraping
    # These are the actual ZIP codes used by the scraper pipeline
    MARKET_ZIPS = {
        'Dallas': ['75001', '75006', '75019', '75024', '75038', '75040', '75050', '75060', '75062', '75067', '75080', '75081', '75082', '75093', '75104', '75115', '75116', '75134', '75137', '75141', '75150', '75154', '75159', '75166', '75172', '75180', '75181', '75182', '75189', '75201', '75203', '75204', '75205', '75206', '75207', '75208', '75209', '75210', '75211', '75212', '75214', '75215', '75216', '75217', '75218', '75219', '75220', '75223', '75224', '75225', '75226', '75227', '75228', '75229', '75230', '75231', '75232', '75233', '75234', '75235', '75236', '75237', '75238', '75240', '75241', '75243', '75244', '75246', '75247', '75248', '75249', '75251', '75252', '75253', '75254', '75270', '75287'],
        'Houston': ['77002', '77003', '77004', '77005', '77006', '77007', '77008', '77009', '77010', '77011', '77012', '77013', '77014', '77015', '77016', '77017', '77018', '77019', '77020', '77021', '77022', '77023', '77024', '77025', '77026', '77027', '77028', '77029', '77030', '77031', '77032', '77033', '77034', '77035', '77036', '77037', '77038', '77039', '77040', '77041', '77042', '77043', '77044', '77045', '77046', '77047', '77048', '77049', '77050', '77051', '77053', '77054', '77055', '77056', '77057', '77058', '77059', '77060', '77061', '77062', '77063', '77064', '77065', '77066', '77067', '77068', '77069', '77070', '77071', '77072', '77073', '77074', '77075', '77076', '77077', '77078', '77079', '77080', '77081', '77082', '77083', '77084', '77085', '77086', '77087', '77088', '77089', '77090', '77091', '77092', '77093', '77094', '77095', '77096', '77098', '77099'],
        'Phoenix': ['85001', '85003', '85004', '85006', '85007', '85008', '85009', '85012', '85013', '85014', '85015', '85016', '85017', '85018', '85019', '85020', '85021', '85022', '85023', '85024', '85027', '85028', '85029', '85031', '85032', '85033', '85034', '85035', '85037', '85040', '85041', '85042', '85043', '85044', '85045', '85048', '85050', '85051', '85053', '85054', '85083', '85085', '85086', '85087'],
        'Denver': ['80002', '80003', '80004', '80005', '80007', '80010', '80011', '80012', '80013', '80014', '80015', '80016', '80017', '80018', '80019', '80020', '80021', '80022', '80023', '80024', '80030', '80031', '80033', '80110', '80111', '80112', '80113', '80120', '80121', '80122', '80123', '80124', '80125', '80126', '80127', '80128', '80129', '80130', '80134', '80202', '80203', '80204', '80205', '80206', '80207', '80209', '80210', '80211', '80212', '80214', '80215', '80216', '80218', '80219', '80220', '80221', '80222', '80223', '80224', '80226', '80227', '80228', '80229', '80230', '80231', '80232', '80233', '80234', '80235', '80236', '80237', '80238', '80239', '80246', '80247', '80249', '80260', '80264', '80290', '80293', '80294'],
        'Las Vegas': ['89030', '89031', '89032', '89081', '89084', '89085', '89086', '89101', '89102', '89103', '89104', '89106', '89107', '89108', '89109', '89110', '89113', '89115', '89117', '89118', '89119', '89120', '89121', '89122', '89123', '89124', '89128', '89129', '89130', '89131', '89134', '89135', '89138', '89139', '89141', '89142', '89143', '89144', '89145', '89146', '89147', '89148', '89149', '89156', '89166', '89169', '89178', '89179', '89183'],
        'Stockton': ['95201', '95202', '95203', '95204', '95205', '95206', '95207', '95209', '95210', '95211', '95212', '95215', '95219', '95227', '95230', '95231', '95234', '95236', '95237', '95240', '95242', '95258', '95304', '95320', '95330', '95336', '95337', '95361', '95366', '95376', '95377', '95391'],
        'Bay Area': ['94102', '94103', '94104', '94105', '94107', '94108', '94109', '94110', '94111', '94112', '94114', '94115', '94116', '94117', '94118', '94121', '94122', '94123', '94124', '94127', '94129', '94130', '94131', '94132', '94133', '94134', '94158', '94501', '94502', '94536', '94538', '94539', '94540', '94541', '94542', '94544', '94545', '94546', '94550', '94551', '94552', '94555', '94560', '94566', '94568', '94577', '94578', '94579', '94580', '94586', '94587', '94588', '94601', '94602', '94603', '94605', '94606', '94607', '94608', '94609', '94610', '94611', '94612', '94613', '94618', '94619', '94621'],
        'Inland Empire': ['91701', '91708', '91709', '91710', '91730', '91737', '91739', '91752', '91758', '91761', '91762', '91763', '91764', '91765', '91766', '91767', '91768', '91784', '91785', '91786', '92313', '92316', '92324', '92335', '92336', '92337', '92346', '92354', '92359', '92376', '92377', '92392', '92399', '92401', '92404', '92405', '92407', '92408', '92410', '92411', '92503', '92504', '92505', '92506', '92507', '92508', '92509', '92518', '92521', '92553', '92557', '92570', '92571', '92582', '92583', '92584', '92585', '92586', '92587', '92591', '92592', '92595', '92596'],
        'Trenton': ['08601', '08602', '08608', '08609', '08610', '08611', '08618', '08619', '08620', '08628', '08629', '08638', '08648', '08690', '08691'],
        'Newark': ['07101', '07102', '07103', '07104', '07105', '07106', '07107', '07108', '07111', '07112', '07114'],
    }

    def search_by_employer_id(
        self,
        employer_id: str,
        max_pages: int = 10,
        results_per_page: int = 50
    ) -> List[Dict]:
        """
        Search jobs by employer ID.

        IMPORTANT: employerId searches return DIFFERENT jobs than keyword searches!
        Combining both methods can yield ~200 jobs per company vs 100 limit.

        Args:
            employer_id: The employer's UUID
            max_pages: Max pages to fetch (API caps at 100 jobs regardless)
            results_per_page: Results per page

        Returns:
            List of jobs for this employer
        """
        all_jobs = []
        page = 0

        while page < max_pages:
            payload = {
                'honestJobsOnly': False,
                'startingPage': page,
                'resultsPerPage': results_per_page,
                'jobSeekerId': '',
                'keywords': '',
                'location': '',
                'radius': 10000,  # Wide radius
                'latitude': 0,
                'longitude': 0,
                'sortLogic': 'actualdistance',
                'employerId': employer_id  # KEY: Filter by employer
            }

            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.BASE_URL}/jobPost/SearchAnonymous",
                        json=payload,
                        headers=self.headers
                    )
                    response.raise_for_status()

                    data = response.json()
                    jobs = data.get('result', [])

                    if not jobs:
                        break

                    all_jobs.extend(jobs)
                    page += 1

                    if len(jobs) < results_per_page:
                        break

            except Exception as e:
                logger.error(f"   employerId search error: {e}")
                break

        return all_jobs

    def search_combined_strategy(
        self,
        company_name: str,
        employer_id: str = None,
        max_pages: int = 10
    ) -> List[Dict]:
        """
        Combined keyword + employerId search strategy.

        KEY DISCOVERY: Keyword search and employerId search return DIFFERENT result sets
        with near-zero overlap! This effectively doubles our job capture per company.

        Example results:
        - Walmart keyword: 100 jobs
        - Walmart employerId: 100 DIFFERENT jobs
        - Combined: ~200 unique jobs (0 overlap)

        Args:
            company_name: Company name for keyword search
            employer_id: Optional employer ID (looked up from KNOWN_EMPLOYERS if not provided)
            max_pages: Max pages per search method

        Returns:
            Combined deduplicated list of jobs
        """
        all_jobs = {}  # Dict for dedup by job ID

        # Method 1: Keyword search
        logger.info(f"   🔍 Keyword search: '{company_name}'")
        keyword_jobs = self.scrape_full_site(
            max_pages=max_pages,
            keywords=company_name
        )
        for job in keyword_jobs:
            job_id = job.get('id')
            if job_id:
                all_jobs[job_id] = job
        keyword_count = len(keyword_jobs)

        # Method 2: EmployerId search (if available)
        emp_id = employer_id or self.KNOWN_EMPLOYERS.get(company_name)
        employer_count = 0

        if emp_id:
            logger.info(f"   🏢 EmployerId search: {emp_id[:8]}...")
            employer_jobs = self.search_by_employer_id(emp_id, max_pages=max_pages)
            for job in employer_jobs:
                job_id = job.get('id')
                if job_id:
                    all_jobs[job_id] = job
            employer_count = len(employer_jobs)

        unique_count = len(all_jobs)
        overlap = (keyword_count + employer_count) - unique_count

        logger.info(f"   📊 {company_name}: keyword={keyword_count}, employerId={employer_count}, combined={unique_count}, overlap={overlap}")

        return list(all_jobs.values())

    def discover_employer_ids(
        self,
        search_keywords: List[str] = None,
        max_pages_per_keyword: int = 5
    ) -> Dict[str, str]:
        """
        Discover employer IDs by running keyword searches and collecting unique employers.

        This builds up our KNOWN_EMPLOYERS dictionary for future combined scraping.

        Args:
            search_keywords: Keywords to search (defaults to comprehensive list)
            max_pages_per_keyword: Max pages per keyword search

        Returns:
            Dict mapping company name to employer ID
        """
        if search_keywords is None:
            search_keywords = [
                # Major employers
                'Walmart', 'Amazon', 'Target', 'Home Depot', 'Lowes',
                'Starbucks', 'McDonalds', 'Wendys', 'Taco Bell', 'Burger King',
                'FedEx', 'UPS', 'USPS', 'XPO', 'JB Hunt',
                'Sysco', 'US Foods', 'Penske', 'Ryder',
                'CVS', 'Walgreens', 'Kroger', 'Safeway', 'Publix',
                # Job types
                'CDL', 'driver', 'warehouse', 'forklift', 'delivery',
                'manufacturing', 'production', 'maintenance', 'technician',
                'food service', 'retail', 'customer service',
            ]

        employers_found = {}

        for keyword in search_keywords:
            jobs = self.scrape_full_site(
                max_pages=max_pages_per_keyword,
                keywords=keyword
            )

            for job in jobs:
                emp_id = job.get('employerId')
                emp_name = job.get('companyName')
                if emp_id and emp_name and emp_name not in employers_found:
                    employers_found[emp_name] = emp_id

        logger.info(f"📊 Discovered {len(employers_found)} unique employers")
        return employers_found

    def scrape_maximum_coverage(
        self,
        include_known_employers: bool = True,
        discover_new_employers: bool = True,
        max_pages_per_search: int = 10
    ) -> List[Dict]:
        """
        Maximum coverage scraping using combined keyword + employerId strategy.

        This is the most comprehensive scraping method, designed to capture
        as many jobs as possible by exploiting the API's quirk where keyword
        and employerId searches return different result sets.

        Args:
            include_known_employers: Search all KNOWN_EMPLOYERS by ID
            discover_new_employers: Run keyword searches to find new employers
            max_pages_per_search: Max pages per individual search

        Returns:
            Comprehensive deduplicated list of all jobs
        """
        all_jobs = {}  # Dict for dedup by job ID

        # Phase 1: Search all known employers by ID
        if include_known_employers:
            logger.info(f"🏢 Phase 1: Searching {len(self.KNOWN_EMPLOYERS)} known employers by ID...")
            for company_name, emp_id in self.KNOWN_EMPLOYERS.items():
                try:
                    jobs = self.search_by_employer_id(emp_id, max_pages=max_pages_per_search)
                    new_count = 0
                    for job in jobs:
                        job_id = job.get('id')
                        if job_id and job_id not in all_jobs:
                            all_jobs[job_id] = job
                            new_count += 1
                    if new_count > 0:
                        logger.info(f"   {company_name}: +{new_count} jobs")
                except Exception as e:
                    logger.warning(f"   {company_name}: Error - {e}")

        phase1_total = len(all_jobs)
        logger.info(f"   Phase 1 total: {phase1_total} jobs")

        # Phase 2: Keyword searches to capture additional jobs and discover new employers
        if discover_new_employers:
            logger.info("🔍 Phase 2: Comprehensive keyword searches...")

            discovery_keywords = [
                # Broad job type keywords
                'driver', 'CDL', 'truck', 'delivery', 'warehouse', 'forklift',
                'manufacturing', 'production', 'maintenance', 'technician',
                'food service', 'retail', 'customer service', 'logistics',
                # Company names not in KNOWN_EMPLOYERS
                'Pepsi', 'Coca Cola', 'Frito Lay', 'Nestle', 'General Mills',
                'Tyson', 'Cargill', 'ADM', 'John Deere', 'Caterpillar',
                'Tesla', 'Ford', 'GM', 'Toyota', 'Honda',
                'AT&T', 'Verizon', 'T-Mobile', 'Comcast', 'Charter',
            ]

            new_employers = {}

            for keyword in discovery_keywords:
                jobs = self.scrape_full_site(
                    max_pages=max_pages_per_search,
                    keywords=keyword
                )

                new_count = 0
                for job in jobs:
                    job_id = job.get('id')
                    if job_id and job_id not in all_jobs:
                        all_jobs[job_id] = job
                        new_count += 1

                    # Track new employers
                    emp_id = job.get('employerId')
                    emp_name = job.get('companyName')
                    if emp_id and emp_name and emp_name not in self.KNOWN_EMPLOYERS:
                        if emp_name not in new_employers:
                            new_employers[emp_name] = emp_id

                if new_count > 0:
                    logger.info(f"   '{keyword}': +{new_count} new jobs")

            phase2_new = len(all_jobs) - phase1_total
            logger.info(f"   Phase 2 added: {phase2_new} jobs")
            logger.info(f"   New employers discovered: {len(new_employers)}")

        logger.info(f"✅ Maximum coverage complete: {len(all_jobs)} total unique jobs")
        return list(all_jobs.values())

    def search_by_zip(
        self,
        zip_code: str,
        keywords: str = '',
        radius: int = 50,
        max_pages: int = 5
    ) -> List[Dict]:
        """
        Search jobs by ZIP code with radius.

        Args:
            zip_code: ZIP code to search around
            keywords: Optional keyword filter
            radius: Search radius in miles
            max_pages: Max pages to fetch

        Returns:
            List of jobs near this ZIP code
        """
        # Use ZIP code as location string - API will geocode it
        return self.search_all_pages(
            location=zip_code,
            keywords=keywords,
            radius=radius,
            max_pages=max_pages
        )

    def scrape_all_markets(
        self,
        markets: List[str] = None,
        keywords: List[str] = None,
        radius: int = 50,
        max_pages_per_search: int = 5,
        use_employer_ids: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        Comprehensive scrape of ALL FreeWorld markets using ZIP codes.

        This is the main method for full job board population.
        Uses combined keyword + employerId strategy for maximum coverage.

        Args:
            markets: List of markets to scrape (defaults to all MARKET_ZIPS)
            keywords: Job search keywords (defaults to comprehensive list for non-CDL)
            radius: Search radius per ZIP in miles
            max_pages_per_search: Max pages per individual search
            use_employer_ids: Also search by known employer IDs

        Returns:
            Dict mapping market name to list of jobs
        """
        if markets is None:
            markets = list(self.MARKET_ZIPS.keys())

        if keywords is None:
            # Comprehensive keywords for ALL job types (not just CDL)
            keywords = [
                # Transportation/Driving
                'CDL', 'driver', 'truck', 'delivery', 'transportation',
                # Warehouse/Logistics
                'warehouse', 'forklift', 'logistics', 'shipping', 'receiving',
                # Manufacturing
                'manufacturing', 'production', 'assembly', 'operator', 'machine',
                # Maintenance/Technical
                'maintenance', 'mechanic', 'technician', 'electrical', 'HVAC',
                # General labor
                'labor', 'construction', 'landscaping', 'cleaning', 'sanitation',
                # Service industry
                'food service', 'cook', 'dishwasher', 'restaurant', 'hotel',
                # Retail/Customer service
                'retail', 'customer service', 'cashier', 'sales',
                # Entry-level keywords
                'entry level', 'no experience', 'will train',
            ]

        results = {}

        for market in markets:
            logger.info(f"\n{'='*60}")
            logger.info(f"🏙️ Scraping market: {market}")
            logger.info(f"{'='*60}")

            market_jobs = {}  # Dict for dedup

            # Get ZIP codes for this market (use first 3 for coverage, not all)
            zips = self.MARKET_ZIPS.get(market, [])[:3]
            if not zips:
                # Fallback to market name as location
                zips = [market]

            # Phase 1: ZIP-based keyword searches
            logger.info(f"📍 Phase 1: ZIP-based searches ({len(zips)} ZIPs, {len(keywords)} keywords)")
            for zip_code in zips:
                for keyword in keywords:
                    try:
                        jobs = self.search_by_zip(
                            zip_code=zip_code,
                            keywords=keyword,
                            radius=radius,
                            max_pages=max_pages_per_search
                        )

                        new_count = 0
                        for job in jobs:
                            job_id = job.get('id')
                            if job_id and job_id not in market_jobs:
                                job['_market'] = market
                                job['_search_zip'] = zip_code
                                job['_search_keyword'] = keyword
                                market_jobs[job_id] = job
                                new_count += 1

                        if new_count > 0:
                            logger.info(f"   {zip_code} + '{keyword}': +{new_count} jobs")

                    except Exception as e:
                        logger.warning(f"   {zip_code} + '{keyword}': Error - {e}")

            phase1_count = len(market_jobs)
            logger.info(f"   Phase 1 total: {phase1_count} unique jobs")

            # Phase 2: Employer ID searches (nationwide, filter later)
            if use_employer_ids:
                logger.info(f"🏢 Phase 2: Employer ID searches ({len(self.KNOWN_EMPLOYERS)} employers)")
                for company_name, emp_id in self.KNOWN_EMPLOYERS.items():
                    try:
                        jobs = self.search_by_employer_id(emp_id, max_pages=3)

                        new_count = 0
                        for job in jobs:
                            job_id = job.get('id')
                            if job_id and job_id not in market_jobs:
                                # Check if job is in this market's area
                                job_city = (job.get('address') or {}).get('city', '').lower()
                                job_state = (job.get('address') or {}).get('state', '').lower()
                                market_lower = market.lower()

                                # Simple proximity check - could be improved with actual geocoding
                                is_in_market = (
                                    market_lower in job_city or
                                    job_city in market_lower or
                                    (market == 'Bay Area' and job_state == 'ca') or
                                    (market == 'Inland Empire' and job_state == 'ca')
                                )

                                if is_in_market:
                                    job['_market'] = market
                                    job['_search_employer'] = company_name
                                    market_jobs[job_id] = job
                                    new_count += 1

                        if new_count > 0:
                            logger.info(f"   {company_name}: +{new_count} jobs in {market}")

                    except Exception as e:
                        logger.warning(f"   {company_name}: Error - {e}")

                phase2_new = len(market_jobs) - phase1_count
                logger.info(f"   Phase 2 added: {phase2_new} jobs")

            results[market] = list(market_jobs.values())
            logger.info(f"✅ {market} complete: {len(market_jobs)} total unique jobs")

        # Summary
        total_jobs = sum(len(jobs) for jobs in results.values())
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 ALL MARKETS SUMMARY")
        logger.info(f"{'='*60}")
        for market, jobs in results.items():
            logger.info(f"   {market}: {len(jobs)} jobs")
        logger.info(f"   TOTAL: {total_jobs} jobs across {len(results)} markets")

        return results

    def scrape_all_markets_combined(
        self,
        markets: List[str] = None,
        keywords: List[str] = None,
        radius: int = 50,
        max_pages_per_search: int = 5
    ) -> List[Dict]:
        """
        Scrape all markets and return combined deduplicated list.

        Convenience wrapper around scrape_all_markets() that returns
        a single list instead of market-grouped dict.

        Returns:
            Combined list of all jobs across all markets
        """
        results = self.scrape_all_markets(
            markets=markets,
            keywords=keywords,
            radius=radius,
            max_pages_per_search=max_pages_per_search
        )

        # Combine and dedupe
        all_jobs = {}
        for market, jobs in results.items():
            for job in jobs:
                job_id = job.get('id')
                if job_id:
                    all_jobs[job_id] = job

        return list(all_jobs.values())

    def scrape_non_cdl_jobs(
        self,
        markets: List[str] = None,
        max_pages_per_search: int = 5
    ) -> List[Dict]:
        """
        Scrape NON-CDL fair-chance jobs specifically.

        This focuses on job categories that don't require a CDL, making it
        ideal for Free Agents who are still working toward their CDL or
        prefer non-driving careers.

        Job categories covered:
        - Warehouse (forklift, picker, packer, shipping/receiving)
        - Manufacturing (assembly, production, machine operator)
        - Food service (cook, prep, dishwasher, server)
        - Retail (cashier, stocker, sales associate)
        - Hospitality (housekeeper, front desk, maintenance)
        - Construction (laborer, helper, apprentice)
        - Customer service (call center, support)

        Returns:
            List of non-CDL fair-chance jobs
        """
        non_cdl_keywords = [
            # Warehouse (no CDL needed)
            'warehouse', 'forklift', 'picker', 'packer', 'shipping', 'receiving',
            'inventory', 'order puller', 'material handler',
            # Manufacturing
            'manufacturing', 'production', 'assembly', 'machine operator',
            'quality control', 'packaging', 'line worker',
            # Food service
            'cook', 'prep cook', 'dishwasher', 'food service', 'kitchen',
            'restaurant', 'cafeteria', 'catering',
            # Retail
            'retail', 'cashier', 'stocker', 'sales associate', 'merchandiser',
            # Hospitality
            'housekeeper', 'housekeeping', 'front desk', 'hotel',
            'janitorial', 'custodian', 'cleaning',
            # Construction/Labor
            'laborer', 'construction helper', 'landscaping', 'groundskeeper',
            # Maintenance
            'maintenance', 'building maintenance', 'facility',
            # Customer service
            'customer service', 'call center', 'support representative',
            # Entry level
            'entry level', 'no experience', 'will train', 'immediate hire',
        ]

        return self.scrape_all_markets_combined(
            markets=markets,
            keywords=non_cdl_keywords,
            max_pages_per_search=max_pages_per_search
        )

    def scrape_stepping_stone_jobs(
        self,
        markets: List[str] = None,
        max_pages_per_search: int = 5
    ) -> List[Dict]:
        """
        Scrape 'stepping stone' jobs - positions that can lead to CDL careers.

        These are jobs at trucking/logistics companies that often have
        internal CDL training programs or pathways to driver positions.

        Examples:
        - Dock worker → Yard jockey → CDL driver
        - Warehouse at Sysco/US Foods → delivery driver
        - Forklift operator at trucking company → CDL training

        Returns:
            List of stepping stone fair-chance jobs
        """
        stepping_stone_keywords = [
            # Dock/Yard positions
            'dock worker', 'yard jockey', 'yard driver', 'spotter',
            'dock to driver', 'hostler',
            # Warehouse at trucking companies
            'warehouse driver', 'local delivery', 'route helper',
            # Forklift at logistics companies
            'forklift warehouse', 'forklift logistics',
            # General stepping stones
            'loader unloader', 'freight handler', 'lumper',
            # Companies with known CDL programs
            'Sysco warehouse', 'US Foods warehouse', 'XPO dock',
            'FedEx handler', 'UPS handler',
        ]

        return self.scrape_all_markets_combined(
            markets=markets,
            keywords=stepping_stone_keywords,
            max_pages_per_search=max_pages_per_search
        )


def generate_job_id(company: str, location: str, title: str) -> str:
    """Generate unique job ID from key fields"""
    key = f"{company}|{location}|{title}".lower().strip()
    return hashlib.md5(key.encode()).hexdigest()


def transform_honestjobs_to_canonical(
    raw_data: List[Dict],
    run_id: str,
    search_location: str = '',
    market: str = ''
) -> pd.DataFrame:
    """
    Transform HonestJobs API response to canonical DataFrame format

    Args:
        raw_data: List of job dictionaries from HonestJobs API
        run_id: Unique pipeline run identifier
        search_location: Location used for the search
        market: Market name for meta.market field

    Returns:
        DataFrame in canonical schema format
    """
    from jobs_schema import ensure_schema

    if not raw_data:
        return ensure_schema(pd.DataFrame())

    records = []

    for job in raw_data:
        # Extract address info
        address = job.get('address') or {}
        city = address.get('city', '')
        state = address.get('state', '')
        postal_code = address.get('postalCode', '')
        latitude = address.get('latitude')
        longitude = address.get('longitude')

        # Build location string
        if city and state:
            location_raw = f"{city}, {state}"
        elif city:
            location_raw = city
        else:
            location_raw = search_location

        # Extract salary info
        pay_rate = job.get('payRate')
        max_pay_rate = job.get('maxPayRate')
        frequency = job.get('frequency', '')
        pay_display = job.get('payRateDisplayOption', '')

        # Build salary display string
        if pay_rate and max_pay_rate and pay_rate != max_pay_rate:
            salary_display = f"${pay_rate:,.0f} - ${max_pay_rate:,.0f} / {frequency}"
        elif pay_rate:
            salary_display = f"${pay_rate:,.0f} / {frequency}"
        elif pay_display:
            salary_display = pay_display
        else:
            salary_display = ""

        # Normalize salary unit
        salary_unit = None
        if frequency:
            freq_lower = frequency.lower()
            if 'hour' in freq_lower:
                salary_unit = 'hour'
            elif 'week' in freq_lower:
                salary_unit = 'week'
            elif 'month' in freq_lower:
                salary_unit = 'month'
            elif 'year' in freq_lower or 'annual' in freq_lower:
                salary_unit = 'year'

        # Extract company info
        company = job.get('companyName', '')
        employer = job.get('employer') or {}
        employer_name = employer.get('name', company)
        industry = employer.get('industryName', '')
        is_verified_fair_chance = employer.get('isVerifiedFairChance', False)

        title = job.get('title', '')

        # Generate unique job ID
        job_id = generate_job_id(company, location_raw, title)

        # Build source URL
        source_url = job.get('sourceUrl', '')
        honestjobs_id = job.get('id', '')

        # Determine fair chance status
        is_fair_chance = job.get('isFairChance', False) or is_verified_fair_chance
        verified_hires = job.get('organizationVerifiedHires', 0)
        combined_hires = job.get('organizationCombinedHireCount', 0)

        # Parse fairChanceInfo if available
        fair_chance_info = job.get('fairChanceInfo') or {}
        fair_chance_label = fair_chance_info.get('label', '') if fair_chance_info else ''
        is_fair_chance_verified_label = 'verified' in fair_chance_label.lower() if fair_chance_label else False

        # Build enhanced description with fair chance info
        # This ensures the AI classifier will detect fair chance status
        description = job.get('description', '')
        fair_chance_section = []
        if is_fair_chance:
            fair_chance_section.append('<h3>Fair Chance Employer</h3>')
            fair_chance_section.append('<p>This employer is committed to fair chance hiring and considers candidates with criminal records.</p>')
        if fair_chance_label:
            fair_chance_section.append(f'<p><strong>Status: {fair_chance_label}</strong></p>')
        if verified_hires > 0:
            fair_chance_section.append(f'<p>This employer has hired {verified_hires} justice-impacted individuals.</p>')
        if combined_hires > 0 and combined_hires != verified_hires:
            fair_chance_section.append(f'<p>Total fair chance hires: {combined_hires}</p>')

        if fair_chance_section:
            description = description + '\n\n' + '\n'.join(fair_chance_section)

        record = {
            # ID fields
            'id.job': job_id,
            'id.source': 'honestjobs',
            'id.source_row': len(records),

            # Source fields (raw from API) - only standard fields that survive ensure_schema
            'source.title': title,
            'source.company': company,
            'source.location_raw': location_raw,
            'source.description_raw': description,  # Enhanced with fair chance info
            'source.url': source_url,
            'source.salary_raw': salary_display,
            'source.posted_date': job.get('updateDate', ''),

            # HonestJobs-specific fields (persisted to Supabase)
            'source.honestjobs_id': honestjobs_id,
            'source.verified_hires': verified_hires,
            'source.is_fair_chance': is_fair_chance,
            'source.employer_id': job.get('employerId', ''),

            # Normalized location components
            'norm.city': city,
            'norm.state': state,
            'norm.zip_code': postal_code,
            'norm.location': location_raw,

            # Salary normalization
            'norm.salary_min': pay_rate,
            'norm.salary_max': max_pay_rate,
            'norm.salary_unit': salary_unit,

            # Meta fields
            'meta.market': market or job.get('_market', search_location),
            'meta.distance_miles': job.get('distance'),

            # System fields
            'sys.created_at': datetime.now().isoformat(),
            'sys.updated_at': datetime.now().isoformat(),
            'sys.run_id': run_id,
            'sys.is_fresh_job': True,
            'sys.version': '3.0',

            # Route fields
            'route.stage': 'ingested',
        }

        records.append(record)

    df = pd.DataFrame(records)

    # Ensure schema compliance
    df = ensure_schema(df)

    # Log stats - all HonestJobs jobs are fair chance by definition
    logger.info(f"✅ HonestJobs transform complete: {len(df)} jobs")
    logger.info(f"   Source: honestjobs (all jobs are fair-chance eligible)")

    return df


def search_honestjobs(
    location: str,
    run_id: str,
    keywords: str = '',
    radius: int = 50,
    max_pages: int = 10,
    market: str = '',
    honest_jobs_only: bool = False
) -> pd.DataFrame:
    """
    High-level function to search HonestJobs and return canonical DataFrame

    Args:
        location: Location string (e.g., "Houston, TX")
        run_id: Pipeline run ID
        keywords: Job search keywords
        radius: Search radius in miles
        max_pages: Maximum pages to fetch
        market: Market name for meta.market
        honest_jobs_only: Filter to verified employers only

    Returns:
        DataFrame in canonical schema format
    """
    adapter = HonestJobsAdapter()

    # Parse coordinates from location if it matches a known market
    lat, lng = None, None
    for market_name, coords in adapter.MARKET_COORDINATES.items():
        if market_name.lower() in location.lower():
            lat, lng = coords['lat'], coords['lng']
            break

    jobs = adapter.search_all_pages(
        location=location,
        keywords=keywords,
        radius=radius,
        latitude=lat,
        longitude=lng,
        max_pages=max_pages,
        honest_jobs_only=honest_jobs_only
    )

    return transform_honestjobs_to_canonical(
        raw_data=jobs,
        run_id=run_id,
        search_location=location,
        market=market
    )


# Pipeline integration class
class HonestJobsPipelineIntegration:
    """Integration helper for running HonestJobs through the FreeWorld pipeline"""

    def __init__(self, run_id: str = None):
        self.run_id = run_id or f"honestjobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.adapter = HonestJobsAdapter()

    def run_honestjobs_through_pipeline(
        self,
        markets: List[str],
        keywords: str = '',
        radius: int = 50,
        max_pages_per_market: int = 5,
        pipeline=None
    ) -> pd.DataFrame:
        """
        Scrape HonestJobs and run results through the FreeWorld pipeline

        Args:
            markets: List of FreeWorld market names
            keywords: Job search keywords
            radius: Search radius in miles
            max_pages_per_market: Max pages per market
            pipeline: Optional FreeWorldPipelineV3 instance

        Returns:
            Processed DataFrame
        """
        # Scrape jobs from all markets
        all_jobs = self.adapter.search_multi_market(
            markets=markets,
            keywords=keywords,
            radius=radius,
            max_pages_per_market=max_pages_per_market
        )

        if not all_jobs:
            logger.warning("No jobs found from HonestJobs")
            from jobs_schema import ensure_schema
            return ensure_schema(pd.DataFrame())

        # Transform to canonical format
        df = transform_honestjobs_to_canonical(
            raw_data=all_jobs,
            run_id=self.run_id,
            search_location=', '.join(markets),
            market=markets[0] if len(markets) == 1 else ''
        )

        # If pipeline provided, run through remaining stages
        if pipeline:
            logger.info("Running HonestJobs data through pipeline stages 2-8...")
            # Pipeline stages 2-8 would be run here
            # For now, return the ingested data
            pass

        return df


if __name__ == '__main__':
    # Test the adapter
    logging.basicConfig(level=logging.INFO)

    print("Testing HonestJobs Adapter...")
    print("=" * 50)

    adapter = HonestJobsAdapter()

    # Test 1: Single location search with CDL keyword
    print("\n1. Testing CDL keyword search (Houston)...")
    result = adapter.search_jobs(
        location="Houston, TX",
        keywords="CDL driver",
        radius=50
    )
    print(f"   Found {len(result.get('result', []))} CDL jobs")
    for job in result.get('result', [])[:3]:
        print(f"   - {job.get('title')} @ {job.get('companyName')}")

    # Test 2: Combined strategy demonstration (key breakthrough!)
    print("\n2. Testing COMBINED keyword + employerId strategy...")
    print("   (This bypasses the 100-job limit per search!)")

    # Test with Walmart - should show ~200 jobs vs 100
    walmart_jobs = adapter.search_combined_strategy('Walmart')
    print(f"   Walmart combined: {len(walmart_jobs)} unique jobs")

    # Test 3: Employer ID search directly
    print("\n3. Testing employerId search...")
    if 'Walmart' in adapter.KNOWN_EMPLOYERS:
        emp_jobs = adapter.search_by_employer_id(
            adapter.KNOWN_EMPLOYERS['Walmart'],
            max_pages=5
        )
        print(f"   Walmart by employerId: {len(emp_jobs)} jobs")

    # Test 4: Discover new employer IDs
    print("\n4. Testing employer discovery...")
    new_employers = adapter.discover_employer_ids(
        search_keywords=['CDL', 'driver', 'warehouse'],
        max_pages_per_keyword=2
    )
    print(f"   Discovered {len(new_employers)} employers")
    for name, emp_id in list(new_employers.items())[:5]:
        print(f"   - {name}: {emp_id[:8]}...")

    # Test 5: Transform to canonical format
    print("\n5. Testing canonical transform...")
    df = transform_honestjobs_to_canonical(
        raw_data=walmart_jobs[:50],  # Sample
        run_id='test_run',
        market='Nationwide'
    )
    print(f"   DataFrame shape: {df.shape}")
    print(f"   Columns: {len(df.columns)}")

    # Show sample data
    if not df.empty:
        print("\n6. Sample job:")
        job = df.iloc[0]
        print(f"   Title: {job.get('source.title', 'N/A')}")
        print(f"   Company: {job.get('source.company', 'N/A')}")
        print(f"   Location: {job.get('norm.location', 'N/A')}")
        print(f"   URL: {str(job.get('source.url', 'N/A'))[:60]}...")
        # Check if description has fair chance info
        desc = str(job.get('source.description_raw', ''))
        has_fc = 'Fair Chance Employer' in desc
        print(f"   Fair Chance in description: {has_fc}")

    # Test 6: Maximum coverage scrape (optional - takes longer)
    print("\n7. Testing maximum coverage scrape (sample)...")
    print("   (Using 3 known employers to demonstrate)")
    sample_employers = dict(list(adapter.KNOWN_EMPLOYERS.items())[:3])
    original_employers = adapter.KNOWN_EMPLOYERS
    adapter.KNOWN_EMPLOYERS = sample_employers

    max_jobs = adapter.scrape_maximum_coverage(
        include_known_employers=True,
        discover_new_employers=False,  # Skip discovery for speed
        max_pages_per_search=3
    )
    print(f"   Maximum coverage (3 employers): {len(max_jobs)} unique jobs")

    adapter.KNOWN_EMPLOYERS = original_employers

    print("\n" + "=" * 50)
    print("HonestJobs Adapter test complete!")
    print("\nKEY INSIGHT: Keyword + EmployerId searches return DIFFERENT jobs!")
    print("Combined strategy effectively DOUBLES job capture per company.")
