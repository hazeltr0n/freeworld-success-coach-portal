# GovernmentJobs.com Scraper Integration

## Overview

Automated scraper for GovernmentJobs.com that runs **Monday/Wednesday/Friday at 2am Central** via GitHub Actions. Scrapes CDL jobs across all 10 FreeWorld markets and processes them through Pipeline v3.1.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Actions (M/W/F at 2am Central)                  │
│  .github/workflows/scheduled_governmentjobs.yml         │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  GovernmentJobs Adapter                                 │
│  governmentjobs_adapter.py                              │
│  GovernmentJobsPipelineIntegration class                │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Production Scraper                                     │
│  scrape_governmentjobs_production.py                    │
│  - 10 markets (Dallas, Houston, Trenton, etc.)          │
│  - JSON-LD structured data extraction                   │
│  - Playwright browser automation                        │
│  - Smart job link detection                             │
│  - Rate limiting (2s between requests)                  │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Pipeline v3.1 (8 Stages)                               │
│  1. Ingestion      → DataFrame from scraper             │
│  2. Normalization  → 100+ field schema                  │
│  3. Business Rules → Quality filtering                  │
│  4. Deduplication  → Hash-based dedup                   │
│  5. AI Classification → CDL + Pathway classifiers       │
│  6. Routing Logic  → Final job selection                │
│  7. Link Tracking  → Short.io URLs                      │
│  8. Data Storage   → Supabase upload                    │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Supabase Database                                      │
│  - jobs table (complete job data)                       │
│  - Analytics tracking                                   │
│  - Agent portal integration                             │
└─────────────────────────────────────────────────────────┘
```

## Files

### Core Components

1. **`scrape_governmentjobs_production.py`** - Production scraper
   - Covers 10 markets with configurable pagination
   - JSON-LD structured data extraction (Schema.org JobPosting)
   - Smart job link detection with extensive filtering
   - Authentication support to bypass bot detection
   - HTML preservation in descriptions

2. **`governmentjobs_adapter.py`** - Pipeline integration adapter
   - `GovernmentJobsPipelineIntegration` class
   - Main method: `run_governmentjobs_through_pipeline()`
   - Runs scraper and processes through all 8 pipeline stages
   - Returns job counts and DataFrame

3. **`.github/workflows/scheduled_governmentjobs.yml`** - GitHub Actions workflow
   - Scheduled: M/W/F at 2am Central (7am UTC)
   - Cron: `'0 7 * * 1,3,5'`
   - Manual trigger support for testing
   - 60-minute timeout

### Test/Development Files

4. **`scrape_governmentjobs_dallas.py`** - Dallas-only test scraper
   - Used for development and testing
   - Same extraction logic as production version
   - Useful for debugging without running full scrape

5. **`inspect_next_job_button.py`** - Research/investigation script
   - Explored navigation patterns on GovernmentJobs.com
   - Not used in production

## Markets Covered

The production scraper covers all 10 FreeWorld markets:

| Market | ZIP Code | Radius |
|--------|----------|--------|
| Dallas, TX | 75201 | 50 miles |
| Houston, TX | 77002 | 50 miles |
| Trenton, NJ | 08608 | 50 miles |
| Newark, NJ | 07102 | 50 miles |
| Las Vegas, NV | 89101 | 50 miles |
| San Francisco, CA (Bay Area) | 94102 | 50 miles |
| Stockton, CA | 95202 | 50 miles |
| Riverside, CA (Inland Empire) | 92501 | 50 miles |
| Phoenix, AZ | 85003 | 50 miles |
| Denver, CO | 80202 | 50 miles |

**Configuration**: 3 pages per market × 10 markets = ~30 pages total
**Expected Jobs**: ~200-400 quality CDL jobs per run

## Setup Instructions

### 1. GitHub Repository Secrets

Add the following secrets to your GitHub repository:
(`Settings` → `Secrets and variables` → `Actions` → `New repository secret`)

#### Required Secrets:
```bash
# GovernmentJobs.com credentials
GOVERNMENT_JOBS_EMAIL=placement@freeworld.org
GOVERNMENT_JOBS_PASSWORD=FreeWorld2024!

# OpenAI API
OPENAI_API_KEY=sk-...

