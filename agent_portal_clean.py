#!/usr/bin/env python3
"""
Clean Agent Portal Implementation
Simplified, focused function for Free Agent job portal without app.py complexity
"""

import pandas as pd
from typing import Dict, Any

def generate_agent_portal(agent_params: Dict[str, Any]) -> str:
    """
    Clean agent portal implementation using EXACT same code path as Memory Only search
    
    Args:
        agent_params: Dict with agent_name, agent_uuid, location, coach_username, etc.
        
    Returns:
        HTML fragment for agent portal
    """
    
    print(f"🎯 CLEAN AGENT PORTAL: Starting for {agent_params.get('agent_name', 'Unknown')}")
    print(f"🎯 CLEAN AGENT PORTAL: Using same code path as Memory Only search")
    
    try:
        import streamlit as st
        
        # Check for daily refresh limit to prevent excessive portal refreshes
        import datetime
        from datetime import datetime, timezone
        
        agent_uuid = agent_params.get('agent_uuid', 'unknown')
        last_refresh_key = f"agent_last_refresh_{agent_uuid}"
        
        # Check if agent has refreshed within last 24 hours
        last_refresh = getattr(st.session_state, last_refresh_key, None)
        now = datetime.now(timezone.utc)
        
        can_refresh = True
        if last_refresh:
            hours_since_refresh = (now - last_refresh).total_seconds() / 3600
            can_refresh = hours_since_refresh >= 24
            print(f"🕐 REFRESH CHECK: Last refresh {hours_since_refresh:.1f}h ago, can_refresh={can_refresh}")
        
        # Use existing DataFrame from memory search if available and within refresh window
        has_existing_data = (
            hasattr(st.session_state, 'memory_search_df') and 
            st.session_state.memory_search_df is not None and
            not st.session_state.memory_search_df.empty
        )
        
        if has_existing_data and not can_refresh:
            print(f"🎯 CLEAN AGENT PORTAL: Using existing memory_search_df with {len(st.session_state.memory_search_df)} jobs")
            df = st.session_state.memory_search_df
            
            # Use EXACT same HTML generation code path as Memory Only search (line 5296-5310 in app.py)
            from free_agent_system import update_job_tracking_for_agent
            from pdf.html_pdf_generator import jobs_dataframe_to_dicts, render_jobs_html
            
            # Process DataFrame the same way Memory Only search does
            processed_df = update_job_tracking_for_agent(df, agent_params)
            
            # Apply unified sorting to match FPDF exactly
            if len(processed_df) > 0:
                print(f"🎯 CLEAN AGENT PORTAL: Applying unified sorting (matches FPDF)")
                
                try:
                    from job_sorting_utils import apply_unified_sorting
                    processed_df = apply_unified_sorting(processed_df)
                    print(f"🎯 CLEAN AGENT PORTAL: Jobs sorted by route type (Local→OTR→Unknown) then quality")
                except Exception as e:
                    print(f"⚠️ CLEAN AGENT PORTAL: Sorting failed, using original order: {e}")
            
            # 4. Apply max_jobs limit from agent params
            max_jobs = agent_params.get('max_jobs', 25)  # Default to 25 if not specified
            if max_jobs and max_jobs != "All" and isinstance(max_jobs, int) and len(processed_df) > max_jobs:
                processed_df = processed_df.head(max_jobs)
                print(f"🎯 CLEAN AGENT PORTAL: Limited to {max_jobs} jobs per agent settings")
            elif max_jobs == "All":
                print(f"🎯 CLEAN AGENT PORTAL: Showing all {len(processed_df)} jobs (no limit)")
            
            jobs = jobs_dataframe_to_dicts(processed_df)
            
            # Pass agent_params as-is - don't override show_prepared_for
            agent_params_with_prepared = {**agent_params}
            
            html = render_jobs_html(jobs, agent_params_with_prepared, fragment=True)
            
            print(f"🎯 CLEAN AGENT PORTAL: HTML generated successfully ({len(html)} chars)")
            return html
            
        else:
            print(f"🎯 CLEAN AGENT PORTAL: No memory_search_df found, running memory search pipeline...")
            
            # Run the EXACT same memory search pipeline as the main app (lines 5077-5156 in app.py)
            if 'pipeline' not in st.session_state:
                from pipeline_wrapper import StreamlitPipelineWrapper
                st.session_state.pipeline = StreamlitPipelineWrapper()
            
            pipeline = st.session_state.pipeline
            location = agent_params.get('location', 'Houston')
            
            # Use agent parameters for the memory search
            params = {
                'mode': 'sample',
                'route_type_filter': [agent_params.get('route_type_filter', agent_params.get('route_filter', 'both'))],  # Support both modern and legacy parameter names
                'match_quality_filter': agent_params.get('match_quality_filter', agent_params.get('match_level', 'good and so-so')).split(' and ') if isinstance(agent_params.get('match_quality_filter', agent_params.get('match_level', 'good and so-so')), str) else agent_params.get('match_quality_filter', ['good', 'so-so']),  # Support both parameter formats
                'fair_chance_only': agent_params.get('fair_chance_only', False),  # Agent's fair chance preference
                'max_jobs': agent_params.get('max_jobs', 25),  # Agent's max jobs limit
                'search_terms': '',
                'push_to_airtable': False,
                'generate_pdf': False,
                'generate_csv': False,
                'search_radius': 50,
                'no_experience': False,
                'force_fresh': False,
                'force_fresh_classification': False,
                'memory_only': True,  # FORCE memory-only mode
                'memory_hours': 168,  # 7 days lookback (was 72h = 3 days!)
                'candidate_id': agent_params.get('agent_uuid', ''),
                'candidate_name': agent_params.get('agent_name', ''),
                'search_sources': {'indeed': False, 'google': False},  # Memory only
                'search_strategy': 'memory_first',
                'location': location
            }
            
            print(f"🎯 AGENT FILTER DEBUG: Using route_filter='{agent_params.get('route_filter')}', fair_chance_only={agent_params.get('fair_chance_only')}, max_jobs={agent_params.get('max_jobs')}")
            
            print(f"🎯 CLEAN AGENT PORTAL: Running memory search for location: {location}")
            
            # Run pipeline (same as main app)
            df, metadata = pipeline.run_pipeline(params)
            
            if metadata.get('success', False) and df is not None and not df.empty:
                # Store in session state exactly like main app does (line 5199)
                st.session_state.memory_search_df = df
                
                # Update refresh timestamp for this agent
                setattr(st.session_state, last_refresh_key, now)
                print(f"🕐 REFRESH TIMESTAMP: Updated for agent {agent_uuid}")
                st.session_state.memory_search_metadata = metadata
                st.session_state.memory_search_params = params.copy()
                
                print(f"🎯 CLEAN AGENT PORTAL: Memory search completed, found {len(df)} jobs")
                
                # Now generate HTML using the same process
                from free_agent_system import update_job_tracking_for_agent
                from pdf.html_pdf_generator import jobs_dataframe_to_dicts, render_jobs_html
                
                processed_df = update_job_tracking_for_agent(df, agent_params)
                
                # Apply unified sorting to match FPDF exactly (pipeline path)
                if len(processed_df) > 0:
                    print(f"🎯 CLEAN AGENT PORTAL: Applying unified sorting (matches FPDF) (pipeline path)")
                    
                    try:
                        from job_sorting_utils import apply_unified_sorting
                        processed_df = apply_unified_sorting(processed_df)
                        print(f"🎯 CLEAN AGENT PORTAL: Jobs sorted by route type (Local→OTR→Unknown) then quality (pipeline path)")
                    except Exception as e:
                        print(f"⚠️ CLEAN AGENT PORTAL: Sorting failed, using original order: {e}")
                
                # 4. Apply max_jobs limit from agent params
                max_jobs = agent_params.get('max_jobs', 25)  # Default to 25 if not specified
                if max_jobs and max_jobs != "All" and isinstance(max_jobs, int) and len(processed_df) > max_jobs:
                    processed_df = processed_df.head(max_jobs)
                    print(f"🎯 CLEAN AGENT PORTAL: Limited to {max_jobs} jobs per agent settings")
                elif max_jobs == "All":
                    print(f"🎯 CLEAN AGENT PORTAL: Showing all {len(processed_df)} jobs (no limit)")
                
                jobs = jobs_dataframe_to_dicts(processed_df)
                
                # Pass agent_params as-is - don't override show_prepared_for
                agent_params_with_prepared = {**agent_params}
                
                html = render_jobs_html(jobs, agent_params_with_prepared, fragment=True)
                
                return html
            else:
                error_msg = metadata.get('error', 'No jobs found in memory')
                print(f"❌ CLEAN AGENT PORTAL: Memory search failed - {error_msg}")
                return f"""
                <div class='fw-splash'>
                    <h1>No Jobs Found</h1>
                    <p>No jobs found in memory for location: {location}</p>
                    <p>Error: {error_msg}</p>
                </div>
                """
            
    except Exception as e:
        print(f"❌ CLEAN AGENT PORTAL: Exception - {e}")
        import traceback
        print(f"❌ CLEAN AGENT PORTAL: Traceback - {traceback.format_exc()}")
        return f"""
        <div class='fw-splash'>
            <h1>Clean Portal Error</h1>
            <p>{e}</p>
        </div>
        """

if __name__ == "__main__":
    # Test the clean portal
    test_params = {
        'agent_name': 'Test Agent',
        'agent_uuid': 'test-123',
        'location': 'Houston',
        'coach_username': 'test.coach'
    }
    
    html = generate_agent_portal(test_params)
    print(f"Generated HTML: {len(html)} characters")