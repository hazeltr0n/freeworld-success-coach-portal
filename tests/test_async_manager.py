import os
import sys
from unittest import mock
from datetime import datetime, timezone
import requests

def import_async_manager():
    """Import async_job_manager from parent directory"""
    base = os.path.abspath(os.path.dirname(__file__))
    root = os.path.abspath(os.path.join(base, '..'))
    if root not in sys.path:
        sys.path.insert(0, root)
    import async_job_manager
    return async_job_manager

def test_create_job_entry_success():
    """Test creating a new async job entry in the database"""
    ajm = import_async_manager()
    
    # Mock the supabase client
    mock_client = mock.Mock()
    mock_result = mock.Mock()
    mock_result.data = [{
        'id': 123,
        'coach_username': 'test_coach',
        'job_type': 'google_jobs',
        'search_params': {'location': 'Houston', 'terms': 'CDL driver'},
        'status': 'pending',
        'result_count': 0,
        'quality_job_count': 0,
        'created_at': '2025-08-31T10:00:00Z',
        'scheduled_search_id': None,
        'request_id': None,
        'submitted_at': None,
        'completed_at': None,
        'error_message': None
    }]
    
    mock_client.table().insert().execute.return_value = mock_result
    
    # Create AsyncJobManager with mocked client
    manager = ajm.AsyncJobManager()
    manager.supabase_client = mock_client
    
    # Test creating job entry
    search_params = {'location': 'Houston', 'terms': 'CDL driver'}
    job = manager.create_job_entry('test_coach', 'google_jobs', search_params)
    
    # Verify the job object
    assert isinstance(job, ajm.AsyncJob)
    assert job.id == 123
    assert job.coach_username == 'test_coach'
    assert job.job_type == 'google_jobs'
    assert job.status == 'pending'
    assert job.search_params == search_params
    
    # Verify supabase was called correctly
    mock_client.table.assert_called_with('async_job_queue')


def test_submit_google_search_success():
    """Test successful Google Jobs search submission"""
    ajm = import_async_manager()
    
    # Mock supabase client
    mock_client = mock.Mock()
    mock_result = mock.Mock()
    mock_result.data = [{
        'id': 456,
        'coach_username': 'test_coach',
        'job_type': 'google_jobs',
        'search_params': {'location': 'Dallas', 'search_terms': 'truck driver'},
        'status': 'pending',
        'result_count': 0,
        'quality_job_count': 0,
        'created_at': '2025-08-31T10:00:00Z',
        'scheduled_search_id': None,
        'request_id': None,
        'submitted_at': None,
        'completed_at': None,
        'error_message': None
    }]
    
    mock_client.table().insert().execute.return_value = mock_result
    mock_client.table().update().eq().execute.return_value = mock.Mock(data=[{}])
    
    # Mock requests response
    mock_response = mock.Mock()
    mock_response.json.return_value = {'id': 'async-123-456'}
    mock_response.raise_for_status.return_value = None
    
    # Create manager with mocks
    manager = ajm.AsyncJobManager()
    manager.supabase_client = mock_client
    manager.outscraper_api_key = 'test-api-key'
    
    with mock.patch('requests.get', return_value=mock_response) as mock_get:
        # Test search submission
        search_params = {
            'location': 'Dallas',
            'search_terms': 'truck driver',
            'limit': 100
        }
        
        job = manager.submit_google_search(search_params, 'test_coach')
        
        # Verify job was created and updated
        assert job.id == 456
        assert job.status == 'submitted'
        assert job.request_id == 'async-123-456'
        
        # Verify API call was made
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert 'truck driver Dallas' in call_args[1]['params']['query']
        assert call_args[1]['params']['async'] == 'true'


def test_submit_google_search_api_error():
    """Test Google Jobs search submission with API error"""
    ajm = import_async_manager()
    
    # Mock supabase client
    mock_client = mock.Mock()
    mock_result = mock.Mock()
    mock_result.data = [{
        'id': 789,
        'coach_username': 'test_coach',
        'job_type': 'google_jobs',
        'search_params': {'location': 'Phoenix', 'search_terms': 'driver'},
        'status': 'pending',
        'result_count': 0,
        'quality_job_count': 0,
        'created_at': '2025-08-31T10:00:00Z',
        'scheduled_search_id': None,
        'request_id': None,
        'submitted_at': None,
        'completed_at': None,
        'error_message': None
    }]
    
    mock_client.table().insert().execute.return_value = mock_result
    mock_client.table().update().eq().execute.return_value = mock.Mock(data=[{}])
    
    # Mock requests to raise an error
    mock_response = mock.Mock()
    mock_response.raise_for_status.side_effect = requests.RequestException('API Error')
    
    manager = ajm.AsyncJobManager()
    manager.supabase_client = mock_client
    manager.outscraper_api_key = 'test-api-key'
    
    with mock.patch('requests.get', return_value=mock_response):
        # Test that error is properly handled
        search_params = {'location': 'Phoenix', 'search_terms': 'driver', 'limit': 100}
        
        try:
            manager.submit_google_search(search_params, 'test_coach')
            assert False, "Expected RequestException to be raised"
        except requests.RequestException:
            pass  # Expected
        
        # Verify job status was updated to failed
        update_calls = mock_client.table().update.call_args_list
        assert len(update_calls) > 0
        # Check if any update call set status to 'failed'
        failed_update_found = False
        for call in update_calls:
            if call[0][0].get('status') == 'failed':
                failed_update_found = True
                break
        assert failed_update_found


