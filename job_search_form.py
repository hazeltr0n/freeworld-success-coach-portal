import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cost_calculator import CostCalculator
from job_scraper import FreeWorldJobScraper
from pipeline_v2 import FreeWorldJobPipeline
from multi_search_strategy import MultiSearchStrategy
from datetime import datetime

class JobSearchForm:
    def __init__(self):
        self.calculator = CostCalculator()
        self.scraper = FreeWorldJobScraper()
        self.pipeline = FreeWorldJobPipeline()
        self.multi_search = MultiSearchStrategy(self.scraper)
        
        # Market configuration for hardcoded market approach
        self.MARKET_SEARCH_QUERIES = {
            "Houston": "Houston, TX",
            "Dallas": "Dallas, TX", 
            "Bay Area": "San Francisco, CA",
            "Stockton": "Stockton, CA",
            "Denver": "Denver, CO",
            "Las Vegas": "Las Vegas, NV", 
            "Newark": "Newark, NJ",
            "Phoenix": "Phoenix, AZ",
            "Trenton": "Trenton, NJ",
            "Inland Empire": "Ontario, CA"
        }
    
    def build_indeed_url(self, job_terms, location, radius, no_experience=True):
        """Build Indeed search URL with all parameters"""
        base_url = "https://www.indeed.com/jobs"
        
        # Build query parameters
        params = []
        params.append(f"q={job_terms.replace(' ', '+')}")
        params.append(f"l={location.replace(' ', '+').replace(',', '%2C')}")
        params.append(f"radius={radius}")
        
        # Add entry level filter if requested
        if no_experience:
            params.append("sc=0kf%3Aexplvl%28ENTRY_LEVEL%29%3B")
        
        # Join all parameters
        url = base_url + "?" + "&".join(params)
        return url
    
    def show_market_selection(self):
        """Show market selection menu and return selected markets"""
        print("\n🗺️ Select Target Market(s):")
        markets = list(self.MARKET_SEARCH_QUERIES.keys())
        
        for i, market in enumerate(markets, 1):
            location = self.MARKET_SEARCH_QUERIES[market]
            print(f"  [{i:2}] {market} ({location})")
        
        print(f"\n💡 You can select multiple markets by separating numbers with commas")
        print(f"   Examples: '1' (single market) or '1,3,5' (multiple markets)")
        
        while True:
            try:
                choice = input(f"\nSelect market(s) (1-{len(markets)}): ").strip()
                
                # Parse comma-separated selections
                market_numbers = [int(num.strip()) for num in choice.split(',')]
                selected_markets = []
                selected_locations = []
                
                # Validate all selections
                for market_num in market_numbers:
                    if 1 <= market_num <= len(markets):
                        market_index = market_num - 1
                        selected_market = markets[market_index]
                        selected_location = self.MARKET_SEARCH_QUERIES[selected_market]
                        selected_markets.append(selected_market)
                        selected_locations.append(selected_location)
                    else:
                        print(f"❌ Invalid market number: {market_num} (must be 1-{len(markets)})")
                        break
                else:
                    # All selections valid
                    if selected_markets:
                        print(f"✅ Selected {len(selected_markets)} market(s):")
                        for market, location in zip(selected_markets, selected_locations):
                            print(f"   • {market} ({location})")
                        return selected_markets, selected_locations
                    else:
                        print(f"❌ No valid markets selected")
                        
            except ValueError:
                print(f"❌ Please enter valid numbers separated by commas (e.g., '1,3,5')")
    
    def get_user_input(self):
        """Get search parameters from user"""
        print("\n🚛 FreeWorld Job Search Tool")
        print("=" * 40)
        
        # Get search parameters - now support multiple queries
        job_terms = input("Job search terms (separate multiple queries with commas, e.g., 'CDL Driver, Truck Driver, Delivery Driver'): ").strip()
        if not job_terms:
            job_terms = "CDL Driver"
        
        # Get market selection - now supports multiple markets
        selected_markets, search_locations = self.show_market_selection()
        
        # No experience filter
        no_exp = input("\nInclude 'no experience required' filter? (y/n): ").strip().lower()
        no_experience = no_exp in ['y', 'yes']
        
        return {
            'job_terms': job_terms,
            'locations': search_locations,  # List of search locations
            'selected_markets': selected_markets,  # List of selected markets
            'radius': 50,  # Fixed at 50 miles
            'no_experience': no_experience,
            'search_indeed': True,
            'search_google': False
        }
    
    def show_search_modes(self):
        """Show cost estimates and let user choose mode"""
        print("\n💰 Search Mode Options:")
        
        print("\n🧪 [1] Test Mode:")
        print("     • 10 Indeed jobs per query")
        test_cost = self.calculator.estimate_search_cost(indeed_jobs=10, google_pages=0)
        print(f"     • Cost: ${test_cost:.2f} per market")
        
        print("\n📊 [2] Sample Mode:")
        print("     • 100 Indeed jobs per query")
        sample_cost = self.calculator.estimate_search_cost(indeed_jobs=100, google_pages=0)
        print(f"     • Cost: ${sample_cost:.2f} per market")
        
        print("\n🚀 [3] Full Mode:")
        print("     • 1000 Indeed jobs per query") 
        full_cost = self.calculator.estimate_search_cost(indeed_jobs=1000, google_pages=0)
        print(f"     • Cost: ${full_cost:.2f} per market")
        
        print("\n🔄 [4] Multi-Search Mode:")
        print("     • 3000+ jobs using multiple search variations")
        print("     • Overcomes Indeed's 1000 job limit")
        multi_cost = self.calculator.estimate_search_cost(indeed_jobs=1000, google_pages=0) * 3
        print(f"     • Cost: ${multi_cost:.2f} per market")
        
        print("\n🌟 [5] Maximum Multi-Search:")
        print("     • 5000+ jobs using extensive search variations") 
        print("     • Maximum job discovery across all variations")
        max_multi_cost = self.calculator.estimate_search_cost(indeed_jobs=1000, google_pages=0) * 5
        print(f"     • Cost: ${max_multi_cost:.2f} per market")
        
        # Get user choice
        mode_choice = input("\nChoose search mode (1, 2, 3, 4, or 5): ").strip()
        
        if mode_choice == "1":
            return {"mode": "test", "indeed_limit": 10, "google_pages": 0, "cost": test_cost, "multi_query": True, "use_multi_search": False}
        elif mode_choice == "2":
            return {"mode": "sample", "indeed_limit": 100, "google_pages": 0, "cost": sample_cost, "multi_query": True, "use_multi_search": False}
        elif mode_choice == "3":
            return {"mode": "full", "indeed_limit": 1000, "google_pages": 0, "cost": full_cost, "multi_query": True, "use_multi_search": False}
        elif mode_choice == "4":
            return {"mode": "multi-search", "indeed_limit": 1000, "google_pages": 0, "cost": multi_cost, "multi_query": False, "use_multi_search": True, "max_searches": 3}
        else:
            return {"mode": "maximum-multi", "indeed_limit": 1000, "google_pages": 0, "cost": max_multi_cost, "multi_query": False, "use_multi_search": True, "max_searches": 7}
    
    def show_route_filter_selection(self):
        """Show route type filter options"""
        print("\n=== ROUTE TYPE FILTER ===")
        print("1. Both (Local and OTR jobs)")
        print("2. Local only (Home daily)")
        print("3. OTR only (Over-the-road)")
        
        while True:
            try:
                choice = input("\nSelect route filter (1-3): ").strip()
                
                if choice == "1":
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
    
    def show_airtable_option(self):
        """Show Airtable push option"""
        print("\n=== AIRTABLE INTEGRATION ===")
        print("1. Export CSV files only (default)")
        print("2. Export CSV files AND push to Airtable")
        
        while True:
            try:
                choice = input("\nSelect export option (1-2): ").strip()
                
                if choice == "1" or choice == "":
                    print("✅ Selected: CSV files only")
                    return False
                elif choice == "2":
                    print("✅ Selected: CSV files + Airtable push")
                    return True
                else:
                    print("❌ Please enter 1 or 2")
            except ValueError:
                print("❌ Please enter a valid number")
    
    def confirm_search(self, search_params, mode_info, route_filter):
        """Show final confirmation before running search"""
        # Search source is always Indeed only
        sources_text = "Indeed"
        
        print("\n📋 Search Summary:")
        print(f"   Terms: {search_params['job_terms']}")
        
        # Handle multiple markets
        if len(search_params['selected_markets']) == 1:
            print(f"   Market: {search_params['selected_markets'][0]}")
            print(f"   Search Location: {search_params['locations'][0]}")
        else:
            print(f"   Markets: {len(search_params['selected_markets'])} markets selected")
            for market, location in zip(search_params['selected_markets'], search_params['locations']):
                print(f"     • {market} ({location})")
        
        print(f"   Radius: {search_params['radius']} miles")
        print(f"   No experience filter: {'Yes' if search_params['no_experience'] else 'No'}")
        print(f"   Search sources: {sources_text}")
        print(f"   Mode: {mode_info['mode'].title()}")
        
        # Show route filter
        route_filter_display = {
            "both": "Both Local and OTR jobs",
            "local": "Local jobs only (home daily)",
            "otr": "OTR jobs only (over-the-road)"
        }
        print(f"   Route Filter: {route_filter_display[route_filter]}")
        
        # Show multi-query and multi-market info
        queries = [q.strip() for q in search_params['job_terms'].split(',') if q.strip()]
        num_markets = len(search_params['selected_markets'])
        
        print(f"\n🔍 Search Scale:")
        print(f"   • {len(queries)} search term(s): {', '.join(queries)}")
        print(f"   • {num_markets} market(s)")
        
        if mode_info.get('use_multi_search', False):
            # Multi-search mode
            total_variations = len(queries) * num_markets * mode_info['max_searches']
            expected_jobs = total_variations * mode_info['indeed_limit'] * 0.7  # Account for deduplication
            print(f"   • Multi-Search: {mode_info['max_searches']} variations per query")
            print(f"   • Total search variations: {len(queries)} × {num_markets} × {mode_info['max_searches']} = {total_variations}")
            print(f"   • Expected unique jobs: ~{int(expected_jobs)}")
        else:
            # Standard mode
            total_searches = len(queries) * num_markets
            expected_jobs = total_searches * mode_info['indeed_limit']
            print(f"   • Total searches: {len(queries)} × {num_markets} = {total_searches}")
            print(f"   • Jobs per search: {mode_info['indeed_limit']}")
            print(f"   • Expected total jobs: ~{expected_jobs}")
        
        # Calculate estimated cost for all markets
        total_cost = mode_info['cost'] * num_markets
        print(f"   • Estimated cost: ${total_cost:.2f}")
        
        print(f"\n📄 Output:")
        print(f"   • Separate PDF report for each market ({num_markets} PDFs)")
        print(f"   • All files saved to Desktop")
        
        confirm = input("\nProceed with search? (y/n): ").strip().lower()
        return confirm in ['y', 'yes']
    
    def run_search_workflow(self):
        """Main workflow for the search form with continuous search and multi-market functionality"""
        print("🚛 FreeWorld Job Search Tool")
        print("=" * 40)
        
        while True:  # Main loop for multiple searches
            try:
                # Get search parameters (now includes multiple markets)
                search_params = self.get_user_input()
                
                # Get route filter selection
                route_filter = self.show_route_filter_selection()
                
                # Get Airtable push option
                push_to_airtable = self.show_airtable_option()
                
                # Show mode options with costs
                mode_info = self.show_search_modes()
                
                # Get final confirmation
                if not self.confirm_search(search_params, mode_info, route_filter):
                    print("Search cancelled.")
                    break
                
                print(f"\n🔍 Starting multi-market search...")
                print(f"🎯 Processing {len(search_params['selected_markets'])} market(s)")
                
                # Parse multiple queries from comma-separated input
                queries = [q.strip() for q in search_params['job_terms'].split(',') if q.strip()]
                
                all_market_results = []
                
                # Process each market separately
                for market_idx, (market, location) in enumerate(zip(search_params['selected_markets'], search_params['locations']), 1):
                    print(f"\n" + "=" * 60)
                    print(f"🗺️ MARKET {market_idx}/{len(search_params['selected_markets'])}: {market} ({location})")
                    print("=" * 60)
                    
                    market_results = []
                    
                    # Run all queries for this market
                    for query_idx, query in enumerate(queries, 1):
                        print(f"\n🔍 Search {query_idx}/{len(queries)} in {market}: '{query}'")
                        
                        # Build Indeed URL for this query and market
                        indeed_url = self.build_indeed_url(
                            query,
                            location, 
                            search_params['radius'],
                            search_params['no_experience']
                        )
                        
                        print(f"  🔗 Indeed URL: {indeed_url}")
                        
                        # Create search params for this query and market
                        query_params = {
                            'job_terms': query,
                            'location': location,
                            'selected_market': market,
                            'radius': search_params['radius'],
                            'no_experience': search_params['no_experience'],
                            'search_indeed': True,
                            'search_google': False,
                            'indeed_url': indeed_url
                        }
                        
                        # Run search for this query in this market
                        if mode_info.get('use_multi_search', False):
                            # Use MultiSearchStrategy for enhanced job discovery
                            print(f"  🔄 Using Multi-Search Strategy (max {mode_info['max_searches']} variations)")
                            query_results = self.multi_search.run_multi_search(
                                query_params, 
                                mode_info, 
                                max_searches=mode_info['max_searches']
                            )
                        else:
                            # Use standard single search
                            query_results = self.scraper.run_full_search(query_params, mode_info)
                        
                        if query_results is not None and len(query_results) > 0:
                            query_results['source_query'] = query  # Track which query found each job
                            query_results['source_market'] = market  # Track which market
                            market_results.append(query_results)
                            print(f"  ✅ Found {len(query_results)} jobs")
                        else:
                            print(f"  ❌ No jobs found for '{query}'")
                    
                    # Process this market's results
                    if market_results:
                        import pandas as pd
                        market_df = pd.concat(market_results, ignore_index=True)
                        print(f"\n📊 {market}: {len(market_df)} total jobs from {len(queries)} queries")
                        
                        # Remove duplicates for this market
                        if 'job_id' in market_df.columns:
                            initial_count = len(market_df)
                            market_df = market_df.drop_duplicates(subset=['job_id'])
                            print(f"  🔄 Removed {initial_count - len(market_df)} duplicates, {len(market_df)} unique jobs remaining")
                        
                        print(f"\n🧠 Processing {market} jobs through pipeline...")
                        
                        # Add selected market to raw results for hardcoded market approach
                        market_df['selected_market'] = market
                        
                        # Create temporary CSV file for pipeline processing
                        temp_filename = f"temp_raw_jobs_{market}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        temp_path = f"data/{temp_filename}"
                        os.makedirs("data", exist_ok=True)
                        market_df.to_csv(temp_path, index=False)
                        
                        # Process through enhanced pipeline with hardcoded market
                        pipeline_results = self.pipeline.run_full_pipeline(
                            [temp_path], 
                            f"form_search_{market.replace(' ', '_')}",
                            hardcoded_market=market,
                            route_filter=route_filter,
                            push_to_airtable=push_to_airtable,
                            use_smart_classification=True  # Enable smart classification by default
                        )
                        
                        # Clean up temp file
                        try:
                            os.remove(temp_path)
                        except (OSError, FileNotFoundError):
                            pass  # Ignore cleanup failures
                        
                        if pipeline_results:
                            print(f"  ✅ {market} pipeline completed!")
                            print(f"  📊 {pipeline_results['summary']['final_count']} final jobs from {pipeline_results['summary']['initial_count']} raw jobs")
                            print(f"  📈 Quality retention rate: {pipeline_results['summary']['retention_rate']:.1f}%")
                            
                            # Store results for summary
                            all_market_results.append({
                                'market': market,
                                'results': pipeline_results
                            })
                            
                            # Show brief breakdown for this market
                            final_df = pipeline_results['dataframe']
                            good_jobs = final_df[final_df['final_status'] == 'included']
                            
                            if len(good_jobs) > 0:
                                quality_counts = good_jobs['match'].value_counts()
                                quality_summary = ', '.join([f"{quality}: {count}" for quality, count in quality_counts.items()])
                                print(f"  🏆 Quality jobs: {quality_summary}")
                        else:
                            print(f"  ❌ {market} pipeline failed")
                    else:
                        print(f"\n❌ No jobs found for {market}")
                
                # Show final summary across all markets
                if all_market_results:
                    print(f"\n" + "=" * 60)
                    print(f"🎉 MULTI-MARKET SEARCH COMPLETE!")
                    print("=" * 60)
                    
                    total_jobs = sum(result['results']['summary']['final_count'] for result in all_market_results)
                    print(f"📊 Total quality jobs across all markets: {total_jobs}")
                    
                    print(f"\n📁 Generated Files:")
                    for market_result in all_market_results:
                        market = market_result['market']
                        files = market_result['results']['files']
                        job_count = market_result['results']['summary']['final_count']
                        print(f"\n  🗺️ {market} ({job_count} jobs):")
                        for file_type, file_path in files.items():
                            if file_path:
                                print(f"     • {file_type}: {os.path.basename(file_path)}")
                    
                    print(f"\n📂 All files saved to: ~/Desktop/FreeWorld_Jobs/")
                    
                else:
                    print("\n❌ No jobs found across any markets.")
                
                # Ask if user wants to run another search
                print(f"\n" + "=" * 50)
                while True:
                    another_search = input("Would you like to run another search? (y/n): ").lower().strip()
                    if another_search in ['y', 'yes']:
                        print(f"\n🚛 Starting new search...")
                        print("=" * 40)
                        break  # Break inner loop to start new search
                    elif another_search in ['n', 'no']:
                        print(f"\n✅ Thanks for using FreeWorld Job Search Tool!")
                        return  # Exit completely
                    else:
                        print("❌ Please enter 'y' for yes or 'n' for no")
                
            except KeyboardInterrupt:
                print("\n\nSearch cancelled by user.")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
                
                # Ask if they want to try again after error
                while True:
                    try_again = input("\nWould you like to try another search? (y/n): ").lower().strip()
                    if try_again in ['y', 'yes']:
                        break  # Continue to next iteration
                    elif try_again in ['n', 'no']:
                        return  # Exit completely
                    else:
                        print("❌ Please enter 'y' for yes or 'n' for no")
                
                if try_again in ['n', 'no']:
                    break
        
        # Keep console open
        input("\nPress Enter to exit...")

    def run_search(self, target_markets, locations, mode_info, search_terms, route_filter, airtable_upload=False, custom_market_name=None):
        """Execute the job search and processing pipeline for multiple markets"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"\n=== STARTING MULTI-MARKET JOB SEARCH ===")
        print(f"Timestamp: {timestamp}")
        print(f"Processing {len(target_markets)} market(s)")
        
        try:
            # Process each market separately using the pipeline
            for market_idx, (target_market, location) in enumerate(zip(target_markets, locations), 1):
                print(f"\n" + "=" * 60)
                print(f"🗺️ MARKET {market_idx}/{len(target_markets)}: {target_market} ({location})")
                print("=" * 60)
                
                # Use standard pipeline with proper market handling
                # For predefined markets: target_market is market name, custom_location is None
                # For custom locations: target_market is "Custom", custom_location is the location
                is_custom_location = (target_market == "Custom")
                
                results = self.pipeline.run_pipeline(
                    target_market=target_market,
                    location=location,
                    max_jobs=mode_info['limit'],
                    timestamp=timestamp,
                    use_form_prefix=True,
                    custom_search_terms=search_terms,
                    route_filter=route_filter,
                    airtable_upload=airtable_upload,
                    hardcoded_market=custom_market_name if custom_market_name else target_market,
                    custom_location=custom_market_name if is_custom_location else None
                )
                
                if results:
                    print(f"\n✅ {target_market} search complete!")
                    print(f"📊 Quality jobs included: {results['summary']['final_count'] if results and 'summary' in results else 'Unknown'}")
                else:
                    print(f"\n❌ {target_market} search failed")
                    
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return False
            
        return True

if __name__ == "__main__":
    form = JobSearchForm()
    form.run_search_workflow()