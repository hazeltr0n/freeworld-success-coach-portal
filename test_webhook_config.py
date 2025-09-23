#!/usr/bin/env python3
"""
Test and diagnose Outscraper webhook configuration issues
"""

import os
import sys
import requests
import json
from datetime import datetime

def load_secrets():
    """Load secrets from Streamlit config"""
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

def check_webhook_environment():
    """Check webhook environment variables"""
    print("🔍 Checking webhook environment...")

    # Load secrets
    if not load_secrets():
        print("⚠️ Could not load secrets from .streamlit/secrets.toml")

    # Check required environment variables
    required_vars = [
        'OUTSCRAPER_API_KEY',
        'OUTSCRAPER_WEBHOOK_URL'
    ]

    optional_vars = [
        'OUTSCRAPER_WEBHOOK_SECRET',
        'WEBHOOK_PORT'
    ]

    print("\n📋 Required Environment Variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'key' in var.lower() or 'secret' in var.lower():
                display_value = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
            else:
                display_value = value
            print(f"  ✅ {var} = {display_value}")
        else:
            print(f"  ❌ {var} = NOT SET")

    print("\n📋 Optional Environment Variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            display_value = value[:8] + '...' + value[-4:] if 'secret' in var.lower() else value
            print(f"  ✅ {var} = {display_value}")
        else:
            print(f"  ⚪ {var} = NOT SET")

def test_webhook_endpoint():
    """Test the webhook endpoint accessibility"""
    print("\n🌐 Testing webhook endpoint...")

    webhook_url = os.getenv('OUTSCRAPER_WEBHOOK_URL')
    if not webhook_url:
        print("❌ OUTSCRAPER_WEBHOOK_URL not configured")
        return False

    print(f"📍 Webhook URL: {webhook_url}")

    # Test health endpoint
    try:
        health_url = webhook_url.replace('/job-complete', '/health')
        print(f"🏥 Testing health endpoint: {health_url}")

        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint accessible")
            try:
                health_data = response.json()
                print(f"   Status: {health_data.get('status', 'unknown')}")
                print(f"   Service: {health_data.get('service', 'unknown')}")
            except:
                print("   Response: OK (non-JSON)")
        else:
            print(f"❌ Health endpoint returned {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - webhook service not running")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout - webhook service unresponsive")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

    # Test status endpoint
    try:
        status_url = webhook_url.replace('/job-complete', '/status')
        print(f"📊 Testing status endpoint: {status_url}")

        response = requests.get(status_url, timeout=10)
        if response.status_code == 200:
            print("✅ Status endpoint accessible")
            try:
                status_data = response.json()
                print(f"   Status: {status_data.get('status', 'unknown')}")
                print(f"   Pending jobs: {status_data.get('pending_jobs', 'unknown')}")
                print(f"   Recent completed: {status_data.get('recent_completed_jobs', 'unknown')}")
            except:
                print("   Response: OK (non-JSON)")
        else:
            print(f"❌ Status endpoint returned {response.status_code}")

    except Exception as e:
        print(f"❌ Status check failed: {e}")

    return True

def test_webhook_payload():
    """Test webhook with a sample payload"""
    print("\n🧪 Testing webhook with sample payload...")

    webhook_url = os.getenv('OUTSCRAPER_WEBHOOK_URL')
    if not webhook_url:
        print("❌ OUTSCRAPER_WEBHOOK_URL not configured")
        return False

    # Sample payload that matches Outscraper format
    test_payload = {
        "id": "test-request-12345",
        "status": "Success",
        "results_location": "https://api.outscraper.cloud/requests/test-request-12345",
        "data": [{
            "title": "Test CDL Driver Position",
            "company_name": "Test Trucking Company",
            "location": "Houston, TX",
            "description": "Test job description for webhook validation",
            "salary": "$50,000 - $60,000",
            "link": "https://jobs.google.com/test",
            "apply_options": [{"link": "https://testcompany.com/apply"}],
            "detected_extensions": {"posted_at": "1 day ago"}
        }]
    }

    headers = {
        'Content-Type': 'application/json'
    }

    # Add webhook secret if configured
    webhook_secret = os.getenv('OUTSCRAPER_WEBHOOK_SECRET')
    if webhook_secret:
        headers['X-Webhook-Secret'] = webhook_secret
        print("🔐 Using webhook secret for authentication")

    try:
        print(f"📤 Sending test payload to: {webhook_url}")
        response = requests.post(webhook_url, json=test_payload, headers=headers, timeout=30)

        print(f"📬 Response status: {response.status_code}")

        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Webhook processed successfully")
                print(f"   Message: {result.get('message', 'No message')}")
                if 'job_id' in result:
                    print(f"   Job ID: {result['job_id']}")
            except:
                print("✅ Webhook processed (non-JSON response)")
        elif response.status_code == 400:
            print("❌ Bad request - check payload format")
            try:
                error = response.json()
                print(f"   Error: {error.get('error', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text}")
        elif response.status_code == 401:
            print("❌ Unauthorized - check webhook secret")
        elif response.status_code == 404:
            print("❌ Not found - check webhook URL path")
        elif response.status_code == 500:
            print("❌ Internal server error - check webhook service logs")
            try:
                error = response.json()
                print(f"   Error: {error.get('error', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text}")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")

        return response.status_code == 200

    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - webhook service not running")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout - webhook processing too slow")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def check_async_job_manager():
    """Check AsyncJobManager configuration"""
    print("\n🤖 Checking AsyncJobManager configuration...")

    try:
        from async_job_manager import AsyncJobManager

        manager = AsyncJobManager()
        print("✅ AsyncJobManager initialized successfully")

        # Check if Supabase is available
        if manager.supabase_client:
            print("✅ Supabase client available")

            # Check pending jobs
            try:
                pending_jobs = manager.get_pending_jobs()
                print(f"📊 Pending async jobs: {len(pending_jobs)}")

                if pending_jobs:
                    print("   Recent pending jobs:")
                    for job in pending_jobs[:3]:
                        print(f"   - ID: {job.id}, Request: {job.request_id}, Coach: {job.coach_username}")

            except Exception as e:
                print(f"⚠️ Could not retrieve pending jobs: {e}")
        else:
            print("❌ Supabase client not available")

        # Check webhook URL configuration
        webhook_url = os.getenv('OUTSCRAPER_WEBHOOK_URL')
        if webhook_url:
            print(f"✅ Webhook URL configured: {webhook_url}")
        else:
            print("❌ Webhook URL not configured")

        return True

    except ImportError as e:
        print(f"❌ Could not import AsyncJobManager: {e}")
        return False
    except Exception as e:
        print(f"❌ AsyncJobManager check failed: {e}")
        return False

def generate_webhook_config():
    """Generate webhook configuration recommendations"""
    print("\n🛠️ Webhook Configuration Recommendations:")
    print("=" * 60)

    webhook_url = os.getenv('OUTSCRAPER_WEBHOOK_URL')
    if not webhook_url:
        print("\n❌ MISSING: OUTSCRAPER_WEBHOOK_URL")
        print("Add to .streamlit/secrets.toml:")
        print('OUTSCRAPER_WEBHOOK_URL = "https://your-domain.com/webhook/outscraper/job-complete"')
        print("\nOptions for webhook hosting:")
        print("1. Deploy webhook service to cloud (Heroku, Railway, etc.)")
        print("2. Use ngrok for local development testing")
        print("3. Set up a dedicated webhook server")

    webhook_secret = os.getenv('OUTSCRAPER_WEBHOOK_SECRET')
    if not webhook_secret:
        print("\n⚠️ RECOMMENDED: OUTSCRAPER_WEBHOOK_SECRET")
        print("Add to .streamlit/secrets.toml:")
        print('OUTSCRAPER_WEBHOOK_SECRET = "your-random-secret-string"')
        print("This secures your webhook against unauthorized requests")

    print("\n📋 Complete webhook configuration example:")
    print("# Add to .streamlit/secrets.toml")
    print('OUTSCRAPER_WEBHOOK_URL = "https://your-webhook-domain.com/webhook/outscraper/job-complete"')
    print('OUTSCRAPER_WEBHOOK_SECRET = "random-secret-string-for-security"')
    print('WEBHOOK_PORT = "5000"  # Optional, defaults to 5000')

def main():
    """Run all webhook diagnostic tests"""
    print("🔍 Outscraper Webhook Configuration Diagnostic")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Check environment
    check_webhook_environment()

    # Check AsyncJobManager
    manager_ok = check_async_job_manager()

    # Test webhook endpoint
    if os.getenv('OUTSCRAPER_WEBHOOK_URL'):
        endpoint_ok = test_webhook_endpoint()

        if endpoint_ok:
            # Test with sample payload
            payload_ok = test_webhook_payload()
        else:
            payload_ok = False
    else:
        endpoint_ok = False
        payload_ok = False

    # Generate recommendations
    generate_webhook_config()

    # Summary
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSTIC SUMMARY:")
    print(f"   Environment: {'✅ OK' if os.getenv('OUTSCRAPER_WEBHOOK_URL') else '❌ MISSING'}")
    print(f"   AsyncJobManager: {'✅ OK' if manager_ok else '❌ FAILED'}")
    print(f"   Webhook Endpoint: {'✅ OK' if endpoint_ok else '❌ FAILED'}")
    print(f"   Payload Test: {'✅ OK' if payload_ok else '❌ FAILED'}")

    if all([os.getenv('OUTSCRAPER_WEBHOOK_URL'), manager_ok, endpoint_ok, payload_ok]):
        print("\n🎉 Webhook configuration is working correctly!")
        return True
    else:
        print("\n⚠️ Webhook configuration needs attention - see recommendations above")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)