"""
AI-Powered Query Optimization System
Analyzes search performance and optimizes job search queries to maximize quality job discovery
"""
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import openai
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QueryPerformance:
    """Data class for query performance metrics"""
    query: str
    market: str
    total_jobs: int
    quality_jobs: int
    quality_percentage: float
    cost_efficiency: float
    diversity_score: float
    date_range: str
    
class QueryPerformanceAnalyzer:
    """Analyzes historical query performance to identify optimization opportunities"""
    
    def __init__(self, supabase_connection=None):
        """Initialize analyzer with database connection"""
        self.supabase = supabase_connection
        if not self.supabase:
            # Try to initialize Supabase connection
            try:
                from job_memory_db import JobMemoryDB
                memory_db = JobMemoryDB()
                self.supabase = memory_db.supabase
            except Exception as e:
                logger.warning(f"Could not initialize Supabase connection: {e}")
                self.supabase = None
    
    def analyze_query_effectiveness(self, timeframe_days: int = 30, min_sample_size: int = 10) -> pd.DataFrame:
        """
        Analyze historical query performance across all markets
        
        Args:
            timeframe_days: Number of days to analyze
            min_sample_size: Minimum jobs required for statistical significance
            
        Returns:
            DataFrame with query performance metrics
        """
        if not self.supabase:
            logger.error("Supabase connection not available for query analysis")
            return pd.DataFrame()
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=timeframe_days)
            cutoff_str = cutoff_date.isoformat()
            
            # Query historical performance data
            query = f"""
            SELECT 
                search_query,
                market,
                source,
                COUNT(*) as total_jobs,
                COUNT(CASE WHEN match_level = 'good' THEN 1 END) as excellent_jobs,
                COUNT(CASE WHEN match_level = 'so-so' THEN 1 END) as possible_jobs,
                COUNT(CASE WHEN match_level IN ('good', 'so-so') THEN 1 END) as quality_jobs,
                COUNT(DISTINCT company) as unique_companies,
                COUNT(CASE WHEN route_type = 'Local' THEN 1 END) as local_jobs,
                COUNT(CASE WHEN route_type = 'OTR' THEN 1 END) as otr_jobs,
                MIN(classified_at) as earliest_date,
                MAX(classified_at) as latest_date,
                ROUND(
                    COUNT(CASE WHEN match_level IN ('good', 'so-so') THEN 1 END) * 100.0 / COUNT(*), 
                    2
                ) as quality_percentage
            FROM job_classifications
            WHERE classified_at >= '{cutoff_str}'
                AND search_query IS NOT NULL 
                AND search_query != ''
                AND market IS NOT NULL
            GROUP BY search_query, market, source
            HAVING COUNT(*) >= {min_sample_size}
            ORDER BY quality_percentage DESC, total_jobs DESC
            """
            
            result = self.supabase.rpc('execute_sql', {'query': query}).execute()
            
            if not result.data:
                logger.warning("No query performance data found")
                return pd.DataFrame()
            
            # Convert to DataFrame and calculate additional metrics
            df = pd.DataFrame(result.data)
            
            # Calculate diversity score (companies per job)
            df['diversity_score'] = df['unique_companies'] / df['total_jobs']
            
            # Calculate cost efficiency (quality jobs per 100 total jobs)
            df['cost_efficiency'] = df['quality_jobs'] / df['total_jobs'] * 100
            
            # Add route type balance score
            df['route_balance'] = np.minimum(df['local_jobs'], df['otr_jobs']) / df['total_jobs']
            
            logger.info(f"Analyzed {len(df)} query-market combinations over {timeframe_days} days")
            
            return df
            
        except Exception as e:
            logger.error(f"Error analyzing query effectiveness: {e}")
            return pd.DataFrame()
    
    def identify_top_performers(self, analysis_df: pd.DataFrame, top_n: int = 20) -> List[QueryPerformance]:
        """
        Identify top-performing queries across all metrics
        
        Args:
            analysis_df: Results from analyze_query_effectiveness
            top_n: Number of top performers to return
            
        Returns:
            List of QueryPerformance objects sorted by overall score
        """
        if analysis_df.empty:
            return []
        
        # Calculate composite score
        # Weight: quality_percentage (50%), cost_efficiency (30%), diversity_score (20%)
        analysis_df['composite_score'] = (
            analysis_df['quality_percentage'] * 0.5 +
            analysis_df['cost_efficiency'] * 0.3 +
            analysis_df['diversity_score'] * 20 * 0.2  # Scale diversity to similar range
        )
        
        # Get top performers
        top_performers = analysis_df.nlargest(top_n, 'composite_score')
        
        # Convert to QueryPerformance objects
        performance_list = []
        for _, row in top_performers.iterrows():
            perf = QueryPerformance(
                query=row['search_query'],
                market=row['market'],
                total_jobs=int(row['total_jobs']),
                quality_jobs=int(row['quality_jobs']),
                quality_percentage=float(row['quality_percentage']),
                cost_efficiency=float(row['cost_efficiency']),
                diversity_score=float(row['diversity_score']),
                date_range=f"{row['earliest_date'][:10]} to {row['latest_date'][:10]}"
            )
            performance_list.append(perf)
        
        logger.info(f"Identified {len(performance_list)} top-performing queries")
        
        return performance_list
    
    def identify_underperformers(self, analysis_df: pd.DataFrame, threshold: float = 30.0) -> List[str]:
        """
        Identify queries that consistently underperform
        
        Args:
            analysis_df: Results from analyze_query_effectiveness
            threshold: Quality percentage threshold below which queries are considered underperforming
            
        Returns:
            List of underperforming query strings
        """
        if analysis_df.empty:
            return []
        
        underperformers = analysis_df[
            analysis_df['quality_percentage'] < threshold
        ]['search_query'].unique().tolist()
        
        logger.info(f"Identified {len(underperformers)} underperforming queries (< {threshold}% quality)")
        
        return underperformers
    
    def analyze_market_patterns(self, analysis_df: pd.DataFrame) -> Dict[str, Dict]:
        """
        Analyze market-specific query performance patterns
        
        Args:
            analysis_df: Results from analyze_query_effectiveness
            
        Returns:
            Dictionary with market-specific insights
        """
        if analysis_df.empty:
            return {}
        
        market_analysis = {}
        
        for market in analysis_df['market'].unique():
            market_data = analysis_df[analysis_df['market'] == market]
            
            # Calculate market-specific metrics
            best_query = market_data.nlargest(1, 'quality_percentage')
            avg_quality = market_data['quality_percentage'].mean()
            total_queries = len(market_data)
            
            market_analysis[market] = {
                'average_quality_percentage': round(avg_quality, 2),
                'total_query_variations': total_queries,
                'best_performing_query': best_query['search_query'].iloc[0] if not best_query.empty else None,
                'best_query_quality': round(best_query['quality_percentage'].iloc[0], 2) if not best_query.empty else 0,
                'top_3_queries': market_data.nlargest(3, 'quality_percentage')[['search_query', 'quality_percentage']].to_dict('records')
            }
        
        logger.info(f"Analyzed patterns for {len(market_analysis)} markets")
        
        return market_analysis

