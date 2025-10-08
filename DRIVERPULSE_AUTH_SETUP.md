# DriverPulse Automated Authentication Setup

## Overview
This system uses **GitHub Actions** to automatically refresh DriverPulse authentication RIGHT BEFORE each scrape. This solves the 5-minute auth timeout problem by getting fresh auth on-demand.

## Architecture

### For Manual "Run Now" Batches
```
User clicks "Run Now" in Streamlit
  → Streamlit triggers GitHub Actions workflow via API
  → GitHub Actions runs Playwright + Gmail 2FA (fresh auth)
  → Stores cookies in Supabase system_config table
  → Streamlit polls for fresh auth (< 1 min old)
  → Streamlit runs the scrape with fresh cookies
```

### For Scheduled Batches
```
GitHub Actions (every 6 hours)
  → Step 1: Refresh auth (Playwright + Gmail 2FA)
  → Step 2: Run scheduled batches (scrapes all due jobs)
  → All in one workflow - no timeout issues!
```

## Setup Instructions

### 1. Add GitHub Secrets

Go to your GitHub repo → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

#### DriverPulse Credentials
- `DRIVER_PULSE_EMAIL` - Your DriverPulse login email
- `DRIVER_PULSE_FIRST_NAME` - First name for login form
- `DRIVER_PULSE_LAST_NAME` - Last name for login form
- `DRIVER_PULSE_PHONE` - Phone number for login form

#### Gmail 2FA Credentials
- `DRIVER_PULSE_GMAIL_CREDENTIALS` - Contents of your `gmail_credentials.json` file
- `DRIVER_PULSE_GMAIL_TOKEN` - Contents of your `gmail_token.json` file

#### Supabase Credentials
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Your Supabase anon/public key

#### API Keys (for scheduled scraping)
- `OPENAI_API_KEY` - For AI job classification
- `OUTSCRAPER_API_KEY` - For job scraping
- `SHORTIO_API_KEY` - For link tracking
- `SHORTIO_DOMAIN` - Your Short.io domain

#### GitHub Token (for triggering workflows from Streamlit)
- `GITHUB_TOKEN` - Personal Access Token with `repo` and `workflow` permissions
  - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  - Generate new token with `repo` and `workflow` scopes
  - Copy token and add as secret

### 2. How to Get Gmail Credentials

If you don't have `gmail_credentials.json` and `gmail_token.json`:

1. **Enable Gmail API:**
   - Go to https://console.cloud.google.com/
   - Create new project or select existing
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download credentials as `gmail_credentials.json`

2. **Generate Token:**
   ```bash
   python driver_pulse_2fa.py  # Follow prompts to authorize
   # This creates gmail_token.json
   ```

3. **Copy JSON to GitHub Secrets:**
   ```bash
   # For gmail_credentials.json secret
   cat gmail_credentials.json | pbcopy  # macOS
   # Paste into DRIVER_PULSE_GMAIL_CREDENTIALS

   # For gmail_token.json secret
   cat gmail_token.json | pbcopy  # macOS
   # Paste into DRIVER_PULSE_GMAIL_TOKEN
   ```

### 3. Add Streamlit Secrets (for triggering from app)

Add to `.streamlit/secrets.toml`:

```toml
GITHUB_TOKEN = "ghp_your_token_here"
GITHUB_REPO_OWNER = "your-github-username"
GITHUB_REPO_NAME = "freeworld-job-scraper-main"
```

### 4. Test the Workflows

**Test auth-only workflow:**
1. Go to GitHub repo → Actions tab
2. Select "Refresh DriverPulse Authentication" workflow
3. Click "Run workflow" → Run workflow button
4. Watch the logs to verify success

**Test scheduled batch workflow:**
1. Go to GitHub repo → Actions tab
2. Select "Scheduled Batch Job Scraper" workflow
3. Click "Run workflow" → Run workflow button
4. Verify: Auth refresh → Then batch execution

