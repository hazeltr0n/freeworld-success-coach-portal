class CostCalculator:
    def __init__(self):
        # Outscraper flat rate pricing (per scraped job via Outscraper)
        # Indeed via Outscraper: $0.001 per scraped job
        # Google Jobs via Outscraper: $0.005 per scraped job
        self.indeed_cost_per_job = 0.001
        self.google_cost_per_job = 0.005
        
        # OpenAI classification cost (per job) 
        self.openai_cost_per_job = 0.0003  # $0.0003 per job for GPT-4o-mini
        
        # Legacy pricing tiers (kept for compatibility)
        self.indeed_tiers = [
            {'min': 1, 'max': 500, 'cost': 0.0},
            {'min': 501, 'max': 5000, 'cost': 0.002},
            {'min': 5001, 'max': float('inf'), 'cost': 0.001}
        ]
        
        # Google Careers pricing tiers (per search/page)
        self.google_tiers = [
            {'min': 1, 'max': 10, 'cost': 0.0},
            {'min': 11, 'max': 100000, 'cost': 0.005},
            {'min': 100001, 'max': float('inf'), 'cost': 0.003}
        ]
    
    def calculate_cost_from_scraped_jobs(self, indeed_jobs: int = 0, google_jobs: int = 0) -> float:
        """Calculate total cost purely from scraped jobs by source.

        Args:
            indeed_jobs: Number of jobs scraped from Indeed via Outscraper
            google_jobs: Number of jobs scraped from Google Jobs via Outscraper

        Returns:
            Total USD cost
        """
        indeed_jobs = max(0, int(indeed_jobs or 0))
        google_jobs = max(0, int(google_jobs or 0))
        return indeed_jobs * self.indeed_cost_per_job + google_jobs * self.google_cost_per_job
    
    def calculate_cost_bulk(self, num_jobs):
        """Calculate bulk scraping cost (Outscraper + OpenAI classification)"""
        if num_jobs <= 0:
            return 0.0
        
        # Legacy bulk estimate retained for compatibility; prefer calculate_cost_from_scraped_jobs
        # Assume indeed-like rate for rough bulk estimate
        scraping_cost = num_jobs * self.indeed_cost_per_job
        
        # OpenAI classification cost
        classification_cost = num_jobs * self.openai_cost_per_job
        
        return scraping_cost + classification_cost
    
    def calculate_indeed_cost(self, num_jobs):
        """Calculate cost for Indeed jobs based on pricing tiers"""
        if num_jobs <= 0:
            return 0.0
            
        total_cost = 0.0
        remaining_jobs = num_jobs
        
        for tier in self.indeed_tiers:
            if remaining_jobs <= 0:
                break
                
            # How many jobs fall in this tier?
            if tier['max'] == float('inf'):
                tier_capacity = remaining_jobs
            else:
                tier_capacity = min(remaining_jobs, tier['max'] - tier['min'] + 1)
                if tier['min'] > num_jobs:
                    continue
                tier_capacity = min(tier_capacity, tier['max'] - max(tier['min'], num_jobs - remaining_jobs + 1) + 1)
            
            jobs_in_tier = min(remaining_jobs, tier_capacity)
            tier_cost = jobs_in_tier * tier['cost']
            total_cost += tier_cost
            
            if jobs_in_tier > 0:
                print(f"  Indeed {tier['min']}-{tier['max'] if tier['max'] != float('inf') else '∞'}: {jobs_in_tier} jobs × ${tier['cost']:.3f} = ${tier_cost:.2f}")
            
            remaining_jobs -= jobs_in_tier
        
        return total_cost
    
    def calculate_google_cost_by_queries(self, num_queries):
        """Deprecated: Prefer per-scraped-job accounting.

        Kept for backwards compatibility if estimating via queries.
        """
        if num_queries <= 0:
            return 0.0
        return num_queries * self.google_cost_per_job
    
    def calculate_google_cost(self, num_pages):
        """Calculate cost for Google Careers pages based on pricing tiers (legacy method)"""
        if num_pages <= 0:
            return 0.0
            
        total_cost = 0.0
        remaining_pages = num_pages
        
        for tier in self.google_tiers:
            if remaining_pages <= 0:
                break
                
            # How many pages fall in this tier?
            if tier['max'] == float('inf'):
                tier_capacity = remaining_pages
            else:
                tier_capacity = min(remaining_pages, tier['max'] - tier['min'] + 1)
                if tier['min'] > num_pages:
                    continue
                tier_capacity = min(tier_capacity, tier['max'] - max(tier['min'], num_pages - remaining_pages + 1) + 1)
            
            pages_in_tier = min(remaining_pages, tier_capacity)
            tier_cost = pages_in_tier * tier['cost']
            total_cost += tier_cost
            
            if pages_in_tier > 0:
                print(f"  Google {tier['min']}-{tier['max'] if tier['max'] != float('inf') else '∞'}: {pages_in_tier} pages × ${tier['cost']:.3f} = ${tier_cost:.2f}")
            
            remaining_pages -= pages_in_tier
        
        return total_cost
    
    def estimate_search_cost(self, indeed_jobs=0, google_pages=0):
        """Estimate total search cost"""
        print(f"\n💰 Cost Breakdown:")
        
        # Indeed costs
        if indeed_jobs > 0:
            print(f"Indeed jobs requested: {indeed_jobs}")
            indeed_cost = indeed_jobs * self.indeed_cost_per_job
            print(f"Indeed total: ${indeed_cost:.2f}")
        else:
            indeed_cost = 0.0
        
        # Google costs  
        if google_pages > 0:
            print(f"Google Careers pages requested: {google_pages}")
            google_cost = self.calculate_google_cost(google_pages)
            print(f"Google total: ${google_cost:.2f}")
        else:
            google_cost = 0.0
        
        # OpenAI cost (accurate: $0.0003 per job for GPT-4o Mini)
        openai_cost = indeed_jobs * 0.0003 if indeed_jobs > 0 else 0.0
        if openai_cost > 0:
            print(f"OpenAI classification: ${openai_cost:.2f}")
        
        total_cost = indeed_cost + google_cost + openai_cost
        print(f"📊 TOTAL ESTIMATED COST: ${total_cost:.2f}")
        
        return total_cost
    
    def calculate_total_cost(self, num_jobs):
        """Calculate total estimated cost for a job search including OpenAI classification"""
        # OpenAI cost estimate for classification only (memory jobs)
        openai_cost = num_jobs * self.openai_cost_per_job if num_jobs > 0 else 0.0
        return openai_cost
    
    def show_mode_costs(self):
        """Show cost estimates for different search modes"""
        print("💰 Search Mode Cost Estimates:")
        
        print("\n🧪 Test Mode (10 Indeed jobs, 1 Google page):")
        test_cost = self.estimate_search_cost(indeed_jobs=10, google_pages=1)
        
        print("\n🚀 Full Mode (2000 Indeed jobs, 50 Google pages):")
        full_cost = self.estimate_search_cost(indeed_jobs=2000, google_pages=50)
        
        return {'test': test_cost, 'full': full_cost}

if __name__ == "__main__":
    calculator = CostCalculator()
    calculator.show_mode_costs()
