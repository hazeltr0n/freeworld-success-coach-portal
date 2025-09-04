#!/usr/bin/env python3
"""Test Google Jobs API independently before integration"""

import os
import sys
import pandas as pd
import requests
from pathlib import Path

def load_secrets():
    """Load secrets from .streamlit/secrets.toml"""
    secrets_file = Path('.streamlit/secrets.toml')
    if secrets_file.exists():
        try:
            import toml
            secrets = toml.load(secrets_file)
            for key, value in secrets.items():
                os.environ[key] = str(value)
            print(f"✅ Loaded {len(secrets)} secrets")
            return True
        except ImportError:
            print("⚠️ toml module not available. Install with: pip install toml")
            return False
        except Exception as e:
            print(f"❌ Failed to load secrets: {e}")
            return False
    else:
        print("❌ No secrets file found")
        return False

def load_market_cities():
    """Load market-city mapping from CSV"""
    try:
        df = pd.read_csv('market_cities.csv')
        print(f"✅ Loaded {len(df)} city mappings")
        return df
    except Exception as e:
        print(f"❌ Failed to load market_cities.csv: {e}")
        return None

def build_google_queries(search_terms, market, radius=50):
    """Build queries based on radius from CSV"""
    df = load_market_cities()
    if df is None:
        return [f"{search_terms} {market}"]
    
    # Extract market name (could be "Houston, TX" or just "Houston")
    market_key = market.split(',')[0].strip()
    
    # Filter cities based on radius
    radius_column = f'within_{radius}'
    
    # Get cities for this market within the radius
    market_cities = df[
        (df['market'] == market_key) & 
        (df[radius_column] == True)
    ]
    
    if len(market_cities) == 0:
        print(f"⚠️ No cities found for market '{market_key}' with radius {radius}")
        return [f"{search_terms} {market}"]
    
    # Build queries
    queries = []
    for _, row in market_cities.iterrows():
        query = f"{search_terms} {row['city']} {row['state']}"
        queries.append(query)
    
    print(f"📍 Market: {market}, Radius: {radius}mi → {len(queries)} queries")
    print(f"   Cities: {', '.join([row['city'] for _, row in market_cities.head(5).iterrows()])}{'...' if len(market_cities) > 5 else ''}")
    
    return queries