class AIQueryGenerator:
    """Uses AI to generate and optimize search queries"""
    
    def __init__(self):
        """Initialize AI query generator"""
        self.client = None
        self._init_openai()
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OpenAI API key not found - AI query generation unavailable")
                return
            
            openai.api_key = api_key
            self.client = openai
            logger.info("✅ OpenAI client initialized for AI query generation")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            self.client = None
    
    def generate_query_variations(self, base_query: str, market: str, num_variations: int = 10) -> List[str]:
        """
        Generate semantic variations of a base query using AI
        
        Args:
            base_query: Starting query to generate variations from
            market: Target market for context
            num_variations: Number of variations to generate
            
        Returns:
            List of query variations
        """
        if not self.client:
            logger.warning("OpenAI not available - returning basic variations")
            return self._generate_basic_variations(base_query)
        
        try:
            prompt = f"""
            Generate {num_variations} professional job search query variations for the trucking/CDL industry.
            
            Base query: "{base_query}"
            Target market: {market}
            
            Requirements:
            - Focus on CDL driving positions and freight transport
            - Include variations that might appeal to different experience levels
            - Consider both local and over-the-road (OTR) opportunities
            - Use industry-standard terminology
            - Keep queries concise (2-5 words typically)
            - Avoid overly generic terms that might return non-driving jobs
            
            Return only the query variations, one per line, without numbering or extra text.
            """
            
            response = self.client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in CDL job search optimization. Generate effective job search queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            # Parse response into individual queries
            content = response.choices[0].message.content.strip()
            variations = [line.strip() for line in content.split('\n') if line.strip()]
            
            # Filter and clean variations
            cleaned_variations = []
            for variation in variations:
                # Remove numbering, quotes, and extra formatting
                cleaned = variation.strip('1234567890.-"\'()[]')
                cleaned = cleaned.strip()
                
                if cleaned and len(cleaned) > 3:
                    cleaned_variations.append(cleaned)
            
            logger.info(f"Generated {len(cleaned_variations)} AI query variations for '{base_query}' in {market}")
            
            return cleaned_variations[:num_variations]  # Ensure we don't exceed requested number
            
        except Exception as e:
            logger.error(f"Error generating AI query variations: {e}")
            return self._generate_basic_variations(base_query)
    
    def _generate_basic_variations(self, base_query: str) -> List[str]:
        """Generate basic variations when AI is not available"""
        base_terms = base_query.lower().split()
        variations = []
        
        # Common CDL job search patterns
        cdl_variations = [
            "CDL driver", "truck driver", "commercial driver", "freight driver",
            "tractor trailer driver", "delivery driver CDL", "local CDL driver",
            "OTR driver", "regional driver", "dedicated driver"
        ]
        
        # Add location-specific variations
        location_modifiers = ["local", "regional", "OTR", "dedicated", "home daily"]
        
        for modifier in location_modifiers:
            if "driver" in base_query.lower():
                variations.append(f"{modifier} {base_query}")
        
        # Add base variations
        variations.extend(cdl_variations)
        
        # Remove duplicates and limit to 10
        unique_variations = list(dict.fromkeys(variations))[:10]
        
        logger.info(f"Generated {len(unique_variations)} basic query variations")
        
        return unique_variations
    
    def suggest_new_search_angles(self, market_data: Dict) -> List[str]:
        """
        Suggest completely new search strategies based on market analysis
        
        Args:
            market_data: Market analysis results
            
        Returns:
            List of new search angle suggestions
        """
        if not self.client:
            return self._get_default_search_angles()
        
        try:
            # Build context from market data
            context = f"Market analysis shows:\n"
            for market, data in market_data.items():
                context += f"- {market}: {data['average_quality_percentage']}% avg quality, best: '{data['best_performing_query']}'\n"
            
            prompt = f"""
            Based on this CDL job market analysis, suggest 8 new search strategies that might discover high-quality jobs:
            
            {context}
            
            Consider:
            - Emerging industry trends (electric vehicles, autonomous support, specialized freight)
            - Underexplored job categories (equipment transport, specialized hauling, local delivery)
            - Different terminology that might be used by employers
            - Niche markets that might have less competition
            
            Return only the search query suggestions, one per line.
            """
            
            response = self.client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a CDL industry expert who identifies emerging job market opportunities."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=250
            )
            
            content = response.choices[0].message.content.strip()
            suggestions = [line.strip() for line in content.split('\n') if line.strip()]
            
            # Clean and filter suggestions
            cleaned_suggestions = []
            for suggestion in suggestions:
                cleaned = suggestion.strip('1234567890.-"\'()[]')
                cleaned = cleaned.strip()
                if cleaned and len(cleaned) > 3:
                    cleaned_suggestions.append(cleaned)
            
            logger.info(f"AI generated {len(cleaned_suggestions)} new search angle suggestions")
            
            return cleaned_suggestions
            
        except Exception as e:
            logger.error(f"Error generating new search angles: {e}")
            return self._get_default_search_angles()
    
    def _get_default_search_angles(self) -> List[str]:
        """Default search angles when AI is not available"""
        return [
            "equipment operator CDL",
            "specialized hauling driver", 
            "construction equipment transport",
            "auto transport driver",
            "flatbed driver experienced",
            "tanker driver hazmat",
            "refrigerated freight driver",
            "LTL delivery driver"
        ]

