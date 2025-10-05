# DriverPulse → Canonical Schema Mapping (ZERO Schema Changes)

## 🎯 Strategy: Combine DriverPulse fields into existing schema fields

### Mapping Rules

We have 24 DriverPulse fields → 139 existing canonical fields. NO new fields added.

---

## 📋 Field-by-Field Mapping

### IDENTITY Namespace
```python
'id.job' → generate_job_id(company_name, f"{zip}, {state}", job_title)
'id.source' → 'driver_pulse'
'id.source_row' → active_job_id  # DriverPulse unique job ID
```

### SOURCE Namespace (Raw/Immutable)
```python
'source.title' → job_title
'source.company' → company_name
'source.location_raw' → f"{zip}, {state}" if zip else state
'source.url' → f"https://pulse.tenstreet.com/{company_url_part}/job/{active_job_id}"
'source.posted_date' → ''  # Not available

# CRITICAL: Combine description + requirements + benefits into ONE field
'source.description_raw' → COMBINED FORMAT:
    """
    {job_description}

    <h3>Requirements</h3>
    {job_requirements}

    <h3>Benefits</h3>
    {job_general_benefits}
    """

# Salary: Format from structured fields
'source.salary_raw' → format_salary(job_min_pay, job_max_pay, job_pay, job_min_max_pay_unit)
    # Examples:
    # "$1200 - $1800 per week"
    # "$24.50 per hour"
```

### NORMALIZED Namespace
```python
'norm.title' → clean_html(job_title)
'norm.company' → clean_html(company_name)
'norm.state' → state
'norm.city' → lookup_city_from_zip(zip) or ''  # Optional ZIP lookup
'norm.location' → f"{city}, {state}" if city else state

# Strip HTML from combined description
'norm.description' → strip_html(source.description_raw)
    # This will contain: description + requirements + benefits as clean text

# Parse salary from structured fields
'norm.salary_min' → parse_to_annual(job_min_pay, job_min_max_pay_unit)
'norm.salary_max' → parse_to_annual(job_max_pay, job_min_max_pay_unit)
'norm.salary_unit' → normalize_unit(job_min_max_pay_unit)
    # "per week" → "week"
    # "per hour" → "hour"
'norm.salary_display' → f"${job_min_pay} - ${job_max_pay} {job_min_max_pay_unit}"
'norm.salary_currency' → 'USD'
```

### RULES Namespace
```python
# Extract from combined norm.description text
'rules.is_owner_op' → detect_owner_operator(norm.title, norm.description)
'rules.is_school_bus' → detect_school_bus(norm.title, norm.description)
'rules.has_experience_req' → detect_experience(norm.description)
'rules.experience_years_min' → extract_years_from_requirements(norm.description)
    # Regex: r"(\d+)\+?\s*years?\s*(of\s*)?(experience|CDL)"
```

### AI Namespace
```python
# AI gets the full combined description with sections
# No changes needed - existing classifier receives norm.description

'ai.match' → 'good|so-so|bad|error'
'ai.reason' → AI reasoning
'ai.summary' → 4-6 sentence summary
'ai.endorsements' → Extract from requirements section
'ai.route_type' → 'Local|OTR|Regional'
'ai.fair_chance' → From requirements/benefits sections
```

### METADATA Namespace
```python
'meta.market' → state or custom market
'meta.query' → search_term
'meta.tracked_url' → Short.io link (generated later)

# Use existing meta fields for DriverPulse-specific data
'meta.airtable_id' → company_id  # Repurpose this field for DriverPulse company ID
```

### SEARCH Namespace
```python
'search.location' → f"{zip}, {state}"
'search.radius' → int(zip_within) if zip_within else 0
'search.exact_location' → location_type != 'zip_radius'
```

### SYSTEM Namespace
```python
'sys.created_at' → scraped_at
'sys.run_id' → Pipeline run ID
'sys.source' → 'driver_pulse'
'sys.is_fresh_job' → True
```

---

## 🔧 Implementation: Update `driver_pulse_adapter.py` Only

### Combined Description Format
```python
def _combine_job_content(self, job: Dict) -> str:
    """Combine description, requirements, and benefits into single HTML block"""

    parts = []

    # Main description
    description = job.get('job_description', '')
    if description:
        parts.append(description)

    # Requirements section (CRITICAL for classification)
    requirements = job.get('job_requirements', '')
    if requirements:
        parts.append('<h3>Requirements</h3>')
        parts.append(requirements)

    # Benefits section
    benefits = job.get('job_general_benefits', '')
    if benefits:
        parts.append('<h3>Benefits</h3>')
        parts.append(benefits)

    return '\n\n'.join(parts)

def _format_salary(self, job: Dict) -> str:
    """Format salary from DriverPulse structured fields"""

    min_pay = job.get('job_min_pay', '')
    max_pay = job.get('job_max_pay', '')
    single_pay = job.get('job_pay', '')
    unit = job.get('job_min_max_pay_unit', '')

    # Handle range
    if min_pay and max_pay:
        return f"${min_pay} - ${max_pay} {unit}"

    # Handle single value
    if single_pay:
        return f"${single_pay} {unit}"

    # Handle min only
    if min_pay:
        return f"${min_pay}+ {unit}"

    return ''

def _format_location(self, job: Dict) -> str:
    """Format location from DriverPulse geo fields"""

    zip_code = job.get('zip', '')
    state = job.get('state', '')

    if zip_code and state:
        return f"{zip_code}, {state}"
    elif state:
        return state

    return ''

def _build_application_url(self, job: Dict) -> str:
    """Construct DriverPulse application URL"""

    company_url = job.get('company_url_part', '')
    job_id = job.get('active_job_id', '')

    if company_url and job_id:
        return f"https://pulse.tenstreet.com/{company_url}/job/{job_id}"

    return ''
```

