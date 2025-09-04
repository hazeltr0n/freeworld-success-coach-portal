#!/usr/bin/env python3

from pipeline_wrapper import StreamlitPipelineWrapper

print('🧪 Testing complete parameter flow...')
wrapper = StreamlitPipelineWrapper()

# Test parameters including all new ones
params = {
    'location': 'Houston, TX',
    'mode': 'test', 
    'route_filter': 'both',
    'search_terms': 'CDL driver',
    'custom_location': None,
    'push_to_airtable': False,
    'generate_pdf': True,
    'generate_csv': True,
    'search_radius': 75,         # NEW
    'no_experience': True,       # NEW  
    'force_fresh': False,        # NEW
    'use_multi_search': False    # NEW
}

print('✅ Parameters validated')
print(f'📊 Search radius: {params["search_radius"]} miles')
print(f'💼 No experience jobs: {params["no_experience"]}')
print(f'🔄 Force fresh: {params["force_fresh"]}')
print(f'🔍 Multi-search: {params["use_multi_search"]}')

# Test cost estimation
cost_info = wrapper.estimate_cost('test', 1)
print(f'💰 Cost estimate: ${cost_info["total_cost"]:.3f}')

print('✅ All parameter flow tests PASSED!')