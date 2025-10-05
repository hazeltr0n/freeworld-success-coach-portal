-- Add ZIP code and radius filtering to free_agents table
-- This allows agents to set their preferred location and job radius

ALTER TABLE free_agents ADD COLUMN IF NOT EXISTS zip_code TEXT;
ALTER TABLE free_agents ADD COLUMN IF NOT EXISTS zip_radius_miles INTEGER DEFAULT 25;

-- Add index for ZIP code lookups
CREATE INDEX IF NOT EXISTS idx_free_agents_zip_code ON free_agents(zip_code);

-- Comments
COMMENT ON COLUMN free_agents.zip_code IS 'Agent preferred ZIP code for job filtering';
COMMENT ON COLUMN free_agents.zip_radius_miles IS 'Job search radius in miles from ZIP code (default 25)';

-- Also add zip_code to jobs table if not exists (for filtering)
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS zip_code TEXT;
CREATE INDEX IF NOT EXISTS idx_jobs_zip_code ON jobs(zip_code);

COMMENT ON COLUMN jobs.zip_code IS 'Job location ZIP code extracted from normalized location';
