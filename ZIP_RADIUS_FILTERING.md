# ZIP Code Radius Filtering System

## Overview
Instead of filtering jobs by broad "markets" at scrape time, we now:
1. **Scrape broadly** - Pull ALL jobs from wide geographic areas
2. **Preserve ZIP codes** - Extract and store ZIP from job locations
3. **Filter at agent level** - Each Free Agent sets their ZIP + radius preference
4. **Calculate distance** - Show only jobs within X miles of agent's ZIP

## Benefits

### For Coaches
- **One scrape serves all agents** - No need to run separate searches per location
- **Better coverage** - Broad scrapes capture more opportunities
- **Cost efficient** - Single API call vs multiple targeted searches

### For Free Agents
- **Personalized results** - See jobs relevant to THEIR exact location
- **Adjustable radius** - Can expand/contract search area as needed
- **Accurate distances** - "12 miles from you" vs generic "Houston market"

## Architecture

### 1. Data Collection (Preserve ZIP codes)

**Normalization** (`canonical_transforms.py`):
```python
def parse_location(location: str) -> Tuple[str, str, str, str]:
    # Input: "Houston, TX 77064"
    # Output: (city, state, full_location, zip_code)
    # Returns: ("Houston", "TX", "Houston, TX", "77064")
```

**Schema** (`jobs_schema.py`):
```python
'norm.zip_code': str,  # Extracted ZIP code (5 or 5+4 digits)
```

**Database**:
```sql
ALTER TABLE jobs ADD COLUMN zip_code TEXT;
CREATE INDEX idx_jobs_zip_code ON jobs(zip_code);
```

### 2. Agent Preferences (Free Agents table)

**Migration** (`20251004230241_add_zip_radius_to_free_agents.sql`):
```sql
ALTER TABLE free_agents ADD COLUMN zip_code TEXT;
ALTER TABLE free_agents ADD COLUMN zip_radius_miles INTEGER DEFAULT 25;
```

**Free Agent record**:
```json
{
  "id": 123,
  "name": "John Driver",
  "zip_code": "77064",
  "zip_radius_miles": 25,
  "pathway_preferences": ["CDL Jobs", "Dock→Driver"]
}
```

### 3. Distance Calculation

**Using uszipcode library**:
```python
from uszipcode import SearchEngine
from geopy.distance import geodesic

search = SearchEngine()

# Get agent ZIP coordinates
agent_zip = search.by_zipcode("77064")
agent_coords = (agent_zip.lat, agent_zip.lng)

# Get job ZIP coordinates
job_zip = search.by_zipcode("77001")
job_coords = (job_zip.lat, job_zip.lng)

# Calculate distance
distance = geodesic(agent_coords, job_coords).miles
# Returns: 12.3 miles
```

### 4. Agent Portal Filtering

**Current Query** (market-based):
```python
jobs = supabase.table('jobs')\
    .select('*')\
    .eq('market', agent_market)\
    .execute()
```

**New Query** (ZIP radius-based):
```python
# Step 1: Get agent preferences
agent = supabase.table('free_agents').select('*').eq('id', agent_id).single().execute()
agent_zip = agent.data['zip_code']
agent_radius = agent.data['zip_radius_miles']

# Step 2: Get agent ZIP coordinates
search = SearchEngine()
agent_zipinfo = search.by_zipcode(agent_zip)
agent_coords = (agent_zipinfo.lat, agent_zipinfo.lng)

# Step 3: Get all jobs with ZIP codes in general area (state-level pre-filter)
jobs = supabase.table('jobs')\
    .select('*')\
    .eq('normalized_location', f'%{agent_zipinfo.state}%')\
    .execute()

# Step 4: Filter by distance in Python
filtered_jobs = []
for job in jobs.data:
    if not job['zip_code']:
        continue

    job_zipinfo = search.by_zipcode(job['zip_code'])
    if not job_zipinfo:
        continue

    job_coords = (job_zipinfo.lat, job_zipinfo.lng)
    distance = geodesic(agent_coords, job_coords).miles

    if distance <= agent_radius:
        job['distance_miles'] = round(distance, 1)
        filtered_jobs.append(job)

# Step 5: Sort by distance (closest first)
filtered_jobs.sort(key=lambda x: x['distance_miles'])
```

## Implementation Plan

