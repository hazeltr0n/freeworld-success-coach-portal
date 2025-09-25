-- Migration: Flatten search_config JSON into individual columns
-- This improves performance and makes analytics rollup work properly

-- Add individual columns for search_config fields
ALTER TABLE agent_profiles
ADD COLUMN IF NOT EXISTS location TEXT DEFAULT 'Houston',
ADD COLUMN IF NOT EXISTS route_filter TEXT DEFAULT 'both',
ADD COLUMN IF NOT EXISTS fair_chance_only BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS max_jobs INTEGER DEFAULT 25,
ADD COLUMN IF NOT EXISTS match_level TEXT DEFAULT 'good and so-so';

-- Migrate existing data from search_config JSON to individual columns
UPDATE agent_profiles
SET
    location = COALESCE(search_config->>'location', 'Houston'),
    route_filter = COALESCE(search_config->>'route_filter', 'both'),
    fair_chance_only = COALESCE((search_config->>'fair_chance_only')::boolean, false),
    max_jobs = COALESCE((search_config->>'max_jobs')::integer, 25),
    match_level = COALESCE(search_config->>'match_level', 'good and so-so')
WHERE search_config IS NOT NULL;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_agent_profiles_location ON agent_profiles(location);
CREATE INDEX IF NOT EXISTS idx_agent_profiles_route_filter ON agent_profiles(route_filter);
CREATE INDEX IF NOT EXISTS idx_agent_profiles_fair_chance ON agent_profiles(fair_chance_only);

-- Keep search_config for backward compatibility during transition
-- Can be removed later once all code is updated

-- Update the analytics rollup view/table to use the new columns
-- This will make analytics rollup work with all editable fields