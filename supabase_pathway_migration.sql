-- Supabase Migration: Career Pathway System
-- This script adds career pathway support to the jobs table and updates existing data

-- ============================================================================
-- PART 1: ADD CAREER PATHWAY COLUMNS TO JOBS TABLE
-- ============================================================================

-- Add career_pathway column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='jobs' AND column_name='career_pathway') THEN
        ALTER TABLE jobs ADD COLUMN career_pathway TEXT;
        RAISE NOTICE 'Added career_pathway column to jobs table';
    ELSE
        RAISE NOTICE 'career_pathway column already exists';
    END IF;
END $$;

-- Add training_provided column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='jobs' AND column_name='training_provided') THEN
        ALTER TABLE jobs ADD COLUMN training_provided BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added training_provided column to jobs table';
    ELSE
        RAISE NOTICE 'training_provided column already exists';
    END IF;
END $$;

-- Add classifier_type column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='jobs' AND column_name='classifier_type') THEN
        ALTER TABLE jobs ADD COLUMN classifier_type TEXT DEFAULT 'cdl';
        RAISE NOTICE 'Added classifier_type column to jobs table';
    ELSE
        RAISE NOTICE 'classifier_type column already exists';
    END IF;
END $$;

-- ============================================================================
-- PART 2: CREATE INDEXES FOR PERFORMANCE
-- ============================================================================

-- Index for career pathway filtering (critical for agent portal performance)
CREATE INDEX IF NOT EXISTS idx_jobs_career_pathway
ON jobs(career_pathway);

-- Composite index for location + pathway filtering
CREATE INDEX IF NOT EXISTS idx_jobs_location_pathway
ON jobs(location, career_pathway);

-- Composite index for common agent portal queries
CREATE INDEX IF NOT EXISTS idx_jobs_portal_filtering
ON jobs(location, career_pathway, match_level, created_at);

-- ============================================================================
-- PART 3: UPDATE EXISTING JOBS WITH CDL PATHWAY CLASSIFICATION
-- ============================================================================

-- Count jobs that need updating
DO $$
DECLARE
    null_pathway_count INTEGER;
    empty_pathway_count INTEGER;
    total_jobs INTEGER;
BEGIN
    -- Count NULL career_pathway jobs
    SELECT COUNT(*) INTO null_pathway_count
    FROM jobs WHERE career_pathway IS NULL;

    -- Count empty career_pathway jobs
    SELECT COUNT(*) INTO empty_pathway_count
    FROM jobs WHERE career_pathway = '';

    -- Count total jobs
    SELECT COUNT(*) INTO total_jobs FROM jobs;

    RAISE NOTICE 'MIGRATION ANALYSIS:';
    RAISE NOTICE '  Total jobs: %', total_jobs;
    RAISE NOTICE '  Jobs with NULL career_pathway: %', null_pathway_count;
    RAISE NOTICE '  Jobs with empty career_pathway: %', empty_pathway_count;
    RAISE NOTICE '  Jobs needing update: %', (null_pathway_count + empty_pathway_count);
END $$;

-- Update NULL career_pathway jobs to 'cdl_pathway'
UPDATE jobs
SET career_pathway = 'cdl_pathway',
    classifier_type = 'cdl'
WHERE career_pathway IS NULL;

-- Update empty career_pathway jobs to 'cdl_pathway'
UPDATE jobs
SET career_pathway = 'cdl_pathway',
    classifier_type = 'cdl'
WHERE career_pathway = '';

-- Update any jobs without classifier_type
UPDATE jobs
SET classifier_type = 'cdl'
WHERE classifier_type IS NULL OR classifier_type = '';

-- ============================================================================
-- PART 4: ADD PATHWAY PREFERENCES TO AGENTS TABLE
-- ============================================================================

-- Add pathway_preferences column to agents table if it doesn't exist
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='agents') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name='agents' AND column_name='pathway_preferences') THEN
            ALTER TABLE agents ADD COLUMN pathway_preferences TEXT[];
            RAISE NOTICE 'Added pathway_preferences column to agents table';
        ELSE
            RAISE NOTICE 'pathway_preferences column already exists in agents table';
        END IF;
    ELSE
        RAISE NOTICE 'agents table does not exist - skipping pathway_preferences addition';
    END IF;
END $$;

-- ============================================================================
-- PART 5: VALIDATION AND VERIFICATION
-- ============================================================================

-- Verify the migration results
DO $$
DECLARE
    cdl_pathway_count INTEGER;
    total_jobs INTEGER;
    coverage_percentage DECIMAL;
BEGIN
    -- Count jobs with cdl_pathway
    SELECT COUNT(*) INTO cdl_pathway_count
    FROM jobs WHERE career_pathway = 'cdl_pathway';

    -- Count total jobs
    SELECT COUNT(*) INTO total_jobs FROM jobs;

    -- Calculate coverage
    IF total_jobs > 0 THEN
        coverage_percentage := (cdl_pathway_count::DECIMAL / total_jobs::DECIMAL) * 100;
    ELSE
        coverage_percentage := 0;
    END IF;

    RAISE NOTICE 'MIGRATION RESULTS:';
    RAISE NOTICE '  Jobs with cdl_pathway: %', cdl_pathway_count;
    RAISE NOTICE '  Total jobs: %', total_jobs;
    RAISE NOTICE '  CDL pathway coverage: %% ', ROUND(coverage_percentage, 2);

    -- Verify no NULL or empty pathways remain
    SELECT COUNT(*) INTO cdl_pathway_count
    FROM jobs WHERE career_pathway IS NULL OR career_pathway = '';

    IF cdl_pathway_count = 0 THEN
        RAISE NOTICE '✅ SUCCESS: All jobs now have career_pathway assigned';
    ELSE
        RAISE NOTICE '⚠️  WARNING: % jobs still have NULL/empty career_pathway', cdl_pathway_count;
    END IF;
END $$;

-- Display pathway distribution
SELECT
    career_pathway,
    COUNT(*) as job_count,
    ROUND((COUNT(*)::DECIMAL / (SELECT COUNT(*) FROM jobs)::DECIMAL) * 100, 2) as percentage
FROM jobs
WHERE career_pathway IS NOT NULL
GROUP BY career_pathway
ORDER BY job_count DESC;

-- ============================================================================
-- PART 6: CREATE PATHWAY ENUM (OPTIONAL - FOR FUTURE TYPE SAFETY)
-- ============================================================================

-- Create enum type for career pathways (optional - can be used for type safety)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'career_pathway_type') THEN
        CREATE TYPE career_pathway_type AS ENUM (
            'cdl_pathway',
            'dock_to_driver',
            'internal_cdl_training',
            'warehouse_to_driver',
            'logistics_progression',
            'non_cdl_driving',
            'general_warehouse',
            'construction_apprentice',
            'stepping_stone',
            'no_pathway'
        );
        RAISE NOTICE 'Created career_pathway_type enum';
    ELSE
        RAISE NOTICE 'career_pathway_type enum already exists';
    END IF;
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

RAISE NOTICE '🚀 PATHWAY MIGRATION COMPLETED SUCCESSFULLY!';
RAISE NOTICE '';
RAISE NOTICE 'Next Steps:';
RAISE NOTICE '1. Test pathway filtering in agent portals';
RAISE NOTICE '2. Verify new jobs get proper career_pathway classification';
RAISE NOTICE '3. Test unified Career Pathways multiselect in UI';
RAISE NOTICE '4. Monitor query performance with new indexes';