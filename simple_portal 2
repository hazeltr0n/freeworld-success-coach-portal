"""
SIMPLE JOB PORTAL - NO BULLSHIT VERSION
Direct Supabase query -> Job cards with apply buttons
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
import base64
import json

# Import only what we need
from supabase_utils import get_client
from link_tracker import LinkTracker

def decode_agent_params(encoded_config: str) -> Dict:
    """Decode base64 agent configuration"""
    try:
        decoded_bytes = base64.b64decode(encoded_config.encode('utf-8'))
        return json.loads(decoded_bytes.decode('utf-8'))
    except Exception as e:
        st.error(f"Invalid configuration: {e}")
        return {}

def get_jobs_from_supabase(location: str, hours: int = 72) -> List[Dict]:
    """Get jobs directly from Supabase - NO PIPELINE BULLSHIT"""
    client = get_client()
    if not client:
        return []
    
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Direct query - get ALL fields
        result = client.table('jobs').select('*').ilike(
            'location', f'%{location}%'
        ).gte(
            'created_at', cutoff_time.isoformat()
        ).in_(
            'match_level', ['good', 'so-so']
        ).execute()
        
        return result.data or []
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return []

def create_tracking_url(original_url: str, job_title: str, coach: str, agent_uuid: str) -> str:
    """Create Short.io tracking URL"""
    try:
        tracker = LinkTracker()
        if not tracker.is_available:
            return original_url
            
        tags = [
            f"coach:{coach}",
            f"candidate:{agent_uuid}",
            "type:job_click",
            "source:simple_portal"
        ]
        
        tracking_url = tracker.create_short_link(
            original_url,
            title=f"Job - {job_title[:30]}",
            tags=tags
        )
        return tracking_url if tracking_url else original_url
        
    except Exception:
        return original_url

def render_job_card(job: Dict, coach_name: str, agent_name: str, agent_uuid: str) -> str:
    """Render a single job card with guaranteed apply button"""
    
    # DIRECT SUPABASE FIELD MAPPING - NO BULLSHIT
    title = job.get('job_title', 'CDL Driver Position')
    company = job.get('company', 'Company')
    location = job.get('location', '')
    description = job.get('job_description', '')
    match_level = job.get('match_level', 'good')
    route_type = job.get('route_type', '')
    salary = job.get('salary_text', '')
    
    # Clean description
    if description:
        import re
        description = re.sub(r'<[^>]+>', ' ', description)
        description = re.sub(r'\s+', ' ', description).strip()
        if len(description) > 300:
            description = description[:300] + "..."
    
    # FALLBACK CHAIN FOR APPLY URLS (exact Supabase field names)
    apply_url = (
        job.get('apply_url') or 
        job.get('indeed_job_url') or 
        job.get('google_job_url') or 
        job.get('clean_apply_url') or
        ""
    )
    
    print(f"🔥 DEBUG: {title[:30]} - apply_url: {apply_url[:50] if apply_url else 'NONE'}")
    
    # Create tracking URL if we have an apply URL
    if apply_url and apply_url.strip():
        final_url = create_tracking_url(apply_url.strip(), title, coach_name, agent_uuid)
        apply_button = f'<a href="{final_url}" target="_blank" class="apply-button">Apply Now →</a>'
    else:
        apply_button = f'<div class="no-apply">DEBUG: No URL found in any field</div>'
    
    # Match quality styling
    match_class = f"match-{match_level}" if match_level in ['good', 'so-so'] else 'match-good'
    match_display = 'Excellent' if match_level == 'good' else 'Good Fit' if match_level == 'so-so' else 'Good'
    
    return f"""
    <div class="job-card">
        <div class="job-header">
            <h3 class="job-title">{title}</h3>
            <span class="job-match {match_class}">{match_display}</span>
        </div>
        <div class="job-company">{company}</div>
        <div class="job-location">📍 {location}</div>
        <div class="job-description">{description}</div>
        {apply_button}
    </div>
    """

def get_page_style() -> str:
    """Get the CSS styling for the page"""
    return """
    <style>
    /* FreeWorld Variables */
    :root {
        --fw-freedom-green: rgb(161, 221, 56);
        --fw-midnight: rgb(31, 41, 55);
        --fw-horizon-grey: rgb(243, 244, 246);
    }
    
    /* Job card styling */
    .job-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        margin-bottom: 16px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .job-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
        gap: 12px;
    }
    
    .job-title {
        font-size: 18px;
        font-weight: 600;
        color: var(--fw-midnight);
        margin: 0;
        flex: 1;
    }
    
    .job-match {
        background: var(--fw-freedom-green);
        color: var(--fw-midnight);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        flex-shrink: 0;
    }
    
    .job-company {
        font-size: 16px;
        font-weight: 500;
        color: #374151;
        margin-bottom: 8px;
    }
    
    .job-location {
        font-size: 14px;
        color: #6b7280;
        margin-bottom: 12px;
    }
    
    .job-description {
        font-size: 14px;
        line-height: 1.4;
        color: #374151;
        margin-bottom: 16px;
    }
    
    .apply-button {
        display: inline-block;
        background: var(--fw-freedom-green);
        color: var(--fw-midnight);
        text-decoration: none;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.2s;
    }
    
    .apply-button:hover {
        background: rgb(190, 235, 75);
        transform: translateY(-1px);
    }
    
    .no-apply {
        background: #f3f4f6;
        color: #6b7280;
        padding: 12px 20px;
        border-radius: 8px;
        font-size: 14px;
        text-align: center;
        border: 1px dashed #d1d5db;
    }
    
    /* Page styling */
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    
    .page-header {
        text-align: center;
        margin-bottom: 30px;
        padding-bottom: 20px;
        border-bottom: 2px solid var(--fw-freedom-green);
    }
    
    .page-title {
        font-size: 28px;
        font-weight: 700;
        color: var(--fw-midnight);
        margin-bottom: 8px;
    }
    
    .page-subtitle {
        font-size: 16px;
        color: #6b7280;
    }
    
    /* Hide Streamlit elements */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    </style>
    """

def main():
    """Main portal function"""
    st.set_page_config(
        page_title="FreeWorld Job Portal",
        page_icon="🚛",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Get configuration from URL
    config_param = st.query_params.get('config', '')
    if not config_param:
        st.error("Invalid portal link - missing configuration")
        return
    
    # Decode configuration
    config = decode_agent_params(config_param)
    if not config:
        return
    
    # Extract config values
    agent_uuid = config.get('agent_uuid', '')
    location = config.get('location', 'Houston')
    coach = 'james.hazelton'  # Default coach for now
    
    # Apply styling
    st.markdown(get_page_style(), unsafe_allow_html=True)
    
    # Page header
    st.markdown(f"""
    <div class="main-container">
        <div class="page-header">
            <h1 class="page-title">Your Job Matches</h1>
            <p class="page-subtitle">Quality CDL opportunities in {location}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Get jobs from Supabase
    with st.spinner("Loading your job matches..."):
        jobs = get_jobs_from_supabase(location)
    
    if not jobs:
        st.markdown("""
        <div class="main-container">
            <div class="job-card">
                <h3>No jobs found</h3>
                <p>No quality job matches found for {location} in the last 72 hours.</p>
            </div>
        </div>
        """.format(location=location), unsafe_allow_html=True)
        return
    
    # Render job cards
    job_cards_html = '<div class="main-container">'
    for job in jobs[:25]:  # Limit to 25 jobs
        job_cards_html += render_job_card(job, coach, agent_uuid)
    job_cards_html += '</div>'
    
    st.markdown(job_cards_html, unsafe_allow_html=True)
    
    # Footer stats
    st.markdown(f"""
    <div class="main-container">
        <div style="text-align: center; margin-top: 30px; padding: 20px; background: var(--fw-horizon-grey); border-radius: 8px;">
            <p style="margin: 0; color: #6b7280; font-size: 14px;">
                Showing {len(jobs)} quality job matches • Powered by FreeWorld
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()