def test_single_query():
    """Test single city query"""
    print("\n=== TEST 1: Single Query ===")
    
    api_key = os.getenv('OUTSCRAPER_API_KEY')
    if not api_key:
        print("❌ OUTSCRAPER_API_KEY not found")
        return False
    
    try:
        response = requests.get(
            "https://api.outscraper.cloud/google-search-jobs",
            headers={'X-API-KEY': api_key},
            params={
                'query': 'CDL Driver Dallas TX',
                'pagesPerQuery': 1,
                'language': 'en',
                'region': 'US',
                'async': 'false'
            },
            timeout=30
        )
        
        print(f"📡 API Response: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"📊 Response structure: {type(data)}")
                
                if data.get('data'):
                    print(f"📊 Data array length: {len(data['data'])}")
                    
                    # Google returns nested: data[query_index][job_index]
                    jobs = data['data'][0] if isinstance(data['data'][0], list) else [data['data'][0]]
                    
                    print(f"✅ Single query result: {len(jobs)} jobs")
                    
                    if jobs and len(jobs) > 0:
                        first_job = jobs[0]
                        print(f"📋 Available fields: {list(first_job.keys())}")
                        print(f"📋 Sample job:")
                        print(f"   Title: {first_job.get('title', 'N/A')}")
                        print(f"   Company: {first_job.get('company', 'N/A')}")
                        print(f"   Location: {first_job.get('location', 'N/A')}")
                        
                        apply_urls = first_job.get('apply_urls', 'N/A')
                        if apply_urls and apply_urls != 'N/A':
                            print(f"   Apply URLs: {str(apply_urls)[:100]}...")
                        else:
                            print(f"   Apply URLs: {apply_urls}")
                    return True
                else:
                    print("❌ No data in response")
                    return False
                    
            except Exception as json_error:
                print(f"❌ JSON parsing failed: {json_error}")
                print(f"📋 Raw response (first 500 chars): {response.text[:500]}")
                return False
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"📋 Error response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_multi_city_batch():
    """Test multi-city batch query using CSV data"""
    print("\n=== TEST 2: Multi-City Batch (CSV-based) ===")
    
    api_key = os.getenv('OUTSCRAPER_API_KEY')
    if not api_key:
        print("❌ OUTSCRAPER_API_KEY not found")
        return False
    
    # Build queries using CSV data for Dallas with radius=25
    queries = build_google_queries("CDL Driver", "Dallas, TX", radius=25)
    
    if len(queries) == 0:
        print("❌ No queries generated")
        return False
    
    # Limit to first 5 queries for testing
    test_queries = queries[:5]
    
    try:
        response = requests.get(
            "https://api.outscraper.cloud/google-search-jobs",
            headers={'X-API-KEY': api_key},
            params={
                'query': test_queries,
                'pagesPerQuery': 1,
                'language': 'en',
                'region': 'US',
                'async': 'false'
            },
            timeout=60
        )
        
        print(f"📡 Batch API Response: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                total_jobs = 0
                query_results = []
                
                for i, query_result in enumerate(data.get('data', [])):
                    if isinstance(query_result, list):
                        jobs_count = len(query_result)
                        total_jobs += jobs_count
                        query_results.append(jobs_count)
                        print(f"   Query {i+1} ({test_queries[i] if i < len(test_queries) else 'Unknown'}): {jobs_count} jobs")
                
                print(f"✅ Batch total: {total_jobs} jobs from {len(test_queries)} queries")
                print(f"💰 Cost: $0.005 (Indeed equivalent: ${len(test_queries) * 0.10:.2f})")
                print(f"💰 Cost savings: {((len(test_queries) * 0.10) - 0.005) / (len(test_queries) * 0.10) * 100:.1f}%")
                
                return True
                
            except Exception as json_error:
                print(f"❌ JSON parsing failed: {json_error}")
                return False
                
        else:
            print(f"❌ Batch API Error: {response.status_code}")
            print(f"📋 Error response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Batch request timed out")
        return False
    except Exception as e:
        print(f"❌ Batch request failed: {e}")
        return False

def test_csv_mapping():
    """Test CSV mapping functionality"""
    print("\n=== TEST 3: CSV Mapping ===")
    
    df = load_market_cities()
    if df is None:
        return False
    
    # Test different markets and radii
    test_cases = [
        ("Houston", 25),
        ("Houston", 50),
        ("Dallas", 25),
        ("Dallas", 50),
        ("Austin", 100),
        ("Bay Area", 25)
    ]
    
    for market, radius in test_cases:
        queries = build_google_queries("CDL Driver", market, radius)
        print(f"   {market} @ {radius}mi: {len(queries)} cities")
    
    return True

def main():
    """Run all tests"""
    print("🧪 Google Jobs API Test Suite")
    print("=" * 50)
    
    # Load secrets
    if not load_secrets():
        print("❌ Cannot proceed without API keys")
        return
    
    # Test CSV mapping
    csv_ok = test_csv_mapping()
    
    # Test single query
    single_ok = test_single_query()
    
    # Test batch query
    batch_ok = test_multi_city_batch()
    
    # Summary
    print(f"\n🎯 TEST RESULTS:")
    print(f"   CSV Mapping: {'✅ PASS' if csv_ok else '❌ FAIL'}")
    print(f"   Single Query: {'✅ PASS' if single_ok else '❌ FAIL'}")
    print(f"   Batch Query: {'✅ PASS' if batch_ok else '❌ FAIL'}")
    
    if all([csv_ok, single_ok, batch_ok]):
        print(f"\n🎉 All tests passed! Google Jobs API is ready for integration.")
    else:
        print(f"\n❌ Some tests failed. Check configuration and API access.")

if __name__ == "__main__":
    main()