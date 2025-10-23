# Testing Guide: Simple Config-Based Scheduled Scrapes

## Overview

This guide walks through testing the complete Google scrape automation system end-to-end.

## System Architecture

```
Main Scraper (Mon/Wed/Fri 2am)          Poller (Mon/Wed/Fri 2:30am-5am, every 30 mins)
         │                                            │
         ▼                                            ▼
run_config_scrapes.py                    poll_google_results.py
         │                                            │
         │  Reads CSV                                 │  Fetches results
         │  Submits to Outscraper                     │  Processes through pipeline
         │  Saves to async_job_queue                  │  Uploads to Supabase
         │                                            │
         └──────────────► async_job_queue ◄──────────┘
                          (status: submitted → completed)
```

## Test Configuration Files

### Small Test Batch (12 queries)
- **Config**: `scheduled_scrapes_config_test.json`
- **CSV**: `google_query_to_market_test.csv`
- **Purpose**: Fast validation of complete workflow

### Production Batch (237 queries)
- **Config**: `scheduled_scrapes_config.json`
- **CSV**: `google_query_to_market.csv`
- **Purpose**: Full production scraping

## Step-by-Step Testing

### Step 1: Test Google Scrape Submission

Run the test config to submit a small Google batch:

```bash
python run_config_scrapes.py scheduled_scrapes_config_test.json
```

**Expected Output**:
```
================================================================================
🤖 CONFIG-BASED SCHEDULED SCRAPER
⏰ 2025-10-21 XX:XX:XX UTC
================================================================================

📄 Using config file: scheduled_scrapes_config_test.json
📋 Loaded config:
   Indeed scrapes: 0
   DriverPulse scrapes: 0
   Google scrapes: 1

================================================================================
🌐 GOOGLE SCRAPES - 1 configured
================================================================================

🔍 Google Scrape 1/1

   📋 Loaded 12 city queries from google_query_to_market_test.csv
   🎯 Mapped to 6 markets

   🚀 Submitting 12 queries to Outscraper...
   ✅ Task created: YbT63A...
   💾 Saved to async_job_queue (ID: 123)
   ⏳ Poller will fetch results when ready

================================================================================
✅ SCRAPE RUN COMPLETE
================================================================================

GOOGLE:
   Scrapes run: 1
   ✅ Task YbT63A...: 12 queries (6 markets) - submitted to Outscraper

================================================================================
```

**Validation Checklist**:
- [ ] Task ID returned from Outscraper
- [ ] Job record created in async_job_queue
- [ ] Status is 'submitted'
- [ ] search_params includes csv_mapping and query counts

### Step 2: Verify Database Record

Check Supabase async_job_queue table:

```sql
SELECT
    id,
    job_type,
    status,
    request_id,
    search_params,
    created_at
FROM async_job_queue
WHERE job_type = 'google_jobs'
ORDER BY created_at DESC
LIMIT 1;
```

**Expected Result**:
```json
{
  "id": "...",
  "job_type": "google_jobs",
  "status": "submitted",
  "request_id": "YbT63A...",
  "search_params": {
    "csv_mapping": "google_query_to_market_test.csv",
    "limit_per_query": 10,
    "queries_count": 12,
    "markets_count": 6
  },
  "coach_username": "scheduled_config",
  "created_at": "2025-10-21T..."
}
```

### Step 3: Wait for Outscraper Completion

Google scrapes typically take 30-120 minutes. You can manually check status:

```bash
# Get the task_id from Step 1 output
export TASK_ID="YbT63A..."

curl -H "X-API-KEY: $OUTSCRAPER_API_KEY" \
  "https://api.outscraper.cloud/requests/$TASK_ID"
```

**Status Values**:
- `Pending` - Queued but not started
- `In Progress` - Currently running
- `Success` - Complete and ready to fetch
- `Failed` - Error occurred

### Step 4: Test Poller (Manual)

Once Outscraper status is 'Success', run the poller manually:

```bash
python poll_google_results.py
```

**Expected Output**:
```
================================================================================
🔍 GOOGLE RESULTS POLLER
⏰ 2025-10-21 XX:XX:XX UTC
================================================================================

📋 Found 1 pending Google task(s)

🔍 Checking task YbT63A... (Job ID: 123)
   ✅ Task complete! Processing results...
   📋 Loaded 12 query→market mappings
   📊 Raw results: 12 job batches from Outscraper
   📦 Extracted 120 individual jobs
   🔄 Transforming to canonical format...
   ✅ Transformed 120 jobs
   🧠 Processing through pipeline...
   🤖 Running AI classification...
   💾 Uploading to Supabase...
   ✅ Complete: 120 jobs, 85 quality, 85 uploaded
   💾 Updated job 123 status to 'completed'

================================================================================
✅ Poller complete: 1/1 tasks processed
================================================================================
```

