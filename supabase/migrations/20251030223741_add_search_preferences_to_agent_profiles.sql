-- Add new search preference fields to agent_profiles table
-- Note: Some fields already exist (lookback_hours, zip_code, zip_radius_miles, location, route_filter, fair_chance_only)
-- We're adding fields for the new ZIP/Market choice and route array

-- Location type selector ('zip' or 'market')
ALTER TABLE agent_profiles ADD COLUMN IF NOT EXISTS location_type TEXT DEFAULT 'market';

-- Market selection (for when location_type = 'market')
ALTER TABLE agent_profiles ADD COLUMN IF NOT EXISTS saved_market TEXT;

-- Route types as array (replaces route_filter which is 'both'/'local'/'otr')
ALTER TABLE agent_profiles ADD COLUMN IF NOT EXISTS saved_routes TEXT[];

-- Quality filter ('good_only' or 'good_and_soso') - maps from match_level
ALTER TABLE agent_profiles ADD COLUMN IF NOT EXISTS saved_quality TEXT DEFAULT 'good_and_soso';

-- Last search timestamp
ALTER TABLE agent_profiles ADD COLUMN IF NOT EXISTS last_search_at TIMESTAMPTZ;

-- Add helpful comments
COMMENT ON COLUMN agent_profiles.location_type IS 'Location search type: zip (ZIP+radius) or market (predefined region)';
COMMENT ON COLUMN agent_profiles.saved_market IS 'Predefined market region when location_type=market';
COMMENT ON COLUMN agent_profiles.saved_routes IS 'Route type preferences: Local, Regional, OTR, Dedicated';
COMMENT ON COLUMN agent_profiles.saved_quality IS 'Quality filter: good_only or good_and_soso';
