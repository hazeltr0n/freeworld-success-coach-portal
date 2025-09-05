#!/usr/bin/env python3
"""
Multi-search strategy to overcome Indeed's 1000 job limit per query
"""
import pandas as pd
import time
from datetime import datetime

class MultiSearchStrategy:
    def __init__(self, scraper):
        self.scraper = scraper
        
        # Search variation strategies focused on entry-level positions
        self.experience_filters = [
            "entry level",
            "no experience", 
            "training provided",
            "new driver welcome"
        ]
        
        self.job_type_variations = [
            "CDL driver no experience",
            "entry level truck driver", 
            "CDL training provided",
            "new CDL driver",
            "CDL driver trainee",
            "commercial driver entry level"
        ]
        
        self.radius_variations = [25, 50, 75]
        
    def build_search_variations(self, base_job_terms, location, selected_market):
        """Build multiple search variations to overcome 1000 job limit"""
        variations = []
        
        # Strategy 1: Different job title variations
        for job_variation in self.job_type_variations:
            variation = {
                'job_terms': job_variation,
                'location': location,
                'selected_market': selected_market,
                'strategy': f'job_type:{job_variation}',
                'radius': 50
            }
            variations.append(variation)
        
        # Strategy 2: Different radius searches for the base term
        for radius in self.radius_variations:
            variation = {
                'job_terms': base_job_terms,
                'location': location, 
                'selected_market': selected_market,
                'strategy': f'radius:{radius}',
                'radius': radius
            }
            variations.append(variation)
        
        # Strategy 3: Experience level variations
        for exp_filter in self.experience_filters:
            variation = {
                'job_terms': f"{base_job_terms} {exp_filter}",
                'location': location,
                'selected_market': selected_market,
                'strategy': f'experience:{exp_filter}',
                'radius': 50
            }
            variations.append(variation)
        
        return variations
    
    def run_multi_search(self, search_params, mode_info, max_searches=5):
        """
        Run multiple search variations to get more than 1000 jobs
        
        Args:
            search_params: Base search parameters
            mode_info: Mode configuration
            max_searches: Maximum number of search variations to run
        """
        print(f"\n🔄 Multi-Search Strategy: Overcoming Indeed's 1000 job limit")
        print("=" * 60)
        
        # Build search variations
        variations = self.build_search_variations(
            search_params['job_terms'],
            search_params['location'], 
            search_params['selected_market']
        )
        
        # Limit the number of searches to prevent excessive API usage
        variations = variations[:max_searches]
        
        print(f"📋 Running {len(variations)} search variations:")
        for i, var in enumerate(variations, 1):
            print(f"  {i}. {var['strategy']}: '{var['job_terms']}' (r={var['radius']})")
        
        all_jobs = []
        search_results = []
        
        for i, variation in enumerate(variations, 1):
            print(f"\n🔍 Search {i}/{len(variations)}: {variation['strategy']}")
            
            # Build Indeed URL for this variation
            indeed_url = self._build_indeed_url(
                variation['job_terms'],
                variation['location'],
                variation['radius'],
                search_params.get('no_experience', False)
            )
            
            # Search Indeed with this variation
            jobs = self.scraper.search_indeed_jobs(indeed_url, mode_info['indeed_limit'])
            
            if jobs:
                # Add metadata to jobs
                df = pd.DataFrame(jobs)
                df['search_variation'] = variation['strategy']
                df['search_terms'] = variation['job_terms']
                df['selected_market'] = variation['selected_market']
                
                all_jobs.append(df)
                search_results.append({
                    'strategy': variation['strategy'],
                    'job_count': len(jobs),
                    'search_terms': variation['job_terms']
                })
                
                print(f"  ✅ Found {len(jobs)} jobs")
            else:
                print(f"  ❌ No jobs found")
                search_results.append({
                    'strategy': variation['strategy'], 
                    'job_count': 0,
                    'search_terms': variation['job_terms']
                })
            
            # Rate limiting between searches
            if i < len(variations):
                print("  ⏸️  Waiting 2 seconds between searches...")
                time.sleep(2)
        
        # Combine all results
        if all_jobs:
            combined_df = pd.concat(all_jobs, ignore_index=True)
            
            # Show summary
            print(f"\n📊 Multi-Search Results Summary:")
            print(f"  Total raw jobs collected: {len(combined_df)}")
            
            for result in search_results:
                print(f"  • {result['strategy']}: {result['job_count']} jobs")
            
            # Remove duplicates across searches
            print(f"\n🔄 Removing duplicates across searches...")
            initial_count = len(combined_df)
            
            # Generate job IDs for deduplication
            combined_df['job_id'] = combined_df.apply(
                lambda x: self.scraper._generate_job_id(x['company'], x['location'], x['job_title']), 
                axis=1
            )
            
            # Remove duplicates by job_id
            combined_df = combined_df.drop_duplicates(subset='job_id', keep='first')
            final_count = len(combined_df)
            
            duplicates_removed = initial_count - final_count
            print(f"  🗑️  Removed {duplicates_removed} duplicate jobs")
            print(f"  ✅ Final unique jobs: {final_count}")
            
            return combined_df
        else:
            print("\n❌ No jobs found across all search variations")
            return None
    
    def _build_indeed_url(self, job_terms, location, radius, no_experience=True):
        """Build Indeed search URL with parameters"""
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

if __name__ == "__main__":
    # Test the multi-search strategy
    import sys
    import os
    sys.path.append('src')
    
    from job_scraper import FreeWorldJobScraper
    
    scraper = FreeWorldJobScraper()
    strategy = MultiSearchStrategy(scraper)
    
    # Test search parameters
    test_params = {
        'job_terms': 'CDL Driver',
        'location': 'Dallas, TX',
        'selected_market': 'Dallas',
        'no_experience': True
    }
    
    test_mode = {'indeed_limit': 1000}
    
    print("🧪 Testing Multi-Search Strategy")
    results = strategy.run_multi_search(test_params, test_mode, max_searches=3)
    
    if results is not None:
        print(f"\n🎯 Test completed: {len(results)} unique jobs found")
    else:
        print("\n❌ Test failed: No jobs found")