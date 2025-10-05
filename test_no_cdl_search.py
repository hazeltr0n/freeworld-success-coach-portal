#!/usr/bin/env python3
"""
Test to see what jobs come back for 'No CDL' vs 'CDL School' searches
"""

from driver_pulse_source import DriverPulseSource, DriverPulseConfig

def test_no_cdl_search():
    print("🔍 Testing 'No CDL' Search Results")
    print("=" * 60)

    # Test 1: No CDL search
    config1 = DriverPulseConfig(
        search_text="CDL training no experience new driver recent grad student",
        location="Dallas, TX",
        max_companies=10,
        max_jobs_per_company=3
    )

    source1 = DriverPulseSource(config1)
    source1.load_authentication()

    print("\nTEST 1: No CDL Search")
    print(f"Search: '{config1.search_text}'")
    print("-" * 60)

    jobs1 = source1.scrape_jobs(limit=10)
    print(f"\nFound {len(jobs1)} jobs\n")

    for i, job in enumerate(jobs1[:5], 1):
        print(f"{i}. {job['source_title']}")
        print(f"   Company: {job['source_company']}")
        desc = job['source_description'][:200].replace('\n', ' ')
        print(f"   Description: {desc}...")
        print()

    # Test 2: CDL School search
    print("\n" + "=" * 60)
    config2 = DriverPulseConfig(
        search_text="CDL school graduate recent grad new driver training",
        location="Dallas, TX",
        max_companies=10,
        max_jobs_per_company=3
    )

    source2 = DriverPulseSource(config2)
    source2.load_authentication()

    print("\nTEST 2: CDL School Grad Search")
    print(f"Search: '{config2.search_text}'")
    print("-" * 60)

    jobs2 = source2.scrape_jobs(limit=10)
    print(f"\nFound {len(jobs2)} jobs\n")

    for i, job in enumerate(jobs2[:5], 1):
        print(f"{i}. {job['source_title']}")
        print(f"   Company: {job['source_company']}")
        desc = job['source_description'][:200].replace('\n', ' ')
        print(f"   Description: {desc}...")
        print()

    # Compare overlap
    companies1 = {j['source_company'] for j in jobs1}
    companies2 = {j['source_company'] for j in jobs2}

    overlap = companies1 & companies2
    print("\n" + "=" * 60)
    print(f"OVERLAP ANALYSIS:")
    print(f"  No CDL companies: {len(companies1)}")
    print(f"  CDL School companies: {len(companies2)}")
    print(f"  Overlapping companies: {len(overlap)}")
    print(f"  Overlap %: {len(overlap) / len(companies1) * 100:.1f}%")

if __name__ == "__main__":
    test_no_cdl_search()
