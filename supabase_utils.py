import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta, timezone
import pandas as pd

try:
    from supabase import create_client, Client
except Exception:
    create_client = None
    Client = None


def get_client() -> "Client | None":
    """Initialize Supabase client from env variables or Streamlit secrets.

    Requires SUPABASE_URL and SUPABASE_ANON_KEY (or service role key if using RLS writes).
    """
    # Check for offline mode first
    offline_mode = os.getenv('OFFLINE_MODE', '').lower() in ('true', '1', 'yes')
    if offline_mode:
        return None
    
    # Try Streamlit secrets first (for deployment)
    url = None
    key = None
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            offline_from_secrets = st.secrets.get("OFFLINE_MODE", "").lower() in ('true', '1', 'yes')
            if offline_from_secrets:
                return None
            url = st.secrets.get("SUPABASE_URL")
            key = st.secrets.get("SUPABASE_ANON_KEY")
    except Exception:
        pass  # Streamlit secrets not available or no secrets file found
    
    # Fallback to environment variables
    if not url or not key:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
    
    # Check if we have dummy/test values (offline mode)
    if url and ('dummy' in url.lower() or 'test' in url.lower()):
        return None
    
    if not (url and key) or create_client is None:
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        # Log the specific error for debugging
        print(f"⚠️  Supabase connection failed: {e}")
        return None


def upsert_candidate_clicks_bulk(rows: List[Dict]) -> Tuple[int, str | None]:
    """Upsert candidate click totals into Supabase.

    Expects rows with keys: candidate_id, candidate_name, clicks
    Returns: (count_written, error)
    """
    client = get_client()
    if client is None:
        return 0, "Supabase client not available"
    try:
        data = [
            {
                "candidate_id": str(r.get("candidate_id", "")),
                "candidate_name": r.get("candidate_name", ""),
                "clicks": int(r.get("clicks", 0)),
            }
            for r in rows
            if r.get("candidate_id")
        ]
        if not data:
            return 0, None
        res = (
            client.table("candidate_clicks")
            .upsert(data, on_conflict="candidate_id")
            .execute()
        )
        count = len(res.data) if getattr(res, "data", None) else len(data)
        return count, None
    except Exception as e:
        return 0, str(e)


