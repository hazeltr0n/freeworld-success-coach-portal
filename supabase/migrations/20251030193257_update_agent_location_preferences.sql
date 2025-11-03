-- Update agent location preferences to support ZIP/Radius OR Market selection
-- Removes saved_city (not needed), adds saved_market and saved_location_type

-- Remove saved_city column (simplify to ZIP or Market only)
ALTER TABLE free_agents DROP COLUMN IF EXISTS saved_city;

-- Add market selection option
ALTER TABLE free_agents ADD COLUMN IF NOT EXISTS saved_market TEXT;

-- Add location type selector ('zip' or 'market')
ALTER TABLE free_agents ADD COLUMN IF NOT EXISTS saved_location_type TEXT DEFAULT 'zip';

-- Add helpful comments
COMMENT ON COLUMN free_agents.saved_location_type IS 'Location search type: zip (ZIP+radius) or market (predefined region)';
COMMENT ON COLUMN free_agents.saved_market IS 'Predefined market region: Dallas, Atlanta, Houston, Phoenix, etc.';
