# DriverPulse Pipeline Complete Trace
**Generated: October 7, 2025**

This document traces the COMPLETE flow of DriverPulse data from button click to Supabase storage, documenting every file called and every data transformation.

---

## 🚀 Entry Point: Button Click in Streamlit UI

**File**: `app.py`
**Line**: 6776
**Trigger**: User clicks "Run Now" button in DriverPulse section

```python
if dp_run_now:
    dp_search_params['run_immediately'] = True
    job = dp_manager.submit_driver_pulse_search(dp_search_params, coach.username)
```

**What happens**:
- Creates `AsyncJobManager` instance (`dp_manager`)
- Calls `submit_driver_pulse_search()` with search parameters and coach username
- Search parameters include: `search_terms`, `filter_settings` (filter_mode, custom_zips, classifier_type)

---

## 📋 Stage 1: Job Queue Creation

**File**: `async_job_manager.py`
**Method**: `submit_driver_pulse_search()` (lines 391-589)

### Step 1.1: Create Job Entry in Supabase (line 394)
```python
job = self.create_job_entry(coach_username, 'driver_pulse_jobs', search_params)
```
- Inserts record into `async_job_queue` table
- Status: `'pending'`
- Returns `AsyncJob` object with job ID

### Step 1.2: Initialize DriverPulse Integration (line 397-400)
```python
from driver_pulse_adapter import DriverPulsePipelineIntegration
integration = DriverPulsePipelineIntegration()
```

### Step 1.3: Update Job Status to Processing (lines 403-406)
```python
self.update_job(job.id, {
    'status': 'processing',
    'submitted_at': datetime.now(timezone.utc).isoformat()
})
```

### Step 1.4: Notify Coach (lines 408-414)
```python
self.notify_coach(
    coach_username,
    f"🔄 DriverPulse scrape started for '{search_params['search_terms']}'!",
    'search_submitted',
    job.id
)
```

---

## 🔍 Stage 2: DriverPulse Scraping & Filtering

**File**: `driver_pulse_adapter.py`
**Method**: `run_driver_pulse_through_pipeline()` (lines 294-598)

### Step 2.1: Load Target ZIP Codes (lines 319-322)
```python
filter_mode = filter_settings.get('filter_mode', 'all_markets')
custom_zips = filter_settings.get('custom_zips', None)
target_zips = self._load_location_markets(filter_mode, custom_zips)
```

**What happens**:
- If `filter_mode == "custom_zips"`: Uses custom ZIP list
- If `filter_mode == "all_markets"`: Loads all ZIPs from `zip_market_lookup.VALID_ZIPS`
- Returns set of ~4,561 ZIPs for FreeWorld markets OR custom list

### Step 2.2: Authenticate with DriverPulse API (lines 324-349)
```python
from driver_pulse_source import DriverPulseSource, DriverPulseConfig

# Load credentials from Streamlit secrets
email = st.secrets.get('DRIVER_PULSE_EMAIL')
first_name = st.secrets.get('DRIVER_PULSE_FIRST_NAME')
last_name = st.secrets.get('DRIVER_PULSE_LAST_NAME')
phone = st.secrets.get('DRIVER_PULSE_PHONE')

source.create_new_authentication(email, first_name, last_name, phone)
```

**What happens**:
- Creates fresh authentication session via Playwright browser automation
- Generates auth cookies and headers for API calls
- **File**: `driver_pulse_source.py` handles Playwright authentication

### Step 2.3: Paginate Through All Companies (lines 354-398)
```python
all_companies = {}
page_num = 1
max_pages = 13  # API limit

while page_num <= max_pages:
    result = source.search_companies(search_text=search_terms, page_number=page_num)
    companies = result['response']

    for company_id in company_ids:
        all_companies[company_id] = companies[company_id]

    page_num += 1
```

**What happens**:
- Searches DriverPulse for companies matching `search_terms`
- Paginates through up to 13 pages (page 14+ returns no results)
- Each company has `highlighted_content` list containing job IDs
- Returns ~1000-2000 companies with ~10K-12K total jobs

