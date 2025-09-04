#!/usr/bin/env python3
"""
Debug Supabase Jobs Table
Check what match_level values actually exist in the jobs table
"""

import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

def check_supabase_jobs_data():
    """Check the actual data in the Supabase jobs table"""
    try:
        from supabase_utils import get_client
        client = get_client()
        
        if not client:
            print("❌ Cannot connect to Supabase")
            return
        
        print("🔍 ANALYZING SUPABASE JOBS TABLE")
        print("=" * 60)
        
        # Get overall match_level breakdown (no time filter)
        print("\n1. OVERALL MATCH LEVEL DISTRIBUTION (All Time)")
        print("-" * 50)
        
        query = client.table('jobs').select('match_level')
        
        all_matches = []
        page_size = 1000
        page = 0
        
        while True:
            start = page * page_size
            end = start + page_size - 1
            
            result = query.range(start, end).execute()
            batch = result.data or []
            
            if not batch:
                break
                
            all_matches.extend(batch)
            
            if len(batch) < page_size:
                break
            page += 1
        
        if not all_matches:
            print("❌ No jobs found in table!")
            return
        
        df = pd.DataFrame(all_matches)
        df['match_level'] = df['match_level'].fillna('null').str.lower()
        
        match_counts = df['match_level'].value_counts()
        total_jobs = len(df)
        
        print(f"Total jobs in table: {total_jobs:,}")
        print("\nMatch level breakdown:")
        for match_level, count in match_counts.items():
            percentage = (count / total_jobs) * 100
            print(f"  {match_level}: {count:,} ({percentage:.1f}%)")
        
        # Check recent data (last week)
        print("\n2. RECENT MATCH LEVEL DISTRIBUTION (Last 7 Days)")
        print("-" * 50)
        
        since = (datetime.now(timezone.utc) - timedelta(hours=168)).isoformat()
        recent_query = client.table('jobs').select('match_level,market,created_at').gte('created_at', since)
        
        recent_matches = []
        page = 0
        
        while True:
            start = page * page_size
            end = start + page_size - 1
            
            result = recent_query.range(start, end).execute()
            batch = result.data or []
            
            if not batch:
                break
                
            recent_matches.extend(batch)
            
            if len(batch) < page_size:
                break
            page += 1
        
        if not recent_matches:
            print("❌ No recent jobs found!")
            return
        
        recent_df = pd.DataFrame(recent_matches)
        recent_df['match_level'] = recent_df['match_level'].fillna('null').str.lower()
        
        recent_match_counts = recent_df['match_level'].value_counts()
        total_recent = len(recent_df)
        
        print(f"Recent jobs (7 days): {total_recent:,}")
        print("\nRecent match level breakdown:")
        for match_level, count in recent_match_counts.items():
            percentage = (count / total_recent) * 100
            print(f"  {match_level}: {count:,} ({percentage:.1f}%)")
        
        # Check by market
        print("\n3. TOP 5 MARKETS - RECENT MATCH BREAKDOWN")
        print("-" * 50)
        
        market_breakdown = recent_df.groupby(['market', 'match_level']).size().unstack(fill_value=0)
        market_totals = market_breakdown.sum(axis=1).sort_values(ascending=False)
        
        top_markets = market_totals.head(5)
        
        for market in top_markets.index:
            total = market_totals[market]
            print(f"\n{market} ({total:,} jobs):")
            
            if market in market_breakdown.index:
                for match_level in ['good', 'so-so', 'bad', 'null']:
                    if match_level in market_breakdown.columns:
                        count = market_breakdown.loc[market, match_level]
                        if count > 0:
                            pct = (count / total) * 100
                            print(f"  {match_level}: {count:,} ({pct:.1f}%)")
        
        # Check for any other unexpected values
        print("\n4. UNUSUAL MATCH LEVEL VALUES")
        print("-" * 50)
        
        unusual_values = [val for val in match_counts.index if val not in ['good', 'so-so', 'bad', 'null', 'unknown']]
        
        if unusual_values:
            print("Found unusual match_level values:")
            for val in unusual_values:
                count = match_counts[val]
                print(f"  '{val}': {count:,}")
        else:
            print("No unusual values found.")
        
        print("\n" + "=" * 60)
        print("✅ ANALYSIS COMPLETE")
        
    except Exception as e:
        print(f"❌ Error analyzing jobs table: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_supabase_jobs_data()