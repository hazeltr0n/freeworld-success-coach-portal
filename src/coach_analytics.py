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

# Assuming user_management is available for coach data
try:
    from user_management import get_coach_manager
except ImportError:
    get_coach_manager = None

def get_coach_performance_metrics(
    coach_username: str,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    """
    Calculates performance metrics for a given coach within a date range.
    Metrics include search patterns, job quality preferences, and success rates.
    """
    metrics = {
        "coach_username": coach_username,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_searches": 0,
        "total_jobs_generated": 0,
        "total_quality_jobs": 0,
        "total_clicks": 0,
        "unique_agents_engaged": 0,
        "avg_clicks_per_agent": 0.0,
        "job_quality_breakdown": {},
        "search_pattern_breakdown": {},
        "success_rate": 0.0 # e.g., (total_clicks / total_quality_jobs) or (unique_agents_engaged / total_agents_assigned)
    }

    if not fetch_click_events or not get_client:
        print("Warning: Supabase utilities not available. Cannot fetch click data.")
        return metrics

    # Fetch click events for the coach
    all_clicks_df = fetch_click_events(start_date, end_date)
    
    # Handle empty DataFrame or missing columns gracefully
    if all_clicks_df.empty:
        return metrics
        
    # Ensure coach_username column exists (added by fetch_click_events)
    if 'coach_username' not in all_clicks_df.columns:
        print(f"Warning: coach_username column missing from click data")
        return metrics
        
    coach_clicks_df = all_clicks_df[all_clicks_df['coach_username'] == coach_username]

    if coach_clicks_df.empty:
        return metrics

    metrics["total_clicks"] = len(coach_clicks_df)
    metrics["unique_agents_engaged"] = coach_clicks_df['candidate_id'].nunique()
    if metrics["unique_agents_engaged"] > 0:
        metrics["avg_clicks_per_agent"] = metrics["total_clicks"] / metrics["unique_agents_engaged"]

    # Placeholder for search patterns and job quality (requires pipeline data)
    # For now, we'll use click data to infer job quality preferences
    if 'match' in coach_clicks_df.columns:
        metrics["job_quality_breakdown"] = coach_clicks_df['match'].value_counts().to_dict()

    # Placeholder for total searches and jobs generated (requires pipeline analytics data)
    # This data would typically come from a 'search_analytics' table in Supabase
    # For now, we'll just use click data as a proxy for engagement success
    metrics["success_rate"] = metrics["total_clicks"] / max(1, metrics["total_quality_jobs"]) # Needs actual total_quality_jobs

    return metrics

def generate_weekly_performance_report(coach_username: str) -> Dict[str, Any]:
    """
    Generates a weekly performance report for a coach.
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)
    
    print(f"Generating weekly report for {coach_username} from {start_date.date()} to {end_date.date()}")
    metrics = get_coach_performance_metrics(coach_username, start_date, end_date)
    
    report = {
        "title": f"Weekly Performance Report for {coach_username}",
        "period": f"{start_date.date()} to {end_date.date()}",
        "metrics": metrics,
        "summary": f"Coach {coach_username} had {metrics['total_clicks']} total clicks from {metrics['unique_agents_engaged']} unique agents this week."
    }
    return report

def get_coach_comparison_data(coach_usernames: List[str], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Compares performance metrics across multiple coaches.
    """
    comparison_data = {"coaches": {}}
    for coach_username in coach_usernames:
        metrics = get_coach_performance_metrics(coach_username, start_date, end_date)
        comparison_data["coaches"][coach_username] = metrics
    return comparison_data

if __name__ == "__main__":
    # Example Usage:
    # Set up mock environment variables for testing if not running with actual Supabase
    # os.environ["SUPABASE_URL"] = "YOUR_SUPABASE_URL"
    # os.environ["SUPABASE_ANON_KEY"] = "YOUR_SUPABASE_ANON_KEY"

    # Test individual coach performance
    print("\n--- Testing Individual Coach Performance ---")
    test_coach = "test_coach" # Replace with an actual coach username
    end_date_test = datetime.now(timezone.utc)
    start_date_test = end_date_test - timedelta(days=30)
    coach_metrics = get_coach_performance_metrics(test_coach, start_date_test, end_date_test)
    print(f"Metrics for {test_coach}:\n{coach_metrics}")

    # Test weekly report generation
    print("\n--- Testing Weekly Report Generation ---")
    weekly_report = generate_weekly_performance_report(test_coach)
    print(f"Weekly Report for {test_coach}:\n{weekly_report}")

    # Test coach comparison
    print("\n--- Testing Coach Comparison ---")
    test_coaches = ["test_coach", "another_coach"] # Replace with actual coach usernames
    comparison_metrics = get_coach_comparison_data(test_coaches, start_date_test, end_date_test)
    print(f"Coach Comparison:\n{comparison_metrics}")
