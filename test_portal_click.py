#!/usr/bin/env python3
"""
Test portal click tracking specifically
"""

import requests
import json

# Test portal click payload (simulates clicking a free agent portal link)
WEBHOOK_URL = "https://yqbdltothngundojuebk.functions.supabase.co/shortio-clicks"
PORTAL_PAYLOAD = {
    "link": {
        "idString": "portal123",
        "shortURL": "https://freeworldjobs.short.gy/portal123", 
        "originalURL": "https://fwcareercoach.streamlit.app/agent_job_feed?agent=test-agent-uuid&config=abc123",
        "tags": [
            "coach:test_coach",
            "candidate:test-agent-uuid",  # This is the key!
            "agent:Test-Agent-Portal",
            "market:Houston", 
            "type:portal_access"
        ]
    },
    "referrer": "https://linkedin.com",
    "country": "US",
    "userAgent": "Portal-Test/1.0"
}

def test_portal_click():
    """Test portal click webhook"""
    print("🏠 TESTING PORTAL CLICK")
    print("=" * 50)
    print(f"Webhook URL: {WEBHOOK_URL}")
    print(f"Payload: {json.dumps(PORTAL_PAYLOAD, indent=2)}")
    print()
    
    try:
        response = requests.post(
            WEBHOOK_URL, 
            json=PORTAL_PAYLOAD, 
            timeout=15,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"\n✅ Success: {response_data.get('success')}")
                print(f"🏠 Click type: {response_data.get('click_type')}")
                print(f"👤 Candidate ID: {response_data.get('candidate_id')}")
                print(f"👨‍🏫 Coach: {response_data.get('coach')}")
                print(f"📝 Message: {response_data.get('message')}")
                
                if response_data.get('click_type') == 'portal':
                    print("\n🎉 PORTAL CLICK DETECTED AND PROCESSED!")
                    print("   Check agent_profiles table for updated portal_clicks count")
                else:
                    print(f"\n⚠️  Expected portal click, got: {response_data.get('click_type')}")
                    
            except json.JSONDecodeError:
                print("⚠️  Response not JSON")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_portal_click()