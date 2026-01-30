"""
Company Intelligence Hub for FreeWorld Job Scraper

Aggregates company data across multiple sources:
- HonestJobs: verified_hires, is_fair_chance, employer_id
- AI Classifier: fair_chance signals from job descriptions
- Airtable: FreeWorld placement data and hiring success
- Job Sources: JSearch, Outscraper, Google Jobs

Provides unified company profiles with comprehensive fair chance intelligence.
"""

import os
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import hashlib

# Fuzzy matching
try:
    from rapidfuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    logging.warning("rapidfuzz not installed - fuzzy matching disabled")

logger = logging.getLogger(__name__)


# =============================================================================
# COMPANY NAME NORMALIZATION
# =============================================================================

# Common company suffixes to strip for normalization
COMPANY_SUFFIXES = [
    r'\s+inc\.?$', r'\s+llc\.?$', r'\s+corp\.?$', r'\s+corporation$',
    r'\s+co\.?$', r'\s+company$', r'\s+ltd\.?$', r'\s+limited$',
    r'\s+plc\.?$', r'\s+lp\.?$', r'\s+llp\.?$', r'\s+pllc\.?$',
    r'\s+usa$', r'\s+us$', r'\s+america$', r'\s+north america$',
    r'\s+international$', r'\s+intl\.?$', r'\s+group$', r'\s+holdings$',
    r'\s+services$', r'\s+solutions$', r'\s+enterprises$',
    r',\s*inc\.?$', r',\s*llc\.?$', r',\s*corp\.?$',
]

# Known company name aliases (canonical -> variations)
# This maps variations to the canonical name
COMPANY_ALIASES = {
    # Retail
    'home depot': ['the home depot', 'home depot inc', 'home depot usa', 'homedepot'],
    'walmart': ['wal-mart', 'wal mart', 'walmart inc', 'walmart stores'],
    'target': ['target corp', 'target corporation', 'target stores'],
    'lowes': ["lowe's", 'lowes home improvement', "lowe's companies"],
    'costco': ['costco wholesale', 'costco wholesale corporation'],
    'sams club': ["sam's club", 'sams club inc'],

    # Food/Beverage
    'starbucks': ['starbucks coffee', 'starbucks corporation'],
    'sysco': ['sysco corporation', 'sysco foods'],
    'us foods': ['usfoods', 'us foods inc', 'us foods holding'],
    'pepsi': ['pepsico', 'pepsi-cola', 'pepsi co'],
    'coca cola': ['coca-cola', 'coke', 'the coca-cola company'],
    'nestle': ['nestle usa', 'nestlé', 'nestle purina'],

    # Logistics/Trucking
    'fedex': ['federal express', 'fedex corporation', 'fedex ground', 'fedex freight'],
    'ups': ['united parcel service', 'ups inc', 'ups freight'],
    'xpo': ['xpo logistics', 'xpo inc'],
    'jb hunt': ['j.b. hunt', 'jb hunt transport', 'j b hunt'],
    'schneider': ['schneider national', 'schneider trucking'],
    'werner': ['werner enterprises', 'werner trucking'],
    'swift': ['swift transportation', 'swift trucking'],
    'penske': ['penske logistics', 'penske truck leasing', 'penske transportation'],
    'ryder': ['ryder system', 'ryder truck', 'ryder logistics'],
    'dhl': ['dhl express', 'dhl supply chain', 'dhl logistics'],

    # Staffing
    'manpower': ['manpowergroup', 'manpower inc', 'manpower group'],
    'aerotek': ['aerotek inc', 'aerotek staffing'],
    'robert half': ['robert half international', 'roberthalf', 'robert half technology'],

    # Manufacturing
    'caterpillar': ['caterpillar inc', 'cat inc'],
    'eaton': ['eaton corporation', 'eaton corp'],
    'koch': ['koch industries', 'koch inc'],

    # Hospitality
    'aramark': ['aramark corporation', 'aramark services'],
    'hilton': ['hilton hotels', 'hilton worldwide', 'hilton hospitality'],

    # Waste Management
    'wm': ['waste management', 'waste management inc', 'wm inc'],
    'republic services': ['republic services inc', 'republic waste'],
}

