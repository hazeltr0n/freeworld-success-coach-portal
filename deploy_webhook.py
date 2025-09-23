#!/usr/bin/env python3
"""
Deploy and test Outscraper webhook service
Supports both local testing with ngrok and production deployment
"""

import os
import sys
import time
import subprocess
import requests
import json
import secrets
from datetime import datetime

def check_requirements():
    """Check if required dependencies are available"""
    print("🔍 Checking requirements...")

    required_modules = ['flask', 'toml']
    missing = []

    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            missing.append(module)
            print(f"❌ {module}")

    if missing:
        print(f"\n📦 Install missing dependencies:")
        print(f"pip install {' '.join(missing)}")
        return False

    return True

def generate_webhook_secret():
    """Generate a secure webhook secret"""
    return secrets.token_urlsafe(32)

def setup_ngrok_development():
    """Set up ngrok for local development testing"""
    print("\n🌐 Setting up ngrok for local development...")

    # Check if ngrok is installed
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        print(f"✅ ngrok installed: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ ngrok not found")
        print("Install ngrok from: https://ngrok.com/")
        print("Or use: brew install ngrok  # on macOS")
        return None

    # Start webhook service in background
    webhook_port = int(os.environ.get('WEBHOOK_PORT', 5000))
    print(f"🚀 Starting webhook service on port {webhook_port}...")

    try:
        # Start the webhook service
        webhook_process = subprocess.Popen([
            sys.executable, 'outscraper_webhook.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Give it time to start
        time.sleep(3)

        # Check if webhook is running
        try:
            response = requests.get(f'http://localhost:{webhook_port}/webhook/outscraper/health', timeout=5)
            if response.status_code == 200:
                print("✅ Webhook service started successfully")
            else:
                print(f"⚠️ Webhook service responding with status {response.status_code}")
        except:
            print("❌ Webhook service not responding")
            webhook_process.terminate()
            return None

        # Start ngrok tunnel
        print(f"🔗 Creating ngrok tunnel for port {webhook_port}...")
        ngrok_process = subprocess.Popen([
            'ngrok', 'http', str(webhook_port), '--log=stdout'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Give ngrok time to establish tunnel
        time.sleep(5)

        # Get the public URL from ngrok API
        try:
            ngrok_api = requests.get('http://localhost:4040/api/tunnels').json()
            public_url = ngrok_api['tunnels'][0]['public_url']
            webhook_url = f"{public_url}/webhook/outscraper/job-complete"

            print(f"🎉 Webhook URL: {webhook_url}")
            print(f"🔧 ngrok dashboard: http://localhost:4040")

            return {
                'webhook_url': webhook_url,
                'public_url': public_url,
                'webhook_process': webhook_process,
                'ngrok_process': ngrok_process
            }

        except Exception as e:
            print(f"❌ Failed to get ngrok URL: {e}")
            webhook_process.terminate()
            ngrok_process.terminate()
            return None

    except Exception as e:
        print(f"❌ Failed to start services: {e}")
        return None

def update_secrets_with_webhook(webhook_url, webhook_secret=None):
    """Update secrets.toml with webhook configuration"""
    print("\n📝 Updating secrets.toml with webhook configuration...")

    secrets_path = ".streamlit/secrets.toml"

    if not webhook_secret:
        webhook_secret = generate_webhook_secret()

    try:
        # Read existing secrets
        if os.path.exists(secrets_path):
            import toml
            secrets_data = toml.load(secrets_path)
        else:
            secrets_data = {}

        # Update webhook configuration
        secrets_data['OUTSCRAPER_WEBHOOK_URL'] = webhook_url
        secrets_data['OUTSCRAPER_WEBHOOK_SECRET'] = webhook_secret
        secrets_data['WEBHOOK_PORT'] = "5000"

        # Write back to file
        with open(secrets_path, 'w') as f:
            import toml
            toml.dump(secrets_data, f)

        print(f"✅ Updated {secrets_path}")
        print(f"   Webhook URL: {webhook_url}")
        print(f"   Webhook Secret: {webhook_secret[:8]}...")

        return True

    except Exception as e:
        print(f"❌ Failed to update secrets: {e}")
        return False

def test_webhook_integration(webhook_url, webhook_secret):
    """Test webhook integration with sample payload"""
    print("\n🧪 Testing webhook integration...")

    test_payload = {
        "id": f"test-{int(time.time())}",
        "status": "Success",
        "results_location": "https://api.outscraper.cloud/requests/test",
        "data": [{
            "title": "Test CDL Driver - Webhook Integration",
            "company_name": "Webhook Test Company",
            "location": "Houston, TX",
            "description": "Test job for webhook integration validation",
            "salary": "$55,000",
            "link": "https://jobs.google.com/test-webhook",
            "apply_options": [{"link": "https://test.com/apply"}],
            "detected_extensions": {"posted_at": "test"}
        }]
    }

    headers = {
        'Content-Type': 'application/json',
        'X-Webhook-Secret': webhook_secret
    }

    try:
        print(f"📤 Sending test payload to: {webhook_url}")
        response = requests.post(webhook_url, json=test_payload, headers=headers, timeout=30)

        if response.status_code == 200:
            print("✅ Webhook test successful!")
            try:
                result = response.json()
                print(f"   Message: {result.get('message', 'Success')}")
            except:
                print("   Response: OK")
            return True
        else:
            print(f"❌ Webhook test failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Webhook test error: {e}")
        return False

def create_production_deployment_guide():
    """Create a guide for production deployment"""
    guide_content = """# Outscraper Webhook Production Deployment Guide

## Option 1: Deploy to Railway

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login and create project:
   ```bash
   railway login
   railway init
   ```

3. Deploy webhook service:
   ```bash
   railway add
   railway deploy
   ```

4. Set environment variables in Railway dashboard:
   - OUTSCRAPER_API_KEY
   - OUTSCRAPER_WEBHOOK_SECRET
   - All other FreeWorld secrets

5. Get your webhook URL:
   ```
   https://your-app.railway.app/webhook/outscraper/job-complete
   ```

## Option 2: Deploy to Heroku

1. Create Heroku app:
   ```bash
   heroku create your-webhook-app
   ```

2. Set config vars:
   ```bash
   heroku config:set OUTSCRAPER_API_KEY=your-key
   heroku config:set OUTSCRAPER_WEBHOOK_SECRET=your-secret
   ```

3. Deploy:
   ```bash
   git push heroku main
   ```

4. Your webhook URL:
   ```
   https://your-webhook-app.herokuapp.com/webhook/outscraper/job-complete
   ```

## Option 3: Self-hosted VPS

1. Set up a VPS (DigitalOcean, Linode, etc.)
2. Install Python, nginx, and supervisor
3. Configure nginx to proxy to webhook service
4. Use supervisor to keep webhook service running
5. Set up SSL certificate (Let's Encrypt)

## Testing Webhook

After deployment, test your webhook:

```bash
python3 test_webhook_config.py
```

## Updating Configuration

Update your .streamlit/secrets.toml:

```toml
OUTSCRAPER_WEBHOOK_URL = "https://your-deployed-webhook.com/webhook/outscraper/job-complete"
OUTSCRAPER_WEBHOOK_SECRET = "your-production-secret"
```

## Monitoring

Monitor webhook health at:
- https://your-webhook-url/webhook/outscraper/health
- https://your-webhook-url/webhook/outscraper/status
"""

    with open('WEBHOOK_DEPLOYMENT_GUIDE.md', 'w') as f:
        f.write(guide_content)

    print("📋 Created WEBHOOK_DEPLOYMENT_GUIDE.md")

def main():
    """Main deployment workflow"""
    print("🚀 Outscraper Webhook Deployment Setup")
    print("=" * 50)

    # Check requirements
    if not check_requirements():
        return False

    print("\nChoose deployment option:")
    print("1. Local development with ngrok (recommended for testing)")
    print("2. Production deployment guide")
    print("3. Test existing webhook configuration")

    choice = input("\nEnter your choice (1-3): ").strip()

    if choice == '1':
        # Local development setup
        deployment = setup_ngrok_development()

        if deployment:
            webhook_url = deployment['webhook_url']
            webhook_secret = generate_webhook_secret()

            # Update secrets
            if update_secrets_with_webhook(webhook_url, webhook_secret):
                print("\n✅ Local webhook setup complete!")
                print(f"🔗 Webhook URL: {webhook_url}")
                print(f"🔧 ngrok dashboard: http://localhost:4040")

                # Test integration
                if test_webhook_integration(webhook_url, webhook_secret):
                    print("\n🎉 Webhook integration test passed!")
                    print("\nYour webhook is ready for testing async Google Jobs searches!")
                    print("Keep this terminal running to maintain the ngrok tunnel.")

                    try:
                        print("\nPress Ctrl+C to stop the webhook service...")
                        deployment['webhook_process'].wait()
                    except KeyboardInterrupt:
                        print("\n🛑 Stopping services...")
                        deployment['webhook_process'].terminate()
                        deployment['ngrok_process'].terminate()
                        print("✅ Services stopped")
                else:
                    print("\n❌ Webhook integration test failed")
                    return False
            else:
                return False
        else:
            return False

    elif choice == '2':
        # Production deployment guide
        create_production_deployment_guide()
        print("\n📋 Production deployment guide created!")
        print("See WEBHOOK_DEPLOYMENT_GUIDE.md for instructions")

        # Generate production webhook secret
        production_secret = generate_webhook_secret()
        print(f"\n🔐 Generated production webhook secret:")
        print(f"OUTSCRAPER_WEBHOOK_SECRET = \"{production_secret}\"")
        print("\nAdd this to your production secrets configuration")

    elif choice == '3':
        # Test existing configuration
        print("\n🧪 Testing existing webhook configuration...")
        os.system('python3 test_webhook_config.py')

    else:
        print("❌ Invalid choice")
        return False

    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)