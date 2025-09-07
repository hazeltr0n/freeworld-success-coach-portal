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

def show_companies_dashboard():
    """Display the companies analytics dashboard"""
    
    st.markdown("# 🏢 Companies Analytics Dashboard")
    st.markdown("---")
    
    # Import companies functions
    try:
        from companies_rollup import (
            get_company_analytics, get_fair_chance_companies, 
            get_market_company_breakdown, update_companies_table
        )
    except ImportError:
        st.error("❌ Companies rollup module not available")
        return
    
    # Control buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Update Companies Data"):
            with st.spinner("Updating companies rollup table..."):
                try:
                    update_companies_table()
                    st.success("✅ Companies data updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to update: {e}")
    
    with col2:
        show_fair_chance_only = st.checkbox("🤝 Fair Chance Only")
    
    with col3:
        market_filter = st.selectbox(
            "🌍 Filter by Market", 
            ["All Markets", "Houston", "Dallas", "Las Vegas", "Bay Area", "Denver", "Phoenix", "Other"],
            index=0
        )
    
    # Load companies data
    try:
        if show_fair_chance_only:
            companies_df = get_fair_chance_companies()
        elif market_filter != "All Markets":
            companies_df = get_market_company_breakdown(market_filter)
        else:
            companies_df = get_company_analytics(limit=500)
        
        if companies_df.empty:
            st.warning("📊 No companies data available. Click 'Update Companies Data' to populate the table.")
            return
            
    except Exception as e:
        st.error(f"❌ Error loading companies data: {e}")
        return
    
    # Summary metrics
    st.markdown("## 📈 Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Companies", len(companies_df))
    
    with col2:
        fair_chance_count = companies_df['has_fair_chance'].sum() if 'has_fair_chance' in companies_df.columns else 0
        fair_chance_pct = (fair_chance_count / len(companies_df) * 100) if len(companies_df) > 0 else 0
        st.metric("Fair Chance Companies", f"{fair_chance_count} ({fair_chance_pct:.1f}%)")
    
    with col3:
        total_jobs = companies_df['total_jobs'].sum() if 'total_jobs' in companies_df.columns else 0
        st.metric("Total Job Postings", f"{total_jobs:,}")
    
    with col4:
        avg_jobs_per_company = companies_df['total_jobs'].mean() if 'total_jobs' in companies_df.columns else 0
        st.metric("Avg Jobs/Company", f"{avg_jobs_per_company:.1f}")
    
    # Charts
    st.markdown("## 📊 Analytics")
    
    # Top companies by job count
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏆 Top Companies by Job Count")
        top_companies = companies_df.nlargest(15, 'total_jobs') if 'total_jobs' in companies_df.columns else companies_df.head(15)
        
        fig = px.bar(
            top_companies, 
            x='total_jobs', 
            y='company_name',
            orientation='h',
            title="Jobs Posted (Last 60 Days)",
            color='has_fair_chance' if 'has_fair_chance' in companies_df.columns else None,
            color_discrete_map={True: '#10B981', False: '#6B7280'}
        )
        fig.update_layout(height=500, showlegend=True if 'has_fair_chance' in companies_df.columns else False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🤝 Fair Chance Distribution")
        
        if 'has_fair_chance' in companies_df.columns:
            fair_chance_counts = companies_df['has_fair_chance'].value_counts()
            fig = px.pie(
                values=fair_chance_counts.values,
                names=['Fair Chance' if x else 'Standard' for x in fair_chance_counts.index],
                title="Companies by Fair Chance Status",
                color_discrete_sequence=['#10B981', '#6B7280']
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Fair chance data not available")
    
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
            st.plotly_chart(fig, use_container_width=True)
    
    # Companies table
    st.markdown("## 📋 Companies Details")
    
    # Prepare display columns
    display_columns = ['company_name', 'total_jobs']
    
    if 'has_fair_chance' in companies_df.columns:
        companies_df['fair_chance_status'] = companies_df['has_fair_chance'].map({True: '🤝 Yes', False: '❌ No'})
        display_columns.append('fair_chance_status')
    
    if 'fair_chance_jobs' in companies_df.columns:
        display_columns.append('fair_chance_jobs')
    
    if 'markets' in companies_df.columns:
        companies_df['markets_display'] = companies_df['markets'].apply(
            lambda x: ', '.join(x[:3]) + (f' (+{len(x)-3} more)' if len(x) > 3 else '') if isinstance(x, list) and x else 'Unknown'
        )
        display_columns.append('markets_display')
    
    if 'quality_breakdown' in companies_df.columns:
        companies_df['quality_summary'] = companies_df['quality_breakdown'].apply(
            lambda x: f"Good: {x.get('good', 0)}, So-so: {x.get('so-so', 0)}" if isinstance(x, dict) else "N/A"
        )
        display_columns.append('quality_summary')
    
    # Column configuration for better display
    column_config = {
        'company_name': st.column_config.TextColumn('Company Name', width='large'),
        'total_jobs': st.column_config.NumberColumn('Total Jobs', format='%d'),
        'fair_chance_status': st.column_config.TextColumn('Fair Chance'),
        'fair_chance_jobs': st.column_config.NumberColumn('Fair Chance Jobs', format='%d'),
        'markets_display': st.column_config.TextColumn('Markets', width='medium'),
        'quality_summary': st.column_config.TextColumn('Job Quality', width='medium')
    }
    
    # Search functionality
    search_term = st.text_input("🔍 Search companies:", placeholder="Enter company name...")
    
    display_df = companies_df[display_columns].copy()
    
    if search_term:
        mask = display_df['company_name'].str.contains(search_term, case=False, na=False)
        display_df = display_df[mask]
    
    # Display table
    st.dataframe(
        display_df,
        column_config=column_config,
        use_container_width=True,
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
                file_name=f"companies_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        # Show detailed view for selected company
        if not display_df.empty:
            selected_company = st.selectbox(
                "🔍 View Company Details:",
                ["Select a company..."] + display_df['company_name'].tolist()
            )
            
            if selected_company != "Select a company...":
                company_details = companies_df[companies_df['company_name'] == selected_company].iloc[0]
                
                st.markdown(f"### 🏢 {selected_company}")
                
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.write(f"**Total Jobs:** {company_details.get('total_jobs', 0)}")
                    st.write(f"**Fair Chance Jobs:** {company_details.get('fair_chance_jobs', 0)}")
                    st.write(f"**Active Jobs:** {company_details.get('active_jobs', 0)}")
                
                with detail_col2:
                    if 'markets' in company_details and company_details['markets']:
                        st.write(f"**Markets:** {', '.join(company_details['markets'])}")
                    if 'route_types' in company_details and company_details['route_types']:
                        st.write(f"**Route Types:** {', '.join(company_details['route_types'])}")
                
                # Show job titles
                if 'job_titles' in company_details and company_details['job_titles']:
                    st.write("**Common Job Titles:**")
                    for title in company_details['job_titles'][:5]:
                        st.write(f"• {title}")

if __name__ == "__main__":
    show_companies_dashboard()