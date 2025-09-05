-- Supabase Job Deduplication Function
-- Creates a key of (market, company) for all jobs and keeps only the newest from each group
-- Run this in the Supabase SQL Editor

-- Create the deduplication function
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
            id,
            job_id,
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
        id,
        job_id,
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
        AND j.id NOT IN (SELECT id FROM jobs_to_keep);

    -- Delete duplicate jobs (keep only the jobs in jobs_to_keep)
    DELETE FROM jobs 
    WHERE 
        market IS NOT NULL 
        AND company IS NOT NULL 
        AND TRIM(market) != '' 
        AND TRIM(company) != ''
        AND id NOT IN (SELECT id FROM jobs_to_keep);

    -- Count total jobs after cleanup
    SELECT COUNT(*) INTO jobs_after FROM jobs;

    -- Clean up temp table
    DROP TABLE jobs_to_keep;

    -- Return results
    RETURN QUERY SELECT jobs_before, groups_with_dupes, removed_count, jobs_after;
END;
$$ LANGUAGE plpgsql;

-- Create a safer analysis function (read-only) to preview what would be cleaned
CREATE OR REPLACE FUNCTION analyze_duplicate_jobs()
RETURNS TABLE (
    market TEXT,
    company TEXT,
    duplicate_count INTEGER,
    newest_job_title TEXT,
    newest_classified_at TIMESTAMP,
    oldest_classified_at TIMESTAMP,
    jobs_to_remove INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH job_groups AS (
        SELECT 
            j.market,
            j.company,
            j.job_title,
            j.classified_at,
            j.created_at,
            COUNT(*) OVER (PARTITION BY LOWER(TRIM(j.market)), LOWER(TRIM(j.company))) as group_size,
            ROW_NUMBER() OVER (
                PARTITION BY LOWER(TRIM(j.market)), LOWER(TRIM(j.company))
                ORDER BY j.classified_at DESC NULLS LAST, j.created_at DESC NULLS LAST
            ) as row_num,
            MIN(j.classified_at) OVER (PARTITION BY LOWER(TRIM(j.market)), LOWER(TRIM(j.company))) as oldest_date,
            MAX(j.classified_at) OVER (PARTITION BY LOWER(TRIM(j.market)), LOWER(TRIM(j.company))) as newest_date
        FROM jobs j
        WHERE 
            j.market IS NOT NULL 
            AND j.company IS NOT NULL 
            AND TRIM(j.market) != '' 
            AND TRIM(j.company) != ''
    )
    SELECT DISTINCT
        jg.market,
        jg.company,
        jg.group_size::INTEGER as duplicate_count,
        (SELECT job_title FROM job_groups WHERE market = jg.market AND company = jg.company AND row_num = 1) as newest_job_title,
        jg.newest_date as newest_classified_at,
        jg.oldest_date as oldest_classified_at,
        (jg.group_size - 1)::INTEGER as jobs_to_remove
    FROM job_groups jg
    WHERE jg.group_size > 1
    ORDER BY jg.group_size DESC, jg.market, jg.company;
END;
$$ LANGUAGE plpgsql;

-- Create a function to clean up a specific market (for targeted cleanup)
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
            id,
            job_id,
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
    SELECT id, job_id, market, company, job_title, classified_at, created_at
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
        AND j.id NOT IN (SELECT id FROM market_jobs_to_keep);

    -- Delete duplicate jobs for this market
    DELETE FROM jobs 
    WHERE 
        LOWER(TRIM(market)) = LOWER(TRIM(target_market))
        AND company IS NOT NULL 
        AND TRIM(company) != ''
        AND id NOT IN (SELECT id FROM market_jobs_to_keep);

    -- Clean up temp table
    DROP TABLE market_jobs_to_keep;

    -- Return results
    RETURN QUERY SELECT removed_count, groups_count;
END;
$$ LANGUAGE plpgsql;

-- Usage Examples:
-- 
-- 1. ANALYZE duplicates (safe, read-only):
-- SELECT * FROM analyze_duplicate_jobs() ORDER BY duplicate_count DESC LIMIT 20;
--
-- 2. CLEANUP ALL duplicates (destructive):
-- SELECT * FROM cleanup_duplicate_jobs();
--
-- 3. CLEANUP specific market (destructive):
-- SELECT * FROM cleanup_market_duplicates('Dallas');
--
-- 4. Check specific market duplicates:
-- SELECT * FROM analyze_duplicate_jobs() WHERE market = 'Dallas';

-- Create indexes to improve performance (optional)
CREATE INDEX IF NOT EXISTS idx_jobs_market_company_dedup 
ON jobs (LOWER(TRIM(market)), LOWER(TRIM(company)), classified_at DESC, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_jobs_classified_at 
ON jobs (classified_at DESC) WHERE classified_at IS NOT NULL;