# Simple Config-Based Scheduled Scrapes

## What This Does

Runs the same job scrapes **every Monday, Wednesday, and Friday at 2am Central Time** via GitHub Actions.

**No database tracking. No UI. No complexity. Just works.**

## Configuration

Edit `scheduled_scrapes_config.json` to change what gets scraped:

```json
{
  "indeed_scrapes": [
    {
      "search_terms": "CDL Driver",
      "limit": 250,
      "no_experience": true
    }
  ],
  "driverpulse_scrapes": [
    {
      "search_terms": "CDL",
      "filter_mode": "all_markets"
    }
  ],
  "google_scrapes": []
}
```

## Current Setup

### Indeed Scrapes (4 search terms × 9 markets = 36 scrapes)

**Search Terms:**
- CDL Driver
- Class A Driver
- Class B Driver
- Local CDL Home Daily

**Markets:**
- Dallas, TX
- Houston, TX
- Trenton, NJ
- Newark, NJ
- Bay Area, CA
- Stockton, CA
- Inland Empire, CA
- Denver, CO
- Phoenix, AZ

**Settings:**
- 250 job limit per search
- No experience filter: enabled
- Auto-uploads to Supabase
- Auto-generates Short.io tracked URLs

### DriverPulse Scrapes (1 scrape)

**Search Terms:**
- CDL

**Markets:**
- All markets nationwide

### Google Scrapes (1 async task = 237 city queries → 10 markets)

**Query Mapping:**
- Uses `google_query_to_market.csv` to map 237 city queries to 10 markets
- Markets: Trenton, Bay Area, Las Vegas, Houston, Inland Empire, Phoenix, Denver, Stockton, Newark, Dallas

**Settings:**
- 50 jobs per query (237 queries × 50 = ~11,850 jobs max)
- Async submission to Outscraper
- Results processed separately (see "Google Results Processing" below)

**Note**: Google scrapes are submitted to Outscraper as an async task. The task runs in the background and results must be fetched separately.

## Schedule

Runs **Mon/Wed/Fri at 2am Central Time (7am UTC)** via GitHub Actions workflow: `.github/workflows/scheduled_config_scrapes.yml`

## Manual Testing

Run locally:
```bash
python run_config_scrapes.py
```

Run via GitHub Actions:
1. Go to Actions tab in GitHub
2. Click "Scheduled Config-Based Scrapes"
3. Click "Run workflow"

## How It Works

1. GitHub Actions triggers on schedule (Mon/Wed/Fri 2am Central)
2. Refreshes DriverPulse authentication
3. Reads `scheduled_scrapes_config.json`
4. Runs all Indeed scrapes (36 total: 4 terms × 9 markets)
5. Runs all DriverPulse scrapes (1 total: all markets)
6. Each scrape:
   - Fetches jobs from source
   - Runs through pipeline (normalization, dedup, AI classification)
   - Generates Short.io tracked URLs
   - Uploads to Supabase
7. Prints summary of results

## Output

All jobs are uploaded directly to Supabase `jobs` table with:
- Full job details
- AI classifications (good/so-so/bad)
- Short.io tracked URLs
- Coach attribution: `scheduled_config`

## Troubleshooting

### Check if workflow ran
- GitHub → Actions tab → "Scheduled Config-Based Scrapes"
- Look for green checkmarks (success) or red X's (failure)

### Check what was scraped
- Look at Supabase `jobs` table
- Filter by `coach_username = 'scheduled_config'`
- Filter by `created_at` for today's date

### Manually trigger a test run
- GitHub → Actions → "Scheduled Config-Based Scrapes" → Run workflow
- This runs immediately (doesn't wait for schedule)

## Modifying the Config

1. Edit `scheduled_scrapes_config.json`
2. Commit and push changes
3. Next scheduled run (or manual trigger) will use new config

**Examples:**

Add a new Indeed search term:
```json
{
  "search_terms": "Delivery Driver",
  "limit": 250,
  "no_experience": true
}
```

Change DriverPulse search:
```json
{
  "search_terms": "Truck Driver Entry Level",
  "filter_mode": "all_markets"
}
```

## Files

- `scheduled_scrapes_config.json` - What to scrape
- `run_config_scrapes.py` - Script that runs the scrapes
- `.github/workflows/scheduled_config_scrapes.yml` - GitHub Actions workflow (schedule)

---

**Last Updated:** October 21, 2025
