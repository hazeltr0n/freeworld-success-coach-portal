import os
import pytest
import pandas as pd
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

# Ensure the path to src is correct
import sys
sys.path.insert(0, os.path.abspath('./')) # Add project root to path
sys.path.insert(0, os.path.abspath('./src')) # Add src directory to path

# Mock Supabase utilities for testing
@pytest.fixture
def mock_supabase_utils():
    with patch('supabase_utils.get_client') as mock_get_client:
        with patch('supabase_utils.fetch_click_events') as mock_fetch_click_events:
            
            # Mock get_client
            mock_get_client.return_value = MagicMock() # Return a mock client

            # Mock fetch_click_events to return sample data
            sample_clicks = [
                # Coach: test_coach, Agent: agent1, Market: Houston, Match: good
                {"clicked_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(), "coach": "test_coach", "coach_username": "test_coach", "market": "Houston", "route": "local", "match": "good", "fair": True, "candidate_id": "agent1_uuid", "candidate_name": "Agent One", "short_id": "click1", "target_url": "http://job1.com"},
                {"clicked_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(), "coach": "test_coach", "coach_username": "test_coach", "market": "Houston", "route": "local", "match": "good", "fair": True, "candidate_id": "agent1_uuid", "candidate_name": "Agent One", "short_id": "click2", "target_url": "http://job2.com"},
                {"clicked_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(), "coach": "test_coach", "coach_username": "test_coach", "market": "Dallas", "route": "otr", "match": "so-so", "fair": False, "candidate_id": "agent1_uuid", "candidate_name": "Agent One", "short_id": "click3", "target_url": "http://job3.com"},
                # Coach: another_coach, Agent: agent2, Market: Austin, Match: good
                {"clicked_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(), "coach": "another_coach", "coach_username": "another_coach", "market": "Austin", "route": "local", "match": "good", "fair": True, "candidate_id": "agent2_uuid", "candidate_name": "Agent Two", "short_id": "click4", "target_url": "http://job4.com"},
                {"clicked_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(), "coach": "another_coach", "coach_username": "another_coach", "market": "Houston", "route": "otr", "match": "bad", "fair": False, "candidate_id": "agent2_uuid", "candidate_name": "Agent Two", "short_id": "click5", "target_url": "http://job5.com"},
                # Coach: test_coach, Agent: agent3, Market: Houston, Match: good
                {"clicked_at": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(), "coach": "test_coach", "coach_username": "test_coach", "market": "Houston", "route": "local", "match": "good", "fair": True, "candidate_id": "agent3_uuid", "candidate_name": "Agent Three", "short_id": "click6", "target_url": "http://job6.com"},
            ]
            
            # Convert sample_clicks to DataFrame as fetch_click_events now returns DataFrame
            # Convert sample_clicks to DataFrame as fetch_click_events now returns DataFrame
        mock_fetch_click_events.side_effect = lambda start, end, **kwargs: pd.DataFrame(sample_clicks)
            
            yield

# Mock user_management for coach data
@pytest.fixture
def mock_user_management():
    with patch('user_management.get_coach_manager') as mock_get_coach_manager:
        mock_coach_manager = MagicMock()
        mock_coach_manager.coaches = {
            "test_coach": MagicMock(username="test_coach", full_name="Test Coach"),
            "another_coach": MagicMock(username="another_coach", full_name="Another Coach"),
            "admin": MagicMock(username="admin", full_name="Admin User", role="admin"),
        }
        mock_get_coach_manager.return_value = mock_coach_manager
        yield

# Test coach_analytics.py
from coach_analytics import get_coach_performance_metrics, generate_weekly_performance_report, get_coach_comparison_data

def test_get_coach_performance_metrics(mock_supabase_utils, mock_user_management):
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    metrics = get_coach_performance_metrics("test_coach", start_date, end_date)

    assert metrics["coach_username"] == "test_coach"
    assert metrics["total_clicks"] == 4 # click1, click2, click3, click6
    assert metrics["unique_agents_engaged"] == 2 # agent1_uuid, agent3_uuid
    assert metrics["avg_clicks_per_agent"] == 2.0
    assert metrics["job_quality_breakdown"] == {'good': 3, 'so-so': 1}

def test_generate_weekly_performance_report(mock_supabase_utils, mock_user_management):
    report = generate_weekly_performance_report("test_coach")
    assert "Weekly Performance Report" in report["title"]
    assert report["metrics"]["total_clicks"] == 4

def test_get_coach_comparison_data(mock_supabase_utils, mock_user_management):
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    comparison_data = get_coach_comparison_data(["test_coach", "another_coach"], start_date, end_date)
    assert "test_coach" in comparison_data["coaches"]
    assert "another_coach" in comparison_data["coaches"]
    assert comparison_data["coaches"]["test_coach"]["total_clicks"] == 4
    assert comparison_data["coaches"]["another_coach"]["total_clicks"] == 2

# Test engagement_analytics.py
from engagement_analytics import get_free_agent_engagement_insights

def test_get_free_agent_engagement_insights(mock_supabase_utils, mock_user_management):
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    insights = get_free_agent_engagement_insights(start_date, end_date)

    assert insights["total_clicks"] == 6
    assert insights["unique_agents"] == 3
    assert insights["avg_clicks_per_agent"] == 2.0
    assert len(insights["clicks_over_time"]) > 0
    assert insights["top_agents_by_clicks"][0]['candidate_id'] == 'agent1_uuid' # Agent1 has 3 clicks
    assert insights["geographic_engagement"] == {'Houston': 4, 'Dallas': 1, 'Austin': 1}
    assert insights["top_job_categories"] == {'good': 4, 'so-so': 1, 'bad': 1}
    assert "clicks_by_hour" in insights["engagement_patterns"]

    # Test with coach filter
    coach_filtered_insights = get_free_agent_engagement_insights(start_date, end_date, coach_username="another_coach")
    assert coach_filtered_insights["total_clicks"] == 2
    assert coach_filtered_insights["unique_agents"] == 1 # agent2_uuid

# Test business_intelligence.py
from business_intelligence import generate_monthly_bi_report, export_report_to_pdf

def test_generate_monthly_bi_report(mock_supabase_utils, mock_user_management):
    # Use a month with sample data (e.g., current month)
    current_month = datetime.now(timezone.utc).month
    current_year = datetime.now(timezone.utc).year
    report = generate_monthly_bi_report(current_month, current_year)

    assert "Monthly Business Intelligence Report" in report["title"]
    assert report["overall_metrics"]["total_clicks_program"] == 6
    assert report["overall_metrics"]["unique_agents_program"] == 3
    assert len(report["top_performing_coaches"]) > 0
    assert report["top_performing_coaches"][0]['coach_username'] == 'test_coach' # test_coach has more clicks
    assert len(report["top_engaging_agents"]) > 0

    # Check placeholders
    assert report["market_trends"]["example_trend"] == "Placeholder for job market trend analysis."
    assert report["roi_calculations"]["example_roi"] == "Placeholder for ROI calculation."

# Mock open for export_report_to_pdf
@pytest.fixture
def mock_open(mocker):
    mock_file = mocker.mock_open()
    mocker.patch('builtins.open', mock_file)
    return mock_file

def test_export_report_to_pdf(mock_open):
    report_data = {
        "title": "Test Report", 
        "period": "Jan 2023", 
        "overall_metrics": {"total_clicks_program": 100},
        "market_trends": {"example_trend": "Placeholder"},
        "roi_calculations": {"example_roi": "Placeholder"},
        "top_performing_coaches": [],
        "top_engaging_agents": [],
        "raw_data_summary": {}
    }
    output_path = "test_report.pdf"
    success = export_report_to_pdf(report_data, output_path)

    assert success is True
    mock_open.assert_called_once_with(output_path, 'w')
    mock_open().write.assert_called()
