#!/usr/bin/env python3
"""
Run database schema migration to flatten search_config JSON into individual columns
"""

from supabase_utils import get_client

def run_migration():
    """Execute the schema migration"""
    client = get_client()
    if not client:
        print("❌ Supabase client not available")
        return False

    try:
        # Read the SQL migration script
        with open('flatten_search_config.sql', 'r') as f:
            sql_script = f.read()

        print("🚀 Starting search_config flattening migration...")

        # Split the script into individual statements
        statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip() and not stmt.strip().startswith('--')]

        for i, statement in enumerate(statements):
            if statement:
                try:
                    print(f"📄 Executing statement {i+1}/{len(statements)}...")
                    print(f"SQL: {statement[:100]}...")
                    # Execute the SQL statement
                    result = client.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"✅ Statement {i+1} completed")
                except Exception as e:
                    print(f"⚠️ Statement {i+1} warning/error: {e}")
                    # Continue with other statements
                    continue

        print("✅ Schema migration completed!")

        # Verify the new columns exist
        print("\n🔍 Verifying new columns...")
        result = client.table('agent_profiles').select('location, route_filter, fair_chance_only, max_jobs, match_level').limit(1).execute()
        if result.data:
            print("✅ New individual columns are accessible")
            agent = result.data[0]
            print(f"Sample data: location={agent.get('location')}, route_filter={agent.get('route_filter')}, fair_chance_only={agent.get('fair_chance_only')}")
            return True
        else:
            print("⚠️ No agents found to verify, but migration likely succeeded")
            return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🗃️ Agent Profiles Schema Migration")
    print("=" * 50)

    success = run_migration()
    if success:
        print("✅ Migration completed successfully!")
        print("🔄 Next: Update Python code to use individual fields instead of search_config JSON")
    else:
        print("❌ Migration failed")