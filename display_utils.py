#!/usr/bin/env python3
"""
Display utilities for consistent DataFrame column ordering across the application.
Centralizes column definitions to avoid duplication and ensure consistency.
"""

def get_quality_display_columns():
    """
    Get column order for quality jobs display - matches PDF card layout.

    Returns:
        list: Column names in display order
    """
    return [
        'source.title',           # Job Title (main identifier)
        'source.company',         # Company (key info)
        'source.location',        # Location (geographic relevance)
        'ai.route_type',          # Route Type (Local/Regional/OTR)
        'ai.match',              # Match Quality (good/so-so/bad)
        'ai.career_pathway',     # Career Pathway (e.g., cdl_pathway, dock_to_driver)
        'ai.training_provided',  # Training Provided (boolean)
        'ai.fair_chance',        # Fair Chance Employer (boolean)
        'ai.summary',            # Job Description Summary
        'meta.tracked_url'       # Apply Link (for testing)
    ]

def get_full_dataframe_columns():
    """
    Get column order for full DataFrame display - testing/debugging priority.

    Returns:
        list: Column names in display order (testing fields first)
    """
    return [
        # Testing & Debug Priority (leftmost)
        'ai.match',              # Quality classification
        'ai.route_type',         # Route classification
        'ai.career_pathway',     # Career pathway classification
        'ai.training_provided',  # Training provided flag
        'sys.is_fresh_job',      # Fresh vs memory

        # Core Job Info (center)
        'source.title',          # Job title
        'source.company',        # Company
        'source.location',       # Location
        'ai.fair_chance',       # Fair chance status
        'ai.summary',           # AI summary

        # URLs (rightmost)
        'meta.tracked_url'       # Tracking URL
    ]

def filter_available_columns(columns, dataframe):
    """
    Filter column list to only include columns that exist in the DataFrame.

    Args:
        columns (list): Desired column order
        dataframe (pd.DataFrame): DataFrame to check for column existence

    Returns:
        list: Available columns in the desired order
    """
    return [col for col in columns if col in dataframe.columns]

def reorder_dataframe_columns(df, desired_columns):
    """
    Reorder DataFrame columns according to desired order, keeping extra columns at the end.

    Args:
        df (pd.DataFrame): DataFrame to reorder
        desired_columns (list): Desired column order

    Returns:
        pd.DataFrame: DataFrame with reordered columns
    """
    available_desired = filter_available_columns(desired_columns, df)
    remaining_columns = [col for col in df.columns if col not in available_desired]
    final_column_order = available_desired + remaining_columns

    return df[final_column_order]

def get_quality_display_dataframe(df):
    """
    Get quality jobs DataFrame with proper column ordering and filtering.

    Args:
        df (pd.DataFrame): Source DataFrame

    Returns:
        pd.DataFrame: Quality jobs with display columns in proper order
    """
    # Filter to quality jobs only
    quality_df = df[df.get('ai.match', '').isin(['good', 'so-so'])].copy()
    if quality_df.empty:
        quality_df = df.copy()

    # Get available display columns and reorder
    display_cols = get_quality_display_columns()
    available_cols = filter_available_columns(display_cols, quality_df)

    if available_cols:
        return quality_df[available_cols].copy().reset_index(drop=True)
    else:
        # Fallback to original DataFrame if no display columns available
        return quality_df.reset_index(drop=True)

def get_full_display_dataframe(df):
    """
    Get full DataFrame with proper column ordering for testing/debugging.

    Args:
        df (pd.DataFrame): Source DataFrame

    Returns:
        pd.DataFrame: Full DataFrame with columns in testing-friendly order
    """
    desired_cols = get_full_dataframe_columns()
    return reorder_dataframe_columns(df, desired_cols).reset_index(drop=True)