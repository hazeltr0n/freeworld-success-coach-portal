-- Add coach_username column for backward compatibility
-- This allows old code to still work while we transition to coach_usernames array

ALTER TABLE agent_profiles
ADD COLUMN IF NOT EXISTS coach_username TEXT;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_agent_profiles_coach_username ON agent_profiles (coach_username);

-- Add comment explaining this is for backward compatibility
COMMENT ON COLUMN agent_profiles.coach_username IS 'Backward compatibility field - primary coach. Use coach_usernames array for multi-coach support.';
