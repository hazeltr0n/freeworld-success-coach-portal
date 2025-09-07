#!/usr/bin/env python3
"""
Local test of portal parameter encoding - bypassing Streamlit setup issues
"""

import sys
import os
import json
import base64

# Add current directory to path
sys.path.append('.')

def test_portal_encoding():
    """Test the portal encoding function locally"""
    print("🧪 TESTING PORTAL PARAMETER ENCODING LOCALLY")
    print("=" * 50)
    
    # Import our functions
    try:
        from free_agent_system import encode_agent_params
        print("✅ Successfully imported encode_agent_params")
    except Exception as e:
        print(f"❌ Failed to import encode_agent_params: {e}")
        return
    
    # Test with the EXACT same parameters that should be sent from PDF config
    test_params = {
        'agent_uuid': '86d13115-a216-4b51-9f2d-9b638d8e1437',
        'agent_name': 'Kyron Wilson-ayers', 
        'location': 'Las Vegas',
        'route_type_filter': ['Local'],  # This is what PDF multiselect sends
        'match_quality_filter': ['good', 'so-so'], # This is what PDF multiselect sends
        'fair_chance_only': False,
        'max_jobs': 50,
        'coach_username': 'James Hazelton'
    }
    
    print("\n📝 INPUT PARAMETERS:")
    print(json.dumps(test_params, indent=2))
    
    # Test encoding
    try:
        encoded = encode_agent_params(test_params)
        print(f"\n🔐 ENCODED URL PARAMETER:")
        print(encoded)
        
        # Test decoding
        decoded_json = base64.urlsafe_b64decode(encoded.encode()).decode()
        decoded_params = json.loads(decoded_json)
        
        print(f"\n🔓 DECODED PARAMETERS:")
        print(json.dumps(decoded_params, indent=2))
        
        # Validation
        print(f"\n✅ VALIDATION RESULTS:")
        
        success = True
        
        if 'route_type_filter' in decoded_params:
            print(f"✅ Has route_type_filter: {decoded_params['route_type_filter']}")
        else:
            print(f"❌ Missing route_type_filter")
            success = False
            
        if 'match_quality_filter' in decoded_params:
            print(f"✅ Has match_quality_filter: {decoded_params['match_quality_filter']}")
        else:
            print(f"❌ Missing match_quality_filter")
            success = False
            
        if 'route_filter' in decoded_params:
            print(f"⚠️ Still has old route_filter: {decoded_params['route_filter']}")
            success = False
        else:
            print(f"✅ No old route_filter parameter")
            
        if 'match_level' in decoded_params:
            print(f"⚠️ Still has old match_level: {decoded_params['match_level']}")  
            success = False
        else:
            print(f"✅ No old match_level parameter")
        
        # Generate test URL
        base_url = "http://localhost:8501"  # Local Streamlit
        portal_url = f"{base_url}/agent_job_feed?config={encoded}"
        
        print(f"\n🔗 LOCAL TEST URL:")
        print(portal_url)
        
        print(f"\n🌐 QA PORTAL URL:")
        qa_url = f"https://fwcareertest.streamlit.app/agent_job_feed?config={encoded}"
        print(qa_url)
        
        if success:
            print(f"\n🎉 ENCODING FUNCTION WORKS CORRECTLY!")
            print(f"If this URL doesn't work on QA portal, it's definitely a cache/deployment issue.")
        else:
            print(f"\n❌ ENCODING FUNCTION HAS ISSUES")
            
    except Exception as e:
        print(f"❌ Encoding failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_portal_encoding()