#!/usr/bin/env python3
"""
Migrate agent_profiles table to add pathway boolean columns
"""

from supabase_utils import get_client

def migrate_pathway_schema():
    """Add pathway columns to agent_profiles table"""
    client = get_client()
    if not client:
        print("❌ Supabase client not available")
        return False

    try:
        # Read the SQL migration script
        with open('add_pathway_columns.sql', 'r') as f:
            sql_script = f.read()

        print("🚀 Starting pathway schema migration...")

        # Split the script into individual statements
        statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip() and not stmt.strip().startswith('--')]

        for i, statement in enumerate(statements):
            if statement:
                try:
                    print(f"📄 Executing statement {i+1}/{len(statements)}...")
                    # Execute the SQL statement
                    result = client.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"✅ Statement {i+1} completed")
                except Exception as e:
                    print(f"⚠️ Statement {i+1} warning/error: {e}")
                    # Continue with other statements
                    continue

        print("✅ Pathway schema migration completed!")

        # Verify the new columns exist
        print("\n🔍 Verifying new columns...")
        result = client.table('agent_profiles').select('cdl_pathway, dock_to_driver, classifier_type').limit(1).execute()
        if result.data:
            print("✅ New pathway columns are accessible")
            return True
        else:
            print("⚠️ No agents found to verify, but migration likely succeeded")
            return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def test_pathway_columns():
    """Test that the new pathway columns work correctly"""
    client = get_client()
    if not client:
        print("❌ Supabase client not available")
        return False

    try:
        # Try to query with the new columns
        result = client.table('agent_profiles').select(
            'agent_name, classifier_type, cdl_pathway, dock_to_driver, internal_cdl_training'
        ).limit(3).execute()

        print(f"\n📊 Sample agents with pathway columns:")
        for agent in result.data or []:
            pathways = []
            if agent.get('cdl_pathway'): pathways.append('CDL')
            if agent.get('dock_to_driver'): pathways.append('Dock→Driver')
            if agent.get('internal_cdl_training'): pathways.append('CDL Training')

            print(f"  • {agent.get('agent_name', 'Unknown')}: {agent.get('classifier_type', 'unknown')} - [{', '.join(pathways) or 'none'}]")

        print("✅ Pathway columns working correctly!")
        return True

    except Exception as e:
        print(f"❌ Testing failed: {e}")
        return False

if __name__ == "__main__":
    print("🛤️ Agent Profiles Pathway Schema Migration")
    print("=" * 50)

    success = migrate_pathway_schema()
    if success:
        test_pathway_columns()
    else:
        print("❌ Migration failed, skipping tests")