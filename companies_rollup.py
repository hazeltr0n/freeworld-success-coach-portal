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

def extract_market_from_location(location: str) -> str:
    """Extract market name from job location"""
    if not location or pd.isna(location):
        return "Unknown"
    
    # Common market mappings
    market_mapping = {
        'houston': 'Houston',
        'dallas': 'Dallas', 
        'las vegas': 'Las Vegas',
        'bay area': 'Bay Area',
        'stockton': 'Stockton',
        'denver': 'Denver',
        'newark': 'Newark',
        'phoenix': 'Phoenix',
        'trenton': 'Trenton',
        'inland empire': 'Inland Empire',
        'san francisco': 'Bay Area',
        'oakland': 'Bay Area',
        'san jose': 'Bay Area'
    }
    
    location_lower = str(location).lower()
    
    # Check for direct market matches
    for key, market in market_mapping.items():
        if key in location_lower:
            return market
    
    # Extract state/city
    parts = str(location).split(',')
    if len(parts) >= 1:
        city = parts[0].strip().title()
        return city if city else "Unknown"
    
    return "Unknown"

def analyze_jobs_for_companies() -> pd.DataFrame:
    """Analyze jobs table and create companies rollup data"""
    client = get_client()
    if not client:
        raise Exception("Supabase client not available")
    
    print("🔍 Fetching jobs data from Supabase...")
    
    # Get jobs from the last 60 days to focus on active/recent companies
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    
    # Fetch jobs data - use correct Supabase field names
    result = client.table('jobs').select(
        'company, location, job_title, match_level, route_type, fair_chance, salary, created_at, success_coach'
    ).gte('created_at', cutoff_date).execute()
    
    jobs_data = result.data or []
    print(f"📊 Analyzing {len(jobs_data)} jobs from the last 60 days...")
    
    if not jobs_data:
        print("⚠️ No jobs data found")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(jobs_data)
    
    # Normalize company names
    df['normalized_company'] = df['company'].apply(normalize_company_name)
    
    # Extract markets
    df['market'] = df['location'].apply(extract_market_from_location)
    
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
        
        # Date ranges
        dates = pd.to_datetime(company_jobs['created_at'])
        oldest_date = dates.min()
        newest_date = dates.max()
        
        # Salary averages
        salary_data = company_jobs[['salary_min', 'salary_max']].dropna()
        avg_salary_min = salary_data['salary_min'].mean() if not salary_data.empty else None
        avg_salary_max = salary_data['salary_max'].mean() if not salary_data.empty else None
        
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
            'oldest_job_date': oldest_date.isoformat() if pd.notna(oldest_date) else None,
            'newest_job_date': newest_date.isoformat() if pd.notna(newest_date) else None,
            'avg_salary_min': float(avg_salary_min) if pd.notna(avg_salary_min) else None,
            'avg_salary_max': float(avg_salary_max) if pd.notna(avg_salary_max) else None,
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

def get_company_analytics(company_name: str = None, limit: int = 50) -> pd.DataFrame:
    """Get companies data with optional filtering"""
    client = get_client()
    if not client:
        raise Exception("Supabase client not available")
    
    query = client.table('companies').select('*').order('total_jobs', desc=True)
    
    if company_name:
        query = query.ilike('normalized_company_name', f'%{company_name}%')
    
    if limit:
        query = query.limit(limit)
    
    result = query.execute()
    return pd.DataFrame(result.data or [])

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