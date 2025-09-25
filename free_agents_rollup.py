#!/usr/bin/env python3
"""
Free Agents Rollup and Analytics
Enhanced analytics and rollup functionality for Free Agent management
"""

import os
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from collections import Counter
import json

try:
    from supabase_utils import get_client
except Exception:
    get_client = None

def create_free_agents_analytics_table_sql():
    """Generate SQL to create enhanced free agents analytics table"""
    return """
    -- Enhanced Free Agents Analytics Table
    CREATE TABLE IF NOT EXISTS free_agents_analytics (
        id SERIAL PRIMARY KEY,
        agent_uuid TEXT NOT NULL UNIQUE,
        agent_name TEXT NOT NULL,
        coach_username TEXT NOT NULL,

        -- Basic info
        agent_email TEXT,
        agent_city TEXT,
        agent_state TEXT,
        market TEXT,

        -- Engagement metrics
        total_portal_visits INTEGER DEFAULT 0,
        total_job_clicks INTEGER DEFAULT 0,
        total_applications INTEGER DEFAULT 0,

        -- Dates
        first_portal_visit TIMESTAMPTZ,
        last_portal_visit TIMESTAMPTZ,
        last_job_click TIMESTAMPTZ,
        last_application_at TIMESTAMPTZ,

        -- Preferences and config
        route_preferences JSONB DEFAULT '{}'::JSONB,
        pathway_preferences TEXT[],
        search_config JSONB DEFAULT '{}'::JSONB,

        -- Performance metrics
        click_through_rate NUMERIC DEFAULT 0,
        engagement_score NUMERIC DEFAULT 0,
        avg_jobs_per_search NUMERIC DEFAULT 0,

        -- Job interaction data
        companies_clicked JSONB DEFAULT '{}'::JSONB,
        route_types_clicked JSONB DEFAULT '{}'::JSONB,
        markets_engaged JSONB DEFAULT '{}'::JSONB,
        job_qualities_clicked JSONB DEFAULT '{}'::JSONB,

        -- Activity status
        is_active BOOLEAN DEFAULT TRUE,
        activity_level TEXT DEFAULT 'new', -- new, low, medium, high, inactive
        last_activity_at TIMESTAMPTZ,

        -- Coach relationship
        priority_level TEXT DEFAULT 'normal',
        notes TEXT,
        tags TEXT[],

        -- Metadata
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- Performance indexes
    CREATE INDEX IF NOT EXISTS idx_free_agents_analytics_uuid ON free_agents_analytics(agent_uuid);
    CREATE INDEX IF NOT EXISTS idx_free_agents_analytics_coach ON free_agents_analytics(coach_username);
    CREATE INDEX IF NOT EXISTS idx_free_agents_analytics_market ON free_agents_analytics(market);
    CREATE INDEX IF NOT EXISTS idx_free_agents_analytics_active ON free_agents_analytics(is_active);
    CREATE INDEX IF NOT EXISTS idx_free_agents_analytics_activity_level ON free_agents_analytics(activity_level);
    CREATE INDEX IF NOT EXISTS idx_free_agents_analytics_engagement ON free_agents_analytics(engagement_score DESC);
    CREATE INDEX IF NOT EXISTS idx_free_agents_analytics_last_activity ON free_agents_analytics(last_activity_at DESC);

    -- JSONB indexes for performance
    CREATE INDEX IF NOT EXISTS idx_free_agents_analytics_route_prefs ON free_agents_analytics USING GIN(route_preferences);
    CREATE INDEX IF NOT EXISTS idx_free_agents_analytics_companies_clicked ON free_agents_analytics USING GIN(companies_clicked);
    CREATE INDEX IF NOT EXISTS idx_free_agents_analytics_search_config ON free_agents_analytics USING GIN(search_config);

    -- Auto-update trigger
    CREATE OR REPLACE FUNCTION update_free_agents_analytics_updated_at()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    DROP TRIGGER IF EXISTS update_free_agents_analytics_updated_at ON free_agents_analytics;
    CREATE TRIGGER update_free_agents_analytics_updated_at
        BEFORE UPDATE ON free_agents_analytics
        FOR EACH ROW
        EXECUTE FUNCTION update_free_agents_analytics_updated_at();
    """

