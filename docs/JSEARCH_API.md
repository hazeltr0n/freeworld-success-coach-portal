# JSearch API Documentation

Complete reference documentation for the OpenWeb Ninja JSearch API. Provides real-time job listings and salary data from Google for Jobs.

## Base URL

```
https://api.openwebninja.com/jsearch
```

## Authentication

All requests require an API key in the header:

```
x-api-key: YOUR_API_KEY
```

---

## Endpoints

### 1. Job Search

**GET** `/search`

Search for jobs posted on any public job site across the web via Google for Jobs.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | **Yes** | - | Free-form search query. Include job title and location (e.g., "CDL driver jobs in Houston TX") |
| `page` | integer | No | 1 | Page to return (each page has up to 10 results). Range: 1-100 |
| `num_pages` | integer | No | 1 | Number of pages to return. Range: 1-20. **Pricing:** 1 page = 1x, 2-10 pages = 2x, 11-20 pages = 3x |
| `country` | string | No | "us" | Country code ([ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)) |
| `language` | string | No | - | Language code ([ISO 639](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes)) |
| `date_posted` | enum | No | "all" | Filter by posting date: `all`, `today`, `3days`, `week`, `month` |
| `work_from_home` | boolean | No | false | Only return remote/WFH jobs |
| `employment_types` | string | No | - | Comma-separated: `FULLTIME`, `CONTRACTOR`, `PARTTIME`, `INTERN` |
| `job_requirements` | string | No | - | Comma-separated: `under_3_years_experience`, `more_than_3_years_experience`, `no_experience`, `no_degree` |
| `radius` | number | No | - | Distance from location in km (not strictly enforced by Google) |
| `exclude_job_publishers` | string | No | - | Comma-separated list of publishers to exclude |
| `fields` | string | No | - | Comma-separated list of fields to include (field projection) |

#### Example Request

```bash
curl 'https://api.openwebninja.com/jsearch/search?query=CDL%20driver%20jobs%20in%20Houston%20TX&page=1&num_pages=1&country=us&date_posted=week&job_requirements=no_experience' \
  --header 'x-api-key: YOUR_API_KEY'
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | string | Unique job identifier |
| `job_title` | string | Job title |
| `employer_name` | string | Company name |
| `employer_logo` | string | URL to company logo |
| `employer_website` | string | Company website |
| `job_publisher` | string | Source (Indeed, LinkedIn, etc.) |
| `job_employment_type` | string | Employment type |
| `job_employment_types` | array | All employment types |
| `job_apply_link` | string | Primary apply URL |
| `job_apply_is_direct` | boolean | Direct application or redirect |
| `apply_options` | array | All apply links with publisher info |
| `job_description` | string | Full job description |
| `job_is_remote` | boolean | Remote job flag |
| `job_posted_at` | string | Human-readable posted date |
| `job_posted_at_timestamp` | integer | Unix timestamp |
| `job_posted_at_datetime_utc` | string | ISO 8601 datetime |
| `job_location` | string | Full location string |
| `job_city` | string | City |
| `job_state` | string | State |
| `job_country` | string | Country code |
| `job_latitude` | number | Latitude |
| `job_longitude` | number | Longitude |
| `job_benefits` | array | Benefits list |
| `job_google_link` | string | Google Jobs link |
| `job_min_salary` | number | Minimum salary |
| `job_max_salary` | number | Maximum salary |
| `job_salary_period` | string | Salary period (YEAR, MONTH, etc.) |
| `job_highlights` | object | Qualifications, Benefits, Responsibilities |
| `job_onet_soc` | string | O*NET SOC code |
| `job_onet_job_zone` | string | O*NET job zone |

---

### 2. Job Details

**GET** `/job-details`

Get full job details including application options, employer reviews, and salary estimates.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `job_id` | string | **Yes** | - | Job ID from search results. Supports batching up to 20 IDs (comma-separated) |
| `country` | string | No | "us" | Country code |
| `language` | string | No | - | Language code |
| `fields` | string | No | - | Field projection |

#### Example Request

```bash
curl 'https://api.openwebninja.com/jsearch/job-details?job_id=gcnkkB1_QjIlxbV9AAAAAA%3D%3D&country=us' \
  --header 'x-api-key: YOUR_API_KEY'
