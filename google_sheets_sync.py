#!/usr/bin/env python3
"""
Google Sheets Job Seeker Data Sync
Automatically fetch job seeker counts from live Google Sheet
"""

import pandas as pd
import streamlit as st
from typing import Dict, Optional
import requests
import re

# Google Sheets URL and configuration
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/10YbEgbTjuXTQKjy2-OYs8uhGYi0dOW9jUAz9QMVcO-0/edit?gid=621688987#gid=621688987"
SHEET_ID = "10YbEgbTjuXTQKjy2-OYs8uhGYi0dOW9jUAz9QMVcO-0"
SHEET_GID = "621688987"

# Market mapping from CBSA names to our system names
CBSA_TO_MARKET_MAPPING = {
    'Phoenix-Mesa-Chandler, AZ': 'Phoenix',
    'Stockton, CA': 'Stockton',
    'San Francisco-Oakland-Berkeley, CA': 'Bay Area',
    'Denver-Aurora-Lakewood, CO': 'Denver',
    'New York-Newark-Jersey City, NY-NJ-PA': 'Newark',
    'Houston-The Woodlands-Sugar Land, TX': 'Houston',
    'Dallas-Fort Worth-Arlington, TX': 'Dallas',
    'Las Vegas-Henderson-Paradise, NV': 'Las Vegas',
    'Riverside-San Bernardino-Ontario, CA': 'Inland Empire',
    'Trenton-Princeton, NJ': 'Trenton',
    'Los Angeles-Long Beach-Anaheim, CA': 'Inland Empire'  # Note: Both map to Inland Empire
}

def get_google_sheet_csv_url(sheet_id: str, gid: str) -> str:
    """Convert Google Sheets URL to CSV export URL"""
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

def fetch_job_seeker_data() -> Dict[str, int]:
    """
    Fetch job seeker counts from Google Sheets
    Returns a dictionary mapping market names to job seeker counts
    """
    try:
        # Convert to CSV export URL
        csv_url = get_google_sheet_csv_url(SHEET_ID, SHEET_GID)

        # Fetch the CSV data
        response = requests.get(csv_url, timeout=10)
        response.raise_for_status()

        # Parse CSV content
        from io import StringIO
        csv_content = StringIO(response.text)
        df = pd.read_csv(csv_content)

        # Print column names for debugging
        print("📊 Google Sheet columns:", df.columns.tolist())
        print("📊 First few rows:")
        print(df.head())

        # Look for the specific columns we know about
        market_col = None
        count_col = None

        # Find CBSA/market column (first column typically)
        if len(df.columns) > 0:
            market_col = df.columns[0]  # Usually the first column
            print(f"🎯 Using market column: {market_col}")

        # Find "Active Job Seekers" column
        for col in df.columns:
            if 'active job seekers' in col.lower().strip():
                count_col = col
                print(f"🎯 Found job seekers column: {col}")
                break

        if not count_col:
            print("❌ Could not find 'Active Job Seekers' column")
            print("Available columns:", df.columns.tolist())
            return {}

        if market_col and count_col:
            # Build the mapping using CBSA mapping
            job_seeker_data = {}

            for _, row in df.iterrows():
                cbsa_name = str(row[market_col]).strip()
                count = row[count_col]

                # Skip empty rows
                if pd.isna(cbsa_name) or cbsa_name.lower() in ['', 'nan', 'total']:
                    continue

                # Map CBSA name to our market name
                market_name = CBSA_TO_MARKET_MAPPING.get(cbsa_name)
                if not market_name:
                    print(f"⚠️ Unknown CBSA: {cbsa_name}")
                    continue

                # Try to convert count to integer
                try:
                    count = int(float(count)) if not pd.isna(count) else 0

                    # Handle Inland Empire (sum both CBSAs)
                    if market_name == 'Inland Empire':
                        if market_name in job_seeker_data:
                            job_seeker_data[market_name] += count
                        else:
                            job_seeker_data[market_name] = count
                    else:
                        job_seeker_data[market_name] = count

                    print(f"✅ {cbsa_name} -> {market_name}: {count}")

                except (ValueError, TypeError):
                    print(f"⚠️ Could not parse count for {cbsa_name}: {count}")

            print(f"✅ Successfully loaded {len(job_seeker_data)} markets from Google Sheets")
            return job_seeker_data

        else:
            print("❌ Could not identify required columns")
            return {}

    except Exception as e:
        print(f"❌ Error fetching Google Sheets data: {e}")
        return {}

def get_cached_job_seeker_data() -> Dict[str, int]:
    """
    Get job seeker data with caching to avoid repeated API calls
    """
    # Try to use Streamlit session state for caching
    if hasattr(st, 'session_state'):
        if 'job_seeker_data' not in st.session_state or st.session_state.get('job_seeker_data_stale', True):
            print("🔄 Fetching fresh job seeker data from Google Sheets...")
            st.session_state.job_seeker_data = fetch_job_seeker_data()
            st.session_state.job_seeker_data_stale = False

        return st.session_state.job_seeker_data
    else:
        # Fallback for non-Streamlit environments
        return fetch_job_seeker_data()

def refresh_job_seeker_cache():
    """Force refresh of job seeker data cache"""
    if hasattr(st, 'session_state'):
        st.session_state.job_seeker_data_stale = True

# Fallback data in case Google Sheets is unavailable
FALLBACK_JOB_SEEKER_COUNTS = {
    'Houston': 45,
    'Dallas': 32,
    'Las Vegas': 28,
    'Bay Area': 24,
    'Phoenix': 18,
    'Denver': 15,
    'Newark': 12,
    'Stockton': 8,
    'California': 25,
    'Texas': 20,
    'Unknown': 0
}

def get_job_seeker_counts() -> Dict[str, int]:
    """
    Get job seeker counts with fallback to static data
    """
    try:
        live_data = get_cached_job_seeker_data()
        if live_data:
            print(f"✅ Using live Google Sheets data ({len(live_data)} markets)")
            return live_data
        else:
            print("⚠️ Using fallback data - Google Sheets unavailable")
            return FALLBACK_JOB_SEEKER_COUNTS
    except Exception as e:
        print(f"❌ Error loading job seeker data, using fallback: {e}")
        return FALLBACK_JOB_SEEKER_COUNTS

if __name__ == "__main__":
    # Test the function
    print("🧪 Testing Google Sheets sync...")
    data = fetch_job_seeker_data()
    print(f"📊 Result: {data}")