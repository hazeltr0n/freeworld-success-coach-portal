-- Add coach_usernames array field and placement/employment status to free_agents_analytics table
-- This supports the multi-coach agent system and restores missing status fields

-- Add coach_usernames array field (multi-coach support)
ALTER TABLE free_agents_analytics
ADD COLUMN IF NOT EXISTS coach_usernames TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Add placement_status and employment_status (missing fields)
ALTER TABLE free_agents_analytics
ADD COLUMN IF NOT EXISTS placement_status TEXT DEFAULT '';

ALTER TABLE free_agents_analytics
ADD COLUMN IF NOT EXISTS employment_status TEXT DEFAULT '';

-- Create GIN index for efficient array searches on coach_usernames
CREATE INDEX IF NOT EXISTS idx_free_agents_analytics_coach_usernames
ON free_agents_analytics USING GIN (coach_usernames);

-- Add helpful comments
COMMENT ON COLUMN free_agents_analytics.coach_usernames IS 'Array of all coach usernames associated with this agent (for multi-coach filtering)';
COMMENT ON COLUMN free_agents_analytics.placement_status IS 'Current placement status from Airtable (e.g., Placed, Searching, Unknown)';
COMMENT ON COLUMN free_agents_analytics.employment_status IS 'Current employment status from Airtable (e.g., Employed, Searching, Inactive)';
