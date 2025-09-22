#!/usr/bin/env python3
"""
Companies Rollup Table Management
Creates and maintains a rollup table of companies derived from the jobs table
"""

import os
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from collections import Counter
import json

try:
    from supabase_utils import get_client
except Exception:
    get_client = None

def create_companies_table_sql():
    """Generate SQL to create the companies rollup table"""
    return """
    CREATE TABLE IF NOT EXISTS companies (
        id SERIAL PRIMARY KEY,
        company_name TEXT NOT NULL,
        normalized_company_name TEXT NOT NULL,
        total_jobs INTEGER DEFAULT 0,
        active_jobs INTEGER DEFAULT 0,
        fair_chance_jobs INTEGER DEFAULT 0,
        has_fair_chance BOOLEAN DEFAULT FALSE,
        markets TEXT[] DEFAULT ARRAY[]::TEXT[],
        job_titles TEXT[] DEFAULT ARRAY[]::TEXT[],
        route_types TEXT[] DEFAULT ARRAY[]::TEXT[],
        quality_breakdown JSONB DEFAULT '{}'::JSONB,
        route_breakdown JSONB DEFAULT '{}'::JSONB,
        free_agent_feedback JSONB DEFAULT '{}'::JSONB,
        is_blacklisted BOOLEAN DEFAULT FALSE,
        blacklist_reason TEXT,
        oldest_job_date TIMESTAMPTZ,
        newest_job_date TIMESTAMPTZ,
        avg_salary_min NUMERIC,
        avg_salary_max NUMERIC,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(normalized_company_name);
    CREATE INDEX IF NOT EXISTS idx_companies_fair_chance ON companies(has_fair_chance);
    CREATE INDEX IF NOT EXISTS idx_companies_active_jobs ON companies(active_jobs);
    CREATE INDEX IF NOT EXISTS idx_companies_updated ON companies(updated_at);
    CREATE INDEX IF NOT EXISTS idx_companies_blacklisted ON companies(is_blacklisted);
    CREATE INDEX IF NOT EXISTS idx_companies_quality_breakdown ON companies USING GIN(quality_breakdown);
    CREATE INDEX IF NOT EXISTS idx_companies_route_breakdown ON companies USING GIN(route_breakdown);
    
    -- Create function to update updated_at timestamp
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    
    -- Create trigger to auto-update updated_at
    DROP TRIGGER IF EXISTS update_companies_updated_at ON companies;
    CREATE TRIGGER update_companies_updated_at 
        BEFORE UPDATE ON companies 
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();
    """

def normalize_company_name(company_name: str) -> str:
    """Normalize company name for consistent grouping"""
    if not company_name or pd.isna(company_name):
        return "Unknown Company"
    
    # Convert to lowercase and strip whitespace
    normalized = str(company_name).lower().strip()
    
    # Remove common suffixes and variations
    suffixes_to_remove = [
        ', inc.', ' inc.', ', inc', ' inc',
        ', llc.', ' llc.', ', llc', ' llc', 
        ', corp.', ' corp.', ', corp', ' corp',
        ', ltd.', ' ltd.', ', ltd', ' ltd',
        ', co.', ' co.', ', co', ' co',
        ' company', ' companies'
    ]
    
    for suffix in suffixes_to_remove:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
    
    # Handle common variations
    normalized = normalized.replace('&', 'and')
    normalized = ' '.join(normalized.split())  # Normalize whitespace
    
    return normalized.title()

# NOTE: extract_market_from_location function removed - we now use the market field directly from jobs table