class QueryOptimizer:
    """Main optimization engine that combines analysis and AI generation"""
    
    def __init__(self):
        """Initialize query optimizer"""
        self.analyzer = QueryPerformanceAnalyzer()
        self.generator = AIQueryGenerator()
        
    def optimize_search_strategy(self, market: str, target_quality_threshold: float = 65.0) -> Dict:
        """
        Generate optimized search strategy for a specific market
        
        Args:
            market: Target market name
            target_quality_threshold: Desired quality percentage threshold
            
        Returns:
            Dictionary with optimized search strategy
        """
        logger.info(f"Optimizing search strategy for {market} market (target: {target_quality_threshold}%)")
        
        # Step 1: Analyze historical performance
        analysis_df = self.analyzer.analyze_query_effectiveness(timeframe_days=60)
        
        if analysis_df.empty:
            logger.warning("No historical data available - using default strategy")
            return self._get_default_strategy(market)
        
        # Step 2: Get market-specific data
        market_data = analysis_df[analysis_df['market'] == market] if market in analysis_df['market'].values else analysis_df
        
        # Step 3: Identify top performers for this market
        top_performers = self.analyzer.identify_top_performers(market_data, top_n=10)
        
        # Step 4: Identify underperformers to avoid
        underperformers = self.analyzer.identify_underperformers(market_data, threshold=target_quality_threshold * 0.5)
        
        # Step 5: Generate new query variations for top performers
        new_variations = []
        for performer in top_performers[:3]:  # Use top 3 as seeds
            variations = self.generator.generate_query_variations(
                performer.query, market, num_variations=5
            )
            new_variations.extend(variations)
        
        # Step 6: Generate completely new search angles
        market_patterns = self.analyzer.analyze_market_patterns(analysis_df)
        new_angles = self.generator.suggest_new_search_angles(market_patterns)
        
        # Step 7: Compile optimized strategy
        strategy = {
            'market': market,
            'target_quality_threshold': target_quality_threshold,
            'optimization_date': datetime.now().isoformat(),
            
            # Recommended queries (proven performers)
            'recommended_queries': [
                {
                    'query': p.query,
                    'quality_percentage': p.quality_percentage,
                    'total_jobs': p.total_jobs,
                    'reason': 'proven_performer'
                }
                for p in top_performers[:5]
            ],
            
            # New variations to test
            'test_queries': [
                {
                    'query': q,
                    'reason': 'ai_variation',
                    'status': 'untested'
                }
                for q in new_variations[:8]
            ],
            
            # New angles to explore
            'exploration_queries': [
                {
                    'query': q,
                    'reason': 'new_angle',
                    'status': 'untested'
                }
                for q in new_angles[:5]
            ],
            
            # Queries to avoid
            'avoid_queries': underperformers,
            
            # Performance summary
            'current_performance': {
                'average_quality_percentage': float(market_data['quality_percentage'].mean()) if not market_data.empty else 0,
                'total_query_variations_tested': len(market_data),
                'top_performer_quality': top_performers[0].quality_percentage if top_performers else 0
            }
        }
        
        logger.info(f"Generated optimization strategy with {len(strategy['recommended_queries'])} proven queries, "
                   f"{len(strategy['test_queries'])} variations to test, and {len(strategy['exploration_queries'])} new angles")
        
        return strategy
    
    def _get_default_strategy(self, market: str) -> Dict:
        """Default strategy when no historical data is available"""
        return {
            'market': market,
            'target_quality_threshold': 65.0,
            'optimization_date': datetime.now().isoformat(),
            'recommended_queries': [
                {'query': 'CDL driver', 'reason': 'default_baseline'},
                {'query': 'truck driver', 'reason': 'default_baseline'},
                {'query': 'local CDL driver', 'reason': 'default_baseline'}
            ],
            'test_queries': [
                {'query': 'commercial driver', 'reason': 'default_variation'},
                {'query': 'freight driver', 'reason': 'default_variation'},
                {'query': 'delivery driver CDL', 'reason': 'default_variation'}
            ],
            'exploration_queries': [
                {'query': 'regional driver', 'reason': 'default_exploration'},
                {'query': 'dedicated driver', 'reason': 'default_exploration'}
            ],
            'avoid_queries': [],
            'current_performance': {
                'average_quality_percentage': 0,
                'total_query_variations_tested': 0,
                'top_performer_quality': 0
            }
        }

# Example usage and testing
if __name__ == "__main__":
    # Initialize optimizer
    optimizer = QueryOptimizer()
    
    # Test with Houston market
    strategy = optimizer.optimize_search_strategy("Houston", target_quality_threshold=60.0)
    
    print("=== OPTIMIZED SEARCH STRATEGY ===")
    print(f"Market: {strategy['market']}")
    print(f"Target Quality: {strategy['target_quality_threshold']}%")
    
    print(f"\n🏆 Recommended Queries ({len(strategy['recommended_queries'])}):")
    for query in strategy['recommended_queries']:
        print(f"  • {query['query']} ({query.get('quality_percentage', 'N/A')}%)")
    
    print(f"\n🧪 Test Queries ({len(strategy['test_queries'])}):")
    for query in strategy['test_queries']:
        print(f"  • {query['query']} ({query['reason']})")
    
    print(f"\n🔍 Exploration Queries ({len(strategy['exploration_queries'])}):")
    for query in strategy['exploration_queries']:
        print(f"  • {query['query']} ({query['reason']})")
    
    if strategy['avoid_queries']:
        print(f"\n❌ Avoid These Queries ({len(strategy['avoid_queries'])}):")
        for query in strategy['avoid_queries']:
            print(f"  • {query}")