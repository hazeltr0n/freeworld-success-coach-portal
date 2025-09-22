#!/usr/bin/env python3
"""
Supabase Companies Table Setup Script
Sets up the enhanced companies table with all new features and optimized indexes
"""

import os
from companies_rollup import create_companies_table_sql, get_client

def setup_companies_table():
    """Set up the companies table with all enhancements"""

    client = get_client()
    if not client:
        print("❌ Supabase client not available")
        return False

    print("🏗️ Setting up enhanced companies table...")

    # Get the SQL for creating the table
    sql = create_companies_table_sql()

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
        # Performance indexes for companies queries
        """
        -- Additional performance indexes for companies dashboard
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_total_jobs_desc
        ON companies(total_jobs DESC);

        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_fair_chance_jobs_desc
        ON companies(fair_chance_jobs DESC) WHERE has_fair_chance = true;

        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_markets_gin
        ON companies USING GIN(markets);

        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_active_jobs_desc
        ON companies(active_jobs DESC) WHERE active_jobs > 0;
        """,

        # Jobs table optimization for company rollup
        """
        -- Optimize jobs table for company rollup queries
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_company_match_level
        ON jobs(company, match_level) WHERE match_level IN ('good', 'so-so');

        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_created_at_match_level
        ON jobs(created_at DESC, match_level) WHERE match_level IN ('good', 'so-so');

        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_company_route_type
        ON jobs(company, route_type) WHERE match_level IN ('good', 'so-so');
        """,

        # Function to refresh companies data efficiently
        """
        -- Function to refresh companies rollup efficiently
        CREATE OR REPLACE FUNCTION refresh_companies_rollup(days_back INTEGER DEFAULT 60)
        RETURNS TEXT AS $$
        DECLARE
            affected_rows INTEGER;
            cutoff_date TIMESTAMPTZ;
        BEGIN
            cutoff_date := NOW() - (days_back || ' days')::INTERVAL;

            -- Clear existing data
            DELETE FROM companies;
            GET DIAGNOSTICS affected_rows = ROW_COUNT;

            RETURN 'Cleared ' || affected_rows || ' existing companies. Ready for fresh data.';
        END;
        $$ LANGUAGE plpgsql;
        """,

        # View for quick company stats
        """
        -- View for quick company analytics
        CREATE OR REPLACE VIEW company_quick_stats AS
        SELECT
            COUNT(*) as total_companies,
            COUNT(*) FILTER (WHERE has_fair_chance = true) as fair_chance_companies,
            SUM(total_jobs) as total_jobs,
            SUM(fair_chance_jobs) as total_fair_chance_jobs,
            COUNT(*) FILTER (WHERE is_blacklisted = true) as blacklisted_companies,
            ROUND(AVG(total_jobs), 2) as avg_jobs_per_company
        FROM companies;
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
    print("3. The first section creates the enhanced companies table")
    print("4. The optimization queries add performance indexes")
    print("5. After running all SQL, run: python companies_rollup.py --update")
    print("6. This will populate the table with current company data")
    print()
    print("📊 BENEFITS:")
    print("• Faster companies dashboard loading")
    print("• Real-time blacklist filtering in pipeline")
    print("• Enhanced route type analytics")
    print("• Free agent feedback tracking")
    print("• Market-based analysis")
    print("• No query limits - get ALL companies with good/so-so jobs")
    print()

    return True

if __name__ == "__main__":
    setup_companies_table()