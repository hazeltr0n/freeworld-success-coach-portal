#!/usr/bin/env python3
"""
Free Agent Management System
Handles URL encoding/decoding, agent management, and job feed generation
Uses existing pipeline without modifications
"""

import base64
import json
from typing import Dict, List, Any, Tuple
import pandas as pd
from datetime import datetime, timezone
import streamlit as st

def encode_agent_params(params: Dict[str, Any]) -> str:
    """Encode agent parameters into a URL-safe string"""
    param_map = {
        'agent_uuid': params.get('agent_uuid', ''),
        'agent_name': params.get('agent_name', ''),
        'location': params.get('location', 'Houston'),  # Just city name
        'route_filter': params.get('route_filter', 'both'),  # local/otr/both
        'fair_chance_only': params.get('fair_chance_only', False),
        'max_jobs': params.get('max_jobs', 25),  # 15/25/50/100
        'match_level': params.get('match_level', 'good and so-so'),  # good/so-so/good and so-so/all
        'coach_username': params.get('coach_username', ''),
    }
    
    json_str = json.dumps(param_map, separators=(',', ':'))
    encoded = base64.urlsafe_b64encode(json_str.encode()).decode()
    return encoded

def decode_agent_params(encoded: str) -> Dict[str, Any]:
    """Decode agent parameters from URL-safe string"""
    try:
        json_str = base64.urlsafe_b64decode(encoded.encode()).decode()
        return json.loads(json_str)
    except Exception:
        return {
            'agent_uuid': '',
            'agent_name': '',
            'location': 'Houston',
            'route_filter': 'both',
            'fair_chance_only': False,
            'max_jobs': 25,
            'match_level': 'good and so-so',
            'coach_username': '',
        }

def generate_agent_url(agent_uuid: str, params: Dict[str, Any]) -> str:
    """Generate the agent portal URL using encoded config parameter.
    
    Uses the new simplified portal system that loads jobs via instant_memory_search.
    The URL format is: /agent_job_feed?config={encoded_params}
    """
    # Ensure agent_uuid is in params for encoding
    params = params.copy()
    params['agent_uuid'] = agent_uuid
    
    # Encode agent parameters
    encoded_config = encode_agent_params(params)
    
    # Determine base URL depending on environment
    try:
        import streamlit as st
        import os
        
        # Detect environment and set appropriate base URL
        current_dir = os.getcwd()
        repo_name = os.path.basename(current_dir)
        
        # Multiple ways to detect QA environment
        is_qa_portal = (
            'freeworld-qa-portal' in current_dir or 
            repo_name == 'freeworld-qa-portal' or
            '/mount/src/freeworld-qa-portal' in current_dir or
            os.path.exists('.qa-portal-marker')  # Fallback marker file
        )
        
        if is_qa_portal:
            # QA Portal URL
            base_url = "https://fwcareertest.streamlit.app"  # QA environment
            print(f"🧪 QA Environment detected - using QA portal URL: {base_url}")
        else:
            # Production URL  
            base_url = "https://fwcareercoach.streamlit.app"  # Production environment
            print(f"🏭 Production Environment detected - using production URL: {base_url}")
        
        print(f"🔍 Environment debug: current_dir='{current_dir}', repo_name='{repo_name}', is_qa_portal={is_qa_portal}")
            
        # Override for local development
        is_local = False
        try:
            is_local = not (hasattr(st, 'get_option') and st.get_option('server.headless'))
        except Exception:
            is_local = False
        if is_local:
            base_url = "http://localhost:8501"
            
    except Exception:
        base_url = "https://fwcareercoach.streamlit.app"  # Fallback to production

    # Generate URL pointing to agent_job_feed with encoded config
    return f"{base_url}/agent_job_feed?config={encoded_config}"

