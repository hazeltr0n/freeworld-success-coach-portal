#!/usr/bin/env python3
"""
Discover actual Airtable field names for Free Agents table
"""

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def discover_airtable_fields():
    """Discover and display all Airtable field names"""
    try:
        from pyairtable import Api
        
        api_key = os.getenv('AIRTABLE_API_KEY')
        base_id = os.getenv('AIRTABLE_BASE_ID')
        table_id = os.getenv('AIRTABLE_CANDIDATES_TABLE_ID', 'tbl3fhAB14MkkewN1')
        
        print(f"🔍 Connecting to Airtable Free Agents table...")
        print(f"   Base ID: {base_id}")
        print(f"   Table ID: {table_id}")
        
        client = Api(api_key).table(base_id, table_id)
        
        # Fetch first few records to see field structure
        records = list(client.iterate(page_size=3))
        
        if not records:
            print("❌ No records found")
            return
        
        print(f"\n📊 Found {len(records)} sample records")
        
        # Collect all unique field names
        all_fields = set()
        for record in records:
            fields = record.get('fields', {})
            all_fields.update(fields.keys())
        
        # Sort fields alphabetically
        sorted_fields = sorted(all_fields)
        
        print(f"\n📋 All Airtable fields ({len(sorted_fields)} total):")
        for i, field in enumerate(sorted_fields, 1):
            print(f"  {i:2d}. {field}")
        
        print(f"\n🔍 Sample record values:")
        sample_record = records[0].get('fields', {})
        key_fields = ['uuid', 'fullName', 'email', 'city', 'state', 'firstName', 'lastName']
        
        for field in key_fields:
            value = sample_record.get(field, 'NOT FOUND')
            print(f"  {field}: {value}")
        
        print(f"\n💡 Suggested mapping to Supabase agent_profiles:")
        mapping = {
            'agent_uuid': 'uuid',
            'agent_name': 'fullName', 
            'agent_email': 'email',
            'agent_city': 'city',
            'agent_state': 'state'
        }
        
        for supabase_field, airtable_field in mapping.items():
            status = "✓" if airtable_field in all_fields else "❌"
            print(f"  {status} {supabase_field} ← {airtable_field}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    # Set the table ID
    os.environ['AIRTABLE_CANDIDATES_TABLE_ID'] = 'tbl3fhAB14MkkewN1'
    discover_airtable_fields()