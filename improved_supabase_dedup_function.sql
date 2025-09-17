-- Improved Supabase Job Deduplication Function
-- Uses (market, company) when company exists, (market, job_title) when company is empty
-- This prevents removing genuinely different jobs that just lack company info

-- Create the improved deduplication function
CREATE OR REPLACE FUNCTION cleanup_duplicate_jobs_improved()
RETURNS TABLE (
    total_jobs_before INTEGER,
    duplicate_groups INTEGER,
    jobs_removed INTEGER,
    total_jobs_after INTEGER,
    company_based_removals INTEGER,
    title_based_removals INTEGER
) AS $$
DECLARE
    jobs_before INTEGER;
    jobs_after INTEGER;
    groups_with_dupes INTEGER;
    removed_count INTEGER;
    company_removals INTEGER := 0;
    title_removals INTEGER := 0;
BEGIN
    -- Count total jobs before cleanup
    SELECT COUNT(*) INTO jobs_before FROM jobs;
    
    -- Strategy 1: Remove duplicates for jobs WITH company names (market + company)
    WITH company_jobs_ranked AS (
        SELECT 
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
    ),
    company_jobs_to_remove AS (
        SELECT job_id
        FROM company_jobs_ranked
        WHERE row_num > 1  -- Keep only rank 1 (newest), remove others
    )
    DELETE FROM jobs 
    WHERE job_id IN (SELECT job_id FROM company_jobs_to_remove);
    
    -- Count removals from company-based deduplication
    GET DIAGNOSTICS company_removals = ROW_COUNT;
    
    -- Strategy 2: Remove duplicates for jobs WITHOUT company names (market + job_title)
    WITH empty_company_jobs_ranked AS (
        SELECT 
            job_id,
            market,
            job_title,
            classified_at,
            created_at,
            -- Create dedup key (market, job_title) - case insensitive
            LOWER(TRIM(market)) || '|' || LOWER(TRIM(job_title)) as dedup_key,
            -- Rank by newest classified_at, then created_at as tiebreaker
            ROW_NUMBER() OVER (
                PARTITION BY LOWER(TRIM(market)), LOWER(TRIM(job_title))
                ORDER BY classified_at DESC NULLS LAST, created_at DESC NULLS LAST
            ) as row_num
        FROM jobs
        WHERE 
            market IS NOT NULL 
            AND job_title IS NOT NULL
            AND TRIM(market) != '' 
            AND TRIM(job_title) != ''
            AND (company IS NULL OR TRIM(company) = '')  -- Only empty company jobs
    ),
    title_jobs_to_remove AS (
        SELECT job_id
        FROM empty_company_jobs_ranked
        WHERE row_num > 1  -- Keep only rank 1 (newest), remove others
    )
    DELETE FROM jobs 
    WHERE job_id IN (SELECT job_id FROM title_jobs_to_remove);
    
    -- Count removals from title-based deduplication
    GET DIAGNOSTICS title_removals = ROW_COUNT;
    
    -- Calculate totals
    removed_count := company_removals + title_removals;
    
    -- Count total jobs after cleanup
    SELECT COUNT(*) INTO jobs_after FROM jobs;
    
    -- Count remaining duplicate groups (for verification)
    WITH all_dedup_keys AS (
        -- Company-based keys
        SELECT 
            LOWER(TRIM(market)) || '|' || LOWER(TRIM(company)) as dedup_key,
            COUNT(*) as group_size
        FROM jobs
        WHERE 
            market IS NOT NULL 
            AND company IS NOT NULL 
            AND TRIM(market) != '' 
            AND TRIM(company) != ''
        GROUP BY LOWER(TRIM(market)), LOWER(TRIM(company))
        HAVING COUNT(*) > 1
        
        UNION ALL
        
        -- Title-based keys (for empty company jobs)
        SELECT 
            LOWER(TRIM(market)) || '|' || LOWER(TRIM(job_title)) as dedup_key,
            COUNT(*) as group_size
        FROM jobs
        WHERE 
            market IS NOT NULL 
            AND job_title IS NOT NULL
            AND TRIM(market) != '' 
            AND TRIM(job_title) != ''
            AND (company IS NULL OR TRIM(company) = '')
        GROUP BY LOWER(TRIM(market)), LOWER(TRIM(job_title))
        HAVING COUNT(*) > 1
    )
    SELECT COUNT(*) INTO groups_with_dupes FROM all_dedup_keys;
    
    -- Return summary statistics
    RETURN QUERY SELECT 
        jobs_before::INTEGER,
        groups_with_dupes::INTEGER,
        removed_count::INTEGER,
        jobs_after::INTEGER,
        company_removals::INTEGER,
        title_removals::INTEGER;
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- SELECT * FROM cleanup_duplicate_jobs_improved();

-- Create a function to analyze what would be removed (dry run)
CREATE OR REPLACE FUNCTION analyze_duplicate_jobs_improved()
RETURNS TABLE (
    dedup_strategy TEXT,
    market TEXT,
    key_field TEXT,
    key_value TEXT,
    duplicate_count INTEGER,
    newest_job_title TEXT,
    oldest_date TIMESTAMP,
    newest_date TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    -- Strategy 1: Company-based duplicates
    WITH company_duplicates AS (
        SELECT 
            'market + company' as strategy,
            market,
            'company' as field,
            company as value,
            COUNT(*) as dup_count,
            MAX(job_title) as sample_title,
            MIN(COALESCE(classified_at, created_at)) as oldest,
            MAX(COALESCE(classified_at, created_at)) as newest
        FROM jobs
        WHERE 
            market IS NOT NULL 
            AND company IS NOT NULL 
            AND TRIM(market) != '' 
            AND TRIM(company) != ''
        GROUP BY market, company
        HAVING COUNT(*) > 1
    ),
    title_duplicates AS (
        SELECT 
            'market + job_title' as strategy,
            market,
            'job_title' as field,
            job_title as value,
            COUNT(*) as dup_count,
            MAX(job_title) as sample_title,
            MIN(COALESCE(classified_at, created_at)) as oldest,
            MAX(COALESCE(classified_at, created_at)) as newest
        FROM jobs
        WHERE 
            market IS NOT NULL 
            AND job_title IS NOT NULL
            AND TRIM(market) != '' 
            AND TRIM(job_title) != ''
            AND (company IS NULL OR TRIM(company) = '')
        GROUP BY market, job_title
        HAVING COUNT(*) > 1
    )
    SELECT 
        cd.strategy::TEXT,
        cd.market::TEXT,
        cd.field::TEXT,
        cd.value::TEXT,
        cd.dup_count::INTEGER,
        cd.sample_title::TEXT,
        cd.oldest,
        cd.newest
    FROM company_duplicates cd
    
    UNION ALL
    
    SELECT 
        td.strategy::TEXT,
        td.market::TEXT,
        td.field::TEXT,
        td.value::TEXT,
        td.dup_count::INTEGER,
        td.sample_title::TEXT,
        td.oldest,
        td.newest
    FROM title_duplicates td
    
    ORDER BY dup_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- SELECT * FROM analyze_duplicate_jobs_improved();