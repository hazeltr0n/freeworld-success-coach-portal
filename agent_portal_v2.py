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

def main():
    """Main function for agent portal v2 - can be called from app.py or run standalone"""

    # Only set page config if running standalone (not imported)
    import sys
    if __name__ == "__main__" or 'app' not in sys.modules:
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

        # Fetch click events for this agent
        client = get_client()

        try:
            # Get applications from job_feedback table
            job_feedback = client.table('job_feedback').select('*').eq('candidate_id', agent_id).eq('feedback_type', 'i_applied_to_this_job').order('created_at', desc=True).limit(100).execute()

            # Get all click events for job views
            click_events = client.table('click_events').select('*').eq('candidate_id', agent_id).order('clicked_at', desc=True).limit(100).execute()

            # Get aggregated stats
            candidate_stats = client.table('candidate_clicks').select('*').eq('candidate_id', agent_id).execute()

            total_clicks = candidate_stats.data[0].get('clicks', 0) if candidate_stats.data else 0

            # Process applications from job_feedback
            application_events = []
            for feedback in job_feedback.data:
                # job_feedback already has job_title and company, but try to enrich with jobs table if job_id exists
                job_id = feedback.get('job_id')
                if job_id:
                    try:
                        job_result = client.table('jobs').select('apply_url, match_level, route_type').eq('job_id', job_id).limit(1).execute()

                        if job_result.data:
                            job = job_result.data[0]
                            # Only override if we got better data from jobs table
                            if job.get('apply_url'):
                                feedback['apply_url'] = job.get('apply_url')
                            if job.get('match_level'):
                                feedback['match'] = job.get('match_level')
                            if job.get('route_type'):
                                feedback['route'] = job.get('route_type')
                    except Exception as e:
                        print(f"Error enriching application: {e}")

                # Extract actual URL from job_url if it's a click-redirect-lite URL
                job_url = feedback.get('job_url', '')
                if 'click-redirect-lite' in job_url and '?target=' in job_url:
                    try:
                        from urllib.parse import urlparse, parse_qs, unquote
                        parsed = urlparse(job_url)
                        params = parse_qs(parsed.query)
                        if 'target' in params:
                            feedback['extracted_url'] = unquote(params['target'][0])
                    except:
                        pass

                # Map created_at to clicked_at for consistent display
                feedback['clicked_at'] = feedback.get('created_at')
                application_events.append(feedback)

            # Process click events for job views (skip portal URLs)
            regular_clicks = []
            for event in click_events.data:
                url = event.get('original_url', '')

                # Skip portal URLs (they contain 'agent_job_feed' or 'agent_id=')
                if 'agent_job_feed' in url or 'agent_id=' in url:
                    continue

                # Look up job details - prefer job_id if available, fallback to URL match
                try:
                    job_id = event.get('job_id')

                    if job_id:
                        # Use job_id for direct lookup (preferred method)
                        job_result = client.table('jobs').select('job_title, company, match_level, route_type, apply_url').eq('job_id', job_id).limit(1).execute()
                    else:
                        # Fallback to URL matching for older records
                        job_result = client.table('jobs').select('job_title, company, match_level, route_type, apply_url').eq('tracked_url', url).limit(1).execute()

                    if job_result.data:
                        job = job_result.data[0]
                        event['job_title'] = job.get('job_title')
                        event['company'] = job.get('company')
                        event['match'] = job.get('match_level')
                        event['route'] = job.get('route_type')
                        event['apply_url'] = job.get('apply_url')
                except Exception as e:
                    print(f"Error enriching click event: {e}")

                regular_clicks.append(event)

            # Metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Job Clicks", total_clicks)
            with col2:
                st.metric("Total Applications", len(application_events))

            st.markdown("---")

            # Helper function to format match quality
            def format_match_quality(match):
                if match == 'good':
                    return 'Excellent Match'
                elif match == 'so-so':
                    return 'Possible Fit'
                else:
                    return match or 'Unknown'

            # Applications Section
            st.subheader("📝 Your Applications")
            if application_events:
                st.caption(f"Showing {len(application_events)} applications")

                for event in application_events:
                    job_title = event.get('job_title') or 'Job Title Not Available'
                    company = event.get('company') or 'Company Not Available'
                    date_str = event.get('clicked_at', 'Unknown date')[:10]

                    with st.expander(f"{company} - {date_str}", expanded=False):
                        st.write(f"**Job:** {job_title}")
                        st.write(f"**Company:** {company}")
                        st.write(f"**Date:** {event.get('clicked_at', 'N/A')[:19]}")
                        # For applications, prefer apply_url (from jobs table), fallback to job_url (from job_feedback)
                        st.write(f"**Application Link:** {event.get('apply_url') or event.get('job_url') or 'N/A'}")

                        # Show quality/route info if available
                        if event.get('match'):
                            st.write(f"**Match Quality:** {format_match_quality(event.get('match'))}")
                        if event.get('route'):
                            st.write(f"**Route Type:** {event.get('route')}")
                        if event.get('market'):
                            st.write(f"**Market:** {event.get('market')}")
            else:
                st.info("No applications yet. When you click 'Apply' on a job, it will show up here!")

            st.markdown("---")

            # Click History Section
            st.subheader("👁️ Jobs You've Viewed")
            if regular_clicks:
                st.caption(f"Showing last {len(regular_clicks)} job views")

                for event in regular_clicks:
                    job_title = event.get('job_title') or 'Job Title Not Available'
                    company = event.get('company') or 'Company Not Available'
                    date_str = event.get('clicked_at', 'Unknown date')[:10]

                    with st.expander(f"{company} - {date_str}", expanded=False):
                        st.write(f"**Job:** {job_title}")
                        st.write(f"**Company:** {company}")
                        st.write(f"**Date:** {event.get('clicked_at', 'N/A')[:19]}")
                        # For job views, prefer apply_url (from jobs table), fallback to original_url (from click_events)
                        st.write(f"**Link:** {event.get('apply_url') or event.get('original_url') or 'N/A'}")

                        # Show quality/route info if available
                        if event.get('match'):
                            st.write(f"**Match Quality:** {format_match_quality(event.get('match'))}")
                        if event.get('route'):
                            st.write(f"**Route Type:** {event.get('route')}")
                        if event.get('market'):
                            st.write(f"**Market:** {event.get('market')}")
            else:
                st.info("No job views yet. Start searching to see your history here!")

        except Exception as e:
            st.error(f"Error loading activity data: {e}")
            st.info("Your activity tracking will appear here once you start viewing jobs.")

if __name__ == "__main__":
    main()
