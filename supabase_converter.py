#!/usr/bin/env python3
"""
Supabase to Canonical DataFrame Converter - FILTERING FIX v2.0
Converts Supabase job_postings data back to full canonical DataFrame format
MAJOR FIX: Route type filtering now works correctly at database query level
CACHE_BUSTER: supabase_filter_fix_262d9f9_sept5
"""

import pandas as pd
from typing import List, Dict
from datetime import datetime, timedelta
from jobs_schema import ensure_schema

def supabase_to_canonical_df(supabase_rows: List[Dict], 
                               agent_params: Dict = None, 
                               search_params: Dict = None) -> pd.DataFrame:
    """Convert Supabase job_postings rows to canonical DataFrame format.
    
    This is the REVERSE of prepare_for_supabase() - takes Supabase data
    and reconstructs the full canonical DataFrame with all fields.
    
    Args:
        supabase_rows: List of dictionaries from Supabase job_postings table
        agent_params: Dict with agent.* field data (uuid, name, coach, etc.)
        search_params: Dict with search.* field data (location, mode, filters, etc.)
        
    Returns:
        pd.DataFrame with full canonical schema
    """
    
    if not supabase_rows:
        return ensure_schema(pd.DataFrame())  # Return empty canonical DF
    
    print(f"🔄 Converting {len(supabase_rows)} Supabase rows to canonical DataFrame")
    
    # Provide defaults for missing parameters
    if agent_params is None:
        agent_params = {}
    if search_params is None:
        search_params = {}
    
    # Create DataFrame from Supabase rows
    df = pd.DataFrame(supabase_rows)
    
    # Initialize canonical DataFrame with schema
    canonical_df = ensure_schema(pd.DataFrame(index=range(len(df))))
    
    # COMPLETE MAPPING: Supabase fields → Canonical fields
    
    # === IDENTITY FIELDS ===
    canonical_df['id.job'] = df.get('job_id', '')
    canonical_df['id.source'] = df.get('source', 'memory')  # Mark as memory source
    canonical_df['id.source_row'] = ''  # Not stored in Supabase
    
    # === SOURCE FIELDS (Raw API data) ===
    canonical_df['source.title'] = df.get('job_title', '')
    canonical_df['source.company'] = df.get('company', '')
    canonical_df['source.location_raw'] = df.get('location', '')
    canonical_df['source.description_raw'] = df.get('job_description', '')
    
    # Single unified URL field - prioritize best URL from any source
    apply_urls = pd.Series(df.get('apply_url', ''))
    indeed_urls = pd.Series(df.get('indeed_job_url', ''))
    google_urls = pd.Series(df.get('google_job_url', ''))
    
    # Priority: apply_url (direct) -> indeed_job_url -> google_job_url
    canonical_df['source.url'] = apply_urls.replace('', pd.NA).fillna(
        indeed_urls.replace('', pd.NA).fillna(
            google_urls.replace('', pd.NA).fillna('')
        )
    )
    
    canonical_df['source.salary_raw'] = df.get('salary', '')
    canonical_df['source.posted_date'] = ''  # Not stored in Supabase
    
    # === NORMALIZED FIELDS ===
    # These may not be stored in Supabase - extract from raw fields
    canonical_df['norm.title'] = df.get('job_title', '')  # Use job_title as normalized
    canonical_df['norm.company'] = df.get('company', '')
    canonical_df['norm.city'] = ''  # Extract from location if needed
    canonical_df['norm.state'] = ''  # Extract from location if needed
    canonical_df['norm.location'] = df.get('location', '')
    canonical_df['norm.description'] = df.get('summary', '')  # Use AI summary as norm description
    canonical_df['norm.salary_display'] = df.get('salary', '')
    canonical_df['norm.salary_min'] = None
    canonical_df['norm.salary_max'] = None
    canonical_df['norm.salary_unit'] = ''
    canonical_df['norm.salary_currency'] = 'USD'
    
    # === BUSINESS RULES FIELDS ===
    canonical_df['rules.is_owner_op'] = False
    canonical_df['rules.is_school_bus'] = False
    canonical_df['rules.has_experience_req'] = False
    canonical_df['rules.experience_years_min'] = None
    canonical_df['rules.is_spam_source'] = False
    canonical_df['rules.duplicate_r1'] = ''
    canonical_df['rules.duplicate_r2'] = ''
    canonical_df['rules.collapse_group'] = ''
    
    # === AI CLASSIFICATION FIELDS ===
    canonical_df['ai.match'] = df.get('match_level', '')
    canonical_df['ai.reason'] = df.get('match_reason', '')
    canonical_df['ai.summary'] = df.get('summary', '')
    canonical_df['ai.fair_chance'] = df.get('fair_chance', '')
    canonical_df['ai.endorsements'] = df.get('endorsements', '')
    canonical_df['ai.route_type'] = df.get('route_type', '')
    canonical_df['ai.raw_response'] = ''  # Not stored in Supabase
    
    # === ROUTING FIELDS ===
    canonical_df['route.stage'] = 'exported'  # Memory jobs are fully processed
    canonical_df['route.final_status'] = df.get('filter_reason', 'exported')
    canonical_df['route.filtered'] = False
    canonical_df['route.ready_for_ai'] = False  # Already classified
    canonical_df['route.ready_for_export'] = True  # Memory jobs are pre-filtered quality
    canonical_df['route.error'] = ''
    canonical_df['route.batch_id'] = ''
    
    # === METADATA FIELDS ===
    canonical_df['meta.market'] = df.get('market', '')
    canonical_df['meta.query'] = df.get('search_query', '')
    canonical_df['meta.search_terms'] = df.get('search_query', '')  # Use same as query
    canonical_df['meta.tracked_url'] = df.get('tracked_url', '')  # Use stored tracking URL from Supabase
    canonical_df['meta.airtable_id'] = ''  # Not applicable for memory jobs
    
    # === SEARCH PARAMETERS ===
    # Populate from search_params or use defaults
    canonical_df['search.location'] = search_params.get('location', df.get('search_location', df.get('location', '')))
    canonical_df['search.custom_location'] = search_params.get('custom_location', '')
    canonical_df['search.route_filter'] = search_params.get('route_filter', 'both')
    canonical_df['search.mode'] = search_params.get('mode', df.get('search_mode', 'memory'))
    canonical_df['search.job_limit'] = search_params.get('job_limit', 100)
    canonical_df['search.radius'] = search_params.get('radius', 50)
    canonical_df['search.exact_location'] = search_params.get('exact_location', False)
    canonical_df['search.no_experience'] = search_params.get('no_experience', True)
    canonical_df['search.force_fresh'] = search_params.get('force_fresh', False)
    canonical_df['search.memory_only'] = True  # These are memory jobs
    canonical_df['search.business_rules'] = search_params.get('business_rules', True)
    canonical_df['search.deduplication'] = search_params.get('deduplication', True)
    canonical_df['search.experience_filter'] = search_params.get('experience_filter', True)
    canonical_df['search.model'] = search_params.get('model', 'gpt-4o-mini')
    canonical_df['search.batch_size'] = search_params.get('batch_size', 25)
    canonical_df['search.sources'] = search_params.get('sources', df.get('source', 'memory'))
    canonical_df['search.strategy'] = search_params.get('strategy', 'balanced')
    canonical_df['search.coach_username'] = search_params.get('coach_username', df.get('coach_username', df.get('success_coach', '')))
    
    # === FREE AGENT FIELDS ===
    # Populate from agent_params or use defaults
    canonical_df['agent.uuid'] = agent_params.get('agent_uuid', df.get('agent_uuid', ''))
    canonical_df['agent.name'] = agent_params.get('agent_name', df.get('agent_name', ''))
    canonical_df['agent.first_name'] = agent_params.get('agent_first_name', df.get('agent_first_name', ''))
    canonical_df['agent.last_name'] = agent_params.get('agent_last_name', '')
    canonical_df['agent.email'] = agent_params.get('agent_email', df.get('agent_email', ''))
    canonical_df['agent.phone'] = agent_params.get('agent_phone', '')
    canonical_df['agent.city'] = agent_params.get('agent_city', '')
    canonical_df['agent.state'] = agent_params.get('agent_state', '')
    canonical_df['agent.coach_name'] = agent_params.get('coach_name', df.get('coach_name', ''))
    canonical_df['agent.coach_username'] = agent_params.get('coach_username', df.get('coach_username', df.get('success_coach', '')))
    canonical_df['agent.preferred_route'] = agent_params.get('preferred_route', '')
    canonical_df['agent.experience_years'] = agent_params.get('experience_years', None)
    canonical_df['agent.endorsements_held'] = agent_params.get('endorsements_held', '')
    canonical_df['agent.notes'] = agent_params.get('notes', '')
    canonical_df['agent.last_contact'] = agent_params.get('last_contact', '')
    canonical_df['agent.status'] = agent_params.get('status', 'active')
    
    # === QUALITY ASSURANCE FIELDS ===
    canonical_df['qa.missing_required_fields'] = False
    canonical_df['qa.flags'] = ''
    canonical_df['qa.last_validated_at'] = ''
    canonical_df['qa.data_quality_score'] = 1.0  # Memory jobs are high quality
    
    # === SYSTEM FIELDS ===
    canonical_df['sys.created_at'] = df.get('created_at', '')
    canonical_df['sys.updated_at'] = df.get('updated_at', '')
    canonical_df['sys.classified_at'] = df.get('classified_at', '')
    canonical_df['sys.run_id'] = 'memory_retrieval'
    canonical_df['sys.version'] = '1.0.0'
    canonical_df['sys.classification_source'] = df.get('classification_source', 'supabase_memory')
    canonical_df['sys.is_fresh_job'] = False  # These are all memory jobs
    canonical_df['sys.model'] = 'gpt-4o-mini'
    canonical_df['sys.prompt_sha'] = ''
    canonical_df['sys.schema_sha'] = ''
    canonical_df['sys.coach'] = df.get('success_coach', df.get('coach_username', ''))
    
    print(f"✅ Converted to canonical DataFrame: {len(canonical_df)} jobs, {len(canonical_df.columns)} fields")
    
    # Validate the canonical DataFrame
    from jobs_schema import validate_canonical_df
    validation = validate_canonical_df(canonical_df, "Memory->Canonical")
    
    if not validation['valid']:
        print(f"⚠️ Validation issues found but proceeding...")
    
    return canonical_df


