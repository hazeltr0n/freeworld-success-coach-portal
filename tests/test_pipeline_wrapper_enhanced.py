import os
import sys
from unittest import mock
import pandas as pd

def import_wrapper():
    """Import pipeline_wrapper from parent directory"""
    base = os.path.abspath(os.path.dirname(__file__))
    root = os.path.abspath(os.path.join(base, '..'))
    if root not in sys.path:
        sys.path.insert(0, root)
    import pipeline_wrapper as pw
    return pw

def test_memory_only_short_circuits_subprocess():
    """Test that memory-only searches use direct Python calls, not subprocess"""
    pw = import_wrapper()
    wrapper = pw.StreamlitPipelineWrapper()

    # Mock the memory search method to return predictable results
    with mock.patch.object(wrapper, 'run_memory_only_search') as mock_memory_search:
        mock_memory_search.return_value = {
            'bypass_executed': True,
            'jobs_found': 15,
            'jobs_df': pd.DataFrame({'ai.match': ['good', 'so-so', 'bad'] * 5}),
            'bypass_type': 'MEMORY_ONLY',
            'files': {}
        }
        
        # Spy on subprocess.run to ensure it's NOT called for memory_only
        with mock.patch('subprocess.run') as subp:
            df, metadata = wrapper.run_pipeline({
                'location': 'Houston',
                'mode': 'sample',
                'memory_only': True,
            })
            
            # Verify memory search was called instead of subprocess
            mock_memory_search.assert_called_once()
            subp.assert_not_called()
            
            # Verify expected return format
            assert isinstance(df, pd.DataFrame)
            assert isinstance(metadata, dict)
            assert metadata.get('search_type') == 'memory_only'
            assert metadata.get('cost') == 0  # Memory-only has no cost


def test_force_fresh_flag_mapping():
    """Test that force_fresh parameter properly maps to --force-fresh CLI flag"""
    pw = import_wrapper()
    wrapper = pw.StreamlitPipelineWrapper()

    with mock.patch('subprocess.run') as subp:
        m = mock.Mock()
        m.returncode = 0
        m.stdout = 'Complete CSV: /tmp/test.csv\n'
        m.stderr = ''
        subp.return_value = m

        # Test force_fresh=True adds the flag (when not memory-only)
        df, meta = wrapper.run_pipeline({
            'location': 'Houston',
            'mode': 'sample',
            'force_fresh': True,
            'memory_only': False,
        })

        args = ' '.join(subp.call_args[0][0])
        assert '--force-fresh' in args
        
        # Test force_fresh is ignored for memory-only searches
        subp.reset_mock()
        with mock.patch.object(wrapper, 'run_memory_only_search') as mock_mem:
            mock_mem.return_value = {'bypass_executed': True, 'jobs_found': 0, 'jobs_df': pd.DataFrame()}
            
            df, meta = wrapper.run_pipeline({
                'location': 'Houston',
                'mode': 'sample', 
                'force_fresh': True,
                'memory_only': True,  # This should bypass subprocess entirely
            })
            
            # Should not call subprocess at all
            subp.assert_not_called()


def test_exact_location_vs_radius_mapping():
    """Test radius=0 maps to --exact-location flag, other values use --radius"""
    pw = import_wrapper()
    wrapper = pw.StreamlitPipelineWrapper()

    with mock.patch('subprocess.run') as subp:
        m = mock.Mock()
        m.returncode = 0
        m.stdout = 'Complete CSV: /tmp/test.csv\n'
        m.stderr = ''
        subp.return_value = m

        # Test radius=0 uses --exact-location
        df, meta = wrapper.run_pipeline({
            'location': 'Austin',
            'mode': 'test',
            'search_radius': 0,
        })

        args = ' '.join(subp.call_args[0][0])
        assert '--exact-location' in args
        assert '--radius' not in args

        # Test radius>0 uses --radius flag
        subp.reset_mock()
        df, meta = wrapper.run_pipeline({
            'location': 'Austin',
            'mode': 'test',
            'search_radius': 50,
        })

        args = ' '.join(subp.call_args[0][0])
        assert '--radius 50' in args
        assert '--exact-location' not in args


def test_multi_market_comma_separation():
    """Test multiple markets are passed as comma-separated values"""
    pw = import_wrapper()
    wrapper = pw.StreamlitPipelineWrapper()

    with mock.patch('subprocess.run') as subp:
        m = mock.Mock()
        m.returncode = 0
        m.stdout = 'Complete CSV: /tmp/test.csv\n'
        m.stderr = ''
        subp.return_value = m

        df, meta = wrapper.run_pipeline({
            'markets': ['Houston', 'Dallas', 'Phoenix'],
            'mode': 'test',
        })

        args = ' '.join(subp.call_args[0][0])
        assert '--market Houston,Dallas,Phoenix' in args


def test_search_terms_and_route_filter_mapping():
    """Test search terms and route filters are properly passed through"""
    pw = import_wrapper()
    wrapper = pw.StreamlitPipelineWrapper()

    with mock.patch('subprocess.run') as subp:
        m = mock.Mock()
        m.returncode = 0
        m.stdout = 'Complete CSV: /tmp/test.csv\n'
        m.stderr = ''
        subp.return_value = m

        df, meta = wrapper.run_pipeline({
            'location': 'Dallas',
            'mode': 'test',
            'search_terms': 'CDL driver, truck driver, delivery',
            'route_filter': 'local',
        })

        args = ' '.join(subp.call_args[0][0])
        assert '--terms CDL driver, truck driver, delivery' in args
        assert '--route local' in args


if __name__ == '__main__':
    print("🧪 Running pipeline wrapper tests...")
    
    test_memory_only_short_circuits_subprocess()
    print("✅ Memory-only subprocess bypass test passed")
    
    test_force_fresh_flag_mapping()
    print("✅ Force fresh flag mapping test passed")
    
    test_exact_location_vs_radius_mapping()
    print("✅ Exact location vs radius mapping test passed")
    
    test_multi_market_comma_separation()
    print("✅ Multi-market comma separation test passed")
    
    test_search_terms_and_route_filter_mapping()
    print("✅ Search terms and route filter mapping test passed")
    
    print("\n🎉 All pipeline wrapper tests passed!")