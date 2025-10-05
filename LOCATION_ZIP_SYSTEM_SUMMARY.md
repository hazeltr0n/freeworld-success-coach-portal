# Location & ZIP Code System - Complete Implementation Summary

## Overview
Built a comprehensive location-based job filtering system with multi-market support and ZIP code radius filtering for personalized agent-level job delivery.

---

## 1. Multi-Market Job Distribution System

### Database Schema
**Created `location_markets` table:**
```sql
-- Migration: 20251004221717_create_location_markets_library.sql
CREATE TABLE location_markets (
    id SERIAL PRIMARY KEY,
    location_string TEXT NOT NULL,      -- "city, st" or ZIP code
    location_type TEXT NOT NULL,        -- 'city', 'zip', or 'coordinate'
    markets TEXT[] NOT NULL,            -- Array of market names (supports multiple)
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    default_zips TEXT[],                -- Added in 20251004232439
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(location_string, location_type)
);
```

**Seeded with:**
- 1,367 city mappings from existing MarketMapper
- 2,153 unique location→market pairs from production jobs
- **168 locations with multiple markets** (e.g., Stockton → [Stockton, Bay Area, Sacramento])
- **Total: 3,041 location mappings**

### Enhanced MarketMapper (`market_mapper.py`)

**New Features:**
- `return_all=True` parameter to get ALL markets for a location
- Supports 3 input types:
  1. "City, ST" strings (via Supabase `location_markets` table + hardcoded fallback)
  2. ZIP codes (via uszipcode library - NOT WORKING due to dependency issues)
  3. Lat/lng coordinates (via geopy distance calculation)

**Query Priority:**
1. Supabase `location_markets` lookup (primary)
2. Hardcoded `market_lookup` dict (fallback)
3. Coordinate-based distance calculation (if geopy installed)

### Multi-Market Job Handler (`multi_market_handler.py`)

**Purpose:** Duplicate jobs for multiple markets with unique job IDs

**Key Functions:**
- `duplicate_jobs_for_markets(df, mapper)` - Creates separate records per market
- Appends market to job_id: `ABC123_stockton`, `ABC123_bay_area`
- Stores original job_id in `metadata.original_job_id`
- Prevents PRIMARY KEY conflicts

**Example:**
```python
# Input: 1 Stockton job
# Output: 3 records
# - ABC123_stockton (market: Stockton)
# - ABC123_bay_area (market: Bay Area)
# - ABC123_sacramento (market: Sacramento)
```

---

## 2. ZIP Code Extraction & Storage System

### Schema Changes

**Added to `jobs_schema.py`:**
```python
'norm.zip_code': str,  # Extracted ZIP code (5 or 5+4 digits)
```

**Database Migrations:**

**1. Jobs table** (20251004230241):
```sql
ALTER TABLE jobs ADD COLUMN zip_code TEXT;
CREATE INDEX idx_jobs_zip_code ON jobs(zip_code);
```

**2. Free agents table** (20251004230241):
```sql
ALTER TABLE free_agents ADD COLUMN zip_code TEXT;
ALTER TABLE free_agents ADD COLUMN zip_radius_miles INTEGER DEFAULT 25;
CREATE INDEX idx_free_agents_zip_code ON free_agents(zip_code);
```

**3. Location markets table** (20251004232439):
```sql
ALTER TABLE location_markets ADD COLUMN default_zips TEXT[];
CREATE INDEX idx_location_markets_default_zips ON location_markets USING GIN (default_zips);
```

### ZIP Extraction Logic (`canonical_transforms.py`)

**Updated `parse_location()` function:**
- Now returns 4 values: `(city, state, full_location, zip_code)`
- Regex extracts ZIP: `\b(\d{5}(?:-\d{4})?)\b`
- Handles ZIP+4 format (e.g., "85001-1234")

