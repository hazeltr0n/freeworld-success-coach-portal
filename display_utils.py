#!/usr/bin/env python3
"""
Display utilities for consistent DataFrame column ordering across the application.
Centralizes column definitions to avoid duplication and ensure consistency.
"""

def get_quality_display_columns():
    """
    Get column order for quality jobs display - matches PDF card layout.

    Returns:
        list: Column names in display order
    """
    return [
        'source.title',           # Job Title (main identifier)
        'source.company',         # Company (key info)
        'source.location',        # Location (geographic relevance)
        'ai.route_type',          # Route Type (Local/Regional/OTR)
        'ai.match',              # Match Quality (good/so-so/bad)
        'ai.career_pathway',     # Career Pathway (e.g., cdl_pathway, dock_to_driver)
        'ai.training_provided',  # Training Provided (boolean)
        'ai.fair_chance',        # Fair Chance Employer (boolean)
        'ai.summary',            # Job Description Summary
        'meta.tracked_url'       # Apply Link (for testing)
    ]

def get_full_dataframe_columns():
    """
    Get column order for full DataFrame display - testing/debugging priority.

    Returns:
        list: Column names in display order (testing fields first)
    """
    return [
        # Testing & Debug Priority (leftmost)
        'ai.match',              # Quality classification
        'ai.route_type',         # Route classification
        'ai.career_pathway',     # Career pathway classification
        'ai.training_provided',  # Training provided flag
        'sys.is_fresh_job',      # Fresh vs memory

        # Core Job Info (center)
        'source.title',          # Job title
        'source.company',        # Company
        'source.location',       # Location
        'ai.fair_chance',       # Fair chance status
        'ai.summary',           # AI summary

        # URLs (rightmost)
        'meta.tracked_url'       # Tracking URL
    ]

def filter_available_columns(columns, dataframe):
    """
    Filter column list to only include columns that exist in the DataFrame.

    Args:
        columns (list): Desired column order
        dataframe (pd.DataFrame): DataFrame to check for column existence

    Returns:
        list: Available columns in the desired order
    """
    return [col for col in columns if col in dataframe.columns]

def reorder_dataframe_columns(df, desired_columns):
    """
    Reorder DataFrame columns according to desired order, keeping extra columns at the end.

    Args:
        df (pd.DataFrame): DataFrame to reorder
        desired_columns (list): Desired column order

    Returns:
        pd.DataFrame: DataFrame with reordered columns
    """
    available_desired = filter_available_columns(desired_columns, df)
    remaining_columns = [col for col in df.columns if col not in available_desired]
    final_column_order = available_desired + remaining_columns

    return df[final_column_order]

def get_quality_display_dataframe(df):
    """
    Get quality jobs DataFrame with proper column ordering and filtering.

    Args:
        df (pd.DataFrame): Source DataFrame

    Returns:
        pd.DataFrame: Quality jobs with display columns in proper order
    """
    # Filter to quality jobs only
    quality_df = df[df.get('ai.match', '').isin(['good', 'so-so'])].copy()
    if quality_df.empty:
        quality_df = df.copy()

    # Get available display columns and reorder
    display_cols = get_quality_display_columns()
    available_cols = filter_available_columns(display_cols, quality_df)

    if available_cols:
        return quality_df[available_cols].copy().reset_index(drop=True)
    else:
        # Fallback to original DataFrame if no display columns available
        return quality_df.reset_index(drop=True)

def get_full_display_dataframe(df):
    """
    Get full DataFrame with proper column ordering for testing/debugging.

    Args:
        df (pd.DataFrame): Source DataFrame

    Returns:
        pd.DataFrame: Full DataFrame with columns in testing-friendly order
    """
    desired_cols = get_full_dataframe_columns()
    return reorder_dataframe_columns(df, desired_cols).reset_index(drop=True)


# === NEW UTILITY FUNCTIONS TO ELIMINATE DUPLICATION ===

import streamlit as st
from typing import Dict

# Critical imports for HTML preview functionality
try:
    from pdf.html_pdf_generator import jobs_dataframe_to_dicts, render_jobs_html
except ImportError:
    jobs_dataframe_to_dicts = None
    render_jobs_html = None


