#!/usr/bin/env python3
"""
Scheduled Google Jobs Scraper
Runs Tue/Thu at 2am Central
Submits to Outscraper API, poller processes results
"""

import os
import sys
import csv
import requests
from datetime import datetime, timezone
from supabase_utils import get_client

def main():
    print(f"\n{'='*80}")
    print(f"🌐 SCHEDULED GOOGLE JOBS SCRAPER")
    print(f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*80}\n")

    # Load query mapping
    csv_file = 'google_query_to_market.csv'
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        query_mapping = {row['Query']: row['Market'] for row in reader}

    queries = list(query_mapping.keys())
    print(f"📋 Loaded {len(queries)} city queries from {csv_file}")
    print(f"🎯 Mapped to {len(set(query_mapping.values()))} markets")

    # Submit to Outscraper
    api_key = os.getenv('OUTSCRAPER_API_KEY')
    if not api_key:
        print("❌ OUTSCRAPER_API_KEY not set")
        sys.exit(1)

    url = "https://api.outscraper.cloud/tasks"
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}

    payload = {
        "settings": {"output_extension": "json"},
        "org": "os",
        "service_name": "google_search_jobs_service",
        "est": 10,
        "limit_per_query": 50,
        "language": "en",
        "title": "",
        "queries": queries,
        "tags": "scheduledgoogle",
        "region": "US"
    }

    print(f"\n🚀 Submitting {len(queries)} queries to Outscraper...")
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    result = response.json()
    task_id = result.get('id')

    if not task_id:
        print(f"❌ No task ID in response: {result}")
        sys.exit(1)

    print(f"✅ Task created: {task_id}")

    # Save to async_job_queue for poller
    client = get_client()
    if client:
        job_record = {
            'job_type': 'google_jobs',
            'status': 'submitted',
            'request_id': task_id,
            'search_params': {
                'csv_mapping': csv_file,
                'limit_per_query': 50,
                'queries_count': len(queries),
                'markets_count': len(set(query_mapping.values()))
            },
            'coach_username': 'scheduled_google',
            'result_count': 0,
            'quality_job_count': 0,
            'created_at': datetime.now(timezone.utc).isoformat()
        }

        db_result = client.table('async_job_queue').insert(job_record).execute()
        job_id = db_result.data[0]['id'] if db_result.data else None
        print(f"💾 Saved to async_job_queue (ID: {job_id})")

    print(f"⏳ Poller will fetch results when ready (Tue/Thu 3:30am-2pm)")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
