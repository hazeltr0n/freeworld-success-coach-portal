#!/usr/bin/env python3
"""
Check current database schema for enhanced feedback columns
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def check_schema():
    """Check if the enhanced feedback columns exist"""

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

    # Check jobs table columns
    print("\n🔍 Checking jobs table columns...")
    jobs_columns = [
        ('job_flagged', 'BOOLEAN for permanent negative feedback'),
        ('feedback_expired_links', 'INTEGER counter for job_expired feedback'),
        ('feedback_likes', 'INTEGER counter for positive feedback'),
        ('last_expired_feedback_at', 'TIMESTAMPTZ for expiry tracking')
    ]

    for col_name, description in jobs_columns:
        try:
            result = supabase.table('jobs').select(col_name).limit(1).execute()
            print(f"  ✅ {col_name} - EXISTS")
        except Exception as e:
            print(f"  ❌ {col_name} - MISSING ({description})")

    # Check agent_profiles table columns
    print("\n🔍 Checking agent_profiles table columns...")
    agent_columns = [
        ('total_applications', 'INTEGER counter for applications submitted'),
        ('last_application_at', 'TIMESTAMPTZ for last application time')
    ]

    for col_name, description in agent_columns:
        try:
            result = supabase.table('agent_profiles').select(col_name).limit(1).execute()
            print(f"  ✅ {col_name} - EXISTS")
        except Exception as e:
            print(f"  ❌ {col_name} - MISSING ({description})")

    print(f"\n📋 Schema Summary:")
    print(f"   If any columns are MISSING, apply sql/enhanced_feedback_schema.sql")
    print(f"   You can run it manually in Supabase Dashboard > SQL Editor")

    return True

if __name__ == "__main__":
    check_schema()