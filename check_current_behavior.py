#!/usr/bin/env python3
"""
Check current search term behavior
"""

# Test how search terms are currently being processed
search_terms = "CDL driver, class a driver, class b driver"
search_terms_list = [term.strip() for term in search_terms.split(',') if term.strip()]

print(f"🔍 Input: '{search_terms}'")
print(f"📋 Split into: {search_terms_list}")
print(f"🔢 Number of queries: {len(search_terms_list)}")

# Test URL generation
location = "Houston, TX"
radius = 25
encoded_location = location.replace(' ', '+').replace(',', '%2C')
indeed_urls = []

for term in search_terms_list:
    encoded_term = term.replace(' ', '+')
    indeed_url = f"https://www.indeed.com/jobs?q={encoded_term}&l={encoded_location}&radius={radius}"
    indeed_urls.append(indeed_url)

print(f"\n🔗 Generated URLs:")
for i, url in enumerate(indeed_urls, 1):
    print(f"   {i}. {url}")

# Test limit calculation
job_limit = 1000
num_queries = len(search_terms_list)
effective_limit = job_limit * num_queries

print(f"\n📊 Limit calculation:")
print(f"   Job limit per query: {job_limit}")
print(f"   Number of queries: {num_queries}")
print(f"   Total API limit: {effective_limit}")
print(f"   Expected total jobs: {effective_limit}")