### Step 2.4: Fetch Full Job Details in Parallel (lines 404-456)
```python
total_job_ids = sum(len(c.get('highlighted_content', [])) for c in all_companies.values())

def fetch_job_detail(job_info):
    company_id, company_data, job_snippet = job_info
    result = source._call_api("get_carrier_active_job_detail", detail_params)
    full_job = result['response'][0]
    full_job['company_name'] = company_data.get('company_name')
    return full_job

with ThreadPoolExecutor(max_workers=20) as executor:
    for future in as_completed(futures):
        job = future.result()
        if job:
            all_jobs.append(job)
```

**What happens**:
- Loops through all companies' `highlighted_content` job snippets
- Calls API endpoint `get_carrier_active_job_detail` for each job ID
- 20 parallel workers for speed
- Returns ~10K-12K complete job records with all fields:
  - `job_title`, `company_name`, `job_description`, `job_requirements`, `job_general_benefits`
  - `zip`, `state`, `lat`, `lng`
  - `job_min_pay`, `job_max_pay`, `job_pay`, `job_min_max_pay_unit`
  - `active_job_id`, `company_id`, `company_url_part`, `company_logo`

### Step 2.5: Convert to Outscraper Format (lines 459-460)
```python
outscraper_jobs = self.adapter._convert_to_outscraper_format(all_jobs)
```

**File**: `driver_pulse_adapter.py`
**Method**: `_convert_to_outscraper_format()` (lines 152-223)

**Data Transformations**:
```python
for job in jobs:
    outscraper_job = {
        'title': job.get('job_title', ''),
        'company': job.get('company_name', ''),

        # COMBINED: description + requirements + benefits
        'snippet': self._combine_job_content(job),  # Lines 33-60

        # FORMATTED: City, ST from ZIP lookup
        'formattedLocation': self._format_location(job),  # Lines 83-100

        # CONSTRUCTED: DriverPulse application URL
        'viewJobLink': self._build_application_url(job),  # Lines 102-110

        # FORMATTED: Salary from structured fields
        'salarySnippet': self._format_salary(job),  # Lines 62-81

        # METADATA
        'zip_code': job.get('zip', ''),
        'latitude': job.get('lat', ''),
        'longitude': job.get('lng', ''),
        'source': 'driver_pulse',

        # CRITICAL: FreeWorld market from ZIP
        'meta.market': ZIP_TO_FREEWORLD_MARKET.get(job.get('zip', ''), job.get('state', ''))  # Line 210
    }
```

**Key Helper Methods**:

1. **`_combine_job_content()`** (lines 33-60):
   ```python
   parts = []

   # Main description
   if job.get('job_description'):
       parts.append(job.get('job_description'))

   # Requirements section (CRITICAL for classification)
   if job.get('job_requirements'):
       parts.append('<h3>Requirements</h3>')
       parts.append(job.get('job_requirements'))

   # Benefits section
   if job.get('job_general_benefits'):
       parts.append('<h3>Benefits</h3>')
       parts.append(job.get('job_general_benefits'))

   return '\n\n'.join(parts)
   ```

2. **`_format_location()`** (lines 83-100):
   ```python
   zip_code = job.get('zip', '')

   # Use ZIP → City, ST lookup
   if zip_code and ZIP_LOOKUP_AVAILABLE:
       city_state = ZIP_TO_CITY_STATE.get(zip_code)
       if city_state:
           return city_state  # e.g., "Dallas, TX"

   # Fallback: "ZIP, STATE"
   if zip_code and state:
       return f"{zip_code}, {state}"
   ```

3. **`_format_salary()`** (lines 62-81):
   ```python
   min_pay = job.get('job_min_pay', '')
   max_pay = job.get('job_max_pay', '')
   unit = job.get('job_min_max_pay_unit', '')

   if min_pay and max_pay:
       return f"${min_pay} - ${max_pay} {unit}"  # e.g., "$0.50 - $0.55 CPM"
   ```

### Step 2.6: Filter to Target ZIP Codes (lines 463-483)
```python
if target_zips:
    jobs_before = len(outscraper_jobs)

    filtered_jobs = []
    for job in outscraper_jobs:
        job_zip = str(job.get('zip_code', '')).zfill(5)
        if job_zip in target_zips:
            filtered_jobs.append(job)

    outscraper_jobs = filtered_jobs
    jobs_after = len(outscraper_jobs)

    print(f"   Before filter: {jobs_before} jobs")
    print(f"   After filter: {jobs_after} jobs")
```

