-- Fix Companies Analytics Function to use actual market column
CREATE OR REPLACE FUNCTION refresh_companies_analytics(days_back INTEGER DEFAULT 60)
RETURNS JSON AS $$
DECLARE
    result_json JSON;
    companies_count INTEGER := 0;
    error_msg TEXT;
BEGIN
    -- Clear existing companies data
    DELETE FROM companies WHERE id > 0;

    -- Insert fresh companies data from jobs analysis using ACTUAL market column
    INSERT INTO companies (
        company_name,
        normalized_company_name,
        total_jobs,
        active_jobs,
        fair_chance_jobs,
        has_fair_chance,
        markets,
        job_titles,
        route_types,
        quality_breakdown,
        route_breakdown,
        oldest_job_date,
        newest_job_date,
        is_blacklisted
    )
    SELECT
        company,
        LOWER(TRIM(company)) as normalized_company_name,
        COUNT(*) as total_jobs,
        COUNT(*) as active_jobs,
        COUNT(*) FILTER (WHERE fair_chance ILIKE '%fair%' OR fair_chance ILIKE '%yes%' OR fair_chance = 'true') as fair_chance_jobs,
        COUNT(*) FILTER (WHERE fair_chance ILIKE '%fair%' OR fair_chance ILIKE '%yes%' OR fair_chance = 'true') > 0 as has_fair_chance,
        ARRAY_AGG(DISTINCT market) FILTER (WHERE
            market IS NOT NULL
            AND market != ''
            AND market IN ('Houston', 'Dallas', 'Las Vegas', 'Bay Area', 'Phoenix', 'Denver', 'Newark', 'Stockton', 'Inland Empire', 'Trenton')
        ) as markets,
        ARRAY_AGG(DISTINCT job_title ORDER BY job_title) FILTER (WHERE job_title IS NOT NULL) as job_titles,
        ARRAY_AGG(DISTINCT route_type) FILTER (WHERE route_type IS NOT NULL) as route_types,
        JSON_BUILD_OBJECT(
            'good', COUNT(*) FILTER (WHERE match_level = 'good'),
            'so-so', COUNT(*) FILTER (WHERE match_level = 'so-so'),
            'bad', COUNT(*) FILTER (WHERE match_level = 'bad')
        ) as quality_breakdown,
        JSON_BUILD_OBJECT(
            'Local', COUNT(*) FILTER (WHERE route_type ILIKE '%local%'),
            'OTR', COUNT(*) FILTER (WHERE route_type ILIKE '%otr%' OR route_type ILIKE '%over%'),
            'Regional', COUNT(*) FILTER (WHERE route_type ILIKE '%regional%')
        ) as route_breakdown,
        MIN(created_at) as oldest_job_date,
        MAX(created_at) as newest_job_date,
        FALSE as is_blacklisted
    FROM jobs
    WHERE
        created_at >= NOW() - (days_back || ' days')::INTERVAL
        AND match_level IN ('good', 'so-so')  -- Only companies with quality jobs
        AND company IS NOT NULL
        AND TRIM(company) != ''
    GROUP BY company
    HAVING COUNT(*) >= 1;  -- At least 1 job

    GET DIAGNOSTICS companies_count = ROW_COUNT;

    -- Build success result
    result_json := JSON_BUILD_OBJECT(
        'success', true,
        'timestamp', NOW(),
        'companies_updated', companies_count,
        'days_analyzed', days_back,
        'message', 'Companies analytics refreshed successfully with corrected market logic'
    );

    RETURN result_json;

EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS error_msg = MESSAGE_TEXT;

    -- Return error result
    result_json := JSON_BUILD_OBJECT(
        'success', false,
        'timestamp', NOW(),
        'error', error_msg,
        'message', 'Failed to refresh companies analytics'
    );

    RETURN result_json;
END;
$$ LANGUAGE plpgsql;