def analyze_jobs_for_companies() -> pd.DataFrame:
    """Analyze jobs table and create companies rollup data - only include companies with good/so-so jobs"""
    client = get_client()
    if not client:
        raise Exception("Supabase client not available")

    print("🔍 Fetching jobs data from Supabase...")

    # Fetch ALL jobs data with good/so-so quality - NO TIME LIMITS
    # Get every single quality job in the entire database
    print("🔄 Fetching ALL jobs with good/so-so quality (no time limits)...")

    all_jobs_data = []
    page_size = 1000  # Supabase default limit
    offset = 0

    while True:
        result = client.table('jobs').select(
            'company, location, job_title, match_level, route_type, fair_chance, salary, created_at, success_coach, market'
        ).in_('match_level', ['good', 'so-so']).range(offset, offset + page_size - 1).execute()

        page_data = result.data or []
        if not page_data:
            break

        all_jobs_data.extend(page_data)
        print(f"   📄 Loaded page {offset//page_size + 1}: {len(page_data)} jobs")

        if len(page_data) < page_size:
            break  # Last page

        offset += page_size

        # Safety break to prevent infinite loops
        if offset > 50000:  # Max 50k jobs
            print("⚠️ Safety break: reached 50k jobs limit")
            break

    jobs_data = all_jobs_data
    print(f"📊 Analyzing {len(jobs_data)} total quality jobs (ALL TIME)...")
    
    if not jobs_data:
        print("⚠️ No jobs data found")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(jobs_data)
    
    # Normalize company names
    df['normalized_company'] = df['company'].apply(normalize_company_name)
    
    # Use the market field directly from the jobs table (no conversion needed)
    
    # Parse salary data (assuming it's stored as text like "50000-60000" or "50000")
    def parse_salary(salary_str):
        if not salary_str or pd.isna(salary_str):
            return None, None
        
        try:
            salary_str = str(salary_str).replace('$', '').replace(',', '')
            if '-' in salary_str:
                parts = salary_str.split('-')
                return float(parts[0]), float(parts[1])
            else:
                val = float(salary_str)
                return val, val
        except:
            return None, None
    
    df[['salary_min', 'salary_max']] = df['salary'].apply(
        lambda x: pd.Series(parse_salary(x))
    )
    
    # Group by normalized company name
    companies_rollup = []
    
    for company_name, company_jobs in df.groupby('normalized_company'):
        if company_name == "Unknown Company" and len(company_jobs) < 3:
            continue  # Skip unknown companies with very few jobs
        
        # Calculate metrics
        total_jobs = len(company_jobs)
        
        # Fair chance analysis
        fair_chance_jobs = company_jobs['fair_chance'].astype(str).str.lower().str.contains('fair|yes|true', na=False).sum()
        has_fair_chance = fair_chance_jobs > 0
        
        # Markets (unique locations)
        markets = company_jobs['market'].dropna().unique().tolist()
        
        # Job titles (top 10 most common)
        job_titles = company_jobs['job_title'].dropna().value_counts().head(10).index.tolist()
        
        # Route types
        route_types = company_jobs['route_type'].dropna().unique().tolist()
        
        # Quality breakdown
        quality_counts = company_jobs['match_level'].value_counts().to_dict()

        # Route breakdown with job counts
        route_counts = company_jobs['route_type'].value_counts().to_dict()
        # Normalize route names
        normalized_route_counts = {}
        for route, count in route_counts.items():
            if pd.notna(route):
                route_key = str(route).lower()
                if 'local' in route_key:
                    normalized_route_counts['Local'] = normalized_route_counts.get('Local', 0) + count
                elif 'otr' in route_key or 'over the road' in route_key:
                    normalized_route_counts['OTR'] = normalized_route_counts.get('OTR', 0) + count
                elif 'regional' in route_key:
                    normalized_route_counts['Regional'] = normalized_route_counts.get('Regional', 0) + count
                else:
                    normalized_route_counts['Other'] = normalized_route_counts.get('Other', 0) + count

        # Free agent feedback aggregation (placeholder for future enhancement)
        feedback_data = {}
        # Note: Free agent feedback will be populated when click tracking data is integrated
        # For now, we'll track basic engagement metrics
        feedback_data['total_jobs_posted'] = total_jobs
        feedback_data['last_job_date'] = company_jobs['created_at'].max() if not company_jobs.empty else None

        # Date ranges
        dates = pd.to_datetime(company_jobs['created_at'])
        oldest_date = dates.min()
        newest_date = dates.max()

        # Salary averages
        salary_data = company_jobs[['salary_min', 'salary_max']].dropna()
        avg_salary_min = salary_data['salary_min'].mean() if not salary_data.empty else None
        avg_salary_max = salary_data['salary_max'].mean() if not salary_data.empty else None

        # Ensure no NaN or infinity values
        if avg_salary_min is not None and (pd.isna(avg_salary_min) or not pd.isfinite(avg_salary_min)):
            avg_salary_min = None
        if avg_salary_max is not None and (pd.isna(avg_salary_max) or not pd.isfinite(avg_salary_max)):
            avg_salary_max = None
        
        companies_rollup.append({
            'company_name': company_jobs['company'].iloc[0],  # Original name
            'normalized_company_name': company_name,
            'total_jobs': total_jobs,
            'active_jobs': total_jobs,  # All jobs in 60-day window are considered "active"
            'fair_chance_jobs': int(fair_chance_jobs),
            'has_fair_chance': bool(has_fair_chance),
            'markets': markets,
            'job_titles': job_titles,
            'route_types': [rt for rt in route_types if rt and not pd.isna(rt)],
            'quality_breakdown': quality_counts,
            'route_breakdown': normalized_route_counts,
            'free_agent_feedback': feedback_data,
            'is_blacklisted': False,  # Default to not blacklisted
            'blacklist_reason': None,
            'oldest_job_date': oldest_date.isoformat() if pd.notna(oldest_date) else None,
            'newest_job_date': newest_date.isoformat() if pd.notna(newest_date) else None,
            'avg_salary_min': avg_salary_min,
            'avg_salary_max': avg_salary_max,
        })
    
    return pd.DataFrame(companies_rollup)

