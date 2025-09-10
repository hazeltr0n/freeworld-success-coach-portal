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
    except (AttributeError, ImportError):
        pass  # Streamlit secrets not available
    
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
                .select('market,match_level,created_at')
                .gte('created_at', since)
                # Include all job quality levels to show complete breakdown
                # .in_('match_level', ['good', 'so-so']) # Removed filter to include bad jobs too
                .range(start, end)
                .order('created_at', desc=True)
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
    """Save agent profile to Supabase agent_profiles table"""
    client = get_client()
    if client is None:
        return False, "Supabase client not available"
    
    try:
        # Prepare data for Supabase
        profile_data = {
            'coach_username': coach_username,
            'agent_uuid': agent_data.get('agent_uuid', ''),
            'agent_name': agent_data.get('agent_name', ''),
            'agent_email': agent_data.get('agent_email', ''),
            'agent_city': agent_data.get('agent_city', ''),
            'agent_state': agent_data.get('agent_state', ''),
            'search_config': {
                'location': agent_data.get('location', 'Houston'),
                'route_filter': agent_data.get('route_filter', 'both'),
                'fair_chance_only': agent_data.get('fair_chance_only', False),
                'max_jobs': agent_data.get('max_jobs', 25),
                'match_level': agent_data.get('match_level', 'good and so-so')
            },
            'custom_url': agent_data.get('custom_url', ''),
            'is_active': True,
            'last_accessed': 'NOW()'
        }
        
        # Only add admin_portal_url if it exists in the input data and is not empty
        # This prevents database errors when the column doesn't exist yet
        if agent_data.get('admin_portal_url'):
            profile_data['admin_portal_url'] = agent_data['admin_portal_url']
        
        # Upsert (insert or update) with fallback for missing admin_portal_url column
        try:
            result = client.table('agent_profiles').upsert(
                profile_data, 
                on_conflict='coach_username,agent_uuid'
            ).execute()
        except Exception as e:
            # If admin_portal_url column doesn't exist, retry without it
            if 'admin_portal_url' in str(e) and 'admin_portal_url' in profile_data:
                print(f"⚠️ Retrying save without admin_portal_url: {e}")
                profile_data_fallback = profile_data.copy()
                del profile_data_fallback['admin_portal_url']
                result = client.table('agent_profiles').upsert(
                    profile_data_fallback,
                    on_conflict='coach_username,agent_uuid'
                ).execute()
            else:
                raise e
        
        return True, None
        
    except Exception as e:
        return False, str(e)

def load_agent_profiles_from_supabase(coach_username: str, include_inactive: bool = False) -> Tuple[List[Dict], str | None]:
    """Load agent profiles for a coach from Supabase"""
    client = get_client()
    if client is None:
        return [], "Supabase client not available"
    
    try:
        # Build query based on whether to include inactive agents
        query_base = client.table('agent_profiles').select(
            'agent_uuid, agent_name, agent_email, agent_city, agent_state, '
            'search_config, custom_url, is_active, created_at, last_accessed, '
            'admin_portal_url'
        ).eq('coach_username', coach_username)
        
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
                'search_config, custom_url, is_active, created_at, last_accessed'
            ).eq('coach_username', coach_username)
            
            if not include_inactive:
                query_base = query_base.eq('is_active', True)
                
            result = query_base.order('created_at', desc=True).execute()
        
        profiles = []
        for row in result.data or []:
            # Flatten search_config into main dict for compatibility
            profile = {
                'agent_uuid': row.get('agent_uuid', ''),
                'agent_name': row.get('agent_name', ''),
                'agent_email': row.get('agent_email', ''),
                'agent_city': row.get('agent_city', ''),
                'agent_state': row.get('agent_state', ''),
                'custom_url': row.get('custom_url', ''),
                'admin_portal_url': row.get('admin_portal_url', ''),
                'created_at': row.get('created_at', ''),
                'last_accessed': row.get('last_accessed', ''),
            }
            
            # Add search config fields
            search_config = row.get('search_config', {})
            profile.update({
                'location': search_config.get('location', 'Houston'),
                'route_filter': search_config.get('route_filter', 'both'),
                'fair_chance_only': search_config.get('fair_chance_only', False),
                'max_jobs': search_config.get('max_jobs', 25),
                'match_level': search_config.get('match_level', 'good and so-so'),
                # Keep experience_level for backward compatibility during transition
                'experience_level': search_config.get('experience_level', 'both')
            })
            
            profiles.append(profile)
        
        return profiles, None
        
    except Exception as e:
        return [], str(e)

