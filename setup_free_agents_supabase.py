#!/usr/bin/env python3
"""
Supabase Free Agents Analytics Setup Script
Sets up the enhanced free agents analytics table and optimizations
"""

from free_agents_rollup import create_free_agents_analytics_table_sql, get_client

def setup_free_agents_analytics():
    """Set up the free agents analytics table with all enhancements"""

    client = get_client()
    if not client:
        print("❌ Supabase client not available")
        return False

    print("🏗️ Setting up enhanced free agents analytics table...")

    # Get the SQL for creating the table
    sql = create_free_agents_analytics_table_sql()

    print("=" * 60)
    print("📋 SQL TO RUN IN SUPABASE DASHBOARD:")
    print("=" * 60)
    print()
    print(sql)
    print()
    print("=" * 60)
    print()
    print("🔧 ADDITIONAL OPTIMIZATION QUERIES:")
    print("=" * 60)
    print()

    # Additional optimization queries
    optimization_queries = [
        # Performance indexes for agent profiles table
        """
        -- Optimize existing agent_profiles table for analytics
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_profiles_coach_active
        ON agent_profiles(coach_username, is_active) WHERE is_active = true;

        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_profiles_last_activity
        ON agent_profiles(last_portal_visit DESC NULLS LAST);

        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_profiles_engagement
        ON agent_profiles(portal_visits DESC, job_clicks DESC);
        """,

        # Click events table optimization
        """
        -- Optimize click_events table for agent analytics
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_click_events_candidate_date
        ON click_events(candidate_id, clicked_at DESC) WHERE candidate_id IS NOT NULL;

        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_click_events_coach_date
        ON click_events(coach, clicked_at DESC) WHERE coach IS NOT NULL;

        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_click_events_market_route
        ON click_events(market, route, clicked_at DESC);
        """,

        # Views for quick analytics
        """
        -- Create views for quick agent analytics
        CREATE OR REPLACE VIEW agent_engagement_summary AS
        SELECT
            ap.agent_uuid,
            ap.agent_name,
            ap.coach_username,
            ap.agent_city || ', ' || ap.agent_state as location,
            ap.portal_visits,
            ap.job_clicks,
            ap.total_applications,
            ap.last_portal_visit,
            ap.last_job_click,
            CASE
                WHEN ap.portal_visits > 0 THEN (ap.job_clicks::float / ap.portal_visits * 100)
                ELSE 0
            END as click_through_rate,
            COUNT(ce.id) as recent_clicks
        FROM agent_profiles ap
        LEFT JOIN click_events ce ON ap.agent_uuid = ce.candidate_id
            AND ce.clicked_at > NOW() - INTERVAL '30 days'
        WHERE ap.is_active = true
        GROUP BY ap.agent_uuid, ap.agent_name, ap.coach_username, ap.agent_city,
                 ap.agent_state, ap.portal_visits, ap.job_clicks, ap.total_applications,
                 ap.last_portal_visit, ap.last_job_click;
        """,

        # Function to calculate agent engagement score
        """
        -- Function to calculate engagement score
        CREATE OR REPLACE FUNCTION calculate_agent_engagement_score(
            portal_visits INTEGER,
            job_clicks INTEGER,
            applications INTEGER,
            last_activity TIMESTAMPTZ
        ) RETURNS NUMERIC AS $$
        DECLARE
            visit_score NUMERIC := 0;
            click_score NUMERIC := 0;
            app_score NUMERIC := 0;
            recency_factor NUMERIC := 1.0;
            days_since_activity INTEGER;
            total_score NUMERIC;
        BEGIN
            -- Calculate base scores
            visit_score := LEAST(COALESCE(portal_visits, 0) * 2, 50);
            click_score := LEAST(COALESCE(job_clicks, 0) * 5, 100);
            app_score := COALESCE(applications, 0) * 20;

            -- Calculate recency factor
            IF last_activity IS NOT NULL THEN
                days_since_activity := EXTRACT(DAYS FROM NOW() - last_activity);

                IF days_since_activity > 30 THEN
                    recency_factor := 0.5;
                ELSIF days_since_activity > 14 THEN
                    recency_factor := 0.7;
                ELSIF days_since_activity > 7 THEN
                    recency_factor := 0.9;
                END IF;
            ELSE
                recency_factor := 0.5; -- No activity data
            END IF;

            total_score := (visit_score + click_score + app_score) * recency_factor;

            RETURN LEAST(total_score, 200); -- Max score of 200
        END;
        $$ LANGUAGE plpgsql;
        """,

        # Trigger to auto-update analytics when agent data changes
        """
        -- Trigger to refresh analytics when agent profiles change
        CREATE OR REPLACE FUNCTION refresh_agent_analytics()
        RETURNS TRIGGER AS $$
        BEGIN
            -- This would trigger an analytics refresh
            -- For now, just update the updated_at timestamp
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        -- Apply trigger (if it doesn't already exist)
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.triggers
                WHERE trigger_name = 'agent_profiles_analytics_refresh'
            ) THEN
                CREATE TRIGGER agent_profiles_analytics_refresh
                    BEFORE UPDATE ON agent_profiles
                    FOR EACH ROW
                    EXECUTE FUNCTION refresh_agent_analytics();
            END IF;
        END $$;
        """
    ]

    for i, query in enumerate(optimization_queries, 1):
        print(f"-- Query {i}:")
        print(query.strip())
        print()

    print("=" * 60)
    print("🚀 INSTRUCTIONS:")
    print("=" * 60)
    print()
    print("1. Copy and paste the above SQL into your Supabase SQL Editor")
    print("2. Run each query section one at a time")
    print("3. The first section creates the free_agents_analytics table")
    print("4. The optimization queries add performance indexes")
    print("5. After running all SQL, run: python free_agents_rollup.py --update")
    print("6. This will populate the analytics table with current agent data")
    print()
    print("📊 BENEFITS:")
    print("• Real-time agent engagement tracking")
    print("• Market-based agent analytics")
    print("• Route preference insights")
    print("• Coach performance metrics per agent")
    print("• Click-through rate analytics")
    print("• Automated engagement scoring")
    print("• Activity level classification")
    print("• Re-engagement identification")
    print()

    return True

if __name__ == "__main__":
    setup_free_agents_analytics()