def calculate_engagement_score(agent_data: Dict) -> float:
    """Calculate engagement score based on activity metrics"""
    try:
        # Base metrics
        portal_visits = agent_data.get('portal_visits', 0) or 0
        job_clicks = agent_data.get('job_clicks', 0) or 0
        applications = agent_data.get('total_applications', 0) or 0

        # Time-based factors
        last_activity = agent_data.get('last_portal_visit') or agent_data.get('last_job_click')
        days_since_activity = 0
        if last_activity:
            try:
                last_dt = pd.to_datetime(last_activity)
                days_since_activity = (datetime.now(timezone.utc) - last_dt.tz_convert('UTC')).days
            except:
                days_since_activity = 30  # Default if parsing fails

        # Calculate base score
        visit_score = min(portal_visits * 2, 50)  # Max 50 points for visits
        click_score = min(job_clicks * 5, 100)    # Max 100 points for clicks
        app_score = applications * 20             # 20 points per application

        # Recency penalty (reduce score for inactive agents)
        if days_since_activity > 30:
            recency_factor = 0.5
        elif days_since_activity > 14:
            recency_factor = 0.7
        elif days_since_activity > 7:
            recency_factor = 0.9
        else:
            recency_factor = 1.0

        total_score = (visit_score + click_score + app_score) * recency_factor
        return round(min(total_score, 200), 2)  # Max score of 200

    except Exception as e:
        print(f"Error calculating engagement score: {e}")
        return 0.0

def determine_activity_level(engagement_score: float, days_since_activity: int) -> str:
    """Determine activity level based on engagement and recency"""
    if days_since_activity > 60:
        return 'inactive'
    elif engagement_score >= 100:
        return 'high'
    elif engagement_score >= 50:
        return 'medium'
    elif engagement_score >= 10:
        return 'low'
    else:
        return 'new'

def extract_market_from_agent_location(city: str, state: str) -> str:
    """Extract market from agent location"""
    if not city and not state:
        return "Unknown"

    location_str = f"{city or ''} {state or ''}".lower().strip()

    # Market mapping based on cities/states
    market_mapping = {
        'houston': 'Houston',
        'dallas': 'Dallas',
        'las vegas': 'Las Vegas',
        'bay area': 'Bay Area',
        'stockton': 'Stockton',
        'denver': 'Denver',
        'newark': 'Newark',
        'phoenix': 'Phoenix',
        'trenton': 'Trenton',
        'inland empire': 'Inland Empire',
        'san francisco': 'Bay Area',
        'oakland': 'Bay Area',
        'san jose': 'Bay Area',
        # State-based fallbacks
        'texas': 'Texas',
        'california': 'California',
        'nevada': 'Las Vegas',
        'colorado': 'Denver',
        'arizona': 'Phoenix',
        'new jersey': 'Newark'
    }

    # Check for direct matches
    for key, market in market_mapping.items():
        if key in location_str:
            return market

    # Fallback to state or city
    if state:
        return state.title()
    elif city:
        return city.title()

    return "Unknown"

def analyze_agent_click_patterns(agent_uuid: str, days_back: int = 30) -> Dict:
    """Analyze click patterns for an agent"""
    client = get_client()
    if not client:
        return {}

    try:
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()

        # Get click events for this agent
        result = client.table('click_events').select(
            'clicked_at, company, route, match, fair, market, job_title'
        ).eq('candidate_id', agent_uuid).gte('clicked_at', cutoff_date).execute()

        clicks_data = result.data or []

        if not clicks_data:
            return {
                'companies_clicked': {},
                'route_types_clicked': {},
                'markets_engaged': {},
                'job_qualities_clicked': {},
                'total_clicks': 0
            }

        # Analyze patterns
        companies = Counter(click.get('company', 'Unknown') for click in clicks_data)
        routes = Counter(click.get('route', 'Unknown') for click in clicks_data)
        markets = Counter(click.get('market', 'Unknown') for click in clicks_data)
        qualities = Counter(click.get('match', 'Unknown') for click in clicks_data)

        return {
            'companies_clicked': dict(companies.most_common(10)),
            'route_types_clicked': dict(routes),
            'markets_engaged': dict(markets),
            'job_qualities_clicked': dict(qualities),
            'total_clicks': len(clicks_data)
        }

    except Exception as e:
        print(f"Error analyzing click patterns for {agent_uuid}: {e}")
        return {}

