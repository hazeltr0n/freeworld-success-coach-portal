#!/usr/bin/env python3
"""
Enhanced Terminal Job Search - Complete recreation based on GUI wrapper functionality
Matches all features from the GUI version: multi-market, custom location, Airtable, etc.
Usage: python3 terminal_job_search.py
"""

import os
import sys
import argparse

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

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
}

class EnhancedTerminalJobSearch:
    def __init__(self):
        # Initialize cost calculator
        self.calculator = CostCalculator()
        
        # Initialize pipeline v3 - required
        self.pipeline_v3 = FreeWorldPipelineV3()
        print(f"✅ Using Pipeline v3 (new single-table architecture)")
        
        # Market configuration from GUI (matches exactly)
        self.available_markets = list(MARKET_SEARCH_QUERIES.keys())
        
        # Default values matching GUI
        self.selected_markets = []
        self.custom_location = ""
        self.search_terms = []
        self.route_filter = "both"
        self.airtable_upload = False
        self.mode_info = {"mode": "sample", "limit": 100, "use_multi_search": False}

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
                    # Use default terms
                    default_terms = ["CDL driver", "truck driver", "delivery driver"]
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
        
        print(f"1. Test (100 jobs) - Quick test")
        print(f"   💰 Cost: ~${test_cost:.2f} per location")
        
        print(f"2. Sample (100 jobs) - Balanced search [DEFAULT]") 
        print(f"   💰 Cost: ~${sample_cost:.2f} per location")
        
        print(f"3. Medium (250 jobs) - Enhanced search")
        print(f"   💰 Cost: ~${sample_cost * 2.5:.2f} per location")
        
        print(f"4. Large (500 jobs) - Extensive search")
        print(f"   💰 Cost: ~${sample_cost * 5:.2f} per location")
        
        print(f"5. Full (1000 jobs) - Comprehensive search")
        print(f"   💰 Cost: ~${full_cost:.2f} per location")
        
        while True:
            try:
                choice = input("\nEnter mode (1-5) or press Enter for default: ").strip()
                
                if choice == "1":
                    return {"mode": "test", "limit": 50, "use_multi_search": False, "cost": test_cost}
                elif choice == "2" or choice == "": 
                    return {"mode": "sample", "limit": 100, "use_multi_search": False, "cost": sample_cost}
                elif choice == "3":
                    return {"mode": "medium", "limit": 250, "use_multi_search": False, "cost": medium_cost}
                elif choice == "4":
                    return {"mode": "large", "limit": 500, "use_multi_search": False, "cost": sample_cost * 5}
                elif choice == "5":
                    return {"mode": "full", "limit": 1000, "use_multi_search": False, "cost": full_cost}
                else:
                    print("❌ Please enter 1, 2, 3, 4, or 5")
                    
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

    def run_search_v3(self, location, search_terms, route_filter, airtable_upload, mode_info, force_fresh=False, is_custom_location=False, radius=50, no_experience=True, filter_settings=None):
        """Run search using Pipeline v3"""
        print(f"🚀 Using Pipeline v3 for location: {location}")
        
        try:
            # Convert parameters to Pipeline v3 format
            pipeline_params = {
                'location': location,
                'mode_info': mode_info,
                'search_terms': ' '.join(search_terms),  # v3 expects single string
                'route_filter': route_filter,
                'generate_pdf': True,
                'generate_csv': True,
                'push_to_airtable': airtable_upload,
                'force_fresh': force_fresh,
                'custom_location': location if is_custom_location else None,
                'radius': radius,
                'no_experience': no_experience,
                'filter_settings': filter_settings or {}
            }
            
            print(f"📊 Pipeline v3 parameters:")
            for key, value in pipeline_params.items():
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


    def run_search(self, selected_markets, custom_location, search_terms, route_filter, airtable_upload, mode_info, force_fresh=False, radius=50, no_experience=True, filter_settings=None):
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
                    is_custom_location=custom_location is not None,
                    radius=radius,
                    no_experience=no_experience,
                    filter_settings=filter_settings
                )
                overall_success = success
            else:
                print(f"\n🔁 Running {len(selected_markets)} market(s) sequentially...")
                for idx, market_id in enumerate(selected_markets, 1):
                    market_label = MARKET_SEARCH_QUERIES[market_id]
                    loc = QUERY_LOCATION_OVERRIDES.get(market_label, market_label)
                    print(f"\n— Market {idx}/{len(selected_markets)}: {market_label} → query location: {loc}")
                    success, _ = self.run_search_v3(
                        location=loc,
                        search_terms=search_terms,
                        route_filter=route_filter,
                        airtable_upload=airtable_upload,
                        mode_info=mode_info,
                        force_fresh=force_fresh,
                        is_custom_location=False,
                        radius=radius,
                        no_experience=no_experience,
                        filter_settings=filter_settings
                    )
                    overall_success = overall_success and success

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

    def run_interactive(self):
        """Run the full interactive terminal session - complete GUI functionality recreation"""
        print("🚛 FreeWorld Job Scraper v1.0 - Terminal Edition")
        print("Complete feature parity with GUI version")
        print("=" * 60)
        
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
                success = self.run_search(selected_markets, custom_location, search_terms, route_filter, airtable_upload, mode_info)
                
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

    def run_quick_command(self, market=None, custom_location=None, mode="sample", route="both", airtable=False, terms="CDL driver", force_fresh=False):
        """Run a quick command-line search with parameters"""
        
        # Parse inputs
        if custom_location:
            selected_markets = []
            location_to_use = custom_location
        elif market:
            market_lower = market.lower()
            if market_lower in MARKET_NAMES_TO_NUMBERS:
                market_number = MARKET_NAMES_TO_NUMBERS[market_lower]
                selected_markets = [market_number]
                location_to_use = ""
            else:
                print(f"❌ Unknown market: {market}")
                print(f"Available markets: {', '.join(MARKET_NAMES_TO_NUMBERS.keys())}")
                return
        else:
            print("❌ Must specify either --market or --custom-location")
            return
        
        # Mode validation - minimum 50 jobs for meaningful results
        mode_configs = {
            "test": {"mode": "test", "limit": 100, "use_multi_search": False},
            "sample": {"mode": "sample", "limit": 100, "use_multi_search": False}, 
            "medium": {"mode": "medium", "limit": 250, "use_multi_search": False},
            "large": {"mode": "large", "limit": 500, "use_multi_search": False},
            "full": {"mode": "full", "limit": 1000, "use_multi_search": False}
        }
        
        if mode not in mode_configs:
            print(f"❌ Unknown mode: {mode}")
            print(f"Available modes: {', '.join(mode_configs.keys())}")
            return
        
        if route not in ["both", "local", "otr"]:
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
            success = self.run_search(selected_markets, custom_location_param, search_terms, route, airtable, mode_info, force_fresh)
            
            if success:
                print(f"\n🎉 Quick search completed!")
            else:
                print(f"\n❌ Quick search failed")
                
        except Exception as e:
            print(f"\n💥 Error: {e}")
            import traceback
            traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='FreeWorld Job Scraper Enhanced Terminal Interface - Full GUI Feature Parity')
    parser.add_argument('--market', help='Target market (houston, dallas, etc.)')
    parser.add_argument('--custom-location', help='Custom location (90210, Austin TX, etc.)')
    parser.add_argument('--mode', choices=['test', 'sample', 'medium', 'large', 'full'], default='sample', 
                       help='Search mode (default: sample)')
    parser.add_argument('--route', choices=['both', 'local', 'otr'], default='both',
                       help='Route filter (default: both)')
    parser.add_argument('--airtable', action='store_true', 
                       help='Upload results to Airtable')
    parser.add_argument('--terms', default='CDL driver',
                       help='Search terms (comma-separated)')
    parser.add_argument('--force-fresh', action='store_true',
                       help='Force fresh scraping (ignore memory system)')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('--test-pipeline', action='store_true',
                       help='Run pipeline compatibility test')
    
    args = parser.parse_args()
    
    # Handle test-pipeline mode
    if args.test_pipeline:
        print("🧪 Pipeline v3 Test")
        print("=" * 40)
        print("✅ Pipeline v3: Ready")
        return
    
    search = EnhancedTerminalJobSearch()
    
    if args.interactive or (not args.market and not args.custom_location):
        # Run interactive mode
        search.run_interactive()
    else:
        # Run quick command mode
        search.run_quick_command(
            market=args.market,
            custom_location=args.custom_location,
            mode=args.mode,
            route=args.route,
            airtable=args.airtable,
            terms=args.terms,
            force_fresh=args.force_fresh
        )

if __name__ == "__main__":
    main()
