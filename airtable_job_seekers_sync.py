#!/usr/bin/env python3
"""
Airtable Job Seeker Data Sync
Automatically fetch job seeker counts from Airtable
"""

import pandas as pd
import streamlit as st
from typing import Dict, Optional
import requests
import json

def get_airtable_credentials():
    """Get Airtable credentials from Streamlit secrets or environment"""
    try:
        if hasattr(st, 'secrets') and 'AIRTABLE_API_KEY' in st.secrets:
            return {
                'api_key': st.secrets['AIRTABLE_API_KEY'],
                'base_id': st.secrets['AIRTABLE_BASE_ID']
            }
        else:
            import os
            return {
                'api_key': os.getenv('AIRTABLE_API_KEY'),
                'base_id': os.getenv('AIRTABLE_BASE_ID')
            }
    except Exception as e:
        print(f"❌ Error getting Airtable credentials: {e}")
        return None

def fetch_job_seeker_data_from_airtable() -> Dict[str, int]:
    """
    Fetch job seeker counts from Airtable
    Returns a dictionary mapping market names to job seeker counts
    """
    try:
        creds = get_airtable_credentials()
        if not creds or not creds['api_key'] or not creds['base_id']:
            print("❌ Airtable credentials not available")
            return {}

        # Use candidates table with the filtered view for active job seekers
        table_name = "tbl3fhAB14MkkewN1"  # Candidates table ID
        view_name = "viwZWU2DGIT8TjKc1"   # Filtered view ID from URL
        url = f"https://api.airtable.com/v0/{creds['base_id']}/{table_name}"

        headers = {
            'Authorization': f'Bearer {creds["api_key"]}',
            'Content-Type': 'application/json'
        }

        # Fetch all records (handle pagination) using the filtered view
        all_records = []
        params = {
            'pageSize': 100,  # Max page size
            'view': view_name  # Use the filtered view
        }

        while True:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            records = data.get('records', [])
            all_records.extend(records)

            # Check if there are more pages
            offset = data.get('offset')
            if not offset:
                break
            params['offset'] = offset

        print(f"📊 Fetched {len(all_records)} records from Airtable")

        # CBSA to market mapping - EXACT mapping as specified by user
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
            'Los Angeles-Long Beach-Anaheim, CA': 'Inland Empire'
        }

        # Count records by Market field directly (already mapped correctly)
        market_counts = {}

        for record in all_records:
            fields = record.get('fields', {})

            # Get Market value directly - this is already mapped correctly
            market = fields.get('Market', '').strip()

            # Only count markets that have values
            if market and market != '':
                if market in market_counts:
                    market_counts[market] += 1
                else:
                    market_counts[market] = 1

        print(f"📊 Market counts: {market_counts}")

        # The market data is already in the correct format
        job_seeker_data = market_counts

        for market, count in job_seeker_data.items():
            print(f"✅ {market}: {count}")

        print(f"✅ Successfully loaded {len(job_seeker_data)} markets from Airtable")
        return job_seeker_data

    except Exception as e:
        print(f"❌ Error fetching Airtable job seeker data: {e}")
        return {}

def get_cached_airtable_job_seeker_data() -> Dict[str, int]:
    """
    Get job seeker data with caching to avoid repeated API calls
    """
    # Try to use Streamlit session state for caching
    if hasattr(st, 'session_state'):
        if 'airtable_job_seeker_data' not in st.session_state or st.session_state.get('airtable_job_seeker_data_stale', True):
            print("🔄 Fetching fresh job seeker data from Airtable...")
            st.session_state.airtable_job_seeker_data = fetch_job_seeker_data_from_airtable()
            st.session_state.airtable_job_seeker_data_stale = False

        return st.session_state.airtable_job_seeker_data
    else:
        # Fallback for non-Streamlit environments
        return fetch_job_seeker_data_from_airtable()

def refresh_airtable_job_seeker_cache():
    """Force refresh of Airtable job seeker data cache"""
    if hasattr(st, 'session_state'):
        st.session_state.airtable_job_seeker_data_stale = True

# Fallback data in case Airtable is unavailable
FALLBACK_JOB_SEEKER_COUNTS = {
    'Houston': 45,
    'Dallas': 32,
    'Las Vegas': 28,
    'Bay Area': 24,
    'Phoenix': 18,
    'Denver': 15,
    'Newark': 12,
    'Stockton': 8,
    'Inland Empire': 15,
    'Trenton': 5,
    'California': 25,
    'Texas': 20,
    'Unknown': 0
}

def get_job_seeker_counts() -> Dict[str, int]:
    """
    Get job seeker counts with fallback to static data
    """
    try:
        live_data = get_cached_airtable_job_seeker_data()
        if live_data:
            print(f"✅ Using live Airtable data ({len(live_data)} markets)")
            return live_data
        else:
            print("⚠️ Using fallback data - Airtable unavailable")
            return FALLBACK_JOB_SEEKER_COUNTS
    except Exception as e:
        print(f"❌ Error loading job seeker data from Airtable, using fallback: {e}")
        return FALLBACK_JOB_SEEKER_COUNTS

if __name__ == "__main__":
    # Test the function
    print("🧪 Testing Airtable job seeker sync...")
    data = fetch_job_seeker_data_from_airtable()
    print(f"📊 Result: {data}")