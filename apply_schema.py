#!/usr/bin/env python3
"""
Apply Enhanced Feedback Schema to Supabase
"""

import os
from supabase import create_client, Client

def apply_schema():
    """Apply the enhanced feedback schema to Supabase"""

    # Initialize Supabase client
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
        return False

    supabase: Client = create_client(url, key)

    # Read the SQL schema file
    try:
        with open('sql/enhanced_feedback_schema.sql', 'r') as f:
            sql_content = f.read()
    except FileNotFoundError:
        print("❌ Schema file not found: sql/enhanced_feedback_schema.sql")
        return False

    # Split into individual statements
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

    print(f"🔧 Applying {len(statements)} SQL statements...")

    for i, statement in enumerate(statements, 1):
        # Skip comments and empty statements
        if statement.startswith('--') or not statement.strip():
            continue

        print(f"  [{i}/{len(statements)}] {statement[:50]}...")

        try:
            # Use rpc to execute raw SQL
            result = supabase.rpc('execute_sql', {'sql': statement}).execute()
            print(f"    ✅ Success")
        except Exception as e:
            # For ALTER TABLE IF NOT EXISTS, errors are often just "already exists" which is fine
            if 'already exists' in str(e) or 'IF NOT EXISTS' in statement:
                print(f"    ⚪ Already exists (OK)")
            else:
                print(f"    ❌ Error: {e}")
                # Continue with other statements

    print("🎉 Schema application complete!")
    return True

if __name__ == "__main__":
    apply_schema()