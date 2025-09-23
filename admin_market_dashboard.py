#!/usr/bin/env python3
"""
Admin Market Analytics Dashboard
Comprehensive market statistics from Supabase with custom time windows
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Market analytics constants
DEFAULT_TIME_WINDOW = 168  # 1 week in hours

# Import Airtable sync for live job seeker data
try:
    from airtable_job_seekers_sync import get_job_seeker_counts, refresh_airtable_job_seeker_cache
    LIVE_AIRTABLE_SYNC = True
except ImportError as e:
    LIVE_AIRTABLE_SYNC = False

# Fallback job seeker counts (updated to match live Airtable test results)
FALLBACK_JOB_SEEKER_COUNTS = {
    'Houston': 153,     # Live: 153
    'Dallas': 81,       # Live: 81
    'Stockton': 96,     # Live: 96
    'Inland Empire': 21, # Live: 21 (16+5)
    'Bay Area': 21,     # Live: 21
    'Phoenix': 15,      # Live: 15
    'Trenton': 9,       # Live: 9
    'Newark': 5,        # Live: 5
    'Las Vegas': 1,     # Live: 1
    'Denver': 0,        # Live: 0 (filtered out)
    'Unknown': 0
}

# All financial functions removed - focusing on pure market analytics from jobs table

def get_market_analytics(hours: Optional[int] = None) -> pd.DataFrame:
    """Get comprehensive market analytics from Supabase"""
    try:
        from supabase_utils import get_client
        client = get_client()
        
        if not client:
            st.error("❌ Cannot connect to Supabase")
            return pd.DataFrame()
        
        # Build query with optional time filter
        query = client.table('jobs').select('market,match_level,route_type,created_at')
        
        if hours:
            since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
            query = query.gte('created_at', since)
        
        # Execute query with pagination for large datasets
        all_jobs = []
        page_size = 1000
        page = 0
        
        while True:
            start = page * page_size
            end = start + page_size - 1
            
            result = query.range(start, end).order('created_at', desc=True).execute()
            batch = result.data or []
            
            if not batch:
                break
                
            all_jobs.extend(batch)
            
            if len(batch) < page_size:
                break
            page += 1
        
        if not all_jobs:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(all_jobs)
        
        # Clean and standardize data
        df['match_level'] = df['match_level'].fillna('unknown').str.lower()
        df['route_type'] = df['route_type'].fillna('Unknown').str.title()
        df['market'] = df['market'].fillna('Unknown')

        # Debug: Print unique market names to see what we have
        print("🔍 Markets in jobs data:", sorted(df['market'].unique()))
        
        # Get job seeker counts once for all markets (more efficient)
        if LIVE_AIRTABLE_SYNC:
            job_seeker_counts = get_job_seeker_counts()
            print("🔍 Airtable job seeker counts:", job_seeker_counts)
        else:
            job_seeker_counts = FALLBACK_JOB_SEEKER_COUNTS
            print("🔍 Using fallback job seeker counts:", job_seeker_counts)

        # Define target markets (exclude custom locations like Montgomery)
        TARGET_MARKETS = {
            'Houston', 'Dallas', 'Las Vegas', 'Bay Area', 'Phoenix', 'Denver',
            'Newark', 'Stockton', 'Inland Empire', 'Trenton'
        }

        # Group by market and calculate statistics (only target markets)
        stats = []

        for market in df['market'].unique():
            # Skip non-target markets
            if market not in TARGET_MARKETS:
                continue
            market_jobs = df[df['market'] == market]
            
            # Quality breakdown
            good_count = len(market_jobs[market_jobs['match_level'] == 'good'])
            so_so_count = len(market_jobs[market_jobs['match_level'] == 'so-so'])
            bad_count = len(market_jobs[market_jobs['match_level'] == 'bad'])
            unknown_quality = len(market_jobs[~market_jobs['match_level'].isin(['good', 'so-so', 'bad'])])
            
            # Route breakdown
            local_count = len(market_jobs[market_jobs['route_type'] == 'Local'])
            otr_count = len(market_jobs[market_jobs['route_type'] == 'Otr'])
            unknown_route = len(market_jobs[market_jobs['route_type'] == 'Unknown'])
            
            total_jobs = len(market_jobs)
            quality_jobs = good_count + so_so_count
            quality_rate = (quality_jobs / total_jobs * 100) if total_jobs > 0 else 0

            # Get job seeker count for this market
            job_seekers = job_seeker_counts.get(market, 0)

            # Calculate ratios
            jobs_per_seeker = round(quality_jobs / job_seekers, 2) if job_seekers > 0 else 0
            total_jobs_per_seeker = round(total_jobs / job_seekers, 2) if job_seekers > 0 else 0

            stats.append({
                'market': market,
                'total_jobs': total_jobs,
                'good': good_count,
                'so_so': so_so_count,
                'bad': bad_count,
                'unknown_quality': unknown_quality,
                'local': local_count,
                'otr': otr_count,
                'unknown_route': unknown_route,
                'quality_jobs': quality_jobs,
                'quality_rate': round(quality_rate, 1),
                'job_seekers': job_seekers,
                'jobs_per_seeker': jobs_per_seeker,
                'total_jobs_per_seeker': total_jobs_per_seeker
            })
        
        result_df = pd.DataFrame(stats)
        result_df = result_df.sort_values(['quality_jobs', 'total_jobs'], ascending=[False, False])
        
        return result_df
        
    except Exception as e:
        st.error(f"❌ Error fetching market analytics: {e}")
        return pd.DataFrame()

def render_market_summary_cards(df: pd.DataFrame):
    """Render summary cards with key metrics"""
    if df.empty:
        st.warning("No data available")
        return
    
    # Calculate totals
    total_jobs = df['total_jobs'].sum()
    total_quality = df['quality_jobs'].sum()
    total_good = df['good'].sum()
    total_so_so = df['so_so'].sum()
    total_local = df['local'].sum()
    total_otr = df['otr'].sum()
    total_job_seekers = df['job_seekers'].sum()
    avg_quality_rate = df['quality_rate'].mean()
    avg_jobs_per_seeker = df['jobs_per_seeker'].mean()

    # Create summary cards
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric(
            label="📊 Total Jobs",
            value=f"{total_jobs:,}",
            delta=f"{len(df)} markets"
        )
    
    with col2:
        st.metric(
            label="⭐ Quality Jobs", 
            value=f"{total_quality:,}",
            delta=f"{avg_quality_rate:.1f}% avg rate"
        )
    
    with col3:
        st.metric(
            label="✅ Excellent",
            value=f"{total_good:,}",
            delta=f"{(total_good/total_jobs*100):.1f}%" if total_jobs > 0 else "0%"
        )
    
    with col4:
        st.metric(
            label="🏠 Local Routes",
            value=f"{total_local:,}",
            delta=f"{(total_local/total_jobs*100):.1f}%" if total_jobs > 0 else "0%"
        )
    
    with col5:
        st.metric(
            label="🛣️ OTR Routes",
            value=f"{total_otr:,}",
            delta=f"{(total_otr/total_jobs*100):.1f}%" if total_jobs > 0 else "0%"
        )

    with col6:
        st.metric(
            label="👥 Total Job Seekers",
            value=f"{total_job_seekers:,}",
            delta=f"{avg_jobs_per_seeker:.1f} avg jobs/seeker"
        )

    # Overall ratio metric (prominent)
    st.markdown("### 🎯 **Key Metric: Quality Jobs to Job Seekers Ratio**")
    overall_ratio = total_quality / total_job_seekers if total_job_seekers > 0 else 0

    col_ratio1, col_ratio2, col_ratio3 = st.columns(3)
    with col_ratio1:
        ratio_color = "🔴" if overall_ratio < 10 else "🟢"
        st.metric(
            label=f"{ratio_color} **Overall Quality Jobs per Job Seeker**",
            value=f"{overall_ratio:.2f}",
            delta="Target: 10+ jobs per seeker",
            delta_color="inverse" if overall_ratio < 10 else "normal"
        )

    with col_ratio2:
        st.metric(
            label="📊 Total Quality Jobs",
            value=f"{total_quality:,}",
            delta=f"{len(df)} markets"
        )

    with col_ratio3:
        st.metric(
            label="👥 Total Active Job Seekers",
            value=f"{total_job_seekers:,}",
            delta="From Airtable filtered view"
        )

def render_market_analytics_table(df: pd.DataFrame):
    """Render detailed market analytics table"""
    if df.empty:
        st.warning("No market data available")
        return
    
    # Format the dataframe for display
    display_df = df.copy()
    
    # Reorder columns for better readability - adding job seekers and ratio
    columns_order = [
        'market', 'total_jobs', 'quality_jobs', 'job_seekers', 'jobs_per_seeker',
        'quality_rate', 'good', 'so_so', 'bad', 'local', 'otr', 'unknown_route'
    ]

    display_df = display_df[columns_order]

    # Rename columns for better display
    display_df.columns = [
        'Market', 'Total Jobs', 'Quality Jobs', 'Job Seekers', 'Quality Jobs/Seeker',
        'Quality %', 'Good', 'So-So', 'Bad', 'Local', 'OTR', 'Unknown Route'
    ]
    
    # Style the dataframe
    def style_quality_rate(val):
        if pd.isna(val):
            return ''
        elif val >= 75:
            return 'background-color: #d4edda; color: #155724'
        elif val >= 50:
            return 'background-color: #fff3cd; color: #856404'
        else:
            return 'background-color: #f8d7da; color: #721c24'

    def style_jobs_per_seeker(val):
        if pd.isna(val):
            return ''
        elif val < 10:
            return 'background-color: #f8d7da; color: #721c24; font-weight: bold'  # Red for under 10
        elif val >= 20:
            return 'background-color: #d4edda; color: #155724; font-weight: bold'  # Green for 20+
        else:
            return 'background-color: #fff3cd; color: #856404'  # Yellow for 10-19
    
    def style_job_count(val):
        if pd.isna(val):
            return ''
        elif val >= 100:
            return 'font-weight: bold; color: #28a745'
        elif val >= 50:
            return 'font-weight: bold; color: #ffc107'
        else:
            return 'color: #6c757d'
    
    # Apply styling
    styled_df = display_df.style.format({
        'Quality %': '{:.1f}%',
        'Total Jobs': '{:,}',
        'Quality Jobs': '{:,}',
        'Job Seekers': '{:,}',
        'Quality Jobs/Seeker': '{:.2f}',
        'Good': '{:,}',
        'So-So': '{:,}',
        'Bad': '{:,}',
        'Local': '{:,}',
        'OTR': '{:,}',
        'Unknown Route': '{:,}'
    }).map(style_quality_rate, subset=['Quality %']).map(style_job_count, subset=['Total Jobs']).map(style_jobs_per_seeker, subset=['Quality Jobs/Seeker'])
    
    st.dataframe(styled_df, hide_index=True)

def render_market_charts(df: pd.DataFrame):
    """Render interactive charts for market analytics"""
    if df.empty:
        return
    
    # Prepare data for charts
    top_markets = df.head(10).copy()  # Top 10 markets by quality jobs
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Quality Jobs by Market")
        
        # Stacked bar chart for quality distribution
        fig_quality = go.Figure(data=[
            go.Bar(name='Excellent', x=top_markets['market'], y=top_markets['good'], marker_color='#28a745'),
            go.Bar(name='Good Fit', x=top_markets['market'], y=top_markets['so_so'], marker_color='#ffc107'),
            go.Bar(name='Poor Fit', x=top_markets['market'], y=top_markets['bad'], marker_color='#dc3545')
        ])
        
        fig_quality.update_layout(
            barmode='stack',
            title="Job Quality Distribution",
            xaxis_title="Market",
            yaxis_title="Number of Jobs",
            height=400
        )
        
        st.plotly_chart(fig_quality)
    
    with col2:
        st.subheader("🛣️ Route Types by Market")
        
        # Stacked bar chart for route distribution (Local, OTR, Unknown)
        fig_routes = go.Figure(data=[
            go.Bar(name='Local', x=top_markets['market'], y=top_markets['local'], marker_color='#17a2b8'),
            go.Bar(name='OTR', x=top_markets['market'], y=top_markets['otr'], marker_color='#6f42c1'),
            go.Bar(name='Unknown', x=top_markets['market'], y=top_markets['unknown_route'], marker_color='#6c757d')
        ])
        
        fig_routes.update_layout(
            barmode='stack',
            title="Route Type Distribution",
            xaxis_title="Market",
            yaxis_title="Number of Jobs",
            height=400
        )
        
        st.plotly_chart(fig_routes)
    
    # Quality rate comparison
    st.subheader("⭐ Quality Rate Comparison")
    
    fig_rates = px.bar(
        top_markets, 
        x='market', 
        y='quality_rate',
        title="Quality Rate by Market",
        color='quality_rate',
        color_continuous_scale='RdYlGn',
        labels={'quality_rate': 'Quality Rate (%)', 'market': 'Market'}
    )
    
    fig_rates.update_layout(height=400)
    st.plotly_chart(fig_rates)

def render_export_options(df: pd.DataFrame, time_window: str):
    """Render data export options"""
    if df.empty:
        return
    
    st.subheader("📤 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # CSV export
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📄 Download as CSV",
            data=csv_data,
            file_name=f"market_analytics_{time_window.replace(' ', '_')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Summary report
        total_jobs = df['total_jobs'].sum()
        quality_jobs = df['quality_jobs'].sum()
        
        summary = f"""Market Analytics Report - {time_window}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

