import pandas as pd

from supabase_converter import supabase_to_canonical_df


def test_supabase_to_canonical_core_mapping():
    rows = [
        {
            'job_id': 'abc123',
            'job_title': 'CDL A Driver',
            'company': 'Acme Trucking',
            'location': 'Dallas, TX',
            'job_description': 'Drive local routes',
            'apply_url': 'https://indeed.com/viewjob?jk=abc',
            'salary': '$28/hr',
            'match_level': 'good',
            'match_reason': 'Local + No touch',
            'summary': 'Great local position',
            'route_type': 'Local',
            'market': 'Dallas',
            'search_query': 'CDL driver Dallas',
            'classification_source': 'supabase_memory',
            'created_at': '2025-08-30T10:00:00Z',
        }
    ]

    df = supabase_to_canonical_df(rows)

    # Must include critical canonical fields
    for col in [
        'id.job', 'source.title', 'source.company', 'source.location_raw',
        'ai.match', 'ai.summary', 'ai.route_type',
        'meta.market', 'meta.query', 'search.location',
        'sys.classification_source', 'sys.is_fresh_job']:
        assert col in df.columns, f"missing {col}"

    # Mapping basics
    r0 = df.iloc[0]
    assert r0['id.job'] == 'abc123'
    assert r0['source.title'] == 'CDL A Driver'
    assert r0['source.company'] == 'Acme Trucking'
    assert r0['source.location_raw'] == 'Dallas, TX'
    assert r0['ai.match'] == 'good'
    assert r0['ai.route_type'] == 'Local'
    assert r0['meta.market'] == 'Dallas'
    assert r0['sys.classification_source'] == 'supabase_memory'
    assert r0['sys.is_fresh_job'] is False

