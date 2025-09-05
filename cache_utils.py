"""
Cache utilities for FreeWorld Success Coach Portal
Centralized cache management to prevent the cache issues we've been having
"""

import streamlit as st
import time
import random
from typing import List, Optional

def clear_all_caches_and_refresh():
    """
    Centralized cache clearing function to replace all the scattered cache clearing code.
    This is the ONE place to handle cache clearing properly.
    """
    try:
        # Clear Streamlit caches
        st.cache_data.clear()
        st.cache_resource.clear()
        
        # Clear problematic session state keys but preserve authentication
        keys_to_preserve = {
            "current_coach",  # Keep user logged in
            "cache_cleared_at",  # Keep our cache clear timestamp
        }
        
        # Clear all other session state
        keys_to_delete = [key for key in st.session_state.keys() if key not in keys_to_preserve]
        for key in keys_to_delete:
            try:
                del st.session_state[key]
            except Exception:
                pass
        
        # Set cache clear timestamp
        from datetime import datetime
        st.session_state.cache_cleared_at = datetime.now().strftime("%H:%M:%S")
        
        # Don't set any query params - keep URLs clean
        
        st.success("✅ All caches cleared successfully!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Cache clearing failed: {e}")

def get_safe_session_value(key: str, default=None):
    """
    Safely get a session state value with proper error handling
    """
    try:
        return st.session_state.get(key, default)
    except Exception:
        return default

def set_safe_session_value(key: str, value):
    """
    Safely set a session state value with proper error handling
    """
    try:
        st.session_state[key] = value
        return True
    except Exception:
        return False

def cleanup_old_session_keys(max_age_hours: int = 24):
    """
    Clean up old session state keys that might be causing memory bloat
    """
    current_time = time.time()
    keys_to_check = [
        "search_results", "candidate_search_results", "candidate_search_results_tab",
        "last_results", "agent_profiles", "analytics_lookback_days"
    ]
    
    for key in keys_to_check:
        if key in st.session_state:
            try:
                # If the key exists but is stale, remove it
                key_age = current_time - st.session_state.get(f"{key}_timestamp", current_time)
                if key_age > (max_age_hours * 3600):
                    del st.session_state[key]
                    if f"{key}_timestamp" in st.session_state:
                        del st.session_state[f"{key}_timestamp"]
            except Exception:
                pass

# Cache decorator with better defaults
def safe_cache_data(ttl: int = 300, max_entries: int = 10, show_spinner: bool = False):
    """
    Wrapper around st.cache_data with safer defaults
    """
    return st.cache_data(ttl=ttl, max_entries=max_entries, show_spinner=show_spinner)

def safe_cache_resource(ttl: int = 3600, max_entries: int = 5, show_spinner: bool = False):
    """
    Wrapper around st.cache_resource with safer defaults
    """
    return st.cache_resource(ttl=ttl, max_entries=max_entries, show_spinner=show_spinner)