#!/usr/bin/env python3
"""Debug script to examine Supabase coaches table structure."""

import sys
import os
sys.path.append('.')

# Set environment variables from secrets file
os.environ['SUPABASE_URL'] = 'https://yqbdltothngundojuebk.supabase.co'
os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlxYmRsdG90aG5ndW5kb2p1ZWJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU5Mjk4MzgsImV4cCI6MjA3MTUwNTgzOH0.PrJTCbSpmQYQJRM92KKB2TC2xX88IN2coYZGnVotAG8'

from supabase_utils import get_client

def debug_coaches_table():
    """Examine the coaches table structure and data."""
    print("🔍 Debugging Supabase coaches table...")

    client = get_client()
    if client is None:
        print("❌ Failed to get Supabase client")
        return

    print("✅ Supabase client connected")

    try:
        # Get all coaches
        print("\n📋 Fetching all coaches...")
        result = client.table('coaches').select('*').execute()

        if not result.data:
            print("⚠️ No coaches found in database")
            return

        print(f"📊 Found {len(result.data)} coaches")

        # Examine structure of first coach
        for i, coach in enumerate(result.data):
            print(f"\n👤 Coach {i+1}: {coach.get('username', 'unknown')}")
            print(f"📋 Raw data structure:")
            print(f"   Top-level keys: {list(coach.keys())}")

            # If there's a data field (JSON), examine it
            if 'data' in coach:
                data = coach['data']
                if isinstance(data, dict):
                    print(f"   Data field keys: {list(data.keys())}")

                    # Check for specific fields
                    has_batches = 'can_access_batches' in data
                    print(f"   Has can_access_batches: {has_batches}")

                    # Check for extra fields not in SuccessCoach
                    from user_management import SuccessCoach
                    import inspect
                    valid_fields = set(inspect.signature(SuccessCoach.__init__).parameters.keys()) - {'self'}
                    data_fields = set(data.keys())

                    extra_fields = data_fields - valid_fields
                    missing_fields = valid_fields - data_fields

                    if extra_fields:
                        print(f"   ⚠️ EXTRA fields in data: {extra_fields}")
                    if missing_fields:
                        print(f"   ⚠️ MISSING fields in data: {missing_fields}")

                    print(f"   ✅ Valid field count: {len(data_fields & valid_fields)}/{len(valid_fields)}")
                else:
                    print(f"   Data field type: {type(data)}")
                    print(f"   Data field value: {data}")

            print("-" * 50)

    except Exception as e:
        print(f"❌ Error examining coaches table: {e}")

if __name__ == "__main__":
    debug_coaches_table()