### Phase 1: Data Pipeline ✅
- [x] Update `parse_location()` to extract ZIP codes
- [x] Add `norm.zip_code` to schema
- [x] Add `zip_code` column to jobs table
- [x] Migration pushed to Supabase

### Phase 2: Agent Preferences ✅
- [x] Add `zip_code` and `zip_radius_miles` to free_agents table
- [x] Migration pushed to Supabase
- [ ] Update Free Agent Management UI to capture ZIP + radius
- [ ] Set sensible defaults (radius=25 miles)

### Phase 3: Portal Filtering 🔄
- [ ] Install required libraries (`pip3 install uszipcode geopy`)
- [ ] Update `agent_portal_clean.py` to use ZIP radius filtering
- [ ] Add distance display in job cards ("12.3 miles away")
- [ ] Remove market-based filtering (or use as secondary filter)

### Phase 4: Scraping Strategy
- [ ] Update scraping to be state/region-based (broader coverage)
- [ ] Remove tight location filters from Outscraper/Google APIs
- [ ] Rely on ZIP radius filtering to narrow results per agent

## Example Workflow

### Scenario: Houston-area Free Agent

**Agent Profile**:
```
Name: John Driver
ZIP: 77064 (Northwest Houston)
Radius: 25 miles
Pathways: CDL Jobs, Dock→Driver
```

**Coach runs broad scrape**:
```python
# Search entire Houston metro + surrounding areas
pipeline.run_search(
    location="Houston, TX",
    radius=100,  # Wide coverage
    job_limit=500
)
```

**Jobs stored with ZIP codes**:
```
Job 1: CDL Driver - Houston, TX 77001 (Downtown)
Job 2: Warehouse - Houston, TX 77064 (Northwest)
Job 3: CDL Driver - Houston, TX 77338 (Humble)
Job 4: Dock Worker - Katy, TX 77450
```

**Agent portal calculates distances**:
```
ZIP 77001 → 77064: 18.2 miles ✓ (within 25)
ZIP 77064 → 77064: 0.0 miles ✓ (within 25)
ZIP 77338 → 77064: 22.1 miles ✓ (within 25)
ZIP 77450 → 77064: 15.8 miles ✓ (within 25)
```

**Agent sees personalized results**:
```
✓ Warehouse Worker - 0.0 miles away
✓ Dock Worker (Katy) - 15.8 miles away
✓ CDL Driver (Downtown) - 18.2 miles away
✓ CDL Driver (Humble) - 22.1 miles away
```

## Performance Considerations

### Database Query Optimization
- Pre-filter by state to reduce dataset size
- Use indexed ZIP column for faster lookups
- Cache ZIP coordinates to avoid repeated geocoding

### ZIP Geocoding Cache
```python
# Global cache to avoid repeated lookups
zip_cache = {}

def get_zip_coords(zip_code):
    if zip_code not in zip_cache:
        zipinfo = search.by_zipcode(zip_code)
        zip_cache[zip_code] = (zipinfo.lat, zipinfo.lng)
    return zip_cache[zip_code]
```

### Supabase RPC Function (Future)
Create a PostgreSQL function for server-side distance calculation:
```sql
CREATE OR REPLACE FUNCTION jobs_within_radius(
    agent_zip TEXT,
    radius_miles INTEGER
) RETURNS TABLE(...) AS $$
BEGIN
    -- Calculate distances using PostGIS
    -- Return only jobs within radius
END;
$$ LANGUAGE plpgsql;
```

## Migration Path

1. **Backfill existing jobs** - Extract ZIP from `location` field for historical data
2. **Update Free Agent UI** - Add ZIP + radius fields to management interface
3. **Update Agent Portal** - Switch from market-based to ZIP radius filtering
4. **Test with real agents** - Validate accuracy and performance
5. **Deprecate market filtering** - Keep markets for analytics only

## Testing

```bash
# Test ZIP extraction
python3 -c "
from canonical_transforms import parse_location
result = parse_location('Houston, TX 77064')
print(f'ZIP extracted: {result[3]}')
"

# Test distance calculation
python3 -c "
from uszipcode import SearchEngine
from geopy.distance import geodesic

search = SearchEngine()
zip1 = search.by_zipcode('77064')
zip2 = search.by_zipcode('77001')

coords1 = (zip1.lat, zip1.lng)
coords2 = (zip2.lat, zip2.lng)

distance = geodesic(coords1, coords2).miles
print(f'Distance: {distance:.1f} miles')
"
```
