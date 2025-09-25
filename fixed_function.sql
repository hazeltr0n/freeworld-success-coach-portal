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
    total_clicks_all_time INTEGER;
    total_clicks_14d INTEGER;
    total_apps_all_time INTEGER;
    total_apps_14d INTEGER;
BEGIN
    -- Clear existing analytics data
    DELETE FROM free_agents_analytics WHERE id > 0;

    -- Process each active agent (use DISTINCT to handle duplicates)
    FOR rec IN
        SELECT DISTINCT ON (agent_uuid) *
        FROM agent_profiles
        WHERE is_active = true
        ORDER BY agent_uuid, updated_at DESC
    LOOP
        -- Calculate all-time clicks from click_events
        SELECT COUNT(*) INTO total_clicks_all_time
        FROM click_events
        WHERE candidate_id = rec.agent_uuid;

        -- Calculate 14-day clicks from click_events
        SELECT COUNT(*) INTO total_clicks_14d
        FROM click_events
        WHERE candidate_id = rec.agent_uuid
          AND clicked_at > CURRENT_TIMESTAMP - INTERVAL '14 days';

        -- FIXED: Get all-time applications from job_feedback table
        SELECT COUNT(*) INTO total_apps_all_time
        FROM job_feedback
        WHERE candidate_id = rec.agent_uuid
          AND feedback_type = 'i_applied_to_this_job';

        -- FIXED: Calculate 14-day applications from job_feedback table
        SELECT COUNT(*) INTO total_apps_14d
        FROM job_feedback
        WHERE candidate_id = rec.agent_uuid
          AND created_at > CURRENT_TIMESTAMP - INTERVAL '14 days'
          AND feedback_type = 'i_applied_to_this_job';

        -- Calculate engagement score based on all-time data
        engagement_score := calculate_agent_engagement_score(
            COALESCE(rec.portal_visits, 0),
            COALESCE(total_clicks_all_time, 0),
            COALESCE(total_apps_all_time, 0),
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

        -- Get recent click data (companies clicked in last 14 days for coach check-ins)
        SELECT JSON_BUILD_OBJECT(
            'companies_clicked_14d', JSON_OBJECT_AGG(company, click_count),
            'total_companies_14d', COUNT(DISTINCT company),
            'total_clicks_14d', COALESCE(SUM(click_count), 0)
        ) INTO click_data
        FROM (
            SELECT company, COUNT(*) as click_count
            FROM click_events
            WHERE candidate_id = rec.agent_uuid
              AND clicked_at > CURRENT_TIMESTAMP - INTERVAL '14 days'
              AND company IS NOT NULL
            GROUP BY company
            ORDER BY click_count DESC
            LIMIT 10
        ) recent_clicks;

        -- Insert analytics record with both all-time and 14-day metrics
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
            job_clicks_14d,
            total_applications,
            applications_14d,
            last_portal_visit,
            last_job_click,
            last_application_at,
            route_preferences,
            pathway_preferences,
            click_through_rate,
            engagement_score,
            companies_clicked,
            click_data,
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
            COALESCE(total_clicks_all_time, 0),  -- All-time clicks
            COALESCE(total_clicks_14d, 0),       -- 14-day clicks
            COALESCE(total_apps_all_time, 0),    -- All-time applications (FIXED)
            COALESCE(total_apps_14d, 0),         -- 14-day applications (FIXED)
            rec.last_portal_visit,
            rec.last_job_click,
            rec.last_application_at,
            COALESCE(rec.search_config, '{}'::JSONB),
            COALESCE(rec.pathway_preferences, ARRAY[]::TEXT[]),
            CASE
                WHEN COALESCE(rec.portal_visits, 0) > 0
                THEN ROUND((COALESCE(total_clicks_all_time, 0)::NUMERIC / rec.portal_visits * 100), 2)
                ELSE 0
            END,
            engagement_score,
            JSON_BUILD_OBJECT(
                'all_time_clicks', COALESCE(total_clicks_all_time, 0),
                'clicks_14d', COALESCE(total_clicks_14d, 0),
                'all_time_applications', COALESCE(total_apps_all_time, 0),
                'applications_14d', COALESCE(total_apps_14d, 0)
            ),
            COALESCE(click_data, '{}'::JSON),
            true,
            activity_level,
            COALESCE(rec.last_portal_visit, rec.last_job_click, rec.created_at),
            COALESCE(rec.priority_level::TEXT, 'normal'),
            rec.notes,
            COALESCE(rec.tags, ARRAY[]::TEXT[])
        ) ON CONFLICT (agent_uuid) DO UPDATE SET
            agent_name = EXCLUDED.agent_name,
            coach_username = EXCLUDED.coach_username,
            total_job_clicks = EXCLUDED.total_job_clicks,
            job_clicks_14d = EXCLUDED.job_clicks_14d,
            total_applications = EXCLUDED.total_applications,
            applications_14d = EXCLUDED.applications_14d,
            companies_clicked = EXCLUDED.companies_clicked,
            click_data = EXCLUDED.click_data,
            engagement_score = EXCLUDED.engagement_score,
            activity_level = EXCLUDED.activity_level,
            updated_at = CURRENT_TIMESTAMP;

        agents_count := agents_count + 1;
    END LOOP;

    -- Build success result
    result_json := JSON_BUILD_OBJECT(
        'success', true,
        'timestamp', CURRENT_TIMESTAMP,
        'agents_updated', agents_count,
        'message', 'Free agents analytics refreshed - FIXED to use job_feedback table'
    );

    RETURN result_json;

EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS error_msg = MESSAGE_TEXT;

    result_json := JSON_BUILD_OBJECT(
        'success', false,
        'timestamp', CURRENT_TIMESTAMP,
        'error', error_msg,
        'message', 'Failed to refresh free agents analytics'
    );

    RETURN result_json;
END;
$$ LANGUAGE plpgsql;