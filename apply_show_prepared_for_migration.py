#!/usr/bin/env python3
"""
Apply the show_prepared_for column migration directly to Supabase
"""
import sys
import os
sys.path.append('/workspaces/freeworld-success-coach-portal')

from supabase_utils import get_client

def apply_migration():
    print("🔧 Applying show_prepared_for column migration to Supabase...")

    client = get_client()
    if not client:
        print("❌ Failed to connect to Supabase")
        return False

    try:
        # Method 1: Try to add the column by performing an update with the new field
        # This should automatically add the column if it doesn't exist
        print("\n🔄 Method 1: Testing column addition via update...")

        # First, get a sample record to test with
        sample_result = client.table('agent_profiles').select('agent_uuid').limit(1).execute()

        if sample_result.data:
            test_uuid = sample_result.data[0]['agent_uuid']
            print(f"   Using test agent: {test_uuid}")

            # Try to update with the new show_prepared_for field
            update_result = client.table('agent_profiles').update({
                'show_prepared_for': True
            }).eq('agent_uuid', test_uuid).execute()

            print("   ✅ Successfully updated record with show_prepared_for field!")
            print(f"   Updated data: {update_result.data}")

            # Now update all other records to have the default value
            print("\n🔄 Setting default values for all other records...")
            bulk_result = client.table('agent_profiles').update({
                'show_prepared_for': True
            }).neq('agent_uuid', test_uuid).execute()

            print(f"   ✅ Updated {len(bulk_result.data) if bulk_result.data else 0} additional records")

        else:
            print("   ❌ No agent profiles found to test with")
            return False

        # Method 2: Verify the column exists by querying for it
        print("\n🧪 Verifying column exists...")
        verify_result = client.table('agent_profiles').select('agent_uuid, agent_name, show_prepared_for').limit(3).execute()

        if verify_result.data:
            print("✅ Migration successful! Column verified:")
            for record in verify_result.data:
                name = record.get('agent_name', 'Unknown')
                prepared_for = record.get('show_prepared_for', 'NULL')
                print(f"   - {name}: show_prepared_for = {prepared_for}")
            return True
        else:
            print("❌ Verification failed - no data returned")
            return False

    except Exception as e:
        print(f"❌ Migration failed with error: {e}")

        # If the direct approach fails, we might need to use RPC
        print("\n🔄 Trying alternative approach with RPC...")
        try:
            # Check if there's an RPC function we can use
            rpc_result = client.rpc('execute_sql', {
                'sql': 'ALTER TABLE agent_profiles ADD COLUMN IF NOT EXISTS show_prepared_for BOOLEAN DEFAULT TRUE;'
            }).execute()
            print("✅ RPC ALTER TABLE executed successfully")
            return True
        except Exception as rpc_error:
            print(f"❌ RPC approach also failed: {rpc_error}")
            print("\nℹ️  Manual intervention may be needed:")
            print("   1. Go to Supabase dashboard")
            print("   2. Navigate to agent_profiles table")
            print("   3. Add column: name='show_prepared_for', type='boolean', default=true")
            return False

if __name__ == "__main__":
    success = apply_migration()
    if success:
        print("\n🎉 Migration completed successfully!")
        print("✅ The show_prepared_for column is now available in the agent_profiles table")
        print("🔗 Portal links will now respect the prepared message setting")
    else:
        print("\n❌ Migration failed - manual intervention may be required")