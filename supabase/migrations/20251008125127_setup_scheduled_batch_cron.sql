-- Schedule the Edge Function to run every hour
-- This will trigger our scheduled batch runner
-- Note: pg_cron extension is already enabled in Supabase
SELECT cron.schedule(
    'run-scheduled-batches-hourly', -- job name
    '0 * * * *', -- every hour at minute 0
    $$
    SELECT
      net.http_post(
          url:='https://yqbdltothngundojuebk.supabase.co/functions/v1/run-scheduled-batches',
          headers:=jsonb_build_object(
              'Content-Type','application/json',
              'Authorization', 'Bearer ' || current_setting('app.settings.cron_secret', true)
          ),
          body:=jsonb_build_object('triggered_by', 'pg_cron', 'timestamp', now())
      ) as request_id;
    $$
);

-- Add comment
COMMENT ON EXTENSION pg_cron IS 'Scheduled batch execution - runs every hour to check for due batches';
