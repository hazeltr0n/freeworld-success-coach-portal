-- Database trigger to auto-learn markets from new job locations
-- Runs Edge Function when new jobs with unknown locations are inserted

-- Create a function that calls the Edge Function
CREATE OR REPLACE FUNCTION trigger_auto_learn_markets()
RETURNS TRIGGER AS $$
BEGIN
  -- Check if this is a new location not in location_markets
  IF NOT EXISTS (
    SELECT 1 FROM location_markets
    WHERE location_string = LOWER(TRIM(NEW.location))
  ) AND NEW.zip_code IS NOT NULL THEN

    -- Call Edge Function via pg_net (requires pg_net extension)
    -- This is async - won't block the insert
    PERFORM net.http_post(
      url := current_setting('app.supabase_url') || '/functions/v1/auto-learn-markets',
      headers := jsonb_build_object(
        'Content-Type', 'application/json',
        'Authorization', 'Bearer ' || current_setting('app.supabase_service_role_key')
      ),
      body := jsonb_build_object(
        'location', NEW.location,
        'zip_code', NEW.zip_code
      )
    );
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on jobs table (fires AFTER insert)
DROP TRIGGER IF EXISTS auto_learn_markets_trigger ON jobs;

CREATE TRIGGER auto_learn_markets_trigger
  AFTER INSERT ON jobs
  FOR EACH ROW
  EXECUTE FUNCTION trigger_auto_learn_markets();

-- Note: This requires pg_net extension to be enabled
-- Enable with: CREATE EXTENSION IF NOT EXISTS pg_net;
