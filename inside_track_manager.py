"""
Inside Track Jobs Manager
Manages partner jobs that appear at the top of Free Agent feeds with special badges.
Jobs are stored in the main jobs table with source='inside_track'.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import hashlib
import uuid

from supabase_utils import get_client


def generate_inside_track_job_id(company: str, title: str, market: str) -> str:
    """Generate a unique job_id for inside track jobs."""
    content = f"inside_track|{company.lower().strip()}|{title.lower().strip()}|{market.lower().strip()}"
    return hashlib.md5(content.encode()).hexdigest()


def load_inside_track_jobs(
    coach_username: Optional[str] = None,
    market: Optional[str] = None,
    visible_only: bool = True
) -> List[Dict]:
    """
    Load inside track jobs from the jobs table.

    Args:
        coach_username: Optional filter by coach who created the job
        market: Optional filter by market
        visible_only: If True, only return visible jobs (default)

    Returns:
        List of job dictionaries
    """
    client = get_client()
    if client is None:
        print("❌ Supabase client not available")
        return []

    try:
        query = client.table('jobs').select('*').eq('source', 'inside_track')

        if market:
            query = query.eq('market', market)

        if coach_username:
            query = query.eq('success_coach', coach_username)

        # Filter by visibility using the filter_reason field
        # visible jobs have filter_reason = 'included: inside_track'
        # hidden jobs have filter_reason = 'hidden: inside_track'
        if visible_only:
            query = query.eq('filter_reason', 'included: inside_track')

        # Order by created_at descending (newest first)
        query = query.order('created_at', desc=True)

        result = query.execute()
        return result.data or []

    except Exception as e:
        print(f"❌ Error loading inside track jobs: {e}")
        return []


def save_inside_track_job(job_data: Dict, coach_username: str) -> Tuple[bool, str]:
    """
    Save a new inside track job to the jobs table.

    Args:
        job_data: Dictionary with job fields:
            - job_title (required)
            - company (required)
            - location (required) - "City, State" format
            - market (required)
            - job_description (required)
            - apply_url (required)
            - salary (optional)
            - route_type (optional, default 'Local')
            - fair_chance (optional, default 'fair_chance_employer')
            - career_pathway (optional)
            - match_level (optional, default 'good')
            - partner_name (optional)
            - partner_notes (optional)
            - expires_at (optional)
        coach_username: Username of coach creating the job

    Returns:
        Tuple of (success: bool, message: str)
    """
    client = get_client()
    if client is None:
        return False, "Supabase client not available"

    # Validate required fields
    required_fields = ['job_title', 'company', 'location', 'market', 'job_description']
    missing = [f for f in required_fields if not job_data.get(f)]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    try:
        # Parse location into city/state
        location = job_data['location']
        city, state = '', ''
        if ',' in location:
            parts = location.split(',')
            city = parts[0].strip()
            state = parts[1].strip() if len(parts) > 1 else ''
        else:
            city = location.strip()

        # Generate job_id
        job_id = generate_inside_track_job_id(
            job_data['company'],
            job_data['job_title'],
            job_data['market']
        )

        now = datetime.now(timezone.utc).isoformat()

        # The apply_url will be generated dynamically at feed-render time
        # to include the agent_id. Store the original company URL in clean_apply_url
        # for coach reference.
        original_apply_url = job_data.get('apply_url', '')

        # Inside track type: 'partner_opportunity' (anonymous) or 'inside_track' (direct)
        inside_track_type = job_data.get('inside_track_type', 'inside_track')

        # Build the job record matching the jobs table schema
        record = {
            'job_id': job_id,
            'source': 'inside_track',
            'inside_track_type': inside_track_type,
            'job_title': job_data['job_title'],
            'company': job_data['company'],
            'location': location,
            'zip_code': job_data.get('zip_code', ''),
            'job_description': job_data['job_description'],
            'apply_url': '',  # Will be generated at feed time with agent context
            'clean_apply_url': original_apply_url,  # Original company URL for coach reference
            'salary': job_data.get('salary', ''),
            'market': job_data['market'],

            # AI/classification fields (coach-provided for inside track)
            'match_level': job_data.get('match_level', 'good'),
            'match_reason': f"Partner opportunity via {coach_username}",
            'summary': job_data.get('job_description', '')[:500],  # Use description as summary
            'route_type': job_data.get('route_type', 'Local'),
            'fair_chance': 'fair_chance_employer',  # All inside track jobs are fair chance
            'career_pathway': job_data.get('career_pathway', 'cdl_pathway'),

            # Routing/visibility
            'filter_reason': 'included: inside_track',

            # Metadata
            'success_coach': coach_username,
            'created_at': now,
            'updated_at': now,

            # Inside track specific fields
            'partner_name': job_data.get('partner_name', ''),
            'partner_notes': job_data.get('partner_notes', ''),
            'expires_at': job_data.get('expires_at') if job_data.get('expires_at') else None,
        }

        # Use batch_insert_jobs_with_dedup RPC (has 5 min timeout vs PostgREST default)
        try:
            result = client.rpc('batch_insert_jobs_with_dedup', {'p_jobs_data': [record]}).execute()
            # RPC returns count, check if insert succeeded
            if result.data and result.data > 0:
                action = "created"
            else:
                action = "updated"  # ON CONFLICT triggered an update
        except Exception as insert_err:
            # If duplicate key error, try direct update
            if 'duplicate' in str(insert_err).lower() or '23505' in str(insert_err):
                result = client.table('jobs').update(record).eq('job_id', job_id).execute()
                action = "updated"
            else:
                raise insert_err

        if result.data:
            return True, f"Job {action} successfully: {job_data['job_title']}"
        else:
            return False, "No data returned from save"

    except Exception as e:
        return False, f"Error saving job: {e}"


def toggle_job_visibility(job_id: str, is_visible: bool) -> Tuple[bool, str]:
    """
    Toggle visibility of an inside track job.

    Args:
        job_id: The job_id to toggle
        is_visible: True to show, False to hide

    Returns:
        Tuple of (success: bool, message: str)
    """
    client = get_client()
    if client is None:
        return False, "Supabase client not available"

    try:
        new_status = 'included: inside_track' if is_visible else 'hidden: inside_track'

        result = client.table('jobs').update({
            'filter_reason': new_status,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('job_id', job_id).eq('source', 'inside_track').execute()

        if result.data:
            status_text = "visible" if is_visible else "hidden"
            return True, f"Job is now {status_text}"
        else:
            return False, "Job not found or not an inside track job"

    except Exception as e:
        return False, f"Error toggling visibility: {e}"


def repost_job(job_id: str) -> Tuple[bool, str]:
    """
    Repost an inside track job by updating its timestamps.
    This makes the job appear fresh in feeds.

    Args:
        job_id: The job_id to repost

    Returns:
        Tuple of (success: bool, message: str)
    """
    client = get_client()
    if client is None:
        return False, "Supabase client not available"

    try:
        now = datetime.now(timezone.utc).isoformat()

        # Verify job exists
        job_result = client.table('jobs').select('job_id').eq('job_id', job_id).eq('source', 'inside_track').execute()

        if not job_result.data:
            return False, "Job not found or not an inside track job"

        # Update timestamps to make job appear fresh
        result = client.table('jobs').update({
            'created_at': now,
            'updated_at': now,
            'filter_reason': 'included: inside_track'  # Ensure visible on repost
        }).eq('job_id', job_id).eq('source', 'inside_track').execute()

        if result.data:
            return True, "Job reposted successfully"
        else:
            return False, "Failed to repost job"

    except Exception as e:
        return False, f"Error reposting job: {e}"


def delete_inside_track_job(job_id: str) -> Tuple[bool, str]:
    """
    Delete an inside track job from the jobs table.

    Args:
        job_id: The job_id to delete

    Returns:
        Tuple of (success: bool, message: str)
    """
    client = get_client()
    if client is None:
        return False, "Supabase client not available"

    try:
        result = client.table('jobs').delete().eq('job_id', job_id).eq('source', 'inside_track').execute()

        if result.data:
            return True, "Job deleted successfully"
        else:
            return False, "Job not found or not an inside track job"

    except Exception as e:
        return False, f"Error deleting job: {e}"


def generate_interest_url(job_id: str, agent_id: str, agent_name: str = "") -> str:
    """
    Generate the edge function URL for expressing interest in an inside track job.

    Args:
        job_id: The inside track job ID
        agent_id: The Free Agent's UUID
        agent_name: Optional agent name for display

    Returns:
        URL to the inside-track-interest edge function
    """
    import urllib.parse

    # Use the Supabase project URL
    base_url = "https://yqbdltothngundojuebk.supabase.co/functions/v1/inside-track-interest"

    params = {
        'job_id': job_id,
        'agent_id': agent_id,
    }
    if agent_name:
        params['agent_name'] = agent_name

    return f"{base_url}?{urllib.parse.urlencode(params)}"


def get_inside_track_for_feed(market: str) -> List[Dict]:
    """
    Get visible inside track jobs for a specific market.
    Used when building Free Agent feeds.

    Args:
        market: The market to filter by

    Returns:
        List of job dictionaries with is_inside_track=True flag
    """
    jobs = load_inside_track_jobs(market=market, visible_only=True)

    # Add the inside track flag to each job
    for job in jobs:
        job['is_inside_track'] = True

    return jobs


def load_inside_track_interests(coach_username: Optional[str] = None, job_id: Optional[str] = None) -> List[Dict]:
    """
    Load interest records from inside_track_interests table.

    Args:
        coach_username: Optional filter by coach
        job_id: Optional filter by job

    Returns:
        List of interest records with job details
    """
    client = get_client()
    if client is None:
        print("❌ Supabase client not available")
        return []

    try:
        query = client.table('inside_track_interests').select('*')

        if coach_username:
            query = query.eq('coach_username', coach_username)

        if job_id:
            query = query.eq('job_id', job_id)

        # Order by newest first
        query = query.order('created_at', desc=True)

        result = query.execute()
        interests = result.data or []

        # Enrich with job details
        if interests:
            job_ids = list(set(i['job_id'] for i in interests))
            jobs_result = client.table('jobs').select('job_id, job_title, company, market').in_('job_id', job_ids).execute()
            jobs_map = {j['job_id']: j for j in (jobs_result.data or [])}

            for interest in interests:
                job = jobs_map.get(interest['job_id'], {})
                interest['job_title'] = job.get('job_title', 'Unknown')
                interest['company'] = job.get('company', 'Unknown')
                interest['market'] = job.get('market', 'Unknown')

        return interests

    except Exception as e:
        print(f"❌ Error loading inside track interests: {e}")
        return []


def update_interest_status(interest_id: str, status: str, notes: str = None) -> Tuple[bool, str]:
    """
    Update the status of an interest record.

    Args:
        interest_id: The interest record ID
        status: New status (new, contacted, applied, hired, declined)
        notes: Optional coach notes

    Returns:
        Tuple of (success: bool, message: str)
    """
    client = get_client()
    if client is None:
        return False, "Supabase client not available"

    try:
        update = {
            'status': status,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        if status == 'contacted':
            update['contacted_at'] = datetime.now(timezone.utc).isoformat()

        if notes is not None:
            update['coach_notes'] = notes

        result = client.table('inside_track_interests').update(update).eq('id', interest_id).execute()

        if result.data:
            return True, f"Status updated to {status}"
        else:
            return False, "Interest record not found"

    except Exception as e:
        return False, f"Error updating status: {e}"


def get_inside_track_metadata(job: Dict) -> Dict:
    """
    Extract inside track metadata from a job record.

    Args:
        job: The job dictionary from Supabase

    Returns:
        Dictionary with partner_name, partner_notes, expires_at
    """
    return {
        'partner_name': job.get('partner_name', ''),
        'partner_notes': job.get('partner_notes', ''),
        'expires_at': job.get('expires_at', ''),
    }


def update_inside_track_job(job_id: str, updates: Dict, coach_username: str) -> Tuple[bool, str]:
    """
    Update an existing inside track job.

    Args:
        job_id: The job_id to update
        updates: Dictionary of fields to update
        coach_username: Username of coach making the update

    Returns:
        Tuple of (success: bool, message: str)
    """
    client = get_client()
    if client is None:
        return False, "Supabase client not available"

    try:
        # Build update record
        record = {'updated_at': datetime.now(timezone.utc).isoformat()}

        # Map of allowed update fields
        allowed_fields = {
            'job_title', 'company', 'location', 'job_description', 'apply_url',
            'salary', 'market', 'match_level', 'route_type', 'fair_chance',
            'career_pathway', 'partner_name', 'partner_notes', 'expires_at'
        }

        for field, value in updates.items():
            if field in allowed_fields:
                record[field] = value

        result = client.table('jobs').update(record).eq('job_id', job_id).eq('source', 'inside_track').execute()

        if result.data:
            return True, "Job updated successfully"
        else:
            return False, "Job not found or not an inside track job"

    except Exception as e:
        return False, f"Error updating job: {e}"
