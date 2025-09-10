#!/usr/bin/env python3
"""
Unified Job Sorting Utilities
Based on the working FPDF sorting implementation
"""

import pandas as pd

def get_unified_sort_priority(row):
    """
    Unified sorting priority function that matches the working FPDF implementation.
    
    Priority order:
    1. Route type: Local (0) → OTR/Regional (1) → Unknown (2)  
    2. Quality within route: Excellent+Fair (1) → Excellent (2) → Possible+Fair (3) → Possible (4) → Other (5)
    
    Returns combined priority score where route_priority * 10 + quality_priority
    """
    # Route type priority (most important) - EXACTLY as FPDF does it
    route_type = str(row.get('ai.route_type', '')).lower()
    if route_type == 'local':
        route_priority = 0
    elif route_type in ['otr', 'regional']:
        route_priority = 1  
    else:
        route_priority = 2  # Unknown/other
    
    # Quality priority within route type - EXACTLY as FPDF does it
    ai_match = row.get('ai.match', '')
    fair_chance = row.get('ai.fair_chance', '').lower()
    
    is_excellent = ai_match == 'good'
    is_possible = ai_match == 'so-so'  
    has_fair_chance = 'fair_chance_employer' in fair_chance
    
    if is_excellent and has_fair_chance:
        quality_priority = 1  # Highest quality
    elif is_excellent:
        quality_priority = 2  # Second quality  
    elif is_possible and has_fair_chance:
        quality_priority = 3  # Third quality
    elif is_possible:
        quality_priority = 4  # Fourth quality
    else:
        quality_priority = 5  # Lowest quality (bad/unknown matches)
    
    # Combine: route_priority * 10 + quality_priority for proper ordering
    # This ensures Local jobs always come first, then OTR, then Unknown
    return route_priority * 10 + quality_priority

def apply_unified_sorting(df):
    """
    Apply the unified sorting to a DataFrame.
    Returns sorted DataFrame with the _sort_priority column removed.
    """
    if df is None or df.empty:
        return df
    
    # Apply sorting - exactly as FPDF does it
    df_sorted = df.copy()
    df_sorted['_sort_priority'] = df_sorted.apply(get_unified_sort_priority, axis=1)
    df_sorted = df_sorted.sort_values('_sort_priority').drop('_sort_priority', axis=1).reset_index(drop=True)
    
    return df_sorted