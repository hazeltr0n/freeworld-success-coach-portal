# DriverPulse API → Canonical Schema Field Mapping

## 📊 Complete Field Mapping Strategy

### DriverPulse API Fields (24 total)
From `get_carrier_active_job_detail` endpoint:

```python
DRIVERPULSE_FIELDS = {
    # Job Identity
    'active_job_id': 'Unique job ID from DriverPulse',
    'company_id': 'Company identifier',
    'job_title': 'Job title',

    # Company Info
    'company_name': 'Company name',
    'company_logo': 'Logo filename',
    'company_url_part': 'URL slug for company profile',
    'url_part': 'Duplicate of company_url_part',

    # Job Content (THE GOLD MINE)
    'job_description': 'Full HTML job description',
    'job_requirements': 'HTML requirements text - CDL class, experience years, endorsements',
    'job_general_benefits': 'Benefits text',

    # Compensation
    'job_pay': 'Single pay value (often null when min/max exist)',
    'job_min_pay': 'Minimum pay',
    'job_max_pay': 'Maximum pay',
    'job_min_max_pay_unit': 'Pay unit (e.g., "per week", "per hour")',

    # Location Data
    'state': 'State abbreviation',
    'zip': 'ZIP code',
    'lat': 'Latitude',
    'lng': 'Longitude',
    'location_type': 'Type of location (zip_radius, state, etc.)',
    'zip_within': 'Radius distance',
    'value': 'Radius value for zip searches',
    'ident': 'Location identifier type',

    # Scraper Metadata
    'scraped_at': 'Timestamp when scraped',
    'search_term': 'Original search query'
}
```

---

## 🎯 Proposed Canonical Schema Mapping

### IDENTITY Namespace
```python
'id.job' → generate_job_id(company_name, location, job_title)
'id.source' → 'driver_pulse'
'id.source_row' → active_job_id  # DriverPulse unique job ID
```

### SOURCE Namespace (Raw/Immutable Data)
```python
'source.title' → job_title
'source.company' → company_name
'source.location_raw' → f"{zip}, {state}" or just state if zip is missing
'source.description_raw' → job_description (full HTML)
'source.url' → f"https://pulse.tenstreet.com/{company_url_part}/job/{active_job_id}"
'source.salary_raw' → format_salary(job_pay, job_min_pay, job_max_pay, job_min_max_pay_unit)
'source.posted_date' → ''  # Not available from API
```

**NEW FIELDS TO ADD TO SCHEMA:**
```python
'source.requirements_raw' → job_requirements  # CRITICAL for classification
'source.benefits_raw' → job_general_benefits
'source.company_id' → company_id
'source.company_logo' → company_logo
'source.latitude' → lat
'source.longitude' → lng
```

### NORMALIZED Namespace
```python
'norm.title' → clean_html(job_title)
'norm.company' → clean_html(company_name)
'norm.state' → state
'norm.city' → ''  # Extract from ZIP lookup if needed
'norm.location' → f"{city}, {state}" or just state
'norm.description' → strip_html(job_description)
'norm.salary_min' → parse_salary(job_min_pay, job_min_max_pay_unit)
'norm.salary_max' → parse_salary(job_max_pay, job_min_max_pay_unit)
'norm.salary_unit' → normalize_unit(job_min_max_pay_unit)  # "per week" → "week"
'norm.salary_display' → format_display(job_min_pay, job_max_pay, job_min_max_pay_unit)
'norm.salary_currency' → 'USD'  # Default
```

**NEW FIELDS TO ADD TO SCHEMA:**
```python
'norm.requirements' → strip_html(job_requirements)  # Clean text for AI
'norm.benefits' → strip_html(job_general_benefits)
```

### RULES Namespace
```python
# These will be extracted from job_requirements field using regex/AI
'rules.is_owner_op' → detect_owner_operator(job_title, job_description, job_requirements)
'rules.is_school_bus' → detect_school_bus(job_title, job_description)
'rules.has_experience_req' → detect_experience(job_requirements)  # Look for "X years"
'rules.experience_years_min' → extract_years(job_requirements)  # "2 years" → 2.0
```

