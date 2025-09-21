#!/usr/bin/env python3
"""
Enhanced Terminal Job Search - Complete recreation based on GUI wrapper functionality
Matches all features from the GUI version: multi-market, custom location, Airtable, etc.
Usage: python3 terminal_job_search.py
"""

import os
import sys
import argparse
from pathlib import Path

try:
    import toml
    HAS_TOML = True
except ImportError:
    HAS_TOML = False

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def load_secrets():
    """Load secrets from .streamlit/secrets.toml into environment variables"""
    if not HAS_TOML:
        print("⚠️ toml module not available. Install with: pip install toml")
        return False
        
    secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
    
    if secrets_path.exists():
        try:
            secrets = toml.load(secrets_path)
            for key, value in secrets.items():
                if isinstance(value, (str, int, float, bool)):
                    os.environ.setdefault(key, str(value))
            print(f"✅ Loaded {len(secrets)} secrets from {secrets_path}")
            return True
        except Exception as e:
            print(f"⚠️ Failed to load secrets: {e}")
    else:
        print(f"⚠️ No secrets file found at {secrets_path}")
        print("💡 Copy .streamlit/secrets.toml.example to .streamlit/secrets.toml and add your API keys")
    
    return False

from cost_calculator import CostCalculator
from datetime import datetime

# Pipeline v3 imports - required
from pipeline_v3 import FreeWorldPipelineV3

from shared_search import (
    MARKET_SEARCH_QUERIES,
    MARKET_NAMES_TO_NUMBERS,
    QUERY_LOCATION_OVERRIDES,
)

# For query building only: override certain markets to use a representative city
QUERY_LOCATION_OVERRIDES = {
    "Bay Area, CA": "Berkeley, CA",
    "Inland Empire, CA": "Ontario, CA",
    "San Antonio, TX": "San Antonio, TX",  # Already specific city
    "Austin, TX": "Austin, TX",  # Already specific city
}

