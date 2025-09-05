"""
Career Coach Interface for Natural Language Job Search Requests
Processes user requirements like "free agent with travel restrictions needs local job"
and translates them into optimized search strategies.
"""

import os
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import openai
from datetime import datetime

from query_optimizer import QueryOptimizer

logger = logging.getLogger(__name__)

@dataclass
class JobRequirements:
    """Structured job requirements extracted from natural language"""
    route_preference: str  # "local", "otr", "regional", "flexible"
    experience_level: str  # "new", "experienced", "expert"
    special_requirements: List[str]  # ["no_felonies", "home_daily", "cdl_a", etc.]
    location_flexibility: str  # "restricted", "regional", "nationwide"
    job_type_preferences: List[str]  # ["delivery", "freight", "tanker", etc.]
    salary_expectations: Optional[str]
    schedule_preferences: List[str]  # ["day_shift", "flexible", "no_weekends"]

class CareerCoach:
    """AI-powered career coach for personalized job search strategies"""
    
    def __init__(self):
        """Initialize career coach with AI capabilities"""
        self.query_optimizer = QueryOptimizer()
        self.client = None
        self._init_openai()
        
        # Common requirement mappings
        self.route_keywords = {
            'local': ['local', 'home daily', 'no overnight', 'city', 'delivery', 'home every night'],
            'otr': ['over the road', 'otr', 'long haul', 'nationwide', 'cross country', 'weeks out'],
            'regional': ['regional', 'multi-state', 'home weekly', 'home weekends'],
            'dedicated': ['dedicated', 'dedicated route', 'same customers']
        }
        
        self.experience_keywords = {
            'new': ['new driver', 'recent graduate', 'cdl school', 'entry level', 'training'],
            'experienced': ['experienced', '2+ years', 'seasoned', 'skilled'],
            'expert': ['expert', 'trainer', 'lead driver', '5+ years', 'senior']
        }
        
        self.restriction_keywords = {
            'travel_restricted': ['travel restrictions', 'cannot travel', 'local only', 'home daily required'],
            'background_sensitive': ['background check', 'felony friendly', 'fair chance', 'second chance'],
            'cdl_class': ['cdl a', 'cdl b', 'class a', 'class b'],
            'endorsement_needs': ['hazmat', 'tanker', 'passenger', 'doubles', 'triples']
        }
    
    def _init_openai(self):
        """Initialize OpenAI client for natural language processing"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OpenAI API key not found - using rule-based processing only")
                return
            
            openai.api_key = api_key
            self.client = openai
            logger.info("✅ OpenAI client initialized for career coaching")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            self.client = None
    
    def process_natural_language_request(self, user_input: str, target_market: str = None) -> Dict:
        """
        Process natural language job search request and return personalized strategy
        
        Args:
            user_input: Natural language description like "free agent with travel restrictions needs local job"
            target_market: Optional target market for location-specific optimization
            
        Returns:
            Dictionary with personalized job search strategy
        """
        logger.info(f"Processing career coach request: '{user_input}'")
        
        # Step 1: Extract structured requirements
        requirements = self._extract_requirements(user_input)
        
        # Step 2: Generate personalized search strategy
        strategy = self._generate_personalized_strategy(requirements, target_market)
        
        # Step 3: Get optimized queries based on requirements
        optimized_queries = self._get_optimized_queries(requirements, target_market)
        
        # Step 4: Provide coaching advice
        coaching_advice = self._generate_coaching_advice(requirements, strategy)
        
        return {
            'user_request': user_input,
            'target_market': target_market,
            'extracted_requirements': requirements,
            'personalized_strategy': strategy,
            'optimized_queries': optimized_queries,
            'coaching_advice': coaching_advice,
            'generated_at': datetime.now().isoformat()
        }
    
    def _extract_requirements(self, user_input: str) -> JobRequirements:
        """
        Extract structured requirements from natural language input
        
        Args:
            user_input: Natural language job search request
            
        Returns:
            JobRequirements object with structured data
        """
        input_lower = user_input.lower()
        
        # Extract route preference
        route_preference = "flexible"
        for route_type, keywords in self.route_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                route_preference = route_type
                break
        
        # Extract experience level
        experience_level = "experienced"  # Default assumption
        for exp_level, keywords in self.experience_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                experience_level = exp_level
                break
        
        # Extract special requirements
        special_requirements = []
        for requirement_type, keywords in self.restriction_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                special_requirements.append(requirement_type)
        
        # Extract location flexibility
        location_flexibility = "regional"  # Default
        if any(keyword in input_lower for keyword in ['travel restrictions', 'cannot travel', 'local only']):
            location_flexibility = "restricted"
        elif any(keyword in input_lower for keyword in ['nationwide', 'anywhere', 'flexible location']):
            location_flexibility = "nationwide"
        
        # Extract job type preferences
        job_type_preferences = []
        job_types = {
            'delivery': ['delivery', 'courier', 'package'],
            'freight': ['freight', 'cargo', 'shipping'],
            'tanker': ['tanker', 'liquid', 'chemical'],
            'flatbed': ['flatbed', 'construction', 'equipment'],
            'refrigerated': ['refrigerated', 'reefer', 'food transport']
        }
        
        for job_type, keywords in job_types.items():
            if any(keyword in input_lower for keyword in keywords):
                job_type_preferences.append(job_type)
        
        # Extract schedule preferences
        schedule_preferences = []
        schedule_keywords = {
            'day_shift': ['day shift', 'days only', 'no nights'],
            'flexible': ['flexible schedule', 'any shift'],
            'no_weekends': ['no weekends', 'weekdays only', 'monday through friday']
        }
        
        for schedule_type, keywords in schedule_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                schedule_preferences.append(schedule_type)
        
        # Extract salary expectations (basic pattern matching)
        salary_expectations = None
        salary_patterns = [
            r'\$(\d+(?:,\d+)?)\s*(?:per\s+)?(?:hour|hr)',
            r'\$(\d+(?:,\d+)?)\s*(?:per\s+)?(?:year|annually)',
            r'(\d+)\s*(?:per\s+)?(?:hour|hr)',
            r'over\s+\$(\d+(?:,\d+)?)',
            r'at\s+least\s+\$(\d+(?:,\d+)?)'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, input_lower)
            if match:
                salary_expectations = match.group(0)
                break
        
        requirements = JobRequirements(
            route_preference=route_preference,
            experience_level=experience_level,
            special_requirements=special_requirements,
            location_flexibility=location_flexibility,
            job_type_preferences=job_type_preferences,
            salary_expectations=salary_expectations,
            schedule_preferences=schedule_preferences
        )
        
        logger.info(f"Extracted requirements: route={route_preference}, experience={experience_level}, "
                   f"restrictions={len(special_requirements)}, job_types={len(job_type_preferences)}")
        
        return requirements
    
    def _generate_personalized_strategy(self, requirements: JobRequirements, target_market: str) -> Dict:
        """
        Generate a personalized job search strategy based on requirements
        
        Args:
            requirements: Structured job requirements
            target_market: Target market for search
            
        Returns:
            Personalized strategy dictionary
        """
        strategy = {
            'primary_focus': [],
            'secondary_options': [],
            'markets_to_prioritize': [],
            'search_approach': 'balanced',  # 'aggressive', 'balanced', 'conservative'
            'timeline_estimate': '2-4 weeks',
            'success_probability': 'high'  # 'high', 'medium', 'low'
        }
        
        # Determine primary focus based on route preference
        if requirements.route_preference == 'local':
            strategy['primary_focus'].extend([
                'Home daily positions',
                'Local delivery routes', 
                'City/municipal driving jobs',
                'LTL (Less Than Truckload) positions'
            ])
            strategy['search_approach'] = 'targeted'
            
        elif requirements.route_preference == 'otr':
            strategy['primary_focus'].extend([
                'Over-the-road opportunities',
                'Long haul positions',
                'Cross-country routes',
                'Team driving opportunities'
            ])
            strategy['timeline_estimate'] = '1-3 weeks'
            
        elif requirements.route_preference == 'regional':
            strategy['primary_focus'].extend([
                'Regional routes (multi-state)',
                'Home weekly positions',
                'Dedicated customer routes'
            ])
        
        # Adjust for experience level
        if requirements.experience_level == 'new':
            strategy['secondary_options'].extend([
                'Companies with training programs',
                'Apprenticeship opportunities',
                'Mentorship-based positions'
            ])
            strategy['timeline_estimate'] = '3-6 weeks'
            strategy['success_probability'] = 'medium'
            
        elif requirements.experience_level == 'expert':
            strategy['secondary_options'].extend([
                'Lead driver positions',
                'Trainer opportunities',
                'Specialized equipment roles'
            ])
            strategy['search_approach'] = 'selective'
        
        # Account for special requirements
        if 'background_sensitive' in requirements.special_requirements:
            strategy['secondary_options'].append('Fair chance employers')
            strategy['timeline_estimate'] = '3-5 weeks'
        
        if 'travel_restricted' in requirements.special_requirements:
            strategy['markets_to_prioritize'] = ['Local metropolitan areas']
            if target_market:
                strategy['markets_to_prioritize'].append(f'{target_market} local area')
        
        # Job type specific adjustments
        if 'tanker' in requirements.job_type_preferences:
            strategy['secondary_options'].extend([
                'Hazmat certification preferred',
                'Specialized chemical transport',
                'Food grade tanker opportunities'
            ])
        
        return strategy
    
    def _get_optimized_queries(self, requirements: JobRequirements, target_market: str) -> List[Dict]:
        """
        Get optimized search queries based on requirements
        
        Args:
            requirements: Structured job requirements
            target_market: Target market
            
        Returns:
            List of optimized query dictionaries
        """
        # Get base optimization strategy for market
        if target_market:
            base_strategy = self.query_optimizer.optimize_search_strategy(target_market, 65.0)
        else:
            base_strategy = self.query_optimizer._get_default_strategy("General")
        
        # Filter and prioritize queries based on requirements
        optimized_queries = []
        
        # Priority 1: Route-specific queries
        route_queries = self._get_route_specific_queries(requirements, base_strategy)
        optimized_queries.extend(route_queries)
        
        # Priority 2: Experience-level appropriate queries  
        experience_queries = self._get_experience_queries(requirements, base_strategy)
        optimized_queries.extend(experience_queries)
        
        # Priority 3: Job type specific queries
        if requirements.job_type_preferences:
            type_queries = self._get_job_type_queries(requirements, base_strategy)
            optimized_queries.extend(type_queries)
        
        # Priority 4: General high-performing queries
        general_queries = base_strategy['recommended_queries'][:3]  # Top 3 general performers
        for query in general_queries:
            if not any(q['query'] == query['query'] for q in optimized_queries):  # Avoid duplicates
                optimized_queries.append({
                    'query': query['query'],
                    'priority': 'general_performer',
                    'quality_score': query.get('quality_percentage', 0),
                    'reason': 'proven_market_performer'
                })
        
        # Limit to top 12 queries and sort by relevance
        optimized_queries = optimized_queries[:12]
        
        logger.info(f"Generated {len(optimized_queries)} optimized queries for requirements")
        
        return optimized_queries
    
    def _get_route_specific_queries(self, requirements: JobRequirements, base_strategy: Dict) -> List[Dict]:
        """Generate route-specific queries based on preferences"""
        route_queries = []
        
        if requirements.route_preference == 'local':
            local_terms = [
                'local CDL driver', 'home daily driver', 'city delivery driver',
                'local delivery CDL', 'day cab driver', 'local freight driver'
            ]
            for term in local_terms:
                route_queries.append({
                    'query': term,
                    'priority': 'route_specific',
                    'quality_score': 0,  # Unknown, needs testing
                    'reason': 'local_route_preference'
                })
                
        elif requirements.route_preference == 'otr':
            otr_terms = [
                'OTR driver', 'long haul driver', 'over the road driver',
                'cross country driver', 'nationwide driver'
            ]
            for term in otr_terms:
                route_queries.append({
                    'query': term,
                    'priority': 'route_specific', 
                    'quality_score': 0,
                    'reason': 'otr_route_preference'
                })
                
        elif requirements.route_preference == 'regional':
            regional_terms = [
                'regional driver', 'home weekly driver', 'multi-state driver',
                'dedicated driver', 'regional CDL driver'
            ]
            for term in regional_terms:
                route_queries.append({
                    'query': term,
                    'priority': 'route_specific',
                    'quality_score': 0,
                    'reason': 'regional_route_preference'
                })
        
        return route_queries[:4]  # Limit to top 4 route-specific queries
    
    def _get_experience_queries(self, requirements: JobRequirements, base_strategy: Dict) -> List[Dict]:
        """Generate experience-appropriate queries"""
        experience_queries = []
        
        if requirements.experience_level == 'new':
            new_driver_terms = [
                'entry level CDL driver', 'new CDL driver', 'CDL training provided',
                'recent CDL graduate', 'no experience required CDL'
            ]
            for term in new_driver_terms:
                experience_queries.append({
                    'query': term,
                    'priority': 'experience_specific',
                    'quality_score': 0,
                    'reason': 'new_driver_friendly'
                })
                
        elif requirements.experience_level == 'expert':
            expert_terms = [
                'experienced CDL driver', 'lead driver', 'senior truck driver',
                'CDL driver trainer', 'fleet driver'
            ]
            for term in expert_terms:
                experience_queries.append({
                    'query': term,
                    'priority': 'experience_specific',
                    'quality_score': 0,
                    'reason': 'expert_level_position'
                })
        
        return experience_queries[:3]  # Limit to top 3 experience queries
    
    def _get_job_type_queries(self, requirements: JobRequirements, base_strategy: Dict) -> List[Dict]:
        """Generate job type specific queries"""
        type_queries = []
        
        type_mapping = {
            'delivery': ['delivery driver CDL', 'courier driver', 'package delivery CDL'],
            'freight': ['freight driver', 'cargo driver', 'shipping driver CDL'],
            'tanker': ['tanker driver', 'liquid transport driver', 'chemical transport CDL'],
            'flatbed': ['flatbed driver', 'construction driver', 'equipment transport CDL'],
            'refrigerated': ['reefer driver', 'refrigerated transport', 'food transport CDL']
        }
        
        for job_type in requirements.job_type_preferences:
            if job_type in type_mapping:
                for term in type_mapping[job_type]:
                    type_queries.append({
                        'query': term,
                        'priority': 'job_type_specific',
                        'quality_score': 0,
                        'reason': f'{job_type}_specialization'
                    })
        
        return type_queries[:4]  # Limit to top 4 type-specific queries
    
    def _generate_coaching_advice(self, requirements: JobRequirements, strategy: Dict) -> Dict:
        """
        Generate personalized coaching advice based on requirements and strategy
        
        Args:
            requirements: Structured job requirements
            strategy: Personalized strategy
            
        Returns:
            Dictionary with coaching advice and tips
        """
        advice = {
            'key_recommendations': [],
            'potential_challenges': [],
            'success_tips': [],
            'market_insights': [],
            'next_steps': []
        }
        
        # Key recommendations based on route preference
        if requirements.route_preference == 'local':
            advice['key_recommendations'].extend([
                "Focus on metropolitan areas and suburban markets",
                "Highlight any customer service experience",
                "Consider LTL (Less Than Truckload) companies",
                "Look for home daily guaranteed positions"
            ])
            
            if 'travel_restricted' in requirements.special_requirements:
                advice['success_tips'].append("Emphasize your commitment to local operations in applications")
                
        elif requirements.route_preference == 'otr':
            advice['key_recommendations'].extend([
                "Major carriers often have the best OTR opportunities",
                "Consider team driving for higher pay potential",
                "Evaluate per-mile rates vs percentage pay",
                "Research company policies on home time"
            ])
            
        # Experience-level specific advice
        if requirements.experience_level == 'new':
            advice['key_recommendations'].extend([
                "Prioritize companies with comprehensive training programs",
                "Consider starting with larger carriers for experience",
                "Focus on safety record and learning opportunities"
            ])
            
            advice['potential_challenges'].extend([
                "Limited job options initially",
                "Lower starting pay rates",
                "Insurance requirements may be restrictive"
            ])
            
            advice['success_tips'].extend([
                "Emphasize your willingness to learn and adapt",
                "Highlight any relevant driving experience",
                "Be prepared for additional training requirements"
            ])
            
        elif requirements.experience_level == 'expert':
            advice['key_recommendations'].extend([
                "Target specialized positions with higher pay",
                "Consider owner-operator opportunities",
                "Look for leadership and training roles",
                "Negotiate based on your proven track record"
            ])
            
        # Special requirements considerations
        if 'background_sensitive' in requirements.special_requirements:
            advice['key_recommendations'].extend([
                "Research companies with explicit fair chance policies",
                "Be upfront about background during application process",
                "Focus on companies that value rehabilitation and second chances"
            ])
            
            advice['success_tips'].append("Prepare a brief explanation of your situation that focuses on growth and reliability")
        
        # Job type specific advice
        for job_type in requirements.job_type_preferences:
            if job_type == 'tanker':
                advice['market_insights'].append("Tanker positions often require Hazmat endorsement and offer premium pay")
            elif job_type == 'flatbed':
                advice['market_insights'].append("Flatbed work requires physical fitness but typically offers higher per-mile rates")
            elif job_type == 'refrigerated':
                advice['market_insights'].append("Reefer positions offer steady freight but require attention to temperature management")
        
        # General next steps
        advice['next_steps'].extend([
            "Use the optimized search queries provided",
            "Apply to 3-5 positions daily during your job search",
            "Follow up on applications within 1 week",
            "Prepare for phone screenings and potential road tests",
            "Have references and documentation ready"
        ])
        
        return advice

# Example usage and testing
if __name__ == "__main__":
    # Initialize career coach
    coach = CareerCoach()
    
    # Test with example user requests
    test_requests = [
        "free agent with travel restrictions needs local job",
        "experienced driver looking for OTR position with good home time",
        "new CDL graduate needs entry level position with training",
        "driver with felony looking for fair chance employer",
        "tanker driver with hazmat wants regional work"
    ]
    
    print("🎯 Career Coach Test Results")
    print("=" * 50)
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n{i}. User Request: '{request}'")
        print("-" * 40)
        
        # Process request
        result = coach.process_natural_language_request(request, "Houston")
        
        # Display key results
        reqs = result['extracted_requirements']
        print(f"Route Preference: {reqs.route_preference}")
        print(f"Experience Level: {reqs.experience_level}")
        print(f"Special Requirements: {', '.join(reqs.special_requirements) if reqs.special_requirements else 'None'}")
        
        # Show top optimized queries
        print(f"\nTop Optimized Queries:")
        for j, query in enumerate(result['optimized_queries'][:3], 1):
            print(f"  {j}. {query['query']} ({query['reason']})")
        
        # Show key coaching advice
        advice = result['coaching_advice']
        if advice['key_recommendations']:
            print(f"\nKey Recommendations:")
            for rec in advice['key_recommendations'][:2]:
                print(f"  • {rec}")
    
    print("\n✅ Career Coach system ready for integration!")