#!/usr/bin/env python3
"""
Test script to verify our encode_agent_params function works correctly
"""

import streamlit as st
import json
import base64
from free_agent_system import encode_agent_params

st.title("🧪 Portal Parameter Encoding Test")

st.write("### Testing encode_agent_params function")

# Test with PDF config data (this is what should be sent)
test_params = {
    'agent_uuid': '86d13115-a216-4b51-9f2d-9b638d8e1437',
    'agent_name': 'Kyron Wilson-ayers', 
    'location': 'Las Vegas',
    'route_type_filter': ['Local'],  # PDF config sends this as list
    'match_quality_filter': ['good', 'so-so'], # PDF config sends this as list
    'fair_chance_only': False,
    'max_jobs': 50,
    'coach_username': 'James Hazelton'
}

st.write("**Input parameters:**")
st.json(test_params)

# Test encoding
encoded = encode_agent_params(test_params)
st.write("**Encoded URL parameter:**")
st.code(encoded)

# Test decoding
try:
    decoded_json = base64.urlsafe_b64decode(encoded.encode()).decode()
    decoded_params = json.loads(decoded_json)
    
    st.write("**Decoded parameters:**")
    st.json(decoded_params)
    
    # Check for correct parameter names
    st.write("### ✅ Validation Results")
    
    if 'route_type_filter' in decoded_params:
        st.success(f"✅ Has route_type_filter: {decoded_params['route_type_filter']}")
    else:
        st.error("❌ Missing route_type_filter")
        
    if 'match_quality_filter' in decoded_params:
        st.success(f"✅ Has match_quality_filter: {decoded_params['match_quality_filter']}")
    else:
        st.error("❌ Missing match_quality_filter")
        
    if 'route_filter' in decoded_params:
        st.warning(f"⚠️ Still has old route_filter: {decoded_params['route_filter']}")
    else:
        st.success("✅ No old route_filter parameter")
        
    if 'match_level' in decoded_params:
        st.warning(f"⚠️ Still has old match_level: {decoded_params['match_level']}")
    else:
        st.success("✅ No old match_level parameter")
        
    # Generate test portal URL
    base_url = "https://fwcareertest.streamlit.app"
    portal_url = f"{base_url}/agent_job_feed?config={encoded}"
    
    st.write("### 🔗 Generated Portal URL")
    st.code(portal_url)
    
except Exception as e:
    st.error(f"Decoding error: {e}")