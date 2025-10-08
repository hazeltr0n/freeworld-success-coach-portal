-- Fix auto-learn markets trigger to handle missing config gracefully
-- This makes the trigger defensive and allows upserts to succeed even without Edge Function

-- Replace the trigger function with error handling
CREATE OR REPLACE FUNCTION trigger_auto_learn_markets()
RETURNS TRIGGER AS $$
DECLARE
  supabase_url TEXT;
  service_key TEXT;
BEGIN
  -- Check if this is a new location not in location_markets
  IF NOT EXISTS (
    SELECT 1 FROM location_markets
    WHERE location_string = LOWER(TRIM(NEW.location))
  ) AND NEW.zip_code IS NOT NULL THEN

    -- Try to get config settings, but don't fail if they don't exist
    BEGIN
      supabase_url := current_setting('app.supabase_url', true);
      service_key := current_setting('app.supabase_service_role_key', true);

      -- Only call Edge Function if we have the required config
      IF supabase_url IS NOT NULL AND service_key IS NOT NULL THEN
        PERFORM net.http_post(
          url := supabase_url || '/functions/v1/auto-learn-markets',
          headers := jsonb_build_object(
            'Content-Type', 'application/json',
            'Authorization', 'Bearer ' || service_key
          ),
          body := jsonb_build_object(
            'location', NEW.location,
            'zip_code', NEW.zip_code
          )
        );
      END IF;
    EXCEPTION
      WHEN OTHERS THEN
        -- Silently fail - don't block the insert
        -- Could log to a table here if needed
        NULL;
    END;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Note: To enable the auto-learn feature, set these database parameters:
-- ALTER DATABASE postgres SET app.supabase_url = 'https://yqbdltothngundojuebk.supabase.co';
-- ALTER DATABASE postgres SET app.supabase_service_role_key = '<your-service-role-key>';
