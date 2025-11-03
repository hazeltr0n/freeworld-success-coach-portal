# 🚨 SCHEDULED SCRAPING SYSTEM - COMPLETE BREAKDOWN & ISSUES

**Date:** October 30, 2025
**Status:** FUCKED - Multiple Critical Issues

---

## 📊 CURRENT SYSTEM OVERVIEW

You have **6 GitHub Actions workflows** and **2 Python scripts** running scheduled scrapes:

### Workflows:

1. **`scheduled_config_scrapes.yml`** - Mon/Wed/Fri 2am Central (7am UTC)
   - Runs: `run_config_scrapes.py` → `scheduled_scrapes_config.json`
   - Indeed (4 searches × ALL markets) + DriverPulse + Google

2. **`scheduled_google_scrapes.yml`** - Tue/Thu 2am Central (7am UTC)
   - Runs: `run_config_scrapes.py` (NO CONFIG FILE SPECIFIED - DEFAULTS TO `scheduled_scrapes_config.json`)
   - **PROBLEM**: Uses default config = runs ALL scrapes not just Google

3. **`poll_google_scrapes.yml`** - Tue/Thu every 1.5hrs for 12hrs (8:30am-7pm UTC)
   - Runs: `poll_google_results.py`
   - Checks for completed Google tasks and processes them

4. **`scheduled_batch_scraper.yml`** - Every 6 hours
   - Runs: `run_scheduled_batches.py`
   - Processes async_job_queue batches

5. **`refresh_driverpulse_auth.yml`** - Manual only (cron commented out)

6. **`run_driverpulse_job.yml`** - Workflow dispatch only (async job execution)

---

## 🔥 CRITICAL ISSUES IDENTIFIED

### Issue #1: `scheduled_google_scrapes.yml` Runs EVERYTHING Not Just Google

**File:** `.github/workflows/scheduled_google_scrapes.yml`

**The Problem:**
```yaml
- name: Run Google scrapes only
  run: |
    python run_config_scrapes.py
```

**What's Wrong:**
- No config file specified → defaults to `scheduled_scrapes_config.json`
- That config has Indeed + DriverPulse + Google
- **You're running ALL scrapes on Tue/Thu not just Google**

**Fix:** Add specific Google-only config:
```yaml
run: |
  python run_config_scrapes.py google_only_config.json
```

---

### Issue #2: Indeed Scrapes Loop Through EVERY MARKET Not Your Designated Markets

**File:** `run_config_scrapes.py` lines 14-94

**The Problem:**
```python
def run_indeed_scrapes(scrapes: List[Dict]) -> Dict:
    # Build search params for all markets
    from market_mapper import MarketMapper

    market_mapper = MarketMapper()
    markets = market_mapper.get_all_markets()  # <-- GETS ALL MARKETS

    # Run for each market
    for market_name in markets:
        cities = market_mapper.get_cities_in_market(market_name)
        location = cities[0]  # Use first city

        # Submit Indeed search for this market
        ...
```

**What's Wrong:**
- `get_all_markets()` returns EVERY market in the system
- Your config just says "CDL Driver" with limit 250
- **The script ignores your market designation and scrapes ALL markets**

**Your Config:**
```json
"indeed_scrapes": [
  {
    "search_terms": "CDL Driver",
    "limit": 250,
    "no_experience": true
  }
]
```

**What Actually Happens:**
- CDL Driver × Atlanta (250 jobs)
- CDL Driver × Bay Area (250 jobs)
- CDL Driver × Dallas (250 jobs)
- CDL Driver × Denver (250 jobs)
- CDL Driver × Des Moines (250 jobs)
- CDL Driver × El Paso (250 jobs)
- CDL Driver × Houston (250 jobs)
- CDL Driver × Inland Empire (250 jobs)
- CDL Driver × Las Vegas (250 jobs)
- CDL Driver × Newark (250 jobs)
- CDL Driver × Phoenix (250 jobs)
- CDL Driver × Stockton (250 jobs)
- CDL Driver × Trenton (250 jobs)

**Total:** 13 markets × 4 search terms × 250 jobs = **13,000+ job searches PER RUN**

---

### Issue #3: Google Scrapes Submitted But Not Downloaded

