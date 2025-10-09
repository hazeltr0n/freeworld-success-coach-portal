-- Multi-Coach Agent System Migration
-- This migration restructures agent_profiles to support multiple coaches per agent
--
-- Changes:
-- 1. Remove coach_username from agent_profiles primary key
-- 2. Make agent_uuid the sole primary key
-- 3. Add coach_usernames array field to track all coaches for an agent
-- 4. Ensure agent_coaches junction table exists and is properly configured
-- 5. Migrate existing data to new structure

-- Step 1: Create agent_coaches junction table if it doesn't exist
CREATE TABLE IF NOT EXISTS agent_coaches (
    agent_uuid TEXT NOT NULL,
    coach_username TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (agent_uuid, coach_username)
);

-- Step 2: Create a temporary table with the new structure
CREATE TABLE agent_profiles_new (
    agent_uuid TEXT PRIMARY KEY,
    agent_name TEXT,
    agent_email TEXT,
    agent_city TEXT,
    agent_state TEXT,
    location TEXT DEFAULT 'Houston',
    route_filter TEXT DEFAULT 'both',
    fair_chance_only BOOLEAN DEFAULT false,
    max_jobs INTEGER DEFAULT 25,
    match_level TEXT DEFAULT 'good and so-so',
    show_prepared_for BOOLEAN DEFAULT true,
    zip_code TEXT DEFAULT '',
    zip_radius_miles INTEGER DEFAULT 25,
    lookback_hours INTEGER DEFAULT 72,
    search_config JSONB,
    pathway_preferences TEXT[] DEFAULT ARRAY[]::TEXT[],
    custom_url TEXT DEFAULT '',
    original_long_url TEXT DEFAULT '',
    admin_portal_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    placement_status TEXT DEFAULT '',
    employment_status TEXT DEFAULT '',
    airtable_synced_at TIMESTAMP WITH TIME ZONE,
    coach_usernames TEXT[] DEFAULT ARRAY[]::TEXT[]  -- NEW: Array of coach usernames
);

-- Step 3: Migrate data from old table to new table
-- For duplicate agent_uuids, keep the most recently updated record
-- and combine all coach_usernames into the array
INSERT INTO agent_profiles_new
SELECT DISTINCT ON (agent_uuid)
    agent_uuid,
    agent_name,
    agent_email,
    agent_city,
    agent_state,
    location,
    route_filter,
    fair_chance_only,
    max_jobs,
    match_level,
    show_prepared_for,
    zip_code,
    zip_radius_miles,
    lookback_hours,
    search_config,
    pathway_preferences,
    custom_url,
    original_long_url,
    admin_portal_url,
    is_active,
    created_at,
    GREATEST(last_accessed, NOW()),  -- Use most recent access time
    placement_status,
    employment_status,
    airtable_synced_at,
    ARRAY_AGG(coach_username) OVER (PARTITION BY agent_uuid)  -- Combine all coaches
FROM agent_profiles
ORDER BY agent_uuid, last_accessed DESC NULLS LAST;

-- Step 4: Populate agent_coaches junction table from old data
INSERT INTO agent_coaches (agent_uuid, coach_username, is_active, assigned_at)
SELECT DISTINCT
    agent_uuid,
    coach_username,
    is_active,
    COALESCE(created_at, NOW())
FROM agent_profiles
ON CONFLICT (agent_uuid, coach_username) DO UPDATE
SET is_active = EXCLUDED.is_active,
    assigned_at = EXCLUDED.assigned_at;

-- Step 5: Drop dependent views, drop old table, and rename new table
DROP VIEW IF EXISTS agent_engagement_summary CASCADE;
DROP VIEW IF EXISTS agent_coach_assignments CASCADE;
DROP TABLE agent_profiles CASCADE;
ALTER TABLE agent_profiles_new RENAME TO agent_profiles;

-- Step 6: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_agent_profiles_coach_usernames ON agent_profiles USING GIN (coach_usernames);
CREATE INDEX IF NOT EXISTS idx_agent_profiles_agent_uuid ON agent_profiles (agent_uuid);
CREATE INDEX IF NOT EXISTS idx_agent_coaches_coach_username ON agent_coaches (coach_username);
CREATE INDEX IF NOT EXISTS idx_agent_coaches_agent_uuid ON agent_coaches (agent_uuid);

-- Step 7: Add helpful comment
COMMENT ON COLUMN agent_profiles.coach_usernames IS 'Array of all coach usernames associated with this agent (for quick filtering)';
COMMENT ON TABLE agent_coaches IS 'Junction table for many-to-many relationship between agents and coaches';