SUMMARY:
- Total Markets: {len(df)}
- Total Jobs: {total_jobs:,}
- Quality Jobs: {quality_jobs:,} ({(quality_jobs/total_jobs*100):.1f}%)
- Average Quality Rate: {df['quality_rate'].mean():.1f}%

TOP 5 MARKETS BY QUALITY JOBS:
{df.head(5)[['market', 'quality_jobs', 'quality_rate']].to_string(index=False)}
"""
        
        st.download_button(
            label="📋 Download Summary",
            data=summary,
            file_name=f"market_summary_{time_window.replace(' ', '_')}.txt",
            mime="text/plain"
        )
    
    with col3:
        st.metric(
            label="📊 Dataset Size",
            value=f"{len(df)} markets",
            delta=f"{total_jobs:,} total jobs"
        )

def show_admin_market_dashboard():
    """Main dashboard function"""
    st.title("🏢 Market Analytics Dashboard")
    st.markdown("Comprehensive market statistics with quality and route breakdowns")
    
    # Time window selector
    st.subheader("⏰ Time Window")
    
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        time_preset = st.selectbox(
            "Select Time Window:",
            options=[
                "Last 24 Hours",
                "Last 3 Days", 
                "Last Week",
                "Last Month",
                "Last 3 Months",
                "All Time",
                "Custom"
            ],
            index=2  # Default to Last Week
        )
    
    with col2:
        if time_preset == "Custom":
            custom_hours = st.number_input(
                "Custom Hours:",
                min_value=1,
                max_value=8760,  # 1 year
                value=168,  # 1 week
                step=24
            )
        else:
            custom_hours = None
    
    with col3:
        col3a, col3b = st.columns(2)
        with col3a:
            refresh_button = st.button("🔄 Refresh Data", type="primary")
            if refresh_button:
                try:
                    st.rerun()
                except Exception:
                    # Backward compatibility for older Streamlit
                    st.experimental_rerun()

        with col3b:
            if LIVE_AIRTABLE_SYNC:
                refresh_airtable_button = st.button("📊 Refresh Airtable")
                if refresh_airtable_button:
                    with st.spinner("Refreshing job seeker data from Airtable..."):
                        refresh_airtable_job_seeker_cache()
                        st.success("✅ Airtable job seeker data refreshed!")
                    try:
                        st.rerun()
                    except Exception:
                        st.experimental_rerun()
    
    # Map time presets to hours
    time_mapping = {
        "Last 24 Hours": 24,
        "Last 3 Days": 72,
        "Last Week": 168,
        "Last Month": 720,
        "Last 3 Months": 2160,
        "All Time": None,
        "Custom": custom_hours
    }
    
    hours_filter = time_mapping[time_preset]
    
    # Load and display data
    with st.spinner("🔍 Loading market analytics..."):
        df = get_market_analytics(hours=hours_filter)
    
    if df.empty:
        st.warning(f"⚠️ No data found for {time_preset.lower()}")
        return
    
    # Display summary cards
    render_market_summary_cards(df)
    
    st.divider()
    
    # Display detailed table
    st.subheader("📊 Detailed Market Breakdown")
    render_market_analytics_table(df)
    
    st.divider()
    
    # Display charts
    render_market_charts(df)

    st.divider()

    # Export options
    render_export_options(df, time_preset)

    # Data freshness info
    st.caption(f"📅 Data loaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Time window: {time_preset}")

if __name__ == "__main__":
    show_admin_market_dashboard()
