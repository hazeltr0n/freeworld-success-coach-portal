#!/usr/bin/env python3
"""
Agent Job Feed - Mobile-friendly job display page
Matches PDF styling from fpdf_pdf_generator.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timezone
import time
import os
import base64
import re
import html as _html
from free_agent_system import (
    decode_agent_params, filter_jobs_by_experience, 
    prioritize_jobs_for_display, get_location_for_pipeline
)

# Mobile-first CSS matching PDF styling
def load_mobile_css():
    """Load mobile-optimized CSS matching FreeWorld brand colors"""
    st.markdown("""
    <style>
    /* FreeWorld Brand Colors */
    :root {
        --fw-roots: rgb(0, 71, 81);           /* #004751 - Primary teal */
        --fw-freedom-green: rgb(205, 249, 92); /* #CDF95C - Light green */
        --fw-midnight: rgb(25, 25, 49);       /* #191931 - Dark text */
        --fw-visionary-violet: rgb(89, 60, 188); /* #593CBC - Accent */
        --fw-horizon-grey: rgb(244, 244, 244); /* #F4F4F4 - Background */
        --fw-card-border: rgb(204, 204, 204);  /* #CCCCCC - Border */
        --fw-card-bg: rgb(250, 250, 250);     /* #FAFAFA - Card background */
    }

    /* Mobile-first responsive design */
    .main-container {
        max-width: 390px;
        margin: 0 auto;
        padding: 10px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Header styling */
    .agent-header {
        text-align: center;
        padding: 20px 15px;
        background: linear-gradient(135deg, var(--fw-roots), var(--fw-visionary-violet));
        color: white;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,71,81,0.3);
    }

    .agent-name {
        font-size: 22px;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }

    .agent-subtitle {
        font-size: 14px;
        opacity: 0.9;
        margin-top: 5px;
    }

    /* Loading animation */
    .loading-container {
        text-align: center;
        padding: 40px 20px;
    }

    .loading-spinner {
        border: 3px solid var(--fw-horizon-grey);
        border-top: 3px solid var(--fw-roots);
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 0 auto 20px;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* Job card styling matching PDF layout */
    .job-card {
        background: var(--fw-card-bg);
        border: 1px solid var(--fw-card-border);
        border-radius: 12px;
        margin-bottom: 16px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .job-card:active {
        transform: translateY(1px);
        box-shadow: 0 1px 4px rgba(0,0,0,0.1);
    }

    .job-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
    }

    .job-title {
        font-size: 16px;
        font-weight: 700;
        color: var(--fw-midnight);
        line-height: 1.3;
        margin: 0;
        flex: 1;
        padding-right: 10px;
    }

    .job-match {
        font-size: 11px;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 12px;
        text-transform: uppercase;
        white-space: nowrap;
    }

    .match-good {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }

    .match-so-so {
        background: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }

    .match-bad {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }

    .job-company {
        font-size: 14px;
        font-weight: 600;
        color: var(--fw-roots);
        margin-bottom: 8px;
    }

    .job-details {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 12px;
        font-size: 12px;
        color: #666;
    }

    .job-detail {
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    .job-detail.fair-chance {
        color: var(--fw-freedom-green);
        font-weight: 600;
        background: rgba(161, 221, 56, 0.1);
        padding: 4px 8px;
        border-radius: 12px;
    }

    .job-description {
        font-size: 13px;
        line-height: 1.4;
        color: #333;
        margin-bottom: 16px;
        max-height: 4.2em; /* mobile default */
        overflow: hidden;  /* mobile default */
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 3;     /* clamp to ~3 lines on mobile */
        -webkit-box-orient: vertical;
    }

    /* Apply button matching PDF style */
    .apply-button {
        background: var(--fw-freedom-green);
        color: var(--fw-midnight);
        border: none;
        padding: 14px 20px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 700;
        text-decoration: none;
        display: block;
        text-align: center;
        width: 100%;
        box-sizing: border-box;
        transition: all 0.2s;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .apply-button:hover {
        background: rgb(190, 235, 75);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    .apply-button:active {
        transform: translateY(0px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .no-apply {
        background: #f0f0f0;
        color: #666;
        padding: 14px 20px;
        border-radius: 8px;
        text-align: center;
        font-size: 14px;
        margin-top: 16px;
        border: 1px dashed #ccc;
    }

    /* Stats bar */
    .stats-bar {
        background: var(--fw-horizon-grey);
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 20px;
        text-align: center;
        font-size: 13px;
        color: #666;
    }

    /* Hide Streamlit elements for cleaner mobile experience and remove top whitespace */
    html, body { margin: 0 !important; padding: 0 !important; }
    .stApp > header { display: none; }
    .stApp { padding-top: 0 !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="stAppViewContainer"] { padding: 0 !important; }
    .block-container { padding-top: 0 !important; margin-top: 0 !important; }
    [data-testid="stVerticalBlock"] { margin-top: 0 !important; }
    [data-testid="stMarkdownContainer"] { margin-top: 0 !important; padding-top: 0 !important; }
    section.main > div.block-container > div:first-child { margin-top: 0 !important; padding-top: 0 !important; }

    /* Fullscreen loading overlay */
    .loading-overlay {
        position: fixed; inset: 0; z-index: 9999;
        width: 100vw; height: 100svh; min-height: 100dvh;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        background: var(--fw-midnight);
        text-align: center; padding: 24px;
    }
    .loading-logo {
        width: clamp(120px, 22vw, 220px); height: clamp(120px, 22vw, 220px);
        border-radius: 50%; object-fit: cover; background: #fff;
        box-shadow: 0 8px 24px rgba(0,0,0,0.35); margin-bottom: 16px;
    }
    .loading-stack { display: flex; flex-direction: column; align-items: center; gap: 12px; }
    .loading-title { 
        color: var(--fw-freedom-green); 
        font-size: clamp(24px, 4.5vw, 40px); 
        margin: 0; 
        line-height: 1.05; 
        text-align: center; 
        letter-spacing: 0.01em;
        transform: translateY(-1px); /* subtle optical centering */
    }
    .loading-sub { color: #E5E5E5; font-size: clamp(14px, 2.8vw, 18px); opacity: .9; margin: 0; text-align: center; }
    .loading-spinner {
        border: 4px solid rgba(255,255,255,0.2);
        border-top: 4px solid var(--fw-freedom-green);
        border-radius: 50%; width: 48px; height: 48px;
        animation: spin 1s linear infinite; margin: 20px auto 0;
    }
    
    /* Mobile optimizations */
    @media (max-width: 480px) {
        .main-container {
            padding: 8px;
        }
        
        .job-card {
            margin-bottom: 12px;
            padding: 14px;
        }
        
        .job-title {
            font-size: 15px;
        }
        
        .job-details {
            gap: 8px;
        }
    }
    /* Desktop: always show full description and allow the card to grow */
    @media (min-width: 601px) {
        .job-card .job-description {
            max-height: none !important;
            overflow: visible !important;
            text-overflow: clip !important;
            -webkit-line-clamp: initial !important;
            -webkit-box-orient: initial !important;
            display: block !important;
        }
    }
    /* Account for safe areas on mobile */
    @supports (padding: max(0px)) {
      .loading-overlay { padding-bottom: max(24px, env(safe-area-inset-bottom)); padding-top: max(24px, env(safe-area-inset-top)); }
    }
    </style>
    """, unsafe_allow_html=True)

def _get_fw_logo_data_uri() -> str:
    candidates = [
        os.path.join(os.path.dirname(__file__), 'assets', 'FW-Logo-Roots.svg'),
        os.path.join(os.path.dirname(__file__), 'assets', 'FW-Logo-Roots@3x.png'),
        os.path.join(os.path.dirname(__file__), 'assets', 'FW-Wordmark-Roots@3x.png'),
        os.path.join(os.path.dirname(__file__), 'data', 'FW-Logo-Roots@3x.png'),
        os.path.join(os.path.dirname(__file__), 'data', 'FW-Logo-Roots@2x.png'),
    ]
    for p in candidates:
        try:
            if os.path.exists(p):
                with open(p, 'rb') as f:
                    b64 = base64.b64encode(f.read()).decode('utf-8')
                mime = 'image/svg+xml' if p.lower().endswith('.svg') else 'image/png'
                return f"data:{mime};base64,{b64}"
        except Exception:
            continue
    return ''

def show_loading_screen(agent_name: str):
    """Show full-viewport loading overlay while preparing job feed"""
    logo_uri = _get_fw_logo_data_uri()
    logo_img = f'<img class="loading-logo" src="{logo_uri}" alt="FreeWorld" />' if logo_uri else ''
    st.markdown(f"""
    <div class="loading-overlay">
        <div class="loading-stack">
            {logo_img}
            <h1 class="loading-title">FreeWorld</h1>
            <p class="loading-sub">Preparing your custom job feed...</p>
            <div class="loading-spinner"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_job_card(job: dict, agent_params: dict) -> str:
    """Render a single job card using SUPABASE FIELDS DIRECTLY"""
    # USE SUPABASE FIELDS DIRECTLY - NO FIELD MAPPING NEEDED
    title = job.get('job_title', 'CDL Driver Position')
    company = job.get('company', 'Company')
    location = job.get('location', '')
    match_level = job.get('match_level', 'good')
    route_type = job.get('route_type', '')
    fair_chance = job.get('fair_chance', '')
    salary = job.get('source.salary', '')
    # Prefer normalized full description; sanitize HTML snippets from Outscraper
    def _sanitize_desc(val: str) -> str:
        try:
            s = _html.unescape(str(val or ''))
            # remove scripts/styles blocks
            s = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', '', s)
            # convert common block tags to line breaks
            s = re.sub(r'(?i)</p\s*>', '\n\n', s)
            s = re.sub(r'(?i)<br\s*/?>', '\n', s)
            s = re.sub(r'(?i)<li\b[^>]*>', '• ', s)
            s = re.sub(r'(?i)</li\s*>', '\n', s)
            # drop remaining tags
            s = re.sub(r'<[^>]+>', '', s)
            # collapse excessive whitespace
            s = re.sub(r'\n{3,}', '\n\n', s).strip()
            # convert to HTML-safe line breaks
            s = s.replace('\n', '<br>')
            return s
        except Exception:
            return str(val or '')

    # Mobile agent portal: show full job description (not AI summary)
    # Try multiple description fields in order of preference
    full_description = (
        job.get('source.description', '') or  # Pipeline v3 canonical field
        job.get('job_description', '') or     # Legacy field
        job.get('description', '')            # Alternative field
    )
    description = _sanitize_desc(full_description)
    summary = _sanitize_desc(job.get('ai.summary', '') or job.get('summary', ''))
    
    # URL FALLBACK - prefer tracked short link when available
    apply_url = (
        job.get('tracked_url') or       # New field from instant_memory_search
        job.get('meta.tracked_url') or  # Legacy field from pipeline
        job.get('apply_url') or         # Original apply URL
        job.get('indeed_job_url') or    # Indeed URL  
        job.get('google_job_url') or    # Google Jobs URL
        job.get('clean_apply_url') or   # Cleaned URL
        ""
    )
    
    # Render job card for display
    # Note: match_level and route_type already extracted above from Supabase fields
    
    # Match quality badge
    match_class = f"match-{match_level}" if match_level in ['good', 'so-so', 'bad'] else 'match-good'
    match_display = match_level.title() if match_level != 'so-so' else 'Good Fit'
    
    # Format salary display
    salary_display = salary if salary and salary.strip() else ''
    if salary_display and len(salary_display) > 30:
        salary_display = salary_display[:30].rstrip()
    
    # Job details with fair chance indicator
    details = []
    if location:
        details.append(f'<span class="job-detail">📍 {location}</span>')
    if route_type:
        details.append(f'<span class="job-detail">🚛 {route_type}</span>')
    if fair_chance == 'fair_chance_employer':
        details.append(f'<span class="job-detail fair-chance">✨ Fair Chance Friendly</span>')
    
    details_html = '<div class="job-details">' + ''.join(details) + '</div>'
    
    # Clean description
    if description:
        # Remove HTML tags and clean up text
        import re
        description = re.sub(r'<[^>]+>', ' ', description)
        description = re.sub(r'\s+', ' ', description).strip()
    
    return f"""
    <div class="job-card">
        <div class="job-header">
            <h3 class="job-title">{title}</h3>
            <span class="job-match {match_class}">{match_display}</span>
        </div>
        
        <div class="job-company">{company}</div>
        
        {details_html}
        
        <div class="job-description">{description}</div>
        
        {f'<a href="{apply_url}" target="_blank" class="apply-button">Apply Now →</a>' if apply_url and apply_url.strip() else '<div class="no-apply">Application link not available</div>'}
    </div>
    """

def main():
    """Main agent job feed page"""
    st.set_page_config(
        page_title="Your FreeWorld Jobs",
        page_icon="🚛",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Load mobile CSS
    load_mobile_css()
    
    # Get URL parameters - support both old and new formats
    query_params = st.query_params
    
    # Try new format first (config parameter)
    config = query_params.get("config", "") or query_params.get("agent_config", "")
    
    if config:
        # New format: decode encoded config
        try:
            agent_params = decode_agent_params(config)
        except Exception as e:
            st.error("Invalid configuration. Please contact your career coach.")
            return
    else:
        # Try old format (individual parameters)
        agent_uuid = query_params.get("agent", "")
        token = query_params.get("token", "")
        location = query_params.get("location", "Houston")
        route = query_params.get("route", "both")
        experience = query_params.get("experience", "both")
        limit = query_params.get("limit", "25")
        
        if not agent_uuid or not token:
            st.error("Invalid job feed link. Please contact your career coach.")
            return
        
        # Convert old format to agent_params dict
        agent_params = {
            'agent_uuid': agent_uuid,
            'agent_name': 'Free Agent',  # We don't have the name in old URLs
            'location': location,
            'route_filter': route,
            'fair_chance_only': False,
            'max_jobs': int(limit) if limit.isdigit() else 25,
            'experience_level': experience,
            'coach_username': ''  # We don't have coach in old URLs
        }
    
    # Fill missing attribution fields from query params when possible
    qp = st.query_params
    if not agent_params.get('coach_username'):
        agent_params['coach_username'] = qp.get('coach_username', '') or qp.get('coach', '')
    if not agent_params.get('agent_uuid'):
        agent_params['agent_uuid'] = qp.get('agent', '') or qp.get('agent_uuid', '')

    agent_name = agent_params.get('agent_name', 'Free Agent')
    agent_uuid = agent_params.get('agent_uuid', '')
    
    # Show loading screen initially
    loading_placeholder = st.empty()
    with loading_placeholder:
        show_loading_screen(agent_name)
    
    # Simulate loading delay for better UX
    time.sleep(1.5)
    
    # Execute memory-only pipeline same as main search (ensures tracked links)
    # Agent portal active - memory search mode
    try:
        from pipeline_wrapper import StreamlitPipelineWrapper
        pipeline = StreamlitPipelineWrapper()

        market_label = agent_params.get('location', 'Houston')
        coach_username = agent_params.get('coach_username', '')

        pipeline_params = {
            'memory_only': False,  # Use Indeed + Memory search (will hit bypass threshold)
            'generate_pdf': False,
            'generate_csv': False,
            'location': market_label,
            'location_type': 'markets',
            'markets': market_label,
            'search_terms': 'CDL Driver No Experience',
            'coach_username': coach_username,
            'memory_hours': 72,
            'job_limit': agent_params.get('max_jobs', 25),
            'route_type_filter': [agent_params.get('route_filter', 'both')],  # Pipeline expects list
            'match_quality_filter': agent_params.get('match_level', 'good and so-so').split(' and '),  # Convert to list
            'fair_chance_only': agent_params.get('fair_chance_only', False),
            'candidate_name': agent_params.get('agent_name', ''),
            'candidate_id': agent_params.get('agent_uuid', ''),
            'ui_direct': True,  # use in-process pipeline path
            'search_sources': {'indeed': True, 'google': False},  # Indeed + Memory
            'search_strategy': 'memory_first'  # Check memory first, use bypass if threshold hit
        }

        df, metadata = pipeline.run_pipeline(pipeline_params)
        if not metadata.get('success', False):
            df = pd.DataFrame()
    
        if df.empty:
            # Clear overlay and render no-data state flush to top without extra padding
            loading_placeholder.empty()
            st.markdown(
                """
                <style>
                  [data-testid="stAppViewContainer"] { padding: 0 !important; }
                  .block-container { padding-top: 0 !important; margin-top: 0 !important; }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(f"""
            <div class="main-container">
                <div class="agent-header">
                    <h1 class="agent-name">{agent_name}</h1>
                    <div class="agent-subtitle">FreeWorld Career Coach Jobs</div>
                </div>
                <div style="text-align: center; padding: 40px 20px;">
                    <h3>No jobs found in your area right now</h3>
                    <p style="color: #666;">Check back soon - new opportunities are added daily!</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Filtering is now handled at the Supabase level via pipeline parameters
        # No post-processing filtering needed
        
        # Prioritize jobs for display
        df = prioritize_jobs_for_display(df, agent_params.get('fair_chance_only', False))
        
        # Link generation is now handled by the pipeline - no fallbacks needed

        # Limit to requested job count
        max_jobs = agent_params.get('max_jobs', 25)
        if len(df) > max_jobs:
            df = df.head(max_jobs)
        
        # Tracking URLs already generated by instant_memory_search
        
        # Debug: Print available URL fields in jobs
        if not df.empty:
            sample_job = df.iloc[0]
            url_fields = [col for col in df.columns if 'url' in col.lower() or 'link' in col.lower()]
            print(f"🔍 DEBUG Portal: Available URL fields: {url_fields}")
            for field in url_fields:
                value = sample_job.get(field, '')
                print(f"   {field}: {value[:50] if value else 'EMPTY'}...")
            
            # Additional debug - check all job fields
            print(f"🔍 DEBUG Portal: All job fields: {list(df.columns)}")
            print(f"🔍 DEBUG Portal: First job data sample:")
            for field in ['job_title', 'company', 'apply_url', 'indeed_job_url', 'tracked_url']:
                value = sample_job.get(field, 'MISSING_FIELD')
                print(f"   {field}: {value}")
            
            # Count jobs with URLs
            jobs_with_apply = len(df[df['apply_url'].notna() & (df['apply_url'] != '')])
            jobs_with_indeed = len(df[df['indeed_job_url'].notna() & (df['indeed_job_url'] != '')])  
            jobs_with_tracked = len(df[df['meta.tracked_url'].notna() & (df['meta.tracked_url'] != '')]) if 'meta.tracked_url' in df.columns else 0
            print(f"🔍 DEBUG Portal: Jobs with URLs - apply:{jobs_with_apply}, indeed:{jobs_with_indeed}, tracked:{jobs_with_tracked}")
        
        # Clear loading overlay and show jobs (flush to top)
        loading_placeholder.empty()
        st.markdown(
            """
            <style>
              [data-testid="stAppViewContainer"] { padding: 0 !important; }
              .block-container { padding-top: 0 !important; margin-top: 0 !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        
        # Display header and stats
        job_count = len(df)
        quality_jobs = len(df[df['ai.match'].isin(['good', 'so-so'])])
        
        st.markdown(f"""
        <div class="main-container">
            <div class="agent-header">
                <h1 class="agent-name">{agent_name}</h1>
                <div class="agent-subtitle">FreeWorld Career Coach Jobs</div>
            </div>
            
            <div class="stats-bar">
                Found {job_count} quality opportunities in {agent_params.get('location', 'your area')}
                <br>Updated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </div>
        """, unsafe_allow_html=True)
        
        # Display job cards
        jobs_html = ""
        for _, job in df.iterrows():
            jobs_html += render_job_card(job.to_dict(), agent_params)
        
        st.markdown(jobs_html + "</div>", unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
            Powered by FreeWorld Career Coach<br>
            Questions? Contact your career coach
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        loading_placeholder.empty()
        st.error(f"Error loading jobs: {str(e)}")
        st.markdown("Please contact your career coach for assistance.")

if __name__ == "__main__":
    main()
