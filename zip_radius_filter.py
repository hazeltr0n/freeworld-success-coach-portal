#!/usr/bin/env python3
"""
ZIP Radius Filtering for Agent Portal

Lightweight utility to filter jobs by ZIP code and radius.
Uses free zippopotam.us API for geocoding (no API key needed).
"""

import requests
from functools import lru_cache
from typing import List, Dict, Optional, Tuple
from geopy.distance import geodesic


@lru_cache(maxsize=500)
def get_zip_coordinates(zip_code: str) -> Optional[Tuple[float, float]]:
    """Get lat/lng coordinates for a ZIP code using free API

    Args:
        zip_code: US ZIP code (5 digits)

    Returns:
        Tuple of (lat, lng) or None if not found
    """
    try:
        # Clean ZIP code (remove +4 if present)
        zip_code = str(zip_code).strip().split('-')[0]

        if not zip_code or len(zip_code) != 5:
            return None

        url = f"https://api.zippopotam.us/us/{zip_code}"
        response = requests.get(url, timeout=3)

        if response.status_code == 200:
            data = response.json()
            if 'places' in data and len(data['places']) > 0:
                place = data['places'][0]
                lat = float(place.get('latitude', 0))
                lng = float(place.get('longitude', 0))
                return (lat, lng)
    except Exception as e:
        print(f"⚠️ ZIP lookup failed for {zip_code}: {e}")

    return None


def calculate_distance_miles(zip1: str, zip2: str) -> Optional[float]:
    """Calculate distance in miles between two ZIP codes

    Args:
        zip1: First ZIP code
        zip2: Second ZIP code

    Returns:
        Distance in miles or None if calculation fails
    """
    coords1 = get_zip_coordinates(zip1)
    coords2 = get_zip_coordinates(zip2)

    if coords1 and coords2:
        try:
            return geodesic(coords1, coords2).miles
        except Exception as e:
            print(f"⚠️ Distance calculation failed: {e}")

    return None


def filter_jobs_by_zip_radius(jobs: List[Dict], agent_zip: str, radius_miles: int) -> List[Dict]:
    """Filter jobs to only those within radius of agent ZIP

    Args:
        jobs: List of job dictionaries with 'zip_code' field
        agent_zip: Agent's ZIP code
        radius_miles: Search radius in miles

    Returns:
        Filtered list of jobs with 'distance_miles' added
    """
    if not agent_zip or not radius_miles:
        return jobs

    filtered = []

    for job in jobs:
        job_zip = job.get('zip_code', '').strip()

        if not job_zip:
            # Include jobs without ZIP (can't filter them out)
            filtered.append(job)
            continue

        distance = calculate_distance_miles(agent_zip, job_zip)

        if distance is not None:
            if distance <= radius_miles:
                job['distance_miles'] = round(distance, 1)
                filtered.append(job)
        else:
            # If distance calculation fails, include the job
            filtered.append(job)

    # Sort by distance (closest first)
    filtered.sort(key=lambda j: j.get('distance_miles', 999))

    return filtered


def get_nearby_zips(center_zip: str, radius_miles: int, max_zips: int = 100) -> List[str]:
    """Get list of ZIP codes within radius (for SQL-based filtering)

    This is more efficient for large datasets - pre-compute nearby ZIPs once,
    then use SQL WHERE zip_code IN (...) queries.

    Args:
        center_zip: Center ZIP code
        radius_miles: Search radius in miles
        max_zips: Maximum ZIPs to return (safety limit)

    Returns:
        List of ZIP codes within radius
    """
    # TODO: Implement by querying location_markets table or using spatial database
    # For now, return empty list - use filter_jobs_by_zip_radius() instead
    return []


if __name__ == "__main__":
    # Test ZIP coordinate lookup
    test_zip = "77064"
    coords = get_zip_coordinates(test_zip)
    print(f"ZIP {test_zip} coordinates: {coords}")

    # Test distance calculation
    zip1 = "77064"  # Houston
    zip2 = "77077"  # Houston area
    distance = calculate_distance_miles(zip1, zip2)
    print(f"Distance between {zip1} and {zip2}: {distance:.1f} miles")

    # Test job filtering
    sample_jobs = [
        {'job_id': '1', 'title': 'Job 1', 'zip_code': '77064'},
        {'job_id': '2', 'title': 'Job 2', 'zip_code': '77077'},
        {'job_id': '3', 'title': 'Job 3', 'zip_code': '75001'},  # Dallas - far away
    ]

    filtered = filter_jobs_by_zip_radius(sample_jobs, agent_zip="77064", radius_miles=25)
    print(f"\nFiltered jobs within 25 miles of {test_zip}:")
    for job in filtered:
        print(f"  - {job['title']}: {job.get('distance_miles', 'N/A')} miles")