def filter_jobs_by_match_level(df: pd.DataFrame, match_level: str) -> pd.DataFrame:
    """Filter jobs by AI match quality level"""
    if df.empty:
        return df
    
    if match_level == 'good':
        return df[df['ai.match'] == 'good']
    elif match_level == 'so-so':
        return df[df['ai.match'] == 'so-so']
    elif match_level == 'good and so-so':
        return df[df['ai.match'].isin(['good', 'so-so'])]
    elif match_level == 'all':
        return df  # Include all jobs (good, so-so, bad)
    else:
        # Default to good and so-so
        return df[df['ai.match'].isin(['good', 'so-so'])]

def prioritize_jobs_for_display(df: pd.DataFrame, fair_chance_boost: bool = False) -> pd.DataFrame:
    """Sort jobs by priority: excellence first, then freshness"""
    if df.empty:
        return df
    
    df = df.copy()
    df['display_priority'] = 0
    
    # Excellence priority
    if 'ai.match' in df.columns:
        df.loc[df['ai.match'] == 'good', 'display_priority'] += 100
        df.loc[df['ai.match'] == 'so-so', 'display_priority'] += 50
        df.loc[df['ai.match'] == 'bad', 'display_priority'] += 25
    
    # Fair chance boost
    if fair_chance_boost and 'meta.tags' in df.columns:
        fair_mask = df['meta.tags'].astype(str).str.contains('fair', case=False, na=False)
        df.loc[fair_mask, 'display_priority'] += 15
    
    # Freshness (newest first)
    if 'sys.scraped_at' in df.columns:
        try:
            df['scraped_datetime'] = pd.to_datetime(df['sys.scraped_at'])
            now = datetime.now(timezone.utc)
            df['hours_old'] = (now - df['scraped_datetime']).dt.total_seconds() / 3600
            df['freshness_score'] = 10 - (df['hours_old'] / 24).clip(0, 10)
            df['display_priority'] += df['freshness_score']
        except Exception:
            pass
    
    return df.sort_values('display_priority', ascending=False)

