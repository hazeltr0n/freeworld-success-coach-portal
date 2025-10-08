#!/usr/bin/env python3
"""
Populate city_state column in location_markets table
Uses batched updates and progress tracking to avoid timeouts
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from supabase_utils import get_client
from zip_market_lookup import ZIP_TO_CITY_STATE

def fetch_single_zip(zip_code):
    """Fetch city/state for a single ZIP code from API"""
    try:
        url = f"https://ziptasticapi.com/{zip_code}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            city = data.get('city', '')
            state = data.get('state_short', data.get('state', ''))

            if city and state:
                return zip_code, f"{city}, {state}"

        return zip_code, None

    except Exception:
        return zip_code, None

print("🔍 STEP 1: Loading ZIPs from location_markets table...")
client = get_client()

# Get all ZIP rows from location_markets
result = client.table('location_markets').select('location_string, city_state').eq('location_type', 'zip').execute()

all_zips = {}
already_populated = 0

for row in result.data:
    zip_code = row['location_string']
    existing_city_state = row.get('city_state')

    if existing_city_state:
        already_populated += 1

    all_zips[zip_code] = existing_city_state

print(f"   ✅ Found {len(all_zips)} total ZIP rows")
print(f"   ✅ Already populated: {already_populated} ({already_populated/len(all_zips)*100:.1f}%)")

# STEP 2: Update with existing mappings from ZIP_TO_CITY_STATE
print(f"\n🔄 STEP 2: Updating with existing ZIP_TO_CITY_STATE mappings ({len(ZIP_TO_CITY_STATE)} available)...")

updates_needed = []
for zip_code in all_zips:
    if not all_zips[zip_code] and zip_code in ZIP_TO_CITY_STATE:
        updates_needed.append({
            'location_string': zip_code,
            'city_state': ZIP_TO_CITY_STATE[zip_code]
        })

print(f"   📊 Found {len(updates_needed)} ZIPs to update from existing mappings")

# Batch update in chunks of 500
BATCH_SIZE = 500
for i in range(0, len(updates_needed), BATCH_SIZE):
    batch = updates_needed[i:i+BATCH_SIZE]

    print(f"   🔄 Updating batch {i//BATCH_SIZE + 1}/{(len(updates_needed)-1)//BATCH_SIZE + 1} ({len(batch)} records)...", flush=True)

    # Update each record in the batch
    for update in batch:
        try:
            client.table('location_markets').update({
                'city_state': update['city_state']
            }).eq('location_string', update['location_string']).eq('location_type', 'zip').execute()
        except Exception as e:
            print(f"      ⚠️ Failed to update {update['location_string']}: {e}")

print(f"   ✅ Completed {len(updates_needed)} updates from existing mappings")

# STEP 3: Fetch unmapped ZIPs from API
print("\n🌐 STEP 3: Fetching unmapped ZIPs from API...")

# Reload to get current state after updates
result = client.table('location_markets').select('location_string, city_state').eq('location_type', 'zip').execute()

zips_to_fetch = []
for row in result.data:
    if not row.get('city_state'):
        zips_to_fetch.append(row['location_string'])

print(f"   📊 Need to fetch {len(zips_to_fetch)} ZIPs from API")

if zips_to_fetch:
    new_mappings = {}

    with ThreadPoolExecutor(max_workers=50) as executor:
        future_to_zip = {executor.submit(fetch_single_zip, zip_code): zip_code for zip_code in zips_to_fetch}

        completed = 0
        failed = 0
        for future in as_completed(future_to_zip):
            zip_code, city_state = future.result()
            completed += 1

            if city_state:
                new_mappings[zip_code] = city_state
            else:
                failed += 1

            if completed % 100 == 0:
                print(f"      Progress: {completed}/{len(zips_to_fetch)} ({failed} failed so far)", flush=True)

    print(f"\n   ✅ API fetch complete: {len(new_mappings)} succeeded, {failed} failed")

    # STEP 4: Batch update with new mappings
    print(f"\n💾 STEP 4: Updating database with {len(new_mappings)} new mappings...")

    update_list = [{'location_string': k, 'city_state': v} for k, v in new_mappings.items()]

    for i in range(0, len(update_list), BATCH_SIZE):
        batch = update_list[i:i+BATCH_SIZE]

        print(f"   🔄 Updating batch {i//BATCH_SIZE + 1}/{(len(update_list)-1)//BATCH_SIZE + 1} ({len(batch)} records)...", flush=True)

        for update in batch:
            try:
                client.table('location_markets').update({
                    'city_state': update['city_state']
                }).eq('location_string', update['location_string']).eq('location_type', 'zip').execute()
            except Exception as e:
                print(f"      ⚠️ Failed to update {update['location_string']}: {e}")

    print(f"   ✅ Completed {len(new_mappings)} new updates")

# STEP 5: Final verification
print("\n📊 FINAL VERIFICATION:")
result = client.table('location_markets').select('location_string, city_state').eq('location_type', 'zip').execute()

populated = sum(1 for row in result.data if row.get('city_state'))
total = len(result.data)

print(f"   Total ZIP rows: {total}")
print(f"   Populated: {populated} ({populated/total*100:.1f}%)")
print(f"   Unpopulated: {total - populated} ({(total-populated)/total*100:.1f}%)")

print("\n✅ SUCCESS! City/state population complete")
