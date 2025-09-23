#!/usr/bin/env python3
"""
Fix Supabase Edge Function authentication issue
"""

import requests
import json
import os
import subprocess

def test_with_supabase_headers():
    """Test with Supabase API headers"""
    print("🔑 Testing with Supabase authentication headers...")

    webhook_url = "https://yqbdltothngundojuebk.functions.supabase.co/outscraper-webhook?token=freeworld2024webhook"

    # Try to get Supabase keys from environment
    supabase_url = os.getenv('SUPABASE_URL', 'https://yqbdltothngundojuebk.supabase.co')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    print(f"🔍 Supabase URL: {supabase_url}")
    print(f"🔍 Anon key available: {'YES' if supabase_anon_key else 'NO'}")
    print(f"🔍 Service key available: {'YES' if supabase_service_key else 'NO'}")

    test_payload = {
        "id": "test-auth-fix",
        "status": "SUCCESS",
        "user_id": "test-user"
    }

    # Test 1: With anon key
    if supabase_anon_key:
        print(f"\n🧪 Test 1: With anon key")
        headers = {
            'Authorization': f'Bearer {supabase_anon_key}',
            'apikey': supabase_anon_key,
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(webhook_url, json=test_payload, headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   Error: {e}")

    # Test 2: With service role key
    if supabase_service_key:
        print(f"\n🧪 Test 2: With service role key")
        headers = {
            'Authorization': f'Bearer {supabase_service_key}',
            'apikey': supabase_service_key,
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(webhook_url, json=test_payload, headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   Error: {e}")

    # Test 3: Direct function invoke (if available)
    print(f"\n🧪 Test 3: Using supabase CLI invoke")
    try:
        invoke_result = subprocess.run([
            'supabase', 'functions', 'invoke', 'outscraper-webhook',
            '--data', json.dumps(test_payload),
            '--query', 'token=freeworld2024webhook'
        ], capture_output=True, text=True, timeout=30)

        print(f"   Return code: {invoke_result.returncode}")
        print(f"   Stdout: {invoke_result.stdout}")
        print(f"   Stderr: {invoke_result.stderr}")

    except Exception as e:
        print(f"   Error: {e}")

def check_function_config():
    """Check function configuration"""
    print(f"\n⚙️ Checking function configuration...")

    # Check if there's a verify JWT setting
    config_file = "supabase/config.toml"
    if os.path.exists(config_file):
        print(f"✅ Found {config_file}")
        try:
            with open(config_file, 'r') as f:
                content = f.read()
                if 'verify_jwt' in content:
                    print("🔍 JWT verification settings found in config")
                    # Extract relevant lines
                    lines = content.split('\n')
                    for line in lines:
                        if 'verify_jwt' in line or 'auth' in line.lower():
                            print(f"   {line}")
                else:
                    print("⚠️ No JWT verification settings in config")
        except Exception as e:
            print(f"❌ Error reading config: {e}")
    else:
        print(f"❌ No {config_file} found")

def suggest_fixes():
    """Suggest potential fixes"""
    print(f"\n💡 Potential Fixes:")
    print("=" * 50)

    print("1. **Make Function Public (Recommended for Webhooks)**:")
    print("   Add to supabase/config.toml:")
    print("   ```toml")
    print("   [functions.outscraper-webhook]")
    print("   verify_jwt = false")
    print("   ```")

    print("\n2. **Update Function to Handle Supabase Auth**:")
    print("   Modify function to accept Supabase API key in headers")

    print("\n3. **Use Different Webhook Approach**:")
    print("   - Deploy to Vercel/Netlify with public endpoint")
    print("   - Use the Flask webhook service we created")

    print("\n4. **Check Supabase Dashboard**:")
    print("   - Verify function is set to allow anonymous access")
    print("   - Check function logs for detailed errors")

def create_public_config():
    """Create or update config to make function public"""
    print(f"\n🔧 Creating public function configuration...")

    config_file = "supabase/config.toml"

    # Read existing config
    config_content = ""
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config_content = f.read()

    # Check if outscraper-webhook config exists
    if '[functions.outscraper-webhook]' not in config_content:
        print("➕ Adding outscraper-webhook function config...")

        # Append the function config
        webhook_config = """

# Outscraper Webhook Configuration
[functions.outscraper-webhook]
verify_jwt = false  # Allow public access for webhook
"""

        with open(config_file, 'a') as f:
            f.write(webhook_config)

        print(f"✅ Added public configuration to {config_file}")
        print("🚀 Redeploy with: supabase functions deploy outscraper-webhook")
        return True
    else:
        print("✅ Function config already exists")
        return False

def main():
    """Run authentication fix workflow"""
    print("🔧 Supabase Edge Function Authentication Fix")
    print("=" * 60)

    # Load secrets if available
    try:
        import toml
        secrets_path = ".streamlit/secrets.toml"
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            for key, value in secrets.items():
                os.environ[key] = str(value)
    except:
        pass

    # Test current authentication
    test_with_supabase_headers()

    # Check function configuration
    check_function_config()

    # Suggest fixes
    suggest_fixes()

    # Offer to create public config
    create_public = input("\n❓ Create public function configuration? (y/n): ").lower().strip()
    if create_public == 'y':
        if create_public_config():
            print("\n📋 Next Steps:")
            print("1. Run: supabase functions deploy outscraper-webhook")
            print("2. Test webhook again")
            print("3. Monitor Outscraper for successful webhook calls")

if __name__ == '__main__':
    main()