def fetch_candidate_clicks(limit: int = 100) -> List[Dict]:
    client = get_client()
    if client is None:
        return []
    
    try:
        res = (
            client.table("candidate_clicks")
            .select("candidate_id,candidate_name,clicks,updated_at")
            .order("clicks", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception:
        return []


def fetch_click_events(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Fetch recent click events for in-app analytics.

    Args:
        start_date: The start datetime for the query.
        end_date: The end datetime for the query.

    Returns:
        A pandas DataFrame with click event data.
    """
    client = get_client()
    if client is None:
        return pd.DataFrame()
    
    try:
        res = (
            client.table("click_events")
            .select("clicked_at,coach,market,route,match,fair,candidate_id,candidate_name,short_id,original_url,job_title,company")
            .gte("clicked_at", start_date.isoformat())
            .lte("clicked_at", end_date.isoformat())
            .order("clicked_at", desc=True)
            .execute()
        )
        
        if not res.data:
            return pd.DataFrame()

        df = pd.DataFrame(res.data)
        df['timestamp'] = pd.to_datetime(df['clicked_at'], format='ISO8601')
        df['click_id'] = df['short_id'] # Use short_id as a unique click identifier
        # Map coach to coach_username for dashboard compatibility
        df['coach_username'] = df['coach']
        return df
    except Exception as e:
        print(f"Error fetching click events: {e}")
        return pd.DataFrame()


def fetch_market_quality_counts(hours: int = 72) -> pd.DataFrame:
    """Return counts of good/so-so jobs per market created in the last N hours.

    Columns returned:
      - market
      - good
      - so_so
      - total
    """
    client = get_client()
    if client is None:
        return pd.DataFrame()

    try:
        since = (datetime.now(timezone.utc) - timedelta(hours=int(hours))).isoformat()
        # Fetch filtered rows and aggregate client-side to avoid PostgREST aggregate limits
        rows_all = []
        page = 0
        page_size = 1000
        while True:
            start = page * page_size
            end = start + page_size - 1
            res = (
                client
                .table('jobs')
                .select('market,match_level,updated_at')
                .gte('updated_at', since)
                # Include all job quality levels to show complete breakdown
                # .in_('match_level', ['good', 'so-so']) # Removed filter to include bad jobs too
                .range(start, end)
                .order('updated_at', desc=True)
                .execute()
            )
            batch = res.data or []
            if not batch:
                break
            rows_all.extend(batch)
            if len(batch) < page_size:
                break
            page += 1
        if not rows_all:
            return pd.DataFrame(columns=['market', 'good', 'so_so', 'bad', 'quality_total', 'grand_total'])

        df = pd.DataFrame(rows_all)
        # Group and pivot
        grp = df.groupby(['market', 'match_level']).size().reset_index(name='count')
        pivot = grp.pivot_table(index='market', columns='match_level', values='count', aggfunc='sum').fillna(0)
        pivot = pivot.rename(columns={'so-so': 'so_so'})
        
        # Ensure all quality level columns exist
        for col in ['good', 'so_so', 'bad']:
            if col not in pivot.columns:
                pivot[col] = 0
        
        # Calculate totals
        pivot['quality_total'] = pivot['good'] + pivot['so_so']  # Good + so-so (quality jobs)
        pivot['grand_total'] = pivot['good'] + pivot['so_so'] + pivot['bad']  # All jobs
        
        # Select columns to return (include bad jobs now)
        pivot = pivot[['good', 'so_so', 'bad', 'quality_total', 'grand_total']].reset_index()
        return pivot.sort_values(['grand_total', 'market'], ascending=[False, True])
    except Exception as e:
        print(f"Error fetching market quality counts: {e}")
        return pd.DataFrame(columns=['market', 'good', 'so_so', 'bad', 'quality_total', 'grand_total'])


# =============== Coach persistence (optional) ===============
def _coaches_table(client):
    try:
        return client.table("coaches")
    except Exception:
        return None


def load_coaches_json() -> Dict[str, Dict]:
    """Load coaches stored as JSON rows from Supabase table 'coaches'.

    Schema:
      coaches(username text primary key, data jsonb)
    """
    client = get_client()
    if client is None:
        return {}
    try:
        tbl = _coaches_table(client)
        if tbl is None:
            return {}
        res = tbl.select("username,data").limit(1000).execute()
        rows = res.data or []
        return {r.get("username"): (r.get("data") or {}) for r in rows}
    except Exception as e:
        return {}


def upsert_coaches_json(coaches: Dict[str, Dict]) -> Tuple[int, str | None]:
    """Upsert coaches into 'coaches' table as JSON.

    Returns: (count_upserted, error)
    """
    client = get_client()
    if client is None:
        return 0, "Supabase client not available"
    try:
        tbl = _coaches_table(client)
        if tbl is None:
            return 0, "coaches table not available"
        payload = [{"username": k, "data": v} for k, v in coaches.items()]
        if not payload:
            return 0, None
        res = tbl.upsert(payload, on_conflict="username").execute()
        count = len(res.data) if getattr(res, "data", None) else len(payload)
        return count, None
    except Exception as e:
        return 0, str(e)


def delete_coach_row(username: str) -> Tuple[bool, str | None]:
    client = get_client()
    if client is None:
        return False, "Supabase client not available"
    try:
        tbl = _coaches_table(client)
        if tbl is None:
            return False, "coaches table not available"
        res = tbl.delete().eq("username", username).execute()
        return True, None
    except Exception as e:
        return False, str(e)


# =============== Agent Profiles Management ===============

def save_agent_profile_to_supabase(coach_username: str, agent_data: Dict) -> Tuple[bool, str | None]:
    """
    Save agent profile to Supabase agent_profiles table (multi-coach system)

    In the new system:
    - agent_profiles table has one record per agent_uuid (not per coach)
    - agent_coaches junction table maps many coaches to many agents
    - coach_usernames array in agent_profiles provides quick filtering
    """
    client = get_client()
    if client is None:
        return False, "Supabase client not available"

    try:
        agent_uuid = agent_data.get('agent_uuid', '')

        # First, check if this agent already exists
        existing = client.table('agent_profiles').select('agent_uuid, coach_usernames').eq('agent_uuid', agent_uuid).execute()

        # Prepare data for Supabase (NO coach_username field anymore!)
        profile_data = {
            'agent_uuid': agent_uuid,
            'agent_name': agent_data.get('agent_name', ''),
            'agent_email': agent_data.get('agent_email', ''),
            'agent_city': agent_data.get('agent_city', ''),
            'agent_state': agent_data.get('agent_state', ''),
            # Use individual fields instead of search_config JSON
            'location': agent_data.get('location', 'Houston'),
            'route_filter': agent_data.get('route_filter', 'both'),
            'fair_chance_only': agent_data.get('fair_chance_only', False),
            'max_jobs': agent_data.get('max_jobs', 25),
            'match_level': agent_data.get('match_level', 'good and so-so'),
            'show_prepared_for': agent_data.get('show_prepared_for', True),
            # ZIP code radius filtering fields
            'zip_code': agent_data.get('zip_code', ''),
            'zip_radius_miles': agent_data.get('zip_radius_miles', 25),
            # Lookback hours field
            'lookback_hours': agent_data.get('lookback_hours', 72),
            # Keep search_config for backward compatibility during transition
            'search_config': {
                'location': agent_data.get('location', 'Houston'),
                'route_filter': agent_data.get('route_filter', 'both'),
                'fair_chance_only': agent_data.get('fair_chance_only', False),
                'max_jobs': agent_data.get('max_jobs', 25),
                'match_level': agent_data.get('match_level', 'good and so-so')
            },
            'pathway_preferences': agent_data.get('pathway_preferences', []),
            'custom_url': agent_data.get('custom_url', ''),
            'original_long_url': agent_data.get('original_long_url', ''),  # Store encoded Supabase portal URL
            'is_active': True,
            'last_accessed': 'NOW()'
        }

        # Handle coach_usernames array: add current coach if not already present
        if existing.data:
            # Agent exists - update coach_usernames array
            current_coaches = existing.data[0].get('coach_usernames', []) or []
            if coach_username not in current_coaches:
                current_coaches.append(coach_username)
                profile_data['coach_usernames'] = current_coaches
                print(f"✅ Adding {coach_username} to existing agent {agent_uuid} (coaches: {current_coaches})")
            else:
                profile_data['coach_usernames'] = current_coaches
                print(f"ℹ️ Coach {coach_username} already assigned to agent {agent_uuid}")
        else:
            # New agent - initialize with current coach
            profile_data['coach_usernames'] = [coach_username]
            print(f"✅ Creating new agent {agent_uuid} with coach {coach_username}")

        # Only add admin_portal_url if it exists in the input data and is not empty
        if agent_data.get('admin_portal_url'):
            profile_data['admin_portal_url'] = agent_data['admin_portal_url']

        # Upsert (insert or update) based on agent_uuid only
        try:
            result = client.table('agent_profiles').upsert(
                profile_data,
                on_conflict='agent_uuid'  # Changed from 'coach_username,agent_uuid'
            ).execute()
        except Exception as e:
            # If admin_portal_url column doesn't exist, retry without it
            if 'admin_portal_url' in str(e) and 'admin_portal_url' in profile_data:
                print(f"⚠️ Retrying save without admin_portal_url: {e}")
                profile_data_fallback = profile_data.copy()
                del profile_data_fallback['admin_portal_url']
                result = client.table('agent_profiles').upsert(
                    profile_data_fallback,
                    on_conflict='agent_uuid'
                ).execute()
            else:
                raise e

        # Also create/update entry in agent_coaches junction table (for multi-coach support)
        try:
            junction_data = {
                'agent_uuid': agent_uuid,
                'coach_username': coach_username,
                'is_active': True,
                'assigned_at': 'NOW()'
            }
            client.table('agent_coaches').upsert(
                junction_data,
                on_conflict='agent_uuid,coach_username'
            ).execute()
            print(f"✅ Updated agent_coaches junction table for {coach_username} → {agent_uuid}")
        except Exception as junction_error:
            print(f"⚠️ agent_coaches junction table error: {junction_error}")

        return True, None

    except Exception as e:
        return False, str(e)

def load_agent_profiles_from_supabase(coach_username: str, include_inactive: bool = False) -> Tuple[List[Dict], str | None]:
    """Load agent profiles for a coach from Supabase (multi-coach system)"""
    client = get_client()
    if client is None:
        return [], "Supabase client not available"

    try:
        # Build query - filter by coach_usernames array containing this coach
        query_base = client.table('agent_profiles').select(
            'agent_uuid, agent_name, agent_email, agent_city, agent_state, '
            'location, route_filter, fair_chance_only, max_jobs, match_level, '
            'search_config, custom_url, pathway_preferences, is_active, created_at, last_accessed, '
            'admin_portal_url, lookback_hours, zip_code, zip_radius_miles, show_prepared_for, original_long_url, coach_usernames'
        ).contains('coach_usernames', [coach_username])  # Filter by array membership
        
        # Only filter by is_active if we don't want to include inactive agents
        if not include_inactive:
            query_base = query_base.eq('is_active', True)
        
        # Try with admin_portal_url first, fallback without it if column doesn't exist
        try:
            result = query_base.order('created_at', desc=True).execute()
        except Exception as e:
            # If admin_portal_url column doesn't exist, try without it
            print(f"⚠️ admin_portal_url column not found, trying without it: {e}")
            query_base = client.table('agent_profiles').select(
                'agent_uuid, agent_name, agent_email, agent_city, agent_state, '
                'location, route_filter, fair_chance_only, max_jobs, match_level, '
                'search_config, custom_url, pathway_preferences, is_active, created_at, last_accessed, '
                'lookback_hours, coach_usernames'
            ).contains('coach_usernames', [coach_username])  # Filter by array membership
            
            if not include_inactive:
                query_base = query_base.eq('is_active', True)
                
            result = query_base.order('created_at', desc=True).execute()
        
        profiles = []
        for row in result.data or []:
            # Use centralized formatter to ensure all fields are included
            profile = _format_agent_profile(row)
            # Override with pathway_preferences which might be in the row
            if 'pathway_preferences' in row:
                profile['pathway_preferences'] = row.get('pathway_preferences', [])
            
            profiles.append(profile)
        
        return profiles, None
        
    except Exception as e:
        return [], str(e)

def delete_agent_profile_from_supabase(coach_username: str, agent_uuid: str) -> Tuple[bool, str | None]:
    """Soft-delete an agent profile by setting is_active=False

    This marks the agent as inactive rather than hard-deleting the record.
    Preserves historical data and allows for recovery.
    """
    client = get_client()
    if client is None:
        return False, "Supabase client not available"

    try:
        # Soft delete: Set is_active=False on the agent profile
        result = client.table('agent_profiles').update({
            'is_active': False
        }).eq('agent_uuid', agent_uuid).execute()

        if result.data:
            print(f"✅ Agent profile soft-deleted (is_active=False): {agent_uuid}")
            return True, None
        else:
            print(f"❌ No agent found with UUID: {agent_uuid}")
            return False, "Agent not found"

    except Exception as e:
        print(f"❌ Error soft-deleting agent: {e}")
        return False, str(e)

def update_agent_last_accessed(agent_uuid: str) -> Tuple[bool, str | None]:
    """Update the last_accessed timestamp for an agent"""
    client = get_client()
    if client is None:
        return False, "Supabase client not available"
    
    try:
        result = client.table('agent_profiles').update({
            'last_accessed': 'NOW()'
        }).eq('agent_uuid', agent_uuid).execute()
        
        return True, None
        
    except Exception as e:
        return False, str(e)

def supabase_find_agents(query: str, coach_username: str, by: str = "name", limit: int = 15, filter_by_coach: bool = False) -> List[Dict]:
    """Search agent profiles in Supabase by name, email, or UUID

    Args:
        query: Search term
        coach_username: Coach username to filter by (if filter_by_coach=True)
        by: Search field ("name", "uuid", "email")
        limit: Maximum results
        filter_by_coach: If True, only return agents for this coach. If False, search ALL agents.

    Returns:
        List of agent dictionaries in Airtable-compatible format
    """
    client = get_client()
    if not client or not query.strip():
        return []

    try:
        filter_msg = f"coach='{coach_username}'" if filter_by_coach else "ALL agents"
        print(f"🔍 Supabase search: query='{query}', by='{by}', filter={filter_msg}")

        # Build base query - optionally filter by coach
        base_query = client.table('agent_profiles').select(
            'agent_uuid, agent_name, agent_email, agent_city, agent_state, '
            'location, route_filter, fair_chance_only, max_jobs, match_level, '
            'created_at, search_config, lookback_hours, coach_usernames'
        ).eq('is_active', True)

        # Apply coach filter if requested
        if filter_by_coach:
            base_query = base_query.contains('coach_usernames', [coach_username])
            print(f"🔍 Filtering by coach: {coach_username}")

        # Add search filters based on search type
        query_lower = query.strip().lower()
        print(f"🔍 Search term processed: '{query_lower}'")

        if by == "uuid":
            # UUID search (case insensitive)
            print(f"🔍 UUID search: ilike agent_uuid '%{query_lower}%'")
            result = base_query.ilike('agent_uuid', f'%{query_lower}%').limit(limit).execute()
        elif by == "email":
            # Email search (case insensitive)
            print(f"🔍 Email search: ilike agent_email '%{query_lower}%'")
            result = base_query.ilike('agent_email', f'%{query_lower}%').limit(limit).execute()
        else:  # by == "name" or default
            # Name search using the same pattern as working memory search
            print(f"🔍 Name search: searching agent_name for '{query_lower}'")
            print(f"🔍 Using ILIKE pattern: agent_name ILIKE '%{query_lower}%'")
            result = base_query.ilike('agent_name', f'%{query_lower}%').limit(limit).execute()
        
        print(f"🔍 Supabase query result: {len(result.data or [])} rows")
        
        # Convert to Airtable-compatible format
        agents = []
        for row in result.data or []:
            search_config = row.get('search_config', {})
            
            agent = {
                'name': row.get('agent_name', ''),
                'uuid': row.get('agent_uuid', ''),
                'email': row.get('agent_email', ''),
                'city': (row.get('location', '') or search_config.get('location', '')).split(',')[0] if (row.get('location') or search_config.get('location')) else row.get('agent_city', ''),
                'state': row.get('agent_state', ''),
                'created_at': row.get('created_at'),
                'source': 'supabase'  # Mark as Supabase source
            }
            agents.append(agent)
        
        print(f"🔍 Processed {len(agents)} agents for return")
        for agent in agents[:3]:  # Show first 3
            print(f"   - {agent['name']} | {agent['uuid']}")
        
        return sorted(agents, key=lambda x: x['name'].lower())
        
    except Exception as e:
        print(f"❌ Supabase agent search failed: {e}")
        return []


def fetch_coach_agents_with_stats(coach_username: str, lookback_days: int = 14) -> Tuple[List[Dict], str | None]:
    """Optimized batch loading of agent profiles with click statistics for a coach.
    
    This replaces the inefficient pattern of:
    1. Loading agent profiles individually
    2. Fetching ALL click events for each agent separately
    
    With a single optimized query that:
    1. Gets all agent profiles for the coach
    2. Gets all click events for those agents in one query
    3. Aggregates stats client-side efficiently
    
    Args:
        coach_username: The coach's username
        lookback_days: How many days back to look for click stats
        
    Returns:
        Tuple of (agent_profiles_with_stats, error_message)
    """
    client = get_client()
    if client is None:
        return [], "Supabase client not available"
    
    try:
        # Step 1: Get all agent profiles for this coach
        # Try with admin_portal_url first, fallback without it if column doesn't exist
        try:
            profiles_result = client.table('agent_profiles').select(
                'agent_uuid, agent_name, agent_email, agent_city, agent_state, '
                'location, route_filter, fair_chance_only, max_jobs, match_level, '
                'search_config, custom_url, is_active, created_at, last_accessed, '
                'portal_clicks, last_portal_click, admin_portal_url, show_prepared_for, lookback_hours, '
                'zip_code, zip_radius_miles'
            ).contains('coach_usernames', [coach_username]).eq('is_active', True).order(
                'created_at', desc=True
            ).execute()
        except Exception as e:
            print(f"⚠️ admin_portal_url column not found in optimized query, trying without it: {e}")
            profiles_result = client.table('agent_profiles').select(
                'agent_uuid, agent_name, agent_email, agent_city, agent_state, '
                'location, route_filter, fair_chance_only, max_jobs, match_level, '
                'search_config, custom_url, is_active, created_at, last_accessed, '
                'portal_clicks, last_portal_click, show_prepared_for, lookback_hours, '
                'zip_code, zip_radius_miles'
            ).contains('coach_usernames', [coach_username]).eq('is_active', True).order(
                'created_at', desc=True
            ).execute()
        
        if not profiles_result.data:
            return [], None
        
        # Step 2: Extract agent UUIDs for batch click event query
        agent_uuids = [profile['agent_uuid'] for profile in profiles_result.data if profile.get('agent_uuid')]
        
        if not agent_uuids:
            # Return profiles with zero stats if no UUIDs
            profiles = []
            for row in profiles_result.data:
                profile = _format_agent_profile(row)
                profile.update({
                    'total_clicks': 0,
                    'recent_clicks': 0,
                    'lookback_days': lookback_days
                })
                profiles.append(profile)
            return profiles, None
        
        # Step 3: Get ALL click events for these agents - NO TIME LIMITS
        from datetime import datetime, timedelta, timezone

        # Use the free_agents_analytics table for fast, indexed click stats
        print("📊 Using optimized analytics table for click statistics...")

        try:
            analytics_result = client.table('free_agents_analytics').select(
                'agent_uuid, total_job_clicks, total_portal_visits, total_applications, '
                'last_job_click, last_portal_visit, last_application_at'
            ).contains('coach_usernames', [coach_username]).eq('is_active', True).execute()

            analytics_data = analytics_result.data or []
            print(f"📈 Found analytics data for {len(analytics_data)} agents")

        except Exception as e:
            print(f"⚠️ Analytics table not available ({e}), falling back to direct query...")
            analytics_data = []
        
        # Step 4: Build analytics stats lookup by agent_uuid from pre-computed analytics table
        analytics_stats = {}
        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=7)

        for analytics_row in analytics_data:
            agent_uuid = analytics_row.get('agent_uuid')
            if not agent_uuid:
                continue

            # Use pre-computed totals from analytics table
            total_clicks = analytics_row.get('total_job_clicks', 0) or 0

            # For recent clicks, we need to calculate based on last_job_click timestamp
            recent_clicks = 0
            last_click_str = analytics_row.get('last_job_click', '')
            if last_click_str:
                try:
                    last_click = datetime.fromisoformat(last_click_str.replace('Z', '+00:00'))
                    if last_click > recent_cutoff:
                        # If last click was recent, use total_job_clicks as approximation
                        # This is not perfect but avoids the expensive query
                        recent_clicks = min(total_clicks, 10)  # Cap at reasonable number
                except (ValueError, TypeError):
                    recent_clicks = 0

            analytics_stats[agent_uuid] = {
                'total': total_clicks,
                'recent': recent_clicks,
                'applications': analytics_row.get('total_applications', 0) or 0
            }
        
        # Step 5: Combine profiles with their click stats
        profiles = []
        for row in profiles_result.data:
            agent_uuid = row.get('agent_uuid', '')
            
            # Format base profile
            profile = _format_agent_profile(row)
            
            # Add click statistics from analytics table or fallback to zero
            stats = analytics_stats.get(agent_uuid, {'total': 0, 'recent': 0, 'applications': 0})
            profile.update({
                'total_clicks': stats['total'],
                'recent_clicks': stats['recent'],
                'total_applications': stats['applications'],
                'lookback_days': lookback_days
            })
            
            profiles.append(profile)
        
        return profiles, None
        
    except Exception as e:
        return [], str(e)


def get_free_agents_analytics_data(coach_username=None):
    """Get free agents analytics data with all-time and 14-day metrics"""
    client = get_client()
    if not client:
        print("❌ Supabase client not available")
        return pd.DataFrame()

    try:
        query = client.table('free_agents_analytics').select('*').order('total_job_clicks', desc=True)

        if coach_username:
            query = query.contains('coach_usernames', [coach_username])

        result = query.execute()
        df = pd.DataFrame(result.data or [])
        print(f"✅ Loaded {len(df)} agents from analytics table")
        return df

    except Exception as e:
        print(f"❌ Error loading analytics data: {e}")
        return pd.DataFrame()


def get_system_wide_agent_stats():
    """Get system-wide Free Agent statistics across all coaches"""
    client = get_client()
    if not client:
        print("❌ Supabase client not available")
        return {
            'total_agents': 0,
            'total_clicks_all_time': 0,
            'active_agents_14d': 0,
            'avg_clicks_per_agent': 0.0
        }

    try:
        # Get all analytics data (no coach filter for system-wide stats)
        analytics_result = client.table('free_agents_analytics').select('*').execute()

        if not analytics_result.data:
            print("📊 No analytics data found for system-wide stats")
            return {
                'total_agents': 0,
                'total_clicks_all_time': 0,
                'active_agents_14d': 0,
                'avg_clicks_per_agent': 0.0
            }

        analytics_df = pd.DataFrame(analytics_result.data)
        print(f"📊 Calculating system-wide stats from {len(analytics_df)} total agents")

        # Calculate total agents and 14-day active agents from analytics table
        total_agents = len(analytics_df)
        active_agents_14d = len(analytics_df[analytics_df.get('job_clicks_14d', 0) > 0]) if 'job_clicks_14d' in analytics_df.columns else 0

        # Query ALL click events for accurate all-time total (not just active agents)
        try:
            print("📊 Querying ALL click events for accurate system-wide total...")
            all_clicks_result = client.table('click_events').select('id', count='exact').execute()
            total_clicks_all_time = all_clicks_result.count if hasattr(all_clicks_result, 'count') else 0
            print(f"📊 Total clicks from ALL events: {total_clicks_all_time}")
        except Exception as e:
            print(f"⚠️ Could not query all click events, falling back to analytics table: {e}")
            total_clicks_all_time = analytics_df['total_job_clicks'].sum() if 'total_job_clicks' in analytics_df.columns else 0

        # Calculate average using ALL clicks divided by total agents
        avg_clicks_per_agent = total_clicks_all_time / total_agents if total_agents > 0 else 0.0

        system_stats = {
            'total_agents': total_agents,
            'total_clicks_all_time': int(total_clicks_all_time),
            'active_agents_14d': active_agents_14d,
            'avg_clicks_per_agent': avg_clicks_per_agent
        }

        print(f"📊 System-wide stats: {system_stats}")
        return system_stats

    except Exception as e:
        print(f"❌ Error getting system-wide stats: {e}")
        return {
            'total_agents': 0,
            'total_clicks_all_time': 0,
            'active_agents_14d': 0,
            'avg_clicks_per_agent': 0.0
        }


def refresh_free_agents_analytics_manual():
    """Manually trigger the free agents analytics refresh - using Python fallback if SQL function fails"""
    client = get_client()
    if not client:
        return {"success": False, "error": "Supabase client not available"}

    try:
        print("🔄 Calling Supabase refresh_free_agents_analytics() function...")
        result = client.rpc('refresh_free_agents_analytics').execute()

        if result.data and isinstance(result.data, dict):
            print(f"✅ Analytics refresh result: {result.data}")
            return result.data
        else:
            return {"success": True, "message": "Analytics refresh completed"}

    except Exception as e:
        error_msg = str(e)
        print(f"❌ SQL function failed: {error_msg}")
        print("🔄 Falling back to Python-based refresh...")

        try:
            # Fallback: Use Python-based refresh
            from free_agents_rollup import update_free_agents_analytics_table
            update_free_agents_analytics_table()
            return {"success": True, "message": "Analytics refreshed via Python fallback", "fallback": True}
        except Exception as fallback_error:
            print(f"❌ Python fallback also failed: {fallback_error}")
            return {"success": False, "error": f"Both SQL and Python refresh failed: {error_msg}"}


def _format_agent_profile(row: Dict) -> Dict:
    """Helper to format agent profile from Supabase row"""
    # Start with ALL fields from the row
    profile = dict(row)

    # Add compatibility alias
    if 'custom_url' in profile and 'portal_url' not in profile:
        profile['portal_url'] = profile['custom_url']

    # Flatten search_config for backward compatibility
    # Use individual fields primarily, with JSON as backup
    search_config = row.get('search_config', {})

    # Only set these if they're not already present as individual fields
    if 'location' not in profile or not profile['location']:
        profile['location'] = search_config.get('location', 'Houston')
    if 'route_filter' not in profile or not profile['route_filter']:
        profile['route_filter'] = search_config.get('route_filter', 'both')
    if 'fair_chance_only' not in profile or profile['fair_chance_only'] is None:
        profile['fair_chance_only'] = search_config.get('fair_chance_only', False)
    if 'max_jobs' not in profile or not profile['max_jobs']:
        profile['max_jobs'] = search_config.get('max_jobs', 25)
    if 'match_level' not in profile or not profile['match_level']:
        profile['match_level'] = search_config.get('match_level', 'good and so-so')

    # Keep experience_level for backward compatibility
    if 'experience_level' not in profile:
        profile['experience_level'] = search_config.get('experience_level', 'both')

    # Ensure portal_clicks is never None
    if profile.get('portal_clicks') is None:
        profile['portal_clicks'] = 0

    return profile


def instant_memory_search(location: str, search_terms: str = "", hours: int = 72,
                         coach_username: Optional[str] = None, market: Optional[str] = None,
                         agent_uuid: Optional[str] = None, agent_name: Optional[str] = None,
                         pathway_preferences: Optional[List[str]] = None,
                         agent_zip: Optional[str] = None, zip_radius_miles: Optional[int] = None,
                         route_filter: Optional[str] = None, match_level: Optional[str] = None) -> List[Dict]:
    """Ultra-fast memory search using clean deduplicated data from Supabase.

    This function bypasses the full pipeline for memory-only searches, providing
    sub-second results by querying the deduplicated jobs table directly.

    Args:
        location: Location to search for (e.g., "Houston", "Dallas, TX")
        search_terms: Optional search terms (not implemented yet - for future use)
        hours: How many hours back to search (default 72)
        coach_username: Coach username for link generation
        market: Market filter (crucial for R1 deduplication)
        agent_uuid: Agent UUID for tracking
        agent_name: Agent name for tracking
        pathway_preferences: List of career pathways to filter by (e.g., ['cdl_pathway', 'dock_to_driver'])
        agent_zip: Agent's ZIP code for radius filtering
        zip_radius_miles: Search radius in miles from agent ZIP

    Returns:
        List of job dictionaries ready for display/export
    """
    client = get_client()
    if client is None:
        print("❌ Supabase client not available")
        return []
    
    try:
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        print(f"🔍 Instant memory search: location='{location}', market='{market}', hours={hours}")
        
        # Get reported job URLs to exclude them
        reported_jobs_result = client.table('job_feedback').select('job_url').execute()
        reported_urls = {job['job_url'] for job in (reported_jobs_result.data or [])}
        print(f"🚫 Excluding {len(reported_urls)} reported jobs from memory search")
        
        # Direct Supabase query - no pipeline needed!
        query = client.table('jobs').select('*')
        
        # Exclude reported jobs (if any exist)
        if reported_urls:
            # Supabase doesn't have NOT IN, so we'll filter after retrieval
            pass  # We'll filter these out after getting results

        # Market filter FIRST (crucial for performance and R1 deduplication)
        # Use provided market parameter, otherwise fall back to location
        market_value = market or location
        query = query.eq('market', market_value)

        # Time filter - use updated_at to catch renewed/active jobs
        query = query.gte('updated_at', cutoff_time.isoformat())

        # Quality filter - use agent preference or default to good/so-so
        # Parse match_level string into list (handles "good and so-so and bad" format)
        match_levels = ['good', 'so-so']  # default
        if match_level:
            if isinstance(match_level, list):
                match_levels = match_level
            elif ' and ' in match_level:
                match_levels = [m.strip() for m in match_level.split(' and ')]
            elif match_level in ['good', 'so-so', 'bad']:
                match_levels = [match_level]
            elif match_level == 'both':
                match_levels = ['good', 'so-so']

        query = query.in_('match_level', match_levels)
        include_bad = 'bad' in match_levels

        # Enhanced feedback filtering
        # Exclude permanently flagged jobs
        query = query.eq('job_flagged', False)

        # For expired feedback, we'll use simpler database-level filtering
        # Exclude jobs with recent expired feedback (within 72 hours)
        expired_cutoff = (datetime.utcnow() - timedelta(hours=72)).isoformat()

        # Use Supabase's OR filtering to exclude jobs with recent expired feedback
        # Include jobs where: last_expired_feedback_at IS NULL OR last_expired_feedback_at < cutoff
        query = query.or_(f'last_expired_feedback_at.is.null,last_expired_feedback_at.lt.{expired_cutoff}')

        # Route type filtering - use agent preference
        if route_filter:
            if route_filter.lower() == 'local':
                print(f"🚚 Filtering to LOCAL routes only")
                query = query.eq('route_type', 'Local')
            elif route_filter.lower() == 'otr':
                print(f"🚛 Filtering to OTR/Regional routes only")
                query = query.in_('route_type', ['OTR', 'Regional'])
            # If 'both' or unrecognized, no filter applied (show all route types)

        # Career pathway filtering
        if pathway_preferences:
            print(f"🛤️ Filtering by pathway preferences: {pathway_preferences}")
            query = query.in_('career_pathway', pathway_preferences)

        # Execute query
        result = query.execute()
        jobs = result.data or []
        
        # Filter out reported jobs
        if reported_urls:
            jobs_before = len(jobs)
            jobs = [job for job in jobs if job.get('apply_url') not in reported_urls]
            jobs_filtered = jobs_before - len(jobs)
            if jobs_filtered > 0:
                print(f"🚫 Filtered out {jobs_filtered} reported jobs")

        # Filter out owner-operator and school bus jobs when showing 'bad' jobs
        # These are unsuitable even for experienced drivers
        if include_bad:
            EXCLUDE_PATTERNS = ['own truck', 'owner', '1099', 'lease purchase', 'school bus', 'own vehicle']
            jobs_before = len(jobs)
            jobs = [
                job for job in jobs
                if not any(pattern in (job.get('match_reason') or '').lower() for pattern in EXCLUDE_PATTERNS)
            ]
            jobs_filtered = jobs_before - len(jobs)
            if jobs_filtered > 0:
                print(f"🚫 Filtered out {jobs_filtered} owner-operator/school bus jobs from 'bad' results")

        # ZIP radius filtering (agent-level location filtering)
        if agent_zip and zip_radius_miles:
            print(f"📍 Applying ZIP radius filter: {agent_zip} within {zip_radius_miles} miles")
            from zip_radius_filter import filter_jobs_by_zip_radius
            jobs_before = len(jobs)
            jobs = filter_jobs_by_zip_radius(jobs, agent_zip, zip_radius_miles)
            jobs_filtered = jobs_before - len(jobs)
            if jobs_filtered > 0:
                print(f"📍 Filtered out {jobs_filtered} jobs outside radius")

        # Expired feedback filtering is now handled at database level

        print(f"📦 Found {len(jobs)} quality jobs in Supabase memory (after all filtering)")

        # Always include inside_track jobs for this market (partner opportunities bypass filters)
        inside_track_query = client.table('jobs').select('*').eq('source', 'inside_track').eq('market', market_value).eq('filter_reason', 'included: inside_track')
        inside_track_result = inside_track_query.execute()
        inside_track_jobs = inside_track_result.data or []
        if inside_track_jobs:
            # Add inside track jobs that aren't already in results
            existing_job_ids = {j.get('job_id') for j in jobs}
            new_inside_track = [j for j in inside_track_jobs if j.get('job_id') not in existing_job_ids]
            if new_inside_track:
                jobs = new_inside_track + jobs  # Put partner jobs at the top
                print(f"🤝 Added {len(new_inside_track)} inside track partner jobs to results")

        # EXPORT CSV FIRST - before any link generation bullshit
        if jobs:
            import pandas as pd
            from datetime import datetime
            
            df = pd.DataFrame(jobs)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_filename = f"memory_search_raw_{location.replace(' ', '_')}_{timestamp}.csv"
            csv_path = f"/tmp/{csv_filename}"
            df.to_csv(csv_path, index=False)
            print(f"💾 EXPORTED RAW MEMORY DATA: {csv_path}")
            print(f"📋 Available fields: {list(df.columns)}")
            
            # Show URL field status
            url_fields = [col for col in df.columns if 'url' in col.lower() or 'apply' in col.lower()]
            print(f"🔗 URL fields found: {url_fields}")
            for field in url_fields:
                non_empty = df[field].notna().sum()
                print(f"   {field}: {non_empty}/{len(df)} jobs have values")
        
        # Use existing tracked URLs from database (no Short.io wrapping)
        # Jobs already have Supabase edge function URLs from pipeline stage 7
        # This avoids creating duplicate Short.io links on every portal access

        return jobs
        
    except Exception as e:
        print(f"❌ Error in instant memory search: {e}")
        return []
