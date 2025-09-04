import os
import pandas as pd

from jobs_schema import ensure_schema, sanctify_dataframe


def test_sanctify_fills_core_fields_and_flags(monkeypatch):
    # Minimal canonical-like DF missing key values
    df = pd.DataFrame([
        {
            'id.job': '',
            'source.title': 'Local CDL Driver',
            'source.company': 'Acme Logistics',
            'source.location_raw': 'Houston, TX',
            'ai.match': 'good',
            'meta.tracked_url': '',
            'source.indeed_url': 'https://indeed.com/viewjob?jk=abc',
        }
    ])

    df = ensure_schema(df)

    # Provide coach for sys.coach backfill
    monkeypatch.setenv('FREEWORLD_COACH_USERNAME', 'coach.james')

    out = sanctify_dataframe(df.copy())

    # id.job should be filled
    assert out.loc[0, 'id.job'] != ''

    # route flags for quality
    assert out.loc[0, 'route.ready_for_export'] is True
    assert str(out.loc[0, 'route.final_status']).startswith('included')
    assert out.loc[0, 'route.stage'] == 'exported'

    # tracked url fallback should be populated from indeed url
    assert out.loc[0, 'meta.tracked_url'] == 'https://indeed.com/viewjob?jk=abc'

    # sys metadata filled from env/schema
    assert out.loc[0, 'sys.version'] != ''
    assert out.loc[0, 'sys.coach'] == 'coach.james'