def analyze_free_agents_for_rollup() -> pd.DataFrame:
    """Analyze agent profiles and click data to create analytics rollup"""
    client = get_client()
    if not client:
        raise Exception("Supabase client not available")

    print("👥 Fetching Free Agent data from Supabase...")

    # Get agent profiles with all current data
    result = client.table('agent_profiles').select('*').eq('is_active', True).execute()
    agents_data = result.data or []

    print(f"📊 Analyzing {len(agents_data)} active agents...")

    if not agents_data:
        print("⚠️ No active agents found")
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(agents_data)

    # Enhanced analytics rollup
    agents_rollup = []

    for _, agent in df.iterrows():
        agent_uuid = agent.get('agent_uuid', '')
        if not agent_uuid:
            continue

        # Get click patterns
        click_patterns = analyze_agent_click_patterns(agent_uuid, days_back=30)

        # Extract market from location
        market = extract_market_from_agent_location(
            agent.get('agent_city', ''),
            agent.get('agent_state', '')
        )

        # Calculate engagement metrics
        engagement_score = calculate_engagement_score(agent.to_dict())

        # Determine activity level
        last_activity = agent.get('last_portal_visit') or agent.get('last_job_click')
        days_since_activity = 0
        if last_activity:
            try:
                last_dt = pd.to_datetime(last_activity)
                days_since_activity = (datetime.now(timezone.utc) - last_dt.tz_convert('UTC')).days
            except:
                days_since_activity = 30

        activity_level = determine_activity_level(engagement_score, days_since_activity)

        # Parse route preferences
        route_preferences = {}
        preferred_routes = agent.get('preferred_routes', '')
        if preferred_routes:
            if preferred_routes.lower() in ['local', 'otr', 'regional']:
                route_preferences['primary'] = preferred_routes.lower()
            elif preferred_routes.lower() == 'both':
                route_preferences['primary'] = 'flexible'

        # Parse search config
        search_config = agent.get('search_config', {})
        if isinstance(search_config, str):
            try:
                search_config = json.loads(search_config)
            except:
                search_config = {}

        # Calculate click-through rate
        portal_visits = agent.get('portal_visits', 0) or 0
        job_clicks = agent.get('job_clicks', 0) or 0
        click_through_rate = (job_clicks / portal_visits * 100) if portal_visits > 0 else 0

        agents_rollup.append({
            'agent_uuid': agent_uuid,
            'agent_name': agent.get('agent_name', ''),
            'coach_username': agent.get('coach_username', ''),
            'agent_email': agent.get('agent_email', ''),
            'agent_city': agent.get('agent_city', ''),
            'agent_state': agent.get('agent_state', ''),
            'market': market,

            # Engagement metrics
            'total_portal_visits': portal_visits,
            'total_job_clicks': job_clicks,
            'total_applications': agent.get('total_applications', 0) or 0,

            # Dates
            'first_portal_visit': None,  # Would need historical data
            'last_portal_visit': agent.get('last_portal_visit'),
            'last_job_click': agent.get('last_job_click'),
            'last_application_at': agent.get('last_application_at'),

            # Preferences
            'route_preferences': route_preferences,
            'pathway_preferences': agent.get('pathway_preferences', []) or [],
            'search_config': search_config,

            # Performance metrics
            'click_through_rate': round(click_through_rate, 2),
            'engagement_score': engagement_score,
            'avg_jobs_per_search': 0,  # Would need search history

            # Interaction patterns
            'companies_clicked': click_patterns.get('companies_clicked', {}),
            'route_types_clicked': click_patterns.get('route_types_clicked', {}),
            'markets_engaged': click_patterns.get('markets_engaged', {}),
            'job_qualities_clicked': click_patterns.get('job_qualities_clicked', {}),

            # Status
            'is_active': True,
            'activity_level': activity_level,
            'last_activity_at': last_activity,

            # Coach relationship
            'priority_level': agent.get('priority_level', 'normal'),
            'notes': agent.get('notes', ''),
            'tags': agent.get('tags', []) or [],
        })

    return pd.DataFrame(agents_rollup)

