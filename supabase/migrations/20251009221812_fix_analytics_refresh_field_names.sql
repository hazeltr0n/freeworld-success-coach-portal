-- Fix refresh_free_agents_analytics() to use correct field names from agent_profiles
-- The agent_profiles table doesn't have last_portal_visit, last_job_click, last_application_at
-- It only has last_accessed

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
    total_applications_count INTEGER;
    total_clicks_count INTEGER;
BEGIN
    -- Clear existing analytics data
    DELETE FROM free_agents_analytics WHERE id > 0;

    -- Process each active agent
    FOR rec IN
        SELECT * FROM agent_profiles WHERE is_active = true
    LOOP
        -- Calculate total applications from job_feedback
        SELECT COUNT(*) INTO total_applications_count
        FROM job_feedback
        WHERE candidate_id = rec.agent_uuid
          AND feedback_type = 'i_applied_to_this_job';

        -- Calculate total clicks from click_events (portal visits + job clicks)
        SELECT COUNT(*) INTO total_clicks_count
        FROM click_events
        WHERE candidate_id = rec.agent_uuid;

        -- Calculate engagement score (using last_accessed instead of last_portal_visit)
        engagement_score := calculate_agent_engagement_score(
            0, -- portal visits (deprecated, using total_clicks_count instead)
            total_clicks_count, -- use actual click count from click_events
            total_applications_count,
            rec.last_accessed -- Use last_accessed instead of last_portal_visit
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

        -- Insert analytics record with multi-coach support and correct field names
        INSERT INTO free_agents_analytics (
            agent_uuid,
            agent_name,
            coach_username,
            coach_usernames,
            agent_email,
            agent_city,
            agent_state,
            market,
            total_portal_visits,
            total_job_clicks,
            total_applications,
            applications_14d,
            job_clicks_14d,
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
            tags,
            placement_status,
            employment_status
        ) VALUES (
            rec.agent_uuid,
            rec.agent_name,
            COALESCE(rec.coach_usernames[1], 'unknown'), -- First coach as primary
            COALESCE(rec.coach_usernames, ARRAY[]::TEXT[]), -- Multi-coach support
            rec.agent_email,
            rec.agent_city,
            rec.agent_state,
            market_name,
            0, -- portal_visits (deprecated, all clicks now counted together)
            total_clicks_count, -- use actual click count from click_events
            total_applications_count,
            -- Calculate 14-day applications count from job_feedback table
            (SELECT COUNT(*) FROM job_feedback
             WHERE candidate_id = rec.agent_uuid
               AND created_at >= CURRENT_TIMESTAMP - INTERVAL '14 days'
               AND feedback_type = 'i_applied_to_this_job'),
            -- Calculate 14-day job clicks count from click_events
            (SELECT COUNT(*) FROM click_events
             WHERE candidate_id = rec.agent_uuid
               AND clicked_at >= CURRENT_TIMESTAMP - INTERVAL '14 days'),
            rec.last_accessed, -- Use last_accessed for last_portal_visit
            rec.last_accessed, -- Use last_accessed for last_job_click
            -- Get last_application_at from job_feedback table
            (SELECT MAX(created_at) FROM job_feedback
             WHERE candidate_id = rec.agent_uuid
               AND feedback_type = 'i_applied_to_this_job'),
            COALESCE(rec.search_config, '{}'::JSONB),
            COALESCE(rec.pathway_preferences, ARRAY[]::TEXT[]),
            CASE
                WHEN total_clicks_count > 0
                THEN ROUND((total_applications_count::NUMERIC / total_clicks_count * 100), 2)
                ELSE 0
            END,
            engagement_score,
            COALESCE(click_data, '{}'::JSON),
            true,
            activity_level,
            rec.last_accessed, -- Use last_accessed for last_activity_at
            'normal', -- Default priority level
            '', -- No notes field in agent_profiles
            ARRAY[]::TEXT[], -- No tags field in agent_profiles
            COALESCE(rec.placement_status, ''),
            COALESCE(rec.employment_status, '')
        );

        agents_count := agents_count + 1;
    END LOOP;

    -- Build success result
    result_json := JSON_BUILD_OBJECT(
        'success', true,
        'timestamp', NOW(),
        'agents_updated', agents_count,
        'message', 'Free agents analytics refreshed successfully with correct field names'
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

-- Update the scheduled wrapper function as well
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
