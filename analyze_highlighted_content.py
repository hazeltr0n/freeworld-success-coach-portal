#!/usr/bin/env python3
"""
Analyze what's actually in the highlighted_content field
"""

import json
from driver_pulse_source import DriverPulseSource, DriverPulseConfig

# Create a simple config
config = DriverPulseConfig(
    search_text="CDL driver",
    location="Dallas, TX",
    max_companies=20
)

source = DriverPulseSource(config)

# Load authentication
print("🔐 Loading authentication...")
source.load_authentication()

# Run a search to get raw company data
print("🔍 Searching companies...")
search_results = source.search_companies()

if not search_results or not search_results.get('response'):
    print("❌ No results")
    exit(1)

companies = search_results['response']

print(f"\n📊 Analyzing {len(companies)} companies:")
print("=" * 80)

total_companies = 0
companies_with_highlights = 0
total_highlights = 0
sample_highlights = []

for company_id, company_data in companies.items():
    if company_id in ['default_companies_selected', 'has_results', 'result_count']:
        continue

    total_companies += 1
    highlighted = company_data.get('highlighted_content', [])

    if highlighted:
        companies_with_highlights += 1
        total_highlights += len(highlighted)

        # Collect first 5 samples
        if len(sample_highlights) < 5:
            sample_highlights.append({
                'company_id': company_id,
                'company_name': company_data.get('company_name', 'Unknown'),
                'highlights': highlighted,
                'all_keys': list(company_data.keys())
            })

print(f"\n📈 Statistics:")
print(f"   Total companies: {total_companies}")
print(f"   Companies WITH highlighted_content: {companies_with_highlights}")
print(f"   Companies WITHOUT highlighted_content: {total_companies - companies_with_highlights}")
print(f"   Total highlight entries: {total_highlights}")
if companies_with_highlights > 0:
    print(f"   Average per company (with highlights): {total_highlights/companies_with_highlights:.1f}")

print(f"\n\n📝 Sample Highlighted Content:")
print("=" * 80)

for i, sample in enumerate(sample_highlights, 1):
    print(f"\n{'='*80}")
    print(f"COMPANY {i}: {sample['company_name']} (ID: {sample['company_id']})")
    print(f"{'='*80}")
    print(f"All company data keys: {', '.join(sample['all_keys'])}")
    print(f"\nNumber of highlighted_content items: {len(sample['highlights'])}\n")

    for j, highlight in enumerate(sample['highlights'], 1):
        print(f"  --- Highlight #{j} ---")
        for key, value in highlight.items():
            if isinstance(value, str):
                if len(value) > 300:
                    print(f"    {key}: {value[:300]}...")
                else:
                    print(f"    {key}: {value}")
            else:
                print(f"    {key}: {value}")
        print()

# Also show a sample company WITHOUT highlights
print(f"\n\n📝 Sample Company WITHOUT Highlighted Content:")
print("=" * 80)

for company_id, company_data in companies.items():
    if company_id in ['default_companies_selected', 'has_results', 'result_count']:
        continue

    if not company_data.get('highlighted_content'):
        print(f"Company: {company_data.get('company_name', 'Unknown')}")
        print(f"All available keys: {', '.join(company_data.keys())}")
        print(f"\nSample data:")
        for key, value in company_data.items():
            if isinstance(value, str) and len(value) < 200:
                print(f"  {key}: {value}")
            elif isinstance(value, (int, float, bool)):
                print(f"  {key}: {value}")
        break

# Save full response for inspection
with open('highlighted_content_analysis.json', 'w') as f:
    json.dump({
        'statistics': {
            'total_companies': total_companies,
            'companies_with_highlights': companies_with_highlights,
            'total_highlights': total_highlights
        },
        'samples': sample_highlights
    }, f, indent=2)

print(f"\n\n💾 Full analysis saved to: highlighted_content_analysis.json")
