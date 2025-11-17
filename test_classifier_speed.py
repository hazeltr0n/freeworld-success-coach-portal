"""
Test classifier speed with and without Supabase memory checks

This will help us determine if the bottleneck is:
1. Supabase memory lookups
2. OpenAI API calls themselves
"""

import time
from job_classifier import JobClassifier

# Test data
test_jobs = [
    {
        'job_id': f'speed_test_{i}',
        'job_title': 'CDL Driver - No Experience Required',
        'company': 'ABC Trucking',
        'location': 'Dallas, TX',
        'job_description': 'We are looking for CDL-A drivers. No experience required! Training provided. Pay $55k-65k annually.'
    }
    for i in range(10)
]

print("="*80)
print("CLASSIFIER SPEED TEST")
print("="*80)
print(f"Testing with {len(test_jobs)} jobs\n")

classifier = JobClassifier()

# Test: Direct OpenAI classification (no memory check)
print("🧪 Test 1: Direct OpenAI API calls (bypassing memory system)")
print("-" * 80)

start = time.time()
results = classifier.classify_jobs_in_batches(test_jobs)
elapsed = time.time() - start

print(f"\n✅ Direct classification:")
print(f"   Total time: {elapsed:.2f}s")
print(f"   Per job: {elapsed/len(test_jobs):.2f}s")
print(f"   Throughput: {len(test_jobs)/elapsed:.2f} jobs/sec")

# Show distribution
match_counts = {}
for r in results:
    match = r.get('match', 'unknown')
    match_counts[match] = match_counts.get(match, 0) + 1
print(f"   Results: {match_counts}")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)
print(f"If this is slow (~5s per job), the OpenAI API is the bottleneck.")
print(f"If this is fast (<1s per job), the Supabase memory system is the bottleneck.")
