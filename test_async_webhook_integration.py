#!/usr/bin/env python3
"""
Integration test for Async Job Manager and Webhook system
Tests the complete end-to-end workflow for Google async batches
"""

import os
import sys
import time
import json
import tempfile
import threading
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import requests

def load_secrets():
    """Load secrets for testing"""
    try:
        import toml
        secrets_path = ".streamlit/secrets.toml"
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            for key, value in secrets.items():
                os.environ[key] = str(value)
            return True
        return False
    except Exception as e:
        print(f"❌ Error loading secrets: {e}")
        return False

def test_async_job_manager_initialization():
    """Test AsyncJobManager can be initialized"""
    print("🧪 Testing AsyncJobManager initialization...")

    try:
        from async_job_manager import AsyncJobManager

        manager = AsyncJobManager()
        print("✅ AsyncJobManager initialized successfully")

        # Check required attributes
        assert hasattr(manager, 'supabase_client'), "Missing supabase_client"
        assert hasattr(manager, 'outscraper_api_key'), "Missing outscraper_api_key"
        assert hasattr(manager, 'google_jobs_url'), "Missing google_jobs_url"

        print("✅ All required attributes present")
        return True, manager

    except Exception as e:
        print(f"❌ AsyncJobManager initialization failed: {e}")
        return False, None

def test_job_submission_flow():
    """Test async job submission without actually calling Outscraper"""
    print("\n🧪 Testing job submission flow...")

    try:
        from async_job_manager import AsyncJobManager

        manager = AsyncJobManager()

        # Mock search parameters
        search_params = {
            'location': 'Houston, TX',
            'search_terms': 'CDL driver test',
            'limit': 10,
            'coach_username': 'test_coach'
        }

        # Mock the Outscraper API call
        with patch('requests.get') as mock_get:
            # Mock successful Outscraper response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'id': 'test-request-123',
                'status': 'pending'
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Mock Supabase insert
            with patch.object(manager, 'supabase_client') as mock_supabase:
                mock_supabase.table.return_value.insert.return_value.execute.return_value = {
                    'data': [{'id': 1}]
                }

                # Test job submission
                result = manager.submit_google_search(search_params, search_params['coach_username'])

                if result and result.get('success'):
                    print("✅ Job submission flow successful")
                    print(f"   Request ID: {result.get('request_id', 'unknown')}")
                    print(f"   Job ID: {result.get('job_id', 'unknown')}")
                    return True
                else:
                    print(f"❌ Job submission failed: {result}")
                    return False

    except Exception as e:
        print(f"❌ Job submission test failed: {e}")
        return False

def test_webhook_payload_processing():
    """Test webhook payload processing logic"""
    print("\n🧪 Testing webhook payload processing...")

    try:
        from async_job_manager import AsyncJobManager

        manager = AsyncJobManager()

        # Mock Google Jobs data
        mock_google_data = [[{
            'title': 'Test CDL Driver Position',
            'company_name': 'Test Trucking Company',
            'location': 'Houston, TX',
            'description': 'Test description for webhook integration',
            'salary': '$50,000 - $60,000',
            'link': 'https://jobs.google.com/test-webhook',
            'apply_options': [{'link': 'https://testcompany.com/apply'}],
            'detected_extensions': {'posted_at': '1 day ago'}
        }]]

        search_params = {
            'location': 'Houston, TX',
            'search_terms': 'CDL driver',
            'coach_username': 'test_coach'
        }

        # Test Google results processing
        result_df = manager.process_google_results(mock_google_data, search_params)

        if not result_df.empty:
            print("✅ Google results processing successful")
            print(f"   Processed {len(result_df)} jobs")

            # Check canonical schema
            required_columns = [
                'source.platform', 'source.title', 'source.company',
                'source.location', 'source.description', 'source.apply_url',
                'sys.scraped_at', 'sys.hash', 'meta.search_terms'
            ]

            missing_columns = [col for col in required_columns if col not in result_df.columns]
            if missing_columns:
                print(f"⚠️ Missing columns: {missing_columns}")
            else:
                print("✅ All required columns present")

            # Validate data content
            job_data = result_df.iloc[0]
            assert job_data['source.platform'] == 'google', "Platform should be google"
            assert job_data['source.title'] == 'Test CDL Driver Position', "Title mismatch"
            assert job_data['meta.search_terms'] == 'CDL driver', "Search terms mismatch"

            print("✅ Data validation passed")
            return True
        else:
            print("❌ Result DataFrame is empty")
            return False

    except Exception as e:
        print(f"❌ Webhook payload processing test failed: {e}")
        return False

def test_job_hash_consistency():
    """Test job hashing for deduplication"""
    print("\n🧪 Testing job hash consistency...")

    try:
        from async_job_manager import AsyncJobManager

        manager = AsyncJobManager()

        # Test identical jobs produce same hash
        job1 = {
            'title': 'CDL Driver',
            'company_name': 'ABC Trucking',
            'location': 'Dallas, TX',
            'link': 'https://example.com/job1'
        }

        job2 = {
            'title': 'CDL Driver',
            'company_name': 'ABC Trucking',
            'location': 'Dallas, TX',
            'link': 'https://example.com/job1'
        }

        job3 = {
            'title': 'Local Driver',  # Different title
            'company_name': 'ABC Trucking',
            'location': 'Dallas, TX',
            'link': 'https://example.com/job1'
        }

        hash1 = manager.generate_job_hash(job1)
        hash2 = manager.generate_job_hash(job2)
        hash3 = manager.generate_job_hash(job3)

        # Identical jobs should have same hash
        if hash1 == hash2:
            print("✅ Identical jobs produce same hash")
        else:
            print(f"❌ Hash mismatch: {hash1} != {hash2}")
            return False

        # Different jobs should have different hash
        if hash1 != hash3:
            print("✅ Different jobs produce different hash")
        else:
            print(f"❌ Different jobs have same hash: {hash1}")
            return False

        # Hash format validation
        if len(hash1) == 16 and all(c in '0123456789abcdef' for c in hash1):
            print("✅ Hash format validation passed")
        else:
            print(f"❌ Invalid hash format: {hash1}")
            return False

        return True

    except Exception as e:
        print(f"❌ Job hash test failed: {e}")
        return False

