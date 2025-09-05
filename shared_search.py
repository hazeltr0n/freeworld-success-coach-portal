"""
Shared search configuration and helpers for GUI and Terminal.
This centralizes market mappings, query location overrides, and Indeed URL builder
so both interfaces stay in sync.
"""

from typing import Dict

# Market configuration constants (ID -> Airtable Market Name)
MARKET_SEARCH_QUERIES: Dict[int, str] = {
    1: "Houston", 2: "Dallas", 3: "Bay Area", 4: "Stockton", 
    5: "Denver", 6: "Las Vegas", 7: "Newark", 8: "Phoenix",
    9: "Trenton", 10: "Inland Empire", 11: "San Antonio", 12: "Austin"
}

# Market to Location mapping for query building only (Outscraper/Indeed URLs).
# Do NOT use these values for meta.market or UI display.
MARKET_TO_LOCATION: Dict[str, str] = {
    "Houston": "Houston, TX",
    "Dallas": "Dallas, TX", 
    "Bay Area": "Berkeley, CA",
    "Stockton": "Stockton, CA",
    "Denver": "Denver, CO",
    "Las Vegas": "Las Vegas, NV", 
    "Newark": "Newark, NJ",
    "Phoenix": "Phoenix, AZ",
    "Trenton": "Trenton, NJ",
    "Inland Empire": "Ontario, CA",
    "San Antonio": "San Antonio, TX",
    "Austin": "Austin, TX"
}

# Market name mappings for command line (lowercased keys) - legacy support
MARKET_NAMES_TO_NUMBERS: Dict[str, int] = {
    "houston": 1, "dallas": 2, "bay area": 3, "berkeley": 3, "stockton": 4,
    "denver": 5, "las vegas": 6, "vegas": 6, "newark": 7,
    "phoenix": 8, "trenton": 9, "inland empire": 10, "ontario": 10,
    "san antonio": 11, "austin": 12
}

# For query building only: override certain markets to use a representative city
QUERY_LOCATION_OVERRIDES: Dict[str, str] = {
    "Bay Area, CA": "Berkeley, CA",
    "Inland Empire, CA": "Ontario, CA",
}

def build_indeed_query_url(search_term: str, location: str, radius: int = 50, no_experience: bool = True) -> str:
    """Build an Indeed search URL with all relevant parameters.

    - search_term: e.g., "CDL Driver"  
    - location: market name (e.g. "Dallas") or custom location - will be converted to location format
    - radius: miles
    - no_experience: include no-experience filter when True
    """
    # Convert market name to location format for Indeed API
    # E.g. "Dallas" → "Dallas, TX", "Bay Area" → "Berkeley, CA"
    loc = MARKET_TO_LOCATION.get(location, location)
    
    # Apply any additional overrides if needed
    loc = QUERY_LOCATION_OVERRIDES.get(loc, loc)
    
    base_url = "https://www.indeed.com/jobs"
    q = search_term.replace(' ', '+')
    l = loc.replace(' ', '+').replace(',', '%2C')
    url = f"{base_url}?q={q}&l={l}&radius={int(radius)}"
    if no_experience:
        url += "&sc=0kf%3Aattr%28D7S5D%29%3B"
    return url
