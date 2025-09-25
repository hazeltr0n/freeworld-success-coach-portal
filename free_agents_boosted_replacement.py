#!/usr/bin/env python3
"""
BOOSTED Free Agents Table - Complete Replacement
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone


def show_free_agent_management_page_BOOSTED(coach):
    """BOOSTED Free Agent Management - Fast, Snappy, Complete"""
    from free_agent_system import (
        save_agent_profile, load_agent_profiles, delete_agent_profile, get_market_options
    )
    from supabase_utils import get_free_agents_analytics_data

    st.header("👥 Free Agent Management (Boosted)")
    st.markdown("*Fast loading • Snappy editing • Individual pathway checkboxes • Unsaved changes flow*")

    # Initialize session state
    if 'agents_page' not in st.session_state:
        st.session_state.agents_page = 0
    if 'unsaved_changes' not in st.session_state:
        st.session_state.unsaved_changes = {}

    # Configuration
    PAGE_SIZE = 50

    # Add New Agent Section (Simplified)
    with st.expander("➕ Add New Free Agent", expanded=False):
        _show_add_agent_section_boosted(coach)

    # Load agents with pagination
    page_num = st.session_state.agents_page
    agents, total_count = _load_agents_page_boosted(coach.username, page_num, PAGE_SIZE)

    if not agents:
        st.info("📝 No agents configured yet - add your first agent above")
        return

    # Pagination info and controls
    _show_pagination_controls_boosted(page_num, total_count, PAGE_SIZE)

    # Main agents table (essential columns only)
    _show_agents_table_boosted(agents, coach)

    # No separate pathways editor - we have inline checkboxes now!

    # Bulk operations
    _show_bulk_operations_boosted(agents, coach)


def _show_add_agent_section_boosted(coach):
    """Simplified add agent section"""
    st.markdown("### Quick Add Agent")

    col1, col2 = st.columns(2)
    with col1:
        agent_name = st.text_input("Agent Name", key="quick_add_name")
        agent_email = st.text_input("Email", key="quick_add_email")
    with col2:
        agent_city = st.text_input("City", key="quick_add_city")
        agent_state = st.text_input("State", key="quick_add_state")

    if st.button("Add Agent", type="primary", disabled=not agent_name):
        if agent_name:
            import uuid
            agent_data = {
                'agent_uuid': str(uuid.uuid4()),
                'agent_name': agent_name,
                'agent_email': agent_email,
                'agent_city': agent_city,
                'agent_state': agent_state,
                'location': 'Houston',
                'route_filter': 'both',
                'fair_chance_only': False,
                'max_jobs': 25,
                'classifier_type': 'cdl',
                'pathway_preferences': [],
                'coach_username': coach.username,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'is_active': True
            }

            with st.spinner("Adding agent..."):
                from free_agent_system import save_agent_profile
                success, message = save_agent_profile(coach.username, agent_data)
                if success:
                    st.success(f"✅ Added {agent_name}")
                    st.rerun()
                else:
                    st.error(f"❌ Failed: {message}")


def _load_agents_page_boosted(coach_username: str, page_num: int, page_size: int) -> tuple:
    """Load agents with pagination and analytics"""
    try:
        from free_agent_system import load_agent_profiles
        from supabase_utils import get_free_agents_analytics_data

        # Load all agents (we'll implement true DB pagination later if needed)
        all_agents = load_agent_profiles(coach_username)
        total_count = len(all_agents)

        # Paginate in memory for now
        start_idx = page_num * page_size
        end_idx = start_idx + page_size
        page_agents = all_agents[start_idx:end_idx]

        # Load analytics for this page only
        if page_agents:
            analytics_df = get_free_agents_analytics_data(coach_username)
            analytics_lookup = {}
            if not analytics_df.empty:
                for _, row in analytics_df.iterrows():
                    analytics_lookup[row['agent_uuid']] = {
                        'total_clicks': row.get('total_job_clicks', 0),
                        'clicks_14d': row.get('job_clicks_14d', 0),
                        'engagement_score': row.get('engagement_score', 0),
                        'activity_level': row.get('activity_level', 'new')
                    }

            # Enhance agents with analytics
            for agent in page_agents:
                agent_uuid = agent.get('agent_uuid', '')
                analytics = analytics_lookup.get(agent_uuid, {})
                agent.update({
                    'total_clicks': analytics.get('total_clicks', 0),
                    'clicks_14d': analytics.get('clicks_14d', 0),
                    'engagement_score': analytics.get('engagement_score', 0),
                    'activity_level': analytics.get('activity_level', 'new')
                })

        return page_agents, total_count

    except Exception as e:
        st.error(f"⚠️ Failed to load agents: {e}")
        return [], 0


def _show_pagination_controls_boosted(page_num: int, total_count: int, page_size: int):
    """Show pagination controls"""
    total_pages = (total_count + page_size - 1) // page_size
    start_idx = page_num * page_size + 1
    end_idx = min(start_idx + page_size - 1, total_count)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if page_num > 0:
            if st.button("⬅️ Previous"):
                st.session_state.agents_page = page_num - 1
                st.rerun()

    with col2:
        st.info(f"📊 Showing {start_idx}-{end_idx} of {total_count} agents (Page {page_num + 1} of {total_pages})")

    with col3:
        if page_num < total_pages - 1:
            if st.button("Next ➡️"):
                st.session_state.agents_page = page_num + 1
                st.rerun()


def _show_agents_table_boosted(agents: list, coach):
    """Show lightweight agents table with INLINE PATHWAY CHECKBOXES"""
    st.markdown("### 📊 Your Free Agents")

    # Prepare data with inline pathway checkboxes
    agent_data = []
    for agent in agents:
        is_active = agent.get('is_active', True)
        status = "🟢 Active" if is_active else "👻 Deleted"

        # Convert pathway_preferences JSON to individual boolean columns
        pathway_preferences = agent.get('pathway_preferences', [])
        # Handle legacy format where it might be ['cdl'] instead of ['cdl_pathway']
        if 'cdl' in pathway_preferences and 'cdl_pathway' not in pathway_preferences:
            pathway_preferences = ['cdl_pathway'] + [p for p in pathway_preferences if p != 'cdl']

        agent_row = {
            'Status': status,
            'Free Agent Name': agent.get('agent_name', 'Unknown'),
            'Market': agent.get('location', 'Houston'),
            'Route': agent.get('route_filter', 'both'),
            'Fair Chance': agent.get('fair_chance_only', False),
            'Max Jobs': agent.get('max_jobs', 25),
            # INLINE PATHWAY CHECKBOXES
            'CDL Jobs': 'cdl_pathway' in pathway_preferences,
            'Dock→Driver': 'dock_to_driver' in pathway_preferences,
            'CDL Training': 'internal_cdl_training' in pathway_preferences,
            'Warehouse→Driver': 'warehouse_to_driver' in pathway_preferences,
            'Logistics': 'logistics_progression' in pathway_preferences,
            'Non-CDL': 'non_cdl_driving' in pathway_preferences,
            'Warehouse': 'general_warehouse' in pathway_preferences,
            'Stepping Stone': 'stepping_stone' in pathway_preferences,
            # Rest of columns
            'Engagement': int(agent.get('engagement_score', 0)),
            'City': agent.get('agent_city', ''),
            'State': agent.get('agent_state', ''),
            'Portal Link': _generate_portal_link_boosted(agent),
            'Delete': False,
            # Hidden fields
            '_agent_uuid': agent.get('agent_uuid', ''),
            '_original_data': agent
        }
        agent_data.append(agent_row)

    df = pd.DataFrame(agent_data)

    # Column config with INLINE PATHWAY CHECKBOXES
    from free_agent_system import get_market_options
    column_config = {
        'Status': st.column_config.TextColumn("Status", disabled=True, width="small"),
        'Free Agent Name': st.column_config.TextColumn("Name", disabled=True, width="medium"),
        'Market': st.column_config.SelectboxColumn(
            "Market", options=get_market_options(), width="small", required=True
        ),
        'Route': st.column_config.SelectboxColumn(
            "Route", options=["both", "local", "otr"], width="small", required=True
        ),
        'Fair Chance': st.column_config.CheckboxColumn("Fair Chance", width="small"),
        'Max Jobs': st.column_config.SelectboxColumn(
            "Max Jobs", options=[15, 25, 50, 100], width="small", required=True
        ),
        # INLINE PATHWAY CHECKBOX COLUMNS
        'CDL Jobs': st.column_config.CheckboxColumn("CDL", width="small", help="Traditional CDL driving positions"),
        'Dock→Driver': st.column_config.CheckboxColumn("Dock→CDL", width="small", help="Dock worker to CDL transition"),
        'CDL Training': st.column_config.CheckboxColumn("Training", width="small", help="Company-sponsored CDL programs"),
        'Warehouse→Driver': st.column_config.CheckboxColumn("Warehouse→CDL", width="small", help="Warehouse to driving progression"),
        'Logistics': st.column_config.CheckboxColumn("Logistics", width="small", help="Logistics career advancement"),
        'Non-CDL': st.column_config.CheckboxColumn("Non-CDL", width="small", help="Non-CDL driving positions"),
        'Warehouse': st.column_config.CheckboxColumn("Warehouse", width="small", help="General warehouse opportunities"),
        'Stepping Stone': st.column_config.CheckboxColumn("Stepping", width="small", help="Career stepping stone positions"),
        # Rest of columns
        'Engagement': st.column_config.NumberColumn("Score", disabled=True, width="small"),
        'City': st.column_config.TextColumn("City", width="small"),
        'State': st.column_config.TextColumn("State", width="small"),
        'Portal Link': st.column_config.TextColumn("Portal", disabled=True, width="medium"),
        'Delete': st.column_config.CheckboxColumn("Delete", width="small"),
        # Hide internal columns
        '_agent_uuid': None,
        '_original_data': None
    }

    # Fast data editor - essential columns only
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        height=400,
        num_rows="fixed",
        key="boosted_agents_editor"
    )

    # Check for changes and show save button
    changes_detected = _check_for_changes_boosted(df, edited_df)
    if changes_detected:
        st.warning("⚠️ You have unsaved changes")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("💾 Save Changes", type="primary"):
                _save_changes_boosted(df, edited_df, coach)
                st.success("✅ Changes saved!")
                st.rerun()
        with col2:
            if st.button("↶ Revert"):
                st.rerun()


def _show_career_pathways_editor_boosted(agents: list, coach):
    """Separate career pathways editor with individual checkboxes"""
    if not agents:
        return

    with st.expander("🛤️ Career Pathways Editor", expanded=False):
        st.markdown("### Edit Career Pathways")
        st.markdown("*Individual checkboxes for each pathway type*")

        # Available pathways
        PATHWAYS = [
            ('CDL Jobs', 'cdl_pathway', '🚚 Traditional CDL driving positions'),
            ('Dock→Driver', 'dock_to_driver', '📦 Dock worker to CDL driver transition'),
            ('CDL Training', 'internal_cdl_training', '🎓 Company-sponsored CDL programs'),
            ('Warehouse→Driver', 'warehouse_to_driver', '📋 General warehouse to driving progression'),
            ('Logistics', 'logistics_progression', '🚛 Logistics career advancement'),
            ('Non-CDL Driving', 'non_cdl_driving', '🚐 Non-CDL driving positions'),
            ('Warehouse', 'general_warehouse', '📦 General warehouse opportunities'),
            ('Stepping Stone', 'stepping_stone', '⬆️ Career stepping stone positions')
        ]

        # Agent selection
        agent_options = [f"{agent.get('agent_name', 'Unknown')} ({agent.get('agent_uuid', '')[:8]})"
                        for agent in agents]

        selected_agent_name = st.selectbox("Select Agent", agent_options, key="pathway_agent_select")

        if selected_agent_name:
            # Find selected agent
            agent_idx = agent_options.index(selected_agent_name)
            selected_agent = agents[agent_idx]

            st.markdown(f"**Editing pathways for: {selected_agent.get('agent_name', 'Unknown')}**")

            # Current pathways
            current_pathways = selected_agent.get('pathway_preferences', [])
            classifier_type = selected_agent.get('classifier_type', 'cdl')

            # If CDL agent, always include cdl_pathway
            if classifier_type == 'cdl' and 'cdl_pathway' not in current_pathways:
                current_pathways = ['cdl_pathway'] + current_pathways

            # Individual pathway checkboxes (NOT ListColumn!)
            st.markdown("**Select Career Pathways:**")
            new_pathways = []

            col1, col2 = st.columns(2)
            for i, (display_name, pathway_key, description) in enumerate(PATHWAYS):
                col = col1 if i % 2 == 0 else col2
                with col:
                    checked = pathway_key in current_pathways
                    if st.checkbox(display_name, value=checked, key=f"pathway_{pathway_key}", help=description):
                        new_pathways.append(pathway_key)

            # Save pathways button
            if st.button("💾 Update Pathways", type="primary"):
                success = _update_agent_pathways_boosted(selected_agent, new_pathways, coach)
                if success:
                    st.success(f"✅ Updated pathways for {selected_agent.get('agent_name', 'Unknown')}")
                    st.rerun()


def _show_bulk_operations_boosted(agents: list, coach):
    """Show bulk operations section"""
    with st.expander("🔧 Bulk Operations", expanded=False):
        st.markdown("### Bulk Actions")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔗 Regenerate All Portal Links"):
                with st.spinner("Regenerating portal links..."):
                    from free_agent_system import save_agent_profile
                    count = 0
                    for agent in agents:
                        # This will trigger Short.io creation for agents without custom_url
                        success, _ = save_agent_profile(coach.username, agent)
                        if success:
                            count += 1
                    st.success(f"✅ Regenerated {count} portal links")
                    st.rerun()

        with col2:
            if st.button("📊 Refresh Analytics"):
                # Clear any cached analytics
                st.cache_data.clear()
                st.success("✅ Analytics cache cleared")
                st.rerun()


def _check_for_changes_boosted(original_df, edited_df) -> bool:
    """Check if any editable fields changed"""
    editable_fields = ['Market', 'Route', 'Fair Chance', 'Max Jobs', 'City', 'State', 'Delete']

    for idx in range(len(original_df)):
        for field in editable_fields:
            if str(original_df.iloc[idx][field]) != str(edited_df.iloc[idx][field]):
                return True
    return False


def _save_changes_boosted(original_df, edited_df, coach):
    """Save changes to database (FAST - converts pathway checkboxes back to JSON)"""
    from free_agent_system import save_agent_profile

    # Include pathway fields in editable fields
    editable_fields = ['Market', 'Route', 'Fair Chance', 'Max Jobs', 'City', 'State', 'Delete',
                      'CDL Jobs', 'Dock→Driver', 'CDL Training', 'Warehouse→Driver',
                      'Logistics', 'Non-CDL', 'Warehouse', 'Stepping Stone']

    for idx in range(len(original_df)):
        # Check if this row changed
        changed = False
        for field in editable_fields:
            if str(original_df.iloc[idx][field]) != str(edited_df.iloc[idx][field]):
                changed = True
                break

        if changed:
            # Update agent
            original_agent = original_df.iloc[idx]['_original_data']
            updated_agent = original_agent.copy()

            # Convert pathway checkboxes back to pathway_preferences JSON array
            pathway_preferences = []
            if edited_df.iloc[idx]['CDL Jobs']:
                pathway_preferences.append('cdl_pathway')
            if edited_df.iloc[idx]['Dock→Driver']:
                pathway_preferences.append('dock_to_driver')
            if edited_df.iloc[idx]['CDL Training']:
                pathway_preferences.append('internal_cdl_training')
            if edited_df.iloc[idx]['Warehouse→Driver']:
                pathway_preferences.append('warehouse_to_driver')
            if edited_df.iloc[idx]['Logistics']:
                pathway_preferences.append('logistics_progression')
            if edited_df.iloc[idx]['Non-CDL']:
                pathway_preferences.append('non_cdl_driving')
            if edited_df.iloc[idx]['Warehouse']:
                pathway_preferences.append('general_warehouse')
            if edited_df.iloc[idx]['Stepping Stone']:
                pathway_preferences.append('stepping_stone')

            updated_agent.update({
                'location': str(edited_df.iloc[idx]['Market']),
                'route_filter': str(edited_df.iloc[idx]['Route']),
                'fair_chance_only': bool(edited_df.iloc[idx]['Fair Chance']),
                'max_jobs': int(edited_df.iloc[idx]['Max Jobs']),
                'agent_city': str(edited_df.iloc[idx]['City']),
                'agent_state': str(edited_df.iloc[idx]['State']),
                'pathway_preferences': pathway_preferences,
                'classifier_type': 'cdl' if 'cdl_pathway' in pathway_preferences else 'pathway'
            })

            # Handle deletion
            if edited_df.iloc[idx]['Delete']:
                updated_agent['is_active'] = False

            # FAST save - existing agents won't trigger Short.io API calls
            save_agent_profile(coach.username, updated_agent)


def _update_agent_pathways_boosted(agent: dict, pathways: list, coach) -> bool:
    """Update agent's career pathways"""
    from free_agent_system import save_agent_profile

    updated_agent = agent.copy()

    # Handle CDL vs pathway classification
    if 'cdl_pathway' in pathways:
        updated_agent['classifier_type'] = 'cdl'
        additional_pathways = [p for p in pathways if p != 'cdl_pathway']
        updated_agent['pathway_preferences'] = additional_pathways
    else:
        updated_agent['classifier_type'] = 'pathway'
        updated_agent['pathway_preferences'] = pathways

    success, message = save_agent_profile(coach.username, updated_agent)
    return success


def _generate_portal_link_boosted(agent: dict) -> str:
    """Generate portal link for agent"""
    try:
        from app import generate_dynamic_portal_link
        return generate_dynamic_portal_link(agent)
    except:
        return "Link generation failed"


if __name__ == "__main__":
    # For testing
    class MockCoach:
        username = "test_coach"

    show_free_agent_management_page_BOOSTED(MockCoach())