# Supabase
SUPABASE_URL=https://yqbdltothngundojuebk.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Link tracking
SHORT_IO_API_KEY=sk_...
SHORT_DOMAIN=freeworldjobs.short.gy
```

### 2. Local Development Setup

For testing locally:

```bash
# 1. Create .env file with credentials
cat > .env << EOF
GOVERNMENT_JOBS_EMAIL=placement@freeworld.org
GOVERNMENT_JOBS_PASSWORD=FreeWorld2024!
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://yqbdltothngundojuebk.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SHORT_IO_API_KEY=sk_...
SHORT_DOMAIN=freeworldjobs.short.gy
EOF

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Playwright browsers
playwright install chromium

# 4. Test with Dallas scraper (quick test)
python3 scrape_governmentjobs_dallas.py

# 5. Test full pipeline integration (production test)
python3 -c "from governmentjobs_adapter import GovernmentJobsPipelineIntegration; integration = GovernmentJobsPipelineIntegration(); result = integration.run_governmentjobs_through_pipeline(keywords=['CDL'], max_pages_per_search=1); print(f'✅ Test complete: {result[\"job_count\"]} jobs, {result[\"quality_job_count\"]} quality')"
```

## Testing the Workflow

### Manual Trigger (Recommended for First Test)

1. Go to GitHub repository → `Actions` tab
2. Select `Scheduled GovernmentJobs Scraper` workflow
3. Click `Run workflow` dropdown → `Run workflow` button
4. Wait for completion (~15-30 minutes)
5. Check workflow logs for results
6. Verify jobs in Supabase database

### Monitor Automated Runs

After setup, workflow runs automatically:
- **Monday** at 2am Central
- **Wednesday** at 2am Central
- **Friday** at 2am Central

**Check Status**:
- GitHub Actions tab shows recent runs
- Workflow creates artifacts with results summary
- Jobs appear in Supabase `jobs` table with `id.source = 'governmentjobs'`
- Coach portal shows new jobs with GovernmentJobs attribution

## Expected Performance

### Timing
- **Scraping**: ~10-15 minutes (10 markets × 3 pages each)
- **Pipeline Processing**: ~5-10 minutes (depends on job count)
- **Total Runtime**: ~15-30 minutes per execution

### Output Metrics
- **Total Jobs Scraped**: 200-500 jobs
- **After Deduplication**: 150-400 unique jobs (15-25% duplicates removed)
- **Quality Jobs (good/so-so)**: 50-150 jobs
- **Uploaded to Supabase**: 50-150 jobs (quality only)

### Cost Optimization
- **OpenAI API**: ~$0.05-0.15 per run (AI classification)
- **Short.io**: ~50-150 links per run (within free tier limits)
- **Outscraper**: $0 (not used by GovernmentJobs scraper)

## Technical Details

### Data Extraction Method

GovernmentJobs.com embeds structured data using JSON-LD (Schema.org JobPosting format):

```html
<script type="application/ld+json">
{
  "@type": "JobPosting",
  "title": "CDL Truck Driver",
  "hiringOrganization": {
    "name": "City of Dallas",
    "sameAs": "https://dallascityhall.com"
  },
  "jobLocation": {
    "address": {
      "addressLocality": "Dallas",
      "addressRegion": "TX",
      "postalCode": "75201"
    }
  },
  "baseSalary": {
    "value": {
      "minValue": 45000,
      "maxValue": 65000
    }
  },
  "description": "<p>Full job description HTML...</p>",
  "datePosted": "2025-10-15"
}
</script>
```

**Benefits**:
- ✅ Clean, structured data (no DOM scraping)
- ✅ 100% field coverage
- ✅ Reliable extraction
- ✅ Fast performance

### Job Link Detection Strategy

Smart filtering to avoid clicking navigation/settings links:

```python
# Must be actual job URL
is_job_url = (
    '/jobs/' in href and
    any(char.isdigit() for char in href) and
    'category' not in href.lower()
)

# Skip navigation patterns
skip_patterns = [
    'privacy', 'login', 'sign in', 'account', 'settings',
    'help', 'support', 'terms', 'accessibility', etc.
]

# Only reasonable title lengths
has_good_title = 10 < len(text) < 150
```

**Result**: Only actual job postings detected, no navigation links

### Authentication

GovernmentJobs scraper includes login capability to bypass bot detection:

```python
async def login_to_governmentjobs(page, email: str, password: str) -> bool:
    """Log in to GovernmentJobs.com"""
    # 1. Navigate to login page
    # 2. Fill email and password
    # 3. Click sign in
    # 4. Verify login success