def update_job_tracking_for_agent(df: pd.DataFrame, agent_params: Dict) -> pd.DataFrame:
    """Simple universal agent tracking - one link for all jobs"""
    print(f"🔍 UPDATE_JOB_TRACKING_FOR_AGENT: Starting with {len(df)} jobs")
    print(f"🔍 UPDATE_JOB_TRACKING_FOR_AGENT: Agent params keys: {list(agent_params.keys())}")
    
    if df.empty:
        print("🔍 UPDATE_JOB_TRACKING_FOR_AGENT: DataFrame is empty, returning")
        return df
    
    df = df.copy()
    
    # Apply match level filtering based on agent preferences
    match_level = agent_params.get('match_level', 'good and so-so')
    print(f"🔍 UPDATE_JOB_TRACKING_FOR_AGENT: Applying match level filter: {match_level}")
    original_count = len(df)
    df = filter_jobs_by_match_level(df, match_level)
    filtered_count = len(df)
    print(f"🔍 UPDATE_JOB_TRACKING_FOR_AGENT: Match level filter: {original_count} → {filtered_count} jobs")
    
    if df.empty:
        print("🔍 UPDATE_JOB_TRACKING_FOR_AGENT: DataFrame is empty after match level filtering, returning")
        return df
    
    # Debug: Check what columns exist
    print(f"🔍 UPDATE_JOB_TRACKING_FOR_AGENT: DataFrame columns: {list(df.columns)}")
    
    # Step 1: Ensure all jobs have apply URLs from pipeline data
    print(f"🔍 UPDATE_JOB_TRACKING_FOR_AGENT: Step 1 - Setting up original URLs")
    urls_set = 0
    for idx, job in df.iterrows():
        current_tracked = job.get('meta.tracked_url', '')
        print(f"🔍 Job {idx}: Current tracked_url = '{current_tracked}' (len={len(str(current_tracked))})")
        
        if not current_tracked:  # Only set if not already set
            # Use original job URLs from pipeline data
            # Try comprehensive URL field list including source.url (for HTML preview)
            original_url = (job.get('source.apply_url', '') or 
                          job.get('source.indeed_url', '') or 
                          job.get('source.google_url', '') or 
                          job.get('clean_apply_url', '') or
                          job.get('source.url', ''))  # Fallback for HTML preview
            
            print(f"🔍 Job {idx}: Found original_url = '{original_url[:50] if original_url else 'EMPTY'}...' from pipeline")
            
            # Debug: Show what URL fields are actually available
            available_urls = {
                'source.apply_url': job.get('source.apply_url', ''),
                'source.indeed_url': job.get('source.indeed_url', ''), 
                'source.google_url': job.get('source.google_url', ''),
                'clean_apply_url': job.get('clean_apply_url', ''),
                'source.url': job.get('source.url', '')
            }
            print(f"🔍 Job {idx}: URL fields available: {[(k, len(v)) for k, v in available_urls.items() if v]}")
            
            if original_url:
                df.at[idx, 'meta.tracked_url'] = original_url
                urls_set += 1
                print(f"🔍 Job {idx}: Set meta.tracked_url to '{original_url}'")
    
    print(f"🔍 UPDATE_JOB_TRACKING_FOR_AGENT: Step 1 complete - Set {urls_set} original URLs")
    
    # Step 2: Generate Short.io tracking links (same as PDF generator does)
    print(f"🔍 UPDATE_JOB_TRACKING_FOR_AGENT: Step 2 - Attempting Short.io link generation")
    try:
        from link_tracker import LinkTracker
        print(f"🔍 UPDATE_JOB_TRACKING_FOR_AGENT: LinkTracker imported successfully")
        
        link_tracker = LinkTracker()
        print(f"🔍 UPDATE_JOB_TRACKING_FOR_AGENT: LinkTracker created")
        print(f"🔍 UPDATE_JOB_TRACKING_FOR_AGENT: LinkTracker.is_available = {getattr(link_tracker, 'is_available', 'ATTR_MISSING')}")
        print(f"🔍 UPDATE_JOB_TRACKING_FOR_AGENT: Has create_short_link = {hasattr(link_tracker, 'create_short_link')}")
        
        if hasattr(link_tracker, 'create_short_link') and link_tracker.is_available:
            print(f"🔍 UPDATE_JOB_TRACKING_FOR_AGENT: LinkTracker ready - processing {len(df)} jobs")
            short_links_created = 0
            
            for idx, job in df.iterrows():
                original_url = job.get('meta.tracked_url', '')
                print(f"🔍 Job {idx}: Processing URL '{original_url[:50]}...'")
                
                if original_url and not original_url.startswith('https://freeworldjobs.short.gy'):
                    # Build tags matching PDF generator format exactly
                    tags = []
                    
                    # Coach tag
                    coach_user = agent_params.get('coach_username', '') or ''
                    if coach_user:
                        tags.append(f"coach:{coach_user}")
                    
                    # Market tag
                    market = agent_params.get('location', 'Unknown') or 'Unknown'
                    tags.append(f"market:{market}")
                    
                    # Route tag
                    route = str(job.get('ai.route_type', '')).lower() or 'unknown'
                    tags.append(f"route:{route}")
                    
                    # Match quality tag
                    match = str(job.get('ai.match', '')).lower() or 'unknown'
                    tags.append(f"match:{match}")
                    
                    # Fair chance tag
                    fair = str(job.get('ai.fair_chance', '')).lower()
                    fair_flag = 'true' if 'fair_chance_employer' in fair else 'false'
                    tags.append(f"fair:{fair_flag}")
                    
                    # Candidate tag
                    cand_id = agent_params.get('agent_uuid', '') or ''
                    if cand_id:
                        tags.append(f"candidate:{cand_id}")
                    
                    print(f"🔍 Job {idx}: Tags = {tags}")
                    
                    # Create Short.io link
                    title = job.get('source.title', '').strip()
                    print(f"🔍 Job {idx}: Creating Short.io link for '{title[:30]}...'")
                    
                    try:
                        short_url = link_tracker.create_short_link(original_url, title=title, tags=tags)
                        print(f"🔍 Job {idx}: Short.io returned: '{short_url}'")
                        
                        if short_url and short_url != original_url:
                            df.at[idx, 'meta.tracked_url'] = short_url
                            short_links_created += 1
                            print(f"✅ Job {idx}: Updated to Short.io URL: '{short_url}'")
                        else:
                            print(f"⚠️ Job {idx}: Short.io returned same URL or empty")
                    except Exception as e:
                        print(f"❌ Job {idx}: Short.io link creation failed: {e}")
                else:
                    print(f"🔍 Job {idx}: Skipping (no URL or already a Short.io link)")
            
            print(f"🔍 UPDATE_JOB_TRACKING_FOR_AGENT: Step 2 complete - Created {short_links_created} Short.io links")
        else:
            print("❌ UPDATE_JOB_TRACKING_FOR_AGENT: LinkTracker not available or configured - using original URLs")
            print(f"   - has create_short_link: {hasattr(link_tracker, 'create_short_link')}")
            print(f"   - is_available: {getattr(link_tracker, 'is_available', 'MISSING')}")
            
    except ImportError as e:
        print(f"❌ UPDATE_JOB_TRACKING_FOR_AGENT: LinkTracker import failed: {e}")
    except Exception as e:
        print(f"❌ UPDATE_JOB_TRACKING_FOR_AGENT: Link tracking setup failed: {e}")
    
    # Final debug: Show what we're returning
    final_tracked_count = 0
    final_short_count = 0
    for idx, job in df.iterrows():
        tracked_url = job.get('meta.tracked_url', '')
        if tracked_url:
            final_tracked_count += 1
            if tracked_url.startswith('https://freeworldjobs.short.gy'):
                final_short_count += 1
    
    print(f"🔍 UPDATE_JOB_TRACKING_FOR_AGENT: Final result - {final_tracked_count} jobs with tracked URLs ({final_short_count} Short.io links)")
    
    return df