def wrap_html_in_phone_screen(html_content: str) -> str:
    """Wrap HTML content in a phone screen container for preview only."""
    return f"""
    <div style="
        display: flex;
        justify-content: center;
        align-items: flex-start;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    ">
        <div style="
            width: 375px;
            max-width: 100%;
            background: #000;
            border-radius: 25px;
            padding: 8px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            position: relative;
        ">
            <!-- Phone notch -->
            <div style="
                position: absolute;
                top: 8px;
                left: 50%;
                transform: translateX(-50%);
                width: 120px;
                height: 25px;
                background: #000;
                border-radius: 15px;
                z-index: 10;
            "></div>

            <!-- Phone screen -->
            <div style="
                background: #fff;
                border-radius: 20px;
                overflow: hidden;
                height: 812px;
                overflow-y: auto;
                position: relative;
                -webkit-overflow-scrolling: touch;
            ">
                <!-- Status bar -->
                <div style="
                    height: 44px;
                    background: #fff;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0 20px;
                    font-size: 14px;
                    font-weight: 600;
                    color: #000;
                    border-bottom: 1px solid #e5e7eb;
                ">
                    <span>9:41</span>
                    <div style="display: flex; gap: 4px; align-items: center;">
                        <div style="width: 18px; height: 10px; border: 1px solid #000; border-radius: 2px; position: relative;">
                            <div style="width: 14px; height: 6px; background: #000; border-radius: 1px; position: absolute; top: 1px; left: 1px;"></div>
                        </div>
                        <span style="font-size: 12px;">100%</span>
                    </div>
                </div>

                <!-- Content -->
                <div style="
                    padding: 0;
                    height: calc(812px - 44px);
                    overflow-y: auto;
                ">
                    {html_content}
                </div>
            </div>
        </div>
    </div>
    """


def render_search_summary_header(title: str = "Search Results Summary") -> None:
    """
    Render the search results summary header.

    Eliminates duplicate "📊 Search Results Summary" headers across
    main search path (line 4163) and memory search path (line 5663).

    Args:
        title: The title text to display (default: "Search Results Summary")
    """
    st.markdown(f"### 📊 {title}")


def calculate_quality_metrics(df) -> Dict[str, int]:
    """
    Calculate quality metrics from job search results DataFrame.

    Args:
        df: DataFrame containing job search results with 'ai.match' column

    Returns:
        Dictionary containing:
        - total_jobs: Total number of jobs
        - quality_jobs: Number of 'good' quality jobs
        - good_jobs: Number of 'good' rated jobs
        - soso_jobs: Number of 'so-so' rated jobs
        - bad_jobs: Number of 'bad' rated jobs
    """
    total_jobs = len(df)
    quality_jobs = 0
    good_jobs = 0
    soso_jobs = 0
    bad_jobs = 0

    if 'ai.match' in df.columns:
        good_jobs = int((df['ai.match'] == 'good').sum())
        soso_jobs = int((df['ai.match'] == 'so-so').sum())
        bad_jobs = int((df['ai.match'] == 'bad').sum())
        quality_jobs = good_jobs + soso_jobs  # Quality jobs = good + so-so

    return {
        'total_jobs': total_jobs,
        'quality_jobs': quality_jobs,
        'good_jobs': good_jobs,
        'soso_jobs': soso_jobs,
        'bad_jobs': bad_jobs
    }


