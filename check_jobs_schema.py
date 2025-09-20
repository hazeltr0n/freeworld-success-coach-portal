#!/usr/bin/env python3
"""
Check the actual jobs table schema to understand column names
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def check_jobs_schema():
    """Check the actual jobs table schema"""

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env file")
        return False

    try:
        supabase = create_client(url, key)
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False

    # Get a sample record from jobs table to see the actual columns
    try:
        result = supabase.table('jobs').select('*').limit(1).execute()
        if result.data and len(result.data) > 0:
            job = result.data[0]
            print(f"\n📊 Jobs table columns ({len(job.keys())} total):")
            for i, column in enumerate(sorted(job.keys()), 1):
                value = job[column]
                value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                print(f"  {i:2d}. {column:<25} = {value_preview}")
        else:
            print("❌ No jobs found in table")

    except Exception as e:
        print(f"❌ Error accessing jobs table: {e}")

    return True

if __name__ == "__main__":
    check_jobs_schema()