def get_market_options() -> List[str]:
    """Get available market options"""
    return [
        "Houston", "Dallas", "Bay Area", "Stockton", "Denver",
        "Las Vegas", "Newark", "Phoenix", "Trenton", "Inland Empire", 
        "San Antonio", "Austin", "Custom Location"
    ]

def get_location_for_pipeline(market: str) -> str:
    """Convert market name to full location format for pipeline"""
    location_map = {
        "Houston": "Houston, TX",
        "Dallas": "Dallas, TX", 
        "Bay Area": "Berkeley, CA",
        "Stockton": "Stockton, CA", 
        "Denver": "Denver, CO",
        "Las Vegas": "Las Vegas, NV",
        "Newark": "Newark, NJ",
        "Phoenix": "Phoenix, AZ",
        "Trenton": "Trenton, NJ",
        "Inland Empire": "Ontario, CA",
        "San Antonio": "San Antonio, TX",
        "Austin": "Austin, TX"
    }
    return location_map.get(market, market)

# Agent profile management using Supabase
def save_agent_profile(coach_username: str, agent_data: Dict) -> Tuple[bool, str]:
    """Save agent profile to Supabase ONLY - no session state fallback"""
    try:
        # Generate custom URL for the agent using Short.io
        if 'custom_url' not in agent_data or not agent_data['custom_url']:
            agent_uuid = agent_data.get('agent_uuid', '')
            if agent_uuid:
                # Generate the long URL first
                long_url = generate_agent_url(agent_uuid, agent_data)
                
                # Try to shorten with Short.io for portal visit tracking
                try:
                    from link_tracker import LinkTracker
                    tracker = LinkTracker()
                    
                    if hasattr(tracker, 'create_short_link'):
                        # Tags for portal visit analytics
                        portal_tags = [
                            f"coach:{coach_username}",
                            f"candidate:{agent_uuid}",  # CRITICAL: Agent UUID for tracking
                            f"agent:{agent_data.get('agent_name', 'Unknown').replace(' ', '-')}",
                            f"market:{agent_data.get('location', 'Unknown')}",
                            "type:portal_access"
                        ]
                        
                        short_url = tracker.create_short_link(
                            long_url, 
                            title=f"Job Feed - {agent_data.get('agent_name', 'Agent')}", 
                            tags=portal_tags
                        )
                        agent_data['custom_url'] = short_url
                        print(f"✅ Created Short.io portal link: {short_url}")
                    else:
                        agent_data['custom_url'] = long_url
                        print(f"⚠️ Short.io not available, using long URL")
                        
                except Exception as e:
                    agent_data['custom_url'] = long_url
                    print(f"⚠️ Short.io failed ({e}), using long URL")
        
        # Save to Supabase - REQUIRED, no fallbacks
        from supabase_utils import save_agent_profile_to_supabase
        success, error = save_agent_profile_to_supabase(coach_username, agent_data)
        
        if success:
            print(f"✅ Agent profile saved to Supabase: {agent_data.get('agent_name', 'Unknown')}")
            return True, "Successfully saved to database"
        else:
            print(f"❌ Supabase save failed: {error}")
            return False, f"Database error: {error}"
            
    except ImportError as e:
        error_msg = "Supabase connection not available - check environment variables"
        print(f"❌ {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg

def load_agent_profiles(coach_username: str) -> List[Dict]:
    """Load agent profiles for a coach from Supabase ONLY - no session state fallback"""
    try:
        from supabase_utils import load_agent_profiles_from_supabase
        profiles, error = load_agent_profiles_from_supabase(coach_username)
        
        if error is None:
            print(f"✅ Loaded {len(profiles)} agent profiles from Supabase")
            return profiles
        else:
            print(f"❌ Supabase load failed: {error}")
            return []
            
    except ImportError:
        print("❌ Supabase connection not available")
        return []
    except Exception as e:
        print(f"❌ Error loading profiles: {e}")
        return []


def load_agent_profiles_with_stats(coach_username: str, lookback_days: int = 14) -> List[Dict]:
    """OPTIMIZED: Load agent profiles with click statistics in batch for better performance.
    
    This replaces the pattern of:
    1. load_agent_profiles() - gets N agents
    2. get_agent_click_stats() called N times - inefficient!
    
    With a single optimized call that gets all data in 2 queries instead of N+1.
    
    Args:
        coach_username: The coach's username
        lookback_days: How many days back to look for click stats
        
    Returns:
        List of agent profiles with embedded click statistics
    """
    try:
        from supabase_utils import fetch_coach_agents_with_stats
        profiles, error = fetch_coach_agents_with_stats(coach_username, lookback_days)
        
        if error is None:
            print(f"✅ Loaded {len(profiles)} agent profiles with stats from Supabase (optimized batch)")
            return profiles
        else:
            print(f"❌ Optimized load failed: {error}")
            # Fallback to old method if needed
            return load_agent_profiles(coach_username)
            
    except ImportError:
        print("❌ Supabase connection not available")
        return []
    except Exception as e:
        print(f"❌ Error loading profiles with stats: {e}")
        # Fallback to old method if needed
        return load_agent_profiles(coach_username)

def delete_agent_profile(coach_username: str, agent_uuid: str) -> bool:
    """Delete an agent profile from Supabase ONLY - no session state fallback"""
    try:
        from supabase_utils import delete_agent_profile_from_supabase
        success, error = delete_agent_profile_from_supabase(coach_username, agent_uuid)
        
        if success:
            print(f"✅ Agent profile deleted from Supabase: {agent_uuid}")
            return True
        else:
            print(f"❌ Supabase delete failed: {error}")
            return False
            
    except ImportError:
        print("❌ Supabase connection not available")
        return False
    except Exception as e:
        print(f"❌ Error deleting profile: {e}")
        return False

def get_agent_click_stats(agent_uuid: str, lookback_days: int = 14) -> Dict[str, int]:
    """Get comprehensive click statistics for an agent from Supabase"""
    try:
        from supabase_utils import get_client, fetch_click_events
        
        # Get job click events for the specified lookback period
        from datetime import datetime, timedelta, timezone
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=lookback_days)
        events_df = fetch_click_events(start_date, end_date)
        
        # Convert DataFrame to list of dicts and filter for agent
        if not events_df.empty:
            agent_events = events_df[events_df['candidate_id'] == agent_uuid].to_dict('records')
        else:
            agent_events = []
        
        # Calculate recent job clicks (last 7 days within the lookback period)
        recent_cutoff = datetime.now(timezone.utc) - pd.Timedelta(days=min(7, lookback_days))
        recent_clicks = len([e for e in agent_events 
                           if e.get('clicked_at', '') > recent_cutoff.isoformat()])
        
        # Get portal click stats from agent_profiles table
        portal_clicks = 0
        portal_last_click = None
        try:
            client = get_client()
            if client:
                result = client.table('agent_profiles').select(
                    'portal_clicks, last_portal_click'
                ).eq('agent_uuid', agent_uuid).execute()
                
                if result.data and len(result.data) > 0:
                    profile = result.data[0]
                    portal_clicks = profile.get('portal_clicks', 0) or 0
                    portal_last_click = profile.get('last_portal_click')
        except Exception as e:
            print(f"Warning: Could not fetch portal clicks: {e}")
        
        return {
            'total_clicks': len(agent_events),         # Job clicks
            'recent_clicks': recent_clicks,           # Recent job clicks
            'portal_clicks': portal_clicks,           # Portal access clicks
            'portal_last_click': portal_last_click,   # Last portal click
            'lookback_days': lookback_days
        }
    except Exception:
        return {
            'total_clicks': 0, 
            'recent_clicks': 0, 
            'portal_clicks': 0,
            'portal_last_click': None,
            'lookback_days': lookback_days
        }

