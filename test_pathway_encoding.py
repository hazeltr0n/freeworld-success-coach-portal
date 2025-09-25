#!/usr/bin/env python3
"""
Test pathway parameter encoding in portal links
"""

from free_agent_system import encode_agent_params, decode_agent_params

def test_pathway_encoding():
    """Test that pathway preferences are properly encoded in portal links"""

    print("🧪 Testing Pathway Parameter Encoding")
    print("=" * 50)

    # Test data with pathway preferences
    test_agent_data = {
        'agent_uuid': 'test-uuid-123',
        'agent_name': 'Test Agent',
        'location': 'Houston',
        'route_filter': 'both',
        'fair_chance_only': True,
        'max_jobs': 50,
        'match_level': 'good and so-so',
        'coach_username': 'test_coach',
        'classifier_type': 'pathway',
        'pathway_preferences': ['cdl_pathway', 'dock_to_driver', 'internal_cdl_training']
    }

    print("Original data:")
    for key, value in test_agent_data.items():
        print(f"  {key}: {value}")

    # Encode parameters
    encoded = encode_agent_params(test_agent_data)
    print(f"\nEncoded string: {encoded}")

    # Decode parameters
    decoded = decode_agent_params(encoded)
    print(f"\nDecoded data:")
    for key, value in decoded.items():
        print(f"  {key}: {value}")

    # Verify pathway preferences are preserved
    original_pathways = test_agent_data.get('pathway_preferences', [])
    decoded_pathways = decoded.get('pathway_preferences', [])

    if original_pathways == decoded_pathways:
        print(f"\n✅ Pathway preferences correctly preserved: {decoded_pathways}")
    else:
        print(f"\n❌ Pathway preferences not preserved:")
        print(f"   Original: {original_pathways}")
        print(f"   Decoded: {decoded_pathways}")

    # Check all required fields
    required_fields = ['classifier_type', 'pathway_preferences']
    missing_fields = [field for field in required_fields if field not in decoded]

    if not missing_fields:
        print("✅ All required fields present in decoded data")
    else:
        print(f"❌ Missing fields: {missing_fields}")

    # Test empty pathways
    print("\n" + "=" * 50)
    print("Testing empty pathway preferences...")

    empty_pathways_data = test_agent_data.copy()
    empty_pathways_data['pathway_preferences'] = []

    encoded_empty = encode_agent_params(empty_pathways_data)
    decoded_empty = decode_agent_params(encoded_empty)

    if decoded_empty.get('pathway_preferences') == []:
        print("✅ Empty pathway preferences correctly handled")
    else:
        print(f"❌ Empty pathway preferences issue: {decoded_empty.get('pathway_preferences')}")

    print("\n🎯 Pathway encoding test complete!")

if __name__ == "__main__":
    test_pathway_encoding()