### Updated Adapter
```python
def _convert_to_outscraper_format(self, jobs: List[Dict]) -> List[Dict]:
    """Convert DriverPulse job format to Outscraper-compatible format

    ZERO SCHEMA CHANGES: Combines description + requirements + benefits into
    source.description_raw field using HTML sections.
    """
    outscraper_jobs = []

    for job in jobs:
        outscraper_job = {
            # Basic fields
            'title': job.get('job_title', ''),
            'company': job.get('company_name', ''),

            # COMBINED: description + requirements + benefits
            'snippet': self._combine_job_content(job),

            # FORMATTED: location from zip + state
            'formattedLocation': self._format_location(job),

            # CONSTRUCTED: DriverPulse URL
            'viewJobLink': self._build_application_url(job),

            # Job ID (maps to id.source_row)
            'job_id': job.get('active_job_id', ''),

            # FORMATTED: Salary from structured fields
            'salarySnippet': self._format_salary(job),

            # Metadata
            'source': 'driver_pulse',
            'scraped_at': job.get('scraped_at', datetime.now().isoformat()),
            'search_term': job.get('search_term', ''),

            # Store DriverPulse company ID in existing meta field
            # (repurpose meta.airtable_id since we're not using Airtable here)
            'company_metadata': json.dumps({
                'driver_pulse_company_id': job.get('company_id', ''),
                'company_logo': job.get('company_logo', ''),
                'company_url_part': job.get('company_url_part', ''),
                'latitude': job.get('lat', ''),
                'longitude': job.get('lng', ''),
            }),

            # Market from DriverPulse scraper context
            'meta.market': job.get('market_scraped', job.get('state', '')),
        }

        # Ensure required fields
        if not outscraper_job['title']:
            outscraper_job['title'] = 'CDL Driver Position'
        if not outscraper_job['company']:
            outscraper_job['company'] = 'Unknown Company'
        if not outscraper_job['formattedLocation']:
            outscraper_job['formattedLocation'] = 'Unknown Location'

        outscraper_jobs.append(outscraper_job)

    return outscraper_jobs
```

---

## 🎨 Example: Combined Description Output

### Input (DriverPulse API):
```json
{
  "job_description": "<strong>Zimmerman Transfer Inc.</strong> is looking for a Milk Hauler...",
  "job_requirements": "<ul><li>Class A CDL License</li><li>CDL Tanker Endorsement</li><li>2+ years experience</li></ul>",
  "job_general_benefits": "No ELOG - We are Ag Exempt. Health insurance. 401k matching."
}
```

### Output (source.description_raw):
```html
<strong>Zimmerman Transfer Inc.</strong> is looking for a Milk Hauler...

<h3>Requirements</h3>
<ul><li>Class A CDL License</li><li>CDL Tanker Endorsement</li><li>2+ years experience</li></ul>

<h3>Benefits</h3>
No ELOG - We are Ag Exempt. Health insurance. 401k matching.
```

### After Normalization (norm.description):
```text
Zimmerman Transfer Inc. is looking for a Milk Hauler...

Requirements
- Class A CDL License
- CDL Tanker Endorsement
- 2+ years experience

Benefits
No ELOG - We are Ag Exempt. Health insurance. 401k matching.
```

---

## 📊 AI Classifier Impact

The AI classifier will receive a **better structured** description with clear sections:

```python
classification_input = {
    'title': 'Home Daily Milk Hauler',
    'company': 'Zimmerman Transfer, Inc.',
    'location': '53543, WI',
    'description': """
        Zimmerman Transfer Inc. is looking for a Milk Hauler...

        Requirements
        - Class A CDL License
        - CDL Tanker Endorsement
        - 2+ years experience

        Benefits
        No ELOG - We are Ag Exempt. Health insurance. 401k matching.
    """
}
```

**Result:** AI can easily find the Requirements section and extract:
- CDL Class: A
- Endorsements: Tanker
- Experience: 2+ years
- Fair Chance: Not mentioned → likely background check required

---

## ✅ Advantages of Zero-Schema Approach

1. **No Schema Changes Required**
   - Use existing `source.description_raw` field
   - No migration needed
   - No risk of breaking existing code

2. **Clear Section Headers**
   - AI can identify Requirements vs Benefits vs Description
   - Better than mixed HTML blob
   - Structured but flexible

3. **All Data Preserved**
   - Nothing lost from DriverPulse API
   - Company metadata stored as JSON in meta field
   - Geo coordinates available if needed later

4. **Backward Compatible**
   - Outscraper/Google Jobs still work (they don't have Requirements/Benefits sections)
   - Pipeline stages unchanged
   - Existing classifiers work better with structured input

5. **Simple Implementation**
   - Only update `driver_pulse_adapter.py`
   - Add 4 helper methods
   - ~30 minutes total

---

## 🚀 Implementation Checklist

- [ ] Add `_combine_job_content()` method
- [ ] Add `_format_salary()` method
- [ ] Add `_format_location()` method
- [ ] Add `_build_application_url()` method
- [ ] Update `_convert_to_outscraper_format()` to use helpers
- [ ] Test with real DriverPulse data
- [ ] Verify AI classification accuracy improves

**Total Time: ~30 minutes**

No schema changes. No migration. Just better data formatting.
