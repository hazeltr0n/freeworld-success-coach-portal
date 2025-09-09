"""
Ultra-Simple Pipeline Wrapper - Direct calls to parent scripts
No imports, no complex paths, just works.
"""

import os
import io
import subprocess
from typing import Dict, List, Tuple, Any

# Ensure pandas is always available
try:
    import pandas as pd
except ImportError:
    # Fallback for deployment issues
    pd = None

# Simple market list
MARKETS = [
    "Houston", "Dallas", "Bay Area", "Stockton", "Denver",
    "Las Vegas", "Newark", "Phoenix", "Trenton", "Inland Empire"
]

# Market to location mappings - ONLY for Indeed scraper (city, state format)
MARKET_TO_LOCATION_MAP = {
    "Houston": "Houston, TX",
    "Dallas": "Dallas, TX", 
    "Bay Area": "Berkeley, CA",  # Representative city for Bay Area
    "Stockton": "Stockton, CA",
    "Denver": "Denver, CO",
    "Las Vegas": "Las Vegas, NV",
    "Newark": "Newark, NJ",
    "Phoenix": "Phoenix, AZ",
    "Trenton": "Trenton, NJ",
    "Inland Empire": "Ontario, CA",  # Representative city for Inland Empire
    "San Antonio": "San Antonio, TX",
    "Austin": "Austin, TX"
}