# Build reverse lookup: variation -> canonical
_ALIAS_LOOKUP = {}
for canonical, aliases in COMPANY_ALIASES.items():
    _ALIAS_LOOKUP[canonical] = canonical
    for alias in aliases:
        _ALIAS_LOOKUP[alias.lower()] = canonical


def normalize_company_name(name: str) -> str:
    """
    Normalize a company name for matching.

    Steps:
    1. Lowercase
    2. Strip common suffixes (Inc, LLC, Corp, etc.)
    3. Remove punctuation
    4. Collapse whitespace
    5. Check alias mapping

    Args:
        name: Raw company name

    Returns:
        Normalized canonical name
    """
    if not name:
        return ''

    # Lowercase and strip
    normalized = name.lower().strip()

    # Remove common suffixes
    for suffix_pattern in COMPANY_SUFFIXES:
        normalized = re.sub(suffix_pattern, '', normalized, flags=re.IGNORECASE)

    # Remove punctuation except hyphens and apostrophes initially
    normalized = re.sub(r"[^\w\s\-']", '', normalized)

    # Collapse whitespace
    normalized = ' '.join(normalized.split())

    # Check alias mapping
    if normalized in _ALIAS_LOOKUP:
        normalized = _ALIAS_LOOKUP[normalized]

    # Final cleanup - remove remaining punctuation
    normalized = re.sub(r"[\-']", ' ', normalized)
    normalized = ' '.join(normalized.split())

    return normalized


def generate_company_id(company_name: str) -> str:
    """Generate consistent company ID from normalized name."""
    normalized = normalize_company_name(company_name)
    return hashlib.md5(normalized.encode()).hexdigest()


def fuzzy_match_company(
    company_name: str,
    known_companies: List[str],
    threshold: int = 85
) -> Optional[Tuple[str, int]]:
    """
    Find the best fuzzy match for a company name.

    Args:
        company_name: Company name to match
        known_companies: List of known company names (normalized)
        threshold: Minimum score for a match (0-100)

    Returns:
        Tuple of (matched_name, score) or None if no match found
    """
    if not FUZZY_AVAILABLE:
        return None

    if not company_name or not known_companies:
        return None

    normalized = normalize_company_name(company_name)

    # First check exact match
    if normalized in known_companies:
        return (normalized, 100)

    # Use rapidfuzz for fuzzy matching
    result = process.extractOne(
        normalized,
        known_companies,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=threshold
    )

    if result:
        matched_name, score, _ = result
        return (matched_name, int(score))

    return None


# =============================================================================
# COMPANY PROFILE DATA STRUCTURES
# =============================================================================

@dataclass
class FairChanceSignals:
    """Aggregated fair chance signals from all sources."""

    # HonestJobs signals
    honestjobs_verified_hires: int = 0
    honestjobs_is_verified: bool = False
    honestjobs_employer_id: str = ''

    # AI classifier signals (from job descriptions)
    ai_fair_chance_jobs: int = 0
    ai_background_check_jobs: int = 0
    ai_no_requirements_jobs: int = 0

    # FreeWorld internal signals
    freeworld_placements: int = 0
    freeworld_success_rate: float = 0.0
    freeworld_last_placement: str = ''

    # Computed signals
    @property
    def overall_fair_chance_score(self) -> float:
        """
        Compute an overall fair chance score (0-100).

        Weights:
        - HonestJobs verified: 40 points max
        - AI detected fair chance: 30 points max
        - FreeWorld placements: 30 points max
        """
        score = 0.0

        # HonestJobs component (0-40)
        if self.honestjobs_is_verified:
            score += 20
        if self.honestjobs_verified_hires > 0:
            # Cap at 20 points for 10+ hires
            hires_score = min(self.honestjobs_verified_hires * 2, 20)
            score += hires_score

        # AI component (0-30)
        total_ai_jobs = self.ai_fair_chance_jobs + self.ai_background_check_jobs + self.ai_no_requirements_jobs
        if total_ai_jobs > 0:
            fair_ratio = self.ai_fair_chance_jobs / total_ai_jobs
            score += fair_ratio * 30

        # FreeWorld component (0-30)
        if self.freeworld_placements > 0:
            score += min(self.freeworld_placements * 5, 15)
            score += self.freeworld_success_rate * 15

        return min(score, 100)

    @property
    def confidence_level(self) -> str:
        """Return confidence level based on data availability."""
        sources = 0
        if self.honestjobs_verified_hires > 0 or self.honestjobs_is_verified:
            sources += 1
        if self.ai_fair_chance_jobs > 0:
            sources += 1
        if self.freeworld_placements > 0:
            sources += 1

        if sources >= 3:
            return 'high'
        elif sources >= 2:
            return 'medium'
        elif sources >= 1:
            return 'low'
        return 'none'


