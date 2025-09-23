"""
FreeWorld Success Coach Portal - Clean Market Names v2.1
Safe wrapper around existing stable pipeline - NO MODIFICATIONS TO MAIN CODE
DEPLOYMENT VERSION: August 28, 2025 - Markets should show Houston, Dallas, Phoenix etc
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from pipeline_wrapper import StreamlitPipelineWrapper
from user_management import get_coach_manager, check_coach_permission, require_permission, get_current_coach_name

# Page config with FreeWorld branding
st.set_page_config(
    page_title="FreeWorld Job Scraper - Career Coach Portal",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# FreeWorld brand colors and styling
st.markdown("""
<style>
    /* FreeWorld brand colors */
    :root {
        --fw-primary-green: #00B04F;
        --fw-light-green: #4CAF50;
        --fw-dark-green: #388E3C;
        --fw-midnight: #1A1A1A;
        --fw-horizon-grey: #F5F5F5;
    }
    
    /* Custom styling for FreeWorld branding */
    .main-header {
        background: linear-gradient(90deg, var(--fw-primary-green) 0%, var(--fw-light-green) 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .stButton > button {
        background-color: var(--fw-primary-green);
        color: white;
        border-radius: 5px;
        border: none;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background-color: var(--fw-dark-green);
        color: white;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--fw-horizon-grey);
    }
    
    /* Success messages */
    .stSuccess {
        border-left: 4px solid var(--fw-primary-green);
    }
</style>
""", unsafe_allow_html=True)

# Success Coach Authentication
def authenticate_coach():
    """Success Coach login system"""
    
    if "current_coach" not in st.session_state:
        st.session_state.current_coach = None
    
    if st.session_state.current_coach is None:
        # Login page
        col_logo, col_login = st.columns([1, 2])
        
        with col_logo:
            logo_path = "assets/FW-Wordmark-Roots@3x.png"
            if os.path.exists(logo_path):
                st.image(logo_path, width=200)
        
        with col_login:
            st.markdown("### 🚛 Success Coach Portal")
            st.markdown("**FreeWorld Job Scraper** - Find quality CDL driver positions for Free Agents")
            
            # Login form
            with st.form("coach_login"):
                username = st.text_input("Username", placeholder="jessica.martinez")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("🔓 Sign In", width=None)
                
                if submit:
                    coach_manager = get_coach_manager()
                    coach = coach_manager.authenticate(username, password)
                    
                    if coach:
                        st.session_state.current_coach = coach
                        st.success(f"✅ Welcome {coach.full_name}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
            
            # Help text
            st.markdown("---")
            st.info("💡 **Default accounts for testing:**\n\n"
                   "**Admin**: `admin` / `admin123`\n\n"
                   "**Sample Coach**: `sarah.johnson` / `coach123`")
        
        st.stop()

def main():
    """Main Streamlit application"""
    
    # Check authentication first
    authenticate_coach()
    
    # Get current coach info
    coach = st.session_state.current_coach
    coach_manager = get_coach_manager()
    
    # Initialize pipeline wrapper
    @st.cache_resource
    def get_pipeline():
        return StreamlitPipelineWrapper()
    
    pipeline = get_pipeline()
    
    # Coach header with logout
    col_name, col_logout = st.columns([3, 1])
    with col_name:
        st.markdown(f"### 👋 Welcome, {coach.full_name}")
        st.caption(f"Role: {coach.role.title()} | Budget: ${coach.monthly_budget - coach.current_month_spending:.2f} remaining")
    with col_logout:
        if st.button("🚪 Logout"):
            st.session_state.current_coach = None
            st.rerun()
    
    # FreeWorld branded header with logo
    col_logo, col_title = st.columns([1, 4])
    
    with col_logo:
        # Try to display FreeWorld logo (deployment-ready path)
        logo_path = "assets/FW-Wordmark-Roots@3x.png"
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
        else:
            st.markdown("### 🚛")
    
    with col_title:
        st.markdown("""
        <div class="main-header">
            <h1>FreeWorld Job Scraper</h1>
            <p>Career Coach Portal - Find quality CDL driver positions for Free Agents</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Admin panel (only for admins)
    if coach.role == 'admin':
        with st.sidebar.expander("👑 Admin Panel", expanded=False):
            admin_tab = st.selectbox("Admin Function", ["Manage Coaches", "View Analytics", "System Settings"])
            
            if admin_tab == "Manage Coaches":
                st.markdown("**Add New Coach**")
                with st.form("add_coach"):
                    new_username = st.text_input("Username", placeholder="new.coach")
                    new_fullname = st.text_input("Full Name", placeholder="New Coach")
                    new_email = st.text_input("Email", placeholder="new@freeworld.com")
                    new_password = st.text_input("Password", placeholder="coach123")
                    if st.form_submit_button("➕ Add Coach"):
                        if coach_manager.create_coach(new_username, new_fullname, new_email, new_password):
                            st.success(f"✅ Created coach: {new_fullname}")
                        else:
                            st.error("❌ Username already exists")
                
                st.markdown("**Existing Coaches**")
                for username, existing_coach in coach_manager.coaches.items():
                    if username != 'admin':  # Don't show admin in list
                        with st.expander(f"{existing_coach.full_name} ({username})"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Role:** {existing_coach.role}")
                                st.write(f"**Budget:** ${existing_coach.monthly_budget}")
                                st.write(f"**Spent:** ${existing_coach.current_month_spending}")
                            with col2:
                                st.write(f"**Searches:** {existing_coach.total_searches}")
                                st.write(f"**Jobs Found:** {existing_coach.total_jobs_processed}")
    
    # Sidebar controls
    st.sidebar.header("🎯 Search Parameters")
    
    # Location selection - Permission-based
    location_options = ["Select Market"]
    if check_coach_permission('can_use_custom_locations'):
        location_options.append("Custom Location")
    else:
        st.sidebar.info("💡 Custom locations disabled. Contact admin to enable.")
    
    location_type = st.sidebar.radio(
        "Location Type:",
        location_options,
        help="Choose from preset markets or enter a custom location"
    )
    
    location = None
    custom_location = None
    
    if location_type == "Select Market":
        markets = pipeline.get_markets()
        # Debug: Show current markets being loaded
        st.sidebar.write(f"🔍 Debug - Markets loaded: {markets}")

        # Optional multi-market selection
        multi_market = st.sidebar.checkbox(
            "Select multiple markets",
            value=False,
            help="Run the search across multiple markets"
        )

        selected_markets = []
        if multi_market:
            selected_markets = st.sidebar.multiselect(
                "Target Markets:",
                markets,
                default=[],
                help="Choose one or more markets"
            )
            if selected_markets:
                st.sidebar.info(f"🗺️ Selected {len(selected_markets)} market(s)")
        else:
            selected_market = st.sidebar.selectbox(
                "Target Market:",
                markets,
                help="Select from available markets"
            )
            location = pipeline.get_market_location(selected_market)
            st.sidebar.info(f"📍 Query Location: {location}")
        
    else:  # Custom Location
        custom_location = st.sidebar.text_input(
            "Custom Location:",
            placeholder="e.g., Austin, TX or 90210",
            help="Enter city, state, or ZIP code"
        )
        location = custom_location
    
    # Search parameters
    route_filter = st.sidebar.selectbox(
        "Route Preference:",
        ["both", "local", "regional", "otr"],
        help="Filter jobs by route type"
    )
    
    # Search mode - Permission-based
    search_options = ["test", "sample", "medium", "large"]
    if check_coach_permission('can_access_full_mode'):
        search_options.append("full")
    else:
        st.sidebar.info("💡 Full mode (1000 jobs) disabled. Contact admin to enable.")
    
    search_mode = st.sidebar.selectbox(
        "Search Mode:",
        search_options,
        index=1,  # default to sample
        help="Number of jobs to analyze (test=100, sample=100, medium=250, large=500, full=1000)"
    )
    
    search_terms = st.sidebar.text_input(
        "Search Terms:",
        value="CDL driver",
        help="Job search keywords"
    )
    
    # Search radius
    search_radius = st.sidebar.selectbox(
        "Search Radius:",
        [25, 50, 100],
        index=1,  # default to 50
        help="Search radius in miles from target location"
    )
    
    # Experience filter
    no_experience = st.sidebar.checkbox(
        "Include No-Experience Jobs", 
        value=True,
        help="Include jobs that don't require prior experience"
    )
    
    # Advanced options - Permission-based controls
    with st.sidebar.expander("🔧 Advanced Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            generate_pdf = st.checkbox("Generate PDF Report", value=True, disabled=not check_coach_permission('can_generate_pdf'))
            generate_csv = st.checkbox("Generate CSV Export", value=True, disabled=not check_coach_permission('can_generate_csv')) 
            push_to_airtable = st.checkbox("Sync to Airtable", value=False, disabled=not check_coach_permission('can_sync_airtable'))
            
        with col2:
            force_fresh = st.checkbox("Force Fresh Jobs", value=False, help="Bypass cost savings, get fresh jobs only")
            use_multi_search = st.checkbox("Multi-Search Strategy", value=False, disabled=not check_coach_permission('can_use_multi_search'), help="Enhanced job discovery with multiple search variations")
            save_parquet = st.checkbox("Save Parquet Files", value=False, help="Save pipeline stage data for debugging")
    
    # Pipeline Settings (matching GUI wrapper functionality)
    with st.sidebar.expander("⚙️ Pipeline Settings"):
        st.markdown("**Quality Filters**")
        enable_business_rules = st.checkbox("Business Rules Filter", value=True, help="Remove spam and low-quality jobs")
        enable_deduplication = st.checkbox("Deduplication", value=True, help="Remove duplicate job postings")
        enable_experience_filter = st.checkbox("Experience Level Filter", value=True, help="Filter by experience requirements")
        
        st.markdown("**Data Processing**")
        classification_model = st.selectbox("AI Classification Model", ["gpt-4o-mini", "gpt-4o"], index=0)
        batch_size = st.number_input("Batch Size", min_value=1, max_value=100, value=25, help="Jobs processed per API call")
        
        if st.button("🔄 Reset to Defaults"):
            st.rerun()
    
    # Cost estimation
    if location:
        cost_info = pipeline.estimate_cost(search_mode, 1)
        st.sidebar.markdown("---")
        st.sidebar.markdown("💰 **Cost Estimate**")
        st.sidebar.metric(
            f"Search Cost ({search_mode})",
            f"${cost_info['total_cost']:.3f}",
            help=f"Analyzing {cost_info['job_limit']} jobs"
        )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Run button
        has_markets = 'selected_markets' in locals() and isinstance(selected_markets, list) and len(selected_markets) > 0
        run_disabled = (not location and not has_markets) or (location_type == "Custom Location" and not custom_location)
        
        if st.button(
            "🚀 Run Job Search", 
            disabled=run_disabled,
            type="primary",
            width=None
        ):
            if not location and not has_markets:
                st.error("❌ Please select a market or enter a custom location")
                st.stop()
            
            # Build parameters
            params = {
                'location': location,
                'mode': search_mode,
                'route_filter': route_filter,
                'search_terms': search_terms,
                'custom_location': custom_location,
                'push_to_airtable': push_to_airtable,
                'generate_pdf': generate_pdf,
                'generate_csv': generate_csv,
                'search_radius': search_radius,
                'no_experience': no_experience,
                'force_fresh': force_fresh,
                'use_multi_search': use_multi_search,
                'coach_name': coach.full_name
            }

            # Pass multi-market selection if provided
            if location_type == "Select Market" and has_markets:
                params['markets'] = selected_markets
            
            # Run pipeline with progress bar
            target_label = location if location else f"{len(selected_markets)} markets"
            with st.spinner(f"🔍 Searching for jobs in {target_label}..."):
                df, metadata = pipeline.run_pipeline(params)
            
            # Store results in session state
            st.session_state.last_results = {
                'df': df,
                'metadata': metadata,
                'params': params,
                'timestamp': datetime.now()
            }
            
            # Show results and update coach stats
            if metadata.get('success', False):
                # Compute quality jobs across all markets for the success message
                try:
                    ai_series = df.get('ai.match')
                    if ai_series is not None:
                        _q = int((ai_series == 'good').sum() + (ai_series == 'so-so').sum())
                    elif 'route.final_status' in df.columns:
                        _q = int(df['route.final_status'].astype(str).str.startswith('included').sum())
                    else:
                        _q = len(df)
                except Exception:
                    _q = metadata.get('included_jobs', 0)
                st.success(f"✅ Search completed! Found {_q} quality jobs")
                
                # Record search in coach's usage stats
                coach_manager.record_search(
                    coach.username, 
                    metadata.get('included_jobs', 0),
                    metadata.get('total_cost', 0.0)
                )
            else:
                st.error(f"❌ Search failed: {metadata.get('error', 'Unknown error')}")
    
    with col2:
        # Configuration Preview
        st.markdown("⚙️ **Configuration Preview**")
        
        if location or has_markets:
            mode_limits = {'test': '10', 'sample': '100', 'medium': '250', 'large': '500', 'full': '1000'}
            if has_markets and not location:
                loc_label = f"{len(selected_markets)} markets: {', '.join(selected_markets[:3])}{'…' if len(selected_markets) > 3 else ''}"
            else:
                loc_label = location
            config_preview = f"""
**Location:** {loc_label}
**Search Mode:** {search_mode} ({mode_limits[search_mode]} jobs)
**Route Filter:** {route_filter}
**Search Terms:** {search_terms}
**Radius:** {search_radius} miles
**No Experience:** {'✅' if no_experience else '❌'}
**Generate PDF:** {'✅' if generate_pdf else '❌'}
**Generate CSV:** {'✅' if generate_csv else '❌'}
**Sync to Airtable:** {'✅' if push_to_airtable else '❌'}
**Force Fresh:** {'✅' if force_fresh else '❌'}
**Multi-Search:** {'✅' if use_multi_search else '❌'}
            """
            st.text(config_preview)
        else:
            st.info("👆 Select location to see configuration")
        
        # Search status
        if 'last_results' in st.session_state:
            st.markdown("---")
            results = st.session_state.last_results
            metadata = results['metadata']
            
            st.markdown("📊 **Last Search Results**")
            
            if metadata.get('success', False):
                st.metric("Quality Jobs Found", metadata.get('included_jobs', 0))
                st.metric("Total Jobs Analyzed", metadata.get('total_jobs', 0))
                st.caption(f"Search completed: {results['timestamp'].strftime('%Y-%m-%d %H:%M')}")
            else:
                st.error("Last search failed")
    
    # Results display
    if 'last_results' in st.session_state:
        results = st.session_state.last_results
        df = results['df']
        metadata = results['metadata']
        
        if not df.empty and metadata.get('success', False):
            st.markdown("---")
            st.markdown("## 📋 Search Results")
            
            # Results tabs
            tab1, tab2, tab3 = st.tabs(["📊 Data View", "📄 Export Options", "🔄 Sync Options"])
            
            with tab1:
                # Display dataframe
                st.dataframe(
                    df,
                    width=None,
                    height=400
                )
                
                # Basic stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    good_jobs = len(df[df.get('classification', '') == 'good']) if 'classification' in df.columns else 0
                    st.metric("Excellent Matches", good_jobs)
                with col2:
                    so_so_jobs = len(df[df.get('classification', '') == 'so-so']) if 'classification' in df.columns else 0
                    st.metric("Possible Fits", so_so_jobs)
                with col3:
                    route_local = len(df[df.get('route_type', '') == 'local']) if 'route_type' in df.columns else 0
                    st.metric("Local Routes", route_local)
            
            with tab2:
                st.markdown("### 📁 Download Results")
                
                # CSV Download
                csv_bytes = pipeline.dataframe_to_csv_bytes(df)
                if csv_bytes:
                    loc_for_name = results['params'].get('location') or (
                        f"{len(results['params'].get('markets', []))}_markets" if results['params'].get('markets') else 'results'
                    )
                    st.download_button(
                        label="📊 Download CSV",
                        data=csv_bytes,
                        file_name=f"freeworld_jobs_{str(loc_for_name).replace(', ', '_').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        width=None
                    )
                
                # PDF Download - Generate from canonical DataFrame
                if results['params'].get('generate_pdf', True):
                    # Filter to quality jobs only for PDF
                    quality_df = df
                    if 'ai.match' in df.columns:
                        quality_df = df[df['ai.match'].isin(['good', 'so-so'])]
                    
                    if not quality_df.empty:
                        # Generate PDF button
                        if st.button("📄 Generate PDF Report", width=None):
                            with st.spinner("Generating PDF report..."):
                                market_name = results['params'].get('location') or 'Multiple Markets'
                                pdf_bytes = pipeline.generate_pdf_from_canonical(quality_df, market_name)
                            
                            if pdf_bytes:
                                st.download_button(
                                    label="📥 Download PDF Report",
                                    data=pdf_bytes,
                                    file_name=f"freeworld_jobs_{market_name.replace(', ', '_').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                    mime="application/pdf",
                                    width=None
                                )
                                st.success("✅ PDF generated successfully!")
                            else:
                                st.error("❌ PDF generation failed")
                    else:
                        st.info("No quality jobs found for PDF generation")
                else:
                    st.info("PDF generation was disabled for this search")
            
            with tab3:
                st.markdown("### 🔄 Database Sync")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📊 Sync to Supabase", width=None):
                        with st.spinner("Syncing to Supabase..."):
                            success = pipeline.upload_to_supabase(df)
                        
                        if success:
                            st.success("✅ Supabase sync completed")
                        else:
                            st.error("❌ Supabase sync failed")
                
                with col2:
                    if st.button("📋 Sync to Airtable", width=None):
                        with st.spinner("Syncing to Airtable..."):
                            success = pipeline.upload_to_airtable(df)
                        
                        if success:
                            st.success("✅ Airtable sync completed") 
                        else:
                            st.error("❌ Airtable sync failed")
                
                st.info("💡 Tip: Enable auto-sync in Advanced Options to sync automatically during search")
    
    # Analytics Dashboard (matching GUI wrapper)
    if 'last_results' in st.session_state:
        st.markdown("---")
        st.markdown("## 📊 Pipeline Analytics")
        
        results = st.session_state.last_results
        metadata = results['metadata']
        
        if metadata.get('success', False):
            # Pipeline performance metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Pipeline Efficiency", 
                    f"{(metadata.get('included_jobs', 0) / max(1, metadata.get('total_jobs', 1))) * 100:.1f}%",
                    help="Percentage of jobs that passed all filters"
                )
            
            with col2:
                cost_per_job = metadata.get('total_cost', 0) / max(1, metadata.get('included_jobs', 1))
                st.metric(
                    "Cost per Quality Job",
                    f"${cost_per_job:.3f}",
                    help="Average cost to find one quality job"
                )
            
            with col3:
                processing_time = metadata.get('processing_time', 0)
                st.metric(
                    "Processing Time",
                    f"{processing_time:.1f}s",
                    help="Total pipeline execution time"
                )
            
            with col4:
                memory_savings = metadata.get('memory_jobs', 0) / max(1, metadata.get('total_jobs', 1)) * 100
                st.metric(
                    "Memory Efficiency",
                    f"{memory_savings:.1f}%",
                    help="Percentage of jobs loaded from memory vs fresh scraping"
                )
            
            # Pipeline stage breakdown
            if 'stage_metrics' in metadata:
                st.markdown("### 🔧 Pipeline Stage Performance")
                stage_data = []
                for stage, metrics in metadata['stage_metrics'].items():
                    stage_data.append({
                        'Stage': stage,
                        'Input Jobs': metrics.get('input', 0),
                        'Output Jobs': metrics.get('output', 0),
                        'Filtered': metrics.get('filtered', 0),
                        'Processing Time': f"{metrics.get('time', 0):.1f}s" if metrics.get('time', 0) < 60 else f"{int(metrics.get('time', 0) // 60)}m {metrics.get('time', 0) % 60:.1f}s"
                    })
                
                if stage_data:
                    st.dataframe(pd.DataFrame(stage_data), width=None)

if __name__ == "__main__":
    main()
