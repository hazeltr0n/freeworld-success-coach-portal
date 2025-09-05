-- CRITICAL FIX: Remove references to non-existent 'id' column in deduplication functions
-- The dedup functions are referencing 'id' column that doesn't exist in jobs table
-- Jobs table only has 'job_id' as the unique identifier
-- Run this in Supabase SQL Editor to fix the "column id does not exist" error

-- Fix the main cleanup_duplicate_jobs function
CREATE OR REPLACE FUNCTION cleanup_duplicate_jobs()
RETURNS TABLE (
    total_jobs_before INTEGER,
    duplicate_groups INTEGER,
    jobs_removed INTEGER,
    total_jobs_after INTEGER
) AS $$
DECLARE
    jobs_before INTEGER;
    jobs_after INTEGER;
    groups_with_dupes INTEGER;
    removed_count INTEGER;
BEGIN
    -- Count total jobs before cleanup
    SELECT COUNT(*) INTO jobs_before FROM jobs;
    
    -- Create a temporary table with jobs to keep (newest from each market+company group)
    CREATE TEMP TABLE jobs_to_keep AS
    WITH ranked_jobs AS (
        SELECT 
            job_id,        -- Use job_id instead of id
            market,
            company,
            job_title,
            classified_at,
            created_at,
            -- Create dedup key (market, company) - case insensitive
            LOWER(TRIM(market)) || '|' || LOWER(TRIM(company)) as dedup_key,
            -- Rank by newest classified_at, then created_at as tiebreaker
            ROW_NUMBER() OVER (
                PARTITION BY LOWER(TRIM(market)), LOWER(TRIM(company))
                ORDER BY classified_at DESC NULLS LAST, created_at DESC NULLS LAST
            ) as row_num
        FROM jobs
        WHERE 
            market IS NOT NULL 
            AND company IS NOT NULL 
            AND TRIM(market) != '' 
            AND TRIM(company) != ''
    )
    SELECT 
        job_id,        -- Use job_id instead of id
        market,
        company,
        job_title,
        classified_at,
        created_at,
        dedup_key
    FROM ranked_jobs 
    WHERE row_num = 1; -- Keep only the newest job from each group

    -- Count how many groups had duplicates
    WITH group_counts AS (
        SELECT 
            LOWER(TRIM(market)) || '|' || LOWER(TRIM(company)) as dedup_key,
            COUNT(*) as job_count
        FROM jobs
        WHERE 
            market IS NOT NULL 
            AND company IS NOT NULL 
            AND TRIM(market) != '' 
            AND TRIM(company) != ''
        GROUP BY LOWER(TRIM(market)), LOWER(TRIM(company))
    )
    SELECT COUNT(*) INTO groups_with_dupes 
    FROM group_counts 
    WHERE job_count > 1;

    -- Count jobs that will be removed
    SELECT COUNT(*) INTO removed_count
    FROM jobs j
    WHERE 
        j.market IS NOT NULL 
        AND j.company IS NOT NULL 
        AND TRIM(j.market) != '' 
        AND TRIM(j.company) != ''
        AND j.job_id NOT IN (SELECT job_id FROM jobs_to_keep);  -- Use job_id instead of id

    -- Delete duplicate jobs (keep only the jobs in jobs_to_keep)
    DELETE FROM jobs 
    WHERE 
        market IS NOT NULL 
        AND company IS NOT NULL 
        AND TRIM(market) != '' 
        AND TRIM(company) != ''
        AND job_id NOT IN (SELECT job_id FROM jobs_to_keep);    -- Use job_id instead of id

    -- Count total jobs after cleanup
    SELECT COUNT(*) INTO jobs_after FROM jobs;

    -- Clean up temp table
    DROP TABLE jobs_to_keep;

    -- Return results
    RETURN QUERY SELECT jobs_before, groups_with_dupes, removed_count, jobs_after;
END;
$$ LANGUAGE plpgsql;

-- Also fix the market-specific cleanup function
CREATE OR REPLACE FUNCTION cleanup_market_duplicates(target_market TEXT)
RETURNS TABLE (
    jobs_removed INTEGER,
    groups_cleaned INTEGER
) AS $$
DECLARE
    removed_count INTEGER;
    groups_count INTEGER;
BEGIN
    -- Create temp table with jobs to keep for this market
    CREATE TEMP TABLE market_jobs_to_keep AS
    WITH ranked_jobs AS (
        SELECT 
            job_id,        -- Use job_id instead of id
            market,
            company,
            job_title,
            classified_at,
            created_at,
            ROW_NUMBER() OVER (
                PARTITION BY LOWER(TRIM(company))
                ORDER BY classified_at DESC NULLS LAST, created_at DESC NULLS LAST
            ) as row_num
        FROM jobs
        WHERE 
            LOWER(TRIM(market)) = LOWER(TRIM(target_market))
            AND company IS NOT NULL 
            AND TRIM(company) != ''
    )
    SELECT job_id, market, company, job_title, classified_at, created_at    -- Use job_id instead of id
    FROM ranked_jobs 
    WHERE row_num = 1;

    -- Count groups that will be cleaned
    WITH group_counts AS (
        SELECT 
            LOWER(TRIM(company)) as company_key,
            COUNT(*) as job_count
        FROM jobs
        WHERE 
            LOWER(TRIM(market)) = LOWER(TRIM(target_market))
            AND company IS NOT NULL 
            AND TRIM(company) != ''
        GROUP BY LOWER(TRIM(company))
    )
    SELECT COUNT(*) INTO groups_count 
    FROM group_counts 
    WHERE job_count > 1;

    -- Count jobs that will be removed
    SELECT COUNT(*) INTO removed_count
    FROM jobs j
    WHERE 
        LOWER(TRIM(j.market)) = LOWER(TRIM(target_market))
        AND j.company IS NOT NULL 
        AND TRIM(j.company) != ''
        AND j.job_id NOT IN (SELECT job_id FROM market_jobs_to_keep);    -- Use job_id instead of id

    -- Delete duplicate jobs for this market
    DELETE FROM jobs 
    WHERE 
        LOWER(TRIM(market)) = LOWER(TRIM(target_market))
        AND company IS NOT NULL 
        AND TRIM(company) != ''
        AND job_id NOT IN (SELECT job_id FROM market_jobs_to_keep);      -- Use job_id instead of id

    -- Clean up temp table
    DROP TABLE market_jobs_to_keep;

    -- Return results
    RETURN QUERY SELECT removed_count, groups_count;
END;
$$ LANGUAGE plpgsql;

-- Test the fix
SELECT 'Deduplication functions fixed - id column references removed' as status;