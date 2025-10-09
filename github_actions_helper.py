#!/usr/bin/env python3
"""
GitHub Actions Helper for DriverPulse Authentication
Triggers auth refresh workflow and polls for fresh auth
"""

import os
import time
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
import streamlit as st
from supabase_utils import get_client


def trigger_auth_refresh(github_token: str, repo_owner: str, repo_name: str) -> Tuple[bool, str]:
    """
    Trigger GitHub Actions workflow to refresh DriverPulse auth

    Args:
        github_token: GitHub Personal Access Token with workflow permissions
        repo_owner: GitHub username/org (e.g., 'freeworld_james')
        repo_name: Repository name (e.g., 'freeworld-job-scraper-main')

    Returns:
        Tuple of (success: bool, message: str)
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/refresh_driverpulse_auth.yml/dispatches"

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    data = {
        "ref": "main"  # Branch to run workflow on
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)

        if response.status_code == 204:
            return True, "✅ Auth refresh triggered successfully"
        else:
            return False, f"❌ Failed to trigger workflow: {response.status_code} - {response.text}"

    except Exception as e:
        return False, f"❌ Error triggering workflow: {str(e)}"


def wait_for_fresh_auth(max_wait_seconds: int = 240, poll_interval: int = 5) -> Tuple[bool, str]:
    """
    Poll Supabase system_config table waiting for fresh auth data

    Args:
        max_wait_seconds: Maximum time to wait (default 4 minutes)
        poll_interval: Seconds between polls (default 5)

    Returns:
        Tuple of (success: bool, message: str)
    """
    client = get_client()
    if not client:
        return False, "❌ Could not connect to Supabase"

    start_time = time.time()
    trigger_time = datetime.now(timezone.utc)

    while time.time() - start_time < max_wait_seconds:
        try:
            # Check auth timestamp
            result = client.table('system_config').select('updated_at').eq('config_key', 'driver_pulse_auth').execute()

            if result.data and len(result.data) > 0:
                updated_at_str = result.data[0]['updated_at']

                # Parse timestamp (handle both with/without timezone)
                if updated_at_str.endswith('Z'):
                    updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                elif '+' in updated_at_str or updated_at_str.count('-') > 2:
                    updated_at = datetime.fromisoformat(updated_at_str)
                else:
                    # No timezone info, assume UTC
                    updated_at = datetime.fromisoformat(updated_at_str).replace(tzinfo=timezone.utc)

                # Check if auth was updated after we triggered the workflow
                if updated_at > trigger_time:
                    age_seconds = (datetime.now(timezone.utc) - updated_at).total_seconds()
                    return True, f"✅ Fresh auth available (age: {int(age_seconds)}s)"

            # Wait before next poll
            time.sleep(poll_interval)

        except Exception as e:
            return False, f"❌ Error checking auth: {str(e)}"

    return False, f"⏱️ Timeout waiting for fresh auth ({max_wait_seconds}s)"


def get_auth_age() -> Optional[int]:
    """
    Get age of current auth in seconds

    Returns:
        Age in seconds, or None if auth not found
    """
    try:
        client = get_client()
        if not client:
            return None

        result = client.table('system_config').select('config_value').eq('config_key', 'driver_pulse_auth').execute()

        if result.data and len(result.data) > 0:
            import json
            auth_data = result.data[0]['config_value']

            # Parse JSON if string
            if isinstance(auth_data, str):
                auth_data = json.loads(auth_data)

            # Get created_at from inside the auth data
            created_at_str = auth_data.get('created_at')
            if not created_at_str:
                return None

            # Parse timestamp (handle different formats)
            if created_at_str.endswith('Z'):
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            elif '+' in created_at_str or created_at_str.count('-') > 2:
                created_at = datetime.fromisoformat(created_at_str)
            else:
                created_at = datetime.fromisoformat(created_at_str).replace(tzinfo=timezone.utc)

            age = (datetime.now(timezone.utc) - created_at).total_seconds()
            return int(age)

    except Exception as e:
        print(f"⚠️ Error getting auth age: {e}")
        return None

    return None


def refresh_auth_and_wait(progress_callback=None) -> Tuple[bool, str]:
    """
    Convenience function: Trigger auth refresh and wait for completion

    Args:
        progress_callback: Optional function to call with status updates

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Get credentials from Streamlit secrets
    try:
        github_token = st.secrets.get("GITHUB_TOKEN")
        repo_owner = st.secrets.get("GITHUB_REPO_OWNER", "freeworld_james")
        repo_name = st.secrets.get("GITHUB_REPO_NAME", "freeworld-job-scraper-main")

        if not github_token:
            return False, "❌ GITHUB_TOKEN not found in secrets"

    except Exception as e:
        return False, f"❌ Error loading GitHub credentials: {str(e)}"

    # Trigger workflow
    if progress_callback:
        progress_callback("🔄 Triggering auth refresh workflow...")

    success, msg = trigger_auth_refresh(github_token, repo_owner, repo_name)
    if not success:
        return False, msg

    if progress_callback:
        progress_callback("⏳ Waiting for fresh auth (up to 4 minutes)...")

    # Wait for fresh auth
    success, msg = wait_for_fresh_auth(max_wait_seconds=240, poll_interval=5)

    return success, msg
