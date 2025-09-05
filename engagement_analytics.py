import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
import pandas as pd

# Assuming supabase_utils is available for data fetching
try:
    from supabase_utils import get_client, fetch_click_events
except ImportError:
    get_client = None
    fetch_click_events = None

def get_free_agent_engagement_insights(
    start_date: datetime,
    end_date: datetime,
    coach_username: Optional[str] = None
) -> Dict[str, Any]:
    """
    Provides advanced engagement insights for Free Agents within a date range.
    Can be filtered by coach.
    """
    insights = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_clicks": 0,
        "unique_agents": 0,
        "avg_clicks_per_agent": 0.0,
        "clicks_over_time": [],
        "top_agents_by_clicks": [],
        "top_job_categories": [], # Requires job category data in click events
        "geographic_engagement": {}, # Requires location data in click events
        "engagement_patterns": {} # Placeholder for time-based analysis
    }

    if not fetch_click_events or not get_client:
        print("Warning: Supabase utilities not available. Cannot fetch click data.")
        return insights

    all_clicks_df = fetch_click_events(start_date, end_date)

    # Handle empty DataFrame gracefully
    if all_clicks_df.empty:
        return insights

    # Filter by coach if specified
    if coach_username:
        # Ensure coach_username column exists
        if 'coach_username' not in all_clicks_df.columns:
            print(f"Warning: coach_username column missing from click data")
            return insights
        all_clicks_df = all_clicks_df[all_clicks_df['coach_username'] == coach_username]

    if all_clicks_df.empty:
        return insights

    insights["total_clicks"] = len(all_clicks_df)
    insights["unique_agents"] = all_clicks_df['candidate_id'].nunique()
    if insights["unique_agents"] > 0:
        insights["avg_clicks_per_agent"] = insights["total_clicks"] / insights["unique_agents"]

    # Clicks over time
    clicks_over_time = all_clicks_df.groupby(all_clicks_df['timestamp'].dt.date).size().reset_index(name='clicks')
    insights["clicks_over_time"] = clicks_over_time.to_dict(orient='records')

    # Top agents by clicks
    top_agents = all_clicks_df.groupby('candidate_id').size().sort_values(ascending=False).head(10).reset_index(name='clicks')
    # Attempt to get agent names if available
    if 'candidate_name' in all_clicks_df.columns:
        agent_name_map = all_clicks_df.set_index('candidate_id')['candidate_name'].to_dict()
        top_agents['candidate_name'] = top_agents['candidate_id'].map(agent_name_map)
    insights["top_agents_by_clicks"] = top_agents.to_dict(orient='records')

    # Geographic engagement (requires 'city' or 'market' in click events)
    if 'market' in all_clicks_df.columns:
        insights["geographic_engagement"] = all_clicks_df['market'].value_counts().to_dict()

    # Job category preference (requires 'match' or other category in click events)
    if 'match' in all_clicks_df.columns:
        insights["top_job_categories"] = all_clicks_df['match'].value_counts().to_dict()

    # Placeholder for time-based engagement patterns (e.g., clicks by hour of day, day of week)
    insights["engagement_patterns"] = {
        "clicks_by_hour": all_clicks_df['timestamp'].dt.hour.value_counts().sort_index().to_dict(),
        "clicks_by_day_of_week": all_clicks_df['timestamp'].dt.dayofweek.value_counts().sort_index().to_dict() # Monday=0, Sunday=6
    }

    return insights

if __name__ == "__main__":
    # Example Usage:
    # Set up mock environment variables for testing if not running with actual Supabase
    # os.environ["SUPABASE_URL"] = "YOUR_SUPABASE_URL"
    # os.environ["SUPABASE_ANON_KEY"] = "YOUR_SUPABASE_ANON_KEY"

    end_date_test = datetime.now(timezone.utc)
    start_date_test = end_date_test - timedelta(days=30)

    print("\n--- Testing Free Agent Engagement Insights (All Agents) ---")
    all_agents_insights = get_free_agent_engagement_insights(start_date_test, end_date_test)
    print(f"All Agents Insights:\n{all_agents_insights}")

    print("\n--- Testing Free Agent Engagement Insights (Filtered by Coach) ---")
    test_coach = "test_coach" # Replace with an actual coach username
    coach_filtered_insights = get_free_agent_engagement_insights(start_date_test, end_date_test, coach_username=test_coach)
    print(f"Coach-Filtered Insights for {test_coach}:\n{coach_filtered_insights}")
