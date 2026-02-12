#!/usr/bin/env python3
"""
Migration script to add lookback_hours field to agent_profiles table
This ensures agent portal respects the same lookback period as home page memory search
"""

import os
from supabase import create_client

def add_lookback_hours_field():
    """Add lookback_hours field to agent_profiles table with default value of 168"""

    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')

    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        return False

    client = create_client(url, key)

    try:
        print("🔧 Adding lookback_hours field to agent_profiles table...")

        # Check if column already exists by trying to select it
        try:
            test_result = client.table('agent_profiles').select('lookback_hours').limit(1).execute()
            print("✅ lookback_hours column already exists")
            return True
        except Exception:
            print("📝 lookback_hours column doesn't exist, adding it...")

        # Add the column using raw SQL (Supabase doesn't support ALTER TABLE directly)
        # This would need to be run manually in Supabase SQL editor:
        sql_command = """
        ALTER TABLE agent_profiles
        ADD COLUMN IF NOT EXISTS lookback_hours INTEGER DEFAULT 168;

        COMMENT ON COLUMN agent_profiles.lookback_hours IS 'Memory search lookback period in hours (default 168h to match home page)';
        """

        print("📋 SQL to run in Supabase SQL editor:")
        print(sql_command)

        # Try to update existing records to have default value
        print("🔄 Setting default lookback_hours=168 for existing agents...")

        # Get all agents without lookback_hours set
        result = client.table('agent_profiles').select('agent_uuid').execute()

        if result.data:
            # Update all existing agents to have default 168h lookback
            update_result = client.table('agent_profiles').update({
                'lookback_hours': 168
            }).is_('lookback_hours', 'null').execute()

            print(f"✅ Updated {len(update_result.data or [])} existing agents with default lookback_hours=168")

        return True

    except Exception as e:
        print(f"❌ Error adding lookback_hours field: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Agent Profiles Lookback Hours Migration")
    print("=" * 50)

    success = add_lookback_hours_field()

    if success:
        print("\n✅ Migration completed successfully!")
        print("\n🔧 Manual step required:")
        print("   Run this SQL in Supabase SQL editor:")
        print("   ALTER TABLE agent_profiles ADD COLUMN IF NOT EXISTS lookback_hours INTEGER DEFAULT 168;")
    else:
        print("\n❌ Migration failed!")