@dataclass
class JobSourceStats:
    """Job statistics from a single source."""
    source: str
    total_jobs: int = 0
    good_jobs: int = 0
    so_so_jobs: int = 0
    bad_jobs: int = 0
    oldest_job: str = ''
    newest_job: str = ''


@dataclass
class CompanyProfile:
    """Unified company profile aggregating all data sources."""

    # Identity
    company_id: str = ''
    canonical_name: str = ''
    display_name: str = ''
    aliases: List[str] = field(default_factory=list)

    # External IDs
    honestjobs_employer_id: str = ''
    employer_uuid: str = ''  # FreeWorld internal

    # Fair chance intelligence
    fair_chance: FairChanceSignals = field(default_factory=FairChanceSignals)

    # Job statistics by source
    job_stats_by_source: Dict[str, JobSourceStats] = field(default_factory=dict)

    # Aggregate job stats
    total_jobs: int = 0
    active_jobs: int = 0  # Jobs in last 7 days
    fair_chance_jobs: int = 0

    # Geographic coverage
    markets: List[str] = field(default_factory=list)
    states: List[str] = field(default_factory=list)

    # Job characteristics
    route_types: Dict[str, int] = field(default_factory=dict)  # Local: 5, OTR: 3, etc.
    job_titles: List[str] = field(default_factory=list)  # Top 10

    # Salary data
    avg_salary_min: float = 0.0
    avg_salary_max: float = 0.0
    salary_range: str = ''

    # Metadata
    data_sources: List[str] = field(default_factory=list)
    first_seen: str = ''
    last_updated: str = ''

    # Flags
    is_blacklisted: bool = False
    blacklist_reason: str = ''

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/display."""
        return {
            'company_id': self.company_id,
            'canonical_name': self.canonical_name,
            'display_name': self.display_name,
            'aliases': self.aliases,
            'honestjobs_employer_id': self.honestjobs_employer_id,
            'employer_uuid': self.employer_uuid,

            # Fair chance (flattened)
            'fair_chance_score': self.fair_chance.overall_fair_chance_score,
            'fair_chance_confidence': self.fair_chance.confidence_level,
            'honestjobs_verified_hires': self.fair_chance.honestjobs_verified_hires,
            'honestjobs_is_verified': self.fair_chance.honestjobs_is_verified,
            'ai_fair_chance_jobs': self.fair_chance.ai_fair_chance_jobs,
            'freeworld_placements': self.fair_chance.freeworld_placements,
            'freeworld_success_rate': self.fair_chance.freeworld_success_rate,

            # Jobs
            'total_jobs': self.total_jobs,
            'active_jobs': self.active_jobs,
            'fair_chance_jobs': self.fair_chance_jobs,
            'job_stats_by_source': {k: vars(v) for k, v in self.job_stats_by_source.items()},

            # Geography
            'markets': self.markets,
            'states': self.states,

            # Characteristics
            'route_types': self.route_types,
            'job_titles': self.job_titles,
            'avg_salary_min': self.avg_salary_min,
            'avg_salary_max': self.avg_salary_max,
            'salary_range': self.salary_range,

            # Meta
            'data_sources': self.data_sources,
            'first_seen': self.first_seen,
            'last_updated': self.last_updated,
            'is_blacklisted': self.is_blacklisted,
            'blacklist_reason': self.blacklist_reason,
        }


# =============================================================================
# COMPANY INTELLIGENCE HUB
# =============================================================================

class CompanyIntelligenceHub:
    """
    Central hub for company intelligence aggregation.

    Aggregates data from:
    - Supabase jobs table (all sources: JSearch, Outscraper, HonestJobs, etc.)
    - HonestJobs API (verified_hires, fair_chance status)
    - Airtable (FreeWorld placement data)
    """

    def __init__(self, supabase_client=None):
        """
        Initialize the hub.

        Args:
            supabase_client: Optional Supabase client. If not provided,
                           will attempt to create one from environment.
        """
        self.supabase = supabase_client
        self._company_cache: Dict[str, CompanyProfile] = {}
        self._known_companies: List[str] = []

    def _get_supabase(self):
        """Get or create Supabase client."""
        if self.supabase:
            return self.supabase

        try:
            from supabase import create_client
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_ANON_KEY')
            if url and key:
                self.supabase = create_client(url, key)
                return self.supabase
            else:
                logger.error("SUPABASE_URL or SUPABASE_ANON_KEY not set")
                return None
        except Exception as e:
            logger.error(f"Failed to get Supabase client: {e}")
            return None

    def match_company(self, company_name: str) -> Tuple[str, str, int]:
        """
        Match a company name to a canonical name.

        Args:
            company_name: Raw company name

        Returns:
            Tuple of (canonical_name, company_id, match_score)
            match_score is 100 for exact match, <100 for fuzzy
        """
        if not company_name:
            return ('', '', 0)

        # Normalize first
        normalized = normalize_company_name(company_name)
        company_id = generate_company_id(company_name)

        # Check exact match in cache
        if normalized in self._company_cache:
            return (normalized, company_id, 100)

        # Try fuzzy match if we have known companies
        if self._known_companies and FUZZY_AVAILABLE:
            result = fuzzy_match_company(company_name, self._known_companies)
            if result:
                matched_name, score = result
                return (matched_name, generate_company_id(matched_name), score)

        # New company - return normalized name
        return (normalized, company_id, 100)

    def load_known_companies(self) -> int:
        """
        Load known companies from Supabase companies table.

        Returns:
            Number of companies loaded
        """
        supabase = self._get_supabase()
        if not supabase:
            return 0

        try:
            # Fetch all normalized company names
            result = supabase.table('companies').select(
                'normalized_company_name, company_name, employer_uuid'
            ).execute()

            self._known_companies = []
            for row in result.data:
                name = row.get('normalized_company_name') or row.get('company_name', '')
                if name:
                    normalized = normalize_company_name(name)
                    if normalized not in self._known_companies:
                        self._known_companies.append(normalized)

            logger.info(f"Loaded {len(self._known_companies)} known companies")
            return len(self._known_companies)

        except Exception as e:
            logger.error(f"Failed to load known companies: {e}")
            return 0

    def aggregate_company_from_jobs(
        self,
        company_name: str,
        include_honestjobs: bool = True,
        include_airtable: bool = True
    ) -> CompanyProfile:
        """
        Aggregate all data for a single company.

        Args:
            company_name: Company name to aggregate
            include_honestjobs: Include HonestJobs API data
            include_airtable: Include Airtable placement data

        Returns:
            CompanyProfile with aggregated data
        """
        canonical_name, company_id, _ = self.match_company(company_name)

        profile = CompanyProfile(
            company_id=company_id,
            canonical_name=canonical_name,
            display_name=company_name,
            last_updated=datetime.now().isoformat()
        )

        supabase = self._get_supabase()
        if not supabase:
            return profile

        # Aggregate from Supabase jobs
        try:
            # Get all jobs for this company (normalized name match)
            # Use ilike for case-insensitive matching
            result = supabase.table('jobs').select(
                'job_id, job_title, company, location, market, match_level, '
                'fair_chance, route_type, source, salary, created_at, updated_at, '
                'honestjobs_id, verified_hires, is_fair_chance, employer_id'
            ).ilike('company', f'%{canonical_name}%').execute()

            jobs = result.data or []

            # Process jobs
            sources_seen = set()
            markets_seen = set()
            states_seen = set()
            route_counts = {}
            title_counts = {}
            fair_chance_count = 0
            ai_fair_chance = 0
            ai_background_check = 0
            salary_mins = []
            salary_maxs = []
            oldest_date = None
            newest_date = None

            # Track HonestJobs data
            hj_verified_hires = 0
            hj_employer_id = ''
            hj_is_verified = False

            for job in jobs:
                # Source tracking
                source = job.get('source', 'unknown')
                sources_seen.add(source)

                # Initialize source stats if needed
                if source not in profile.job_stats_by_source:
                    profile.job_stats_by_source[source] = JobSourceStats(source=source)

                stats = profile.job_stats_by_source[source]
                stats.total_jobs += 1

                # Quality tracking
                match_level = job.get('match_level', '')
                if match_level == 'good':
                    stats.good_jobs += 1
                elif match_level == 'so-so':
                    stats.so_so_jobs += 1
                elif match_level == 'bad':
                    stats.bad_jobs += 1

                # Market/state tracking
                market = job.get('market', '')
                if market:
                    markets_seen.add(market)

                location = job.get('location', '')
                if location and ',' in location:
                    state = location.split(',')[-1].strip()
                    if len(state) == 2:
                        states_seen.add(state.upper())

                # Route type tracking
                route_type = job.get('route_type', '')
                if route_type:
                    route_counts[route_type] = route_counts.get(route_type, 0) + 1

                # Title tracking
                title = job.get('job_title', '')
                if title:
                    title_counts[title] = title_counts.get(title, 0) + 1

                # Fair chance tracking (AI classifier)
                fair_chance = job.get('fair_chance', '')
                if fair_chance:
                    if 'fair_chance' in fair_chance.lower():
                        ai_fair_chance += 1
                        fair_chance_count += 1
                    elif 'background_check' in fair_chance.lower():
                        ai_background_check += 1

                # HonestJobs data
                if job.get('verified_hires'):
                    hj_verified_hires = max(hj_verified_hires, job['verified_hires'])
                if job.get('employer_id'):
                    hj_employer_id = job['employer_id']
                if job.get('is_fair_chance'):
                    hj_is_verified = True
                    fair_chance_count += 1

                # Date tracking
                created = job.get('created_at', '')
                if created:
                    if oldest_date is None or created < oldest_date:
                        oldest_date = created
                    if newest_date is None or created > newest_date:
                        newest_date = created

                # Salary tracking (simplified)
                # Would need more sophisticated parsing in production

            # Populate profile
            profile.total_jobs = len(jobs)
            profile.fair_chance_jobs = fair_chance_count
            profile.data_sources = list(sources_seen)
            profile.markets = list(markets_seen)
            profile.states = list(states_seen)
            profile.route_types = route_counts

            # Top 10 job titles
            sorted_titles = sorted(title_counts.items(), key=lambda x: x[1], reverse=True)
            profile.job_titles = [t[0] for t in sorted_titles[:10]]

            # Fair chance signals
            profile.fair_chance.honestjobs_verified_hires = hj_verified_hires
            profile.fair_chance.honestjobs_is_verified = hj_is_verified
            profile.fair_chance.honestjobs_employer_id = hj_employer_id
            profile.fair_chance.ai_fair_chance_jobs = ai_fair_chance
            profile.fair_chance.ai_background_check_jobs = ai_background_check

            profile.honestjobs_employer_id = hj_employer_id

            if oldest_date:
                profile.first_seen = oldest_date

            # Count active jobs (last 7 days)
            if newest_date:
                try:
                    cutoff = (datetime.now() - timedelta(days=7)).isoformat()
                    profile.active_jobs = sum(
                        1 for j in jobs
                        if j.get('created_at', '') > cutoff
                    )
                except:
                    pass

        except Exception as e:
            logger.error(f"Error aggregating jobs for {company_name}: {e}")

        # Include Airtable placement data
        if include_airtable:
            profile = self._enrich_with_airtable(profile)

        # Cache the profile
        self._company_cache[canonical_name] = profile

        return profile

    def _enrich_with_airtable(self, profile: CompanyProfile) -> CompanyProfile:
        """
        Enrich profile with Airtable placement data.

        Uses the AirtableCompanyRollup to get actual FreeWorld hiring data
        from the Free Agent database's 'company' field.

        Args:
            profile: Existing company profile

        Returns:
            Enriched profile with FreeWorld placement data
        """
        try:
            from airtable_company_rollup import AirtableCompanyRollup

            rollup = AirtableCompanyRollup()
            hiring_data = rollup.get_company_hiring_data(profile.display_name)

            if hiring_data:
                # Update fair chance signals
                profile.fair_chance.freeworld_placements = hiring_data.placement_count
                profile.fair_chance.freeworld_success_rate = hiring_data.success_rate
                profile.fair_chance.freeworld_last_placement = hiring_data.last_placement

                # Add to data sources
                if 'airtable' not in profile.data_sources:
                    profile.data_sources.append('airtable')

                # Merge markets from Airtable
                for market in hiring_data.markets:
                    if market and market not in profile.markets:
                        profile.markets.append(market)

                logger.info(
                    f"Enriched {profile.display_name} with Airtable: "
                    f"{hiring_data.placement_count} placements, "
                    f"{hiring_data.success_rate:.0%} success rate"
                )
            else:
                logger.debug(f"No Airtable hiring data for {profile.display_name}")

        except ImportError:
            logger.debug("airtable_company_rollup not available")
        except Exception as e:
            logger.warning(f"Airtable enrichment failed for {profile.display_name}: {e}")

        return profile

    def build_full_company_index(
        self,
        min_jobs: int = 1,
        include_blacklisted: bool = False
    ) -> List[CompanyProfile]:
        """
        Build a complete company index from all job data.

        Args:
            min_jobs: Minimum jobs to include a company
            include_blacklisted: Include blacklisted companies

        Returns:
            List of CompanyProfile objects
        """
        supabase = self._get_supabase()
        if not supabase:
            return []

        profiles = []

        try:
            # Get distinct companies from jobs table
            result = supabase.table('jobs').select('company').execute()

            # Group by normalized name
            company_counts = {}
            for row in result.data:
                company = row.get('company', '')
                if not company:
                    continue

                normalized = normalize_company_name(company)
                if normalized not in company_counts:
                    company_counts[normalized] = {
                        'display_name': company,
                        'count': 0
                    }
                company_counts[normalized]['count'] += 1

            # Filter and aggregate
            for normalized, data in company_counts.items():
                if data['count'] < min_jobs:
                    continue

                profile = self.aggregate_company_from_jobs(
                    data['display_name'],
                    include_honestjobs=True,
                    include_airtable=True
                )

                if not include_blacklisted and profile.is_blacklisted:
                    continue

                profiles.append(profile)

            # Sort by total jobs
            profiles.sort(key=lambda p: p.total_jobs, reverse=True)

            logger.info(f"Built company index with {len(profiles)} companies")

        except Exception as e:
            logger.error(f"Error building company index: {e}")

        return profiles

    def get_top_fair_chance_employers(
        self,
        limit: int = 50,
        min_score: float = 30.0
    ) -> List[CompanyProfile]:
        """
        Get top fair chance employers ranked by score.

        Args:
            limit: Maximum companies to return
            min_score: Minimum fair chance score (0-100)

        Returns:
            List of CompanyProfiles sorted by fair_chance_score
        """
        profiles = self.build_full_company_index(min_jobs=1)

        # Filter by score and sort
        fair_chance_profiles = [
            p for p in profiles
            if p.fair_chance.overall_fair_chance_score >= min_score
        ]

        fair_chance_profiles.sort(
            key=lambda p: p.fair_chance.overall_fair_chance_score,
            reverse=True
        )

        return fair_chance_profiles[:limit]

    def update_companies_table(self, profiles: List[CompanyProfile] = None) -> int:
        """
        Update the Supabase companies table with aggregated data.

        Args:
            profiles: Optional list of profiles. If None, builds full index.

        Returns:
            Number of companies updated
        """
        if profiles is None:
            profiles = self.build_full_company_index()

        supabase = self._get_supabase()
        if not supabase:
            return 0

        updated = 0

        for profile in profiles:
            try:
                # Prepare data for upsert
                data = {
                    'normalized_company_name': profile.canonical_name,
                    'company_name': profile.display_name,
                    'total_jobs': profile.total_jobs,
                    'active_jobs': profile.active_jobs,
                    'fair_chance_jobs': profile.fair_chance_jobs,
                    'has_fair_chance': profile.fair_chance.overall_fair_chance_score > 30,
                    'markets': profile.markets,
                    'job_titles': profile.job_titles,
                    'route_breakdown': profile.route_types,
                    'updated_at': datetime.now().isoformat(),

                    # New fair chance intelligence fields
                    # These would need columns added to companies table
                    # 'honestjobs_verified_hires': profile.fair_chance.honestjobs_verified_hires,
                    # 'fair_chance_score': profile.fair_chance.overall_fair_chance_score,
                    # 'freeworld_placements': profile.fair_chance.freeworld_placements,
                }

                # Upsert by normalized name
                supabase.table('companies').upsert(
                    data,
                    on_conflict='normalized_company_name'
                ).execute()

                updated += 1

            except Exception as e:
                logger.error(f"Error updating company {profile.display_name}: {e}")

        logger.info(f"Updated {updated} companies in Supabase")
        return updated


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_company_intelligence_hub() -> CompanyIntelligenceHub:
    """Get a singleton instance of the hub."""
    return CompanyIntelligenceHub()


def lookup_company(company_name: str) -> CompanyProfile:
    """Quick lookup for a single company."""
    hub = get_company_intelligence_hub()
    return hub.aggregate_company_from_jobs(company_name)


def get_fair_chance_score(company_name: str) -> float:
    """Get fair chance score for a company."""
    profile = lookup_company(company_name)
    return profile.fair_chance.overall_fair_chance_score


# =============================================================================
# TEST
# =============================================================================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("Company Intelligence Hub Test")
    print("=" * 60)

    # Test normalization
    print("\n1. Testing company name normalization:")
    test_names = [
        "Home Depot",
        "The Home Depot",
        "Home Depot Inc.",
        "HOME DEPOT USA",
        "Wal-Mart",
        "Walmart Inc",
        "FedEx Ground",
        "Federal Express",
    ]

    for name in test_names:
        normalized = normalize_company_name(name)
        print(f"   '{name}' -> '{normalized}'")

    # Test fuzzy matching
    if FUZZY_AVAILABLE:
        print("\n2. Testing fuzzy matching:")
        known = ['home depot', 'walmart', 'fedex', 'target', 'amazon']
        test_matches = ['Homedepot Inc', 'Wal Mart Stores', 'Fed Ex Ground']

        for name in test_matches:
            result = fuzzy_match_company(name, known)
            if result:
                print(f"   '{name}' -> '{result[0]}' (score: {result[1]})")
            else:
                print(f"   '{name}' -> No match")

    # Test hub
    print("\n3. Testing CompanyIntelligenceHub:")
    hub = CompanyIntelligenceHub()

    # Load known companies
    count = hub.load_known_companies()
    print(f"   Loaded {count} known companies from Supabase")

    # Test company lookup
    print("\n4. Testing company profile aggregation:")
    test_companies = ['Home Depot', 'Walmart', 'Sysco']

    for company in test_companies:
        profile = hub.aggregate_company_from_jobs(company)
        print(f"\n   {profile.display_name}:")
        print(f"      Total jobs: {profile.total_jobs}")
        print(f"      Fair chance score: {profile.fair_chance.overall_fair_chance_score:.1f}")
        print(f"      HonestJobs verified hires: {profile.fair_chance.honestjobs_verified_hires}")
        print(f"      AI fair chance jobs: {profile.fair_chance.ai_fair_chance_jobs}")
        print(f"      Markets: {', '.join(profile.markets[:5])}")
        print(f"      Data sources: {', '.join(profile.data_sources)}")

    print("\n" + "=" * 60)
    print("Company Intelligence Hub test complete!")
