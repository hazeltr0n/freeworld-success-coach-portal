import os
import sys
from unittest import mock


def import_wrapper():
    # Prefer root-level pipeline_wrapper
    import pipeline_wrapper as pw  # type: ignore
    return pw


def test_memory_only_short_circuits_subprocess():
    pw = import_wrapper()
    wrapper = pw.StreamlitPipelineWrapper()

    # Spy on subprocess.run to ensure it's NOT called for memory_only
    with mock.patch('subprocess.run') as subp:
        df, meta = wrapper.run_pipeline({
            'location': 'Houston',
            'mode': 'sample',
            'memory_only': True,
        })
        assert meta.get('success') in (True, False)  # shape contract
        subp.assert_not_called()


def test_command_arguments_for_indeed_route():
    pw = import_wrapper()
    wrapper = pw.StreamlitPipelineWrapper()

    # Ensure the constructed command includes expected flags
    with mock.patch('subprocess.run') as subp:
        m = mock.Mock()
        m.returncode = 0
        m.stdout = 'Complete CSV: /tmp/out.csv\n'
        m.stderr = ''
        subp.return_value = m

        df, meta = wrapper.run_pipeline({
            'location': 'Dallas',
            'mode': 'test',
            'route_filter': 'local',
            'search_terms': 'CDL driver',
            'search_radius': 0,
            'search_sources': {'indeed': True, 'google': False},
        })

        # Validate the called args roughly
        args = ' '.join(subp.call_args[0][0])
        assert '--market Dallas' in args or '--market' in args
        assert '--mode test' in args
        assert '--route local' in args
        assert '--radius 0' in args and '--exact-location' in args
        assert '--sources indeed' in args