def search_memory_jobs(location: str, limit: int = 100, days_back: int = 7, 
                      agent_params: Dict = None, search_params: Dict = None) -> pd.DataFrame:
    """Search Supabase for recent quality jobs by location.
    
    Args:
        location: Location to search for (e.g., "Houston", "Dallas, TX")
        limit: Maximum number of jobs to return
        days_back: How many days back to search
        agent_params: Dict with agent data for canonical DataFrame
        search_params: Dict with search parameters for canonical DataFrame
        
    Returns:
        pd.DataFrame: Canonical DataFrame with memory jobs
    """
    try:
        from supabase_utils import get_client
        
        supabase_client = get_client()
        if not supabase_client:
            print("❌ Supabase client not available")
            return ensure_schema(pd.DataFrame())
        
        # Calculate cutoff date
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        # Use market-based search as primary method
        market_name = (location or '').strip()
        print(f"🔍 Searching Supabase for jobs: market='{market_name}', limit={limit}, since={cutoff_date}")
        if agent_params:
            print(f"🎯 Applying filters: fair_chance_only={agent_params.get('fair_chance_only', False)}, route_types={agent_params.get('route_type_filter', [])}, match_quality={agent_params.get('match_quality_filter', ['good', 'so-so'])}")
        
        # DEBUG: Let's also check what's actually in the database
        try:
            debug_query = supabase_client.table('jobs').select('route_type', count='exact').eq('market', market_name).gte('created_at', cutoff_date)
            debug_result = debug_query.execute()
            print(f"🔍 DEBUG: Total jobs in {market_name} since {cutoff_date}: {debug_result.count}")
            
            # Check specifically for local jobs
            local_debug = supabase_client.table('jobs').select('route_type', count='exact').eq('market', market_name).ilike('route_type', '%local%').gte('created_at', cutoff_date).execute()
            print(f"🔍 DEBUG: Local jobs in {market_name}: {local_debug.count}")
        except Exception as e:
            print(f"🔍 DEBUG query failed: {e}")
        
        # Simplified approach: Skip the complex CASE statement that's causing parsing errors
        # We'll handle priority sorting in Python instead of SQL
        
        # Build query with agent-specific filters
        # Use match_quality_filter from agent_params if available, otherwise default to ['good', 'so-so']
        match_levels = ['good', 'so-so']  # default
        if agent_params and agent_params.get('match_quality_filter'):
            match_levels = agent_params['match_quality_filter']
            
        query = (
            supabase_client
            .table('jobs')
            .select('*')  # Skip the broken priority SQL for now
            .eq('market', market_name)
            .in_('match_level', match_levels)
            .gte('created_at', cutoff_date)
        )
        
        # Apply agent-specific filters at Supabase level for efficiency
        if agent_params:
            # Fair chance filter
            if agent_params.get('fair_chance_only', False):
                query = query.ilike('fair_chance', '%fair_chance_employer%')
                print(f"🎯 Applied fair_chance_only filter at Supabase level")
            
            # Route type filter - handle multiple route types
            route_type_filter = agent_params.get('route_type_filter', [])
            if route_type_filter and len(route_type_filter) < 3:  # If not all route types selected
                # Build proper OR conditions for multiple route types
                if len(route_type_filter) == 1:
                    # Single route type - use direct filter
                    route_type = route_type_filter[0].lower()
                    if route_type == 'local':
                        query = query.ilike('route_type', '%local%')
                        print(f"🎯 Applied LOCAL filter: ilike('route_type', '%local%')")
                    elif route_type == 'otr':
                        # Use OR for OTR variations (over, otr, over-the-road, etc.)
                        query = query.or_('route_type.ilike.%otr%,route_type.ilike.%over%')
                        print(f"🎯 Applied OTR filter: or('route_type.ilike.%otr%,route_type.ilike.%over%')")
                    elif route_type == 'unknown':
                        query = query.or_('route_type.is.null,route_type.eq.')
                        print(f"🎯 Applied UNKNOWN filter: or('route_type.is.null,route_type.eq.')")
                    print(f"🔍 Single route filter applied for: {route_type}")
                else:
                    # Multiple route types - build OR condition
                    route_conditions = []
                    for route_type in route_type_filter:
                        if route_type.lower() == 'local':
                            route_conditions.append('route_type.ilike.%local%')
                        elif route_type.lower() == 'otr':
                            route_conditions.append('route_type.ilike.%otr%')
                            route_conditions.append('route_type.ilike.%over%')
                        elif route_type.lower() == 'unknown':
                            route_conditions.append('route_type.is.null')
                            route_conditions.append('route_type.eq.')
                    
                    if route_conditions:
                        query = query.or_(','.join(route_conditions))
                        print(f"🎯 Applied multiple route type filter: {route_type_filter}")
        
        response = (
            query
            .order('created_at', desc=True)  # Order by newest first (skip priority for now)
            .limit(limit)  # Now we can use normal limit since we're pre-filtering
            .execute()
        )
        
        print(f"📦 Found {len(response.data)} memory jobs in Supabase")
        
        # CRITICAL TEST: If we filtered for Local only, there should be ZERO OTR jobs
        if agent_params and agent_params.get('route_type_filter') == ['Local']:
            otr_jobs = [job for job in response.data if 'otr' in str(job.get('route_type', '')).lower()]
            if otr_jobs:
                print(f"🚨 FILTER FAILED: Found {len(otr_jobs)} OTR jobs when filtering for Local only!")
                print(f"🚨 OTR route types found: {[job.get('route_type') for job in otr_jobs[:3]]}")
            else:
                print(f"✅ FILTER SUCCESS: No OTR jobs found when filtering for Local only")
        
        # Debug: Show breakdown of retrieved jobs including route types
        if response.data:
            priority_counts = {}
            fair_chance_count = 0
            route_type_counts = {}
            
            for job in response.data[:10]:  # Check first 10 jobs
                match_level = job.get('match_level', '')
                fair_chance = job.get('fair_chance', '')
                priority = job.get('priority', 5)
                route_type = job.get('route_type', 'Unknown')
                
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
                route_type_counts[route_type] = route_type_counts.get(route_type, 0) + 1
                
                if 'fair_chance_employer' in str(fair_chance).lower() or str(fair_chance).lower() == 'true':
                    fair_chance_count += 1
            
            print(f"🎯 Job priority breakdown (first 10): {priority_counts}")
            print(f"🚛 Route type breakdown (first 10): {route_type_counts}")
            print(f"🤝 Fair chance jobs in top 10: {fair_chance_count}")
        
        # Convert to canonical DataFrame with full context
        canonical_df = supabase_to_canonical_df(response.data, agent_params, search_params)
        
        return canonical_df
        
    except Exception as e:
        print(f"❌ Error searching memory jobs: {e}")
        return ensure_schema(pd.DataFrame())


if __name__ == "__main__":
    # Test the converter
    print("🧪 Testing Supabase to DataFrame converter")
    
    # Test with empty data
    empty_df = supabase_to_canonical_df([])
    print(f"Empty test: {len(empty_df)} rows, {len(empty_df.columns)} columns")
    
    # Test memory search
    test_df = search_memory_jobs("Houston", limit=5)
    print(f"Memory search test: {len(test_df)} rows")
    
    if not test_df.empty:
        print("Sample fields:")
        print(f"  - Job ID: {test_df['id.job'].iloc[0]}")
        print(f"  - Title: {test_df['source.title'].iloc[0]}")
        print(f"  - Company: {test_df['source.company'].iloc[0]}")
        print(f"  - Match: {test_df['ai.match'].iloc[0]}")
        print(f"  - Classification Source: {test_df['sys.classification_source'].iloc[0]}")
        print(f"  - Is Fresh: {test_df['sys.is_fresh_job'].iloc[0]}")
