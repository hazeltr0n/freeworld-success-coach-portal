#!/usr/bin/env python3
"""
Add show_prepared_for column to agent_profiles table
"""
import sys
import os
sys.path.append('/workspaces/freeworld-success-coach-portal')

from supabase_utils import get_client

def add_show_prepared_for_column():
    print("🔧 Adding show_prepared_for column to agent_profiles table...")

    client = get_client()
    if not client:
        print("❌ Failed to connect to Supabase")
        return False

    try:
        # Read the SQL migration file
        with open('add_show_prepared_for_column.sql', 'r') as f:
            sql_commands = f.read()

        print("📜 Executing SQL migration:")
        print(sql_commands)

        # Split by semicolon and execute each statement
        commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]

        for i, command in enumerate(commands, 1):
            if command.upper().startswith(('ALTER', 'COMMENT', 'UPDATE')):
                print(f"\n🔄 Executing command {i}/{len(commands)}...")
                print(f"   {command[:50]}...")

                # Execute the command using RPC call to avoid direct SQL execution limitations
                try:
                    # For ALTER TABLE, we need to use a different approach
                    if command.upper().startswith('ALTER'):
                        result = client.rpc('execute_sql', {'sql': command}).execute()
                    elif command.upper().startswith('COMMENT'):
                        # Skip comments for now as they might not be supported via RPC
                        print("   ⚠️ Skipping COMMENT command (may require direct DB access)")
                        continue
                    elif command.upper().startswith('UPDATE'):
                        # For UPDATE, try to use the table interface
                        result = client.table('agent_profiles').update({
                            'show_prepared_for': True
                        }).is_('show_prepared_for', None).execute()

                    print("   ✅ Command executed successfully")

                except Exception as e:
                    print(f"   ❌ Command failed: {e}")
                    # Try alternative approach for ALTER TABLE
                    if command.upper().startswith('ALTER'):
                        print("   🔄 Attempting alternative column addition...")
                        # We'll add the column by doing an update that includes the new field
                        # This will force the schema to recognize the new column
                        try:
                            # First, let's try to update one record to see if column exists
                            result = client.table('agent_profiles').select('id').limit(1).execute()
                            if result.data:
                                test_id = result.data[0]['id']
                                # Try to update with the new column
                                result = client.table('agent_profiles').update({
                                    'show_prepared_for': True
                                }).eq('id', test_id).execute()
                                print("   ✅ Column exists and update successful!")
                            else:
                                print("   ❌ No records found to test update")
                        except Exception as e2:
                            print(f"   ❌ Alternative approach failed: {e2}")
                            print("   ℹ️ The column may need to be added directly in Supabase dashboard")

        print("\n🧪 Testing the new column...")

        # Test by trying to select with the new column
        try:
            result = client.table('agent_profiles').select('id, agent_name, show_prepared_for').limit(3).execute()

            if result.data:
                print("✅ Successfully queried new show_prepared_for column!")
                print("📋 Sample records:")
                for record in result.data:
                    prepared_for = record.get('show_prepared_for', 'NULL')
                    print(f"  - {record.get('agent_name', 'Unknown')}: show_prepared_for = {prepared_for}")

                return True
            else:
                print("❌ No data returned from test query")
                return False

        except Exception as e:
            print(f"❌ Test query failed: {e}")
            print("ℹ️ Column may need to be added manually in Supabase dashboard")
            return False

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_show_prepared_for_column()
    if success:
        print("\n🎉 Migration completed successfully!")
        print("✅ show_prepared_for column is now available in agent_profiles table")
    else:
        print("\n❌ Migration may have failed - manual intervention might be needed")
        print("💡 You can add the column manually in Supabase dashboard:")
        print("   Column name: show_prepared_for")
        print("   Type: boolean")
        print("   Default: true")