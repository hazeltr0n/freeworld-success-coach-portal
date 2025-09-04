import os
import sys
import json
import pandas as pd
from unittest import mock

def import_app():
    """Import app module from parent directory"""
    base = os.path.abspath(os.path.dirname(__file__))
    root = os.path.abspath(os.path.join(base, '..'))
    if root not in sys.path:
        sys.path.insert(0, root)
    import app
    return app

def test_render_jobs_html_cached_basic():
    """Test _render_jobs_html_cached with basic job data"""
    app_module = import_app()
    
    # Create sample job DataFrame
    sample_jobs = pd.DataFrame([
        {
            'source.title': 'CDL Driver - Local Routes',
            'source.company': 'FreeWorld Logistics', 
            'ai.match': 'good',
            'ai.summary': 'Excellent local CDL position with competitive pay',
            'ai.route_type': 'Local',
            'source.indeed_url': 'https://indeed.com/job1',
            'meta.tracked_url': 'https://short.io/abc123'
        },
        {
            'source.title': 'OTR Truck Driver',
            'source.company': 'Highway Express',
            'ai.match': 'so-so', 
            'ai.summary': 'Long haul position with good benefits',
            'ai.route_type': 'OTR',
            'source.indeed_url': 'https://indeed.com/job2',
            'meta.tracked_url': 'https://short.io/def456'
        }
    ])
    
    sample_agent_params = {
        'agent_name': 'Test Agent',
        'agent_uuid': 'test-123',
        'location': 'Houston, TX',
        'coach_username': 'test_coach'
    }
    
    # Convert to JSON for caching function (it expects JSON strings)
    df_json = sample_jobs.to_json(orient='records')
    params_json = json.dumps(sample_agent_params)
    
    # Mock the HTML generation dependencies
    with mock.patch('pdf.html_pdf_generator.jobs_dataframe_to_dicts') as mock_to_dicts, \
         mock.patch('pdf.html_pdf_generator.render_jobs_html') as mock_render:
        
        mock_to_dicts.return_value = sample_jobs.to_dict('records')
        mock_render.return_value = '<html><body>Mock HTML Report</body></html>'
        
        # Call the cached function
        html_result = app_module._render_jobs_html_cached(df_json, params_json)
        
        # Verify calls and result
        mock_to_dicts.assert_called_once()
        mock_render.assert_called_once()
        
        assert isinstance(html_result, str)
        assert 'Mock HTML Report' in html_result
        
        # Verify the jobs data was converted properly
        jobs_arg = mock_to_dicts.call_args[0][0]
        assert len(jobs_arg) == 2
        assert jobs_arg.iloc[0]['source.title'] == 'CDL Driver - Local Routes'


def test_df_fingerprint_consistency():
    """Test that _df_fingerprint produces consistent hashes for same data"""
    app_module = import_app()
    
    # Create identical DataFrames
    df1 = pd.DataFrame([
        {'job_id': 1, 'title': 'CDL Driver', 'company': 'Test Co', '_internal': 'ignore'},
        {'job_id': 2, 'title': 'Truck Driver', 'company': 'Other Co', '_internal': 'ignore'}
    ])
    
    df2 = pd.DataFrame([
        {'job_id': 1, 'title': 'CDL Driver', 'company': 'Test Co', '_internal': 'different'},
        {'job_id': 2, 'title': 'Truck Driver', 'company': 'Other Co', '_internal': 'different'}
    ])
    
    # Should produce same fingerprint (ignores _internal columns)
    fingerprint1 = app_module._df_fingerprint(df1)
    fingerprint2 = app_module._df_fingerprint(df2)
    
    assert fingerprint1 == fingerprint2
    assert len(fingerprint1) == 64  # SHA256 hex digest length
    
    # Different data should produce different fingerprint
    df3 = pd.DataFrame([
        {'job_id': 3, 'title': 'Different Job', 'company': 'New Co'}
    ])
    
    fingerprint3 = app_module._df_fingerprint(df3)
    assert fingerprint1 != fingerprint3


def test_render_jobs_html_cached_with_empty_data():
    """Test _render_jobs_html_cached handles empty job data gracefully"""
    app_module = import_app()
    
    # Empty DataFrame
    empty_df = pd.DataFrame()
    empty_params = {'agent_name': 'Test Agent'}
    
    df_json = empty_df.to_json(orient='records')
    params_json = json.dumps(empty_params)
    
    # Mock the dependencies
    with mock.patch('pdf.html_pdf_generator.jobs_dataframe_to_dicts') as mock_to_dicts, \
         mock.patch('pdf.html_pdf_generator.render_jobs_html') as mock_render:
        
        mock_to_dicts.return_value = []
        mock_render.return_value = '<html><body>No jobs found</body></html>'
        
        # Should not crash with empty data
        html_result = app_module._render_jobs_html_cached(df_json, params_json)
        
        assert isinstance(html_result, str)
        assert 'No jobs found' in html_result
        mock_to_dicts.assert_called_once()


def test_render_jobs_html_cached_error_handling():
    """Test _render_jobs_html_cached handles errors gracefully"""
    app_module = import_app()
    
    # Invalid JSON should not crash the function
    invalid_df_json = "invalid json"
    valid_params_json = json.dumps({'agent_name': 'Test'})
    
    try:
        result = app_module._render_jobs_html_cached(invalid_df_json, valid_params_json)
        # If it doesn't raise an exception, it should return something
        assert isinstance(result, str)
    except Exception as e:
        # If it does raise an exception, it should be a reasonable one
        assert 'json' in str(e).lower() or 'decode' in str(e).lower()


if __name__ == '__main__':
    print("🧪 Running HTML cache tests...")
    
    test_render_jobs_html_cached_basic()
    print("✅ Basic HTML cache test passed")
    
    test_df_fingerprint_consistency()
    print("✅ DataFrame fingerprint consistency test passed")
    
    test_render_jobs_html_cached_with_empty_data()
    print("✅ Empty data handling test passed")
    
    test_render_jobs_html_cached_error_handling()
    print("✅ Error handling test passed")
    
    print("\n🎉 All HTML cache tests passed!")