**Check if auth worked:**
```python
# In Python console or Streamlit
from supabase_utils import get_client
client = get_client()
result = client.table('system_config').select('*').eq('config_key', 'driver_pulse_auth').execute()
print(result.data[0]['updated_at'])  # Should show recent timestamp
```

### 5. Automated Schedules

**Auth-only workflow:** Runs daily at 2 AM UTC (backup - not usually needed)

**Scheduled batch workflow:** Runs every 6 hours to scrape all due batches

Change schedules in `.github/workflows/` files:

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
```

Cron syntax examples:
- `'0 */6 * * *'` - Every 6 hours
- `'0 */4 * * *'` - Every 4 hours
- `'0 8,20 * * *'` - 8 AM and 8 PM daily

## Troubleshooting

### Workflow fails with "Playwright not installed"
GitHub Actions should auto-install Playwright. Check workflow logs for installation errors.

### Workflow fails with "Gmail 2FA timeout"
Gmail might not be sending codes fast enough. Try:
1. Run workflow again (sometimes Gmail is slow)
2. Check Gmail credentials are correct
3. Verify Gmail API is enabled

### App shows "Authentication not loaded"
1. Check system_config table has driver_pulse_auth row
2. Verify updated_at timestamp is recent
3. Check Supabase credentials in app secrets

### How to manually update auth if workflow fails
```bash
# Run locally with headless auth
python create_driver_pulse_auth.py

# Then manually insert into Supabase
python -c "
from supabase_utils import get_client
import json
client = get_client()
with open('auth.json') as f:
    auth_data = json.load(f)
client.table('system_config').upsert({
    'config_key': 'driver_pulse_auth',
    'config_value': json.dumps(auth_data)
}, on_conflict='config_key').execute()
"
```

## Files Created

### GitHub Actions Workflows
- `.github/workflows/refresh_driverpulse_auth.yml` - Auth-only workflow (daily backup)
- `.github/workflows/scheduled_batch_scraper.yml` - Auth + batch scraping (every 6 hours)

### Python Scripts
- `refresh_driverpulse_auth.py` - Auth refresh script for GitHub Actions
- `run_scheduled_batches.py` - Batch execution script (already existed)
- `github_actions_helper.py` - Helper for triggering workflows from Streamlit

### Database
- `supabase/migrations/20251008000000_create_system_config_table.sql` - system_config table

### Updated Files
- `driver_pulse_secrets.py` - Now reads from Supabase first, then secrets, then local files

## Monitoring

Check auth freshness in Supabase:
```sql
SELECT config_key, updated_at,
       NOW() - updated_at as age
FROM system_config
WHERE config_key = 'driver_pulse_auth';
```

If `age` is > 25 hours, the workflow might have failed. Check GitHub Actions logs.

## Usage in Streamlit App

To trigger auth refresh before a batch scrape:

```python
from github_actions_helper import refresh_auth_and_wait
import streamlit as st

# In your batch creation code
with st.spinner("Getting fresh DriverPulse authentication..."):
    success, msg = refresh_auth_and_wait(
        progress_callback=lambda status: st.info(status)
    )

if success:
    st.success(msg)
    # Now run your scrape - auth is fresh!
else:
    st.error(msg)
```

Or check auth age before deciding to refresh:

```python
from github_actions_helper import get_auth_age

age_seconds = get_auth_age()
if age_seconds is None or age_seconds > 180:  # > 3 minutes
    # Refresh auth
    refresh_auth_and_wait()
else:
    # Auth is fresh enough, use it
    pass
```

## Cost

**GitHub Actions:** FREE up to 2,000 minutes/month
- Auth workflow: ~2-3 minutes per run
- Batch workflow: ~5-10 minutes per run (depending on job count)
- Running every 6 hours = ~4 runs/day × 10 min = 40 min/day × 30 days = **1,200 min/month**
- Plus manual "Run Now" triggers
- **Should stay within free tier** with normal usage
