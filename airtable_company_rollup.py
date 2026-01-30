"""
Airtable Company Rollup for FreeWorld Job Scraper

Aggregates hiring data from Airtable Free Agent database.
Each Free Agent record has a 'company' field showing where they currently work.
This gives us real placement/hiring data to enrich company profiles.

Usage:
    from airtable_company_rollup import get_freeworld_hiring_data

    hiring_data = get_freeworld_hiring_data()
    # Returns: {'home depot': {'placements': 5, 'agents': [...], 'last_placement': '2024-01-15'}, ...}
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field

# Import company normalization
from company_intelligence import normalize_company_name, fuzzy_match_company, FUZZY_AVAILABLE

logger = logging.getLogger(__name__)


@dataclass
class CompanyHiringData:
    """Hiring data for a single company from Airtable."""

    company_name: str = ''
    normalized_name: str = ''
    placement_count: int = 0
    agent_uuids: List[str] = field(default_factory=list)
    agent_names: List[str] = field(default_factory=list)
    markets: List[str] = field(default_factory=list)
    placement_statuses: Dict[str, int] = field(default_factory=dict)
    first_placement: str = ''
    last_placement: str = ''

    # Computed metrics
    @property
    def success_rate(self) -> float:
        """Estimate success rate based on placement status."""
        if not self.placement_statuses:
            return 0.0

        successful = self.placement_statuses.get('Placed', 0) + \
                    self.placement_statuses.get('Hired', 0) + \
                    self.placement_statuses.get('Employed', 0)

        total = sum(self.placement_statuses.values())
        if total == 0:
            return 0.0

        return successful / total

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'company_name': self.company_name,
            'normalized_name': self.normalized_name,
            'placement_count': self.placement_count,
            'agent_count': len(self.agent_uuids),
            'markets': list(set(self.markets)),
            'placement_statuses': self.placement_statuses,
            'success_rate': self.success_rate,
            'first_placement': self.first_placement,
            'last_placement': self.last_placement,
        }


class AirtableCompanyRollup:
    """
    Aggregates company hiring data from Airtable Free Agent database.

    The Free Agent database has:
    - uuid: Agent's unique identifier
    - fullName: Agent's name
    - company: Where they currently work (THIS IS THE KEY FIELD)
    - placementStatus: Placement status (Placed, Hired, etc.)
    - city/state/CBSA: Location info
    """

    def __init__(self):
        """Initialize the rollup."""
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.candidates_table_id = os.getenv('AIRTABLE_CANDIDATES_TABLE_ID', 'tbl3fhAB14MkkewN1')

        self._cache: Dict[str, CompanyHiringData] = {}
        self._last_refresh: Optional[datetime] = None

    def _get_airtable_table(self):
        """Get Airtable table connection."""
        if not self.api_key or not self.base_id:
            logger.warning("Airtable credentials not configured")
            return None

        try:
            from pyairtable import Api
            api = Api(self.api_key)
            return api.table(self.base_id, self.candidates_table_id)
        except ImportError:
            logger.error("pyairtable not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to connect to Airtable: {e}")
            return None

    def fetch_all_agents_with_companies(self) -> List[Dict]:
        """
        Fetch all Free Agents who have a company listed.

        Airtable fields discovered:
        - Company: Company name where they work
        - placementStatus: e.g., "Placed: CDL Job"
        - employmentStatus: e.g., "Employed In Industry"
        - gotJobDate: When they got hired
        - placementSource: How they found the job
        - cbsa: Metro area for market mapping

        Returns:
            List of agent records with company info
        """
        table = self._get_airtable_table()
        if not table:
            return []

        agents_with_companies = []

        try:
            # Fetch all records with Company field populated
            # Using formula to filter: NOT({Company} = '')
            records = table.all(
                formula="NOT({Company} = '')",
                fields=[
                    'uuid', 'fullName', 'firstName', 'lastName',
                    'Company', 'Company Copy',
                    'placementStatus', 'employmentStatus',
                    'gotJobDate', 'placementSource',
                    'city', 'state', 'cbsa', 'Market'
                ]
            )

            for record in records:
                fields = record.get('fields', {})

                # Extract company
                company = fields.get('Company') or fields.get('Company Copy') or ''

                if not company:
                    continue

                # Extract name
                name = fields.get('fullName') or ''
                if not name:
                    first = fields.get('firstName', '')
                    last = fields.get('lastName', '')
                    name = f"{first} {last}".strip()

                # Extract other fields
                agent = {
                    'uuid': fields.get('uuid', ''),
                    'name': name,
                    'company': company,
                    'placement_status': fields.get('placementStatus', ''),
                    'employment_status': fields.get('employmentStatus', ''),
                    'got_job_date': fields.get('gotJobDate', ''),
                    'placement_source': fields.get('placementSource', ''),
                    'city': fields.get('city', ''),
                    'state': fields.get('state', ''),
                    'cbsa': fields.get('cbsa', ''),
                    'market': fields.get('Market', ''),
                }

                agents_with_companies.append(agent)

            logger.info(f"Fetched {len(agents_with_companies)} agents with company data")

        except Exception as e:
            logger.error(f"Error fetching agents from Airtable: {e}")

        return agents_with_companies

    def build_company_rollup(self, refresh: bool = False) -> Dict[str, CompanyHiringData]:
        """
        Build company hiring rollup from Airtable data.

        Args:
            refresh: Force refresh even if cached

        Returns:
            Dict mapping normalized company name to CompanyHiringData
        """
        # Check cache
        if not refresh and self._cache and self._last_refresh:
            cache_age = (datetime.now() - self._last_refresh).total_seconds()
            if cache_age < 3600:  # 1 hour cache
                return self._cache

        agents = self.fetch_all_agents_with_companies()
        if not agents:
            return {}

        # Group by normalized company name
        company_data: Dict[str, CompanyHiringData] = defaultdict(
            lambda: CompanyHiringData()
        )

        for agent in agents:
            company = agent['company']
            normalized = normalize_company_name(company)

            if not normalized:
                continue

            data = company_data[normalized]

            # Set names if first time
            if not data.company_name:
                data.company_name = company
                data.normalized_name = normalized

            # Aggregate data
            data.placement_count += 1

            if agent['uuid']:
                data.agent_uuids.append(agent['uuid'])
            if agent['name']:
                data.agent_names.append(agent['name'])

            # Market - prefer direct Market field, fallback to CBSA mapping
            market = agent.get('market', '')
            if not market and agent.get('cbsa'):
                market = self._cbsa_to_market(agent['cbsa'])
            if market:
                data.markets.append(market)

            # Placement status tracking
            status = agent['placement_status'] or agent['employment_status'] or 'Unknown'
            data.placement_statuses[status] = data.placement_statuses.get(status, 0) + 1

            # Date tracking - use gotJobDate as the authoritative date
            job_date = agent.get('got_job_date', '')
            if job_date:
                if not data.first_placement or job_date < data.first_placement:
                    data.first_placement = job_date
                if not data.last_placement or job_date > data.last_placement:
                    data.last_placement = job_date

        # Convert defaultdict to regular dict
        self._cache = dict(company_data)
        self._last_refresh = datetime.now()

        logger.info(f"Built rollup for {len(self._cache)} companies from Airtable")
        return self._cache

    def _cbsa_to_market(self, cbsa: str) -> str:
        """Convert CBSA to FreeWorld market name."""
        cbsa_mapping = {
            'Phoenix-Mesa-Chandler, AZ': 'Phoenix',
            'Stockton, CA': 'Stockton',
            'San Francisco-Oakland-Berkeley, CA': 'Bay Area',
            'Denver-Aurora-Lakewood, CO': 'Denver',
            'New York-Newark-Jersey City, NY-NJ-PA': 'Newark',
            'Houston-The Woodlands-Sugar Land, TX': 'Houston',
            'Dallas-Fort Worth-Arlington, TX': 'Dallas',
            'Las Vegas-Henderson-Paradise, NV': 'Las Vegas',
            'Riverside-San Bernardino-Ontario, CA': 'Inland Empire',
            'Trenton-Princeton, NJ': 'Trenton',
            'Los Angeles-Long Beach-Anaheim, CA': 'Inland Empire',
        }

        for cbsa_pattern, market in cbsa_mapping.items():
            if cbsa_pattern.lower() in cbsa.lower():
                return market

        return ''

    def get_company_hiring_data(self, company_name: str) -> Optional[CompanyHiringData]:
        """
        Get hiring data for a specific company.

        Args:
            company_name: Company name to look up

        Returns:
            CompanyHiringData or None if not found
        """
        rollup = self.build_company_rollup()

        normalized = normalize_company_name(company_name)

        # Exact match first
        if normalized in rollup:
            return rollup[normalized]

        # Try fuzzy match
        if FUZZY_AVAILABLE and rollup:
            result = fuzzy_match_company(company_name, list(rollup.keys()), threshold=85)
            if result:
                matched_name, score = result
                logger.debug(f"Fuzzy matched '{company_name}' to '{matched_name}' (score: {score})")
                return rollup.get(matched_name)

        return None

    def get_top_hiring_companies(self, limit: int = 50) -> List[CompanyHiringData]:
        """
        Get top companies by FreeWorld placements.

        Args:
            limit: Max companies to return

        Returns:
            List sorted by placement count
        """
        rollup = self.build_company_rollup()

        sorted_companies = sorted(
            rollup.values(),
            key=lambda x: x.placement_count,
            reverse=True
        )

        return sorted_companies[:limit]

    def export_to_dict(self) -> Dict[str, Dict]:
        """
        Export rollup as simple dict for JSON serialization.

        Returns:
            Dict mapping company name to hiring data dict
        """
        rollup = self.build_company_rollup()
        return {name: data.to_dict() for name, data in rollup.items()}


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_freeworld_hiring_data() -> Dict[str, CompanyHiringData]:
    """
    Get all FreeWorld hiring data by company.

    Returns:
        Dict mapping normalized company name to CompanyHiringData
    """
    rollup = AirtableCompanyRollup()
    return rollup.build_company_rollup()


def get_company_placements(company_name: str) -> int:
    """
    Get number of FreeWorld placements at a company.

    Args:
        company_name: Company name

    Returns:
        Number of placements (0 if not found)
    """
    rollup = AirtableCompanyRollup()
    data = rollup.get_company_hiring_data(company_name)
    return data.placement_count if data else 0


def get_hiring_summary() -> Dict[str, Any]:
    """
    Get summary of FreeWorld hiring data.

    Returns:
        Summary dict with totals and top companies
    """
    rollup = AirtableCompanyRollup()
    data = rollup.build_company_rollup()

    total_placements = sum(d.placement_count for d in data.values())
    unique_companies = len(data)

    top_companies = rollup.get_top_hiring_companies(10)

    return {
        'total_placements': total_placements,
        'unique_companies': unique_companies,
        'top_companies': [
            {
                'name': c.company_name,
                'placements': c.placement_count,
                'success_rate': c.success_rate
            }
            for c in top_companies
        ]
    }


# =============================================================================
# TEST
# =============================================================================

if __name__ == '__main__':
    import json

    logging.basicConfig(level=logging.INFO)

    print("Airtable Company Rollup Test")
    print("=" * 60)

    rollup = AirtableCompanyRollup()

    # Test connection
    print("\n1. Testing Airtable connection...")
    agents = rollup.fetch_all_agents_with_companies()
    print(f"   Found {len(agents)} agents with company data")

    if agents:
        # Show sample
        print("\n   Sample agents with companies:")
        for agent in agents[:5]:
            print(f"      - {agent['name'][:30]:30} @ {agent['company'][:25]}")

    # Build rollup
    print("\n2. Building company rollup...")
    company_data = rollup.build_company_rollup()
    print(f"   Found {len(company_data)} unique companies")

    # Top hiring companies
    print("\n3. Top hiring companies:")
    top = rollup.get_top_hiring_companies(10)
    for i, company in enumerate(top, 1):
        print(f"   {i}. {company.company_name}: {company.placement_count} placements")
        print(f"      Markets: {', '.join(set(company.markets)[:3])}")
        print(f"      Success rate: {company.success_rate:.0%}")

    # Test specific company lookup
    print("\n4. Testing company lookup:")
    test_companies = ['Walmart', 'Home Depot', 'Amazon', 'Sysco']
    for name in test_companies:
        data = rollup.get_company_hiring_data(name)
        if data:
            print(f"   {name}: {data.placement_count} placements, {data.success_rate:.0%} success")
        else:
            print(f"   {name}: No hiring data found")

    # Summary
    print("\n5. Hiring summary:")
    summary = get_hiring_summary()
    print(f"   Total placements: {summary['total_placements']}")
    print(f"   Unique companies: {summary['unique_companies']}")

    print("\n" + "=" * 60)
    print("Airtable Company Rollup test complete!")
