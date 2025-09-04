import types
import pandas as pd

import pipeline_v3 as pv3


def test_generate_pdf_calls_generator_monkeypatched(tmp_path, monkeypatch):
    # Build a minimal exportable DF from canonical fields
    df = pd.DataFrame([
        {
            'id.job': 'abc123',
            'source.title': 'CDL A Driver',
            'source.company': 'Acme',
            'source.location_raw': 'Houston, TX',
            'ai.summary': 'Local driving',
            'ai.match': 'good',
            'ai.route_type': 'Local',
            'source.indeed_url': 'https://indeed.com/viewjob?jk=abc',
        }
    ])

    # Capture calls to generate_fpdf_job_cards
    called = {}

    def fake_gen(df_in, path, market, coach_name, coach_username, candidate_name, candidate_id):
        called['path'] = path
        called['market'] = market
        called['rows'] = len(df_in)
        # Do not write a file; just capture args
        return None

    # Monkeypatch the symbol in the pipeline module
    monkeypatch.setenv('FREEWORLD_COACH_NAME', 'Coach J')
    monkeypatch.setenv('FREEWORLD_COACH_USERNAME', 'coach.j')
    monkeypatch.setenv('FREEWORLD_CANDIDATE_NAME', 'John Doe')
    monkeypatch.setenv('FREEWORLD_CANDIDATE_ID', 'uuid-123')
    monkeypatch.setattr(pv3, 'generate_fpdf_job_cards', fake_gen, raising=True)

    pipe = pv3.FreeWorldPipelineV3()
    # Force output dir to tmp
    pipe.output_dir = str(tmp_path)

    out = pipe._generate_pdf(df, market='Houston', custom_location='')

    # Path should be constructed and fake generator should be called
    assert 'market' in called and called['market'] == 'Houston'
    assert 'rows' in called and called['rows'] == 1

