# Scheduled Batches Automation Setup

## Overview

This system automatically executes scheduled batches without requiring Streamlit to be running. It uses:

- **Supabase Edge Function**: Lightweight serverless function that runs the batch logic
- **pg_cron**: PostgreSQL extension that triggers the Edge Function every hour
- **No manual intervention**: Once set up, batches run automatically 24/7

## Architecture

```
pg_cron (every hour)
    ↓
Supabase Edge Function (run-scheduled-batches)
    ↓
Checks async_job_queue for due batches
    ↓
Updates batch status to 'submitted'
    ↓
For recurring batches: Creates next run entry
```

## Setup Steps

### 1. Deploy the Edge Function

```bash
# Make sure you're in the project root
cd /Users/freeworld_james/Development/freeworld-master/freeworld-job-scraper-main

# Deploy the Edge Function to Supabase
supabase functions deploy run-scheduled-batches
```

### 2. Set Edge Function Secrets

```bash
# Set the CRON_SECRET for Edge Function authorization
supabase secrets set CRON_SECRET="your-secure-random-token-here"

# Generate a secure token (optional):
# python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Enable pg_cron and Set Up the Schedule

```bash
# Apply the migration that enables pg_cron and schedules the job
./scripts/migrate.sh push
```

### 4. Verify Setup

```bash
# Check if pg_cron job was created
supabase db remote sql "SELECT * FROM cron.job;"

# Manually trigger the Edge Function to test
curl -X POST \
  https://yqbdltothngundojuebk.supabase.co/functions/v1/run-scheduled-batches \
  -H "Authorization: Bearer your-cron-secret" \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

## How It Works

### When You Schedule a Batch

1. User clicks "Schedule Recurring Batch" in Streamlit
2. Job created in `async_job_queue` table with:
   - `status = 'scheduled'`
   - `scheduled_run_at = [calculated time]`
   - `search_params` containing frequency, days, time, etc.

### Every Hour (Automatic)

1. **pg_cron triggers** at minute 0 of every hour
2. **Edge Function executes**:
   - Queries for jobs where `status='scheduled'` AND `scheduled_run_at <= now()`
   - For each due job:
     - Updates status to 'submitted'
     - Job gets picked up by normal batch processing
     - If recurring: Creates new entry for next run
3. **Batch executes** through normal pipeline
4. **Results stored** in Supabase with run_id

### Recurring Batches

- **Daily**: Next run = current run + 1 day
- **Weekly**: Next run = current run + 7 days
- **One-time**: No next run created

## Monitoring

### Check Scheduled Batches

```sql
-- See all scheduled batches
SELECT id, coach_username, job_type, scheduled_run_at, search_params->>'frequency' as frequency
FROM async_job_queue
WHERE status = 'scheduled'
ORDER BY scheduled_run_at;
```

### Check pg_cron Logs

```sql
-- See cron job execution history
SELECT * FROM cron.job_run_details
WHERE jobname = 'run-scheduled-batches-hourly'
ORDER BY start_time DESC
LIMIT 10;
```

### Check Edge Function Logs

```bash
# View Edge Function logs in Supabase Dashboard:
# https://supabase.com/dashboard/project/yqbdltothngundojuebk/functions/run-scheduled-batches/logs
```

## Troubleshooting

### Batches Not Running

1. **Check pg_cron is enabled**:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'pg_cron';
   ```

2. **Check cron job exists**:
   ```sql
   SELECT * FROM cron.job WHERE jobname = 'run-scheduled-batches-hourly';
   ```

3. **Check Edge Function is deployed**:
   ```bash
   supabase functions list
   ```

4. **Check Edge Function logs** for errors in Supabase Dashboard

### Manual Trigger for Testing

```bash
# Trigger the Edge Function manually
curl -X POST \
  https://yqbdltothngundojuebk.supabase.co/functions/v1/run-scheduled-batches \
  -H "Authorization: Bearer $(grep CRON_SECRET .env | cut -d '=' -f2)" \
  -H "Content-Type: application/json"
```

### Delete a Cron Job

```sql
-- If you need to remove the cron job
SELECT cron.unschedule('run-scheduled-batches-hourly');
```

## Configuration

### Change Frequency

Edit the migration file to change how often batches are checked:

```sql
-- Every 30 minutes:
'*/30 * * * *'

-- Every 15 minutes:
'*/15 * * * *'

-- Every 6 hours:
'0 */6 * * *'
```

Then reapply migration:
```bash
./scripts/migrate.sh push
```

## Security

- Edge Function requires `CRON_SECRET` for authorization
- Only pg_cron and authorized requests can trigger the function
- Supabase service role key is used to update database (has full access)
- All credentials stored in Supabase secrets (encrypted)

## Cost

- **Edge Functions**: Free tier includes 500K invocations/month (we use ~720/month)
- **pg_cron**: Free (built into Supabase PostgreSQL)
- **Database queries**: Negligible (1-2 queries per hour)

## Next Steps

After setup, you can:
1. Schedule batches from Streamlit normally
2. Walk away - they'll run automatically
3. Check results in the Scheduled Batches table
4. Download CSV results when complete
