#!/usr/bin/env python3
"""
Companies Analytics Dashboard
Streamlit components for displaying companies rollup data
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import uuid as uuid_lib

def show_companies_dashboard():
    """Display the companies analytics dashboard"""
    
    st.markdown("# 🏢 Companies Analytics Dashboard")
    st.markdown("---")
    
    # Import companies functions
    try:
        from companies_rollup import (
            get_company_analytics, get_fair_chance_companies,
            get_market_company_breakdown, update_companies_table,
            update_company_blacklist, update_company_employer_uuid, get_client
        )
    except ImportError:
        st.error("❌ Companies rollup module not available")
        return
    
    # Control buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("⚡ Manual Refresh"):
            with st.spinner("Running manual companies refresh..."):
                try:
                    client = get_client()
                    if client:
                        # Call the Supabase scheduled function manually
                        result = client.rpc('scheduled_companies_refresh').execute()
                        # The function now returns simple text: "SUCCESS: Updated 2051 companies"
                        if result.data and len(result.data) > 0:
                            response_text = result.data[0]
                            if isinstance(response_text, str):
                                if response_text.startswith('SUCCESS:'):
                                    st.success(f"✅ Manual refresh completed! {response_text}")
                                elif response_text.startswith('ERROR:'):
                                    st.error(f"❌ Refresh failed: {response_text}")
                                else:
                                    st.success(f"✅ Manual refresh completed! {response_text}")
                            else:
                                st.success("✅ Manual refresh completed!")
                        else:
                            st.warning("⚠️ No response data from refresh function")

                        st.rerun()
                    else:
                        st.error("❌ Supabase client not available")
                except Exception as e:
                    st.error(f"❌ Manual refresh failed: {e}")

    with col2:
        show_fair_chance_only = st.checkbox("🤝 Fair Chance Only")

    with col3:
        market_filter = st.selectbox(
            "🌍 Filter by Market",
            ["All Markets", "Houston", "Dallas", "Las Vegas", "Bay Area", "Denver", "Phoenix", "Other"],
            index=0
        )
    
    # Load companies data - remove limit to get ALL companies with good/so-so jobs
    try:
        if show_fair_chance_only:
            companies_df = get_fair_chance_companies()
        elif market_filter != "All Markets":
            companies_df = get_market_company_breakdown(market_filter)
        else:
            # Remove limit to get ALL companies with quality jobs - address Supabase query limits
            companies_df = get_company_analytics(limit=None)  # Get ALL companies with good/so-so jobs
        
        if companies_df.empty:
            st.warning("📊 No companies data available. Click 'Manual Refresh' to populate the table.")
            return
            
    except Exception as e:
        st.error(f"❌ Error loading companies data: {e}")
        return
    
    # Summary metrics
    st.markdown("## 📈 Overview")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Quality Companies", len(companies_df))

    with col2:
        fair_chance_count = companies_df['has_fair_chance'].sum() if 'has_fair_chance' in companies_df.columns else 0
        fair_chance_pct = (fair_chance_count / len(companies_df) * 100) if len(companies_df) > 0 else 0
        st.metric("Fair Chance Companies", f"{fair_chance_count} ({fair_chance_pct:.1f}%)")

    with col3:
        total_jobs = companies_df['total_jobs'].sum() if 'total_jobs' in companies_df.columns else 0
        st.metric("Quality Job Postings", f"{total_jobs:,}")

    with col4:
        avg_jobs_per_company = companies_df['total_jobs'].mean() if 'total_jobs' in companies_df.columns else 0
        st.metric("Avg Jobs/Company", f"{avg_jobs_per_company:.1f}")

    with col5:
        blacklisted_count = companies_df['is_blacklisted'].sum() if 'is_blacklisted' in companies_df.columns else 0
        st.metric("Blacklisted", blacklisted_count, delta_color="inverse")
    
    # Note about filtering
    st.info("📋 **Data Note**: Only showing companies with 'good' or 'so-so' quality jobs. Companies with only 'bad' jobs are filtered out.")

    # Company Merge Tool
    with st.expander("🔀 Merge Duplicate Companies", expanded=False):
        st.markdown("**Consolidate companies with different names that are actually the same employer**")
        st.markdown("Example: '1-800-GOT-JUNK?' and '1-800-GOT-JUNK? - San Francisco Bay' → Keep one, merge the other")

        from companies_rollup import merge_companies

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Primary Company (Keep This One)**")
            primary_search = st.text_input("Search primary company:", key="primary_search")

            if primary_search:
                primary_matches = companies_df[companies_df['company_name'].str.contains(primary_search, case=False, na=False)]
                if len(primary_matches) > 0:
                    primary_company = st.selectbox(
                        "Select primary company:",
                        options=primary_matches['company_name'].tolist(),
                        key="primary_select"
                    )
                    primary_id = primary_matches[primary_matches['company_name'] == primary_company]['id'].iloc[0]
                    st.info(f"Primary ID: {primary_id} | Jobs: {primary_matches[primary_matches['company_name'] == primary_company]['total_jobs'].iloc[0]}")
                else:
                    st.warning("No matches found")
                    primary_company = None
                    primary_id = None
            else:
                primary_company = None
                primary_id = None

        with col2:
            st.markdown("**Duplicate Companies (Will Be Merged)**")
            duplicate_search = st.text_input("Search duplicates:", key="duplicate_search")

            if duplicate_search:
                duplicate_matches = companies_df[companies_df['company_name'].str.contains(duplicate_search, case=False, na=False)]
                if len(duplicate_matches) > 0:
                    duplicate_companies = st.multiselect(
                        "Select companies to merge:",
                        options=duplicate_matches['company_name'].tolist(),
                        key="duplicate_select"
                    )
                    if duplicate_companies:
                        duplicate_ids = [int(duplicate_matches[duplicate_matches['company_name'] == name]['id'].iloc[0]) for name in duplicate_companies]
                        total_dup_jobs = sum([int(duplicate_matches[duplicate_matches['company_name'] == name]['total_jobs'].iloc[0]) for name in duplicate_companies])
                        st.info(f"Selected: {len(duplicate_companies)} companies | {total_dup_jobs} jobs")
                    else:
                        duplicate_ids = []
                else:
                    st.warning("No matches found")
                    duplicate_companies = []
                    duplicate_ids = []
            else:
                duplicate_companies = []
                duplicate_ids = []

        st.markdown("---")

        if primary_company and duplicate_companies:
            st.warning(f"⚠️ **Preview**: Set {len(duplicate_companies)} companies as children of '{primary_company}'")
            st.markdown("**What will happen:**")
            st.markdown(f"1. {duplicate_companies} will be marked as child companies of '{primary_company}'")
            st.markdown(f"2. **Existing jobs keep their original company names** (preserved for historical accuracy)")
            st.markdown(f"3. **Future jobs** from child company names will automatically roll up to '{primary_company}'")
            st.markdown(f"4. Analytics will show parent company name for all variants")

            if st.button("🔀 Confirm Merge", type="primary"):
                with st.spinner("Merging companies..."):
                    success, message = merge_companies(primary_id, duplicate_ids)
                    if success:
                        st.success(f"✅ {message}")
                        st.info("⏳ Refreshing company data...")
                        st.rerun()
                    else:
                        st.error(f"❌ Merge failed: {message}")
        elif primary_company or duplicate_companies:
            st.info("👆 Select both a primary company and at least one duplicate to merge")

    # Market breakdown
    if 'markets' in companies_df.columns:
        st.markdown("### 🌍 Geographic Distribution")
        
        # Explode markets array and count
        markets_expanded = companies_df.explode('markets')['markets'].dropna()
        market_counts = markets_expanded.value_counts().head(10)
        
        if not market_counts.empty:
            fig = px.bar(
                x=market_counts.index,
                y=market_counts.values,
                title="Companies by Market",
                labels={'x': 'Market', 'y': 'Number of Companies'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig)
    
    # Companies table
    st.markdown("## 📋 Companies Details")

    # Quality and route breakdown summary
    col1, col2, col3 = st.columns(3)

    # Calculate companies by job quality
    good_companies = 0
    so_so_companies = 0
    fair_chance_companies = companies_df['has_fair_chance'].sum() if 'has_fair_chance' in companies_df.columns else 0

    if 'quality_breakdown' in companies_df.columns:
        for _, row in companies_df.iterrows():
            quality_data = row.get('quality_breakdown')
            if isinstance(quality_data, dict):
                if quality_data.get('good', 0) > 0:
                    good_companies += 1
                if quality_data.get('so-so', 0) > 0:
                    so_so_companies += 1

    with col1:
        st.metric("Companies with Good Jobs", good_companies)
    with col2:
        st.metric("Companies with So-so Jobs", so_so_companies)
    with col3:
        st.metric("Fair Chance Employers", fair_chance_companies)

    # Show route type breakdown summary
    if 'route_breakdown' in companies_df.columns:
        col1, col2, col3 = st.columns(3)

        # Calculate companies offering each route type
        local_companies = sum(1 for _, row in companies_df.iterrows()
                             if isinstance(row.get('route_breakdown'), dict) and row['route_breakdown'].get('Local', 0) > 0)
        otr_companies = sum(1 for _, row in companies_df.iterrows()
                           if isinstance(row.get('route_breakdown'), dict) and row['route_breakdown'].get('OTR', 0) > 0)
        both_companies = sum(1 for _, row in companies_df.iterrows()
                            if isinstance(row.get('route_breakdown'), dict) and
                            row['route_breakdown'].get('Local', 0) > 0 and row['route_breakdown'].get('OTR', 0) > 0)

        with col1:
            st.metric("Companies with Local Routes", local_companies)
        with col2:
            st.metric("Companies with OTR Routes", otr_companies)
        with col3:
            st.metric("Companies with Both Route Types", both_companies)
    
    # Prepare display columns with enhanced data
    display_columns = ['company_name', 'total_jobs']

    # Route type indicators with job counts
    if 'route_breakdown' in companies_df.columns:
        def format_route_info(route_data):
            if not isinstance(route_data, dict) or not route_data:
                return "Unknown"

            route_parts = []
            if route_data.get('Local', 0) > 0:
                route_parts.append(f"Local ({route_data['Local']})")
            if route_data.get('OTR', 0) > 0:
                route_parts.append(f"OTR ({route_data['OTR']})")
            if route_data.get('Regional', 0) > 0:
                route_parts.append(f"Regional ({route_data['Regional']})")

            if not route_parts:
                return "Other"

            return ", ".join(route_parts)

        companies_df['route_info'] = companies_df['route_breakdown'].apply(format_route_info)
        display_columns.append('route_info')

    # Markets display (using actual markets, not city names)
    if 'markets' in companies_df.columns:
        companies_df['markets_display'] = companies_df['markets'].apply(
            lambda x: ', '.join(x) if isinstance(x, list) and x else 'Unknown'
        )
        display_columns.append('markets_display')

    # Fair chance status
    if 'has_fair_chance' in companies_df.columns:
        companies_df['fair_chance_status'] = companies_df['has_fair_chance'].map({True: '🤝 Yes', False: '❌ No'})
        display_columns.append('fair_chance_status')

    if 'fair_chance_jobs' in companies_df.columns:
        display_columns.append('fair_chance_jobs')

    # Free agent feedback
    if 'free_agent_feedback' in companies_df.columns:
        def format_feedback(feedback_data):
            if not isinstance(feedback_data, dict) or not feedback_data:
                return "No data"

            applicants = feedback_data.get('total_applicants', 0)
            applications = feedback_data.get('total_applications', 0)

            if applicants == 0:
                return "No applications"

            return f"{applicants} applicants, {applications} applications"

        companies_df['agent_feedback'] = companies_df['free_agent_feedback'].apply(format_feedback)
        display_columns.append('agent_feedback')

    # Quality breakdown (only good/so-so since we're filtering out bad)
    if 'quality_breakdown' in companies_df.columns:
        companies_df['quality_summary'] = companies_df['quality_breakdown'].apply(
            lambda x: f"Good: {x.get('good', 0)}, So-so: {x.get('so-so', 0)}" if isinstance(x, dict) else "N/A"
        )
        display_columns.append('quality_summary')

    # Blacklist status with editable checkbox
    if 'is_blacklisted' in companies_df.columns:
        display_columns.append('is_blacklisted')

    # Blacklist reason (show when company is blacklisted)
    if 'blacklist_reason' in companies_df.columns:
        # Convert existing reasons to single value from comma-separated
        def parse_blacklist_reason(reason):
            if pd.isna(reason) or reason == '' or reason is None:
                return None
            # If it's a timestamp-based reason, return None (will show as blank)
            if 'Manually blacklisted via dashboard' in str(reason):
                return None
            # If it's comma-separated, take the first one
            reason_str = str(reason).strip()
            if ',' in reason_str:
                return reason_str.split(',')[0].strip()
            return reason_str

        companies_df['blacklist_tags'] = companies_df['blacklist_reason'].apply(parse_blacklist_reason)
        display_columns.append('blacklist_tags')

    # Employer UUID for matching with internal database
    if 'employer_uuid' in companies_df.columns:
        display_columns.append('employer_uuid')

    # Add ID for editing
    if 'id' in companies_df.columns:
        display_columns.insert(0, 'id')
    
    # Column configuration for better display
    column_config = {
        'id': st.column_config.NumberColumn('ID', width='small'),
        'company_name': st.column_config.TextColumn('Company Name', width='large'),
        'total_jobs': st.column_config.NumberColumn('Total Jobs', format='%d'),
        'route_info': st.column_config.TextColumn('Route Types & Counts', width='medium'),
        'markets_display': st.column_config.TextColumn('Markets', width='medium'),
        'fair_chance_status': st.column_config.TextColumn('Fair Chance', width='small'),
        'fair_chance_jobs': st.column_config.NumberColumn('FC Jobs', format='%d', width='small'),
        'agent_feedback': st.column_config.TextColumn('Free Agent Activity', width='medium'),
        'quality_summary': st.column_config.TextColumn('Job Quality', width='medium'),
        'is_blacklisted': st.column_config.CheckboxColumn('Blacklisted', help='Check to blacklist company (auto-marks jobs as bad)', width='small'),
        'blacklist_tags': st.column_config.SelectboxColumn(
            'Blacklist Reason',
            width='medium',
            help='Select reason for blacklisting',
            options=['Spam Agency', 'Experience Required', 'Not Fair Chance Friendly', 'Possible Scam']
        ),
        'employer_uuid': st.column_config.TextColumn(
            'FW Employer ID',
            width='medium',
            help='UUID linking to FreeWorld Admin Portal employer database (manual entry)'
        )
    }
    
    # Search functionality
    search_term = st.text_input("🔍 Search companies:", placeholder="Enter company name...")
    
    display_df = companies_df[display_columns].copy()
    
    if search_term:
        mask = display_df['company_name'].str.contains(search_term, case=False, na=False)
        display_df = display_df[mask]
    
    # Handle blacklist updates
    if 'is_blacklisted' in display_df.columns and 'id' in display_df.columns:
        st.info("💡 **Company Blacklist**: Check the 'Blacklisted' box to automatically mark all jobs from that company as 'bad' quality. This helps filter out problematic companies.")

        # Create editable dataframe
        edited_df = st.data_editor(
            display_df,
            column_config=column_config,
            height=600,
            key="companies_table",
            on_change=None
        )

        # Check for changes and show save button
        has_changes = not edited_df.equals(display_df)

        if has_changes:
            st.warning("⚠️ You have unsaved changes")

            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("💾 Save Changes", type="primary"):
                    # Process all changes
                    changes_made = 0
                    errors = []

                    for idx in edited_df.index:
                        if idx < len(display_df):
                            company_id = int(edited_df.loc[idx, 'id'])
                            company_name = str(edited_df.loc[idx, 'company_name'])

                            # Check for blacklist changes
                            old_blacklist = display_df.loc[idx, 'is_blacklisted']
                            new_blacklist = edited_df.loc[idx, 'is_blacklisted']
                            old_tag = display_df.loc[idx, 'blacklist_tags'] if 'blacklist_tags' in display_df.columns else None
                            new_tag = edited_df.loc[idx, 'blacklist_tags'] if 'blacklist_tags' in edited_df.columns else None

                            if old_blacklist != new_blacklist or old_tag != new_tag:
                                # Use selected reason or default timestamp
                                if new_blacklist:
                                    if new_tag and pd.notna(new_tag) and str(new_tag).strip():
                                        reason = str(new_tag).strip()
                                    else:
                                        reason = f"Manually blacklisted via dashboard on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                                else:
                                    reason = None

                                success, error_msg = update_company_blacklist(company_id, new_blacklist, reason)

                                if success:
                                    changes_made += 1
                                else:
                                    errors.append(f"{company_name} (blacklist): {error_msg}")

                            # Check for employer_uuid changes
                            if 'employer_uuid' in display_df.columns:
                                old_uuid = display_df.loc[idx, 'employer_uuid'] if pd.notna(display_df.loc[idx, 'employer_uuid']) else None
                                new_uuid = edited_df.loc[idx, 'employer_uuid'] if pd.notna(edited_df.loc[idx, 'employer_uuid']) else None

                                if old_uuid != new_uuid:
                                    success, error_msg = update_company_employer_uuid(company_id, new_uuid)

                                    if success:
                                        changes_made += 1
                                    else:
                                        errors.append(f"{company_name} (UUID): {error_msg}")

                    # Show results
                    if changes_made > 0:
                        st.success(f"✅ Successfully updated {changes_made} field(s)")
                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")

                    if changes_made > 0:
                        st.rerun()

            with col2:
                if st.button("🔄 Discard Changes"):
                    st.rerun()
    else:
        # Display regular dataframe
        st.dataframe(
            display_df,
            column_config=column_config,
            height=600
        )
    
    # Export functionality
    st.markdown("## 💾 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export to CSV"):
            csv = companies_df.to_csv(index=False)
            st.download_button(
                label="💾 Download Companies CSV",
                data=csv,
                file_name=f"companies_good_quality_only_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

        # Blacklist management
        st.markdown("#### 🚫 Blacklist Management")
        if st.button("📋 View All Blacklisted Companies"):
            from companies_rollup import get_blacklisted_companies
            blacklisted_df = get_blacklisted_companies()
            if not blacklisted_df.empty:
                st.dataframe(blacklisted_df)
            else:
                st.info("No companies are currently blacklisted.")
    
    with col2:
        # Show detailed view for selected company
        if not display_df.empty:
            selected_company = st.selectbox(
                "🔍 View Company Details:",
                ["Select a company..."] + display_df['company_name'].tolist()
            )
            
            if selected_company != "Select a company...":
                company_details = companies_df[companies_df['company_name'] == selected_company].iloc[0]

                # Show blacklist warning if applicable
                blacklist_warning = ""
                if company_details.get('is_blacklisted', False):
                    blacklist_warning = " 🚫 (BLACKLISTED)"

                st.markdown(f"### 🏢 {selected_company}{blacklist_warning}")
                
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.write(f"**Total Jobs:** {company_details.get('total_jobs', 0)}")
                    st.write(f"**Fair Chance Jobs:** {company_details.get('fair_chance_jobs', 0)}")
                    st.write(f"**Active Jobs:** {company_details.get('active_jobs', 0)}")
                
                with detail_col2:
                    if 'markets' in company_details and company_details['markets']:
                        st.write(f"**Markets:** {', '.join(company_details['markets'])}")
                    if 'route_breakdown' in company_details and company_details['route_breakdown']:
                        route_data = company_details['route_breakdown']
                        if isinstance(route_data, dict):
                            route_info = []
                            for route_type, count in route_data.items():
                                if count > 0:
                                    route_info.append(f"{route_type}: {count}")
                            if route_info:
                                st.write(f"**Route Breakdown:** {', '.join(route_info)}")
                    if 'free_agent_feedback' in company_details and company_details['free_agent_feedback']:
                        feedback = company_details['free_agent_feedback']
                        if isinstance(feedback, dict) and feedback:
                            st.write(f"**Free Agent Activity:** {feedback.get('total_applicants', 0)} applicants, {feedback.get('total_applications', 0)} applications")
                    if 'is_blacklisted' in company_details:
                        status = "🚫 Yes" if company_details['is_blacklisted'] else "✅ No"
                        st.write(f"**Blacklisted:** {status}")
                        if company_details['is_blacklisted'] and company_details.get('blacklist_reason'):
                            st.write(f"**Reason:** {company_details['blacklist_reason']}")
                
                # Show job titles and quality breakdown
                if 'job_titles' in company_details and company_details['job_titles']:
                    st.write("**Common Job Titles:**")
                    for title in company_details['job_titles'][:5]:
                        st.write(f"• {title}")

                # Enhanced quality breakdown
                if 'quality_breakdown' in company_details and company_details['quality_breakdown']:
                    quality_data = company_details['quality_breakdown']
                    if isinstance(quality_data, dict):
                        st.write("**Job Quality Distribution:**")
                        total_quality_jobs = sum(quality_data.values())
                        for quality, count in quality_data.items():
                            percentage = (count / total_quality_jobs * 100) if total_quality_jobs > 0 else 0
                            st.write(f"• {quality.title()}: {count} ({percentage:.1f}%)")

if __name__ == "__main__":
    show_companies_dashboard()