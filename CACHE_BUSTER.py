#!/usr/bin/env python3
"""
CACHE BUSTER FILE - Force Streamlit Cloud Rebuild
Created: September 5, 2025

This file forces Streamlit to completely rebuild the environment
by changing import-level code and dependencies.
"""

CACHE_BUST_VERSION = "v2025.09.08.1820.PRODUCTION_AGENT_LOADING_FIX"

# Force import changes to invalidate Python module cache
import sys
import os
import datetime

# Add aggressive cache busting with environment changes
DEPLOYMENT_TIMESTAMP = datetime.datetime.now().isoformat()
PYTHON_CACHE_SALT = f"REBUILD_{DEPLOYMENT_TIMESTAMP}_{os.getpid()}"

def force_cache_invalidation():
    """Force complete cache invalidation"""
    import time
    import hashlib
    
    # Generate unique runtime identifier
    timestamp = str(time.time())
    cache_key = hashlib.md5(f"{timestamp}_{PYTHON_CACHE_SALT}".encode()).hexdigest()
    
    return f"CACHE_BUST_{CACHE_BUST_VERSION}_{cache_key}"

# Force module reload by changing module-level code
FORCE_REBUILD_TOKEN = f"STREAMLIT_REBUILD_{CACHE_BUST_VERSION}"

if __name__ == "__main__":
    print(f"Cache buster active: {force_cache_invalidation()}")