def render_quality_metrics(metrics: Dict[str, int]) -> None:
    """
    Render quality metrics in a column layout.

    Args:
        metrics: Dictionary from calculate_quality_metrics()
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Jobs", metrics['total_jobs'])
    with col2:
        st.metric("Quality Jobs", metrics['quality_jobs'])
    with col3:
        st.metric("Good Jobs", metrics['good_jobs'])
    with col4:
        st.metric("So-So Jobs", metrics['soso_jobs'])


def render_supabase_upload_info(metadata: Dict) -> None:
    """
    Render Supabase upload confirmation information.
    Args:
        metadata: Pipeline metadata containing supabase_upload_count
    """
    upload_count = metadata.get('supabase_upload_count', 0)
    if upload_count > 0:
        st.success(f"✅ Successfully uploaded {upload_count} fresh jobs to Supabase database")
    elif upload_count == 0:
        st.info("ℹ️ No new jobs were uploaded to Supabase (jobs may be from memory cache)")
    else:
        st.warning("⚠️ Supabase upload status unknown")


def calculate_route_distribution(df) -> Dict[str, int]:
    """
    Calculate route type distribution from job search results DataFrame.

    Args:
        df: DataFrame containing job search results with 'ai.route_type' column

    Returns:
        Dictionary containing route counts (e.g., {'local': 5, 'regional': 3, 'otr': 2})
    """
    route_counts = {}
    if 'ai.route_type' in df.columns:
        route_counts = df['ai.route_type'].value_counts().to_dict()
    return route_counts


def render_html_preview(df, location, candidate_name, candidate_id, max_jobs="All",
                       pdf_fair_chance_only=False, is_memory_search=False, title="HTML Preview"):
    """
    Render HTML preview with phone screen display, preserving debugged memory search logic.

    This function consolidates the 4x duplicated HTML preview functionality while
    preserving the user's debugged logic from the memory search path.

    Args:
        df: DataFrame containing job results
        location: Location for agent params
        candidate_name: Candidate name for agent params
        candidate_id: Candidate ID for agent params
        max_jobs: Maximum jobs to display ("All" or number)
        pdf_fair_chance_only: Whether to filter for fair chance only (main path)
        is_memory_search: True for memory search (uses simplified filtering)
        title: Title for the preview section
    """
    try:
        st.markdown(f"### 👁️ {title}")

        # Check for required dependencies first
        if jobs_dataframe_to_dicts is None or render_jobs_html is None:
            st.warning("📱 HTML preview unavailable: PDF generation dependencies not installed")
            st.info("This feature requires the pdf.html_pdf_generator module")
            return

        # Validate input parameters
        if df is None or df.empty:
            st.warning("📱 No jobs available for HTML preview")
            return

        if not candidate_name or not candidate_id:
            st.warning("📱 HTML preview requires candidate name and ID")
            return

        # Import required functions with error handling
        try:
            from free_agent_system import update_job_tracking_for_agent
        except ImportError:
            st.error("❌ Cannot import update_job_tracking_for_agent from free_agent_system")
            return

        try:
            from user_management import get_current_coach_name
        except ImportError:
            st.error("❌ Cannot import get_current_coach_name from user_management")
            return

        # Build agent params with validation
        try:
            coach_username = get_current_coach_name()
        except Exception as e:
            st.warning(f"⚠️ Could not get coach name: {e}")
            coach_username = "Unknown Coach"

        agent_params = {
            'location': location or "",
            'agent_name': candidate_name,
            'agent_uuid': candidate_id,
            'coach_username': coach_username,
            'show_prepared_for': st.session_state.get('tab_show_prepared_for', True)
        }

        # Apply filtering based on search type (preserving debugged memory logic)
        try:
            if is_memory_search:
                # Memory search: "Supabase has already filtered by route type, quality, and fair chance - no post-processing needed"
                filtered_df = df.copy()
                # Apply max jobs limit only (Supabase already handled filtering)
                if max_jobs != "All" and str(max_jobs).isdigit():
                    filtered_df = filtered_df.head(int(max_jobs))
            else:
                # Main search: Apply same filtering as PDF
                filtered_df = df.copy()
                if pdf_fair_chance_only and 'ai.fair_chance_employer' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['ai.fair_chance_employer'] == True]
                if max_jobs != "All" and str(max_jobs).isdigit():
                    filtered_df = filtered_df.head(int(max_jobs))
        except Exception as e:
            st.error(f"❌ Error filtering DataFrame: {e}")
            filtered_df = df.copy()

        # Process DataFrame the same way PDF does
        try:
            processed_df = update_job_tracking_for_agent(filtered_df, agent_params)
        except Exception as e:
            st.error(f"❌ Error processing job tracking: {e}")
            processed_df = filtered_df

        # Convert to jobs format and render HTML
        try:
            jobs = jobs_dataframe_to_dicts(processed_df, candidate_id=agent_params.get('agent_uuid'))
            if not jobs:
                st.warning("📱 No jobs found after processing")
                return
        except Exception as e:
            st.error(f"❌ Error converting DataFrame to jobs: {e}")
            return

        try:
            html = render_jobs_html(jobs, agent_params)
            if not html or not html.strip():
                st.warning("📱 Generated HTML is empty")
                return
        except Exception as e:
            st.error(f"❌ Error rendering jobs HTML: {e}")
            return

        try:
            phone_html = wrap_html_in_phone_screen(html)
        except Exception as e:
            st.error(f"❌ Error wrapping HTML in phone screen: {e}")
            return

        # Store HTML preview data in session state for persistence
        try:
            if 'last_results' in st.session_state:
                st.session_state.last_results['html_preview_data'] = {
                    'agent_params': agent_params,
                    'phone_html': phone_html,
                    'job_count': len(jobs)
                }
        except Exception as e:
            st.warning(f"⚠️ Could not store HTML preview data: {e}")

        # Render the final HTML preview
        try:
            st.components.v1.html(phone_html, height=900, scrolling=False)
            st.success(f"📱 HTML preview generated successfully ({len(jobs)} jobs)")
        except Exception as e:
            st.error(f"❌ Error displaying HTML preview: {e}")
            st.text_area("Raw HTML Output (for debugging):", phone_html[:1000] + "..." if len(phone_html) > 1000 else phone_html, height=200)

    except Exception as e:
        st.error(f"❌ Critical HTML preview error: {e}")
        st.exception(e)
        st.info("💡 This may be due to missing dependencies or invalid input data")


def render_route_distribution(route_counts: Dict[str, int]) -> None:
    """
    Render route distribution in a column layout.

    Args:
        route_counts: Dictionary containing route counts (e.g., {'local': 5, 'regional': 3, 'otr': 2})
    """
    if route_counts:
        st.markdown("**Route Distribution:**")
        route_cols = st.columns(len(route_counts))
        for i, (route, count) in enumerate(route_counts.items()):
            with route_cols[i]:
                st.metric(str(route), count)


def render_download_button(data, label: str, filename: str, mime_type: str, key: str = None) -> None:
    """
    Render a standardized download button with consistent formatting.

    Args:
        data: The data to download (bytes, string, etc.)
        label: Button label text
        filename: Filename for download
        mime_type: MIME type for the file
        key: Optional unique key for the button
    """
    if data:
        st.download_button(
            label=label,
            data=data,
            file_name=filename,
            mime=mime_type,
            key=key
        )
    else:
        st.error(f"No data available for {label.lower()}")


def render_portal_link_section(search_params: dict, candidate_name: str, candidate_id: str,
                              search_type: str, final_location: str = "",
                              force_fresh_classification: bool = False,
                              is_memory_search: bool = False) -> None:
    """
    Unified portal link generation for all search types.

    Consolidates the 4x duplicated portal link generation code while
    preserving Indeed Fresh restrictions and all business logic.

    Args:
        search_params: Dictionary containing all search form parameters
        candidate_name: Free agent name
        candidate_id: Free agent UUID
        search_type: Type of search (main, memory, indeed_fresh, etc.)
        final_location: Processed location string
        force_fresh_classification: Whether to force fresh AI classification
        is_memory_search: True for memory search paths
    """
    # Validate inputs
    if not candidate_name or not candidate_id:
        st.warning("⚠️ Please provide Free Agent ID and Name to generate a portal link")
        return

    # Block portal links for Indeed searches (business requirement)
    if search_type in ['indeed_fresh', 'indeed']:
        st.info("🔗 Portal links are not available for Indeed searches")
        return

    try:
        st.markdown("### 🔗 Custom Job Portal Link")

        # Build portal configuration from search parameters
        portal_config = {
            # Base parameters from search form
            'mode': search_params.get('mode', 'sample'),
            'search_terms': search_params.get('search_terms', ''),
            'search_radius': search_params.get('search_radius', 50),
            'force_fresh_classification': force_fresh_classification,

            # Location parameters
            'location': final_location,
            'location_type': search_params.get('location_type', 'zip'),

            # Search type specific parameters
            'search_type': search_type,
        }

        # Add memory-specific parameters for memory searches
        if is_memory_search:
            portal_config.update({
                'memory_hours': search_params.get('memory_hours', 72),
                'max_jobs': search_params.get('max_jobs', 50),
                'route_filter': search_params.get('route_filter', 'all'),
                'no_experience': search_params.get('no_experience', False),
                'fair_chance_only': search_params.get('fair_chance_only', False),
            })
        else:
            # Main search parameters
            portal_config.update({
                'route_filter': search_params.get('route_filter', 'all'),
                'no_experience': search_params.get('no_experience', False),
                'fair_chance_only': search_params.get('fair_chance_only', False),
                'max_jobs': search_params.get('max_jobs', 'All'),
                'show_prepared_for': search_params.get('show_prepared_for', True),
            })

        # Generate portal link using free agent system
        try:
            from free_agent_system import generate_agent_url
        except ImportError:
            st.error("❌ Cannot import generate_agent_url from free_agent_system")
            return

        # Add agent and coach info to portal config
        portal_config.update({
            'agent_name': candidate_name.strip(),
            'location': final_location,
            'agent_uuid': candidate_id,
            'coach_username': search_params.get('coach_username', ''),
            'coach_name': search_params.get('coach_name', '')
        })

        # Generate Supabase edge function URL
        try:
            edge_function_url = generate_agent_url(candidate_id, portal_config)
            if not edge_function_url:
                st.error("❌ Failed to generate edge function URL")
                return
        except Exception as e:
            st.error(f"❌ Error generating agent URL: {e}")
            return

        # Create Short.io link
        try:
            from link_tracker import LinkTracker
            link_tracker = LinkTracker()

            # Build tags for analytics
            tags = [
                f"coach:{search_params.get('coach_username', 'unknown')}",
                f"search_type:{search_type}",
                f"mode:{portal_config.get('mode', 'unknown')}"
            ]

            # Add memory-specific tag
            if is_memory_search:
                tags.append("memory_search")

            shortened_url = link_tracker.create_short_link(
                edge_function_url,
                title="Portal Link",
                tags=tags,
                candidate_id=candidate_id
            )

            if shortened_url:
                # Display success message and link
                st.success("✅ Portal link generated successfully!")

                # Display the shortened URL
                st.code(shortened_url, language=None)

                # Copy button (simulated)
                if st.button("📋 Copy Portal Link", key=f"copy_portal_{candidate_id}"):
                    st.success("Portal link copied to clipboard!")

                # Store portal link data in session state for persistence
                try:
                    if 'last_results' in st.session_state:
                        st.session_state.last_results['portal_link_data'] = {
                            'agent_params': {
                                'agent_uuid': candidate_id,
                                'agent_name': candidate_name,
                                'location': final_location
                            },
                            'shortened_url': shortened_url,
                            'portal_config': portal_config
                        }
                except Exception as e:
                    st.warning(f"⚠️ Could not store portal link data: {e}")

                # Display portal configuration for debugging (if enabled)
                if st.session_state.get('show_debug_info', False):
                    st.expander("🔧 Portal Configuration (Debug)", expanded=False).json(portal_config)

            else:
                st.error("❌ Failed to create Short.io link")

        except ImportError:
            st.error("❌ Link tracking module not available")
        except Exception as e:
            st.error(f"❌ Error creating short link: {e}")

    except Exception as e:
        st.error(f"❌ Portal link generation error: {e}")


def run_progressive_pipeline(pipeline, params, display_location: str = None):
    """
    Run pipeline with LIVE stage-by-stage UI feedback showing job counts as each stage executes

    Args:
        pipeline: Pipeline wrapper instance
        params: Pipeline parameters
        display_location: Location name for UI display

    Returns:
        Tuple[DataFrame, Dict]: Results and metadata
    """
    import streamlit as st
    import pandas as pd
    from datetime import datetime

    # Default to params location if display_location not provided
    if not display_location:
        display_location = params.get('location', 'Unknown Location')

    # Create stage containers for live updates
    stage_containers = {
        'ingestion': st.empty(),
        'normalization': st.empty(),
        'business_rules': st.empty(),
        'deduplication': st.empty(),
        'ai_classification': st.empty(),
        'routing': st.empty(),
        'outputs': st.empty()
    }

    # Initialize results
    df = pd.DataFrame()
    metadata = {'success': False, 'error': None}

    try:
        # Start pipeline execution with live updates
        start_time = datetime.now()

        # Get direct access to pipeline_v3 for stage-by-stage execution
        if params.get('ui_direct', False) and not params.get('memory_only', False):
            from pipeline_v3 import FreeWorldPipelineV3

            # Initialize pipeline if needed
            if not hasattr(pipeline, 'pipeline_v3') or pipeline.pipeline_v3 is None:
                pipeline.pipeline_v3 = FreeWorldPipelineV3()

            pipe = pipeline.pipeline_v3

            # Build mode info and basic setup
            mode = params.get('mode', 'sample')
            job_limits = {"test": 10, "mini": 50, "sample": 100, "medium": 250, "large": 500, "full": 1000}
            mode_info = {"mode": mode, "limit": job_limits.get(mode, 100)}

            # Get location to run
            location = params.get('custom_location') or params.get('location', display_location)

            # Import required modules
            from jobs_schema import build_empty_df

            # STAGE 1: INGESTION
            with stage_containers['ingestion']:
                search_type = "Indeed Fresh" if params.get('force_fresh') else "Indeed + Memory"
                st.info(f"📥 Ingesting jobs from {search_type} for {display_location}...")

            # Initialize canonical DataFrame
            canonical_df = build_empty_df()

            # Execute ingestion stage
            canonical_df = pipe._stage1_ingestion(
                canonical_df, location, mode_info,
                params.get('search_terms', 'CDL Driver No Experience'),
                params.get('route_filter', 'both'),
                params.get('force_fresh', False),
                params.get('memory_only', False),
                classifier_type=params.get('classifier_type', 'cdl'),
                radius=params.get('search_radius', 50),
                no_experience=params.get('no_experience', True),
                search_sources=params.get('search_sources'),
                search_strategy=params.get('search_strategy', 'balanced')
            )

            with stage_containers['ingestion']:
                ingestion_count = len(canonical_df)
                st.success(f"✅ Ingested: {ingestion_count} jobs")

            # STAGE 2: NORMALIZATION
            with stage_containers['normalization']:
                st.info("🧹 Normalizing job fields...")

            canonical_df = pipe._stage2_normalization(canonical_df)

            with stage_containers['normalization']:
                st.success(f"✅ Normalized: {len(canonical_df)} jobs")

            # STAGE 3: BUSINESS RULES
            with stage_containers['business_rules']:
                st.info("🧼 Applying business rules and quality filters...")

            canonical_df = pipe._stage3_business_rules(
                canonical_df,
                location,
                params.get('filter_settings', {})
            )

            with stage_containers['business_rules']:
                st.success(f"✅ Business rules applied: {len(canonical_df)} jobs")

            # STAGE 4: DEDUPLICATION
            with stage_containers['deduplication']:
                st.info("🔄 Deduplicating jobs...")

            canonical_df = pipe._stage4_deduplication(
                canonical_df,
                filter_settings=params.get('filter_settings', {})
            )

            with stage_containers['deduplication']:
                dedup_count = len(canonical_df)
                st.success(f"✅ Deduplicated to: {dedup_count} unique jobs")

            # STAGE 5: AI CLASSIFICATION
            with stage_containers['ai_classification']:
                classifier_type = params.get('classifier_type', 'cdl')
                classifier_emoji = "🎯" if classifier_type == "pathway" else "🚛"
                classifier_name = "Pathway Classifier" if classifier_type == "pathway" else "CDL Classifier"
                st.info(f"🤖 Classifying with AI using {classifier_emoji} {classifier_name}...")

            canonical_df = pipe._stage5_ai_classification(
                canonical_df,
                force_fresh_classification=params.get('force_fresh_classification', False),
                classifier_type=classifier_type
            )

            with stage_containers['ai_classification']:
                # Show real-time match breakdown
                if 'ai.match' in canonical_df.columns:
                    match_counts = canonical_df['ai.match'].value_counts().to_dict()
                    st.write("🔎 Match breakdown:", match_counts)

                    # Show metrics
                    good_jobs = match_counts.get('good', 0)
                    soso_jobs = match_counts.get('so-so', 0)
                    quality_jobs = good_jobs + soso_jobs

                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.metric("Excellent Matches", good_jobs)
                    with m2:
                        st.metric("Possible Fits", soso_jobs)
                    with m3:
                        st.metric("Quality Jobs Total", quality_jobs)

                # Show pathway breakdown for pathway classifier
                if classifier_type == "pathway" and 'ai.career_pathway' in canonical_df.columns:
                    pathway_counts = canonical_df['ai.career_pathway'].value_counts().to_dict()
                    st.write("🎯 Career pathway breakdown:", pathway_counts)

                st.success(f"✅ AI classification completed: {len(canonical_df)} jobs classified")

            # STAGE 5.5: ROUTE RULES
            canonical_df = pipe._stage5_5_route_rules(canonical_df)

            # STAGE 6: ROUTING
            with stage_containers['routing']:
                st.info("🧭 Applying route rules and final routing...")

            canonical_df = pipe._stage6_routing(canonical_df, params.get('route_filter', 'both'))

            with stage_containers['routing']:
                # Show route breakdown
                if 'ai.route_type' in canonical_df.columns:
                    route_counts = canonical_df['ai.route_type'].value_counts().to_dict()
                    local_routes = route_counts.get('Local', 0)
                    otr_routes = route_counts.get('OTR', 0)

                    r1, r2 = st.columns(2)
                    with r1:
                        st.metric("Local Routes", local_routes)
                    with r2:
                        st.metric("OTR Routes", otr_routes)

                st.success(f"✅ Routing completed: {len(canonical_df)} jobs routed")

            # STAGE 7: OUTPUTS
            with stage_containers['outputs']:
                st.info("📄 Generating outputs (CSV, PDF, tracking URLs)...")

            # Generate outputs using pipeline method
            # Note: coach/candidate info should already be in the pipeline params, not passed here
            results = pipe._stage7_output(
                canonical_df,
                location,
                custom_location=params.get('custom_location', ''),
                generate_pdf=params.get('generate_pdf', False),
                generate_csv=True,
                generate_html=True,
                show_prepared_for=params.get('show_prepared_for', True)
            )

            with stage_containers['outputs']:
                # Calculate final statistics
                processing_time = (datetime.now() - start_time).total_seconds()

                # Show final summary
                if 'route.final_status' in canonical_df.columns:
                    included_jobs = (canonical_df['route.final_status'].astype(str).str.startswith('included')).sum()
                else:
                    included_jobs = len(canonical_df)

                final_stats = st.columns(3)
                with final_stats[0]:
                    st.metric("Final Quality Jobs", int(included_jobs))
                with final_stats[1]:
                    st.metric("Processing Time", f"{processing_time:.1f}s")
                with final_stats[2]:
                    st.metric("Total Jobs Processed", len(canonical_df))

                st.success("✅ All outputs generated successfully")

            # Prepare return values
            df = canonical_df
            metadata = {
                'success': True,
                'total_jobs': len(canonical_df),
                'included_jobs': int(included_jobs) if 'included_jobs' in locals() else len(canonical_df),
                'processing_time': processing_time,
                'pdf_path': results.get('pdf_path') if isinstance(results, dict) else None,
                'csv_path': results.get('csv_path') if isinstance(results, dict) else None
            }

        else:
            # Fallback to original pipeline execution for memory-only or other cases
            import contextlib, io

            with stage_containers['ingestion']:
                search_type = "Memory Only" if params.get('memory_only') else "Indeed + Memory"
                st.info(f"📥 Searching {search_type} for {display_location}...")

            log_buffer = io.StringIO()
            with contextlib.redirect_stdout(log_buffer), contextlib.redirect_stderr(log_buffer):
                df, metadata = pipeline.run_pipeline(params)

            if metadata.get('success', False) and not df.empty:
                with stage_containers['ingestion']:
                    st.success(f"✅ Search completed: {len(df)} jobs found")

                # Clear unused stage containers for memory-only path
                for key in ['normalization', 'business_rules', 'deduplication', 'ai_classification', 'routing']:
                    stage_containers[key].empty()

                with stage_containers['outputs']:
                    if 'ai.match' in df.columns:
                        match_counts = df['ai.match'].value_counts().to_dict()
                        good_jobs = match_counts.get('good', 0)
                        soso_jobs = match_counts.get('so-so', 0)

                        m1, m2 = st.columns(2)
                        with m1:
                            st.metric("Excellent Matches", good_jobs)
                        with m2:
                            st.metric("Possible Fits", soso_jobs)

                    st.success("✅ Results ready for display")
            else:
                with stage_containers['ingestion']:
                    error_msg = metadata.get('error', 'No results found')
                    st.error(f"❌ Search failed: {error_msg}")

                # Clear other containers
                for key in ['normalization', 'business_rules', 'deduplication', 'ai_classification', 'routing', 'outputs']:
                    stage_containers[key].empty()

    except Exception as e:
        # Handle unexpected errors
        with stage_containers['ingestion']:
            st.error(f"❌ Pipeline execution error: {str(e)}")

        # Clear other containers
        for key in ['normalization', 'business_rules', 'deduplication', 'ai_classification', 'routing', 'outputs']:
            stage_containers[key].empty()

        metadata = {'success': False, 'error': str(e)}

    return df, metadata


def run_search_with_location_handling(pipeline, params, search_type_tab, coach, candidate_id=None, candidate_name=None):
    """
    Unified function to handle both multi-market and single-market searches for any search type.
    Uses progressive UI for indeed_fresh searches, regular spinner for others.
    Eliminates ~80 lines of duplicate multi-market handling code.

    IMPORTANT: Coach/candidate info is added to params BEFORE pipeline execution,
    not to DataFrame afterward, to avoid parameter conflicts with pipeline.
    """
    import pandas as pd
    import streamlit as st

    # Add coach and candidate information to params BEFORE pipeline execution
    if coach:
        params['coach_name'] = coach.full_name
        params['coach_username'] = coach.username
    if candidate_id:
        params['candidate_id'] = candidate_id
    if candidate_name:
        params['candidate_name'] = candidate_name

    if params.get('location_type') == 'multi_markets':
        # Multi-market search: run pipeline for each market and combine results
        markets = params['markets']
        combined_df = pd.DataFrame()
        combined_metadata = {'success': True, 'message': 'Multi-market search completed'}

        if search_type_tab == 'indeed_fresh':
            # Use progressive output for multi-market indeed_fresh searches
            st.markdown("### 🔍 Multi-Market Pipeline Execution Progress")
            st.markdown("---")

            for i, market in enumerate(markets):
                st.markdown(f"#### 📍 Market {i+1}/{len(markets)}: {market}")

                # Create single-market params for this iteration
                single_market_params = params.copy()
                single_market_params.update({
                    'location_type': 'markets',
                    'markets': [market],  # Pass as list, not string
                    'location': market,
                    'ui_direct': True  # Enable progressive output
                })

                # Run progressive pipeline for this market
                market_df, market_metadata = run_progressive_pipeline(pipeline, single_market_params, market)

                # Add market assignment to all jobs from this search
                if not market_df.empty:
                    market_df['meta.market'] = market
                    combined_df = pd.concat([combined_df, market_df], ignore_index=True)

                # Add separator between markets
                if i < len(markets) - 1:
                    st.markdown("---")
        else:
            # Use simple spinner for other search types
            with st.spinner(f"🔍 Searching {len(markets)} markets: {', '.join(markets)}..."):
                for market in markets:
                    # Create single-market params for this iteration
                    single_market_params = params.copy()
                    single_market_params.update({
                        'location_type': 'markets',
                        'markets': [market],  # Pass as list, not string
                        'location': market
                    })

                    # Run pipeline for this market
                    market_df, market_metadata = pipeline.run_pipeline(single_market_params)

                    # Add market assignment to all jobs from this search
                    if not market_df.empty:
                        market_df['meta.market'] = market
                        combined_df = pd.concat([combined_df, market_df], ignore_index=True)

        df, metadata = combined_df, combined_metadata
    else:
        # Single market/location search
        if search_type_tab == 'indeed_fresh':
            # Use progressive pipeline for Indeed Fresh searches
            st.markdown("### 🔍 Pipeline Execution Progress")
            st.markdown("---")
            params['ui_direct'] = True
            df, metadata = run_progressive_pipeline(pipeline, params, params.get('location', 'Unknown Location'))
        else:
            # Use regular spinner for other search types (memory, etc.)
            search_messages = {
                'memory': f"💾 Searching memory only for jobs in {params.get('location', 'Unknown Location')}...",
                'indeed_fresh': f"🔍 Searching fresh Indeed jobs in {params.get('location', 'Unknown Location')}..."
            }
            with st.spinner(search_messages.get(search_type_tab, "Searching...")):
                df, metadata = pipeline.run_pipeline(params)

    # Coach/candidate info is already in the DataFrame from pipeline execution
    # No need to add it again here
    return df, metadata