### AI Namespace (Classification Inputs)
**CRITICAL CHANGE:** AI classifier should receive:
```python
# Current classification input (OLD):
classification_input = {
    'title': norm.title,
    'company': norm.company,
    'location': norm.location,
    'description': norm.description  # Just the description
}

# NEW classification input (PROPOSED):
classification_input = {
    'title': norm.title,
    'company': norm.company,
    'location': norm.location,
    'description': norm.description,
    'requirements': norm.requirements,  # ← CRITICAL: Separate requirements section
    'benefits': norm.benefits,          # ← Helpful for fair chance analysis
    'salary': norm.salary_display       # ← Helpful for quality assessment
}
```

**AI Output Fields (unchanged):**
```python
'ai.match' → 'good|so-so|bad|error'
'ai.reason' → AI reasoning
'ai.summary' → 4-6 sentence summary
'ai.fair_chance' → Background check analysis
'ai.endorsements' → CDL endorsements (extract from job_requirements)
'ai.route_type' → 'Local|OTR|Regional'
'ai.career_pathway' → Pathway classification
'ai.training_provided' → bool
```

### METADATA Namespace
```python
'meta.market' → state or custom market from search config
'meta.query' → search_term
'meta.search_terms' → search_term
```

**NEW FIELDS:**
```python
'meta.driver_pulse_company_id' → company_id
'meta.driver_pulse_job_id' → active_job_id
'meta.driver_pulse_company_url' → f"https://pulse.tenstreet.com/{company_url_part}"
```

### SEARCH Namespace
```python
'search.location' → Original search location
'search.radius' → zip_within (if location_type == 'zip_radius')
'search.exact_location' → location_type != 'zip_radius'
```

### SYSTEM Namespace
```python
'sys.created_at' → scraped_at
'sys.scraped_at' → scraped_at
'sys.run_id' → Pipeline run ID
'sys.source' → 'driver_pulse'
```

---

## 🔧 Implementation Changes Required

### 1. Update `jobs_schema.py` - Add New Fields
```python
COLUMN_REGISTRY = {
    # ... existing fields ...

    # === SOURCE (add these) ===
    'source.requirements_raw': str,   # Raw requirements HTML
    'source.benefits_raw': str,       # Raw benefits text
    'source.company_id': str,         # DriverPulse company ID
    'source.company_logo': str,       # Company logo filename
    'source.latitude': float,         # Geo coordinates
    'source.longitude': float,        # Geo coordinates

    # === NORMALIZED (add these) ===
    'norm.requirements': str,         # Cleaned requirements text
    'norm.benefits': str,             # Cleaned benefits text
}
```

### 2. Update `driver_pulse_adapter.py` - Use Full Job Data
```python
def _convert_to_outscraper_format(self, jobs: List[Dict]) -> List[Dict]:
    """Convert DriverPulse job format to Outscraper-compatible format"""
    outscraper_jobs = []

    for job in jobs:
        outscraper_job = {
            # Basic fields
            'title': job.get('job_title', ''),
            'company': job.get('company_name', ''),
            'snippet': job.get('job_description', ''),  # Full HTML description
            'formattedLocation': f"{job.get('zip', '')}, {job.get('state', '')}",

            # URL - construct from DriverPulse pattern
            'viewJobLink': f"https://pulse.tenstreet.com/{job.get('company_url_part', '')}/job/{job.get('active_job_id', '')}",

            # Salary
            'salarySnippet': self._format_salary(job),

            # NEW: Requirements and Benefits
            'requirements': job.get('job_requirements', ''),  # ← CRITICAL
            'benefits': job.get('job_general_benefits', ''),

            # NEW: Company metadata
            'company_id': job.get('company_id', ''),
            'company_logo': job.get('company_logo', ''),
            'company_url_part': job.get('company_url_part', ''),

            # NEW: Geo data
            'latitude': job.get('lat', ''),
            'longitude': job.get('lng', ''),

            # Metadata
            'source': 'driver_pulse',
            'scraped_at': job.get('scraped_at', ''),
            'search_term': job.get('search_term', ''),
        }

        outscraper_jobs.append(outscraper_job)

    return outscraper_jobs

def _format_salary(self, job: Dict) -> str:
    """Format salary from DriverPulse fields"""
    min_pay = job.get('job_min_pay', '')
    max_pay = job.get('job_max_pay', '')
    unit = job.get('job_min_max_pay_unit', '')

    if min_pay and max_pay:
        return f"${min_pay} - ${max_pay} {unit}"
    elif job.get('job_pay'):
        return f"${job.get('job_pay')} {unit}"
    return ''
```