def delete_agent_profile_from_supabase(coach_username: str, agent_uuid: str) -> Tuple[bool, str | None]:
    """Delete an agent profile from Supabase (soft delete by marking inactive)"""
    client = get_client()
    if client is None:
        return False, "Supabase client not available"
    
    try:
        # Soft delete by marking inactive
        result = client.table('agent_profiles').update({
            'is_active': False,
            'updated_at': 'NOW()'
        }).eq('coach_username', coach_username).eq('agent_uuid', agent_uuid).execute()
        
        return True, None
        
    except Exception as e:
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

def supabase_find_agents(query: str, coach_username: str, by: str = "name", limit: int = 15) -> List[Dict]:
    """Search agent profiles in Supabase by name, email, or UUID
    
    Args:
        query: Search term
        coach_username: Coach username to filter by
        by: Search field ("name", "uuid", "email")
        limit: Maximum results
        
    Returns:
        List of agent dictionaries in Airtable-compatible format
    """
    client = get_client()
    if not client or not query.strip():
        return []
    
    try:
        print(f"🔍 Supabase search: query='{query}', coach='{coach_username}', by='{by}'")
        
        # Build base query for this coach's agents
        base_query = client.table('agent_profiles').select(
            'agent_uuid, agent_name, agent_email, agent_city, agent_state, '
            'portal_clicks, last_portal_click, created_at, search_config'
        ).eq('coach_username', coach_username).eq('is_active', True)
        
        # Add search filters based on search type
        query_lower = query.strip().lower()
        print(f"🔍 Search term processed: '{query_lower}'")
        
        # Debug: show the base query first
        print(f"🔍 Base query filters: coach_username='{coach_username}', is_active=True")
        
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
                'city': search_config.get('location', '').split(',')[0] if search_config.get('location') else row.get('agent_city', ''),
                'state': row.get('agent_state', ''),
                # Add Supabase-specific data
                'portal_clicks': row.get('portal_clicks', 0) or 0,
                'last_portal_click': row.get('last_portal_click'),
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
                'search_config, custom_url, is_active, created_at, last_accessed, '
                'portal_clicks, last_portal_click, admin_portal_url'
            ).eq('coach_username', coach_username).eq('is_active', True).order(
                'created_at', desc=True
            ).execute()
        except Exception as e:
            print(f"⚠️ admin_portal_url column not found in optimized query, trying without it: {e}")
            profiles_result = client.table('agent_profiles').select(
                'agent_uuid, agent_name, agent_email, agent_city, agent_state, '
                'search_config, custom_url, is_active, created_at, last_accessed, '
                'portal_clicks, last_portal_click'
            ).eq('coach_username', coach_username).eq('is_active', True).order(
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
        
        # Step 3: Get all click events for these agents in ONE query
        from datetime import datetime, timedelta, timezone
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=lookback_days)
        
        clicks_result = client.table('click_events').select(
            'clicked_at, candidate_id, candidate_name, coach, market, route, match, fair, short_id'
        ).in_('candidate_id', agent_uuids).gte(
            'clicked_at', start_date.isoformat()
        ).lte(
            'clicked_at', end_date.isoformat()
        ).execute()
        
        # Step 4: Build click stats lookup by agent_uuid
        click_stats = {}
        recent_cutoff = end_date - timedelta(days=min(7, lookback_days))
        
        for click in (clicks_result.data or []):
            agent_uuid = click.get('candidate_id')
            if not agent_uuid:
                continue
                
            if agent_uuid not in click_stats:
                click_stats[agent_uuid] = {'total': 0, 'recent': 0}
            
            click_stats[agent_uuid]['total'] += 1
            
            # Check if this is a recent click (last 7 days)
            clicked_at = click.get('clicked_at', '')
            if clicked_at > recent_cutoff.isoformat():
                click_stats[agent_uuid]['recent'] += 1
        
        # Step 5: Combine profiles with their click stats
        profiles = []
        for row in profiles_result.data:
            agent_uuid = row.get('agent_uuid', '')
            
            # Format base profile
            profile = _format_agent_profile(row)
            
            # Add click statistics
            stats = click_stats.get(agent_uuid, {'total': 0, 'recent': 0})
            profile.update({
                'total_clicks': stats['total'],
                'recent_clicks': stats['recent'],
                'lookback_days': lookback_days
            })
            
            profiles.append(profile)
        
        return profiles, None
        
    except Exception as e:
        return [], str(e)