**What happens**:
- Filters 10K-12K jobs → ~600-1,500 jobs based on target ZIP codes
- **CRITICAL**: This happens BEFORE AI classification to save costs
- 85-95% reduction in jobs to classify

---

## 🔄 Stage 3: Pipeline Format Conversion

**File**: `driver_pulse_adapter.py` (line 500)
**Next File**: `canonical_transforms.py`

```python
from canonical_transforms import transform_ingest_outscraper
df = transform_ingest_outscraper(outscraper_jobs, self.adapter.run_id, "")
```

**File**: `canonical_transforms.py`
**Function**: `transform_ingest_outscraper()` (estimated lines 140-180)

**What happens**:
- Converts Outscraper-format list to pandas DataFrame
- Maps fields to namespaced pipeline format:

```python
source_mapping = {
    'title': 'source.title',
    'company': 'source.company',
    'snippet': 'source.description_raw',
    'formattedLocation': 'source.location_raw',
    'viewJobLink': 'source.url',
    'salarySnippet': 'source.salary_raw',
    'zip_code': 'source.zip_code',  # NEW: Direct ZIP from DriverPulse
}
```

**DataFrame Structure After Conversion**:
```
Columns:
- id.job: MD5 hash of job content
- id.source: 'driver_pulse'
- id.source_row: Job index
- source.title: "CDL A OTR Drivers - No Experience Needed"
- source.company: "10-4 Truck Recruiting LLC"
- source.description_raw: "<description>\n\n<h3>Requirements</h3>\n<requirements>\n\n<h3>Benefits</h3>\n<benefits>"
- source.location_raw: "Dallas, TX"
- source.url: "https://pulse.tenstreet.com/..."
- source.salary_raw: "$0.50 - $0.55 CPM"
- source.zip_code: "75060"
- meta.market: "Dallas"
- sys.scraped_at: ISO timestamp
- sys.run_id: "driver_pulse_20251007_..."
- sys.is_fresh_job: True
```

### Step 3.1: Override Source to DriverPulse (line 503)
```python
df['id.source'] = 'driver_pulse'
```

### Step 3.2: Add Pipeline Metadata (line 516)
```python
df = self.adapter.add_pipeline_metadata(df, coach_username, search_terms)
```

**Method**: `add_pipeline_metadata()` (lines 225-247)
```python
metadata_updates = {
    'meta.coach': coach_username,
    'meta.search_terms': search_terms,
    'meta.data_source': 'driver_pulse',
    'meta.run_id': self.run_id,
    'sys.scraped_at': datetime.now().isoformat(),
    'sys.pipeline_version': 'v3_driver_pulse_adapter'
}
```

---

## 🧠 Stage 4: Pipeline Processing

**File**: `driver_pulse_adapter.py` (lines 518-560)
**Next File**: `pipeline_v3.py`

```python
from pipeline_v3 import FreeWorldPipelineV3
pipeline = FreeWorldPipelineV3()

# Run through pipeline stages
df = pipeline._stage2_normalization(df)
df = pipeline._stage3_business_rules(df, "", filter_settings or {})
df = pipeline._stage4_deduplication(df)
df = pipeline._stage5_ai_classification(df, classifier_type="cdl")
df = pipeline._stage6_routing(df, "")
```

### Stage 4.1: Normalization

**File**: `pipeline_v3.py`
**Method**: `_stage2_normalization()` (lines 1192-1202)

```python
df = transform_normalize(df)
```

**File**: `canonical_transforms.py`
**Function**: `transform_normalize()` (estimated lines 200-300)

**Data Transformations**:
- Creates `norm.*` fields from `source.*` fields:
  - `norm.title`: Cleaned job title (remove special chars, normalize case)
  - `norm.company`: Cleaned company name
  - `norm.location`: Formatted location
  - `norm.description`: HTML-stripped description (for AI classification)
  - `norm.zip_code`: Validated 5-digit ZIP from `source.zip_code`
  - `norm.salary_display`: Formatted salary string
  - `norm.salary_min`, `norm.salary_max`: Parsed numeric values

**Example**:
```python
# Before:
source.description_raw = "<p>Drive for us!</p>\n\n<h3>Requirements</h3>\n<ul><li>CDL A</li></ul>"

# After:
norm.description = "Drive for us! Requirements: CDL A"  # HTML stripped for AI
```