**The Flow:**
1. **Tue/Thu 2am** - `scheduled_google_scrapes.yml` runs
2. Calls Outscraper API → gets `task_id`
3. Saves to `async_job_queue` with `status='submitted'`
4. **Tue/Thu 3:30am-2pm** - `poll_google_scrapes.yml` runs every 1.5hrs
5. Checks Outscraper for completed tasks
6. Downloads results → processes through pipeline → uploads to Supabase

**The Problems:**

**A) Google scraper runs on wrong day:**
- You said "google still isn't working" when you ran it Wednesday morning
- The poller runs **Tue/Thu only** (cron: `* * 2,4`)
- If the scraper ran Wednesday, NO POLLER IS RUNNING to fetch results

**B) 12-hour polling window might not be enough:**
- Outscraper can take 6+ hours for 237-query batches
- Polling starts 1.5hrs after submission (3:30am)
- Polling ends at 2pm (12 hours after submission)
- If Outscraper takes 13+ hours, results never get fetched

**C) Google scraper uses wrong config:**
- `scheduled_google_scrapes.yml` calls `run_config_scrapes.py` with NO args
- Runs the FULL config (Indeed + DriverPulse + Google)
- You get 3 scrape types when you expected 1

---

### Issue #4: Wrong Days - Schedule Mismatch

**Config Scrapes:** Mon/Wed/Fri (line 6 in `scheduled_config_scrapes.yml`)
```yaml
- cron: '0 7 * * 1,3,5'  # Mon/Wed/Fri at 2am Central
```

**Google Scrapes:** Tue/Thu (line 6 in `scheduled_google_scrapes.yml`)
```yaml
- cron: '0 7 * * 2,4'  # Tue/Thu at 2am Central
```

**Google Poller:** Tue/Thu (lines 7-21 in `poll_google_scrapes.yml`)
```yaml
# All cron lines have: * * 2,4  (Tue/Thu)
```

**The Problem:**
- You have 2 separate Google workflows
- One on Tue/Thu (scraper)
- One on Mon/Wed/Fri (config scrapes which ALSO runs Google)
- **Google scrapes run 5 days/week not 2**
- **Poller only runs Tue/Thu - misses Mon/Wed/Fri scrapes**

---

### Issue #5: Google Query Mapping Has Random Markets

**File:** `google_query_to_market.csv` - 237 queries

**Markets Found:**
- Bay Area
- Dallas
- Denver
- Houston
- Inland Empire
- Las Vegas
- **Newark**
- **Phoenix**
- **Stockton**
- **Trenton**

**The Problem:**
- You have 10+ markets in this file
- 237 city queries spread across these markets
- Google scrapes hit ALL these markets on EVERY run
- **You're scraping markets you never designated**

**Example Queries for Trenton (a random market):**
```
CDL Driver Trenton NJ
CDL Driver Ewing Township NJ
CDL Driver Hamilton NJ
CDL Driver Princeton NJ
CDL Driver Bordentown NJ
... (19 more cities)
```

---

## 🎯 ROOT CAUSES

### 1. **No Market Filtering in Indeed Config**
- Config doesn't specify which markets to scrape
- Script uses `get_all_markets()` → scrapes everything

### 2. **Duplicate Google Workflows**
- `scheduled_google_scrapes.yml` (Tue/Thu)
- `scheduled_config_scrapes.yml` (Mon/Wed/Fri) also runs Google
- No config file specified in Google-only workflow

### 3. **Poller Schedule Mismatch**
- Poller only runs Tue/Thu
- Config scrapes run Mon/Wed/Fri
- Mon/Wed/Fri Google scrapes never get polled

### 4. **Google Query CSV Has Too Many Markets**
- 237 queries across 10+ markets
- Includes markets you didn't request (Trenton, Newark, Stockton, etc.)

### 5. **No Indeed Results Visible**
- Indeed searches ARE running (13 markets × 4 terms × 250 jobs)
- But you can't see them because they're buried in thousands of jobs
- OR Indeed API is failing/rate limiting from too many requests

---

## ✅ FIXES REQUIRED

### Fix #1: Create Google-Only Config

**Create:** `google_only_config.json`
```json
{
  "google_scrapes": [
    {
      "csv_mapping": "google_query_to_market.csv",
      "limit_per_query": 50
    }
  ]
}
```

**Update:** `scheduled_google_scrapes.yml` line 38
```yaml
run: |
  python run_config_scrapes.py google_only_config.json
```

---

### Fix #2: Add Market Filtering to Indeed Config

