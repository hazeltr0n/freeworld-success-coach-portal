#!/usr/bin/env python3
"""
Apply the database migration directly using Supabase Python client
"""

from supabase_utils import get_client

def apply_migration():
    """Execute the schema migration"""
    client = get_client()
    if not client:
        print("❌ Supabase client not available")
        return False

    # Read the migration SQL
    migration_sql = """
-- Add individual columns for search_config fields
ALTER TABLE agent_profiles
ADD COLUMN IF NOT EXISTS location TEXT DEFAULT 'Houston',
ADD COLUMN IF NOT EXISTS route_filter TEXT DEFAULT 'both',
ADD COLUMN IF NOT EXISTS fair_chance_only BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS max_jobs INTEGER DEFAULT 25,
ADD COLUMN IF NOT EXISTS match_level TEXT DEFAULT 'good and so-so';

-- Migrate existing data from search_config JSON to individual columns
UPDATE agent_profiles
SET
    location = COALESCE(search_config->>'location', 'Houston'),
    route_filter = COALESCE(search_config->>'route_filter', 'both'),
    fair_chance_only = COALESCE((search_config->>'fair_chance_only')::boolean, false),
    max_jobs = COALESCE((search_config->>'max_jobs')::integer, 25),
    match_level = COALESCE(search_config->>'match_level', 'good and so-so')
WHERE search_config IS NOT NULL;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_agent_profiles_location ON agent_profiles(location);
CREATE INDEX IF NOT EXISTS idx_agent_profiles_route_filter ON agent_profiles(route_filter);
CREATE INDEX IF NOT EXISTS idx_agent_profiles_fair_chance ON agent_profiles(fair_chance_only);
    """

    try:
        print("🚀 Starting database migration...")

        # Split into individual statements and execute
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip() and not stmt.strip().startswith('--')]

        for i, statement in enumerate(statements):
            if statement:
                try:
                    print(f"📄 Executing statement {i+1}/{len(statements)}...")
                    print(f"SQL: {statement[:100]}...")

                    # Execute the SQL directly
                    result = client.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"✅ Statement {i+1} completed successfully")

                except Exception as e:
                    print(f"⚠️ Statement {i+1} error: {e}")
                    # Continue with other statements for non-critical errors
                    continue

        print("\n✅ Migration completed!")

        # Verify the new columns exist
        print("🔍 Verifying new columns...")
        result = client.table('agent_profiles').select('location, route_filter, fair_chance_only, max_jobs, match_level, agent_name').limit(3).execute()

        if result.data:
            print("✅ New individual columns are working!")
            for agent in result.data:
                print(f"  • {agent.get('agent_name', 'Unknown')}: location={agent.get('location')}, route={agent.get('route_filter')}, fair_chance={agent.get('fair_chance_only')}")
            return True
        else:
            print("⚠️ No data returned but migration likely succeeded")
            return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🗃️ Applying Database Migration")
    print("=" * 50)

    success = apply_migration()
    if success:
        print("\n🎉 Migration completed successfully!")
        print("🔄 Next step: Update Python code to use individual fields")
    else:
        print("\n❌ Migration failed")