### 3. Update `canonical_transforms.py` - Map New Fields
```python
def transform_ingest_outscraper(jobs: List[Dict], run_id: str, market: str) -> pd.DataFrame:
    """Transform Outscraper (or DriverPulse) data to canonical format"""

    for job in jobs:
        canonical_job = {
            # ... existing mappings ...

            # NEW: Requirements and Benefits
            'source.requirements_raw': job.get('requirements', ''),
            'source.benefits_raw': job.get('benefits', ''),

            # NEW: Company metadata
            'source.company_id': job.get('company_id', ''),
            'source.company_logo': job.get('company_logo', ''),

            # NEW: Geo data
            'source.latitude': float(job.get('latitude', 0)) if job.get('latitude') else None,
            'source.longitude': float(job.get('longitude', 0)) if job.get('longitude') else None,
        }
```

### 4. Update `job_classifier.py` - Use Requirements Field
```python
def classify_job(self, job_data: Dict) -> Dict:
    """Classify a single job"""

    # Build classification prompt with separate requirements section
    prompt = f"""
Job Title: {job_data.get('title', '')}
Company: {job_data.get('company', '')}
Location: {job_data.get('location', '')}

Job Description:
{job_data.get('description', '')}

Requirements:
{job_data.get('requirements', '')}  # ← NEW: Separate section for clarity

Benefits:
{job_data.get('benefits', '')}

Salary: {job_data.get('salary', '')}

Please classify this CDL driving job...
"""
```

### 5. Update Pipeline Stage 2 - Normalize Requirements
```python
def _stage2_normalization(self, df: pd.DataFrame) -> pd.DataFrame:
    """Stage 2: Normalize raw data to clean canonical format"""

    # ... existing normalizations ...

    # NEW: Normalize requirements and benefits
    if 'source.requirements_raw' in df.columns:
        df['norm.requirements'] = df['source.requirements_raw'].apply(strip_html)

    if 'source.benefits_raw' in df.columns:
        df['norm.benefits'] = df['source.benefits_raw'].apply(strip_html)

    return df
```

---

## 📈 Benefits of This Mapping

1. **Better Classification Accuracy**
   - AI gets separate `requirements` field with experience years, CDL class, endorsements
   - No more parsing requirements from mixed description text
   - Clear separation of job duties vs. qualifications

2. **Complete Data Preservation**
   - All DriverPulse fields mapped to canonical schema
   - Geo coordinates preserved for future features
   - Company metadata available for analytics

3. **Backward Compatibility**
   - Existing Outscraper/Google Jobs ingestion still works
   - New fields are optional (nullable in schema)
   - Pipeline stages don't break if fields are empty

4. **Improved Business Rules**
   - `rules.experience_years_min` can be extracted from clean `norm.requirements`
   - More accurate owner-operator detection
   - Better salary parsing from structured pay fields

5. **Future-Proof**
   - Benefits field available for fair chance analysis
   - Geo coordinates ready for radius filtering
   - Company ID enables deduplication across markets

---

## ⚡ Quick Start Implementation Order

1. **Phase 1: Schema Updates** (5 min)
   - Add new fields to `COLUMN_REGISTRY` in `jobs_schema.py`
   - Run schema validation test

2. **Phase 2: Adapter Updates** (10 min)
   - Update `driver_pulse_adapter.py` to map all 24 fields
   - Add `_format_salary()` helper method

3. **Phase 3: Transform Updates** (10 min)
   - Update `canonical_transforms.py` to handle new fields
   - Add HTML stripping for requirements/benefits

4. **Phase 4: Classifier Updates** (15 min)
   - Update `job_classifier.py` prompt to use separate requirements section
   - Test classification accuracy improvement

5. **Phase 5: Testing** (10 min)
   - Run end-to-end test with real DriverPulse data
   - Validate all fields are populated correctly

**Total Time: ~50 minutes**
