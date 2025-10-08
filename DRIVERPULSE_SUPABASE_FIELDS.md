# DriverPulse → Supabase Field Mapping

## Complete Field List for DriverPulse Jobs

### Core Job Information
| Field | Source | Example | Notes |
|-------|--------|---------|-------|
| `job_id` | `id.job` (pipeline generated) | `527534de2f2912a2f2e5edd16907bb9a` | MD5 hash of job content |
| `job_title` | `norm.title` → `source.title` | `CDL A OTR Drivers - No Experience Needed` | Normalized by pipeline |
| `company` | `norm.company` → `source.company` | `10-4 Truck Recruiting LLC` | Normalized by pipeline |
| `location` | `norm.location` → `source.location` | `Mc Calla, AL` | **✅ NOW: City, ST from ZIP lookup** |
| `zip_code` | `norm.zip_code` → `source.zip_code` | `35111` | **✅ FIXED: From DriverPulse ZIP field** |
| `job_description` | `norm.description` → `source.description_raw` | (HTML content) | **✅ FIXED: Combined description + requirements + benefits** |
| `apply_url` | `source.url` | `https://pulse.tenstreet.com/...` | DriverPulse application URL |
| `salary` | `norm.salary_display` → `source.salary` | `$0.50 - $0.55 CPM` | Formatted from min/max pay fields |

### AI Classification Results
| Field | Source | Example | Notes |
|-------|--------|---------|-------|
| `match_level` | `ai.match` | `good` | CDL job quality: good/so-so/bad |
| `match_reason` | `ai.reason` | `No experience needed for recent CDL school graduates` | Why this rating was given |
| `summary` | `ai.summary` | (Full job summary) | AI-generated structured summary |
| `fair_chance` | `ai.fair_chance` | `no_requirements_mentioned` | Fair chance hiring status |
| `endorsements` | `ai.endorsements` | `none_required` | Required CDL endorsements |
| `route_type` | `ai.route_type` | `OTR` | Route type classification |
| `career_pathway` | `ai.career_pathway` | `cdl_pathway` | Career progression pathway |
| `training_provided` | `ai.training_provided` | `false` | Company provides CDL training |

### Organization & Tracking
| Field | Source | Example | Notes |
|-------|--------|---------|-------|
| `market` | `meta.market` | `TX` | Market/state abbreviation |
| `tracked_url` | `meta.tracked_url` | `https://freeworldjobs.short.gy/d5LDqY` | Short.io tracking link |
| `source` | (hardcoded) | `driver_pulse` | Always "driver_pulse" |
| `filter_reason` | `route.final_status` | `included: good match` | Why job was included/excluded |

### Deduplication Fields
| Field | Source | Example | Notes |
|-------|--------|---------|-------|
| `rules_duplicate_r1` | `rules.duplicate_r1` | `85d60d0fe3c2208f` | Stage 1: Company+Location hash |
| `rules_duplicate_r2` | `rules.duplicate_r2` | `4b4d89ad4b3b928c` | Stage 2: Title+Company hash |
| `rules_duplicate_r3` | `rules.duplicate_r3` | (hash) | **✅ FIXED: Post-AI classification hash** |
| `clean_apply_url` | `route.clean_apply_url` | (cleaned URL) | Normalized apply URL for dedup |
| `job_id_hash` | `sys.hash` | (hash) | System-level unique hash |

### System Metadata
| Field | Source | Example | Notes |
|-------|--------|---------|-------|
| `classification_source` | (hardcoded) | `ai_classification` | How job was classified |
| `classified_at` | (auto-generated) | `2025-10-07 10:18:13.42127+00` | When AI classified the job |
| `created_at` | (auto-generated) | `2025-10-07 10:18:13.421271+00` | When record was created |
| `updated_at` | (auto-generated) | `2025-10-07 10:18:13.421271+00` | When record was updated |

### Legacy/Unused Fields (Empty for DriverPulse)
| Field | Value | Notes |
|-------|-------|-------|
| `indeed_job_url` | (empty) | Only used for Indeed jobs |
| `google_job_url` | (empty) | Only used for Google Jobs |
| `search_query` | (empty) | Not applicable to DriverPulse |
| `success_coach` | `null` | Not assigned at ingestion time |

## Data Transformation Pipeline

```
DriverPulse API Response
    ↓
driver_pulse_adapter.py
    - _combine_job_content() → Combines description + requirements + benefits
    - _format_location() → Converts ZIP → City, ST using zip_market_lookup
    - _format_salary() → Formats pay range
    ↓
pipeline_v3.py (Normalization Stage)
    - Creates norm.title, norm.company, norm.location
    - Creates norm.description from source.description_raw
    - Creates norm.zip_code from source.zip_code
    - Creates norm.salary_display
    ↓
pipeline_v3.py (AI Classification Stage)
    - Runs CDL classifier → ai.match, ai.reason, ai.summary
    - Runs pathway classifier → ai.career_pathway, ai.training_provided
    - Extracts ai.fair_chance, ai.endorsements, ai.route_type
    ↓
pipeline_v3.py (Deduplication Stage)
    - Generates rules.duplicate_r1, rules.duplicate_r2, rules.duplicate_r3
    ↓
async_job_manager.py
    - Maps pipeline fields to FLAT Supabase field names
    - Passes to memory_db.store_classifications()
    ↓
job_memory_db.py
    - Builds final record with all fields
    - Truncates job_description to 5000 chars
    - Converts all values to strings
    - Calls RPC function batch_insert_jobs()
    ↓
Supabase jobs table
```

## Recent Fixes (October 7, 2025)

### Problems Identified
1. ❌ `location` was empty (should be City, ST)
2. ❌ `job_description` was empty (should have combined content)
3. ❌ `zip_code` was empty (should have ZIP from DriverPulse)
4. ❌ `rules_duplicate_r3` was null (should have post-AI dedup hash)

### Solutions Implemented
1. ✅ Regenerated `zip_market_lookup.py` with `ZIP_TO_CITY_STATE` dictionary (13,983 ZIPs)
2. ✅ Updated `driver_pulse_adapter._format_location()` to use City, ST lookup
3. ✅ Updated `async_job_manager.py` to prefer `norm.*` fields over `source.*` fields
4. ✅ Added `rules_duplicate_r3` to both async_job_manager and job_memory_db mappings

### Field Source Priority (Updated)
- `location`: **norm.location** (City, ST from ZIP) → source.location (fallback)
- `job_description`: **norm.description** (combined HTML) → source.description_raw (fallback)
- `zip_code`: **norm.zip_code** (from pipeline) → source.zip_code (fallback)
- `salary`: **norm.salary_display** (formatted) → source.salary (fallback)

All DriverPulse jobs now have complete, consistent data matching the rest of the application!
