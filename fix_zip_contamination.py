#!/usr/bin/env python3
"""
Fix contaminated ZIP market lookups that contain other ZIP codes in the market list
This fixes the root cause of Indeed jobs getting ZIP codes as market names

Example contaminated entry:
  ZIP 95210: ['Sacramento', '95820', 'Bay Area', 'Stockton']
                            ^^^^^^ - This is a ZIP, not a market!

Clean version should be:
  ZIP 95210: ['Stockton']  # Based on location data
"""

import json
import re
from zip_market_lookup import ZIP_TO_MARKETS, ZIP_TO_CITY_STATE

# Valid market names (from our 10-market system)
VALID_MARKETS = {
    'Dallas', 'Houston', 'Phoenix', 'Denver', 'Las Vegas',
    'Stockton', 'Bay Area', 'Inland Empire', 'Trenton', 'Newark',
    'Sacramento',  # Also valid
}

# State to markets mapping for smart assignment
STATE_TO_MARKETS = {
    'TX': ['Dallas', 'Houston'],
    'CA': ['Bay Area', 'Stockton', 'Inland Empire', 'Sacramento'],
    'NJ': ['Newark', 'Trenton'],
    'AZ': ['Phoenix'],
    'CO': ['Denver'],
    'NV': ['Las Vegas']
}

def extract_state_from_city_state(city_state: str) -> str:
    """Extract state abbreviation from 'City, ST' format"""
    if not city_state or ', ' not in city_state:
        return ''

    parts = city_state.split(', ')
    if len(parts) >= 2:
        state = parts[-1].strip()
        # Handle "Dallas-Fort Worth, TX 75006" format
        if ' ' in state:
            state = state.split()[0]
        return state
    return ''

def select_best_market(zip_code: str, markets: list, city_state: str = '') -> list:
    """
    Select the correct market(s) from a contaminated list

    Args:
        zip_code: The ZIP code being processed
        markets: List that may contain market names AND ZIP codes
        city_state: Location string like "Sacramento, CA"

    Returns:
        Clean list with only valid market names
    """
    # Filter out ZIP codes - keep only valid market names
    valid_markets_in_list = [m for m in markets if m in VALID_MARKETS]

    # If no valid markets, use state-based assignment
    if not valid_markets_in_list and city_state:
        state = extract_state_from_city_state(city_state)
        if state in STATE_TO_MARKETS:
            # For now, return all markets in that state
            # Later we can refine with distance calculations
            return STATE_TO_MARKETS[state]

    # If we found valid markets, deduplicate and return
    if valid_markets_in_list:
        return list(dict.fromkeys(valid_markets_in_list))  # Preserve order, remove dupes

    # Last resort: return first non-ZIP market if any
    non_zip_markets = [m for m in markets if not (m.isdigit() and len(m) == 5)]
    if non_zip_markets:
        return [non_zip_markets[0]]

    # Absolute fallback: empty list (will need manual review)
    return []

