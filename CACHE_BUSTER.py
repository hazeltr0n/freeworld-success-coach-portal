#!/usr/bin/env python3
"""
CACHE BUSTER FILE - Force Streamlit Cloud Rebuild
Created: September 5, 2025

This file forces Streamlit to completely rebuild the environment
by changing import-level code and dependencies.
"""

CACHE_BUST_VERSION = "v2025.09.05.1445.FLICKER_TEST"

def force_cache_invalidation():
    """Force complete cache invalidation"""
    import time
    import hashlib
    
    # Generate unique runtime identifier
    timestamp = str(time.time())
    cache_key = hashlib.md5(timestamp.encode()).hexdigest()
    
    return f"CACHE_BUST_{CACHE_BUST_VERSION}_{cache_key}"

if __name__ == "__main__":
    print(f"Cache buster active: {force_cache_invalidation()}")