# Daily Job Health Report System

Automated monitoring system that sends daily email reports about market job availability.

## Overview

The Daily Job Health Report automatically checks all markets for job availability and sends a comprehensive email report to james@freeworld.org every morning at 7am Central Time.

## Features

- **📊 Market Health Summary**: Shows job counts for all markets
- **🚨 Empty Market Alerts**: Highlights markets with zero jobs that need scraping
- **⚠️ Low Job Warnings**: Flags markets with <10 jobs
- **✅ Healthy Status**: Confirms markets with adequate job coverage
- **📧 Email via Gmail API**: Uses the same Gmail integration as DriverPulse

## Setup Instructions

### 1. Install the Cron Job

Run the setup script:

```bash
cd /Users/freeworld_james/Development/freeworld-master/freeworld-job-scraper-main
./scripts/setup_daily_health_cron.sh
```

This will:
- Create a cron job that runs at 7am Central (12pm UTC)
- Create a logs directory for output
- Display the cron configuration

### 2. Verify Installation

Check that the cron job is installed:

```bash
crontab -l | grep market_monitor
```

You should see:
```
0 12 * * * cd /path/to/project && python3 market_monitor.py 72 >> /path/to/logs/daily_health.log 2>&1
```

### 3. Manual Test Run

Test the report manually:

```bash
cd /Users/freeworld_james/Development/freeworld-master/freeworld-job-scraper-main
python3 market_monitor.py 72
```

This will generate and send a report immediately.

## Report Contents

### Email Subject
- **Empty Markets**: `🚨 Daily Job Health: X Markets EMPTY`
- **All Healthy**: `✅ Daily Job Health: All Markets OK (X jobs)`

### Report Sections

1. **Summary**
   - Total jobs across all markets
   - Number of markets with jobs
   - Number of empty markets

2. **Alert Section** (if applicable)
   - List of empty markets requiring action
   - Recommended next steps

3. **Market Details Table**
   - Market name
   - Job count (last 72 hours)
   - Status: 🚨 EMPTY / ⚠️ Low / ✅ Healthy

4. **Recommended Actions**
   - Use DriverPulse for multi-market scraping
   - Schedule async batches
   - Check for API issues

## Configuration

### Change Report Time

Edit the cron job to change when the report runs:

```bash
crontab -e
```

Modify the hour (currently `0 12 * * *` = 12pm UTC = 7am Central):
- `0 13 * * *` = 1pm UTC = 8am Central
- `0 11 * * *` = 11am UTC = 6am Central

### Change Lookback Period

The default is 72 hours. To change:

```bash
# Edit cron job
crontab -e

# Change the argument from 72 to desired hours
# Example: 48 hours
python3 market_monitor.py 48
```

### Change Email Recipient

Edit `market_monitor.py` line 275:

```python
recipient_email = 'james@freeworld.org'
```

## Logs

View the cron job logs:

```bash
tail -f /Users/freeworld_james/Development/freeworld-master/freeworld-job-scraper-main/logs/daily_health.log
```

## Troubleshooting

### Gmail API Authentication

If the email fails to send, check Gmail API credentials:

1. Ensure `token.pickle` exists in project root
2. Ensure `credentials.json` exists
3. Run a manual test to re-authenticate if needed

### Cron Not Running

Check cron service:

```bash
# View cron logs (macOS)
log show --predicate 'process == "cron"' --last 1h

# Check if cron daemon is running
ps aux | grep cron
```

### Empty Markets Alert

If you receive an alert about empty markets:

1. Log into the platform
2. Go to "Batch Jobs" → "DriverPulse Batches"
3. Run a multi-market scrape
4. Or schedule async batches for the empty markets

## Files

- `market_monitor.py` - Main monitoring script
- `scripts/setup_daily_health_cron.sh` - Cron installation script
- `logs/daily_health.log` - Execution logs
- `DAILY_HEALTH_REPORT.md` - This documentation

## Integration

The system integrates with:
- **Supabase** - Queries jobs table for market data
- **Gmail API** - Sends formatted email reports
- **Free Agent System** - Gets list of expected markets

---

*Last Updated: October 2025*