def main():
    print('🔍 Analyzing ZIP_TO_MARKETS for contamination...\n')

    # Find all contaminated ZIPs
    contaminated = []
    for zip_code, markets in ZIP_TO_MARKETS.items():
        # Check if market list contains any ZIP codes
        has_zip = any(m.isdigit() and len(m) == 5 for m in markets)
        if has_zip:
            contaminated.append(zip_code)

    print(f'Found {len(contaminated)} contaminated ZIP entries')

    # Show breakdown
    from collections import Counter
    zip_codes_in_markets = []
    for zip_code, markets in ZIP_TO_MARKETS.items():
        for market in markets:
            if market.isdigit() and len(market) == 5:
                zip_codes_in_markets.append(market)

    counter = Counter(zip_codes_in_markets)
    print(f'\nTop contaminant ZIPs:')
    for zip_code, count in counter.most_common(10):
        city_state = ZIP_TO_CITY_STATE.get(zip_code, 'Unknown')
        print(f'  ZIP {zip_code} ({city_state}): appears {count} times')

    print(f'\nSample contaminated entries (before):')
    for zip_code in list(contaminated)[:5]:
        markets = ZIP_TO_MARKETS[zip_code]
        city_state = ZIP_TO_CITY_STATE.get(zip_code, 'Unknown')
        print(f'  ZIP {zip_code} ({city_state}): {markets}')

    # Ask for confirmation
    response = input(f'\nClean up {len(contaminated)} contaminated ZIPs? (yes/no): ')
    if response.lower() != 'yes':
        print('Aborted')
        return

    # Clean up contaminated ZIPs
    print(f'\n🧹 Cleaning up {len(contaminated)} ZIPs...')
    fixed = {}
    unchanged = {}
    empty = {}

    for zip_code in contaminated:
        old_markets = ZIP_TO_MARKETS[zip_code]
        city_state = ZIP_TO_CITY_STATE.get(zip_code, '')

        new_markets = select_best_market(zip_code, old_markets, city_state)

        if not new_markets:
            empty[zip_code] = (old_markets, city_state)
        elif new_markets != old_markets:
            fixed[zip_code] = (old_markets, new_markets, city_state)
        else:
            unchanged[zip_code] = old_markets

    print(f'\n✅ Results:')
    print(f'  Fixed: {len(fixed)} ZIPs')
    print(f'  Unchanged: {len(unchanged)} ZIPs')
    print(f'  Empty (need review): {len(empty)} ZIPs')

    if empty:
        print(f'\n⚠️  ZIPs that resulted in empty market lists:')
        for zip_code, (old_markets, city_state) in list(empty.items())[:10]:
            print(f'  ZIP {zip_code} ({city_state}): {old_markets}')

    print(f'\nSample fixes:')
    for zip_code, (old, new, city_state) in list(fixed.items())[:10]:
        print(f'  ZIP {zip_code} ({city_state}):')
        print(f'    Before: {old}')
        print(f'    After:  {new}')

    # Write updated file
    response = input(f'\nWrite {len(fixed)} fixes to zip_market_lookup.py? (yes/no): ')
    if response.lower() != 'yes':
        print('Aborted')
        return

    # Read current file
    with open('zip_market_lookup.py', 'r') as f:
        content = f.read()

    # Apply fixes
    for zip_code, (old, new, city_state) in fixed.items():
        # Find the entry in the file
        # Handle both single and multi-line formats
        old_pattern = re.escape(f'"{zip_code}": {json.dumps(old)}')
        new_value = f'"{zip_code}": {json.dumps(new)}'

        if old_pattern in content:
            content = content.replace(old_pattern, new_value)
        else:
            # Try pretty-printed format
            old_pretty = f'"{zip_code}": [\n'
            if old_pretty in content:
                # Find the full entry
                start = content.find(old_pretty)
                if start != -1:
                    # Find end of list
                    end = content.find('],', start) + 1
                    if end > 0:
                        old_entry = content[start:end]
                        # Replace with clean single-line format
                        new_entry = f'"{zip_code}": {json.dumps(new)}'
                        content = content[:start] + new_entry + content[end:]

    # Write back
    with open('zip_market_lookup.py', 'w') as f:
        f.write(content)

    print(f'\n✅ Updated zip_market_lookup.py')
    print(f'   Fixed {len(fixed)} contaminated ZIPs')

    # Verify
    print(f'\n🔍 Verifying fixes...')
    from importlib import reload
    import zip_market_lookup
    reload(zip_market_lookup)

    # Check a few fixed ZIPs
    sample_fixed = list(fixed.keys())[:5]
    for zip_code in sample_fixed:
        new_markets = zip_market_lookup.ZIP_TO_MARKETS.get(zip_code, [])
        has_zip = any(m.isdigit() and len(m) == 5 for m in new_markets)
        if has_zip:
            print(f'  ❌ ZIP {zip_code} still contaminated: {new_markets}')
        else:
            print(f'  ✅ ZIP {zip_code} clean: {new_markets}')

    print(f'\n✅ ZIP contamination cleanup complete!')
    print(f'\nNext steps:')
    print(f'  1. Review empty ZIPs (if any) and manually assign markets')
    print(f'  2. Fix existing Supabase jobs that have ZIP code markets')
    print(f'  3. Commit changes to zip_market_lookup.py')

if __name__ == '__main__':
    main()