def get_coach_agent_uuids(coach_username: str) -> List[str]:
    """Get all agent UUIDs for a specific coach from agent_profiles table"""
    try:
        from supabase_utils import get_client
        client = get_client()
        if not client:
            return []
        
        result = client.table('agent_profiles').select(
            'agent_uuid'
        ).eq('coach_username', coach_username).execute()
        
        if result.data:
            return [agent['agent_uuid'] for agent in result.data if agent.get('agent_uuid')]
        return []
    except Exception as e:
        print(f"Warning: Could not fetch coach agent UUIDs: {e}")
        return []

def get_all_agents_click_stats(coach_username: str, lookback_days: int = 14) -> Dict[str, Any]:
    """Get aggregated click statistics for all coach's agents using agent_profiles as source of truth"""
    try:
        from supabase_utils import fetch_click_events
        
        # Get all agent UUIDs for this coach from agent_profiles (source of truth)
        coach_agent_uuids = get_coach_agent_uuids(coach_username)
        
        if not coach_agent_uuids:
            # No agents found for this coach
            return {
                'total_clicks': 0,
                'recent_clicks': 0,
                'unique_agents': 0,
                'avg_clicks_per_agent': 0,
                'lookback_days': lookback_days
            }
        
        # Get events for the specified lookback period
        events = fetch_click_events(limit=10000, since_days=lookback_days)
        
        # Filter events for this coach's agents using UUIDs (more efficient and accurate)
        coach_events = [e for e in events if e.get('candidate_id') in coach_agent_uuids]
        
        # Calculate metrics
        total_clicks = len(coach_events)
        unique_agents = len(set(e.get('candidate_id', '') for e in coach_events if e.get('candidate_id')))
        
        # Recent clicks (last 7 days within lookback period)
        recent_cutoff = datetime.now(timezone.utc) - pd.Timedelta(days=min(7, lookback_days))
        recent_clicks = len([e for e in coach_events 
                           if e.get('clicked_at', '') > recent_cutoff.isoformat()])
        
        return {
            'total_clicks': total_clicks,
            'recent_clicks': recent_clicks,
            'unique_agents': unique_agents,
            'avg_clicks_per_agent': total_clicks / max(1, unique_agents),
            'lookback_days': lookback_days
        }
    except Exception:
        return {
            'total_clicks': 0,
            'recent_clicks': 0,
            'unique_agents': 0,
            'avg_clicks_per_agent': 0,
            'lookback_days': lookback_days
        }