def update_companies_table():
    """Update the companies rollup table with fresh data"""
    client = get_client()
    if not client:
        raise Exception("Supabase client not available")
    
    print("🏢 UPDATING COMPANIES ROLLUP TABLE")
    print("=" * 50)
    
    # Analyze jobs and create rollup data
    companies_df = analyze_jobs_for_companies()
    
    if companies_df.empty:
        print("⚠️ No companies data to update")
        return
    
    # Clear existing data and insert new data
    print(f"🗑️ Clearing existing companies data...")
    client.table('companies').delete().neq('id', 0).execute()  # Delete all rows
    
    print(f"📊 Inserting {len(companies_df)} companies...")
    
    # Convert DataFrame to list of dicts for Supabase
    companies_data = companies_df.to_dict('records')
    
    # Insert in batches of 100
    batch_size = 100
    for i in range(0, len(companies_data), batch_size):
        batch = companies_data[i:i + batch_size]
        result = client.table('companies').insert(batch).execute()
        print(f"✅ Inserted batch {i//batch_size + 1}: {len(batch)} companies")
    
    print(f"🎉 Companies rollup table updated successfully!")
    
    # Print summary
    total_companies = len(companies_df)
    fair_chance_companies = companies_df['has_fair_chance'].sum()
    top_markets = companies_df.explode('markets')['markets'].value_counts().head(5)
    
    print(f"\n📈 SUMMARY:")
    print(f"   Total Companies: {total_companies}")
    print(f"   Fair Chance Companies: {fair_chance_companies} ({fair_chance_companies/total_companies*100:.1f}%)")
    print(f"   Top Markets: {dict(top_markets)}")
    
    return companies_df

def get_company_analytics(company_name: str = None, limit: int = None) -> pd.DataFrame:
    """Get ALL companies data - using range queries to bypass 1000 row limit"""

    client = get_client()
    if not client:
        raise Exception("Supabase client not available")

    # RESEARCH SOLUTION: Use range queries to get ALL data beyond 1000 row limit
    all_companies = []
    page_size = 1000  # Supabase default limit
    start = 0

    try:
        while True:
            query = client.table('companies').select('*').order('total_jobs', desc=True)

            if company_name:
                query = query.ilike('normalized_company_name', f'%{company_name}%')

            # Use range to get chunks of data
            result = query.range(start, start + page_size - 1).execute()
            page_data = result.data or []

            if not page_data:
                break  # No more data

            all_companies.extend(page_data)
            print(f"📄 Loaded page {start//page_size + 1}: {len(page_data)} companies (total: {len(all_companies)})")

            # If we got less than page_size, we're done
            if len(page_data) < page_size:
                break

            start += page_size

        df = pd.DataFrame(all_companies)

        # Apply limit if specified
        if limit and len(df) > limit:
            df = df.head(limit)

        print(f"✅ FINAL RESULT: Loaded {len(df)} companies using range queries")
        return df

    except Exception as e:
        print(f"❌ Error loading companies data: {e}")
        return pd.DataFrame()

