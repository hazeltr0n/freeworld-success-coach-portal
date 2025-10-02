-- Multi-Coach Support and Placement Status Migration
-- This migration enables multiple coaches to work with the same agent and tracks Airtable placement data

-- Step 1: Create agent_coaches junction table for multi-coach support
CREATE TABLE IF NOT EXISTS agent_coaches (
    id BIGSERIAL PRIMARY KEY,
    agent_uuid TEXT NOT NULL,
    coach_username TEXT NOT NULL,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Composite unique constraint to prevent duplicate assignments
    UNIQUE(agent_uuid, coach_username)
);

-- Step 2: Add placement and employment status columns to agent_profiles
ALTER TABLE agent_profiles
ADD COLUMN IF NOT EXISTS placement_status TEXT,
ADD COLUMN IF NOT EXISTS employment_status TEXT,
ADD COLUMN IF NOT EXISTS airtable_synced_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS hired BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS hired_company TEXT,
ADD COLUMN IF NOT EXISTS hired_date TIMESTAMPTZ;

-- Step 3: Create agent_success_tracking table for platform success metrics
CREATE TABLE IF NOT EXISTS agent_success_tracking (
    id BIGSERIAL PRIMARY KEY,
    agent_uuid TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    hired_company TEXT NOT NULL,
    coach_username TEXT NOT NULL,
    hired_date TIMESTAMPTZ NOT NULL,
    application_count INTEGER DEFAULT 0,
    unique_companies_applied INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT
);

-- Step 4: Migrate existing agent_profiles data to agent_coaches junction table
-- This preserves all existing coach-agent relationships
INSERT INTO agent_coaches (agent_uuid, coach_username, assigned_at, is_active)
SELECT
    agent_uuid,
    coach_username,
    created_at,
    is_active
FROM agent_profiles
WHERE coach_username IS NOT NULL
ON CONFLICT (agent_uuid, coach_username) DO NOTHING;

-- Step 5: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_agent_coaches_agent_uuid ON agent_coaches(agent_uuid);
CREATE INDEX IF NOT EXISTS idx_agent_coaches_coach_username ON agent_coaches(coach_username);
CREATE INDEX IF NOT EXISTS idx_agent_coaches_active ON agent_coaches(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_agent_profiles_placement_status ON agent_profiles(placement_status);
CREATE INDEX IF NOT EXISTS idx_agent_profiles_employment_status ON agent_profiles(employment_status);
CREATE INDEX IF NOT EXISTS idx_agent_profiles_hired ON agent_profiles(hired) WHERE hired = TRUE;
CREATE INDEX IF NOT EXISTS idx_agent_success_tracking_coach ON agent_success_tracking(coach_username);
CREATE INDEX IF NOT EXISTS idx_agent_success_tracking_hired_date ON agent_success_tracking(hired_date);

-- Step 6: Create view for easy querying of agent-coach relationships with placement data
CREATE OR REPLACE VIEW agent_coach_assignments AS
SELECT
    ap.agent_uuid,
    ap.agent_name,
    ap.agent_email,
    ap.location,
    ap.placement_status,
    ap.employment_status,
    ap.hired,
    ap.hired_company,
    ap.hired_date,
    ap.airtable_synced_at,
    ac.coach_username,
    ac.assigned_at,
    ac.is_active AS coach_assignment_active,
    ac.notes AS coach_notes,
    -- Aggregate all coaches for this agent
    (SELECT STRING_AGG(coach_username, ', ' ORDER BY assigned_at)
     FROM agent_coaches
     WHERE agent_uuid = ap.agent_uuid AND is_active = TRUE) AS all_coaches
FROM agent_profiles ap
LEFT JOIN agent_coaches ac ON ap.agent_uuid = ac.agent_uuid
WHERE ac.is_active = TRUE OR ac.is_active IS NULL;

-- Step 7: Create function to get all coaches for an agent
CREATE OR REPLACE FUNCTION get_agent_coaches(p_agent_uuid TEXT)
RETURNS TABLE(coach_username TEXT, assigned_at TIMESTAMPTZ, notes TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT ac.coach_username, ac.assigned_at, ac.notes
    FROM agent_coaches ac
    WHERE ac.agent_uuid = p_agent_uuid AND ac.is_active = TRUE
    ORDER BY ac.assigned_at ASC;
END;
$$ LANGUAGE plpgsql;

-- Step 8: Create function to check if coach has access to agent
CREATE OR REPLACE FUNCTION coach_has_agent_access(p_coach_username TEXT, p_agent_uuid TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM agent_coaches
        WHERE coach_username = p_coach_username
        AND agent_uuid = p_agent_uuid
        AND is_active = TRUE
    );
END;
$$ LANGUAGE plpgsql;

-- Step 9: Update timestamp trigger for agent_coaches
CREATE OR REPLACE FUNCTION update_agent_coaches_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_agent_coaches_timestamp ON agent_coaches;
CREATE TRIGGER trigger_update_agent_coaches_timestamp
    BEFORE UPDATE ON agent_coaches
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_coaches_timestamp();

-- Step 10: Add RLS policies (if Row Level Security is enabled)
-- Note: Adjust these based on your security requirements

-- Allow coaches to see their assigned agents
-- ALTER TABLE agent_coaches ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY coach_access_own_assignments ON agent_coaches
--     FOR SELECT
--     USING (coach_username = current_user);

-- CREATE POLICY coach_manage_own_assignments ON agent_coaches
--     FOR ALL
--     USING (coach_username = current_user);

-- Migration Notes:
-- 1. After migration, agent_profiles.coach_username can eventually be deprecated
-- 2. All queries should use agent_coaches junction table for coach-agent relationships
-- 3. Delete operations should only soft-delete from agent_coaches, not agent_profiles
-- 4. The view agent_coach_assignments provides a convenient way to query relationships
-- 5. Use get_agent_coaches() function to get all coaches for an agent
-- 6. Use coach_has_agent_access() function to verify access before showing agent data
