-- Add agent search preference fields to free_agents table
-- Enables new agent portal v2 with customizable search experience

-- Location preferences
ALTER TABLE free_agents ADD COLUMN IF NOT EXISTS saved_city TEXT;
ALTER TABLE free_agents ADD COLUMN IF NOT EXISTS saved_zip_code TEXT;
ALTER TABLE free_agents ADD COLUMN IF NOT EXISTS saved_radius INTEGER DEFAULT 50;

-- Lookback period (job freshness control)
-- Default: 96 hours (4 days) - sweet spot for freshness + quantity
-- Options: 24, 48, 72, 96, 168, 336 hours
ALTER TABLE free_agents ADD COLUMN IF NOT EXISTS saved_lookback_hours INTEGER DEFAULT 96;

-- Route type preferences (array of selected routes)
-- Options: 'Local', 'Regional', 'OTR', 'Dedicated'
ALTER TABLE free_agents ADD COLUMN IF NOT EXISTS saved_routes TEXT[];

-- Quality filter preference
-- Options: 'good_only', 'good_and_soso'
ALTER TABLE free_agents ADD COLUMN IF NOT EXISTS saved_quality TEXT DEFAULT 'good_only';

-- Fair chance filter (background-friendly jobs only)
ALTER TABLE free_agents ADD COLUMN IF NOT EXISTS saved_fair_chance BOOLEAN DEFAULT false;

-- Activity tracking
ALTER TABLE free_agents ADD COLUMN IF NOT EXISTS last_search_at TIMESTAMPTZ;

-- Add helpful comments
COMMENT ON COLUMN free_agents.saved_lookback_hours IS 'Job freshness preference: 24h (1d), 48h (2d), 72h (3d), 96h (4d-default), 168h (7d), 336h (14d)';
COMMENT ON COLUMN free_agents.saved_routes IS 'Route type preferences: Local, Regional, OTR, Dedicated';
COMMENT ON COLUMN free_agents.saved_quality IS 'Quality filter: good_only or good_and_soso';
