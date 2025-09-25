-- Add show_prepared_for column to agent_profiles table
-- This field will control whether portal links show the "prepared for" message
-- Migration: 20250925223820

-- Add the column with a default value of TRUE (show the message by default)
ALTER TABLE agent_profiles
ADD COLUMN show_prepared_for BOOLEAN DEFAULT TRUE;

-- Add a comment to explain the column
COMMENT ON COLUMN agent_profiles.show_prepared_for IS
'Controls whether portal links display the "Prepared for [Agent] by Coach [Coach]" message. Default TRUE to maintain existing behavior.';

-- Update existing records to have TRUE (maintaining current behavior)
UPDATE agent_profiles
SET show_prepared_for = TRUE
WHERE show_prepared_for IS NULL;