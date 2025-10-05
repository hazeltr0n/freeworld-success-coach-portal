# Multi-Market Job System

## Overview
Jobs can now belong to **multiple markets** simultaneously, allowing better coverage for overlapping geographic areas like Stockton/Bay Area and Newark/Trenton.

## Architecture

### 1. Database Layer (`location_markets` table)
```sql
CREATE TABLE location_markets (
    id SERIAL PRIMARY KEY,
    location_string TEXT NOT NULL,  -- "city, st" or ZIP code
    location_type TEXT NOT NULL,    -- 'city', 'zip', or 'coordinate'
    markets TEXT[] NOT NULL,        -- Array of market names
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    ...
);
```

**Supports:**
- Multiple markets per location via PostgreSQL arrays
- Fast lookups by location string or coordinates
- Extensible to ZIP codes and lat/lng coordinates

### 2. Market Mapping (`market_mapper.py`)
Enhanced to return multiple markets:

```python
mapper = MarketMapper()

# Single market (backward compatible)
market = mapper.map_market(location_string="Stockton, CA")
# Returns: "Stockton"

# ALL markets (new)
markets = mapper.map_market(location_string="Stockton, CA", return_all=True)
# Returns: ["Stockton", "Bay Area"]
```

**Input Methods:**
1. **"City, ST" strings** - Uses 1,376+ city lookup table from `market_lookup`
2. **ZIP codes** - Via `uszipcode` library (converts to city, then looks up)
3. **Lat/lng coordinates** - Via `geopy` distance calculation (50-mile radius)

### 3. Multi-Market Handler (`multi_market_handler.py`)
Duplicates jobs for multiple markets with unique job IDs:

```python
from multi_market_handler import duplicate_jobs_for_markets

# Input: DataFrame with jobs
df_original = pd.DataFrame([{
    'job_id': 'ABC123',
    'norm.location': 'Stockton, CA',
    'job_title': 'CDL Driver'
}])

# Output: Duplicated for each market
df_multi = duplicate_jobs_for_markets(df_original)

# Results:
# job_id              | market      | job_title
# -------------------|-------------|------------
# ABC123_stockton    | Stockton    | CDL Driver
# ABC123_bay_area    | Bay Area    | CDL Driver
```

**Key Features:**
- **Unique job_id per market**: Appends market suffix (e.g., `_stockton`, `_bay_area`)
- **No PRIMARY KEY conflicts**: Each `(job_id, market)` combination is unique
- **Preserves original ID**: Stores in `metadata.original_job_id` for tracking
- **Backward compatible**: Single-market jobs keep original job_id

### 4. DriverPulse Integration
DriverPulse provides lat/lng coordinates for every job, making it perfect for multi-market mapping:

```python
# In driver_pulse_adapter.py
df = transform_ingest_outscraper(outscraper_format, run_id, search_location)

# Apply multi-market mapping using lat/lng
df = duplicate_jobs_for_markets(df, self.market_mapper)
```

**Workflow:**
1. DriverPulse API returns job with `lat`, `lng`, `zip`, `state`
2. Adapter stores as top-level fields: `latitude`, `longitude`, `zip_code`
3. `duplicate_jobs_for_markets()` uses coordinates to find ALL markets within 50 miles
4. Creates one record per market with unique `job_id`

## Benefits

### For Coaches
- **Better coverage**: Stockton coach sees relevant Bay Area jobs
- **No duplicates**: Deduplication still works via R1/R2 hashes
- **Simple queries**: `WHERE market = 'Dallas'` - no array operations needed

### For Free Agents
- **More opportunities**: Jobs appear in all relevant markets
- **Better matching**: Geographic preferences work across overlapping markets

### For Analytics
- **Accurate counts**: Each market gets proper job statistics
- **Easy reporting**: Standard SQL aggregations work (`GROUP BY market`)

## Examples

### Example 1: Stockton Job → Multiple Markets
```python
job = {
    'job_id': 'DP123',
    'latitude': 37.9577,
    'longitude': -121.2908,
    'job_title': 'Local CDL Driver'
}

markets = mapper.map_market(lat=37.9577, lng=-121.2908, return_all=True)
# Returns: ["Stockton", "Bay Area", "Sacramento"]

# Creates 3 job records:
# DP123_stockton     | Stockton     | Local CDL Driver
# DP123_bay_area     | Bay Area     | Local CDL Driver
# DP123_sacramento   | Sacramento   | Local CDL Driver
```

### Example 2: Newark/Trenton Overlap
```python
job = {
    'job_id': 'DP456',
    'latitude': 40.3573,
    'longitude': -74.6672,
    'job_title': 'Warehouse to Driver'
}

markets = mapper.map_market(lat=40.3573, lng=-74.6672, return_all=True)
# Returns: ["Newark", "Trenton"]

# Creates 2 job records:
# DP456_newark   | Newark   | Warehouse to Driver
# DP456_trenton  | Trenton  | Warehouse to Driver
```

## Migration Path

### Phase 1: Seed Location Markets Library ✅
```bash
python3 seed_location_markets.py
```
Populates `location_markets` table with:
- 1,376 city mappings from existing MarketMapper
- Real-world location→market pairs from production jobs table
- Multi-market locations identified automatically

### Phase 2: Update DriverPulse Adapter ✅
- Add `duplicate_jobs_for_markets()` call in `convert_to_pipeline_format()`
- Store lat/lng as top-level fields for market mapping
- Market-specific job_id generation

### Phase 3: Update Pipeline v3 (Future)
- Integrate multi-market support into main pipeline
- Update CSV classifier to use enhanced MarketMapper
- Add analytics for multi-market job performance

## Backward Compatibility

- **Existing code works unchanged**: `return_all=False` (default) returns single market
- **Single-market jobs unchanged**: Keep original job_id when only one market matches
- **Deduplication preserved**: R1/R2 hashes work across all job copies
- **No schema changes**: Uses existing `job_id` and `market` fields

## Future Enhancements

1. **Coach Market Preferences**: Allow coaches to specify primary + secondary markets
2. **Distance-Based Filtering**: Show "X miles from your area" for cross-market jobs
3. **Market Priority Ranking**: Weight markets by distance or coach preference
4. **ZIP Code Library**: Build comprehensive ZIP→markets table for faster lookups
5. **Supabase Function**: Create stored procedure for market lookup at database level
