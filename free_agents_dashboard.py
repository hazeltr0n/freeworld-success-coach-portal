#!/usr/bin/env python3
"""
Free Agents Analytics Dashboard
Enhanced Streamlit dashboard for Free Agent performance and engagement analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

def show_free_agents_dashboard(coach):
    """Display the enhanced free agents analytics dashboard"""

    st.markdown("# 👥 Free Agents Analytics Dashboard")
    st.markdown("---")

    # Import free agents functions
    try:
        from free_agents_rollup import (
            get_free_agents_analytics, get_high_engagement_agents,
            get_inactive_agents, get_market_agent_breakdown,
            update_free_agents_analytics_table, get_client
        )
    except ImportError:
        st.error("❌ Free agents analytics module not available")
        return

    # Control buttons
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("🔄 Update Analytics Data"):
            with st.spinner("Updating free agents analytics..."):
                try:
                    update_free_agents_analytics_table()
                    st.success("✅ Analytics data updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to update: {e}")

    with col2:
        if st.button("⚡ Manual Refresh"):
            with st.spinner("Running manual agents refresh..."):
                try:
                    client = get_client()
                    if client:
                        # Call the Supabase scheduled function manually
                        result = client.rpc('scheduled_agents_refresh').execute()
                        if result.data and isinstance(result.data, dict):
                            if result.data.get('success'):
                                agents_updated = result.data.get('agents_updated', 0)
                                st.success(f"✅ Manual refresh completed! Updated {agents_updated} agents.")
                            else:
                                error_msg = result.data.get('error', 'Unknown error')
                                st.error(f"❌ Refresh failed: {error_msg}")
                        else:
                            st.success("✅ Manual refresh completed!")
                        st.rerun()
                    else:
                        st.error("❌ Supabase client not available")
                except Exception as e:
                    st.error(f"❌ Manual refresh failed: {e}")

    with col3:
        show_coach_filter = st.checkbox("👨‍🏫 My Agents Only", value=True)

    with col4:
        activity_filter = st.selectbox(
            "🎯 Activity Level",
            ["All Levels", "High", "Medium", "Low", "New", "Inactive"],
            index=0
        )

    with col5:
        market_filter = st.selectbox(
            "🌍 Market Filter",
            ["All Markets", "Houston", "Dallas", "Las Vegas", "Bay Area", "Denver", "Phoenix", "Other"],
            index=0
        )

    # Load analytics data
    try:
        coach_username = coach.username if show_coach_filter else None
        agents_df = get_free_agents_analytics(coach_username=coach_username, limit=None)

        if agents_df.empty:
            st.warning("📊 No agents analytics data available. Click 'Update Analytics Data' to populate.")
            return

        # Apply filters
        if activity_filter != "All Levels":
            agents_df = agents_df[agents_df['activity_level'] == activity_filter.lower()]

        if market_filter != "All Markets":
            agents_df = agents_df[agents_df['market'] == market_filter]

    except Exception as e:
        st.error(f"❌ Error loading analytics data: {e}")
        return

    # Summary metrics
    st.markdown("## 📈 Overview")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Agents", len(agents_df))

    with col2:
        active_agents = len(agents_df[agents_df['activity_level'] != 'inactive'])
        active_pct = (active_agents / len(agents_df) * 100) if len(agents_df) > 0 else 0
        st.metric("Active Agents", f"{active_agents} ({active_pct:.1f}%)")

    with col3:
        high_engagement = len(agents_df[agents_df['activity_level'] == 'high'])
        st.metric("High Engagement", high_engagement)

    with col4:
        avg_engagement = agents_df['engagement_score'].mean() if not agents_df.empty else 0
        st.metric("Avg Engagement Score", f"{avg_engagement:.1f}")

    with col5:
        total_clicks = agents_df['total_job_clicks'].sum() if not agents_df.empty else 0
        st.metric("Total Job Clicks", f"{total_clicks:,}")

    # Charts and Analytics
    st.markdown("## 📊 Analytics")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎯 Engagement Distribution")

        if not agents_df.empty:
            # Engagement score histogram
            fig = px.histogram(
                agents_df,
                x='engagement_score',
                nbins=20,
                title="Agent Engagement Score Distribution",
                labels={'engagement_score': 'Engagement Score', 'count': 'Number of Agents'},
                color_discrete_sequence=['#3B82F6']
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig)
        else:
            st.info("No engagement data available")

    with col2:
        st.markdown("### 📍 Market Distribution")

        if not agents_df.empty and 'market' in agents_df.columns:
            market_counts = agents_df['market'].value_counts().head(10)

            if not market_counts.empty:
                fig = px.pie(
                    values=market_counts.values,
                    names=market_counts.index,
                    title="Agents by Market",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig)
            else:
                st.info("No market data available")
        else:
            st.info("Market data not available")

    # Activity Level Analysis
    st.markdown("### 🚀 Activity Level Breakdown")

    if not agents_df.empty:
        activity_counts = agents_df['activity_level'].value_counts()

        col1, col2 = st.columns(2)

        with col1:
            # Activity level pie chart
            fig = px.pie(
                values=activity_counts.values,
                names=[level.title() for level in activity_counts.index],
                title="Agent Activity Levels",
                color_discrete_map={
                    'High': '#10B981',
                    'Medium': '#F59E0B',
                    'Low': '#EF4444',
                    'New': '#8B5CF6',
                    'Inactive': '#6B7280'
                }
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig)

        with col2:
            # Engagement vs Activity scatter plot
            if len(agents_df) > 1:
                fig = px.scatter(
                    agents_df,
                    x='total_portal_visits',
                    y='total_job_clicks',
                    color='activity_level',
                    size='engagement_score',
                    hover_data=['agent_name', 'market'],
                    title="Portal Visits vs Job Clicks",
                    color_discrete_map={
                        'high': '#10B981',
                        'medium': '#F59E0B',
                        'low': '#EF4444',
                        'new': '#8B5CF6',
                        'inactive': '#6B7280'
                    }
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig)
            else:
                st.info("Need more agents for scatter plot")

    # Enhanced Agents Table
    st.markdown("## 📋 Agent Details")

    # Prepare display columns
    display_columns = ['agent_name', 'market', 'activity_level', 'engagement_score']

    if 'total_portal_visits' in agents_df.columns:
        display_columns.append('total_portal_visits')

    if 'total_job_clicks' in agents_df.columns:
        display_columns.append('total_job_clicks')

    if 'click_through_rate' in agents_df.columns:
        display_columns.append('click_through_rate')

    if 'last_activity_at' in agents_df.columns:
        agents_df['last_activity_display'] = pd.to_datetime(agents_df['last_activity_at']).dt.strftime('%Y-%m-%d %H:%M')
        display_columns.append('last_activity_display')

    # Route preferences display
    if 'route_preferences' in agents_df.columns:
        def format_route_prefs(route_data):
            if not isinstance(route_data, dict) or not route_data:
                return "Not set"
            return route_data.get('primary', 'flexible').title()

        agents_df['route_pref_display'] = agents_df['route_preferences'].apply(format_route_prefs)
        display_columns.append('route_pref_display')

    # Coach filter
    if not show_coach_filter and 'coach_username' in agents_df.columns:
        display_columns.insert(1, 'coach_username')

    # Column configuration
    column_config = {
        'agent_name': st.column_config.TextColumn('Agent Name', width='large'),
        'coach_username': st.column_config.TextColumn('Coach', width='medium'),
        'market': st.column_config.TextColumn('Market', width='medium'),
        'activity_level': st.column_config.TextColumn('Activity Level', width='small'),
        'engagement_score': st.column_config.NumberColumn('Engagement Score', format='%.1f', width='small'),
        'total_portal_visits': st.column_config.NumberColumn('Portal Visits', format='%d', width='small'),
        'total_job_clicks': st.column_config.NumberColumn('Job Clicks', format='%d', width='small'),
        'click_through_rate': st.column_config.NumberColumn('CTR %', format='%.1f%%', width='small'),
        'last_activity_display': st.column_config.TextColumn('Last Activity', width='medium'),
        'route_pref_display': st.column_config.TextColumn('Route Pref', width='small')
    }

    # Search functionality
    search_term = st.text_input("🔍 Search agents:", placeholder="Enter agent name...")

    display_df = agents_df[display_columns].copy() if display_columns else agents_df.copy()

    if search_term and not display_df.empty:
        if 'agent_name' in display_df.columns:
            mask = display_df['agent_name'].str.contains(search_term, case=False, na=False)
            display_df = display_df[mask]

    # Display table
    st.dataframe(
        display_df,
        column_config=column_config,
                height=600
    )

    # Detailed Analytics Section
    st.markdown("## 🔍 Detailed Analytics")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔥 Top Performers")
        if not agents_df.empty:
            top_performers = agents_df.nlargest(10, 'engagement_score')[
                ['agent_name', 'market', 'engagement_score', 'total_job_clicks']
            ]
            st.dataframe(top_performers)

    with col2:
        st.markdown("### 😴 Needs Attention")
        inactive_or_low = agents_df[
            agents_df['activity_level'].isin(['inactive', 'low'])
        ].nlargest(10, 'last_activity_at')[
            ['agent_name', 'market', 'activity_level', 'last_activity_display']
        ] if 'last_activity_display' in agents_df.columns else pd.DataFrame()

        if not inactive_or_low.empty:
            st.dataframe(inactive_or_low)
        else:
            st.info("All agents are actively engaged! 🎉")

    # Export functionality
    st.markdown("## 💾 Export & Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Export Analytics CSV"):
            csv = agents_df.to_csv(index=False)
            st.download_button(
                label="💾 Download Analytics CSV",
                data=csv,
                file_name=f"free_agents_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    with col2:
        if st.button("🔥 View High Engagement Only"):
            st.session_state['filter_high_engagement'] = True
            st.rerun()

    with col3:
        if st.button("📧 Generate Re-engagement List"):
            inactive_agents = agents_df[agents_df['activity_level'] == 'inactive']
            if not inactive_agents.empty:
                st.success(f"Found {len(inactive_agents)} agents needing re-engagement")
                st.dataframe(
                    inactive_agents[['agent_name', 'agent_email', 'market', 'last_activity_at']],
                                    )
            else:
                st.info("No inactive agents found!")

    # Company and Route Preferences Analytics
    if not agents_df.empty:
        st.markdown("## 🎯 Preference Analytics")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🛣️ Route Preferences")
            route_prefs = agents_df['route_pref_display'].value_counts() if 'route_pref_display' in agents_df.columns else pd.Series()

            if not route_prefs.empty:
                fig = px.bar(
                    x=route_prefs.index,
                    y=route_prefs.values,
                    title="Agent Route Preferences",
                    labels={'x': 'Route Type', 'y': 'Number of Agents'},
                    color_discrete_sequence=['#3B82F6']
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig)

        with col2:
            st.markdown("### 📈 Engagement Trends")

            # Show engagement by market
            if 'market' in agents_df.columns:
                market_engagement = agents_df.groupby('market')['engagement_score'].mean().sort_values(ascending=False).head(8)

                if not market_engagement.empty:
                    fig = px.bar(
                        x=market_engagement.index,
                        y=market_engagement.values,
                        title="Average Engagement by Market",
                        labels={'x': 'Market', 'y': 'Avg Engagement Score'},
                        color_discrete_sequence=['#10B981']
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig)

    # Action Items and Insights
    if not agents_df.empty:
        st.markdown("## 💡 Insights & Action Items")

        insights = []

        # High performers
        high_engagement_count = len(agents_df[agents_df['activity_level'] == 'high'])
        if high_engagement_count > 0:
            insights.append(f"🔥 You have {high_engagement_count} high-engagement agents who are actively using the platform")

        # Inactive agents
        inactive_count = len(agents_df[agents_df['activity_level'] == 'inactive'])
        if inactive_count > 0:
            insights.append(f"😴 {inactive_count} agents haven't been active recently and may need re-engagement")

        # Low click-through rates
        low_ctr = agents_df[agents_df['click_through_rate'] < 10] if 'click_through_rate' in agents_df.columns else pd.DataFrame()
        if not low_ctr.empty:
            insights.append(f"📊 {len(low_ctr)} agents have low click-through rates (<10%) - consider reviewing their job matches")

        # Market concentration
        if 'market' in agents_df.columns:
            top_market = agents_df['market'].value_counts().index[0]
            market_count = agents_df['market'].value_counts().iloc[0]
            market_pct = market_count / len(agents_df) * 100
            if market_pct > 40:
                insights.append(f"🌍 {market_pct:.1f}% of your agents are in {top_market} - consider expanding to other markets")

        for insight in insights:
            st.info(insight)

        if not insights:
            st.success("🎉 Your agent portfolio looks well-balanced and engaged!")

if __name__ == "__main__":
    # For testing purposes
    class MockCoach:
        username = "test_coach"

    show_free_agents_dashboard(MockCoach())