**Option A:** Modify config to specify markets:
```json
{
  "indeed_scrapes": [
    {
      "search_terms": "CDL Driver",
      "limit": 250,
      "no_experience": true,
      "markets": ["Houston", "Dallas", "Atlanta"]  // <-- ADD THIS
    }
  ]
}
```

**Option B:** Modify `run_config_scrapes.py` to accept market list:
```python
def run_indeed_scrapes(scrapes: List[Dict]) -> Dict:
    for scrape in scrapes:
        # Check if specific markets are specified
        if 'markets' in scrape:
            markets = scrape['markets']
        else:
            # Default to all markets
            market_mapper = MarketMapper()
            markets = market_mapper.get_all_markets()
```

---

### Fix #3: Align Google Poller Schedule

**Update:** `poll_google_scrapes.yml` cron to match ALL scrape days

**Current:** Runs Tue/Thu only (lines 7-21)
```yaml
- cron: '30 8 * * 2,4'  # Tue/Thu
```

**Change to:** Mon/Wed/Fri/Tue/Thu (all 5 days)
```yaml
- cron: '30 8 * * 1,2,3,4,5'  # Mon-Fri
```

OR simplify to daily:
```yaml
- cron: '30 8 * * *'  # Every day
```

---

### Fix #4: Clean Up Google Query CSV

**Current:** 237 queries across 10+ markets

**Options:**

**A) Reduce to your core markets only:**
- Keep only: Houston, Dallas, Atlanta, Denver, Bay Area
- Remove: Trenton, Newark, Stockton, Las Vegas, Phoenix, etc.

**B) Create separate CSVs per market tier:**
- `google_queries_tier1.csv` - Houston, Dallas, Atlanta
- `google_queries_tier2.csv` - Denver, Bay Area, Inland Empire
- Update config to use specific CSV

**C) Reduce queries per market:**
- Instead of 19 cities per market, pick top 5-10 cities

---

### Fix #5: Remove Duplicate Google Workflow

**Option A:** Delete `scheduled_google_scrapes.yml` entirely
- Keep Google in `scheduled_config_scrapes.yml` (Mon/Wed/Fri)
- Update poller to run Mon/Wed/Fri only

**Option B:** Remove Google from `scheduled_scrapes_config.json`
- Keep `scheduled_google_scrapes.yml` (Tue/Thu)
- Keep poller on Tue/Thu only

**Recommended:** Option B (separate Google workflow)
- Cleaner separation of concerns
- Easier to debug
- Less API usage

---

## 📋 IMMEDIATE ACTION ITEMS

1. **STOP the bleeding:**
   - Disable `scheduled_google_scrapes.yml` (comment out cron)
   - Keep only `scheduled_config_scrapes.yml`

2. **Fix Indeed market explosion:**
   - Add market filter to config OR modify script
   - Test with 1 market first

3. **Fix Google CSV:**
   - Reduce to core markets only
   - Test with small batch (10-20 queries)

4. **Align poller schedule:**
   - Make poller run same days as scraper
   - OR extend polling window to 24+ hours

5. **Test each component separately:**
   - Run Indeed config with 1 market manually
   - Run Google scrape with 10 queries manually
   - Verify poller fetches results

---

## 🎯 RECOMMENDED NEW ARCHITECTURE

### Workflow 1: Core Scrapes (Mon/Wed/Fri)
```yaml
# scheduled_config_scrapes.yml
- Indeed: 3 markets × 4 searches × 100 jobs = 1,200 jobs
- DriverPulse: 1 search across all markets = ~500 jobs
- Total: ~1,700 jobs per run
```

### Workflow 2: Google Scrapes (Tue/Thu)
```yaml
# scheduled_google_scrapes.yml
- Google: 3 markets × 20 queries × 50 jobs = 3,000 jobs
- Submit to Outscraper at 2am
- Polling: 3:30am - 2pm (8 polls over 12 hours)
```

### Workflow 3: Batch Processor (Every 6 hours)
```yaml
# scheduled_batch_scraper.yml
- Check async_job_queue for pending jobs
- Execute via GitHub Actions workflow dispatch
- Handles DriverPulse auth + scraping
```

This gives you:
- **Mon/Wed/Fri:** ~1,700 jobs from Indeed + DriverPulse
- **Tue/Thu:** ~3,000 jobs from Google
- **Weekly Total:** ~8,100 jobs (vs current 65,000+)

---

**END OF ANALYSIS**
