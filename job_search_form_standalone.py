import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set API keys directly in the code for standalone distribution
# SECURITY: API key should be set via environment variable or st.secrets
# os.environ['OPENAI_API_KEY'] = 'your-openai-api-key-here'
os.environ['OUTSCRAPER_API_KEY'] = 'NmY3ZWU2ZDY4ZDE3NDE3YWJhNzM2NzJlN2NkMzU5ZmV8MzQwNWIyYmQ2ZA'

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
        
        # Add no experience filter if requested
        if no_experience:
            params.append("sc=0kf%3Aattr%28D7S5D%29%3B")
        
        # Join all parameters
        url = base_url + "?" + "&".join(params)
        return url
    
    def show_market_selection(self):
        """Show market selection menu and return selected markets"""
        print("\n=== SELECT TARGET MARKET(S) ===")
        markets = list(self.MARKET_SEARCH_QUERIES.keys())
        
        for i, market in enumerate(markets, 1):
            location = self.MARKET_SEARCH_QUERIES[market]
            print(f"{i}. {market} ({location})")
        
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
    
    def get_search_terms(self):
        """Get custom search terms from user"""
        print("\n=== JOB SEARCH TERMS ===")
        print("Enter job search terms (separate multiple terms with commas)")
        print("Examples: 'CDL driver, truck driver' or 'delivery driver'")
        
        while True:
            terms_input = input("\nEnter search terms: ").strip()
            
            if not terms_input:
                print("❌ Please enter at least one search term")
                continue
                
            # Split by comma and clean up
            terms = [term.strip() for term in terms_input.split(',') if term.strip()]
            
            if terms:
                print(f"✅ Will search for: {', '.join(terms)}")
                return terms
            else:
                print("❌ Please enter valid search terms")
    
    def show_search_mode_selection(self):
        """Show search mode selection"""
        print("\n=== SEARCH MODE ===")
        print("1. Test (10 jobs) - Quick test")
        print("2. Sample (100 jobs) - Balanced search") 
        print("3. Medium (250 jobs) - Enhanced search")
        print("4. Large (500 jobs) - Extensive search")
        print("5. Full (1000 jobs) - Comprehensive search")
        
        while True:
            try:
                choice = input("\nEnter mode (1-5): ").strip()
                
                if choice == "1":
                    return {"mode": "test", "limit": 10, "use_multi_search": False}
                elif choice == "2": 
                    return {"mode": "sample", "limit": 100, "use_multi_search": False}
                elif choice == "3":
                    return {"mode": "medium", "limit": 250, "use_multi_search": False}
                elif choice == "4":
                    return {"mode": "large", "limit": 500, "use_multi_search": False}
                elif choice == "5":
                    return {"mode": "full", "limit": 1000, "use_multi_search": False}
                else:
                    print("❌ Please enter 1, 2, 3, 4, or 5")
            except ValueError:
                print("❌ Please enter a valid number")
    
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
    
    def show_search_configuration(self, target_markets, locations, mode_info, search_terms, route_filter):
        """Display the search configuration for confirmation"""
        print(f"\n=== SEARCH CONFIGURATION ===")
        
        # Handle multiple markets
        if len(target_markets) == 1:
            print(f"Market: {target_markets[0]}")
            print(f"Location: {locations[0]}")
        else:
            print(f"Markets: {len(target_markets)} markets selected")
            for market, location in zip(target_markets, locations):
                print(f"  • {market} ({location})")
        
        print(f"Mode: {mode_info['mode'].title()} ({mode_info['limit']} jobs per search)")
        if mode_info.get('use_multi_search'):
            print(f"Multi-Search: {mode_info['max_searches']} search variations enabled")
        print(f"Radius: 50 miles")
        print(f"Experience: No experience required filter enabled")
        
        # Show route filter
        route_filter_display = {
            "both": "Both Local and OTR jobs",
            "local": "Local jobs only (home daily)",
            "otr": "OTR jobs only (over-the-road)"
        }
        print(f"Route Filter: {route_filter_display[route_filter]}")
        
        # Show what queries will be used
        print(f"\nSearch terms that will be used:")
        for term in search_terms:
            print(f"  • {term}")
        
        # Calculate total search scale
        num_markets = len(target_markets)
        num_terms = len(search_terms)
        
        if mode_info.get('use_multi_search'):
            # Multi-search mode
            total_variations = num_markets * num_terms * mode_info['max_searches']
            expected_jobs = total_variations * mode_info['limit'] * 0.7  # Account for deduplication
            
            print(f"\n🔍 Multi-Search Scale:")
            print(f"  • {num_terms} search term(s)")
            print(f"  • {num_markets} market(s)")
            print(f"  • {mode_info['max_searches']} variations per term")
            print(f"  • Total search variations: {num_terms} × {num_markets} × {mode_info['max_searches']} = {total_variations}")
            print(f"  • Expected unique jobs: ~{int(expected_jobs)}")
        else:
            # Standard mode  
            total_searches = num_markets * num_terms
            expected_jobs = total_searches * mode_info['limit']
            
            print(f"\n🔍 Search Scale:")
            print(f"  • {num_terms} search term(s)")
            print(f"  • {num_markets} market(s)")
            print(f"  • Total searches: {num_terms} × {num_markets} = {total_searches}")
            print(f"  • Jobs per search: {mode_info['limit']}")
            print(f"  • Expected total jobs: ~{expected_jobs}")
        
        print(f"\nExpected API costs:")
        base_cost = mode_info['limit'] * 0.01  # Mock cost calculation
        if mode_info.get('use_multi_search'):
            total_cost = base_cost * mode_info['max_searches'] * num_markets
        else:
            total_cost = base_cost * num_markets
        print(f"  • OpenAI (classification): ~${total_cost:.2f}")
        print(f"  • Indeed scraping: Free")
        
        print(f"\n📄 Output:")
        print(f"  • Separate PDF report for each market ({num_markets} PDFs)")
        print(f"  • All files saved to Desktop")
        
        # Show sample URL
        sample_url = self.build_indeed_url(search_terms[0], locations[0], "50")
        print(f"\nSample Indeed URL:")
        print(f"  {sample_url}")
        
        confirm = input(f"\nProceed with this search? (y/n): ").lower().strip()
        return confirm in ['y', 'yes']
    
    def run_multi_search_pipeline(self, target_market, location, mode_info, timestamp, search_terms, route_filter, airtable_upload=False, custom_location=None, force_fresh=False):
        """Execute multi-search pipeline for enhanced job discovery"""
        print(f"🔄 Multi-Search Strategy for {target_market}")
        print(f"🎯 Base search terms: {', '.join(search_terms)}")
        
        all_jobs = []
        
        # Run multi-search for each provided search term
        for term_idx, search_term in enumerate(search_terms, 1):
            print(f"\n🔍 Multi-Search {term_idx}/{len(search_terms)}: '{search_term}'")
            
            # Create search parameters for this term
            search_params = {
                'job_terms': search_term,
                'location': location,
                'selected_market': target_market,
                'radius': 50,
                'no_experience': True
            }
            
            # Run multi-search for this term
            term_results = self.multi_search.run_multi_search(
                search_params, 
                mode_info, 
                max_searches=mode_info['max_searches']
            )
            
            if term_results is not None and len(term_results) > 0:
                # Add metadata
                term_results['source_search_term'] = search_term
                term_results['selected_market'] = target_market
                all_jobs.append(term_results)
                print(f"  ✅ Found {len(term_results)} unique jobs for '{search_term}'")
            else:
                print(f"  ❌ No jobs found for '{search_term}'")
        
        if not all_jobs:
            print(f"❌ No jobs found across all multi-search terms for {target_market}")
            return None
        
        # Combine all results
        import pandas as pd
        combined_df = pd.concat(all_jobs, ignore_index=True)
        
        print(f"\n📊 Multi-Search Results for {target_market}:")
        print(f"  • Total jobs collected: {len(combined_df)}")
        
        # Remove duplicates across all search terms
        if 'job_id' in combined_df.columns:
            initial_count = len(combined_df)
            combined_df = combined_df.drop_duplicates(subset='job_id', keep='first')
            duplicates_removed = initial_count - len(combined_df)
            print(f"  • Duplicates removed: {duplicates_removed}")
            print(f"  • Unique jobs: {len(combined_df)}")
        
        # Process through the full pipeline directly (no raw file saved)
        output_prefix = f"form_multi_search_results_{timestamp}"
        results = self.pipeline.run_full_pipeline_from_dataframe(combined_df, output_prefix, target_market, route_filter, push_to_airtable=airtable_upload, custom_location=custom_location)
        
        if results:
            results['search_terms'] = search_terms
            results['multi_search_variations'] = mode_info['max_searches']
            
        return results
    
    def run_search(self, target_markets, locations, mode_info, search_terms, route_filter, airtable_upload=False, market_name=None, custom_location=None):
        """Execute the job search and processing pipeline for multiple markets"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"\n=== STARTING MULTI-MARKET JOB SEARCH ===")
        print(f"Timestamp: {timestamp}")
        print(f"Processing {len(target_markets)} market(s)")
        
        all_market_results = []
        all_processed_dataframes = []  # For combined CSV
        
        try:
            # Process each market separately
            for market_idx, (target_market, location) in enumerate(zip(target_markets, locations), 1):
                print(f"\n" + "=" * 60)
                print(f"🗺️ MARKET {market_idx}/{len(target_markets)}: {target_market} ({location})")
                print("=" * 60)
                
                # Run the search using the pipeline with custom search terms for this market
                if mode_info.get('use_multi_search'):
                    # Use multi-search strategy for enhanced job discovery
                    print(f"🔄 Using Multi-Search Strategy with {mode_info['max_searches']} variations per term")
                    results = self.run_multi_search_pipeline(
                        target_market=target_market,
                        location=location,
                        mode_info=mode_info,
                        timestamp=timestamp,
                        search_terms=search_terms,
                        route_filter=route_filter,
                        airtable_upload=airtable_upload,
                        custom_location=custom_location,
                        force_fresh=getattr(self, 'force_fresh_jobs', False)
                    )
                else:
                    # Use standard pipeline
                    results = self.pipeline.run_pipeline(
                        target_market=target_market,
                        location=location,
                        max_jobs=mode_info['limit'],
                        timestamp=timestamp,
                        use_form_prefix=True,
                        custom_search_terms=search_terms,
                        route_filter=route_filter,
                        airtable_upload=airtable_upload,
                        custom_location=custom_location,
                        force_fresh=getattr(self, 'force_fresh_jobs', False)
                    )
                
                if results:
                    print(f"\n✅ {target_market} search complete!")
                    print(f"📊 Total jobs found: {results.get('total_jobs', 'Unknown')}")
                    print(f"📊 Quality jobs included: {results['summary']['final_count'] if results and 'summary' in results else 'Unknown'}")
                    
                    # Store results for summary and collect dataframe for combined CSV
                    all_market_results.append({
                        'market': target_market,
                        'results': results
                    })
                    
                    # Collect processed data for combined CSV
                    if 'dataframe' in results:
                        all_processed_dataframes.append(results['dataframe'])
                    
                    print(f"📁 Files created for {target_market}:")
                    for file_type, file_path in results.get('files', {}).items():
                        # Handle both string paths and nested structures
                        if isinstance(file_path, dict):
                            continue  # Skip dict entries (like airtable results)
                        if file_path and isinstance(file_path, str) and os.path.exists(file_path):
                            file_size = os.path.getsize(file_path) / 1024  # KB
                            print(f"   • {file_type}: {os.path.basename(file_path)} ({file_size:.1f} KB)")
                        elif isinstance(file_path, list):
                            for i, path in enumerate(file_path):
                                if path and isinstance(path, str) and os.path.exists(path):
                                    file_size = os.path.getsize(path) / 1024  # KB
                                    print(f"   • {file_type}[{i}]: {os.path.basename(path)} ({file_size:.1f} KB)")
                else:
                    print(f"\n❌ {target_market} search failed")
            
            # Show final summary across all markets
            if all_market_results:
                print(f"\n" + "=" * 60)
                print(f"🎉 MULTI-MARKET SEARCH COMPLETE!")
                print("=" * 60)
                
                # Handle different result structures safely
                total_jobs = 0
                for result in all_market_results:
                    if result['results']:
                        if 'summary' in result['results']:
                            total_jobs += result['results']['summary']['final_count']
                        elif 'dataframe' in result['results']:
                            total_jobs += len(result['results']['dataframe'])
                
                print(f"📊 Total quality jobs across all markets: {total_jobs}")
                
                # Create combined CSV for multi-market search
                if len(all_processed_dataframes) > 1:
                    print(f"\n📊 Creating combined CSV from {len(all_processed_dataframes)} markets...")
                    import pandas as pd
                    combined_df = pd.concat(all_processed_dataframes, ignore_index=True)
                    
                    # Remove duplicates across markets (in case same job appears in multiple markets)
                    initial_count = len(combined_df)
                    combined_df = combined_df.drop_duplicates(subset='job_id', keep='first')
                    deduped_count = initial_count - len(combined_df)
                    if deduped_count > 0:
                        print(f"  ♻️ Removed {deduped_count} cross-market duplicates")
                    
                    # Export combined CSV using file processor
                    markets_str = "-".join([result['market'].replace(" ", "") for result in all_market_results])
                    if len(markets_str) > 50:  # If too long, use a shorter name
                        markets_str = f"{len(all_market_results)}Markets"
                    
                    base_filename = f"form_search_results_{markets_str}"
                    self.pipeline.file_processor.export_results(
                        combined_df, 
                        base_filename, 
                        self.pipeline.output_dir, 
                        combined_csv_data=combined_df
                    )
                
                print(f"\n📁 Generated Files:")
                for market_result in all_market_results:
                    market = market_result['market']
                    files = market_result['results'].get('files', {})
                    # Handle different result structures - new pipeline doesn't have 'summary' field
                    if market_result['results'] and 'summary' in market_result['results']:
                        job_count = market_result['results']['summary']['final_count'] 
                    elif market_result['results'] and 'dataframe' in market_result['results']:
                        job_count = len(market_result['results']['dataframe'])
                    else:
                        job_count = 0
                    print(f"\n  🗺️ {market} ({job_count} jobs):")
                    for file_type, file_path in files.items():
                        if file_path and isinstance(file_path, str):
                            print(f"     • {file_type}: {os.path.basename(file_path)}")
                        elif isinstance(file_path, dict):
                            # Handle dict case (like airtable results)
                            continue
                
                print(f"\n📂 PDFs saved in market-specific folders")
                print(f"📂 CSVs saved in centralized CSVs folder")
                return True
            else:
                print(f"\n❌ No successful searches across any markets")
                return False
            
        except Exception as e:
            print(f"\n❌ Search failed: {str(e)}")
            print(f"Error details: {type(e).__name__}")
            return False
    
    def run(self):
        """Main application loop with option to run multiple searches and multi-market functionality"""
        print("🚛 FreeWorld Job Scraper v1.0")
        print("=" * 50)
        
        while True:  # Main loop for multiple searches
            try:
                # Step 1: Select market(s) - now supports multiple
                target_markets, locations = self.show_market_selection()
                
                # Step 2: Get search terms
                search_terms = self.get_search_terms()
                
                # Step 3: Select route type filter
                route_filter = self.show_route_filter_selection()
                
                # Step 4: Select search mode  
                mode_info = self.show_search_mode_selection()
                
                # Step 5: Show configuration and get confirmation
                if not self.show_search_configuration(target_markets, locations, mode_info, search_terms, route_filter):
                    print("❌ Search cancelled by user")
                    break
                
                # Step 6: Run the search for all selected markets
                success = self.run_search(target_markets, locations, mode_info, search_terms, route_filter)
                
                if success:
                    print(f"\n🎉 Multi-market search completed successfully!")
                    print(f"📁 Results saved to: ~/Desktop/FreeWorld_Jobs/")
                    print(f"   Check your Desktop for the 'FreeWorld_Jobs' folder")
                    print(f"   Separate PDF reports generated for each market")
                else:
                    print(f"\n❌ Search failed - check error messages above")
                
                # Step 6: Ask if user wants to run another search
                print(f"\n" + "=" * 50)
                while True:
                    another_search = input("Would you like to run another search? (y/n): ").lower().strip()
                    if another_search in ['y', 'yes']:
                        print(f"\n🚛 Starting new search...")
                        print("=" * 50)
                        break  # Break inner loop to start new search
                    elif another_search in ['n', 'no']:
                        print(f"\n✅ Thanks for using FreeWorld Job Scraper!")
                        return  # Exit completely
                    else:
                        print("❌ Please enter 'y' for yes or 'n' for no")
                        
            except KeyboardInterrupt:
                print(f"\n❌ Search cancelled by user (Ctrl+C)")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {str(e)}")
                print(f"Error type: {type(e).__name__}")
                
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

if __name__ == "__main__":
    form = JobSearchForm()
    form.run()