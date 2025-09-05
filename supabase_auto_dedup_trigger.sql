-- Auto-Deduplication Trigger for Supabase Jobs Table
-- This trigger automatically runs cleanup_duplicate_jobs() after every INSERT operation
-- Run this in the Supabase SQL Editor AFTER creating the deduplication functions

-- First, create a lightweight trigger function that calls our cleanup
CREATE OR REPLACE FUNCTION trigger_auto_dedup()
RETURNS TRIGGER AS $$
DECLARE
    cleanup_result RECORD;
BEGIN
    -- Only run cleanup if this is an INSERT (new jobs uploaded)
    IF TG_OP = 'INSERT' THEN
        -- Call our cleanup function and capture results
        SELECT * INTO cleanup_result FROM cleanup_duplicate_jobs() LIMIT 1;
        
        -- Log the cleanup results (optional - helps with monitoring)
        RAISE NOTICE 'Auto-dedup completed: % jobs before, % removed, % jobs after', 
            cleanup_result.total_jobs_before, 
            cleanup_result.jobs_removed, 
            cleanup_result.total_jobs_after;
    END IF;
    
    -- Return the NEW row (required for AFTER INSERT triggers)
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger that fires AFTER INSERT on the jobs table
-- Using STATEMENT level trigger so it runs once per batch insert, not per row
CREATE OR REPLACE TRIGGER auto_dedup_after_insert
    AFTER INSERT ON jobs
    FOR EACH STATEMENT  -- Runs once per INSERT statement, not per row
    EXECUTE FUNCTION trigger_auto_dedup();

-- Alternative: Row-level trigger (runs for each inserted row - use if batch inserts cause issues)
-- Uncomment these lines if you prefer row-level triggering:
/*
DROP TRIGGER IF EXISTS auto_dedup_after_insert ON jobs;

CREATE OR REPLACE TRIGGER auto_dedup_after_insert
    AFTER INSERT ON jobs
    FOR EACH ROW  -- Runs once per inserted row
    EXECUTE FUNCTION trigger_auto_dedup();
*/

-- Create a function to disable the auto-dedup trigger temporarily (useful for bulk imports)
CREATE OR REPLACE FUNCTION disable_auto_dedup()
RETURNS TEXT AS $$
BEGIN
    DROP TRIGGER IF EXISTS auto_dedup_after_insert ON jobs;
    RETURN 'Auto-dedup trigger disabled';
END;
$$ LANGUAGE plpgsql;

-- Create a function to re-enable the auto-dedup trigger
CREATE OR REPLACE FUNCTION enable_auto_dedup()
RETURNS TEXT AS $$
BEGIN
    -- Drop existing trigger first (if any)
    DROP TRIGGER IF EXISTS auto_dedup_after_insert ON jobs;
    
    -- Recreate the trigger
    CREATE TRIGGER auto_dedup_after_insert
        AFTER INSERT ON jobs
        FOR EACH STATEMENT
        EXECUTE FUNCTION trigger_auto_dedup();
        
    RETURN 'Auto-dedup trigger enabled';
END;
$$ LANGUAGE plpgsql;

-- Check trigger status
CREATE OR REPLACE FUNCTION check_auto_dedup_status()
RETURNS TABLE (
    trigger_name TEXT,
    table_name TEXT,
    trigger_enabled BOOLEAN,
    trigger_timing TEXT,
    trigger_level TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.trigger_name::TEXT,
        t.event_object_table::TEXT,
        (t.status = 'ENABLED')::BOOLEAN as trigger_enabled,
        t.action_timing::TEXT,
        t.action_orientation::TEXT
    FROM information_schema.triggers t
    WHERE t.trigger_name = 'auto_dedup_after_insert'
    AND t.event_object_table = 'jobs';
END;
$$ LANGUAGE plpgsql;

-- Usage Examples:
--
-- 1. CHECK if trigger is active:
-- SELECT * FROM check_auto_dedup_status();
--
-- 2. DISABLE trigger temporarily (for bulk imports):
-- SELECT disable_auto_dedup();
--
-- 3. RE-ENABLE trigger:
-- SELECT enable_auto_dedup();
--
-- 4. MANUAL cleanup (if trigger is disabled):
-- SELECT * FROM cleanup_duplicate_jobs();

-- Create a monitoring table to track auto-dedup activity (optional)
CREATE TABLE IF NOT EXISTS auto_dedup_log (
    id SERIAL PRIMARY KEY,
    triggered_at TIMESTAMPTZ DEFAULT NOW(),
    jobs_before INTEGER,
    jobs_removed INTEGER,
    jobs_after INTEGER,
    trigger_type TEXT DEFAULT 'auto'
);

-- Enhanced trigger function with logging
CREATE OR REPLACE FUNCTION trigger_auto_dedup_with_logging()
RETURNS TRIGGER AS $$
DECLARE
    cleanup_result RECORD;
BEGIN
    -- Only run cleanup if this is an INSERT
    IF TG_OP = 'INSERT' THEN
        -- Call cleanup function
        SELECT * INTO cleanup_result FROM cleanup_duplicate_jobs() LIMIT 1;
        
        -- Log to monitoring table
        INSERT INTO auto_dedup_log (jobs_before, jobs_removed, jobs_after)
        VALUES (
            cleanup_result.total_jobs_before,
            cleanup_result.jobs_removed, 
            cleanup_result.total_jobs_after
        );
        
        -- Also log to PostgreSQL log
        RAISE NOTICE 'Auto-dedup: % before → % removed → % after', 
            cleanup_result.total_jobs_before, 
            cleanup_result.jobs_removed, 
            cleanup_result.total_jobs_after;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update trigger to use logging version
DROP TRIGGER IF EXISTS auto_dedup_after_insert ON jobs;

CREATE TRIGGER auto_dedup_after_insert
    AFTER INSERT ON jobs
    FOR EACH STATEMENT
    EXECUTE FUNCTION trigger_auto_dedup_with_logging();

-- Function to view recent auto-dedup activity
CREATE OR REPLACE FUNCTION view_auto_dedup_history(days_back INTEGER DEFAULT 7)
RETURNS TABLE (
    triggered_at TIMESTAMPTZ,
    jobs_before INTEGER,
    jobs_removed INTEGER,
    jobs_after INTEGER,
    efficiency_percent NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        adl.triggered_at,
        adl.jobs_before,
        adl.jobs_removed,
        adl.jobs_after,
        CASE 
            WHEN adl.jobs_before > 0 THEN 
                ROUND((adl.jobs_removed::NUMERIC / adl.jobs_before::NUMERIC * 100), 2)
            ELSE 0
        END as efficiency_percent
    FROM auto_dedup_log adl
    WHERE adl.triggered_at >= NOW() - (days_back || ' days')::INTERVAL
    ORDER BY adl.triggered_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Final setup confirmation
SELECT 'Auto-deduplication trigger system installed successfully!' as status;