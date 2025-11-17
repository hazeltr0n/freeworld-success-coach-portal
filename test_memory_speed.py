"""
Test Supabase memory lookup speed

This will show us if check_job_memory() is slow
"""

import time
from job_memory_db import JobMemoryDB

# Create memory DB instance
memory_db = JobMemoryDB()

# Test with 100 job IDs
job_ids = [f"test_job_{i}" for i in range(100)]

print("="*80)
print("SUPABASE MEMORY LOOKUP SPEED TEST")
print("="*80)
print(f"Testing lookup of {len(job_ids)} job IDs\n")

# Test 1: Single lookup
start = time.time()
result = memory_db.check_job_memory(job_ids, hours=720)
elapsed = time.time() - start

print(f"✅ Memory lookup completed:")
print(f"   Total time: {elapsed:.2f}s")
print(f"   Per job: {elapsed/len(job_ids):.4f}s")
print(f"   Found: {len(result) if result else 0} jobs")

# Test 2: Multiple small lookups (simulating batch processing)
print(f"\n🔁 Testing 10 lookups of 10 jobs each:")
batch_size = 10
num_batches = 10

start = time.time()
for i in range(num_batches):
    batch_ids = job_ids[i*batch_size:(i+1)*batch_size]
    result = memory_db.check_job_memory(batch_ids, hours=720)
total_elapsed = time.time() - start

print(f"✅ Batch lookups completed:")
print(f"   Total time: {total_elapsed:.2f}s")
print(f"   Per batch: {total_elapsed/num_batches:.2f}s")
print(f"   Per job: {total_elapsed/(batch_size*num_batches):.4f}s")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)
if elapsed < 1.0:
    print(f"✅ Memory lookups are FAST ({elapsed:.2f}s for 100 jobs)")
    print(f"   This is NOT the bottleneck")
else:
    print(f"⚠️ Memory lookups are SLOW ({elapsed:.2f}s for 100 jobs)")
    print(f"   This IS the bottleneck")