def update_free_agents_analytics_table():
    """Update the free agents analytics table with fresh data"""
    client = get_client()
    if not client:
        raise Exception("Supabase client not available")

    print("👥 UPDATING FREE AGENTS ANALYTICS TABLE")
    print("=" * 50)

    # Analyze agents and create analytics data
    agents_df = analyze_free_agents_for_rollup()

    if agents_df.empty:
        print("⚠️ No agents data to update")
        return

    # Clear existing data and insert new data using upsert
    print(f"📊 Upserting {len(agents_df)} agent analytics...")

    # Convert DataFrame to list of dicts for Supabase
    agents_data = agents_df.to_dict('records')

    # Use upsert to handle existing records
    batch_size = 50
    for i in range(0, len(agents_data), batch_size):
        batch = agents_data[i:i + batch_size]
        try:
            # Use upsert with conflict resolution on agent_uuid
            result = client.table('free_agents_analytics').upsert(
                batch,
                on_conflict='agent_uuid'
            ).execute()
            print(f"✅ Upserted batch {i//batch_size + 1}: {len(batch)} agents")
        except Exception as e:
            print(f"❌ Error in batch {i//batch_size + 1}: {e}")
            # Try individual inserts for this batch
            for record in batch:
                try:
                    client.table('free_agents_analytics').upsert(
                        record,
                        on_conflict='agent_uuid'
                    ).execute()
                except Exception as individual_error:
                    print(f"❌ Failed to upsert agent {record.get('agent_name', 'Unknown')}: {individual_error}")

    print(f"🎉 Free agents analytics table updated successfully!")

    # Print summary
    total_agents = len(agents_df)
    active_agents = (agents_df['activity_level'] != 'inactive').sum()
    high_engagement = (agents_df['activity_level'] == 'high').sum()
    top_markets = agents_df['market'].value_counts().head(5)
    avg_engagement = agents_df['engagement_score'].mean()

    print(f"\n📈 SUMMARY:")
    print(f"   Total Active Agents: {total_agents}")
    print(f"   Recently Active: {active_agents} ({active_agents/total_agents*100:.1f}%)")
    print(f"   High Engagement: {high_engagement} ({high_engagement/total_agents*100:.1f}%)")
    print(f"   Average Engagement Score: {avg_engagement:.1f}")
    print(f"   Top Markets: {dict(top_markets)}")

    return agents_df

def get_free_agents_analytics(coach_username: str = None, limit: int = 50) -> pd.DataFrame:
    """Get free agents analytics with manual JOIN using pandas to get portal URLs and individual fields"""
    client = get_client()
    if not client:
        raise Exception("Supabase client not available")

    # Get analytics data
    analytics_query = client.table('free_agents_analytics').select('*').order('engagement_score', desc=True)

    if coach_username:
        analytics_query = analytics_query.eq('coach_username', coach_username)

    if limit:
        analytics_query = analytics_query.limit(limit)

    analytics_result = analytics_query.execute()
    analytics_df = pd.DataFrame(analytics_result.data or [])

    if analytics_df.empty:
        return analytics_df

    # Get agent profiles for the missing fields (custom_url, location, route_filter, etc.)
    agent_uuids = analytics_df['agent_uuid'].unique().tolist()
    profiles_query = client.table('agent_profiles').select(
        'agent_uuid, custom_url, location, route_filter, fair_chance_only, max_jobs, match_level'
    ).in_('agent_uuid', agent_uuids)

    profiles_result = profiles_query.execute()
    profiles_df = pd.DataFrame(profiles_result.data or [])

    # Merge analytics with agent profiles on agent_uuid
    if not profiles_df.empty:
        merged_df = analytics_df.merge(profiles_df, on='agent_uuid', how='left', suffixes=('', '_profile'))
    else:
        # If no profiles, add empty columns
        merged_df = analytics_df.copy()
        merged_df['custom_url'] = ''
        merged_df['location'] = 'Houston'
        merged_df['route_filter'] = 'both'
        merged_df['fair_chance_only'] = False
        merged_df['max_jobs'] = 25
        merged_df['match_level'] = 'good and so-so'

    return merged_df

