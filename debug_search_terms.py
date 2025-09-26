#!/usr/bin/env python3
"""
Debug search terms processing
"""

def test_search_term_processing():
    """Test how search terms are processed in different scenarios"""

    print("🔍 DEBUGGING SEARCH TERM PROCESSING")
    print("=" * 50)

    # Test cases
    test_cases = [
        "CDL Driver No Experience",
        "CDL driver, class a driver, class b driver",
        "CDL Driver No Experience Class A Driver Class B Driver",
        "truck driver, delivery driver, warehouse worker"
    ]

    for i, search_terms in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Input: '{search_terms}'")

        # Split on commas like pipeline_v3 does
        search_terms_list = [term.strip() for term in search_terms.split(',') if term.strip()]

        print(f"After comma split: {search_terms_list}")
        print(f"Number of queries: {len(search_terms_list)}")

        # Show what URLs would be generated
        location = "Houston, TX"
        encoded_location = location.replace(' ', '+').replace(',', '%2C')
        indeed_urls = []

        for term in search_terms_list:
            encoded_term = term.replace(' ', '+')
            indeed_url = f"https://www.indeed.com/jobs?q={encoded_term}&l={encoded_location}&radius=25"
            indeed_urls.append(indeed_url)

        print(f"Generated URLs:")
        for j, url in enumerate(indeed_urls, 1):
            print(f"  {j}. {url}")

        # Show expected behavior
        limit = 100
        if len(search_terms_list) > 1:
            print(f"Expected: {len(search_terms_list)} queries × {limit} jobs = {limit * len(search_terms_list)} total")
        else:
            print(f"Expected: {limit} jobs from single query")

if __name__ == "__main__":
    test_search_term_processing()