### Stage 4.2: Business Rules

**File**: `pipeline_v3.py`
**Method**: `_stage3_business_rules()` (lines 1204-1231)

```python
# Apply market assignment
df = apply_market_assignment(df, market, is_custom_location=False)

# Apply business rules
df = transform_business_rules(df, filter_settings={})
```

**File**: `canonical_transforms.py`
**Functions**:
- `apply_market_assignment()`: Validates/sets `meta.market` field
- `transform_business_rules()`: Creates `rules.*` fields

**Data Transformations**:
- Creates deduplication hashes:
  - `rules.duplicate_r1`: MD5(company|location) - catches same job, same location
  - `rules.duplicate_r2`: MD5(company|title) - catches different locations, same company/title
- Quality flags:
  - `rules.is_owner_op`: Boolean (checks for "owner operator" keywords)
  - `rules.is_school_bus`: Boolean (checks for "school bus" keywords)
  - `rules.is_spam_source`: Boolean (checks company against spam list)
  - `rules.quality_score`: Numeric score (0-100)

### Stage 4.3: Deduplication

**File**: `pipeline_v3.py`
**Method**: `_stage4_deduplication()` (lines 1233-1354)

**What happens**:
1. **Exact Duplicates** (line 1257):
   ```python
   df = df.drop_duplicates(subset=['id.job'], keep='last')
   ```
   - Removes exact same job_id (MD5 hash)
   - Keeps 'last' (fresh data wins over memory data)

2. **R1 Deduplication** (lines 1260-1276):
   ```python
   r1_groups = df.groupby('rules.duplicate_r1')
   for group_key, group_df in r1_groups:
       if len(group_df) > 1:
           # Keep first, mark others as filtered
           df.loc[dupe_indices, 'route.final_status'] = 'filtered: R1 collapse (company+title+market)'
           df.loc[dupe_indices, 'route.filtered'] = True
   ```

3. **R2 Deduplication** (lines 1278-1296):
   ```python
   r2_groups = df.groupby('rules.duplicate_r2')
   # Same company + market, different titles → keep one
   ```

4. **URL Deduplication** (lines 1298-1325):
   ```python
   # Group by clean_apply_url + market
   # Same URL can appear from multiple sources (Indeed + Google)
   ```