def get_high_engagement_agents(coach_username: str = None) -> pd.DataFrame:
    """Get agents with high engagement scores"""
    client = get_client()
    if not client:
        raise Exception("Supabase client not available")

    query = client.table('free_agents_analytics').select('*').eq('activity_level', 'high').order('engagement_score', desc=True)

    if coach_username:
        query = query.eq('coach_username', coach_username)

    result = query.execute()
    return pd.DataFrame(result.data or [])

def get_inactive_agents(coach_username: str = None) -> pd.DataFrame:
    """Get inactive agents that need re-engagement"""
    client = get_client()
    if not client:
        raise Exception("Supabase client not available")

    query = client.table('free_agents_analytics').select('*').eq('activity_level', 'inactive').order('last_activity_at', desc=True)

    if coach_username:
        query = query.eq('coach_username', coach_username)

    result = query.execute()
    return pd.DataFrame(result.data or [])

def get_market_agent_breakdown(market: str) -> pd.DataFrame:
    """Get agents in a specific market"""
    client = get_client()
    if not client:
        raise Exception("Supabase client not available")

    result = client.table('free_agents_analytics').select('*').eq('market', market).order('engagement_score', desc=True).execute()
    return pd.DataFrame(result.data or [])

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Manage free agents analytics table')
    parser.add_argument('--create-table', action='store_true', help='Show SQL to create analytics table')
    parser.add_argument('--update', action='store_true', help='Update analytics data')
    parser.add_argument('--analytics', action='store_true', help='Show agent analytics')
    parser.add_argument('--high-engagement', action='store_true', help='Show high engagement agents')
    parser.add_argument('--inactive', action='store_true', help='Show inactive agents')
    parser.add_argument('--market', help='Show agents in specific market')
    parser.add_argument('--coach', help='Filter by coach username')

    args = parser.parse_args()

    if args.create_table:
        sql = create_free_agents_analytics_table_sql()
        print("🏗️ SQL to create free agents analytics table:")
        print("=" * 60)
        print(sql)

    elif args.update:
        update_free_agents_analytics_table()

    elif args.analytics:
        df = get_free_agents_analytics(coach_username=args.coach)
        print(f"📊 Agent Analytics ({len(df)} agents):")
        if not df.empty:
            display_cols = ['agent_name', 'market', 'activity_level', 'engagement_score', 'total_portal_visits', 'total_job_clicks']
            print(df[display_cols].head(20).to_string(index=False))

    elif args.high_engagement:
        df = get_high_engagement_agents(coach_username=args.coach)
        print(f"🔥 High Engagement Agents ({len(df)} agents):")
        if not df.empty:
            display_cols = ['agent_name', 'market', 'engagement_score', 'total_job_clicks', 'last_activity_at']
            print(df[display_cols].to_string(index=False))

    elif args.inactive:
        df = get_inactive_agents(coach_username=args.coach)
        print(f"😴 Inactive Agents ({len(df)} agents):")
        if not df.empty:
            display_cols = ['agent_name', 'market', 'last_activity_at', 'total_portal_visits', 'total_job_clicks']
            print(df[display_cols].to_string(index=False))

    elif args.market:
        df = get_market_agent_breakdown(args.market)
        print(f"🌍 Agents in {args.market} ({len(df)} agents):")
        if not df.empty:
            display_cols = ['agent_name', 'activity_level', 'engagement_score', 'coach_username']
            print(df[display_cols].to_string(index=False))

    else:
        print("Usage: python free_agents_rollup.py --help")