def test_get_pending_jobs():
    """Test retrieving pending async jobs"""
    ajm = import_async_manager()
    
    # Mock supabase client
    mock_client = mock.Mock()
    mock_result = mock.Mock()
    mock_result.data = [
        {
            'id': 100,
            'coach_username': 'coach1',
            'job_type': 'google_jobs',
            'search_params': {'location': 'Austin'},
            'status': 'pending',
            'result_count': 0,
            'quality_job_count': 0,
            'created_at': '2025-08-31T09:00:00Z',
            'scheduled_search_id': None,
            'request_id': 'req-123',
            'submitted_at': '2025-08-31T09:05:00Z',
            'completed_at': None,
            'error_message': None
        },
        {
            'id': 101,
            'coach_username': 'coach2',
            'job_type': 'google_jobs',
            'search_params': {'location': 'San Antonio'},
            'status': 'submitted',
            'result_count': 0,
            'quality_job_count': 0,
            'created_at': '2025-08-31T09:30:00Z',
            'scheduled_search_id': None,
            'request_id': 'req-456',
            'submitted_at': '2025-08-31T09:35:00Z',
            'completed_at': None,
            'error_message': None
        }
    ]
    
    mock_client.table().select().in_().order().execute.return_value = mock_result
    
    manager = ajm.AsyncJobManager()
    manager.supabase_client = mock_client
    
    # Test getting all pending jobs
    pending_jobs = manager.get_pending_jobs()
    
    assert len(pending_jobs) == 2
    assert all(isinstance(job, ajm.AsyncJob) for job in pending_jobs)
    assert pending_jobs[0].id == 100
    assert pending_jobs[0].status == 'pending'
    assert pending_jobs[1].id == 101
    assert pending_jobs[1].status == 'submitted'
    
    # Verify supabase query was constructed correctly
    mock_client.table.assert_called_with('async_job_queue')


def test_get_completed_jobs():
    """Test retrieving completed async jobs"""
    ajm = import_async_manager()
    
    # Mock supabase client
    mock_client = mock.Mock()
    mock_result = mock.Mock()
    mock_result.data = [
        {
            'id': 200,
            'coach_username': 'coach1',
            'job_type': 'google_jobs',
            'search_params': {'location': 'Houston'},
            'status': 'completed',
            'result_count': 150,
            'quality_job_count': 25,
            'created_at': '2025-08-31T08:00:00Z',
            'scheduled_search_id': None,
            'request_id': 'req-789',
            'submitted_at': '2025-08-31T08:05:00Z',
            'completed_at': '2025-08-31T08:08:00Z',
            'error_message': None
        }
    ]
    
    mock_client.table().select().eq().order().limit().execute.return_value = mock_result
    
    manager = ajm.AsyncJobManager()
    manager.supabase_client = mock_client
    
    # Test getting completed jobs for specific coach
    completed_jobs = manager.get_completed_jobs('coach1', limit=10)
    
    assert len(completed_jobs) == 1
    job = completed_jobs[0]
    assert isinstance(job, ajm.AsyncJob)
    assert job.id == 200
    assert job.status == 'completed'
    assert job.result_count == 150
    assert job.quality_job_count == 25


if __name__ == '__main__':
    print("🧪 Running async manager tests...")
    
    test_create_job_entry_success()
    print("✅ Create job entry test passed")
    
    test_submit_google_search_success()
    print("✅ Submit Google search success test passed")
    
    test_submit_google_search_api_error()
    print("✅ Submit Google search error handling test passed")
    
    test_get_pending_jobs()
    print("✅ Get pending jobs test passed")
    
    test_get_completed_jobs()
    print("✅ Get completed jobs test passed")
    
    print("\n🎉 All async manager tests passed!")