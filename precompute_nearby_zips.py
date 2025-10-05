#!/usr/bin/env python3
"""
Pre-compute nearby ZIPs for fast portal filtering

This runs as a background job or on agent ZIP change.
Stores nearby ZIPs in free_agents.nearby_zips[] for instant SQL filtering.
"""

import requests
from functools import lru_cache
from geopy.distance import geodesic
from supabase import create_client


def get_client():
    """Get Supabase client from secrets"""
    with open('.streamlit/secrets.toml', 'r') as f:
        secrets = {}
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                secrets[key.strip()] = value.strip().strip('"')
    return create_client(secrets['SUPABASE_URL'], secrets['SUPABASE_ANON_KEY'])


@lru_cache(maxsize=500)
def get_zip_coordinates(zip_code: str):
    """Get lat/lng for ZIP code"""
    try:
        zip_code = str(zip_code).strip().split('-')[0]
        if len(zip_code) != 5:
            return None

        url = f"https://api.zippopotam.us/us/{zip_code}"
        response = requests.get(url, timeout=3)

        if response.status_code == 200:
            data = response.json()
            if 'places' in data and len(data['places']) > 0:
                place = data['places'][0]
                return (float(place['latitude']), float(place['longitude']))
    except:
        pass
    return None


def get_nearby_zips(center_zip: str, radius_miles: int, max_zips: int = 200):
    """Find all ZIPs within radius of center ZIP

    Strategy:
    1. Get center ZIP coordinates
    2. Query all unique ZIPs from jobs table
    3. Calculate distance for each
    4. Return ZIPs within radius
    """
    client = get_client()

    # Get center coordinates
    center_coords = get_zip_coordinates(center_zip)
    if not center_coords:
        print(f"❌ Could not geocode center ZIP: {center_zip}")
        return []

    print(f"📍 Finding ZIPs within {radius_miles} miles of {center_zip}")

    # Get all unique ZIPs from jobs table
    result = client.table('jobs').select('zip_code').execute()
    unique_zips = set(row['zip_code'] for row in result.data if row.get('zip_code'))

    print(f"📋 Checking {len(unique_zips)} unique ZIPs from jobs table")

    # Calculate distances
    nearby = []
    for job_zip in unique_zips:
        job_coords = get_zip_coordinates(job_zip)
        if job_coords:
            try:
                distance = geodesic(center_coords, job_coords).miles
                if distance <= radius_miles:
                    nearby.append((job_zip, distance))
            except:
                pass

    # Sort by distance and limit
    nearby.sort(key=lambda x: x[1])
    nearby_zips = [z[0] for z in nearby[:max_zips]]

    print(f"✅ Found {len(nearby_zips)} ZIPs within {radius_miles} miles")
    return nearby_zips


def update_agent_nearby_zips(agent_uuid: str, zip_code: str, radius_miles: int):
    """Update nearby_zips for a single agent"""
    client = get_client()

    nearby = get_nearby_zips(zip_code, radius_miles)

    # Update free_agents table
    client.table('free_agents').update({
        'nearby_zips': nearby
    }).eq('uuid', agent_uuid).execute()

    print(f"✅ Updated agent {agent_uuid}: {len(nearby)} nearby ZIPs")
    return nearby


def update_all_agents_nearby_zips():
    """Batch update all agents with nearby ZIPs"""
    client = get_client()

    # Get all active agents with ZIP codes
    result = client.table('free_agents').select('uuid, zip_code, zip_radius_miles').eq('is_active', True).execute()
    agents = [a for a in result.data if a.get('zip_code')]

    print(f"🔄 Updating {len(agents)} agents with nearby ZIPs\n")

    for i, agent in enumerate(agents):
        zip_code = agent['zip_code']
        radius = agent.get('zip_radius_miles', 25)

        print(f"[{i+1}/{len(agents)}] Agent {agent['uuid'][:8]}... (ZIP: {zip_code}, Radius: {radius}mi)")

        try:
            update_agent_nearby_zips(agent['uuid'], zip_code, radius)
        except Exception as e:
            print(f"  ❌ Error: {e}")

        # Rate limit
        import time
        time.sleep(0.2)

    print(f"\n✅ Updated {len(agents)} agents")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        # Update all agents
        update_all_agents_nearby_zips()
    else:
        # Test with single agent
        print("Usage:")
        print("  python3 precompute_nearby_zips.py --all")
        print("  (Or import and call update_agent_nearby_zips(uuid, zip, radius))")