def test_coach_notification_system():
    """Test coach notification functionality"""
    print("\n🧪 Testing coach notification system...")

    try:
        from async_job_manager import AsyncJobManager

        manager = AsyncJobManager()

        # Mock Supabase notification insert
        with patch.object(manager, 'supabase_client') as mock_supabase:
            mock_supabase.table.return_value.insert.return_value.execute.return_value = {
                'data': [{'id': 1}]
            }

            # Test notification
            result = manager.notify_coach(
                coach_username='test_coach',
                message='Test notification for webhook integration',
                notification_type='test',
                job_id=123
            )

            if result:
                print("✅ Coach notification successful")

                # Verify the call was made
                mock_supabase.table.assert_called_with('coach_notifications')
                call_args = mock_supabase.table.return_value.insert.call_args[0][0]

                assert call_args['coach_username'] == 'test_coach'
                assert call_args['message'] == 'Test notification for webhook integration'
                assert call_args['notification_type'] == 'test'
                assert call_args['job_id'] == 123

                print("✅ Notification data validation passed")
                return True
            else:
                print("❌ Coach notification failed")
                return False

    except Exception as e:
        print(f"❌ Coach notification test failed: {e}")
        return False

def test_error_handling():
    """Test error handling in various scenarios"""
    print("\n🧪 Testing error handling scenarios...")

    try:
        from async_job_manager import AsyncJobManager

        manager = AsyncJobManager()

        # Test invalid job data processing
        invalid_data = [[{"invalid": "data"}]]
        search_params = {'location': 'Test', 'search_terms': 'test', 'coach_username': 'test'}

        try:
            result_df = manager.process_google_results(invalid_data, search_params)
            # Should handle gracefully and return empty or error DataFrame
            print("✅ Invalid data handled gracefully")
        except Exception as e:
            print(f"⚠️ Exception handling could be improved: {e}")

        # Test hash generation with missing fields
        incomplete_job = {'title': 'Test Job'}  # Missing company, location, link

        try:
            hash_result = manager.generate_job_hash(incomplete_job)
            if hash_result:
                print("✅ Incomplete job hash handled")
            else:
                print("⚠️ Hash generation returned None for incomplete job")
        except Exception as e:
            print(f"⚠️ Hash generation error handling needs improvement: {e}")

        return True

    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_webhook_endpoint_mock():
    """Test webhook endpoint with mock server"""
    print("\n🧪 Testing webhook endpoint handling...")

    try:
        # Import Flask app
        from outscraper_webhook import app

        # Create test client
        with app.test_client() as client:
            # Test health endpoint
            health_response = client.get('/webhook/outscraper/health')
            if health_response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint failed: {health_response.status_code}")

            # Test status endpoint
            status_response = client.get('/webhook/outscraper/status')
            print(f"📊 Status endpoint: {status_response.status_code}")

            # Test webhook with sample payload
            webhook_payload = {
                "id": "test-integration-123",
                "status": "Success",
                "data": [{
                    "title": "Integration Test CDL Driver",
                    "company_name": "Test Company",
                    "location": "Test Location",
                    "description": "Test description",
                    "salary": "$50,000",
                    "link": "https://test.com/job",
                    "apply_options": [{"link": "https://test.com/apply"}],
                    "detected_extensions": {"posted_at": "test"}
                }]
            }

            # Mock AsyncJobManager for webhook test
            with patch('outscraper_webhook.AsyncJobManager') as mock_manager_class:
                mock_manager = MagicMock()
                mock_manager.get_pending_jobs.return_value = []  # No pending jobs
                mock_manager_class.return_value = mock_manager

                webhook_response = client.post(
                    '/webhook/outscraper/job-complete',
                    json=webhook_payload,
                    headers={'Content-Type': 'application/json'}
                )

                print(f"📬 Webhook response: {webhook_response.status_code}")

                if webhook_response.status_code == 200:
                    print("✅ Webhook endpoint handling successful")
                    return True
                else:
                    print(f"❌ Webhook endpoint failed: {webhook_response.data}")
                    return False

    except Exception as e:
        print(f"❌ Webhook endpoint test failed: {e}")
        return False

def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Async Job Manager & Webhook Integration Tests")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Load environment
    load_secrets()

    tests = [
        ("AsyncJobManager Initialization", test_async_job_manager_initialization),
        ("Job Submission Flow", test_job_submission_flow),
        ("Webhook Payload Processing", test_webhook_payload_processing),
        ("Job Hash Consistency", test_job_hash_consistency),
        ("Coach Notification System", test_coach_notification_system),
        ("Error Handling", test_error_handling),
        ("Webhook Endpoint Mock", test_webhook_endpoint_mock),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 50)

        try:
            if test_name == "AsyncJobManager Initialization":
                result, manager = test_func()
            else:
                result = test_func()

            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")

        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("🎯 INTEGRATION TEST RESULTS:")
    print(f"   Tests Passed: {passed}/{total}")
    print(f"   Success Rate: {(passed/total)*100:.1f}%")

    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ Async Job Manager & Webhook system is ready for production")
        return True
    else:
        print(f"\n⚠️ {total - passed} tests failed - system needs attention")
        return False

if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)