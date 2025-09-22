#!/usr/bin/env python3
"""
Simple Manual Refresh Test
Test that can be run directly in Streamlit app
"""

import streamlit as st

def test_manual_refresh_buttons():
    """Test the manual refresh functionality in Streamlit"""

    st.title("🧪 Manual Refresh Button Test")
    st.markdown("---")

    st.markdown("""
    ## Test Instructions

    ### 1. Test Companies Manual Refresh
    1. Go to **Companies** tab
    2. Look for the **⚡ Manual Refresh** button (should be next to "🔄 Update Companies Data")
    3. Click the **⚡ Manual Refresh** button
    4. You should see:
       - ⏳ Spinner: "Running manual companies refresh..."
       - ✅ Success message: "Manual refresh completed! Updated X companies."
       - 🔄 Page refresh to show updated data

    ### 2. Test Free Agents Manual Refresh
    1. Go to **Free Agents** tab → **📊 Analytics** sub-tab
    2. Look for the **⚡ Manual Refresh** button (should be next to "🔄 Update Analytics Data")
    3. Click the **⚡ Manual Refresh** button
    4. You should see:
       - ⏳ Spinner: "Running manual agents refresh..."
       - ✅ Success message: "Manual refresh completed! Updated X agents."
       - 🔄 Page refresh to show updated data

    ### 3. Verify Database Functions
    The manual refresh buttons call these Supabase functions:
    - Companies: `scheduled_companies_refresh()`
    - Free Agents: `scheduled_agents_refresh()`

    ### 4. Check Rollup Logs
    After running manual refreshes, you can check the logs in Supabase SQL Editor:
    ```sql
    SELECT * FROM analytics_rollup_log
    ORDER BY executed_at DESC
    LIMIT 10;
    ```

    You should see entries with:
    - `rollup_type`: 'companies' or 'free_agents'
    - `success`: true
    - `records_processed`: number of companies/agents updated
    - `execution_time_ms`: how long it took

    ## ✅ Expected Results

    - **Button Visibility**: Both manual refresh buttons should be visible
    - **Execution**: Clicking buttons should trigger Supabase functions
    - **Feedback**: Success messages with update counts
    - **Logging**: Entries in analytics_rollup_log table
    - **Data Refresh**: Updated analytics data after refresh

    ## 🚫 Troubleshooting

    If you get errors:
    1. **"Supabase client not available"**: Check environment variables
    2. **"Function does not exist"**: Run setup_scheduled_analytics.sql first
    3. **"Permission denied"**: Enable pg_cron extension in Supabase

    ## 🎯 Benefits for Testing

    - **Immediate Testing**: No waiting for scheduled execution
    - **Blacklist Testing**: Update companies blacklist and see immediate effects
    - **Click Tracking**: Test click events and see analytics update
    - **Engagement Analytics**: Refresh agent data to see latest engagement scores
    """)

    # Add actual test buttons if we can load the modules
    st.markdown("## 🔧 Direct Function Test")

    try:
        from companies_rollup import get_client

        if st.button("🧪 Test Companies Function Access"):
            client = get_client()
            if client:
                st.success("✅ Companies client connected successfully!")
                try:
                    # Just test if the function exists
                    result = client.rpc('scheduled_companies_refresh').execute()
                    st.success("✅ Companies refresh function executed!")
                    st.json(result.data)
                except Exception as e:
                    st.error(f"❌ Function execution failed: {e}")
            else:
                st.error("❌ Companies client failed to connect")

    except ImportError:
        st.info("💡 Run this test from the main Streamlit app where modules are available")

    try:
        from free_agents_rollup import get_client as fa_get_client

        if st.button("🧪 Test Free Agents Function Access"):
            client = fa_get_client()
            if client:
                st.success("✅ Free Agents client connected successfully!")
                try:
                    result = client.rpc('scheduled_agents_refresh').execute()
                    st.success("✅ Free Agents refresh function executed!")
                    st.json(result.data)
                except Exception as e:
                    st.error(f"❌ Function execution failed: {e}")
            else:
                st.error("❌ Free Agents client failed to connect")

    except ImportError:
        st.info("💡 Run this test from the main Streamlit app where modules are available")

if __name__ == "__main__":
    test_manual_refresh_buttons()