#!/usr/bin/env python3
"""
Debug script to test agent portal locally with the failing config
"""
import base64
import json
import os
import sys

# Set up environment for local testing
os.environ['STREAMLIT_LOCAL'] = 'true'

def decode_agent_config(encoded_config):
    """Decode the base64 agent config"""
    try:
        decoded_bytes = base64.b64decode(encoded_config)
        decoded_str = decoded_bytes.decode('utf-8')
        return json.loads(decoded_str)
    except Exception as e:
        print(f"❌ Error decoding config: {e}")
        return None

def test_agent_portal():
    """Test the agent portal with the failing config"""

    # This is the failing config from the URL
    failing_config = 'eyJhZ2VudF91dWlkIjoiOGJmM2VkNWEtYWJmMC00MzI2LWI5NDUtNzc2NmY4N2E1ZDUyIiwiYWdlbnRfbmFtZSI6IkphY29iIiwibG9jYXRpb24iOiJJbmxhbmQgRW1waXJlIiwicm91dGVfdHlwZV9maWx0ZXIiOiJib3RoIiwiZmFpcl9jaGFuY2Vfb25seSI6ZmFsc2UsIm1heF9qb2JzIjoiQWxsIiwibWF0Y2hfcXVhbGl0eV9maWx0ZXIiOiJnb29kIGFuZCBzby1zbyIsImNvYWNoX3VzZXJuYW1lIjoiSmFtZXMgSGF6ZWx0b24iLCJzaG93X3ByZXBhcmVkX2ZvciI6dHJ1ZX0='

    print("🔍 Decoding failing agent config...")
    agent_params = decode_agent_config(failing_config)

    if not agent_params:
        print("❌ Failed to decode config")
        return

    print("✅ Decoded agent config:")
    for key, value in agent_params.items():
        print(f"   {key}: {value} ({type(value).__name__})")

    print("\n🎯 Testing agent portal generation...")

    # Import and test the agent portal function
    try:
        from agent_portal_clean import generate_agent_portal

        print("🔄 Calling generate_agent_portal...")
        html_result = generate_agent_portal(agent_params)

        print(f"✅ Agent portal returned HTML: {len(html_result)} characters")

        # Check if it contains error messages
        if "No Jobs Found" in html_result:
            print("❌ Agent portal returned 'No Jobs Found' error")
        elif "Clean Portal Error" in html_result:
            print("❌ Agent portal returned 'Clean Portal Error'")
        else:
            print("✅ Agent portal generated successfully")

        # Show first 200 chars of HTML
        print(f"\n📄 First 200 chars of HTML:")
        print(html_result[:200])

    except Exception as e:
        print(f"❌ Error testing agent portal: {e}")
        import traceback
        print(f"📍 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    print("🚀 Starting agent portal debug test")
    test_agent_portal()
    print("✅ Debug test complete")