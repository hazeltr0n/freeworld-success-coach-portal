-- Add ZIP code and radius filtering to agent_profiles table
-- This migration actually adds the columns (the previous one didn't run)

ALTER TABLE agent_profiles ADD COLUMN IF NOT EXISTS zip_code TEXT;
ALTER TABLE agent_profiles ADD COLUMN IF NOT EXISTS zip_radius_miles INTEGER DEFAULT 25;

-- Add index for ZIP code lookups
CREATE INDEX IF NOT EXISTS idx_agent_profiles_zip_code ON agent_profiles(zip_code);

-- Comments
COMMENT ON COLUMN agent_profiles.zip_code IS 'Agent preferred ZIP code for job filtering';
COMMENT ON COLUMN agent_profiles.zip_radius_miles IS 'Job search radius in miles from ZIP code (default 25)';
