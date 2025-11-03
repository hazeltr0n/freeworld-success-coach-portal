#!/usr/bin/env python3
"""
Agent Portal V2 - Interactive Self-Service Job Search
No login required - link-based authentication via agent_id parameter
"""

import streamlit as st
import base64
from urllib.parse import parse_qs
from supabase_utils import get_client, instant_memory_search
import pandas as pd
from pdf.html_pdf_generator import render_jobs_html

# Page config
st.set_page_config(
    page_title="FreeWorld Job Search",
    page_icon="🚛",
    layout="wide"
)

# Custom CSS for better button contrast
st.markdown("""
<style>
    /* Make primary button text dark for better contrast on green background */
    .stButton > button[kind="primary"] {
        color: #1a1a1a !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# Extract agent_id from URL parameters  
query_params = st.query_params
agent_id = query_params.get('agent_id')

if not agent_id:
    st.error("🔒 Access Denied: No agent ID provided")
    st.info("Please use the link provided by your Success Coach")
    st.stop()

# Load agent profile
@st.cache_data(ttl=300)
def load_agent_profile(agent_id):
    client = get_client()
    result = client.table('agent_profiles').select('*').eq('agent_uuid', agent_id).execute()
    if result.data:
        return result.data[0]
    return None

def search_jobs(market, lookback_hours, route_type, fair_chance_only, zip_code=None, zip_radius=None):
    """Search for jobs based on filters"""
    # Map route type to route_filter format
    if route_type == "Local":
        route_filter = "local"
    elif route_type == "OTR":
        route_filter = "otr"
    else:  # "All"
        route_filter = "both"

    # Always show good + so-so jobs
    match_level = "good and so-so"

    # Run memory search using market + ZIP code + radius
    jobs_list = instant_memory_search(
        location=market,  # Use market for location parameter (same as agent_portal_clean.py)
        hours=lookback_hours,
        market=market,  # Market filter narrows query FIRST for performance
        pathway_preferences=[],  # Empty for now - can add later
        agent_zip=zip_code,
        zip_radius_miles=zip_radius,
        route_filter=route_filter,
        match_level=match_level
    )

    # Filter for fair chance if requested
    if fair_chance_only and jobs_list:
        jobs_list = [job for job in jobs_list if job.get('fair_chance', False)]

    return jobs_list

agent = load_agent_profile(agent_id)

if not agent:
    st.error("❌ Agent profile not found")
    st.stop()

# Check if we should show results page
if st.session_state.get('show_results', False):
    # Clear the flag
    st.session_state['show_results'] = False

    # Get search params
    params = st.session_state.get('search_params', {})

    # Show loading screen
    st.title("🔄 Loading Your Custom Job List")
    market = params.get('market', 'your market')
    zip_code = params.get('zip_code', 'your area')
    radius = params.get('zip_radius', 50)
    st.caption(f"Searching {market} market within {radius} miles of ZIP {zip_code}...")

    progress_container = st.empty()
    with progress_container.container():
        # Show a spinner with message
        with st.spinner("Finding the best matches for you..."):
            # Actually perform the search
            jobs_list = search_jobs(
                market=params.get('market'),  # Market narrows query for performance
                lookback_hours=params.get('lookback_hours'),
                route_type=params.get('route_type'),
                fair_chance_only=params.get('fair_chance_only'),
                zip_code=params.get('zip_code'),
                zip_radius=params.get('zip_radius')
            )

    # Clear the loading screen
    progress_container.empty()

    # Show results
    if jobs_list:
        st.success(f"✅ Found {len(jobs_list)} jobs matching your criteria!")

        # Convert to DataFrame with canonical schema (EXACT same approach as agent_portal_clean.py)
        df = pd.DataFrame(jobs_list)

        canonical_df = pd.DataFrame()
        for _, row in df.iterrows():
            canonical_row = {
                # Source fields
                'source.title': row.get('job_title', ''),
                'source.company': row.get('company', ''),
                'source.url': row.get('apply_url', ''),
                'source.description': row.get('job_description', ''),
                'source.location': row.get('location', ''),

                # System metadata
                'sys.scraped_at': row.get('created_at', ''),
                'sys.is_fresh_job': False,  # From memory

                # AI classification
                'ai.match': row.get('match_level', 'good'),
                'ai.summary': row.get('summary', ''),
                'ai.route_type': row.get('route_type', 'Unknown'),
                'ai.fair_chance': row.get('fair_chance', False),

                # ID fields
                'id.job': row.get('job_id', 'unknown'),

                # Processed fields for compatibility
                'norm.title': row.get('job_title', ''),
                'norm.company': row.get('company', ''),
                'norm.location': row.get('location', ''),
                'norm.city': '',
                'norm.state': '',

                # Tracking fields
                'meta.tracked_url': row.get('tracked_url', ''),
            }
            canonical_df = pd.concat([canonical_df, pd.DataFrame([canonical_row])], ignore_index=True)

        # Use EXACT same processing as agent_portal_clean.py
        from free_agent_system import update_job_tracking_for_agent
        from pdf.html_pdf_generator import jobs_dataframe_to_dicts, render_jobs_html

        agent_params = {
            'agent_uuid': params.get('agent_id'),
            'agent_name': params.get('agent_name', 'Friend'),
            'location': params.get('market'),  # Market name for title (e.g., "Phoenix CDL Jobs")
            'max_jobs': 'All'  # Show all matching jobs
        }

        # Process DataFrame the same way
        processed_df = update_job_tracking_for_agent(canonical_df, agent_params)

        # Apply unified sorting to match FPDF exactly
        if len(processed_df) > 0:
            try:
                from job_sorting_utils import apply_unified_sorting
                processed_df = apply_unified_sorting(processed_df)
                print(f"✅ Jobs sorted by route type (Local→OTR→Unknown) then quality")
            except Exception as e:
                print(f"⚠️ Sorting failed, using original order: {e}")

        # Convert to dicts
        jobs = jobs_dataframe_to_dicts(processed_df, candidate_id=agent_params.get('agent_uuid'))

        # Render HTML with fragment=True
        html = render_jobs_html(jobs, agent_params, fragment=True)
        st.components.v1.html(html, height=2000, scrolling=True)

        # Back button
        if st.button("← Back to Search"):
            st.session_state.pop('search_params', None)
            st.rerun()
    else:
        st.warning("No jobs found matching your criteria. Try adjusting your filters or extending the lookback period.")
        if st.button("← Back to Search"):
            st.session_state.pop('search_params', None)
            st.rerun()

    # Stop here - don't show the search form
    st.stop()

# Welcome header
st.title(f"👋 Welcome, {agent.get('agent_name', 'Friend')}!")
st.caption("Find your next driving opportunity")

# Create tabs for different sections
tab1, tab2 = st.tabs(["🔍 Search Jobs", "📊 My Activity"])

# CONSTANTS
LOOKBACK_OPTIONS = {
    "24 hours (1 day)": 24,
    "48 hours (2 days)": 48,
    "72 hours (3 days)": 72,
    "96 hours (4 days) - Recommended": 96,
    "7 days (168 hours)": 168,
    "14 days (336 hours)": 336
}
ROUTE_TYPES = ["Local", "OTR", "All"]  # All includes unknown routes

with tab1:
    st.header("🔍 Search for Jobs")

    # Market + ZIP code search (both required for performance)
    st.write("**Location**")

    # Market dropdown - 10 standard markets
    MARKETS = ["Dallas", "Houston", "Trenton", "Newark", "Las Vegas", "Bay Area", "Stockton", "Inland Empire", "Phoenix", "Denver"]
    market = st.selectbox("Market/Region", MARKETS,
                         index=MARKETS.index(agent.get('location', 'Dallas')) if agent.get('location') in MARKETS else 0)

    # ZIP code + radius
    col1, col2 = st.columns(2)
    with col1:
        zip_code = st.text_input("ZIP Code (for precise distance)", value=agent.get('zip_code', ''))

    with col2:
        radius = st.selectbox("Radius (miles)", [25, 50, 75, 100],
                            index=[25, 50, 75, 100].index(agent.get('zip_radius_miles', 50)))
    
    # Job freshness
    lookback_label = next((k for k, v in LOOKBACK_OPTIONS.items() if v == agent.get('lookback_hours', 96)),
                         "96 hours (4 days) - Recommended")
    lookback = st.selectbox("Job Age (How Recent)", list(LOOKBACK_OPTIONS.keys()),
                           index=list(LOOKBACK_OPTIONS.keys()).index(lookback_label))
    lookback_hours = LOOKBACK_OPTIONS[lookback]

    # Route type filter
    st.write("**Route Type**")
    saved_routes = agent.get('saved_routes', []) or []
    # Default to "All" if no saved preference
    if not saved_routes or "All" in saved_routes:
        default_route = "All"
    elif "Local" in saved_routes:
        default_route = "Local"
    else:
        default_route = "OTR"

    route_type = st.radio(
        "Select route type",
        ROUTE_TYPES,
        index=ROUTE_TYPES.index(default_route),
        horizontal=True,
        label_visibility="collapsed"
    )

    # Fair chance filter with disclaimer
    st.write("**Background-Friendly Jobs**")
    fair_chance = st.checkbox(
        "Only show jobs that explicitly state they're background-friendly in the ad",
        value=agent.get('fair_chance_only', False)
    )

    if fair_chance:
        st.info("ℹ️ Note: There aren't many jobs that explicitly advertise as background-friendly. You may see fewer results with this filter enabled.")
    
    # Search and save buttons
    col_search, col_save = st.columns([2, 1])
    with col_search:
        if st.button("🔍 Search Jobs", type="primary", use_container_width=True):
            # Validate ZIP code
            if not zip_code:
                st.error("Please enter a ZIP code")
                st.stop()

            # Store search params in session state and trigger results page
            st.session_state['search_params'] = {
                'market': market,  # Market for database query performance
                'lookback_hours': lookback_hours,
                'route_type': route_type,
                'fair_chance_only': fair_chance,
                'zip_code': zip_code,
                'zip_radius': radius,
                'agent_id': agent_id,
                'agent_name': agent.get('agent_name', 'Friend')
            }
            st.session_state['show_results'] = True
            st.rerun()
    
    with col_save:
        if st.button("💾 Save as My Defaults", use_container_width=True):
            if not zip_code:
                st.error("Please enter a ZIP code before saving")
                st.stop()

            client = get_client()

            # Save route as array for consistency with database schema
            saved_route_array = [route_type] if route_type != "All" else ["All"]

            update_data = {
                'location': market,  # Save market preference (stored in location field)
                'zip_code': zip_code,
                'zip_radius_miles': radius,
                'lookback_hours': lookback_hours,
                'saved_routes': saved_route_array,
                'saved_quality': 'good_and_soso',  # Always show good + so-so
                'fair_chance_only': fair_chance,
                'last_search_at': 'now()'
            }

            client.table('agent_profiles').update(update_data).eq('agent_uuid', agent_id).execute()
            st.success("✅ Preferences saved!")
            st.cache_data.clear()

with tab2:
    st.header("📊 My Activity")
    st.info("🚧 Activity tracking coming soon! You'll see jobs you've viewed and applied to here.")
