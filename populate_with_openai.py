#!/usr/bin/env python3
"""
Use OpenAI to look up city/state for remaining unmapped ZIP codes
OpenAI has geographic knowledge and can provide accurate ZIP → City, ST mappings
"""

from supabase_utils import get_client
import os
from openai import OpenAI
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st

# Get OpenAI key from streamlit secrets
try:
    openai_key = st.secrets["OPENAI_API_KEY"]
except:
    openai_key = os.getenv('OPENAI_API_KEY')

openai_client = OpenAI(api_key=openai_key)

def fetch_zips_with_openai(zip_batch):
    """Fetch city/state for a batch of ZIPs using OpenAI"""

    prompt = f"""For each ZIP code below, return the city and state in "City, ST" format.
Use proper title case for city names and 2-letter state abbreviations.
If a ZIP code is invalid or doesn't exist, return null for that entry.

ZIP codes: {', '.join(zip_batch)}

Return ONLY a JSON object mapping ZIP codes to "City, ST" strings (or null if invalid).
Example: {{"12345": "Schenectady, NY", "00000": null}}"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a geographic data expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        result_text = response.choices[0].message.content.strip()

        # Extract JSON from response (handle code blocks)
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()

        mappings = json.loads(result_text)
        return mappings

    except Exception as e:
        print(f"      ⚠️ Error fetching batch: {e}")
        return {}


print("🔍 STEP 1: Finding unmapped ZIPs from location_markets...")
client = get_client()

# Get unmapped ZIPs
result = client.table('location_markets').select('location_string, city_state').eq('location_type', 'zip').execute()

unmapped_zips = []
for row in result.data:
    if not row.get('city_state'):
        unmapped_zips.append(row['location_string'])

print(f"   ✅ Found {len(unmapped_zips)} unmapped ZIPs")

if not unmapped_zips:
    print("\n✅ All ZIPs already mapped!")
    exit(0)

# STEP 2: Try reverse lookup from city rows first (free)
print("\n🔍 STEP 2: Checking city rows for reverse mappings...")

city_result = client.table('location_markets').select('location_string, default_zips').eq('location_type', 'city').execute()

zip_to_city_from_cities = {}

for city_row in city_result.data:
    city_state = city_row.get('location_string', '')
    default_zips = city_row.get('default_zips', [])

    if city_state and default_zips:
        parts = city_state.split(',')
        if len(parts) == 2:
            city = parts[0].strip().title()
            state = parts[1].strip().upper()
            formatted_city_state = f"{city}, {state}"

            for zip_code in default_zips:
                zip_str = str(zip_code).zfill(5)
                if zip_str in unmapped_zips:
                    zip_to_city_from_cities[zip_str] = formatted_city_state

print(f"   ✅ Found {len(zip_to_city_from_cities)} mappings from city rows")

if zip_to_city_from_cities:
    print(f"\n💾 Updating {len(zip_to_city_from_cities)} ZIPs from city row reverse lookup...")

    BATCH_SIZE = 500
    updates = list(zip_to_city_from_cities.items())

    for i in range(0, len(updates), BATCH_SIZE):
        batch = updates[i:i+BATCH_SIZE]
        for zip_code, city_state in batch:
            try:
                client.table('location_markets').update({
                    'city_state': city_state
                }).eq('location_string', zip_code).eq('location_type', 'zip').execute()
            except Exception as e:
                print(f"      ⚠️ Failed to update {zip_code}: {e}")

        print(f"   🔄 Updated batch {i//BATCH_SIZE + 1}/{(len(updates)-1)//BATCH_SIZE + 1}")

    print(f"   ✅ Completed city row updates")

# STEP 3: Check remaining
print("\n🔍 STEP 3: Checking remaining unmapped ZIPs...")

result = client.table('location_markets').select('location_string, city_state').eq('location_type', 'zip').execute()

still_unmapped = []
for row in result.data:
    if not row.get('city_state'):
        still_unmapped.append(row['location_string'])

print(f"   ✅ Still unmapped: {len(still_unmapped)} ZIPs")

if still_unmapped:
    print(f"\n🤖 STEP 4: Using OpenAI to look up {len(still_unmapped)} remaining ZIPs (FAST parallel mode)...")

    # Process in batches of 50 ZIPs per API call, run 10 parallel threads
    OPENAI_BATCH_SIZE = 50
    all_mappings = {}

    # Create all batches
    batches = []
    for i in range(0, len(still_unmapped), OPENAI_BATCH_SIZE):
        batches.append(still_unmapped[i:i+OPENAI_BATCH_SIZE])

    print(f"   📊 Processing {len(batches)} batches in parallel (10 threads)...")

    # Process batches in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_batch = {executor.submit(fetch_zips_with_openai, batch): i for i, batch in enumerate(batches)}

        completed = 0
        for future in as_completed(future_to_batch):
            batch_idx = future_to_batch[future]
            mappings = future.result()

            for zip_code, city_state in mappings.items():
                if city_state:  # Skip nulls
                    all_mappings[zip_code] = city_state

            completed += 1
            print(f"   ✅ Batch {completed}/{len(batches)} complete ({len(all_mappings)} total mappings so far)", flush=True)

    print(f"\n   ✅ OpenAI lookup complete: {len(all_mappings)} total mappings found")

    # STEP 5: Update database
    if all_mappings:
        print(f"\n💾 STEP 5: Updating database with {len(all_mappings)} OpenAI mappings...")

        BATCH_SIZE = 500
        updates = list(all_mappings.items())

        for i in range(0, len(updates), BATCH_SIZE):
            batch = updates[i:i+BATCH_SIZE]

            for zip_code, city_state in batch:
                try:
                    client.table('location_markets').update({
                        'city_state': city_state
                    }).eq('location_string', zip_code).eq('location_type', 'zip').execute()
                except Exception as e:
                    print(f"      ⚠️ Failed to update {zip_code}: {e}")

            print(f"   🔄 Updated batch {i//BATCH_SIZE + 1}/{(len(updates)-1)//BATCH_SIZE + 1}")

        print(f"   ✅ Database update complete")

# FINAL VERIFICATION
print("\n📊 FINAL VERIFICATION:")
result = client.table('location_markets').select('location_string, city_state').eq('location_type', 'zip').execute()

populated = sum(1 for row in result.data if row.get('city_state'))
total = len(result.data)

print(f"   Total ZIP rows: {total}")
print(f"   Populated: {populated} ({populated/total*100:.1f}%)")
print(f"   Unpopulated: {total - populated} ({(total-populated)/total*100:.1f}%)")

if populated < total:
    # Show sample of what's still unmapped
    unmapped_samples = [row['location_string'] for row in result.data if not row.get('city_state')][:10]
    print(f"\n   Sample unmapped ZIPs: {unmapped_samples}")

print("\n✅ Population process complete!")
