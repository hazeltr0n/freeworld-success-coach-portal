#!/usr/bin/env python3
"""
Apply Enhanced Feedback Schema to Supabase - Simple Version
"""

import streamlit as st
from supabase import create_client

def apply_schema():
    """Apply the enhanced feedback schema using individual ALTER TABLE statements"""

    # Use Streamlit secrets (same as the app)
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]  # Try anon key first
    except:
        print("❌ Could not load Supabase credentials from streamlit secrets")
        return False

    try:
        supabase = create_client(url, key)
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False

    # List of individual SQL statements to execute
    statements = [
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_flagged BOOLEAN DEFAULT FALSE",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS feedback_expired_links INTEGER DEFAULT 0",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS feedback_likes INTEGER DEFAULT 0",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS last_expired_feedback_at TIMESTAMPTZ",
        "ALTER TABLE agent_profiles ADD COLUMN IF NOT EXISTS total_applications INTEGER DEFAULT 0",
        "ALTER TABLE agent_profiles ADD COLUMN IF NOT EXISTS last_application_at TIMESTAMPTZ"
    ]

    print(f"🔧 Applying {len(statements)} schema changes...")

    for i, statement in enumerate(statements, 1):
        print(f"  [{i}/{len(statements)}] {statement[:60]}...")

        try:
            # Test with a simple query first to see if we have proper access
            if i == 1:
                # Test basic table access
                test_result = supabase.table('jobs').select('id').limit(1).execute()
                print(f"    ✅ Table access confirmed")

            # For ALTER TABLE, we need to use a different approach
            # Let's check if columns already exist first
            if 'job_flagged' in statement:
                # Check if jobs table has the column already
                try:
                    test = supabase.table('jobs').select('job_flagged').limit(1).execute()
                    print(f"    ⚪ Column job_flagged already exists")
                    continue
                except:
                    print(f"    🔧 Column job_flagged needs to be created")

            elif 'feedback_expired_links' in statement:
                try:
                    test = supabase.table('jobs').select('feedback_expired_links').limit(1).execute()
                    print(f"    ⚪ Column feedback_expired_links already exists")
                    continue
                except:
                    print(f"    🔧 Column feedback_expired_links needs to be created")

            elif 'feedback_likes' in statement:
                try:
                    test = supabase.table('jobs').select('feedback_likes').limit(1).execute()
                    print(f"    ⚪ Column feedback_likes already exists")
                    continue
                except:
                    print(f"    🔧 Column feedback_likes needs to be created")

            elif 'last_expired_feedback_at' in statement:
                try:
                    test = supabase.table('jobs').select('last_expired_feedback_at').limit(1).execute()
                    print(f"    ⚪ Column last_expired_feedback_at already exists")
                    continue
                except:
                    print(f"    🔧 Column last_expired_feedback_at needs to be created")

            elif 'total_applications' in statement:
                try:
                    test = supabase.table('agent_profiles').select('total_applications').limit(1).execute()
                    print(f"    ⚪ Column total_applications already exists")
                    continue
                except:
                    print(f"    🔧 Column total_applications needs to be created")

            elif 'last_application_at' in statement:
                try:
                    test = supabase.table('agent_profiles').select('last_application_at').limit(1).execute()
                    print(f"    ⚪ Column last_application_at already exists")
                    continue
                except:
                    print(f"    🔧 Column last_application_at needs to be created")

            print(f"    ⚠️  Cannot create columns with current permissions - need admin access")

        except Exception as e:
            print(f"    ❌ Error: {e}")

    print("📋 Schema check complete!")
    print("\n💡 To apply schema changes, run the SQL manually in Supabase dashboard:")
    print("   1. Go to Supabase Dashboard > SQL Editor")
    print("   2. Copy and paste sql/enhanced_feedback_schema.sql")
    print("   3. Click Run")

    return True

if __name__ == "__main__":
    apply_schema()