**Fallback System:**
```python
# Step 1: Try to extract ZIP from location string
zip_code = parse_location(location)[3]

# Step 2: If empty, use ZIP API lookup
if not zip_code:
    url = f"https://api.zippopotam.us/us/{state}/{city}"
    response = requests.get(url)
    zip_code = response.json()['places'][0]['post code']
```

**Applied in normalization stage (lines 606-637):**
- Extracts ZIPs from location strings (works for Indeed jobs)
- API fallback for Google Jobs (no ZIPs in data)

### Upload Integration (`job_memory_db.py`)

**Added ZIP mapping (line 234):**
```python
'zip_code': safe_str(job.get('norm.zip_code', job.get('zip_code', ''))),
```

Now `norm.zip_code` from DataFrame → `zip_code` column in Supabase

### Backfill Scripts

**1. `backfill_all_zips.py`** (NOT USED - too slow)
- Tried to backfill via API for each job
- Timeout issues with 9,223 jobs

**2. `populate_location_market_zips.py`** (RUNNING)
- Populates `location_markets.default_zips` via API
- Only 3,041 unique cities (much faster than per-job)
- **Current status: 576/3,041 completed (18.9%)**

---

## 3. ZIP Radius Filtering System

### Agent Preferences Schema
```sql
-- Free agents now have:
zip_code TEXT                    -- Agent's preferred ZIP
zip_radius_miles INTEGER DEFAULT 25  -- Search radius
```

### ZipDistanceCalculator (`zip_distance_calculator.py`)

**Features:**
- Uses free zippopotam.us API for ZIP geocoding
- Calculates distance via `geopy.distance.geodesic`
- `@lru_cache` decorator caches ZIP coordinates
- `filter_jobs_by_radius()` returns jobs within X miles

**Usage:**
```python
calc = ZipDistanceCalculator()

# Get jobs within 25 miles of agent's ZIP
filtered = calc.filter_jobs_by_radius(
    jobs=all_jobs,
    agent_zip="77064",
    radius_miles=25
)
# Returns: Jobs sorted by distance with 'distance_miles' field
```

### Portal Integration (NOT YET IMPLEMENTED)

**Planned approach:**
1. Agent sets `zip_code` and `zip_radius_miles` in preferences
2. Pre-compute nearby ZIPs once (cache in `free_agents.nearby_zips` array)
3. Portal queries: `WHERE zip_code IN (nearby_zips_array)`
4. Fast indexed lookup, no real-time distance calculations

---

## 4. DriverPulse Integration

### Adapter Updates (`driver_pulse_adapter.py`)

**Added imports:**
```python
from multi_market_handler import duplicate_jobs_for_markets
from market_mapper import MarketMapper
```

**Enhanced `_convert_to_outscraper_format()` (lines 168-171):**
```python
# Store lat/lng as top-level fields for market mapping
'latitude': job.get('lat', ''),
'longitude': job.get('lng', ''),
'zip_code': job.get('zip', ''),
```

**Multi-market processing (lines 126-129):**
```python
# Apply multi-market mapping using lat/lng from DriverPulse
df = duplicate_jobs_for_markets(df, self.market_mapper)
```

**Result:** DriverPulse jobs with lat/lng automatically:
1. Get mapped to ALL markets within 50-mile radius
2. Create separate records per market with unique job IDs
3. Each record has proper ZIP code

---

## 5. Data Quality & Coverage

### Source ZIP Coverage
- **Indeed (via Outscraper):** ✅ Has ZIPs in `formattedLocation` (e.g., "Dallas, TX 75342")
- **Google Jobs (via Outscraper):** ❌ NO ZIPs, only "City, ST"
- **DriverPulse:** ✅ Has lat/lng + ZIP for every job

### Current Database Status
- **Total jobs:** 9,223
- **With ZIP codes:** 1,646 (17.8%)
- **Without ZIP codes:** 7,577 (82.2%)

**Note:** Backfill in progress via `populate_location_market_zips.py`

---

## 6. New Google Scraping Strategy (PLANNED)

### Current Problem
- Uses weird radius→city count logic
- Inconsistent coverage per market