**Validation Checklist**:
- [ ] Poller finds pending task
- [ ] Fetches results from Outscraper
- [ ] Loads CSV mapping correctly
- [ ] Extracts jobs from response
- [ ] Maps jobs to markets
- [ ] Transforms to canonical format
- [ ] Runs through pipeline stages 2-8
- [ ] Uploads to Supabase
- [ ] Updates async_job_queue status to 'completed'

### Step 5: Verify Final Database State

Check async_job_queue:

```sql
SELECT
    id,
    status,
    result_count,
    quality_job_count,
    completed_at
FROM async_job_queue
WHERE id = 123;  -- Use actual job ID
```

**Expected Result**:
```json
{
  "id": 123,
  "status": "completed",
  "result_count": 120,
  "quality_job_count": 85,
  "completed_at": "2025-10-21T..."
}
```

Check jobs table:

```sql
SELECT
    COUNT(*) as total_jobs,
    COUNT(*) FILTER (WHERE "ai.match" IN ('good', 'so-so')) as quality_jobs,
    "meta.coach"
FROM jobs
WHERE "meta.run_id" LIKE 'google_poll_%'
  AND "meta.scraped_at" >= NOW() - INTERVAL '1 hour'
GROUP BY "meta.coach";
```

**Expected Result**:
```
total_jobs  | quality_jobs | meta.coach
------------|--------------|------------------
120         | 85           | scheduled_config
```

### Step 6: Test Automated Workflow (Optional)

To test the complete automated workflow via GitHub Actions:

1. **Push all files to GitHub** (when ready to commit)

2. **Manually trigger main scraper**:
   - Go to Actions → "Scheduled Config-Based Scrapes"
   - Click "Run workflow"
   - Wait for completion (~5 mins)

3. **Wait 30+ minutes** for Outscraper to complete

4. **Manually trigger poller**:
   - Go to Actions → "Poll Google Scrape Results"
   - Click "Run workflow"
   - Wait for completion (~2-5 mins)

5. **Verify results** in Supabase

## Troubleshooting

### Poller finds no pending tasks

**Symptoms**: "📭 No pending Google tasks found"

**Causes**:
- Status already changed to 'completed' or 'failed'
- Job_type not 'google_jobs'
- Task was processed already

**Fix**: Check async_job_queue table manually

### Outscraper task fails

**Symptoms**: Outscraper API returns status 'Failed'

**Causes**:
- Invalid queries
- API quota exceeded
- Invalid API key

**Fix**: Check Outscraper dashboard and API limits

### CSV mapping fails

**Symptoms**: "❌ Error processing results: No such file or directory"

**Causes**:
- CSV file path incorrect in config
- CSV file not committed to repo (GitHub Actions)

**Fix**: Verify CSV exists and path matches exactly

### Pipeline processing fails

**Symptoms**: Error during transform or AI classification

**Causes**:
- Invalid Outscraper response format
- OpenAI API issues
- Supabase connection problems

**Fix**: Check full error traceback, verify all env vars set

### No jobs uploaded to Supabase

**Symptoms**: result_count = 0 despite successful processing

**Causes**:
- All jobs filtered out by business rules
- Deduplication removed all jobs
- Stage 8 upload failed silently

**Fix**: Check pipeline logs for filter reasons and upload errors

## Production Deployment

Once testing succeeds:

1. **Commit all files**:
```bash
git add scheduled_scrapes_config.json
git add run_config_scrapes.py
git add poll_google_results.py
git add google_query_to_market.csv
git add .github/workflows/scheduled_config_scrapes.yml
git add .github/workflows/poll_google_scrapes.yml
git add SCHEDULED_SCRAPES_README.md
git add TESTING_SCHEDULED_SCRAPES.md

git commit -m "Add simple config-based scheduled scrapes with Google polling"
git push
```

2. **Verify GitHub Actions secrets** are set:
   - OUTSCRAPER_API_KEY
   - SUPABASE_URL
   - SUPABASE_ANON_KEY
   - OPENAI_API_KEY
   - SHORTIO_API_KEY
   - SHORTIO_DOMAIN

3. **Enable workflows**:
   - GitHub → Actions → Enable workflows if disabled
   - Verify cron schedules are active

4. **Monitor first automated run**:
   - Main scraper: Next Mon/Wed/Fri at 2am Central
   - Poller: 30 mins later at 2:30am, then every 30 mins until 5am

## Expected Performance

### Small Test Batch (12 queries, 10 jobs each = ~120 jobs)
- **Submission**: < 5 seconds
- **Outscraper Processing**: 5-15 minutes
- **Polling + Pipeline**: 60-90 seconds
- **Total End-to-End**: ~10-20 minutes

### Production Batch (237 queries, 50 jobs each = ~11,850 jobs)
- **Submission**: < 10 seconds
- **Outscraper Processing**: 60-120 minutes
- **Polling + Pipeline**: 5-10 minutes
- **Total End-to-End**: ~70-130 minutes

---

**Last Updated**: October 21, 2025
