-- Add missing pathway columns to agent_profiles table for inline checkboxes
-- Each pathway gets its own boolean column for efficient st.data_editor rendering

-- Add classifier type (cdl vs pathway)
ALTER TABLE agent_profiles
ADD COLUMN IF NOT EXISTS classifier_type TEXT DEFAULT 'cdl';

-- Add pathway_preferences as JSON for backward compatibility
ALTER TABLE agent_profiles
ADD COLUMN IF NOT EXISTS pathway_preferences JSONB DEFAULT '[]'::jsonb;

-- Add individual pathway boolean columns for inline checkboxes
ALTER TABLE agent_profiles
ADD COLUMN IF NOT EXISTS cdl_pathway BOOLEAN DEFAULT false;

ALTER TABLE agent_profiles
ADD COLUMN IF NOT EXISTS dock_to_driver BOOLEAN DEFAULT false;

ALTER TABLE agent_profiles
ADD COLUMN IF NOT EXISTS internal_cdl_training BOOLEAN DEFAULT false;

ALTER TABLE agent_profiles
ADD COLUMN IF NOT EXISTS warehouse_to_driver BOOLEAN DEFAULT false;

ALTER TABLE agent_profiles
ADD COLUMN IF NOT EXISTS logistics_progression BOOLEAN DEFAULT false;

ALTER TABLE agent_profiles
ADD COLUMN IF NOT EXISTS non_cdl_driving BOOLEAN DEFAULT false;

ALTER TABLE agent_profiles
ADD COLUMN IF NOT EXISTS general_warehouse BOOLEAN DEFAULT false;

ALTER TABLE agent_profiles
ADD COLUMN IF NOT EXISTS stepping_stone BOOLEAN DEFAULT false;

-- Create index on classifier_type for faster queries
CREATE INDEX IF NOT EXISTS idx_agent_profiles_classifier_type
ON agent_profiles(classifier_type);

-- Create index on pathway columns for filtering
CREATE INDEX IF NOT EXISTS idx_agent_profiles_pathways
ON agent_profiles(cdl_pathway, dock_to_driver, internal_cdl_training, warehouse_to_driver);

-- For CDL agents, set cdl_pathway to true by default
UPDATE agent_profiles
SET cdl_pathway = true
WHERE classifier_type = 'cdl' OR classifier_type IS NULL;

-- Update any existing agents with pathway_preferences to populate boolean columns
-- This is a one-time migration script
DO $$
DECLARE
    agent RECORD;
    preferences JSONB;
BEGIN
    FOR agent IN SELECT * FROM agent_profiles WHERE pathway_preferences IS NOT NULL AND pathway_preferences != '[]'::jsonb
    LOOP
        preferences := agent.pathway_preferences;

        -- Set boolean columns based on pathway_preferences array
        UPDATE agent_profiles
        SET
            cdl_pathway = CASE WHEN preferences ? 'cdl_pathway' THEN true ELSE cdl_pathway END,
            dock_to_driver = CASE WHEN preferences ? 'dock_to_driver' THEN true ELSE dock_to_driver END,
            internal_cdl_training = CASE WHEN preferences ? 'internal_cdl_training' THEN true ELSE internal_cdl_training END,
            warehouse_to_driver = CASE WHEN preferences ? 'warehouse_to_driver' THEN true ELSE warehouse_to_driver END,
            logistics_progression = CASE WHEN preferences ? 'logistics_progression' THEN true ELSE logistics_progression END,
            non_cdl_driving = CASE WHEN preferences ? 'non_cdl_driving' THEN true ELSE non_cdl_driving END,
            general_warehouse = CASE WHEN preferences ? 'general_warehouse' THEN true ELSE general_warehouse END,
            stepping_stone = CASE WHEN preferences ? 'stepping_stone' THEN true ELSE stepping_stone END
        WHERE agent_uuid = agent.agent_uuid AND coach_username = agent.coach_username;
    END LOOP;
END $$;

-- Add comment explaining the schema
COMMENT ON COLUMN agent_profiles.classifier_type IS 'Agent classification: cdl (CDL driver) or pathway (career pathway)';
COMMENT ON COLUMN agent_profiles.pathway_preferences IS 'JSON array of pathway preferences for backward compatibility';
COMMENT ON COLUMN agent_profiles.cdl_pathway IS 'Boolean: Traditional CDL driving positions';
COMMENT ON COLUMN agent_profiles.dock_to_driver IS 'Boolean: Dock worker to CDL driver transition';
COMMENT ON COLUMN agent_profiles.internal_cdl_training IS 'Boolean: Company-sponsored CDL programs';
COMMENT ON COLUMN agent_profiles.warehouse_to_driver IS 'Boolean: General warehouse to driving progression';
COMMENT ON COLUMN agent_profiles.logistics_progression IS 'Boolean: Logistics career advancement';
COMMENT ON COLUMN agent_profiles.non_cdl_driving IS 'Boolean: Non-CDL driving positions';
COMMENT ON COLUMN agent_profiles.general_warehouse IS 'Boolean: General warehouse opportunities';
COMMENT ON COLUMN agent_profiles.stepping_stone IS 'Boolean: Career stepping stone positions';