#!/usr/bin/env python3
"""
Create a SQL executor function in Supabase to run DDL commands
"""
import sys
import os
sys.path.append('/workspaces/freeworld-success-coach-portal')

from supabase_utils import get_client

def create_sql_executor():
    print("🔧 Creating SQL executor function in Supabase...")

    client = get_client()
    if not client:
        print("❌ Failed to connect to Supabase")
        return False

    try:
        # Create the SQL executor function using the SQL editor
        sql_function = """
        CREATE OR REPLACE FUNCTION execute_sql(sql_command text)
        RETURNS json
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        BEGIN
          EXECUTE sql_command;
          RETURN json_build_object('success', true, 'message', 'SQL executed successfully');
        EXCEPTION WHEN OTHERS THEN
          RETURN json_build_object('success', false, 'error', SQLERRM);
        END;
        $$;
        """

        print("📝 Creating SQL executor function...")
        print("SQL Function:")
        print(sql_function)

        # Try to create the function via RPC (this might work if we have the right permissions)
        try:
            # We can't create functions directly, but let's see if we can execute the ALTER TABLE directly
            print("\n🔄 Attempting to execute ALTER TABLE directly...")

            # Some Supabase instances allow direct SQL execution via a special endpoint
            # Let's try using the PostgREST interface differently

            # Alternative: Use a direct SQL execution approach if available
            alter_sql = "ALTER TABLE agent_profiles ADD COLUMN show_prepared_for BOOLEAN DEFAULT TRUE;"

            print(f"Executing: {alter_sql}")

            # This approach uses the PostgREST interface to execute SQL
            headers = {
                'Content-Type': 'application/json',
                'Prefer': 'return=minimal'
            }

            # Try making a raw SQL request
            import requests
            url = client.url.rstrip('/') + '/rest/v1/rpc/sql'
            auth_header = f"Bearer {client.supabase_key}"

            response = requests.post(
                url,
                json={'sql': alter_sql},
                headers={
                    **headers,
                    'Authorization': auth_header,
                    'apikey': client.supabase_key
                }
            )

            if response.status_code == 200:
                print("✅ Direct SQL execution successful!")
                return True
            else:
                print(f"❌ Direct SQL failed: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"❌ Direct execution failed: {e}")

        print("\nℹ️  Unable to execute DDL commands via API")
        print("📋 Manual steps required:")
        print("   1. Open Supabase Dashboard")
        print("   2. Go to SQL Editor")
        print("   3. Run this SQL:")
        print("      ALTER TABLE agent_profiles ADD COLUMN show_prepared_for BOOLEAN DEFAULT TRUE;")
        print("   4. Or go to Table Editor -> agent_profiles -> Add Column:")
        print("      - Name: show_prepared_for")
        print("      - Type: boolean")
        print("      - Default: true")

        return False

    except Exception as e:
        print(f"❌ Function creation failed: {e}")
        return False

if __name__ == "__main__":
    create_sql_executor()