# DriverPulse API Reference

**Source**: Reverse-engineered from network sniffing and testing
**Last Updated**: October 6, 2025
**Working Implementation**: `driver_pulse_scraper_v2.py`

## 🔑 Authentication

Handled via browser cookies stored in `auth.json` (created by `create_driver_pulse_auth.py`)

Required cookies:
- `PHPSESSID`
- `portal_symlink_path`
- `mobileapp_device_registration`

## 📡 API Endpoints

Base URL: `https://pulse.tenstreet.com/`

All API calls use `source._call_api(endpoint_name, params)` method from `driver_pulse_source.py`.

---

### 1. `search_carriers` - Search for Companies

**Purpose**: Get list of companies with job IDs

**Parameters**:
```python
{
    "search_text": "CDL driver",      # Search term
    "page_number": 1,                  # Page number (1-indexed)
    "portal_user_id": "19880939",      # From auth
    "user_timezone": "America/Chicago" # User timezone
}
```

**Returns**:
```python
{
    "response": {
        "2338306": {  # Company ID
            "company_id": "2338306",
            "company_name": "Zimmerman Transfer, Inc.",
            "logo_link": "2338306_logo.png",
            "url_part": "zimmermantransfer",
            "highlighted_content": [  # JOB LISTINGS (snippets only)
                {
                    "job_id": "99468",           # USE THIS to get full details
                    "job_title": "Home Daily Milk Hauler",
                    "search_term": "CDL",
                    "section": "Job Requirements",
                    "value": "Class A <em>CDL</em> License...",
                    "is_pulse_match_posting": true
                }
            ]
        },
        "has_results": true,
        "result_count": 4186
    }
}
```

**Important Notes**:
- **Location parameter is IGNORED** - returns all companies regardless of location
- `highlighted_content` only has JOB SNIPPETS (title, job_id)
- **NO ZIP/lat/lng data** in this response
- Must use `job_id` to get full job details

---

### 2. `get_carrier_active_job_detail` - Get Full Job Details

**Purpose**: Get complete job data including ZIP, lat/lng, description, requirements, benefits, salary

**Parameters**:
```python
{
    "company_id": "2338306",           # From search_carriers
    "active_job_id": "99468",          # From highlighted_content
    "user_timezone": "America/Chicago"
}
```

**Returns**:
```python
{
    "response": [  # Array with 1 element
        {
            # Job Info
            "active_job_id": 99468,
            "job_title": "Home Daily Milk Hauler",
            "job_description": "<full HTML description>",
            "job_requirements": "<full HTML requirements>",
            "job_general_benefits": "<full HTML benefits>",

            # Salary
            "job_min_pay": "1200",
            "job_max_pay": "1800",
            "job_min_max_pay_unit": "per week",
            "job_pay": "",  # Single value if not a range

            # Location Data (THIS IS THE KEY!)
            "zip": "53543",
            "state": "WI",
            "lat": 43.042113,
            "lng": -90.131187,
            "location_type": "zip_radius",
            "zip_within": 25,

            # Company Info (redundant with search_carriers)
            "company_id": 2338306,
            "company_name": "Zimmerman Transfer, Inc.",
            "company_logo": "2338306_logo.png",
            "company_url_part": "zimmermantransfer",
            "url_part": "zimmermantransfer",
            "ident": "A",
            "value": "<full HTML content>"
        }
    ]
}
```

**Critical Fields**:
- ✅ `zip`, `state`, `lat`, `lng` - Location data for market mapping
- ✅ `job_description`, `job_requirements`, `job_general_benefits` - Full HTML content for AI
- ✅ `job_min_pay`, `job_max_pay`, `job_min_max_pay_unit` - Structured salary data
- ✅ `active_job_id` - Unique job identifier

---

### 3. `get_company_details` - Get Company Profile

**Purpose**: Get company profile text and metadata

**Parameters**:
```python
{
    "company_id": "2338306"
}
```

**Returns**:
```python
{
    "company_id": 2338306,
    "company_name": "Zimmerman Transfer, Inc.",
    "has_active_jobs": true,
    "has_profile": true,
    "logo_link": "2338306_logo.png",
    "url_part": "zimmermantransfer",
    "pulsechat_enabled": false,
    "profile_text": "<full HTML company profile>"
}
```

**Use Case**: Get company description for job context (optional - not required for basic scraping)

---

## 🔄 Complete Scraping Workflow

```python
from driver_pulse_source import DriverPulseSource, DriverPulseConfig

# 1. Authenticate
source = DriverPulseSource()
source.load_authentication()

# 2. Search for companies (page 1)
search_result = source.search_companies(search_text="CDL", page_number=1)
companies = search_result['response']

# 3. Extract job IDs from highlighted_content
for company_id, company_data in companies.items():
    if company_id in ['has_results', 'result_count', 'default_companies_selected']:
        continue

    highlighted_jobs = company_data.get('highlighted_content', [])

    # 4. Get full details for each job
    for job_snippet in highlighted_jobs:
        job_id = job_snippet.get('job_id')

        # THIS IS THE KEY CALL
        full_job = source._call_api("get_carrier_active_job_detail", {
            "company_id": company_id,
            "active_job_id": job_id,
            "user_timezone": "America/Chicago"
        })

        if full_job and full_job.get('response'):
            job_data = full_job['response'][0]

            # Now you have:
            # - job_data['zip'], job_data['state'], job_data['lat'], job_data['lng']
            # - job_data['job_description'], job_data['job_requirements']
            # - job_data['job_min_pay'], job_data['job_max_pay']
```

---

## 📊 Data Flow Summary

```
search_carriers
    ↓
companies with highlighted_content
    ↓
Extract job_id from each highlighted job
    ↓
get_carrier_active_job_detail (company_id + job_id)
    ↓
Full job data with ZIP/lat/lng
```

---

## ⚠️ Important Findings

1. **Location parameter doesn't work** in `search_carriers` - always returns all companies
2. **Pagination is required** - use `page_number` to get all companies
3. **highlighted_content** only has snippets - must call `get_carrier_active_job_detail` for full data
4. **ZIP/lat/lng** only available from `get_carrier_active_job_detail` endpoint
5. **Rate limiting** recommended: 0.3 seconds between `get_carrier_active_job_detail` calls

---

## 🎯 Working Implementation

See `driver_pulse_scraper_v2.py` for complete working example that:
1. Authenticates
2. Searches companies (paginated)
3. Extracts job IDs from highlighted_content
4. Fetches full job details for each job
5. Saves complete job data with ZIP/lat/lng

Output format matches what `driver_pulse_adapter.py` expects for pipeline integration.