**CRITICAL**: Filtered jobs are NOT removed, just marked:
- `route.filtered = True`
- `route.final_status = 'filtered: R1 collapse (company+title+market)'`
- `route.ready_for_ai = False` (don't waste AI classification on dupes)

### Stage 4.4: AI Classification

**File**: `pipeline_v3.py`
**Method**: `_stage5_ai_classification()` (lines 1379-1534)

#### Step 4.4.1: Check Memory for Existing Classifications (lines 1392-1424)
```python
if not force_fresh_classification:
    job_ids_to_check = list(fresh_unclassified['id.job'].unique())
    memory_lookup = self.memory_db.check_job_memory(job_ids_to_check, hours=720)
```

**File**: `job_memory_db.py`
**Method**: `check_job_memory()` (lines 456-505)

**What happens**:
- Queries Supabase `jobs` table for existing classifications
- Uses batched queries (500 job IDs at a time)
- Returns dict of `{job_id: {classification fields}}`

**CRITICAL**: Since we ZIP-filtered to ~600-1,500 jobs, memory check queries:
```python
batch_size = 500
# Query 1: First 500 job IDs
# Query 2: Next 500 job IDs
# Query 3: Last 100-500 job IDs
```

**Memory check runs AFTER ZIP filtering**, so we only check ~1,500 jobs, not 11K.

#### Step 4.4.2: Prepare Jobs for Classification (lines 1432-1485)
```python
jobs_for_ai = []
for _, job in fresh_unclassified.iterrows():
    raw_desc = job.get('source.description_raw', '')
    clean_desc = job.get('norm.description', '')

    # Prefer cleaned description
    final_desc = clean_desc if clean_desc and str(clean_desc).strip() else raw_desc

    job_data = {
        'job_id': job['id.job'],
        'job_title': job.get('source.title', ''),
        'company': job.get('source.company', ''),
        'location': job.get('source.location_raw', ''),
        'job_description': final_desc
    }
    jobs_for_ai.append(job_data)
```

#### Step 4.4.3: Run AI Classifier (lines 1487-1533)
```python
if classifier_type == "pathway":
    selected_classifier = self.pathway_classifier
elif classifier_type == "cdl":
    selected_classifier = self.cdl_classifier

ai_results = selected_classifier.classify_jobs_in_batches(jobs_for_ai)
ai_lookup = {result['job_id']: result for result in ai_results}

df = transform_ai_classification(df, ai_lookup, job_ids_classified=None)
```

**File**: `job_classifier.py` OR `pathway_classifier.py`
**Method**: `classify_jobs_in_batches()`

**What happens**:
- Batches jobs into groups of 10-25
- Calls OpenAI GPT-4o-mini for each batch
- Returns structured JSON with fields:
  - `match`: "good" / "so-so" / "bad"
  - `reason`: Why this rating was given
  - `summary`: Structured job summary
  - `fair_chance`: "no_requirements_mentioned" / "fair_chance_friendly" / etc
  - `endorsements`: "none_required" / "hazmat" / etc
  - `route_type`: Set by RouteClassifier BEFORE AI (Local/OTR/Regional/Unknown)

**File**: `canonical_transforms.py`
**Function**: `transform_ai_classification()` (estimated lines 400-500)

**Data Transformations**:
- Maps AI results to `ai.*` fields:
  - `ai.match`: "good" / "so-so" / "bad"
  - `ai.reason`: String explanation
  - `ai.summary`: Full summary
  - `ai.fair_chance`: Fair chance status
  - `ai.endorsements`: Required endorsements
  - `ai.route_type`: **PRESERVED from RouteClassifier** (NOT overwritten)
  - `ai.career_pathway`: "cdl_pathway" / "dock_to_driver" / etc
  - `ai.training_provided`: Boolean

**CRITICAL FIX**: `async_job_manager.py` lines 841, 843 were removed to preserve `ai.route_type`:
```python
# REMOVED (was overwriting route_type with 'Unknown'):
# jobs_df['ai.route_type'] = classified_df.get('route_type', 'Unknown')

# NOW: ai.route_type is already set by RouteClassifier - don't overwrite
```

#### Step 4.4.4: Generate R3 Dedup Hash (lines 1528-1532)
```python
df['rules.duplicate_r3'] = df.apply(lambda row: self._generate_r3_hash(row), axis=1)
```

**Method**: `_generate_r3_hash()` (lines 1356-1377)
```python
company = str(row.get('norm.company', '')).lower().strip()
market = str(row.get('meta.market', '')).lower().strip()
route_type = str(row.get('ai.route_type', 'Unknown')).lower().strip()
match_level = str(row.get('ai.match', 'unknown')).lower().strip()

# Normalize title
title = str(row.get('norm.title', '')).lower().strip()
for word in ['driver', 'cdl', 'class a', ...]:
    title = title.replace(word, '')

r3_key = f"{company}|{market}|{route_type}|{match_level}|{title}"
return hashlib.md5(r3_key.encode()).hexdigest()[:16]
```

**Result**: `rules.duplicate_r3` now populated (e.g., "3c35bd7437417d41")

### Stage 4.5: Routing

**File**: `pipeline_v3.py`
**Method**: `_stage6_routing()` (lines 1536-1555)

```python
df = transform_routing(df, route_filter)
```

**File**: `canonical_transforms.py`
**Function**: `transform_routing()` (estimated lines 600-700)

**What happens**:
- Sets `route.final_status` based on all filters:
  - If `route.filtered == True`: Status already set by business rules/dedup
  - If `ai.match == 'good'`: `'included: good match'`
  - If `ai.match == 'so-so'`: `'included: so-so match'`
  - If `ai.match == 'bad'`: `'filtered: bad match'`
- Sets `route.included` boolean
- Sets `route.ready_for_export` boolean

---

## 💾 Stage 5: Database Storage

**File**: `async_job_manager.py`
**Method**: `submit_driver_pulse_search()` (lines 486-531)

```python
from job_memory_db import JobMemoryDB
memory_db = JobMemoryDB()

# Build frame with FLAT field names
canon = pd.DataFrame()

# Core job info (FLAT names) - use norm.* fields preferentially
canon['job_id'] = df.get('id.job', df.index.map(str))
canon['job_title'] = df.get('norm.title', df.get('source.title', ''))
canon['company'] = df.get('norm.company', df.get('source.company', ''))
canon['location'] = df.get('norm.location', df.get('source.location', ''))
canon['job_description'] = df.get('norm.description', df.get('source.description_raw', ''))
canon['apply_url'] = df.get('source.url', '')
canon['zip_code'] = df.get('norm.zip_code', df.get('source.zip_code', ''))
canon['salary'] = df.get('norm.salary_display', df.get('source.salary', ''))

# AI classification (FLAT names)
canon['match_level'] = df.get('ai.match', '')
canon['match_reason'] = df.get('ai.reason', '')
canon['summary'] = df.get('ai.summary', '')
canon['route_type'] = df.get('ai.route_type', '')
canon['fair_chance'] = df.get('ai.fair_chance', '')
canon['endorsements'] = df.get('ai.endorsements', '')

# Routing status
canon['filter_reason'] = df.get('route.final_status', 'passed_all_filters')

# Tracking
canon['market'] = df.get('meta.market', '')
canon['tracked_url'] = df.get('meta.tracked_url', '')
canon['source'] = 'driver_pulse'

# Dedup hashes
canon['rules_duplicate_r1'] = df.get('rules.duplicate_r1', '')
canon['rules_duplicate_r2'] = df.get('rules.duplicate_r2', '')
canon['rules_duplicate_r3'] = df.get('rules.duplicate_r3', '')
canon['sys.hash'] = df.get('sys.hash', '')

stored_count = memory_db.store_classifications(canon)
```

**File**: `job_memory_db.py`
**Method**: `store_classifications()` (estimated lines 300-450)

**What happens**:
1. Converts namespaced fields to FLAT Supabase field names
2. Truncates `job_description` to 5000 chars
3. Converts all values to strings
4. Calls Supabase RPC function `batch_insert_jobs()`

**Supabase RPC Function**: `batch_insert_jobs()`
- Performs UPSERT on `jobs` table
- Conflict resolution: ON CONFLICT (job_id) DO UPDATE
- Updates `updated_at` timestamp
- Sets `classification_source = 'ai_classification'`
- Sets `classified_at = NOW()`

**Final Supabase Record Example**:
```json
{
  "job_id": "527534de2f2912a2f2e5edd16907bb9a",
  "job_title": "CDL A OTR Drivers - No Experience Needed",
  "company": "10-4 Truck Recruiting LLC",
  "location": "Dallas, TX",
  "zip_code": "75060",
  "job_description": "Drive for us!\n\nRequirements:\n- Valid CDL A license...",
  "apply_url": "https://pulse.tenstreet.com/...",
  "salary": "$0.50 - $0.55 CPM",
  "match_level": "good",
  "match_reason": "No experience needed for recent CDL school graduates",
  "summary": "OTR position for new CDL A drivers...",
  "route_type": "OTR",
  "fair_chance": "no_requirements_mentioned",
  "endorsements": "none_required",
  "market": "Dallas",
  "tracked_url": "https://freeworldjobs.short.gy/d5LDqY",
  "source": "driver_pulse",
  "filter_reason": "included: good match",
  "rules_duplicate_r1": "85d60d0fe3c2208f",
  "rules_duplicate_r2": "4b4d89ad4b3b928c",
  "rules_duplicate_r3": "3c35bd7437417d41",
  "classification_source": "ai_classification",
  "classified_at": "2025-10-07 10:18:13.42127+00",
  "created_at": "2025-10-07 10:18:13.421271+00",
  "updated_at": "2025-10-07 10:18:13.421271+00"
}
```

---

## 📊 Complete Data Flow Summary

### Input → Output Transformation

**Raw DriverPulse API Response**:
```json
{
  "active_job_id": "12345",
  "company_name": "10-4 Truck Recruiting LLC",
  "job_title": "CDL A OTR Drivers - No Experience Needed",
  "job_description": "<p>Drive for us!</p>",
  "job_requirements": "<ul><li>CDL A</li><li>Clean MVR</li></ul>",
  "job_general_benefits": "<ul><li>Health insurance</li></ul>",
  "zip": "75060",
  "state": "TX",
  "job_min_pay": "0.50",
  "job_max_pay": "0.55",
  "job_min_max_pay_unit": "CPM",
  "company_url_part": "10-4-recruiting"
}
```

**After Outscraper Conversion** (`driver_pulse_adapter.py`):
```python
{
  'title': 'CDL A OTR Drivers - No Experience Needed',
  'company': '10-4 Truck Recruiting LLC',
  'snippet': '<p>Drive for us!</p>\n\n<h3>Requirements</h3>\n<ul><li>CDL A</li><li>Clean MVR</li></ul>\n\n<h3>Benefits</h3>\n<ul><li>Health insurance</li></ul>',
  'formattedLocation': 'Dallas, TX',  # From ZIP_TO_CITY_STATE lookup
  'viewJobLink': 'https://pulse.tenstreet.com/10-4-recruiting/job/12345',
  'salarySnippet': '$0.50 - $0.55 CPM',
  'zip_code': '75060',
  'source': 'driver_pulse',
  'meta.market': 'Dallas'  # From ZIP_TO_FREEWORLD_MARKET lookup
}
```

**After Pipeline Ingestion** (`canonical_transforms.py`):
```python
{
  'id.job': '527534de2f2912a2f2e5edd16907bb9a',
  'id.source': 'driver_pulse',
  'source.title': 'CDL A OTR Drivers - No Experience Needed',
  'source.company': '10-4 Truck Recruiting LLC',
  'source.description_raw': '<p>Drive for us!</p>\n\n<h3>Requirements</h3>...',
  'source.location_raw': 'Dallas, TX',
  'source.url': 'https://pulse.tenstreet.com/10-4-recruiting/job/12345',
  'source.salary_raw': '$0.50 - $0.55 CPM',
  'source.zip_code': '75060',
  'meta.market': 'Dallas',
  'sys.scraped_at': '2025-10-07T10:15:00Z',
  'sys.is_fresh_job': True
}
```

**After Normalization** (`pipeline_v3.py`):
```python
{
  # ... all source.* fields preserved ...
  'norm.title': 'CDL A OTR Drivers - No Experience Needed',
  'norm.company': '10-4 Truck Recruiting LLC',
  'norm.location': 'Dallas, TX',
  'norm.description': 'Drive for us! Requirements: CDL A, Clean MVR. Benefits: Health insurance',
  'norm.zip_code': '75060',
  'norm.salary_display': '$0.50 - $0.55 CPM',
  'norm.salary_min': 0.50,
  'norm.salary_max': 0.55
}
```

**After Business Rules** (`pipeline_v3.py`):
```python
{
  # ... all previous fields preserved ...
  'rules.duplicate_r1': '85d60d0fe3c2208f',
  'rules.duplicate_r2': '4b4d89ad4b3b928c',
  'rules.is_owner_op': False,
  'rules.is_school_bus': False,
  'rules.is_spam_source': False,
  'rules.quality_score': 85
}
```

**After AI Classification** (`pipeline_v3.py`):
```python
{
  # ... all previous fields preserved ...
  'ai.match': 'good',
  'ai.reason': 'No experience needed for recent CDL school graduates',
  'ai.summary': 'OTR position for new CDL A drivers...',
  'ai.route_type': 'OTR',  # From RouteClassifier, NOT overwritten
  'ai.fair_chance': 'no_requirements_mentioned',
  'ai.endorsements': 'none_required',
  'ai.career_pathway': 'cdl_pathway',
  'ai.training_provided': False,
  'rules.duplicate_r3': '3c35bd7437417d41'  # Generated post-AI
}
```

**After Routing** (`pipeline_v3.py`):
```python
{
  # ... all previous fields preserved ...
  'route.final_status': 'included: good match',
  'route.included': True,
  'route.filtered': False,
  'route.ready_for_export': True
}
```

**Final Supabase Storage** (`job_memory_db.py`):
```sql
INSERT INTO jobs (
  job_id, job_title, company, location, zip_code, job_description,
  apply_url, salary, match_level, match_reason, summary, route_type,
  fair_chance, endorsements, market, tracked_url, source, filter_reason,
  rules_duplicate_r1, rules_duplicate_r2, rules_duplicate_r3,
  classification_source, classified_at, created_at, updated_at
) VALUES (
  '527534de2f2912a2f2e5edd16907bb9a',
  'CDL A OTR Drivers - No Experience Needed',
  '10-4 Truck Recruiting LLC',
  'Dallas, TX',
  '75060',
  'Drive for us! Requirements: CDL A, Clean MVR. Benefits: Health insurance',
  'https://pulse.tenstreet.com/10-4-recruiting/job/12345',
  '$0.50 - $0.55 CPM',
  'good',
  'No experience needed for recent CDL school graduates',
  'OTR position for new CDL A drivers...',
  'OTR',
  'no_requirements_mentioned',
  'none_required',
  'Dallas',
  'https://freeworldjobs.short.gy/d5LDqY',
  'driver_pulse',
  'included: good match',
  '85d60d0fe3c2208f',
  '4b4d89ad4b3b928c',
  '3c35bd7437417d41',
  'ai_classification',
  '2025-10-07 10:18:13.42127+00',
  '2025-10-07 10:18:13.421271+00',
  '2025-10-07 10:18:13.421271+00'
)
ON CONFLICT (job_id) DO UPDATE SET
  updated_at = EXCLUDED.updated_at,
  classified_at = EXCLUDED.classified_at;
```

---

## 🔍 Key Insights from Complete Trace

### 1. ZIP Filtering Optimization
- **Where**: `driver_pulse_adapter.py` lines 463-483
- **When**: AFTER fetching all jobs, BEFORE AI classification
- **Impact**: Reduces 10K-12K jobs → 600-1,500 jobs (85-95% reduction)
- **Cost Savings**: Only classify ~1,500 jobs instead of 12K

### 2. Memory Check Timing
- **Where**: `pipeline_v3.py` lines 1392-1424
- **When**: AFTER ZIP filtering, BEFORE AI classification
- **Query Size**: ~1,500 job IDs in batches of 500 (3 batches)
- **NOT**: Checking 11K jobs (that was the concern)

### 3. Field Priority in Supabase Storage
- **Location**: `norm.location` → `source.location` (fallback)
- **Description**: `norm.description` → `source.description_raw` (fallback)
- **ZIP**: `norm.zip_code` → `source.zip_code` (fallback)
- **Salary**: `norm.salary_display` → `source.salary` (fallback)

### 4. Critical Fixes Implemented
1. ✅ `location`: Now "City, ST" from `ZIP_TO_CITY_STATE` lookup
2. ✅ `job_description`: Combined description + requirements + benefits
3. ✅ `zip_code`: Mapped through `source_mapping` in `canonical_transforms.py`
4. ✅ `rules_duplicate_r3`: Generated post-AI classification
5. ✅ `market`: Uses `ZIP_TO_FREEWORLD_MARKET` for "Dallas", "Houston" (not "TX", "NY")
6. ✅ `route_type`: Preserved from RouteClassifier (async_job_manager lines 841, 843 removed)

### 5. Files Involved in Complete Flow
1. `app.py` - UI button click
2. `async_job_manager.py` - Job queue management
3. `driver_pulse_adapter.py` - DriverPulse API integration
4. `driver_pulse_source.py` - API authentication & calls
5. `zip_market_lookup.py` - ZIP → City/Market lookups
6. `canonical_transforms.py` - Data transformations
7. `pipeline_v3.py` - Pipeline orchestration
8. `job_classifier.py` - AI classification
9. `route_classifier.py` - Route type classification
10. `job_memory_db.py` - Supabase storage

---

## 🎯 End-to-End Timing Estimate

Based on a typical DriverPulse batch:

1. **Button Click → Job Queue**: < 1 second
2. **Authentication (Playwright)**: 10-15 seconds
3. **Company Search (13 pages)**: 20-30 seconds
4. **Job Detail Fetch (12K jobs, 20 workers)**: 60-90 seconds
5. **ZIP Filtering (12K → 1.5K)**: < 1 second
6. **Pipeline Ingestion**: 2-3 seconds
7. **Normalization**: 3-5 seconds
8. **Business Rules**: 1-2 seconds
9. **Deduplication**: 2-3 seconds
10. **Memory Check (3 batches)**: 3-5 seconds
11. **AI Classification (1.5K jobs)**: 120-180 seconds
12. **R3 Hash Generation**: 1-2 seconds
13. **Routing**: 1 second
14. **Supabase Storage**: 5-10 seconds

**Total**: ~3-5 minutes for complete pipeline execution

---

**End of Complete Pipeline Trace**