### New Approach
Use central ZIP + radius to build comprehensive city lists:

**Market Config:**
```python
MARKET_CONFIGS = [
    {"market": "Dallas", "central_zip": "75060", "radius": 75},
    {"market": "Houston", "central_zip": "77007", "radius": 75},
    # ... etc
]
```

**Build City Lists:**
1. Get all cities from `location_markets` with `default_zips`
2. Calculate distance from central ZIP
3. Include all cities within radius
4. Scrape each city individually

**Script:** `build_market_city_lists.py` (created but needs `default_zips` population to complete)

---

## 7. Files Created/Modified

### New Files
- `multi_market_handler.py` - Multi-market job duplication logic
- `zip_distance_calculator.py` - ZIP-based distance calculations
- `seed_location_markets.py` - Populated location_markets table
- `default_market_zips.py` - Hardcoded market→ZIP fallbacks (deprecated)
- `populate_location_market_zips.py` - API-based ZIP population
- `backfill_all_zips.py` - Job-level ZIP backfill (deprecated - too slow)
- `build_market_city_lists.py` - Generate city lists per market
- `MULTI_MARKET_SYSTEM.md` - Multi-market system documentation
- `ZIP_RADIUS_FILTERING.md` - ZIP radius filtering documentation

### Modified Files
- `market_mapper.py` - Added `return_all` param, Supabase integration
- `canonical_transforms.py` - ZIP extraction + API fallback
- `jobs_schema.py` - Added `norm.zip_code` field
- `job_memory_db.py` - Added ZIP upload mapping
- `driver_pulse_adapter.py` - Multi-market + ZIP integration

### Database Migrations
- `20251004221717_create_location_markets_library.sql`
- `20251004230241_add_zip_radius_to_free_agents.sql`
- `20251004232439_add_default_zips_to_location_markets.sql`
- `20251004191801_add_employer_uuid_to_companies.sql`
- `20251004192625_add_parent_company_hierarchy.sql`

---

## 8. Dependencies

### Python Libraries
- `geopy` - Distance calculations (installed ✅)
- `uszipcode` - ZIP geocoding (FAILED - dependency conflict ❌)
- `requests` - API calls for zippopotam.us (built-in ✅)

### External APIs
- **zippopotam.us** - Free ZIP code geocoding (no API key needed)
- Rate limit: ~10 req/sec with 0.1s delays

---

## 9. Next Steps

### Immediate (In Progress)
1. ✅ Wait for `populate_location_market_zips.py` to finish (576/3,041 done)
2. ⏳ Complete job ZIP backfill using `location_markets.default_zips`
3. ⏳ Build market city lists with `build_market_city_lists.py`

### Short Term
1. Update Google Jobs scraper to use city lists instead of radius logic
2. Implement ZIP radius filtering in agent portal
3. Add ZIP/radius fields to Free Agent Management UI
4. Test end-to-end with real agents

### Future Enhancements
1. Store pre-computed nearby_zips array in `free_agents` table
2. Use PostGIS for spatial queries (alternative to Python distance calc)
3. Agent-level distance display: "12.3 miles from you"
4. Market priority ranking for multi-market jobs

---

## 10. Key Takeaways

### What Works Now
✅ Multi-market job distribution (Stockton → Bay Area, Sacramento)
✅ ZIP extraction from location strings (Indeed jobs)
✅ ZIP API fallback for jobs without ZIPs (Google jobs)
✅ DriverPulse integration with lat/lng mapping
✅ Database schema ready for ZIP radius filtering

### What's Pending
⏳ Complete ZIP population in `location_markets` (18.9% done)
⏳ Backfill all jobs with ZIP codes
⏳ Build comprehensive city lists per market
⏳ Update Google scraper to use city lists
⏳ Agent portal ZIP radius filtering

### Known Issues
❌ `uszipcode` library has dependency conflicts - using API instead
❌ Backfill scripts slow due to API rate limits
❌ Need to complete `default_zips` population before city list generation