def get_fair_chance_companies() -> pd.DataFrame:
    """Get companies that offer fair chance opportunities"""
    client = get_client()
    if not client:
        raise Exception("Supabase client not available")
    
    result = client.table('companies').select('*').eq('has_fair_chance', True).order('fair_chance_jobs', desc=True).execute()
    return pd.DataFrame(result.data or [])

def get_market_company_breakdown(market: str) -> pd.DataFrame:
    """Get companies operating in a specific market"""
    client = get_client()
    if not client:
        raise Exception("Supabase client not available")

    # Use PostgreSQL array contains operator
    result = client.table('companies').select('*').contains('markets', [market]).order('total_jobs', desc=True).execute()
    return pd.DataFrame(result.data or [])

def update_company_blacklist(company_id: int, is_blacklisted: bool, reason: str = None) -> bool:
    """Update blacklist status for a company"""
    client = get_client()
    if not client:
        raise Exception("Supabase client not available")

    update_data = {
        'is_blacklisted': is_blacklisted,
        'blacklist_reason': reason if is_blacklisted else None
    }

    try:
        result = client.table('companies').update(update_data).eq('id', company_id).execute()
        return True
    except Exception as e:
        print(f"Error updating company blacklist: {e}")
        return False

def get_blacklisted_companies() -> pd.DataFrame:
    """Get all blacklisted companies for pipeline filtering"""
    client = get_client()
    if not client:
        return pd.DataFrame()

    try:
        result = client.table('companies').select('company_name, normalized_company_name, blacklist_reason').eq('is_blacklisted', True).execute()
        return pd.DataFrame(result.data or [])
    except Exception as e:
        print(f"Error fetching blacklisted companies: {e}")
        return pd.DataFrame()

def is_company_blacklisted(company_name: str) -> bool:
    """Check if a company is blacklisted"""
    if not company_name:
        return False

    blacklisted_df = get_blacklisted_companies()
    if blacklisted_df.empty:
        return False

    normalized_name = normalize_company_name(company_name)

    # Check both original and normalized names
    is_blacklisted = (
        blacklisted_df['company_name'].str.lower().str.contains(company_name.lower(), na=False).any() or
        blacklisted_df['normalized_company_name'].str.lower().str.contains(normalized_name.lower(), na=False).any()
    )

    return bool(is_blacklisted)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage companies rollup table')
    parser.add_argument('--create-table', action='store_true', help='Create companies table')
    parser.add_argument('--update', action='store_true', help='Update companies rollup data')
    parser.add_argument('--analytics', action='store_true', help='Show companies analytics')
    parser.add_argument('--fair-chance', action='store_true', help='Show fair chance companies')
    parser.add_argument('--market', help='Show companies in specific market')
    
    args = parser.parse_args()
    
    if args.create_table:
        client = get_client()
        if client:
            sql = create_companies_table_sql()
            print("🏗️ Creating companies table...")
            # Note: You'll need to run this SQL manually in Supabase dashboard
            print("Run this SQL in your Supabase dashboard:")
            print(sql)
        else:
            print("❌ Supabase client not available")
    
    elif args.update:
        update_companies_table()
    
    elif args.analytics:
        df = get_company_analytics()
        print(f"📊 Top {len(df)} Companies by Job Count:")
        print(df[['company_name', 'total_jobs', 'has_fair_chance', 'markets']].head(20).to_string(index=False))
    
    elif args.fair_chance:
        df = get_fair_chance_companies()
        print(f"🤝 Fair Chance Companies ({len(df)} total):")
        print(df[['company_name', 'fair_chance_jobs', 'total_jobs', 'markets']].to_string(index=False))
    
    elif args.market:
        df = get_market_company_breakdown(args.market)
        print(f"🌍 Companies in {args.market} ({len(df)} total):")
        print(df[['company_name', 'total_jobs', 'has_fair_chance']].to_string(index=False))
    
    else:
        print("Usage: python companies_rollup.py --help")