-- Add job_id column to click_events table for proper job tracking
-- This allows us to join click_events directly with jobs table via job_id

ALTER TABLE click_events
ADD COLUMN IF NOT EXISTS job_id TEXT;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_click_events_job_id ON click_events(job_id);

-- Add comment
COMMENT ON COLUMN click_events.job_id IS 'Job ID from jobs table for direct joins';
