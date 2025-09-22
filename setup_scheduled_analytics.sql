-- Automated Analytics Rollup Functions for Supabase
-- Sets up scheduled functions to automatically refresh companies and free agents analytics

-- ============================================================================
-- COMPANIES ROLLUP AUTOMATION
-- ============================================================================

-- Function to refresh companies analytics (equivalent to companies_rollup.py --update)
CREATE OR REPLACE FUNCTION refresh_companies_analytics(days_back INTEGER DEFAULT 60)
RETURNS JSON AS $$
DECLARE
    result_json JSON;
    companies_count INTEGER := 0;
    error_msg TEXT;
BEGIN
    -- Clear existing companies data
    DELETE FROM companies WHERE id > 0;

    -- Insert fresh companies data from jobs analysis
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
        'message', 'Companies analytics refreshed successfully'
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

-- ============================================================================
-- FREE AGENTS ROLLUP AUTOMATION
-- ============================================================================

-- Function to refresh free agents analytics (equivalent to free_agents_rollup.py --update)
CREATE OR REPLACE FUNCTION refresh_free_agents_analytics()
RETURNS JSON AS $$
DECLARE
    result_json JSON;
    agents_count INTEGER := 0;
    error_msg TEXT;
    rec RECORD;
    engagement_score NUMERIC;
    activity_level TEXT;
    market_name TEXT;
    click_data JSON;
BEGIN
    -- Clear existing analytics data
    DELETE FROM free_agents_analytics WHERE id > 0;

    -- Process each active agent
    FOR rec IN
        SELECT * FROM agent_profiles WHERE is_active = true
    LOOP
        -- Calculate engagement score
        engagement_score := calculate_agent_engagement_score(
            COALESCE(rec.portal_visits, 0),
            COALESCE(rec.job_clicks, 0),
            COALESCE(rec.total_applications, 0),
            COALESCE(rec.last_portal_visit, rec.last_job_click)
        );

        -- Determine activity level
        IF engagement_score >= 100 THEN
            activity_level := 'high';
        ELSIF engagement_score >= 50 THEN
            activity_level := 'medium';
        ELSIF engagement_score >= 10 THEN
            activity_level := 'low';
        ELSE
            activity_level := 'new';
        END IF;

        -- Determine market from location
        market_name := CASE
            WHEN rec.agent_city ILIKE '%houston%' OR rec.agent_state ILIKE '%houston%' THEN 'Houston'
            WHEN rec.agent_city ILIKE '%dallas%' OR rec.agent_state ILIKE '%dallas%' THEN 'Dallas'
            WHEN rec.agent_city ILIKE '%las vegas%' OR rec.agent_state ILIKE '%nevada%' THEN 'Las Vegas'
            WHEN rec.agent_city ILIKE '%phoenix%' OR rec.agent_state ILIKE '%arizona%' THEN 'Phoenix'
            WHEN rec.agent_city ILIKE '%denver%' OR rec.agent_state ILIKE '%colorado%' THEN 'Denver'
            WHEN rec.agent_state ILIKE '%california%' THEN 'California'
            WHEN rec.agent_state ILIKE '%texas%' THEN 'Texas'
            WHEN rec.agent_city IS NOT NULL AND rec.agent_city != '' THEN rec.agent_city
            WHEN rec.agent_state IS NOT NULL AND rec.agent_state != '' THEN rec.agent_state
            ELSE 'Unknown'
        END;

        -- Get recent click data (last 30 days)
        SELECT JSON_BUILD_OBJECT(
            'companies_clicked', JSON_OBJECT_AGG(company, click_count),
            'total_recent_clicks', COALESCE(SUM(click_count), 0)
        ) INTO click_data
        FROM (
            SELECT company, COUNT(*) as click_count
            FROM click_events
            WHERE candidate_id = rec.agent_uuid
              AND clicked_at > NOW() - INTERVAL '30 days'
              AND company IS NOT NULL
            GROUP BY company
            ORDER BY click_count DESC
            LIMIT 10
        ) recent_clicks;

        -- Insert analytics record
        INSERT INTO free_agents_analytics (
            agent_uuid,
            agent_name,
            coach_username,
            agent_email,
            agent_city,
            agent_state,
            market,
            total_portal_visits,
            total_job_clicks,
            total_applications,
            last_portal_visit,
            last_job_click,
            last_application_at,
            route_preferences,
            pathway_preferences,
            click_through_rate,
            engagement_score,
            companies_clicked,
            is_active,
            activity_level,
            last_activity_at,
            priority_level,
            notes,
            tags
        ) VALUES (
            rec.agent_uuid,
            rec.agent_name,
            rec.coach_username,
            rec.agent_email,
            rec.agent_city,
            rec.agent_state,
            market_name,
            COALESCE(rec.portal_visits, 0),
            COALESCE(rec.job_clicks, 0),
            COALESCE(rec.total_applications, 0),
            rec.last_portal_visit,
            rec.last_job_click,
            rec.last_application_at,
            COALESCE(rec.search_config, '{}'::JSONB),
            COALESCE(rec.pathway_preferences, ARRAY[]::TEXT[]),
            CASE
                WHEN COALESCE(rec.portal_visits, 0) > 0
                THEN ROUND((COALESCE(rec.job_clicks, 0)::NUMERIC / rec.portal_visits * 100), 2)
                ELSE 0
            END,
            engagement_score,
            COALESCE(click_data, '{}'::JSON),
            true,
            activity_level,
            COALESCE(rec.last_portal_visit, rec.last_job_click, rec.created_at),
            COALESCE(rec.priority_level, 'normal'),
            rec.notes,
            COALESCE(rec.tags, ARRAY[]::TEXT[])
        );

        agents_count := agents_count + 1;
    END LOOP;

    -- Build success result
    result_json := JSON_BUILD_OBJECT(
        'success', true,
        'timestamp', NOW(),
        'agents_updated', agents_count,
        'message', 'Free agents analytics refreshed successfully'
    );

    RETURN result_json;

EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS error_msg = MESSAGE_TEXT;

    -- Return error result
    result_json := JSON_BUILD_OBJECT(
        'success', false,
        'timestamp', NOW(),
        'error', error_msg,
        'message', 'Failed to refresh free agents analytics'
    );

    RETURN result_json;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SCHEDULING SETUP (Requires pg_cron extension)
-- ============================================================================

-- Enable pg_cron extension (run this first if not already enabled)
-- CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule companies rollup to run daily at 2:00 AM UTC
SELECT cron.schedule(
    'refresh-companies-daily',
    '0 2 * * *',
    'SELECT refresh_companies_analytics(60);'
);

-- Schedule free agents rollup to run every 6 hours
SELECT cron.schedule(
    'refresh-agents-6hourly',
    '0 */6 * * *',
    'SELECT refresh_free_agents_analytics();'
);

-- ============================================================================
-- MONITORING AND LOGS
-- ============================================================================

-- Create a table to log rollup results
CREATE TABLE IF NOT EXISTS analytics_rollup_log (
    id SERIAL PRIMARY KEY,
    rollup_type TEXT NOT NULL, -- 'companies' or 'free_agents'
    executed_at TIMESTAMPTZ DEFAULT NOW(),
    success BOOLEAN NOT NULL,
    records_processed INTEGER,
    execution_time_ms INTEGER,
    result JSON,
    error_message TEXT
);

-- Function to log rollup execution
CREATE OR REPLACE FUNCTION log_rollup_execution(
    rollup_type TEXT,
    start_time TIMESTAMPTZ,
    result JSON
) RETURNS VOID AS $$
DECLARE
    execution_time_ms INTEGER;
    is_success BOOLEAN;
    records_count INTEGER;
    error_msg TEXT;
BEGIN
    execution_time_ms := EXTRACT(EPOCH FROM (NOW() - start_time)) * 1000;
    is_success := (result->>'success')::BOOLEAN;
    records_count := COALESCE((result->>'companies_updated')::INTEGER, (result->>'agents_updated')::INTEGER, 0);
    error_msg := result->>'error';

    INSERT INTO analytics_rollup_log (
        rollup_type,
        success,
        records_processed,
        execution_time_ms,
        result,
        error_message
    ) VALUES (
        rollup_type,
        is_success,
        records_count,
        execution_time_ms,
        result,
        error_msg
    );
END;
$$ LANGUAGE plpgsql;

-- Enhanced wrapper functions with logging
CREATE OR REPLACE FUNCTION scheduled_companies_refresh()
RETURNS JSON AS $$
DECLARE
    start_time TIMESTAMPTZ := NOW();
    result JSON;
BEGIN
    result := refresh_companies_analytics(60);
    PERFORM log_rollup_execution('companies', start_time, result);
    RETURN result;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION scheduled_agents_refresh()
RETURNS JSON AS $$
DECLARE
    start_time TIMESTAMPTZ := NOW();
    result JSON;
BEGIN
    result := refresh_free_agents_analytics();
    PERFORM log_rollup_execution('free_agents', start_time, result);
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Update cron jobs to use logged versions
SELECT cron.unschedule('refresh-companies-daily');
SELECT cron.unschedule('refresh-agents-6hourly');

SELECT cron.schedule(
    'companies-analytics-daily',
    '0 2 * * *',
    'SELECT scheduled_companies_refresh();'
);

SELECT cron.schedule(
    'agents-analytics-6hourly',
    '0 */6 * * *',
    'SELECT scheduled_agents_refresh();'
);

-- ============================================================================
-- MANUAL TESTING AND MANAGEMENT
-- ============================================================================

-- Test the functions manually:
-- SELECT refresh_companies_analytics(60);
-- SELECT refresh_free_agents_analytics();

-- View scheduled jobs:
-- SELECT * FROM cron.job;

-- View rollup logs:
-- SELECT * FROM analytics_rollup_log ORDER BY executed_at DESC LIMIT 10;

-- Disable scheduling (if needed):
-- SELECT cron.unschedule('companies-analytics-daily');
-- SELECT cron.unschedule('agents-analytics-6hourly');