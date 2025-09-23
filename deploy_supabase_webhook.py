#!/usr/bin/env python3
"""
Deploy the Outscraper webhook Supabase Edge Function
"""

import os
import subprocess
import sys
import time
import requests

def check_supabase_cli():
    """Check if Supabase CLI is installed"""
    try:
        result = subprocess.run(['supabase', '--version'], capture_output=True, text=True)
        print(f"✅ Supabase CLI installed: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ Supabase CLI not found")
        print("Install it with: npm install -g supabase")
        print("Or follow: https://supabase.com/docs/guides/cli")
        return False

def check_supabase_login():
    """Check if logged into Supabase"""
    try:
        result = subprocess.run(['supabase', 'projects', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Supabase CLI authenticated")
            return True
        else:
            print("❌ Not logged into Supabase")
            print("Login with: supabase login")
            return False
    except Exception as e:
        print(f"❌ Error checking Supabase auth: {e}")
        return False

def deploy_edge_function():
    """Deploy the outscraper-webhook edge function"""
    print("🚀 Deploying outscraper-webhook edge function...")

    try:
        # Deploy the function
        result = subprocess.run([
            'supabase', 'functions', 'deploy', 'outscraper-webhook'
        ], capture_output=True, text=True, cwd='.')

        if result.returncode == 0:
            print("✅ Edge function deployed successfully!")
            print(result.stdout)
            return True
        else:
            print("❌ Edge function deployment failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False

    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False

def test_deployed_function():
    """Test the deployed function"""
    print("\n🧪 Testing deployed function...")

    webhook_url = "https://yqbdltothngundojuebk.functions.supabase.co/outscraper-webhook?token=freeworld2024webhook"

    test_payload = {
        "id": f"test-deploy-{int(time.time())}",
        "user_id": "test-user-123",
        "status": "SUCCESS",
        "api_task": True,
        "results_location": f"https://api.outscraper.cloud/requests/test-deploy-{int(time.time())}",
        "quota_usage": [
            {
                "product_name": "Google Maps Data",
                "quantity": 1
            }
        ]
    }

    try:
        response = requests.post(webhook_url, json=test_payload, timeout=15)
        print(f"📬 Response: {response.status_code}")

        if response.status_code == 200:
            print("✅ Webhook function working correctly!")
            try:
                result = response.json()
                print(f"📄 Response: {result}")
            except:
                print(f"📄 Response text: {response.text}")
            return True
        elif response.status_code == 401:
            print("❌ Still getting 401 - token validation issue")
            return False
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def show_deployment_status():
    """Show current deployment status"""
    print("\n📋 Deployment Status:")
    print("=" * 50)

    # Check if function file exists
    function_file = "supabase/functions/outscraper-webhook/index.ts"
    if os.path.exists(function_file):
        print("✅ Edge function code created")
    else:
        print("❌ Edge function code missing")

    # Check current webhook status
    webhook_url = "https://yqbdltothngundojuebk.functions.supabase.co/outscraper-webhook?token=freeworld2024webhook"
    try:
        response = requests.get(webhook_url, timeout=5)
        if response.status_code == 405:  # Method not allowed for GET
            print("✅ Edge function deployed (405 expected for GET)")
        elif response.status_code == 401:
            print("⚠️ Edge function deployed but token validation failing")
        elif response.status_code == 404:
            print("❌ Edge function not deployed")
        else:
            print(f"🤔 Edge function status unclear: {response.status_code}")
    except:
        print("❌ Edge function not accessible")

def main():
    """Main deployment workflow"""
    print("🚀 Supabase Outscraper Webhook Deployment")
    print("=" * 50)

    # Show current status
    show_deployment_status()

    # Check prerequisites
    if not check_supabase_cli():
        return False

    if not check_supabase_login():
        return False

    # Deploy the function
    if deploy_edge_function():
        print("\n⏳ Waiting for function to be available...")
        time.sleep(10)  # Give it time to deploy

        # Test the deployed function
        if test_deployed_function():
            print("\n🎉 SUCCESS! Webhook is now working!")
            print("✅ Outscraper webhook failures should stop")
            return True
        else:
            print("\n⚠️ Function deployed but not working correctly")
            return False
    else:
        print("\n❌ Deployment failed")
        return False

if __name__ == '__main__':
    success = main()

    if success:
        print("\n📋 Next Steps:")
        print("1. Monitor Outscraper for webhook success")
        print("2. Test Google async batch submission")
        print("3. Verify job completion notifications")
    else:
        print("\n📋 Manual Steps:")
        print("1. Install Supabase CLI: npm install -g supabase")
        print("2. Login: supabase login")
        print("3. Deploy: supabase functions deploy outscraper-webhook")

    sys.exit(0 if success else 1)