class EnhancedTerminalJobSearch:
    def __init__(self):
        # Load secrets first (same as Streamlit app)
        load_secrets()
        
        # Initialize cost calculator
        self.calculator = CostCalculator()
        
        # Initialize pipeline v3 - required
        try:
            self.pipeline_v3 = FreeWorldPipelineV3()
            print(f"✅ Using Pipeline v3 (new single-table architecture)")
            
            # Debug: Check environment variables
            candidate_name = os.getenv('FREEWORLD_CANDIDATE_NAME', '')
            candidate_id = os.getenv('FREEWORLD_CANDIDATE_ID', '')
            coach_name = os.getenv('FREEWORLD_COACH_NAME', '')
            coach_username = os.getenv('FREEWORLD_COACH_USERNAME', '')
            print(f"🔍 Terminal script environment variables:")
            print(f"   FREEWORLD_CANDIDATE_NAME: '{candidate_name}' (empty={not candidate_name})")
            print(f"   FREEWORLD_CANDIDATE_ID: '{candidate_id}' (empty={not candidate_id})")
            print(f"   FREEWORLD_COACH_NAME: '{coach_name}' (empty={not coach_name})")
            print(f"   FREEWORLD_COACH_USERNAME: '{coach_username}' (empty={not coach_username})")
            
        except Exception as e:
            print(f"❌ Pipeline v3 initialization failed: {e}")
            print("⚠️ This may be due to missing API keys. Use --test-pipeline to verify setup.")
            self.pipeline_v3 = None
        
        # Market configuration from GUI (matches exactly)
        self.available_markets = list(MARKET_SEARCH_QUERIES.keys())
        
        # Default values matching GUI
        self.selected_markets = []
        self.custom_location = ""
        self.search_terms = []
        self.route_filter = "both"
        self.airtable_upload = False
        self.mode_info = {"mode": "sample", "limit": 100}

    def show_market_selection(self):
        """Show market selection with custom location option - matches GUI exactly"""
        print("\n🗺️ === SELECT TARGET MARKET(S) OR CUSTOM LOCATION ===")
        print("💡 You can select multiple markets OR enter a custom location below.\n")
        
        # Show available markets with checkboxes (simulated)
        print("Available Markets:")
        for i, market in enumerate(self.available_markets, 1):
            location = MARKET_SEARCH_QUERIES[market]
            print(f"  [{i:2}] {market} ({location})")
        
        print(f"\nMultiple selection examples: '1,3,5' or '1-3' or '1 3 5'")
        
        # Get market selections
        while True:
            try:
                market_input = input(f"\nSelect market numbers (1-{len(self.available_markets)}) or press Enter for custom location: ").strip()
                
                if not market_input:
                    # User wants custom location
                    break
                
                # Parse market selections
                selected_indices = self.parse_selection(market_input, len(self.available_markets))
                if selected_indices:
                    selected_markets = [self.available_markets[i-1] for i in selected_indices]
                    locations = [MARKET_SEARCH_QUERIES[market] for market in selected_markets]
                    
                    print(f"✅ Selected {len(selected_markets)} market(s):")
                    for market, location in zip(selected_markets, locations):
                        print(f"   • {market} ({location})")
                    
                    return selected_markets, ""
                else:
                    print("❌ Invalid selection. Please try again.")
                    
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Goodbye!")
                sys.exit(0)
        
        # Custom location input
        print("\n📍 === CUSTOM LOCATION INPUT ===")
        print("Examples: '90210', 'Austin, TX', 'Denver, CO', 'New York, NY'")
        
        while True:
            try:
                custom_location = input("\nEnter custom location: ").strip()
                
                if not custom_location:
                    print("❌ Please enter a location or go back to select markets.")
                    continue
                
                print(f"✅ Custom location: {custom_location}")
                print("⚠️ Note: Custom location takes priority over market selections")
                return [], custom_location
                
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Goodbye!")
                sys.exit(0)

    def parse_selection(self, selection_str, max_num):
        """Parse user selection string like '1,3,5' or '1-3' into list of numbers"""
        try:
            indices = []
            
            # Handle comma-separated
            if ',' in selection_str:
                parts = [part.strip() for part in selection_str.split(',')]
            # Handle space-separated  
            elif ' ' in selection_str:
                parts = selection_str.split()
            # Handle range like '1-3'
            elif '-' in selection_str and selection_str.count('-') == 1:
                start, end = selection_str.split('-')
                return list(range(int(start.strip()), int(end.strip()) + 1))
            # Single number
            else:
                parts = [selection_str]
            
            for part in parts:
                num = int(part.strip())
                if 1 <= num <= max_num:
                    indices.append(num)
                else:
                    return None
            
            return list(set(indices))  # Remove duplicates
            
        except ValueError:
            return None

    def get_search_terms(self):
        """Get custom search terms from user - matches GUI functionality"""
        print("\n🔍 === JOB SEARCH TERMS ===")
        print("Enter job search terms (separate multiple terms with commas)")
        print("Examples: 'CDL driver, truck driver' or 'delivery driver, commercial driver'")
        print("Default terms will be used if left blank: CDL driver, truck driver, delivery driver")
        
        while True:
            try:
                terms_input = input("\nEnter search terms (or press Enter for defaults): ").strip()
                
                if not terms_input:
                    # Use default terms focused on entry-level positions
                    default_terms = ["CDL driver no experience", "entry level CDL driver", "CDL training provided"]
                    print(f"✅ Using default terms: {', '.join(default_terms)}")
                    return default_terms
                    
                # Split by comma and clean up
                terms = [term.strip() for term in terms_input.split(',') if term.strip()]
                
                if terms:
                    print(f"✅ Will search for: {', '.join(terms)}")
                    return terms
                else:
                    print("❌ Please enter valid search terms or press Enter for defaults")
                    
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Goodbye!")
                sys.exit(0)

    def show_route_filter_selection(self):
        """Show route type filter options - matches GUI"""
        print("\n🛣️ === ROUTE TYPE FILTER ===")
        print("1. Both (Local and OTR jobs)")
        print("2. Local only (Home daily)")
        print("3. OTR only (Over-the-road)")
        
        while True:
            try:
                choice = input("\nSelect route filter (1-3): ").strip()
                
                if choice == "1" or choice == "":
                    print("✅ Selected: Both Local and OTR jobs")
                    return "both"
                elif choice == "2":
                    print("✅ Selected: Local jobs only (home daily)")
                    return "local"
                elif choice == "3":
                    print("✅ Selected: OTR jobs only (over-the-road)")
                    return "otr"
                else:
                    print("❌ Please enter 1, 2, or 3")
                    
            except ValueError:
                print("❌ Please enter a valid number")
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Goodbye!")
                sys.exit(0)

    def show_airtable_option(self, custom_location=""):
        """Show Airtable integration option - matches GUI with custom location warning"""
        print("\n🗃️ === AIRTABLE INTEGRATION ===")
        print("1. CSV files only (default)")
        print("2. CSV files + Airtable upload")
        
        if custom_location:
            print("💡 Tip: Consider CSV-only for one-off custom locations")
        
        while True:
            try:
                choice = input("\nSelect export option (1-2): ").strip()
                
                if choice == "1" or choice == "":
                    print("✅ Selected: CSV files only")
                    return False
                elif choice == "2":
                    print("✅ Selected: CSV files + Airtable upload")
                    if custom_location:
                        print("⚠️ Note: Using Airtable upload with custom location")
                    return True
                else:
                    print("❌ Please enter 1 or 2")
                    
            except ValueError:
                print("❌ Please enter a valid number")
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Goodbye!")
                sys.exit(0)

    def show_search_mode_selection(self):
        """Show enhanced search mode selection - matches GUI modes"""
        print("\n📊 === SEARCH MODE ===")
        
        # Get cost estimates - minimum 50 jobs for meaningful results
        test_cost = self.calculator.estimate_search_cost(indeed_jobs=100)   
        sample_cost = self.calculator.estimate_search_cost(indeed_jobs=100)
        medium_cost = self.calculator.estimate_search_cost(indeed_jobs=250)
        full_cost = self.calculator.estimate_search_cost(indeed_jobs=1000)
        
        print(f"1. Test (10 jobs) - Quick test")
        print(f"   💰 Cost: ~${test_cost:.2f} per location")

        print(f"2. Mini (50 jobs) - Small focused search")
        print(f"   💰 Cost: ~${sample_cost:.2f} per location")

        print(f"3. Sample (100 jobs) - Balanced search [DEFAULT]")
        print(f"   💰 Cost: ~${sample_cost:.2f} per location")

        print(f"4. Medium (250 jobs) - Enhanced search")
        print(f"   💰 Cost: ~${sample_cost * 2.5:.2f} per location")

        print(f"5. Large (500 jobs) - Extensive search")
        print(f"   💰 Cost: ~${sample_cost * 5:.2f} per location")

        print(f"6. Full (1000 jobs) - Comprehensive search")
        print(f"   💰 Cost: ~${full_cost:.2f} per location")
        
        while True:
            try:
                choice = input("\nEnter mode (1-6) or press Enter for default: ").strip()
                
                if choice == "1":
                    return {"mode": "test", "limit": 10, "cost": test_cost}
                elif choice == "2":
                    return {"mode": "mini", "limit": 50, "cost": sample_cost}
                elif choice == "3" or choice == "":
                    return {"mode": "sample", "limit": 100, "cost": sample_cost}
                elif choice == "4":
                    return {"mode": "medium", "limit": 250, "cost": medium_cost}
                elif choice == "5":
                    return {"mode": "large", "limit": 500, "cost": sample_cost * 5}
                elif choice == "6":
                    return {"mode": "full", "limit": 1000, "cost": full_cost}
                else:
                    print("❌ Please enter 1, 2, 3, 4, 5, or 6")
                    
            except ValueError:
                print("❌ Please enter a valid number")
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Goodbye!")
                sys.exit(0)

    def show_search_configuration(self, selected_markets, custom_location, search_terms, route_filter, airtable_upload, mode_info, interactive=True):
        """Display comprehensive search configuration preview - matches GUI exactly"""
        print(f"\n📋 === SEARCH CONFIGURATION PREVIEW ===")
        
        # Markets or Custom Location
        if custom_location:
            print(f"Custom Location: {custom_location}")
            if selected_markets:
                print("⚠️ Note: Custom location takes priority over selected markets")
        elif selected_markets:
            print(f"Selected Markets: {', '.join(selected_markets)}")
            locations = [MARKET_SEARCH_QUERIES[market] for market in selected_markets]
            print("Market Details:")
            for market, location in zip(selected_markets, locations):
                print(f"  • {market} ({location})")
        else:
            print("Location: ❌ No markets selected or custom location entered")
        
        # Search configuration
        print(f"Search Terms: {', '.join(search_terms)}")
        print(f"Mode: {mode_info['mode'].title()} ({mode_info['limit']} jobs per search)")
        
        # Route filter display
        route_filter_display = {
            "both": "Both Local and OTR jobs",
            "local": "Local jobs only (home daily)",
            "otr": "OTR jobs only (over-the-road)"
        }
        print(f"Route Filter: {route_filter_display[route_filter]}")
        print(f"Radius: 50 miles")
        print(f"Experience: No experience required filter enabled")
        print(f"Airtable Upload: {'✅ Enabled' if airtable_upload else '❌ Disabled'}")
        
        # Search scale calculation
        num_locations = 1 if custom_location else len(selected_markets)
        num_terms = len(search_terms)
        
        if num_locations > 0:
            total_searches = num_locations * num_terms
            expected_jobs = total_searches * mode_info['limit']
            
            print(f"\n🔍 Search Scale:")
            print(f"  • {num_terms} search term(s)")
            print(f"  • {num_locations} location(s)")
            print(f"  • Total searches: {num_terms} × {num_locations} = {total_searches}")
            print(f"  • Jobs per search: {mode_info['limit']}")
            print(f"  • Expected total jobs: ~{expected_jobs}")
            
            # Cost calculation
            total_cost = mode_info['cost'] * num_locations
            print(f"\n💰 Expected API costs:")
            print(f"  • OpenAI (classification): ~${total_cost:.2f}")
            print(f"  • Indeed scraping: Free")
            
            print(f"\n📄 Output:")
            if custom_location:
                print(f"  • Single PDF report for custom location")
            else:
                print(f"  • Separate PDF report for each market ({num_locations} PDFs)")
            print(f"  • All files saved to Desktop")
            
        
        # Validation
        print(f"\n=== VALIDATION ===")
        if not selected_markets and not custom_location:
            print("❌ No markets selected or custom location entered")
            return False
        elif not search_terms:
            print("❌ No search terms specified")
            return False
        else:
            print("✅ Configuration is valid")
        
        # Warnings
        if custom_location and airtable_upload:
            print("⚠️ Consider disabling Airtable upload for one-off custom locations")
        
        # Skip confirmation in non-interactive mode (CLI args provided)
        if not interactive:
            print("\n✅ Auto-confirming search (non-interactive mode)")
            return True
            
        try:
            confirm = input(f"\nProceed with this search? (y/n): ").lower().strip()
            return confirm in ['y', 'yes']
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")
            sys.exit(0)

    def run_search_v3(self, location, search_terms, route_filter, airtable_upload, mode_info, force_fresh=False, force_fresh_classification=False, memory_only=False, is_custom_location=False, radius=50, no_experience=True, business_rules=True, deduplication=True, experience_filter=True, classification_model="gpt-4o-mini", batch_size=25, generate_pdf=True, generate_csv=True, generate_html=True, save_parquet=False, filter_settings=None, search_sources=None, search_strategy="balanced", classifier_type="cdl"):
        """Run search using Pipeline v3"""
        print(f"🚀 Using Pipeline v3 for location: {location}")
        
        try:
            # Convert parameters to Pipeline v3 format - only include supported parameters
            pipeline_params = {
                'location': location,
                'mode_info': mode_info,
                'search_terms': ' '.join(search_terms),  # v3 expects single string
                'route_filter': route_filter,
                'radius': radius,
                'no_experience': no_experience,
                'generate_pdf': generate_pdf,
                'generate_csv': generate_csv,
                'push_to_airtable': airtable_upload,
                'force_fresh': force_fresh,
                'force_fresh_classification': force_fresh_classification,
                'force_memory_only': memory_only,
                'custom_location': location if is_custom_location else None,
                'filter_settings': filter_settings or {},
                'search_sources': search_sources or {'indeed': True, 'google': False},
                'search_strategy': search_strategy,
                'classifier_type': classifier_type
            }
            
            # Log additional parameters for user visibility (not passed to pipeline)
            additional_params = {
                'business_rules': business_rules,
                'deduplication': deduplication, 
                'experience_filter': experience_filter,
                'classification_model': classification_model,
                'batch_size': batch_size,
                'save_parquet': save_parquet
            }
            
            print(f"📊 Pipeline v3 parameters:")
            for key, value in pipeline_params.items():
                print(f"   {key}: {value}")
            
            print(f"📋 Additional settings (terminal-only):")
            for key, value in additional_params.items():
                print(f"   {key}: {value}")
            
            # Run Pipeline v3
            result = self.pipeline_v3.run_complete_pipeline(**pipeline_params)
            
            if result and result.get('success', True):
                print(f"✅ Pipeline v3 completed successfully")
                print(f"   Summary: {result.get('summary', 'No summary available')}")
                return True, result
            else:
                print(f"❌ Pipeline v3 failed")
                return False, result
                
        except Exception as e:
            print(f"💥 Pipeline v3 error: {e}")
            import traceback
            traceback.print_exc()
            return False, None


    def run_search(self, selected_markets, custom_location, search_terms, route_filter, airtable_upload, mode_info, force_fresh=False, force_fresh_classification=False, memory_only=False, radius=50, no_experience=True, business_rules=True, deduplication=True, experience_filter=True, classification_model="gpt-4o-mini", batch_size=25, generate_pdf=True, generate_csv=True, generate_html=True, save_parquet=False, filter_settings=None, search_sources=None, search_strategy="balanced", classifier_type="cdl"):
        """Execute the search using Pipeline v3 or v2 with fallback"""
        print(f"\n=== STARTING MULTI-LOCATION JOB SEARCH ===")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"Timestamp: {timestamp}")
        
        # Determine location for processing
        hardcoded_market = None
        if custom_location:
            # Custom location: use as-is for both query and labeling
            location = custom_location
            hardcoded_market = None
            print(f"Custom location: {custom_location}")
        elif selected_markets:
            market_label = MARKET_SEARCH_QUERIES[selected_markets[0]]
            # Override query location for certain markets
            location = QUERY_LOCATION_OVERRIDES.get(market_label, market_label)
            hardcoded_market = market_label  # Keep original market label for output/meta
            print(f"Selected market: {selected_markets[0]} ({market_label}) → query location: {location}")
        else:
            print("❌ No location specified")
            return False
        
        print(f"Search terms: {', '.join(search_terms)}")
        print(f"Route filter: {route_filter}")
        print(f"Mode: {mode_info['mode']} ({mode_info.get('limit', 'N/A')} jobs)")
        print(f"Pipeline: v3 (new)")
        print(f"Airtable upload: {'Enabled' if airtable_upload else 'Disabled'}")
        print("=" * 60)
        
        try:
            overall_success = True
            if custom_location or len(selected_markets) <= 1:
                success, result = self.run_search_v3(
                    location=location,
                    search_terms=search_terms,
                    route_filter=route_filter,
                    airtable_upload=airtable_upload,
                    mode_info=mode_info,
                    force_fresh=force_fresh,
                    force_fresh_classification=force_fresh_classification,
                    memory_only=memory_only,
                    is_custom_location=custom_location is not None,
                    radius=radius,
                    no_experience=no_experience,
                    business_rules=business_rules,
                    deduplication=deduplication,
                    experience_filter=experience_filter,
                    classification_model=classification_model,
                    batch_size=batch_size,
                    generate_pdf=generate_pdf,
                    generate_csv=generate_csv,
                    generate_html=generate_html,
                    save_parquet=save_parquet,
                    filter_settings=filter_settings,
                    search_sources=search_sources,
                    search_strategy=search_strategy,
                    classifier_type=classifier_type
                )
                overall_success = success
            else:
                print(f"\n🔁 Running {len(selected_markets)} market(s) sequentially...")
                per_market_csvs = []
                total_rows_by_market = {}
                for idx, market_id in enumerate(selected_markets, 1):
                    market_label = MARKET_SEARCH_QUERIES[market_id]
                    loc = QUERY_LOCATION_OVERRIDES.get(market_label, market_label)
                    print(f"\n— Market {idx}/{len(selected_markets)}: {market_label} → query location: {loc}")
                    success, result = self.run_search_v3(
                        location=loc,
                        search_terms=search_terms,
                        route_filter=route_filter,
                        airtable_upload=airtable_upload,
                        mode_info=mode_info,
                        force_fresh=force_fresh,
                        force_fresh_classification=force_fresh_classification,
                        memory_only=memory_only,
                        is_custom_location=False,
                        radius=radius,
                        no_experience=no_experience,
                        business_rules=business_rules,
                        deduplication=deduplication,
                        experience_filter=experience_filter,
                        classification_model=classification_model,
                        batch_size=batch_size,
                        generate_pdf=generate_pdf,
                        generate_csv=generate_csv,
                        generate_html=generate_html,
                        save_parquet=save_parquet,
                        filter_settings=filter_settings,
                        search_sources=search_sources,
                        search_strategy=search_strategy,
                        classifier_type=classifier_type
                    )
                    overall_success = overall_success and success
                    # Collect per-market CSV path(s) from result
                    try:
                        if result:
                            if result.get('csv_path'):
                                per_market_csvs.append(result['csv_path'])
                            for f in result.get('files', []) or []:
                                if isinstance(f, str) and f.lower().endswith('.csv'):
                                    per_market_csvs.append(f)
                    except Exception:
                        pass

                # Aggregate per-market CSVs into a single combined CSV/Parquet
                try:
                    import pandas as pd
                    unique_csvs = [c for c in dict.fromkeys(per_market_csvs) if c and os.path.exists(c)]
                    print(f"\n📦 Aggregating {len(unique_csvs)} market CSV(s) into combined results…")
                    if unique_csvs:
                        dfs = []
                        for c in unique_csvs:
                            try:
                                _df = pd.read_csv(c)
                                dfs.append(_df)
                                # Track rows by meta.market when available
                                try:
                                    mk = str(_df.get('meta.market', '')).strip()
                                except Exception:
                                    mk = ''
                                total_rows_by_market[os.path.basename(c)] = len(_df)
                            except Exception as e:
                                print(f"⚠️ Could not read {c}: {e}")
                        if dfs:
                            combined_df = pd.concat(dfs, ignore_index=True)
                            # Write combined CSV into the same output dir
                            out_dir = getattr(self.pipeline_v3, 'output_dir', os.getcwd())
                            combined_csv = os.path.join(out_dir, f"multi_market_combined_{timestamp}.csv")
                            combined_df.to_csv(combined_csv, index=False)
                            print(f"✅ Complete CSV: {combined_csv}")
                            # Write combined parquet into parquet dir
                            parquet_dir = os.path.join(out_dir, 'parquet')
                            os.makedirs(parquet_dir, exist_ok=True)
                            combined_parquet = os.path.join(parquet_dir, f"multi_market_combined_{timestamp}.parquet")
                            try:
                                combined_df.to_parquet(combined_parquet, index=False)
                                print(f"✅ Checkpoint saved: {combined_parquet}")
                            except Exception as e:
                                print(f"⚠️ Combined parquet write failed: {e}")
                            # Print simple breakdown
                            try:
                                if 'meta.market' in combined_df.columns:
                                    print(f"🧭 Combined market breakdown: {combined_df['meta.market'].value_counts().to_dict()}")
                            except Exception:
                                pass
                        else:
                            print("⚠️ No per-market CSVs could be read for aggregation")
                    else:
                        print("⚠️ No per-market CSVs detected for aggregation")
                except Exception as e:
                    print(f"⚠️ Aggregation error: {e}")

            if overall_success:
                print(f"\n🎉 Multi-location search completed successfully!")
                print(f"📁 Results saved to: ~/Desktop/FreeWorld_Jobs/")
                return True
            else:
                print(f"\n❌ One or more markets failed - check logs above")
                return False
                
        except Exception as e:
            print(f"\n❌ Search failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def run_interactive(self, dry_run=False):
        """Run the full interactive terminal session - complete GUI functionality recreation"""
        print("🚛 FreeWorld Job Scraper v1.0 - Terminal Edition")
        print("Complete feature parity with GUI version")
        print("=" * 60)

        # Interactive mode default
        generate_html = False

        
        while True:  # Main loop for multiple searches
            try:
                # Step 1: Select markets or custom location
                selected_markets, custom_location = self.show_market_selection()
                
                # Step 2: Get search terms
                search_terms = self.get_search_terms()
                
                # Step 3: Select route filter
                route_filter = self.show_route_filter_selection()
                
                # Step 4: Select Airtable option (with custom location awareness)
                airtable_upload = self.show_airtable_option(custom_location)
                
                # Step 5: Select search mode  
                mode_info = self.show_search_mode_selection()
                
                # Step 6: Show configuration preview and get confirmation
                if not self.show_search_configuration(selected_markets, custom_location, search_terms, route_filter, airtable_upload, mode_info):
                    print("❌ Search cancelled or invalid configuration")
                    
                    # Ask if they want to try again
                    while True:
                        try:
                            retry = input("\nWould you like to try again? (y/n): ").lower().strip()
                            if retry in ['y', 'yes']:
                                break
                            elif retry in ['n', 'no']:
                                return
                            else:
                                print("❌ Please enter 'y' for yes or 'n' for no")
                        except (KeyboardInterrupt, EOFError):
                            print("\n👋 Goodbye!")
                            return
                    continue
                
                # Step 7: Run the search
                success = self.run_search(selected_markets, custom_location, search_terms, route_filter, airtable_upload, mode_info, generate_html=generate_html)
                
                if success:
                    print(f"\n🎉 Search completed successfully!")
                    print(f"📁 Check ~/Desktop/FreeWorld_Jobs/ for your results")
                else:
                    print(f"\n❌ Search encountered errors")
                
                # Step 8: Ask if user wants to run another search
                print(f"\n" + "=" * 60)
                while True:
                    try:
                        another_search = input("Would you like to run another search? (y/n): ").lower().strip()
                        if another_search in ['y', 'yes']:
                            print(f"\n🚛 Starting new search...")
                            print("=" * 60)
                            break
                        elif another_search in ['n', 'no']:
                            print(f"\n✅ Thanks for using FreeWorld Job Scraper!")
                            return
                        else:
                            print("❌ Please enter 'y' for yes or 'n' for no")
                    except (KeyboardInterrupt, EOFError):
                        print("\n👋 Goodbye!")
                        return
                        
            except KeyboardInterrupt:
                print(f"\n❌ Search cancelled by user (Ctrl+C)")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {str(e)}")
                import traceback
                traceback.print_exc()
                
                while True:
                    try:
                        try_again = input("\nWould you like to try another search? (y/n): ").lower().strip()
                        if try_again in ['y', 'yes']:
                            break
                        elif try_again in ['n', 'no']:
                            return
                        else:
                            print("❌ Please enter 'y' for yes or 'n' for no")
                    except (KeyboardInterrupt, EOFError):
                        print("\n👋 Goodbye!")
                        return
        
        input("\nPress Enter to exit...")

    def run_quick_command(self, markets=None, market=None, custom_location=None, mode="sample", route="both", terms="CDL Driver No Experience", radius=50, no_experience=True, business_rules=True, deduplication=True, experience_filter=True, classification_model="gpt-4o-mini", batch_size=25, generate_pdf=True, generate_csv=True, generate_html=True, save_parquet=False, airtable=False, force_fresh=False, force_fresh_classification=False, memory_only=False, search_sources=None, search_strategy="balanced", classifier_type="cdl", dry_run=False):
        """Run a quick command-line search with parameters"""
        
        # Location to Market mapping for new format
        LOCATION_TO_MARKET = {
            "Houston, TX": 1, "Dallas, TX": 2, "Berkeley, CA": 3, "Stockton, CA": 4,
            "Denver, CO": 5, "Las Vegas, NV": 6, "Newark, NJ": 7, "Phoenix, AZ": 8,
            "Trenton, NJ": 9, "Ontario, CA": 10, "San Antonio, TX": 11, "Austin, TX": 12
        }
        
        # Parse inputs - handle both markets (list) and market (single) parameters
        if custom_location:
            selected_markets = []
            location_to_use = custom_location
        elif markets or market:
            # Handle multiple markets or single market
            selected_markets = []
            markets_to_process = markets if markets else [market]
            for market_item in markets_to_process:
                # First try new location format (City, ST)
                if market_item in LOCATION_TO_MARKET:
                    market_number = LOCATION_TO_MARKET[market_item]
                    selected_markets.append(market_number)
                # Fallback to old lowercase format
                elif market_item.lower() in MARKET_NAMES_TO_NUMBERS:
                    market_number = MARKET_NAMES_TO_NUMBERS[market_item.lower()]
                    selected_markets.append(market_number)
                else:
                    print(f"⚠️ Unknown market: {market_item}")
                    print("Available markets:", ", ".join(MARKET_NAMES_TO_NUMBERS.keys()))
                    return
            location_to_use = ""
        else:
            print("❌ Must specify either --market or --custom-location")
            return
        
        # Mode validation - minimum 50 jobs for meaningful results
        mode_configs = {
            "test": {"mode": "test", "limit": 10},
            "mini": {"mode": "mini", "limit": 50},
            "sample": {"mode": "sample", "limit": 100},
            "medium": {"mode": "medium", "limit": 250},
            "large": {"mode": "large", "limit": 500},
            "full": {"mode": "full", "limit": 1000}
        }
        
        if mode not in mode_configs:
            print(f"❌ Unknown mode: {mode}")
            print(f"Available modes: {', '.join(mode_configs.keys())}")
            return
        
        if route not in ["both", "local", "regional", "otr"]:
            print(f"❌ Unknown route filter: {route}")
            return
        
        mode_info = mode_configs[mode]
        search_terms = [term.strip() for term in terms.split(',')]
        
        location_display = custom_location if custom_location else f"{market} market"
        print(f"🚛 Quick Search: {location_display}")
        print(f"📊 Mode: {mode} ({mode_info['limit']} jobs)")
        print(f"🛣️ Routes: {route}")
        print(f"🔍 Terms: {', '.join(search_terms)}")
        print(f"🗃️ Airtable: {'Yes' if airtable else 'No'}")
        print("=" * 50)
        
        try:
            # Convert empty location_to_use back to None for predefined markets
            custom_location_param = location_to_use if location_to_use else None
            success = self.run_search(
                selected_markets=selected_markets,
                custom_location=custom_location_param,
                search_terms=search_terms,
                route_filter=route,
                airtable_upload=airtable,
                mode_info=mode_info,
                force_fresh=force_fresh,
                force_fresh_classification=force_fresh_classification,
                memory_only=memory_only,
                radius=radius,
                no_experience=no_experience,
                business_rules=business_rules,
                deduplication=deduplication,
                experience_filter=experience_filter,
                classification_model=classification_model,
                batch_size=batch_size,
                generate_pdf=generate_pdf,
                generate_csv=generate_csv,
                generate_html=generate_html,
                save_parquet=save_parquet,
                search_sources=search_sources,
                search_strategy=search_strategy,
                classifier_type=classifier_type
            )
            
            if success:
                print(f"\n🎉 Quick search completed!")
            else:
                print(f"\n❌ Quick search failed")
                
        except Exception as e:
            print(f"\n💥 Error: {e}")
            import traceback
            traceback.print_exc()

def main(generate_html: bool = False):
    parser = argparse.ArgumentParser(description='FreeWorld Job Scraper Enhanced Terminal Interface - Full GUI Feature Parity')
    
    # Location parameters
    parser.add_argument('--market', help='Target market (houston, dallas, etc.) - can specify multiple with commas')
    parser.add_argument('--custom-location', help='Custom location (90210, Austin TX, etc.)')
    
    # Search parameters
    parser.add_argument('--mode', choices=['test', 'mini', 'sample', 'medium', 'large', 'full'], default='sample', 
                       help='Search mode (default: sample)')
    parser.add_argument('--route', choices=['both', 'local', 'regional', 'otr'], default='both',
                       help='Route filter (default: both)')
    parser.add_argument('--terms', default='CDL Driver No Experience',
                       help='Search terms (comma-separated)')
    parser.add_argument('--radius', type=int, choices=[0, 25, 50, 100], default=50,
                       help='Search radius in miles (default: 50, use 0 for exact location)')
    parser.add_argument('--exact-location', action='store_true',
                       help='Search exact location only (sets radius=0, faster and more stable)')
    
    # Job source parameters
    parser.add_argument('--sources', choices=['indeed', 'google', 'both'], default='indeed',
                       help='Job sources to search (default: indeed)')
    parser.add_argument('--search-strategy', choices=['balanced', 'google_first', 'indeed_first'], default='balanced',
                       help='Multi-source search strategy when using both sources (default: balanced)')
    
    # Experience and filtering parameters
    parser.add_argument('--no-experience', action='store_true', default=True,
                       help='Filter for no experience required jobs (default: True)')
    parser.add_argument('--disable-no-experience', action='store_true',
                       help='Disable no experience filter')
    parser.add_argument('--enable-business-rules', action='store_true', default=True,
                       help='Enable business rules filtering (default: True)')
    parser.add_argument('--disable-business-rules', action='store_true',
                       help='Disable business rules filtering')
    parser.add_argument('--enable-deduplication', action='store_true', default=True,
                       help='Enable job deduplication (default: True)')
    parser.add_argument('--disable-deduplication', action='store_true',
                       help='Disable job deduplication')
    parser.add_argument('--enable-experience-filter', action='store_true', default=True,
                       help='Enable experience level filtering (default: True)')
    parser.add_argument('--disable-experience-filter', action='store_true',
                       help='Disable experience level filtering')
    
    # AI Classification parameters
    parser.add_argument('--classification-model', choices=['gpt-4o-mini', 'gpt-4o'], default='gpt-4o-mini',
                       help='AI classification model (default: gpt-4o-mini)')
    parser.add_argument('--batch-size', type=int, default=25,
                       help='AI processing batch size (default: 25)')
    parser.add_argument('--classifier-type', choices=['cdl', 'pathway'], default='cdl',
                       help='Job classifier type: cdl for traditional CDL jobs, pathway for career pathway jobs (default: cdl)')

    # Output parameters
    parser.add_argument('--generate-pdf', action='store_true', default=True,
                       help='Generate PDF report (default: True)')
    parser.add_argument('--no-pdf', action='store_true',
                       help='Disable PDF generation')
    parser.add_argument('--generate-csv', action='store_true', default=True,
                       help='Generate CSV export (default: True)')
    parser.add_argument('--no-csv', action='store_true',
                       help='Disable CSV generation')
    parser.add_argument('--generate-html', action='store_true', default=False,
                       help='Generate HTML portal (default: False)')
    parser.add_argument('--no-html', action='store_true',
                       help='Disable HTML generation')
    parser.add_argument('--save-parquet', action='store_true',
                       help='Save parquet checkpoint files (default: False)')
    parser.add_argument('--airtable', action='store_true', 
                       help='Upload results to Airtable')
    
    # Pipeline control parameters
    parser.add_argument('--force-fresh', action='store_true',
                       help='Force fresh scraping (ignore memory system)')
    parser.add_argument('--force-fresh-classification', action='store_true',
                       help='Force fresh AI classification (ignore classification cache)')
    parser.add_argument('--memory-only', action='store_true',
                       help='Force memory-only search (bypass all scraping)')
    
    # Utility parameters
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('--test-pipeline', action='store_true',
                       help='Run pipeline compatibility test')
    parser.add_argument('--dry-run', action='store_true',
                       help='Test run without API calls (shows what would be done)')
    
    args = parser.parse_args()
    
    # Handle test-pipeline mode
    if args.test_pipeline:
        print("🧪 Pipeline v3 Test")
        print("=" * 40)
        
        # Test secrets loading
        secrets_loaded = load_secrets()
        
        # Test required environment variables
        required_vars = ['OPENAI_API_KEY', 'OUTSCRAPER_API_KEY', 'SUPABASE_URL', 'SUPABASE_ANON_KEY']
        missing_vars = []
        
        for var in required_vars:
            if os.getenv(var):
                print(f"✅ {var}: Set")
            else:
                print(f"❌ {var}: Missing")
                missing_vars.append(var)
        
        # Test pipeline initialization  
        try:
            from pipeline_v3 import FreeWorldPipelineV3
            pipeline = FreeWorldPipelineV3()
            print("✅ Pipeline v3: Initialized successfully")
        except Exception as e:
            print(f"❌ Pipeline v3: Initialization failed - {e}")
        
        if missing_vars:
            print(f"\n⚠️ Missing environment variables: {', '.join(missing_vars)}")
            print("💡 Set these in .streamlit/secrets.toml or as environment variables")
        else:
            print("\n🎉 All systems ready!")
            
        return
    
    search = EnhancedTerminalJobSearch()
    
    if args.dry_run:
        print("\n🧪 DRY RUN MODE - No API calls will be made")
        print("=" * 50)
    
    if args.interactive or (not args.market and not args.custom_location):
        # Run interactive mode
        search.run_interactive(dry_run=args.dry_run)
    else:
        # Process argument logic for disable flags
        no_experience = args.no_experience and not args.disable_no_experience
        business_rules = args.enable_business_rules and not args.disable_business_rules
        
        # Handle exact location flag (overrides radius)
        radius = 0 if args.exact_location else args.radius
        if args.exact_location:
            print(f"📍 Exact location mode enabled (radius=0)")
        else:
            print(f"🔍 Using radius search ({radius} miles)")
        deduplication = args.enable_deduplication and not args.disable_deduplication
        experience_filter = args.enable_experience_filter and not args.disable_experience_filter
        generate_pdf = args.generate_pdf and not args.no_pdf
        generate_csv = args.generate_csv and not args.no_csv
        generate_html = args.generate_html and not args.no_html
        
        # Configure job sources
        if args.sources == 'indeed':
            search_sources = {'indeed': True, 'google': False}
        elif args.sources == 'google':
            search_sources = {'indeed': False, 'google': True}
        elif args.sources == 'both':
            search_sources = {'indeed': True, 'google': True}
        else:
            search_sources = {'indeed': True, 'google': False}  # Default fallback
        
        # Handle multiple markets
        markets = []
        if args.market:
            # Support comma-separated markets
            markets = [m.strip() for m in args.market.split(',')]
        
        # Run quick command mode
        search.run_quick_command(
            markets=markets,
            custom_location=args.custom_location,
            mode=args.mode,
            route=args.route,
            terms=args.terms,
            radius=radius,
            no_experience=no_experience,
            business_rules=business_rules,
            deduplication=deduplication,
            experience_filter=experience_filter,
            classification_model=args.classification_model,
            batch_size=args.batch_size,

            generate_pdf=generate_pdf,
            generate_csv=generate_csv,
            generate_html=generate_html,
            save_parquet=args.save_parquet,
            airtable=args.airtable,
            force_fresh=args.force_fresh,
            force_fresh_classification=args.force_fresh_classification,
            memory_only=args.memory_only,
            search_sources=search_sources,
            search_strategy=args.search_strategy,
            classifier_type=args.classifier_type,
            dry_run=args.dry_run
        )

if __name__ == "__main__":
    main()

# EDIT_APPLIED_2025_08_31_generate_html