class StreamlitPipelineWrapper:
    """Ultra-simple wrapper - just calls the working terminal script"""
    
    def __init__(self):
        self.available_markets = MARKETS
        
        # For Streamlit Cloud: everything is in the same directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.terminal_script = os.path.join(current_dir, 'terminal_job_search.py')
        
        # If terminal script not in current dir, try parent (local development)
        if not os.path.exists(self.terminal_script):
            parent_dir = os.path.dirname(current_dir)
            self.terminal_script = os.path.join(parent_dir, 'terminal_job_search.py')
            self.parent_dir = parent_dir
        else:
            self.parent_dir = current_dir
        
        # Verify paths exist
        print(f"🔍 Wrapper Debug:")
        print(f"  Current dir: {current_dir}")
        print(f"  Working dir: {self.parent_dir}")
        print(f"  Terminal script: {self.terminal_script}")
        print(f"  Script exists: {os.path.exists(self.terminal_script)}")
    
    def get_markets(self) -> List[str]:
        return self.available_markets
    
    def get_market_location(self, market: str) -> str:
        # UI display should use the market name only (no ", ST").
        # Conversion to "City, ST" happens only inside the pipeline when
        # constructing Outscraper/Indeed query URLs.
        return market
    
    def estimate_cost(self, mode: str, num_locations: int = 1) -> Dict[str, float]:
        costs = {"test": 0.013, "mini": 0.065, "sample": 0.13, "medium": 0.33, "large": 0.65, "full": 1.30}
        job_limits = {"test": 100, "mini": 50, "sample": 100, "medium": 250, "large": 500, "full": 1000}
        cost = costs.get(mode, 0.13)
        job_limit = job_limits.get(mode, 100)
        return {
            "cost_per_location": cost, 
            "total_cost": cost * num_locations, 
            "num_locations": num_locations,
            "job_limit": job_limit
        }
    
    def run_complete_pipeline(
        self,
        location: str,
        search_terms: str = "CDL Driver No Experience",
        radius: int = 50,
        max_jobs: int = 100,
        match_quality_filter: List[str] = None,
        fair_chance_only: bool = False,
        route_type_filter: List[str] = None,
        experience_level_filter: str = 'Any',
        coach_username: str = None,
        generate_pdf: bool = True,
        generate_csv: bool = True,
        force_memory_only: bool = False,
        mode_info: Dict = None
    ) -> Dict[str, Any]:
        """Complete pipeline with force_memory_only support - calls pipeline_v3 directly"""
        try:
            # Import pipeline v3 for direct method call
            from pipeline_v3 import FreeWorldPipelineV3
            
            # Initialize pipeline if not already done
            if not hasattr(self, 'pipeline_v3') or self.pipeline_v3 is None:
                self.pipeline_v3 = FreeWorldPipelineV3()
            
            # Call pipeline v3 complete pipeline directly
            results = self.pipeline_v3.run_complete_pipeline(
                location=location,
                search_terms=search_terms,
                radius=radius,
                max_jobs=max_jobs,
                match_quality_filter=match_quality_filter,
                fair_chance_only=fair_chance_only,
                route_type_filter=route_type_filter,
                experience_level_filter=experience_level_filter,
                coach_username=coach_username,
                generate_pdf=generate_pdf,
                generate_csv=generate_csv,
                force_memory_only=force_memory_only,
                mode_info=mode_info or {'mode': 'sample', 'limit': max_jobs}
            )
            
            return results
            
        except Exception as e:
            print(f"❌ Complete pipeline error: {str(e)}")
            return {
                'bypass_executed': False,
                'bypass_type': 'FAILED',
                'reason': f'Pipeline error: {str(e)}',
                'jobs_found': 0,
                'jobs_df': None
            }

    # REMOVED: Redundant run_memory_only_search method
    # Now using direct pipeline_v3 calls in _run_memory_only_pipeline method
    
    def _run_memory_only_pipeline(self, params: Dict) -> Tuple[Any, Dict]:
        """Memory-only pipeline using direct Python calls with multi-market support"""
        try:
            def _load_recent_market_csvs(markets: List[str], minutes: int = 1440) -> Any:
                """Best-effort CSV fallback: aggregate recent CSVs for the given markets.
                Looks in FreeWorld_Jobs folder for complete/export CSVs and merges them.
                """
                import glob, time
                out_dir = os.path.join(self.parent_dir, 'FreeWorld_Jobs')
                if not os.path.isdir(out_dir):
                    return pd.DataFrame()
                cutoff = time.time() - (minutes * 60)
                patterns = [
                    os.path.join(out_dir, '*_complete_jobs_*.csv'),     # market slug exports
                    os.path.join(out_dir, 'complete_jobs_*.csv'),        # legacy naming
                    os.path.join(out_dir, 'FreeWorld_Jobs_*_*.csv'),     # per-market CSVs
                    os.path.join(out_dir, '*_quality_jobs_*.csv'),       # quality-only
                    os.path.join(out_dir, '**', '*.csv'),                # any CSV
                ]
                candidates: List[str] = []
                for pat in patterns:
                    for pth in glob.glob(pat, recursive=True):
                        try:
                            if os.path.getmtime(pth) >= cutoff:
                                candidates.append(pth)
                        except Exception:
                            pass
                # Filter by requested markets if provided (match on filename token)
                if markets:
                    m_lower = [m.lower().replace(' ', '_') for m in markets]
                    def _match_market(p: str) -> bool:
                        name = os.path.basename(p).lower()
                        return any(tok in name for tok in m_lower)
                    candidates = [p for p in candidates if _match_market(p)] or candidates
                # Load
                dfs = []
                for p in sorted(set(candidates)):
                    try:
                        dfs.append(pd.read_csv(p))
                    except Exception:
                        pass
                if not dfs:
                    return pd.DataFrame()
                df = pd.concat(dfs, ignore_index=True)
                # Light ordering if canonical fields present
                try:
                    if 'ai.match' in df.columns:
                        order = {'good': 0, 'so-so': 1, 'bad': 2}
                        df['_q'] = df['ai.match'].map(order).fillna(3)
                        if 'sys.scraped_at' in df.columns:
                            df = df.sort_values(['_q', 'sys.scraped_at'], ascending=[True, False])
                        else:
                            df = df.sort_values(['_q'], ascending=[True])
                        df.drop(columns=['_q'], inplace=True, errors='ignore')
                except Exception:
                    pass
                return df
            # Determine all locations to search (markets or a single custom location)
            markets = params.get('markets') or []
            custom_location = params.get('custom_location')
            base_location = params.get('location')

            if custom_location:
                locations_to_run = [custom_location]
            elif isinstance(markets, (list, tuple)) and len(markets) > 0:
                locations_to_run = list(markets)
            elif base_location:
                locations_to_run = [base_location]
            else:
                locations_to_run = ['Houston']

            # Map search mode to max_jobs
            mode = params.get('mode', 'sample')
            max_jobs_map = {'test': 25, 'mini': 50, 'sample': 100, 'medium': 250, 'large': 500, 'full': 1000}
            max_jobs = params.get('max_jobs', max_jobs_map.get(mode, 100))

            combined_df = pd.DataFrame() if pd else None
            combined_quality = 0
            files = {}
            
            # Track metrics across all locations
            all_results_metrics = []

            # Initialize pipeline v3 for direct calls
            from pipeline_v3 import FreeWorldPipelineV3
            if not hasattr(self, 'pipeline_v3') or self.pipeline_v3 is None:
                self.pipeline_v3 = FreeWorldPipelineV3()
            
            for loc in locations_to_run:
                # Call pipeline_v3 memory-only search directly with Free Agent parameters
                results = self.pipeline_v3.run_memory_only_search(
                    location=loc,
                    search_terms=params.get('search_terms', 'CDL Driver No Experience'),
                    radius=params.get('search_radius', 50),
                    max_jobs=max_jobs,
                    match_quality_filter=params.get('match_quality_filter'),
                    fair_chance_only=params.get('fair_chance_only', False),
                    route_type_filter=params.get('route_type_filter'),
                    experience_level_filter=params.get('experience_level_filter', 'Any'),
                    coach_username=params.get('coach_username', ''),
                    generate_pdf=params.get('generate_pdf', False),  # Enable PDF if requested
                    generate_csv=params.get('generate_csv', False),
                    hours=params.get('memory_hours', 72),
                    text_search=params.get('text_search', False),
                    # NUCLEAR FIX: Pass Free Agent parameters directly to pipeline_v3
                    candidate_name=params.get('candidate_name', ''),
                    candidate_id=params.get('candidate_id', ''),
                    force_link_generation=params.get('force_link_generation', False),
                    show_prepared_for=params.get('show_prepared_for', True)
                )

                df_part = results.get('jobs_df')
                if df_part is not None and not df_part.empty:
                    combined_df = df_part if combined_df.empty else pd.concat([combined_df, df_part], ignore_index=True)
                    try:
                        combined_quality += int((df_part['ai.match'].isin(['good', 'so-so'])).sum())
                    except Exception:
                        combined_quality += len(df_part)
                
                # Collect PDF files from results
                result_files = results.get('files', {})
                if result_files.get('pdf'):
                    files['pdf'] = result_files['pdf']
                
                # Collect metrics from each location result
                all_results_metrics.append(results)

            if combined_df is None:
                combined_df = pd.DataFrame() if pd else None

            # CSV fallback only if absolutely no jobs returned
            if combined_df.empty:
                try:
                    combined_df = _load_recent_market_csvs(locations_to_run, minutes=max(60, int(params.get('memory_hours', 72)) * 60 // 60))
                except Exception:
                    pass

            # Extract efficiency metrics from collected pipeline results
            memory_efficiency = 100.0  # Default for memory search
            total_cost = 0.0
            cost_per_quality_job = 0.0  
            processing_time = 0.0
            
            # Get metrics from the collected results (use the first/last result, they should be similar)
            if all_results_metrics:
                latest_result = all_results_metrics[-1]  # Use last result
                memory_efficiency = latest_result.get('memory_efficiency', 100.0)
                total_cost = latest_result.get('total_cost', 0.0)
                cost_per_quality_job = latest_result.get('cost_per_quality_job', 0.0)
                
                # Extract processing time from timing dict
                timing_data = latest_result.get('timing', {})
                if timing_data and isinstance(timing_data, dict):
                    processing_time = timing_data.get('total_time', 0.0)
                
                print(f"🔧 Extracted metrics: memory_eff={memory_efficiency}%, cost=${total_cost:.3f}, time={processing_time:.1f}s")

            metadata = {
                'success': not combined_df.empty,
                'total_jobs': int(len(combined_df)),
                'quality_jobs': int(combined_quality),
                'files': files,
                'pdf_path': files.get('pdf'),  # Add PDF path for download button
                'search_type': 'memory_only',
                # Add missing efficiency metrics for analytics display
                'memory_efficiency': memory_efficiency,
                'total_cost': total_cost,
                'cost_per_quality_job': cost_per_quality_job,
                'processing_time': processing_time,
                'duration': processing_time,  # Alternative key name
            }
            return combined_df, metadata
        
        except Exception as e:
            # Avoid shadowing module-level pd; use a local alias if needed
            try:
                import pandas as _pd  # noqa: F401
                empty_df = _pd.DataFrame()
            except Exception:
                empty_df = None
            print(f"❌ Memory-only pipeline error: {str(e)}")
            metadata = {
                'success': False,
                'total_jobs': 0, 
                'quality_jobs': 0,
                'files': {},
                'search_type': 'memory_only',
                'error': str(e)
            }
            return empty_df, metadata
    
    def run_pipeline(self, params: Dict) -> Tuple[Any, Dict]:
        """Run pipeline - use in-process path for memory-only, subprocess for others"""
        try:
            # UI direct path (avoid subprocess/CSV parsing)
            if params.get('ui_direct', False):
                print(f"🎯 Using UI_DIRECT path - force_link_generation={params.get('force_link_generation', False)}")
                from pipeline_v3 import FreeWorldPipelineV3
                if not hasattr(self, 'pipeline_v3') or self.pipeline_v3 is None:
                    self.pipeline_v3 = FreeWorldPipelineV3()

                # Determine locations to run (support multi-market)
                locations_to_run: List[str]
                custom_location = params.get('custom_location')
                markets = params.get('markets') or []
                if custom_location:
                    locations_to_run = [custom_location]
                elif isinstance(markets, (list, tuple)) and len(markets) > 0:
                    # Run once per market name; pipeline handles mapping to city/state
                    locations_to_run = list(markets)
                else:
                    # Fallback to single provided location or default
                    fallback_loc = params.get('location')
                    # If the fallback is a multi-city combined string, it won't map well; prefer first market if available
                    locations_to_run = [fallback_loc] if fallback_loc else ['Houston']

                # Mode mapping
                mode = params.get('mode', 'sample')
                job_limits = {"test": 100, "mini": 50, "sample": 100, "medium": 250, "large": 500, "full": 1000}
                mode_info = {"mode": mode, "limit": job_limits.get(mode, 100)}

                # Respect memory-only mode in UI direct path
                memory_only_mode = bool(params.get('memory_only', False))
                direct_sources = params.get('search_sources') or {'indeed': True, 'google': False}
                if memory_only_mode:
                    # Disable fresh sources entirely; rely on Smart Credit/memory
                    direct_sources = {'indeed': False, 'google': False}

                # Run pipeline per location and merge results
                combined_df = pd.DataFrame() if pd else None
                combined_meta = {
                    'success': False,
                    'total_jobs': 0,
                    'included_jobs': 0,
                    'match_breakdown': {},
                    'processing_time': 0,
                    'total_cost': 0.0,
                    'memory_efficiency': 0.0,
                    'run_ids': []
                }

                for loc in locations_to_run:
                    results = self.pipeline_v3.run_complete_pipeline(
                        location=loc,
                        mode_info=mode_info,
                        search_terms=params.get('search_terms', 'CDL Driver No Experience'),
                        route_filter=params.get('route_filter', 'both'),
                        push_to_airtable=False,
                        force_fresh=params.get('force_fresh', False),
                        force_fresh_classification=params.get('force_fresh_classification', False),
                        force_memory_only=memory_only_mode,
                        force_link_generation=params.get('force_link_generation', False),
                        hardcoded_market=None,
                        custom_location=custom_location if custom_location else None,
                        generate_pdf=False,  # per-run PDF disabled in UI-direct path
                        generate_csv=False,
                        generate_html=True,
                        radius=params.get('search_radius', 50),
                        no_experience=params.get('no_experience', True),
                        filter_settings=params.get('filter_settings', {}),
                        search_sources=direct_sources,
                        search_strategy=params.get('search_strategy', 'balanced'),
                        coach_name=params.get('coach_name', ''),
                        coach_username=params.get('coach_username', ''),
                        candidate_name=params.get('candidate_name', ''),
                        candidate_id=params.get('candidate_id', '')
                    )

                    df_part = results.get('jobs_df') if isinstance(results, dict) else (pd.DataFrame() if pd else None)
                    if df_part is not None and not df_part.empty:
                        if combined_df.empty:
                            combined_df = df_part
                        else:
                            combined_df = pd.concat([combined_df, df_part], ignore_index=True)
                        combined_meta['success'] = combined_meta['success'] or bool(results.get('success', True))
                        combined_meta['total_jobs'] += int(results.get('total_jobs', len(df_part)))
                        combined_meta['included_jobs'] += int(results.get('included_jobs', 0))
                        combined_meta['processing_time'] += float(results.get('processing_time', 0))
                        combined_meta['total_cost'] += float(results.get('total_cost', 0.0))
                        combined_meta['memory_efficiency'] = max(combined_meta['memory_efficiency'], float(results.get('memory_efficiency', 0.0)))
                        if results.get('run_id'):
                            combined_meta['run_ids'].append(results.get('run_id'))

                # If nothing returned but we ran at least once, still return empty DF with success=False
                if not combined_df.empty:
                    # Recompute included jobs from combined_df for safety
                    try:
                        ai_series = combined_df.get('ai.match')
                        ai_good = int((ai_series == 'good').sum()) if ai_series is not None else 0
                        ai_soso = int((ai_series == 'so-so').sum()) if ai_series is not None else 0
                        combined_meta['included_jobs'] = ai_good + ai_soso if (ai_good + ai_soso) > 0 else combined_meta['included_jobs']
                        combined_meta['total_jobs'] = len(combined_df)
                    except Exception:
                        pass

                return combined_df, combined_meta

            # Check if this is a memory-only search - use direct Python call for performance
            if params.get('memory_only', False):
                print(f"🐌 Using OLD memory-only path - force_link_generation={params.get('force_link_generation', False)}")
                return self._run_memory_only_pipeline(params)
            
            # For all other searches, use subprocess to terminal script
            # Build command for terminal_job_search.py - use same Python as current process
            import sys
            cmd = [sys.executable, 'terminal_job_search.py']
            
            # Add location/market parameters (support multi-market)
            if params.get('custom_location'):
                cmd.extend(['--custom-location', params['custom_location']])
            else:
                markets = params.get('markets') or []
                if isinstance(markets, (list, tuple)) and len(markets) > 0:
                    # Pass comma-separated markets to terminal script which supports multiple
                    cmd.extend(['--market', ','.join(markets)])
                else:
                    market = params.get('location', 'Houston')
                    # Pass the market name directly - let the terminal script handle conversion
                    cmd.extend(['--market', market])
            
            # Add mode parameter - use max_jobs if specified, otherwise use provided mode
            if 'max_jobs' in params:
                max_jobs = params['max_jobs']
                if max_jobs <= 25:
                    cmd.extend(['--mode', 'test'])
                elif max_jobs <= 100:
                    cmd.extend(['--mode', 'sample']) 
                elif max_jobs <= 250:
                    cmd.extend(['--mode', 'medium'])
                elif max_jobs <= 500:
                    cmd.extend(['--mode', 'large'])
                else:
                    cmd.extend(['--mode', 'full'])
            else:
                cmd.extend(['--mode', params.get('mode', 'sample')])
            
            if params.get('search_terms', 'CDL driver') != 'CDL driver':
                cmd.extend(['--terms', params.get('search_terms')])
            
            if params.get('route_filter', 'both') != 'both':
                cmd.extend(['--route', params.get('route_filter')])
            
            # Add radius parameter if specified
            if 'radius' in params:
                radius = params['radius']
                if radius == 0:
                    # Use exact location flag for radius=0
                    cmd.append('--exact-location')
                else:
                    cmd.extend(['--radius', str(radius)])
            elif 'search_radius' in params:
                radius = params['search_radius'] 
                if radius == 0:
                    # Use exact location flag for radius=0
                    cmd.append('--exact-location')
                else:
                    cmd.extend(['--radius', str(radius)])
            
            # Airtable upload disabled in pipeline; ignore UI flag
            
            # Only add force-fresh if explicitly requested AND not memory-only
            if params.get('force_fresh') and not params.get('memory_only'):
                cmd.append('--force-fresh')
            
            # Add memory-only flag if requested
            if params.get('memory_only'):
                cmd.append('--memory-only')
                
            if params.get('force_fresh_classification'):
                cmd.append('--force-fresh-classification')
            
            # Set coach name in environment and preserve Python path
            env = os.environ.copy()
            if params.get('coach_name'):
                env['FREEWORLD_COACH_NAME'] = params.get('coach_name')
            if params.get('coach_username'):
                env['FREEWORLD_COACH_USERNAME'] = params.get('coach_username')
            if params.get('candidate_name'):
                env['FREEWORLD_CANDIDATE_NAME'] = params.get('candidate_name')
            if params.get('candidate_id'):
                env['FREEWORLD_CANDIDATE_ID'] = params.get('candidate_id')
            
            # Ensure subprocess uses same Python environment
            env['PYTHONPATH'] = ':'.join(sys.path)
            
            # Debug: Check environment differences
            supabase_url = env.get('SUPABASE_URL', 'MISSING')
            supabase_key = env.get('SUPABASE_ANON_KEY', 'MISSING')
            print(f"🔍 Environment Diagnostics:")
            print(f"  SUPABASE_URL: {'✅ Set' if supabase_url != 'MISSING' else '❌ Missing'}")
            print(f"  SUPABASE_ANON_KEY: {'✅ Set' if supabase_key != 'MISSING' else '❌ Missing'}")
            print(f"  Current Working Dir: {os.getcwd()}")
            print(f"  Script Working Dir: {self.parent_dir}")
            print(f"  Python Executable: {sys.executable}")
            print(f"  Python Version: {sys.version}")
            print(f"  Platform: {sys.platform}")
            print(f"  Environment Type: {'Streamlit Cloud' if '/mount/src/' in os.getcwd() else 'Local'}")
            
            # Check for key files that might be missing
            key_files = ['data/highway_background.jpg', 'data/FW-Wordmark-Roots@3x.png']
            for file_path in key_files:
                full_path = os.path.join(self.parent_dir, file_path)
                exists = os.path.exists(full_path)
                print(f"  {file_path}: {'✅ Found' if exists else '❌ Missing'}")
            
            # Hide debug info from UI - only print to console
            
            print(f"🚀 Running command: {' '.join(cmd)}")
            print(f"📁 Working directory: {self.parent_dir}")
            
            # Run the command with 5 minute timeout for all searches
            import time
            start_time = time.time()
            timeout = 300  # 5 minutes for all searches
            
            result = subprocess.run(
                cmd, 
                cwd=self.parent_dir, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                env=env
            )
            
            print(f"📊 Return code: {result.returncode}")
            # Hide pipeline output from UI - only print to console
            
            print(f"📄 FULL STDOUT:")
            print("=" * 80)
            if result.stdout:
                print(result.stdout)
            else:
                print("(No stdout output)")
            print("=" * 80)
            
            if result.stderr:
                print(f"❌ FULL STDERR:")
                print("=" * 80)  
                print(result.stderr)
                print("=" * 80)
            
            # Check for success - prioritize CSV generation over PDF
            csv_found = False
            csv_paths = []
            pdf_failed = False
            parquet_stage99_paths = []
            for line in (result.stdout or '').split('\n'):
                if 'Complete CSV:' in line or 'CSV saved:' in line:
                    csv_found = True
                if 'PDF generation failed:' in line:
                    pdf_failed = True
                # Collect stage 99 parquet checkpoints from pipeline output
                if 'Checkpoint saved:' in line and '_99_complete.parquet' in line:
                    try:
                        pth = line.split('Checkpoint saved:')[-1].strip()
                        if pth.endswith('_99_complete.parquet'):
                            parquet_stage99_paths.append(pth)
                    except Exception:
                        pass
            
            # Consider successful if CSV was generated, regardless of PDF status
            if result.returncode == 0 or csv_found:
                # Parse output for file paths and metadata
                csv_path = pdf_path = parquet_path = run_id = None
                included_jobs = total_jobs = 0
                match_breakdown = {}
                processing_time = total_cost = memory_efficiency = cost_per_quality_job_parsed = 0
                lines = (result.stdout or '').split('\n')
                
                print(f"🔍 Parsing {len(lines)} output lines for metadata...")
                run_timestamp = None
                
                for line in lines:
                    if 'CSV saved:' in line:
                        _p = line.split('CSV saved:')[-1].strip()
                        if _p:
                            csv_path = _p
                            csv_paths.append(_p)
                    elif 'Complete CSV:' in line:  # New parsing for Pipeline v3
                        _p = line.split('Complete CSV:')[-1].strip()
                        if _p:
                            csv_path = _p
                            csv_paths.append(_p)
                    elif 'Quality Jobs CSV (exportable only):' in line:
                        # Pipeline v3 export message
                        _p = line.split('Quality Jobs CSV (exportable only):')[-1].strip()
                        if _p:
                            csv_path = _p
                            csv_paths.append(_p)
                    elif 'PDF generated:' in line:
                        pdf_path = line.split('PDF generated:')[-1].strip()
                    elif 'PDF saved:' in line:
                        pdf_path = line.split('PDF saved:')[-1].strip()
                    elif 'Run ID:' in line:
                        try:
                            run_id = line.split('Run ID:')[-1].strip()
                        except Exception:
                            run_id = None
                    elif '(run:' in line and 'initialized' in line:
                        # e.g., "initialized (run: pipeline_v3_YYYY...)"
                        try:
                            import re
                            m = re.search(r'\(run:\s*([^\)]+)\)', line)
                            if m:
                                run_id = m.group(1).strip()
                        except Exception:
                            pass
                    elif line.strip().startswith('Timestamp:'):
                        try:
                            run_timestamp = line.split('Timestamp:')[-1].strip()
                        except Exception:
                            run_timestamp = None
                    elif 'Exporting' in line and 'quality jobs' in line:
                        # Parse "📊 Exporting 50 quality jobs"
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part.isdigit() and i + 1 < len(parts) and 'quality' in parts[i + 1]:
                                included_jobs = int(part)
                                break
                    elif 'Match breakdown:' in line:
                        # Parse "Match breakdown: {'good': 37, 'so-so': 13}"
                        try:
                            breakdown_str = line.split('Match breakdown:')[-1].strip()
                            match_breakdown = eval(breakdown_str)  # Safe since we control the format
                        except:
                            pass
                    elif 'Total processing time:' in line:
                        # Parse processing time - match pipeline_v3 exact format
                        import re
                        try:
                            # Match "⏱️ Total processing time: 2m 34.5s" or "⏱️ Total processing time: 45.6s"
                            if 'm ' in line and 's' in line:
                                # Minutes and seconds format: "2m 34.5s"
                                match = re.search(r'(\d+)m\s+(\d+\.?\d*)s', line)
                                if match:
                                    minutes = float(match.group(1))
                                    seconds = float(match.group(2))
                                    processing_time = minutes * 60 + seconds
                            else:
                                # Seconds only format: "45.6s"
                                match = re.search(r'(\d+\.?\d*)s', line)
                                if match:
                                    processing_time = float(match.group(1))
                        except:
                            pass
                    elif 'Total cost:' in line:
                        # Parse total cost - match pipeline_v3 exact format: "💰 Total cost: $0.123"
                        import re
                        try:
                            match = re.search(r'Total cost:\s*\$(\d+\.?\d*)', line)
                            if match:
                                total_cost = float(match.group(1))
                        except:
                            pass
                    elif 'Cost per quality job:' in line:
                        # Parse cost per quality job - match pipeline_v3 exact format: "💰 Cost per quality job: $0.123"
                        import re
                        try:
                            match = re.search(r'Cost per quality job:\s*\$(\d+\.?\d*)', line)
                            if match:
                                cost_per_quality_job_parsed = float(match.group(1))
                        except:
                            pass
                    elif 'Memory efficiency:' in line:
                        # Parse memory efficiency - match pipeline_v3 exact format: "🧠 Memory efficiency: 85.2%"
                        import re
                        try:
                            match = re.search(r'Memory efficiency:\s*(\d+\.?\d*)%', line)
                            if match:
                                memory_efficiency = float(match.group(1))
                        except:
                            pass
                
                print(f"📄 Found CSV: {csv_path}")
                print(f"📄 Found PDF: {pdf_path}")
                print(f"📊 Quality jobs: {included_jobs}")
                print(f"📊 Match breakdown: {match_breakdown}")
                print(f"⏱️ Processing time: {processing_time}s")
                print(f"💰 Total cost: ${total_cost}")
                print(f"🧠 Memory efficiency: {memory_efficiency}%")
                
                # Debug: Show which lines were processed for metrics
                print(f"🔍 Debug - Parsed metrics from pipeline output:")
                print(f"  - Processing time: {processing_time}s (parsed: {processing_time != 0})")
                print(f"  - Total cost: ${total_cost} (parsed: {total_cost != 0})")  
                print(f"  - Memory efficiency: {memory_efficiency}% (parsed: {memory_efficiency != 0})")
                print(f"  - Cost per quality job (raw): ${cost_per_quality_job_parsed} (parsed: {cost_per_quality_job_parsed > 0})")
                
                # Load results
                df = pd.DataFrame()
                # Load one or more CSVs (multi-market)
                loaded = []
                # Build a unique set of CSV paths from stdout parsing
                parsed_csvs = [p for p in (csv_paths or []) if p]
                if not parsed_csvs and csv_path:
                    parsed_csvs = [csv_path]

                # Also glob for CSVs matching this run timestamp; else fallback to recent mtime window
                try:
                    import glob
                    out_dir = os.path.join(self.parent_dir, 'FreeWorld_Jobs')
                    recent_csvs = []
                    if os.path.isdir(out_dir):
                        if run_timestamp:
                            ts_patterns = [
                                os.path.join(out_dir, f"*_{run_timestamp}.csv"),
                                os.path.join(out_dir, f"*complete_jobs_{run_timestamp}.csv"),
                            ]
                            for pattern in ts_patterns:
                                for pth in glob.glob(pattern):
                                    recent_csvs.append(pth)
                        if not recent_csvs:
                            # Broaden search patterns to include per-market CSVs and recurse into subfolders
                            patterns = [
                                os.path.join(out_dir, '*_complete_jobs_*.csv'),     # market slug files
                                os.path.join(out_dir, 'complete_jobs_*.csv'),        # legacy naming
                                os.path.join(out_dir, 'FreeWorld_Jobs_*_*.csv'),     # per-market CSV naming
                                os.path.join(out_dir, '*_quality_jobs_*.csv'),       # quality-only exports
                                os.path.join(out_dir, '**', '*.csv'),                # any CSV in subfolders
                            ]
                            for pattern in patterns:
                                for pth in glob.glob(pattern, recursive=True):
                                    try:
                                        mtime = os.path.getmtime(pth)
                                        # Only consider files created near this run to avoid stale data
                                        if mtime >= (start_time - 300):  # 5-minute window
                                            recent_csvs.append(pth)
                                    except Exception:
                                        pass
                    # Merge and dedupe
                    all_csvs = list({*parsed_csvs, *recent_csvs})
                except Exception:
                    all_csvs = parsed_csvs

                print(f"🔎 CSV aggregation: parsed={len(parsed_csvs)} recent_globbed={len(all_csvs) - len(parsed_csvs)} total_candidates={len(all_csvs)} ts={run_timestamp}")
                try:
                    import time
                    print("🗂️ CSV candidates:")
                    for c in all_csvs:
                        try:
                            ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(c)))
                        except Exception:
                            ts = "?"
                        print(f"   • {c} (mtime={ts})")
                except Exception:
                    pass

                for p in all_csvs:
                    try:
                        if p and os.path.exists(p):
                            loaded.append(pd.read_csv(p))
                    except Exception as e:
                        print(f"⚠️ Could not read CSV {p}: {e}")
                if loaded:
                    df = pd.concat(loaded, ignore_index=True)
                    total_jobs = len(df)
                print(f"📊 Loaded {total_jobs} jobs from {len(loaded)} CSV file(s)")
                try:
                    if 'meta.market' in df.columns:
                        market_counts = df['meta.market'].value_counts().to_dict()
                        print(f"🧭 Market breakdown: {market_counts}")
                    else:
                        print("🧭 Market breakdown: meta.market column not found")
                except Exception as e:
                    print(f"🧭 Market breakdown error: {e}")
                    # Recompute included_jobs from DataFrame if not parsed
                    try:
                        if included_jobs == 0:
                            if 'route.final_status' in df.columns:
                                included_jobs = df['route.final_status'].astype(str).str.startswith('included').sum()
                            elif 'ai.match' in df.columns:
                                included_jobs = df['ai.match'].isin(['good','so-so']).sum()
                    except Exception:
                        pass
                # Only log missing CSV if we truly couldn't load any file
                if not loaded and csv_path and not os.path.exists(csv_path):
                    print(f"❌ No CSV found at path: {csv_path}")
                
                # Debug: Print parsed values before creating metadata
                print(f"🔍 Final parsed values:")
                print(f"  included_jobs: {included_jobs}")
                print(f"  total_jobs: {total_jobs}")
                print(f"  match_breakdown: {match_breakdown}")
                print(f"  processing_time: {processing_time}")
                print(f"  total_cost: {total_cost}")
                print(f"  memory_efficiency: {memory_efficiency}")
                
                # Extract AI match counts from match_breakdown
                ai_good = match_breakdown.get('good', 0) if match_breakdown else 0
                ai_so_so = match_breakdown.get('so-so', 0) if match_breakdown else 0
                ai_bad = match_breakdown.get('bad', 0) if match_breakdown else 0
                
                # Calculate counts from DataFrame if available
                local_routes = 0
                otr_routes = 0  
                regional_routes = 0
                cost_per_quality_job = 0
                
                if not df.empty:
                    # AI match breakdown (override from DF if available)
                    try:
                        if 'ai.match' in df.columns:
                            _vc = df['ai.match'].value_counts()
                            ai_good = int(_vc.get('good', 0))
                            ai_so_so = int(_vc.get('so-so', 0))
                            ai_bad = int(_vc.get('bad', 0))
                    except Exception:
                        pass
                    if 'ai.route_type' in df.columns and 'ai.match' in df.columns:
                        # Filter to only good/so-so quality jobs for route counting
                        quality_jobs_df = df[df['ai.match'].isin(['good', 'so-so'])]
                        local_routes = (quality_jobs_df['ai.route_type'] == 'Local').sum()
                        otr_routes = (quality_jobs_df['ai.route_type'] == 'OTR').sum()
                        regional_routes = (quality_jobs_df['ai.route_type'] == 'Regional').sum()
                    
                    # Use parsed cost per quality job if available, otherwise calculate it
                    quality_jobs = ai_good + ai_so_so
                    if cost_per_quality_job_parsed > 0:
                        cost_per_quality_job = cost_per_quality_job_parsed
                    else:
                        cost_per_quality_job = total_cost / max(1, quality_jobs) if quality_jobs > 0 else 0

                # Build a combined parquet from the aggregated DataFrame (covers multi-market)
                parquet_debug = {'used_fallback': False, 'dir': None, 'candidates': 0, 'found_stage99': 0}
                try:
                    import glob
                    parquet_dir = os.path.join(self.parent_dir, 'FreeWorld_Jobs', 'parquet')
                    os.makedirs(parquet_dir, exist_ok=True)
                    parquet_debug['dir'] = parquet_dir
                    parquet_debug['found_stage99'] = len(parquet_stage99_paths)

                    if not df.empty:
                        from datetime import datetime
                        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                        combined_name = f"multi_market_combined_{ts}.parquet"
                        combined_path = os.path.join(parquet_dir, combined_name)
                        try:
                            df.to_parquet(combined_path, index=False)
                            parquet_path = combined_path
                        except Exception as write_err:
                            print(f"Parquet write error: {write_err}")
                            parquet_path = None
                    else:
                        # Fallback to the newest stage99 parquet if no DataFrame loaded
                        candidates = glob.glob(os.path.join(parquet_dir, '*_99_complete.parquet'))
                        parquet_debug['candidates'] = len(candidates)
                        if candidates:
                            newest = max(candidates, key=os.path.getmtime)
                            parquet_path = newest
                            parquet_debug['used_fallback'] = True
                            if not run_id:
                                base = os.path.basename(newest)
                                if base.endswith('_99_complete.parquet'):
                                    run_id = base.replace('_99_complete.parquet', '')
                except Exception as e:
                    print(f"Parquet detection error: {e}")
                    parquet_path = None

                return df, {
                    'success': True, 
                    'csv_path': csv_path, 
                    'pdf_path': pdf_path if not pdf_failed else None, 
                    'parquet_path': parquet_path,
                    'run_id': run_id,
                    'parquet_debug': parquet_debug,
                    'total_jobs': total_jobs,
                    'included_jobs': included_jobs,
                    'match_breakdown': match_breakdown,
                    'processing_time': processing_time,
                    'total_cost': total_cost,
                    'memory_efficiency': memory_efficiency,
                    'pdf_failed': pdf_failed,
                    # Additional metrics for UI consistency
                    'ai_good': ai_good,
                    'ai_so_so': ai_so_so,
                    'ai_bad': ai_bad,
                    'local_routes': local_routes,
                    'otr_routes': otr_routes,
                    'regional_routes': regional_routes,
                    'cost_per_quality_job': cost_per_quality_job,
                    'quality_jobs': ai_good + ai_so_so
                }
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                print(f"❌ Pipeline failed: {error_msg}")
                return pd.DataFrame(), {'success': False, 'error': error_msg}
                
        except subprocess.TimeoutExpired as e:
            # Handle timeout specifically to capture any partial output
            print(f"⏰ Pipeline timed out after {timeout} seconds")
            print(f"📄 PARTIAL STDOUT (from timeout):")
            print("=" * 80)
            if e.stdout:
                print(e.stdout.decode() if isinstance(e.stdout, bytes) else str(e.stdout))
            else:
                print("(No stdout output)")
            print("=" * 80)
            
            if e.stderr:
                print(f"❌ PARTIAL STDERR (from timeout):")
                print("=" * 80)
                print(e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr))
                print("=" * 80)
            
            error_msg = f"Pipeline timed out after {timeout} seconds"
            return pd.DataFrame(), {'success': False, 'error': error_msg}
        
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Exception: {error_msg}")
            return pd.DataFrame(), {'success': False, 'error': error_msg}
    
    def dataframe_to_csv_bytes(self, df: Any) -> bytes:
        if df.empty:
            return b""
        return df.to_csv(index=False).encode('utf-8')
    
    def dataframe_to_parquet_bytes(self, df: Any) -> bytes:
        """Serialize a DataFrame to Parquet bytes (full canonical by default)."""
        try:
            if df is None or df.empty:
                return b""
            buf = io.BytesIO()
            # Let pandas choose available engine (pyarrow/fastparquet)
            df.to_parquet(buf, index=False)
            return buf.getvalue()
        except Exception as e:
            print(f"Error generating parquet bytes: {e}")
            return b""
    
    def get_pdf_bytes(self, pdf_path: str) -> bytes:
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                return f.read()
        return b""
    
    def get_parquet_bytes(self, parquet_path: str) -> bytes:
        if parquet_path and os.path.exists(parquet_path):
            try:
                with open(parquet_path, 'rb') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading parquet: {e}")
        return b""
    
    def generate_pdf_from_canonical(self, df: Any, market_name: str, 
                                   coach_name: str = '', coach_username: str = '',
                                   candidate_name: str = '', candidate_id: str = '',
                                   show_prepared_for: bool = True) -> bytes:
        """Generate PDF from DataFrame (for download button functionality)"""
        if df.empty:
            return b""
        
        try:
            print(f"🔍 Wrapper PDF Generator received: {len(df)} jobs")
            print(f"   Market: '{market_name}' (empty={not market_name})")
            print(f"   Coach: '{coach_name}' (empty={not coach_name})")
            print(f"   Coach Username: '{coach_username}' (empty={not coach_username})")
            print(f"   Candidate: '{candidate_name}' (empty={not candidate_name})")
            print(f"   Candidate ID: '{candidate_id}' (empty={not candidate_id})")
            print(f"   Show Prepared For: {show_prepared_for}")
            
            # Use YOUR HTML template system - EXACTLY like HTML preview
            from pdf.html_pdf_generator import jobs_dataframe_to_dicts, render_jobs_html
            
            # Build agent_params - same format as HTML template system
            agent_params = {
                'location': market_name,
                'agent_name': candidate_name,
                'agent_uuid': candidate_id,
                'coach_name': coach_name,
                'coach_username': coach_username,
                'show_prepared_for': show_prepared_for
            }
            
            # Convert DataFrame and generate HTML using YOUR template system
            jobs = jobs_dataframe_to_dicts(df)
            html = render_jobs_html(jobs, agent_params)
            
            # Create temporary PDF file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                temp_path = tmp_file.name
            
            # Convert HTML to PDF using xhtml2pdf (pure Python, works in cloud)
            try:
                from xhtml2pdf import pisa
                
                with open(temp_path, "wb") as result_file:
                    pisa_status = pisa.CreatePDF(html, dest=result_file)
                
                if pisa_status.err:
                    print(f"❌ xhtml2pdf generation failed with errors")
                    return b""
            except ImportError:
                print(f"⚠️ xhtml2pdf not available - cannot generate PDF")
                return b""
            
            # Read PDF bytes
            if os.path.exists(temp_path):
                with open(temp_path, 'rb') as f:
                    pdf_bytes = f.read()
                os.unlink(temp_path)  # Clean up temp file
                print(f"✅ FPDF2 PDF generated successfully: {len(pdf_bytes)} bytes")
                return pdf_bytes
            
            return b""
        except Exception as e:
            print(f"❌ Error generating PDF: {e}")
            import traceback
            traceback.print_exc()
            return b""