def _format_agent_profile(row: Dict) -> Dict:
    """Helper to format agent profile from Supabase row"""
    # Flatten search_config into main dict for compatibility
    profile = {
        'agent_uuid': row.get('agent_uuid', ''),
        'agent_name': row.get('agent_name', ''),
        'agent_email': row.get('agent_email', ''),
        'agent_city': row.get('agent_city', ''),
        'agent_state': row.get('agent_state', ''),
        'custom_url': row.get('custom_url', ''),
        'portal_url': row.get('custom_url', ''),  # Compatibility alias
        'admin_portal_url': row.get('admin_portal_url', ''),
        'created_at': row.get('created_at', ''),
        'last_accessed': row.get('last_accessed', ''),
        'portal_clicks': row.get('portal_clicks', 0) or 0,
        'last_portal_click': row.get('last_portal_click'),
    }
    
    # Add search config fields
    search_config = row.get('search_config', {})
    profile.update({
        'location': search_config.get('location', 'Houston'),
        'route_filter': search_config.get('route_filter', 'both'),
        'fair_chance_only': search_config.get('fair_chance_only', False),
        'max_jobs': search_config.get('max_jobs', 25),
        'match_level': search_config.get('match_level', 'good and so-so'),
        # Keep experience_level for backward compatibility during transition
        'experience_level': search_config.get('experience_level', 'both')
    })
    
    return profile


def instant_memory_search(location: str, search_terms: str = "", hours: int = 72, 
                         coach_username: Optional[str] = None, market: Optional[str] = None,
                         agent_uuid: Optional[str] = None, agent_name: Optional[str] = None) -> List[Dict]:
    """Ultra-fast memory search using clean deduplicated data from Supabase.
    
    This function bypasses the full pipeline for memory-only searches, providing
    sub-second results by querying the deduplicated jobs table directly.
    
    Args:
        location: Location to search for (e.g., "Houston", "Dallas, TX")
        search_terms: Optional search terms (not implemented yet - for future use)
        hours: How many hours back to search (default 72)
        coach_username: Coach username for link generation
        market: Market filter (crucial for R1 deduplication)
        
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
        
        # Direct Supabase query - no pipeline needed!
        query = client.table('jobs').select('*')
        
        # Location filter
        query = query.ilike('location', f'%{location}%')
        
        # Market filter (crucial for R1 deduplication)
        if market:
            query = query.eq('market', market)
        
        # Time filter
        query = query.gte('created_at', cutoff_time.isoformat())
        
        # Quality filter (only good/so-so jobs)
        query = query.in_('match_level', ['good', 'so-so'])
        
        # Execute query
        result = query.execute()
        jobs = result.data or []
        
        print(f"📦 Found {len(jobs)} quality jobs in Supabase memory")
        
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
        
        # Generate tracking URLs with rate limiting
        if jobs and coach_username and agent_uuid:
            print("🔗 Generating Short.io tracking URLs with rate limiting...")
            
            try:
                from link_tracker import LinkTracker
                import time
                
                link_tracker = LinkTracker()
                
                for i, job in enumerate(jobs):
                    # Use apply_url as the base URL for tracking
                    base_url = job.get('apply_url', '') or job.get('indeed_job_url', '') or job.get('clean_apply_url', '')
                    
                    if base_url:
                        # Create tracking tags
                        tags = [
                            f"coach:{coach_username}",
                            f"candidate:{agent_uuid}",
                            f"market:{market or 'unknown'}",
                            "type:job_application"
                        ]
                        
                        # Generate tracked URL
                        try:
                            tracked_url = link_tracker.create_short_link(
                                base_url, 
                                title=f"Job: {job.get('job_title', 'CDL Position')}",
                                tags=tags,
                                candidate_id=agent_uuid
                            )
                            
                            if tracked_url and tracked_url.startswith('https://freeworldjobs.short.gy'):
                                job['tracked_url'] = tracked_url
                            
                            # Rate limiting: 1 second delay every 10 jobs
                            if (i + 1) % 10 == 0:
                                print(f"   Generated {i + 1}/{len(jobs)} tracking URLs... (rate limiting)")
                                time.sleep(1.0)
                                
                        except Exception as e:
                            print(f"   Failed to create tracking URL for job {i + 1}: {e}")
                            continue
                
                tracked_count = sum(1 for job in jobs if job.get('tracked_url'))
                print(f"🔗 Generated {tracked_count}/{len(jobs)} tracking URLs")
                
            except Exception as e:
                print(f"❌ Link generation failed: {e}")
                print("📄 Portal will use original apply URLs directly")
        
        return jobs
        
    except Exception as e:
        print(f"❌ Error in instant memory search: {e}")
        return []
