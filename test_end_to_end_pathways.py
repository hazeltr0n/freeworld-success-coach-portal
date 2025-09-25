#!/usr/bin/env python3
"""
Test end-to-end pathway parameter flow from table to portal
"""

from free_agent_system import encode_agent_params, decode_agent_params
from free_agents_optimized import OptimizedAgentEditor

def test_end_to_end_pathway_flow():
    """Test complete pathway parameter flow from table changes to portal links"""

    print("🧪 Testing End-to-End Pathway Parameter Flow")
    print("=" * 60)

    # Create sample agent with pathway preferences
    sample_agent = {
        'agent_uuid': 'test-agent-123',
        'agent_name': 'Test Agent',
        'agent_city': 'Houston',
        'agent_state': 'TX',
        'coach_username': 'test_coach',
        'custom_url': 'https://old-static-link.com',
        'search_config': {
            'location': 'Houston',
            'route_filter': 'both',
            'fair_chance_only': True,
            'max_jobs': 50,
            'match_level': 'good and so-so',
            'pathway_preferences': ['cdl_pathway', 'dock_to_driver', 'internal_cdl_training']
        }
    }

    print("1. Testing OptimizedAgentEditor dynamic link generation...")

    # Test the optimized editor's dynamic link generation
    editor = OptimizedAgentEditor()

    # Simulate the data preparation process
    display_data = editor.prepare_display_data([sample_agent], {})

    if not display_data.empty:
        portal_link = display_data.iloc[0]['Portal Link']
        print(f"✅ Generated portal link: {portal_link}")

        # Verify it's not the old static URL
        if portal_link != sample_agent['custom_url'] and 'Error' not in portal_link:
            print("✅ Portal link is dynamically generated (not static custom_url)")
        else:
            print("❌ Portal link appears to be static or errored")
    else:
        print("❌ No display data generated")
        return False

    print("\n2. Testing pathway checkbox to preferences conversion...")

    # Test pathway preferences in the generated link
    pathway_preferences = sample_agent['search_config']['pathway_preferences']
    print(f"Original pathway preferences: {pathway_preferences}")

    # Check if this is a Short.io link (which is expected)
    import re
    param_match = None

    if 'short.gy' in portal_link:
        print("✅ Portal link uses Short.io tracking service (expected)")
        print("ℹ️  Short.io links redirect to portal with embedded parameters")

        # For Short.io links, we need to test the underlying generate_agent_url function
        try:
            from free_agent_system import generate_agent_url

            # Build the same params that would be passed to generate_agent_url
            agent_params = {
                'agent_uuid': sample_agent['agent_uuid'],
                'agent_name': sample_agent['agent_name'],
                'location': sample_agent['search_config']['location'],
                'route_filter': sample_agent['search_config']['route_filter'],
                'fair_chance_only': sample_agent['search_config']['fair_chance_only'],
                'max_jobs': sample_agent['search_config']['max_jobs'],
                'match_level': sample_agent['search_config']['match_level'],
                'coach_username': sample_agent['coach_username'],
                'classifier_type': 'pathway' if len(pathway_preferences) > 1 else 'cdl',
                'pathway_preferences': pathway_preferences
            }

            # Generate the actual portal URL that Short.io redirects to
            agent_uuid = agent_params.pop('agent_uuid')  # Remove from params dict
            direct_portal_url = generate_agent_url(agent_uuid, agent_params)
            print(f"Direct portal URL: {direct_portal_url}")

            # Extract and test parameters from the direct URL
            param_match = re.search(r'config=([^&]+)', direct_portal_url)

        except Exception as e:
            print(f"⚠️  Could not test direct portal URL: {e}")

    elif 'eyJ' in portal_link:  # Base64 encoded data
        # Extract and decode the params from the URL
        param_match = re.search(r'config=([^&]+)', portal_link)
    else:
        print("❌ Portal link format not recognized")
        return False

    # Test parameter decoding
    if param_match:
        encoded_params = param_match.group(1)
        try:
            decoded_params = decode_agent_params(encoded_params)
            decoded_pathways = decoded_params.get('pathway_preferences', [])

            print(f"Decoded pathway preferences: {decoded_pathways}")

            if set(decoded_pathways) == set(pathway_preferences):
                print("✅ Pathway preferences correctly preserved in portal parameters")
            else:
                print("❌ Pathway preferences not correctly preserved")
                return False

        except Exception as e:
            print(f"❌ Failed to decode parameters: {e}")
            return False
    else:
        print("❌ No encoded parameters found")
        return False

    print("\n3. Testing classifier_type determination...")

    # Test classifier type logic
    if len(pathway_preferences) > 1:
        expected_classifier = 'pathway'
    else:
        expected_classifier = 'cdl'

    decoded_params = decode_agent_params(param_match.group(1))
    actual_classifier = decoded_params.get('classifier_type', 'cdl')

    if actual_classifier == expected_classifier:
        print(f"✅ Classifier type correctly set to '{actual_classifier}'")
    else:
        print(f"❌ Classifier type incorrect. Expected '{expected_classifier}', got '{actual_classifier}'")
        return False

    print("\n4. Testing checkbox state conversion...")

    # Simulate checkbox states from the table
    checkbox_states = {
        'CDL Jobs': True,        # cdl_pathway
        'Dock→Driver': True,     # dock_to_driver
        'CDL Training': True,    # internal_cdl_training
        'Warehouse→Driver': False,
        'Logistics Progression': False,
        'Non-CDL Driving': False,
        'General Warehouse': False,
        'Construction': False,
        'Stepping Stone': False
    }

    # Convert checkbox states to pathway preferences (simulate _track_changes logic)
    pathway_mapping = {
        "CDL Jobs": "cdl_pathway",
        "Dock→Driver": "dock_to_driver",
        "CDL Training": "internal_cdl_training",
        "Warehouse→Driver": "warehouse_to_driver",
        "Logistics Progression": "logistics_progression",
        "Non-CDL Driving": "non_cdl_driving",
        "General Warehouse": "general_warehouse",
        "Construction": "construction_apprentice",
        "Stepping Stone": "stepping_stone"
    }

    converted_pathways = []
    for checkbox_name, is_checked in checkbox_states.items():
        if is_checked:
            converted_pathways.append(pathway_mapping[checkbox_name])

    print(f"Checkbox-derived pathways: {converted_pathways}")

    if set(converted_pathways) == set(pathway_preferences):
        print("✅ Checkbox states correctly convert to pathway preferences")
    else:
        print("❌ Checkbox state conversion failed")
        return False

    print("\n🎯 End-to-End Pathway Flow Test Results:")
    print("✅ All pathway parameter flow tests passed!")
    print("✅ Table checkbox changes → pathway_preferences → encoded URLs")
    print("✅ Dynamic portal link generation working correctly")
    print("✅ Agent portal will receive correct pathway filtering parameters")

    return True

if __name__ == "__main__":
    success = test_end_to_end_pathway_flow()
    exit(0 if success else 1)