```

---

### 3. Estimated Salary

**GET** `/estimated-salary`

Get salary estimates for a job title in a specific location.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `job_title` | string | **Yes** | - | Job title |
| `location` | string | **Yes** | - | Location (city, state, country) |
| `location_type` | enum | No | "ANY" | `ANY`, `CITY`, `STATE`, `COUNTRY` |
| `years_of_experience` | enum | No | "ALL" | `ALL`, `LESS_THAN_ONE`, `ONE_TO_THREE`, `FOUR_TO_SIX`, `SEVEN_TO_NINE`, `TEN_TO_FOURTEEN`, `ABOVE_FIFTEEN` |
| `fields` | string | No | - | Field projection |

#### Example Request

```bash
curl 'https://api.openwebninja.com/jsearch/estimated-salary?job_title=CDL%20driver&location=Houston%20TX&location_type=CITY' \
  --header 'x-api-key: YOUR_API_KEY'
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `location` | string | Location |
| `job_title` | string | Job title |
| `min_salary` | number | Minimum total salary |
| `max_salary` | number | Maximum total salary |
| `median_salary` | number | Median total salary |
| `min_base_salary` | number | Minimum base salary |
| `max_base_salary` | number | Maximum base salary |
| `median_base_salary` | number | Median base salary |
| `min_additional_pay` | number | Minimum additional pay |
| `max_additional_pay` | number | Maximum additional pay |
| `median_additional_pay` | number | Median additional pay |
| `salary_period` | string | Period (YEAR, MONTH, HOUR, etc.) |
| `salary_currency` | string | Currency code |
| `salary_count` | integer | Number of data points |
| `publisher_name` | string | Data source |
| `confidence` | string | Confidence level |

---

### 4. Company Job Salary

**GET** `/company-job-salary`

Get salary estimates for a specific job title at a specific company.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `company` | string | **Yes** | - | Company name |
| `job_title` | string | **Yes** | - | Job title |
| `location` | string | No | - | Location |
| `location_type` | enum | No | "ANY" | `ANY`, `CITY`, `STATE`, `COUNTRY` |
| `years_of_experience` | enum | No | "ALL" | Experience level |

#### Example Request

```bash
curl 'https://api.openwebninja.com/jsearch/company-job-salary?company=Werner&job_title=CDL%20driver&location=TX' \
  --header 'x-api-key: YOUR_API_KEY'
```

---

## Pricing

| Request Type | Cost |
|--------------|------|
| 1 page of results | 1x |
| 2-10 pages of results | 2x |
| 11-20 pages of results | 3x |
| Job details (per job_id) | 1x |
| Salary estimate | 1x |

**Note:** Each job_id in a batch request counts as a separate request.

---

## Rate Limits

- Depends on subscription tier
- Free tier: ~50 requests
- Check RapidAPI/OpenWeb Ninja dashboard for current limits

---

## Example: CDL Driver Search for Opptek

```python
import requests

API_KEY = "your_api_key"
BASE_URL = "https://api.openwebninja.com/jsearch"

def search_cdl_jobs(location: str, num_pages: int = 5):
    """Search for CDL driver jobs in a location."""

    params = {
        "query": f"CDL driver jobs in {location}",
        "page": 1,
        "num_pages": num_pages,  # Up to 50 jobs per call
        "country": "us",
        "date_posted": "week",
        "job_requirements": "no_experience",  # Entry-level friendly
        "employment_types": "FULLTIME"
    }

    headers = {"x-api-key": API_KEY}

    response = requests.get(f"{BASE_URL}/search", params=params, headers=headers)
    response.raise_for_status()

    data = response.json()
    return data.get("data", [])

# Search Houston market
jobs = search_cdl_jobs("Houston TX", num_pages=5)
print(f"Found {len(jobs)} jobs")

for job in jobs[:5]:
    print(f"- {job['job_title']} at {job['employer_name']}")
    print(f"  Location: {job['job_location']}")
    print(f"  Apply: {job['job_apply_link']}")
```

---

## Comparison: JSearch vs Outscraper

| Feature | JSearch | Outscraper |
|---------|---------|------------|
| Max results per query | 200 (20 pages × 10) | 500 (50 pages × 10) |
| Pricing model | Per request | Per record |
| Async polling needed | No | Yes |
| Real-time results | Yes | Delayed (batch) |
| Cost per 100 jobs | ~$0.32-0.96 | ~$0.30 |

---

## Response Status Codes

| Status | Description |
|--------|-------------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 401 | Unauthorized (invalid API key) |
| 429 | Rate limit exceeded |
| 500 | Server error |

---

## Notes for Integration

1. **Query formatting**: Include both job title AND location in the `query` parameter for best results
2. **Pagination**: Use `num_pages` to get more results in a single call (more cost-effective than multiple calls)
3. **Date filtering**: Use `date_posted=week` or `date_posted=3days` for fresher jobs
4. **No experience filter**: `job_requirements=no_experience` is useful for entry-level CDL jobs
5. **Field projection**: Use `fields` parameter to reduce response size and improve performance

---

*Last updated: January 2026*