```

**Note**: Currently not used in production workflow (scraper works without auth), but available if needed.

## Troubleshooting

### Common Issues

#### 1. No Jobs Found
```
⚠️  No jobs found from GovernmentJobs scraper
```
**Causes**:
- Site structure changed (rare)
- Bot detection triggered (rare with headless Playwright)
- Search returned no results (unlikely for CDL)

**Fix**:
- Check GovernmentJobs.com manually for CDL jobs
- Review workflow logs for error messages
- Test Dallas scraper locally to isolate issue

#### 2. Playwright Browser Installation Failed
```
Error: Executable doesn't exist at /home/runner/.cache/ms-playwright/chromium-1105/chrome-linux/chrome
```
**Fix**:
- Ensure `playwright install chromium` step runs successfully
- Check `playwright install-deps` completed
- May need to update Playwright version in requirements.txt

#### 3. API Rate Limit (OpenAI)
```
Error: Rate limit exceeded for gpt-4o-mini
```
**Fix**:
- Wait 1 minute and retry
- Reduce `max_pages_per_search` to get fewer jobs
- OpenAI usually resets limits quickly

#### 4. Timeout After 60 Minutes
```
Error: The operation was canceled.
```
**Causes**:
- Scraping too slow (network issues)
- AI classification taking too long (API throttling)
- Pipeline processing stuck

**Fix**:
- Check workflow logs for where it got stuck
- Reduce `max_pages_per_search` from 3 to 2
- Check Supabase database connection
- Verify OpenAI API key is valid

## Monitoring & Maintenance

### Weekly Review
- Check GitHub Actions for successful runs (3 per week)
- Verify job counts in Supabase (`id.source = 'governmentjobs'`)
- Monitor OpenAI API costs
- Review quality job percentages (should be ~30-40%)

### Monthly Review
- Check for site structure changes on GovernmentJobs.com
- Update markets configuration if needed
- Review AI classification accuracy
- Optimize `max_pages_per_search` based on results

### Alerts to Watch For
- ❌ Multiple failed workflow runs in a row
- ❌ Sudden drop in job count (e.g., <50 total jobs)
- ❌ Low quality percentage (e.g., <10% good/so-so)
- ❌ High deduplication rate (e.g., >50% duplicates)

## Integration with Main App

GovernmentJobs data appears throughout the system:

### 1. Coach Portal (`app.py`)
- Jobs show up in search results with `source.platform = 'GovernmentJobs'`
- Tracked URLs generated automatically
- Analytics dashboard includes GovernmentJobs metrics

### 2. Agent Portal (`agent_portal_clean.py`)
- Free Agents see GovernmentJobs jobs in their personalized feeds
- Fair chance filter works with GovernmentJobs jobs
- Click tracking through Short.io

### 3. Analytics Dashboard
- Company performance includes government employers
- Geographic coverage maps show government job locations
- Click tracking shows Free Agent engagement

### 4. Database Schema
All jobs stored with consistent schema:
```python
{
    'id.source': 'governmentjobs',
    'id.source_row': 0,
    'id.job': 'governmentjobs_0_20251020_123045',
    'source.platform': 'GovernmentJobs',
    'source.url': 'https://www.governmentjobs.com/jobs/...',
    'source.title': 'CDL Truck Driver',
    'source.company': 'City of Dallas',
    'source.location': 'Dallas, TX',
    'source.salary': '$45,000 - $65,000 Annually',
    'source.description': '<p>HTML description...</p>',
    'ai.match': 'good',
    'ai.summary': 'Local CDL position with city government...',
    'meta.tracked_url': 'https://freeworldjobs.short.gy/abc123',
    # ... 100+ more fields
}
```

## Future Enhancements

### Potential Improvements
1. **Keyword Expansion**: Add more search terms beyond "CDL"
   - "Commercial Driver License"
   - "Class A Driver"
   - "Truck Driver"
   - "Fleet Driver"

2. **Market Expansion**: Add more markets as FreeWorld grows
   - Easy to add: just update `MARKETS` dict in production scraper

3. **Pagination Optimization**: Dynamically adjust pages based on results
   - If market has <20 jobs on page 1, skip pages 2-3
   - If market has >50 jobs, scrape page 4

4. **Authentication Toggle**: Enable login if bot detection increases
   - Already implemented, just uncomment in workflow

5. **Incremental Scraping**: Track last scraped date per market
   - Only scrape jobs posted since last run
   - Reduces redundant work

## Support

For issues or questions:
1. Check workflow logs in GitHub Actions
2. Review Supabase database for job data
3. Test locally with Dallas scraper
4. Check this README for troubleshooting steps

---

**Last Updated**: October 2025
**Status**: Production Ready ✅
**Schedule**: M/W/F at 2am Central
**Maintainer**: FreeWorld Development Team
