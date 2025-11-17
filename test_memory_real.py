"""
Test memory lookup with REAL job IDs from Supabase
This simulates exactly what the pipeline does
"""

import time
from job_memory_db import JobMemoryDB
from supabase_utils import get_client

# Get real job IDs from Supabase
print("📂 Fetching real job IDs from Supabase...")
supabase = get_client()
result = supabase.table('jobs').select('job_id').limit(100).execute()
real_job_ids = [job['job_id'] for job in result.data]
print(f"   Got {len(real_job_ids)} real job IDs\n")

# Test memory lookup
memory_db = JobMemoryDB()

print("="*80)
print("MEMORY LOOKUP TEST WITH REAL JOB IDS")
print("="*80)

# Test: Lookup real job IDs (cache hits expected)
start = time.time()
memory_result = memory_db.check_job_memory(real_job_ids, hours=720)
elapsed = time.time() - start

print(f"\n✅ Memory lookup completed:")
print(f"   Total time: {elapsed:.2f}s")
print(f"   Per job: {elapsed/len(real_job_ids):.4f}s")
print(f"   Found: {len(memory_result) if memory_result else 0} jobs")
print(f"   Hit rate: {len(memory_result)/len(real_job_ids)*100:.1f}%")

# Now test with a mix of real and fake IDs (simulating fresh + duplicate jobs)
mixed_ids = real_job_ids[:50] + [f"fake_job_{i}" for i in range(50)]
print(f"\n🔀 Testing mixed scenario (50 real + 50 fake IDs):")

start = time.time()
mixed_result = memory_db.check_job_memory(mixed_ids, hours=720)
elapsed = time.time() - start

print(f"✅ Mixed lookup completed:")
print(f"   Total time: {elapsed:.2f}s")
print(f"   Per job: {elapsed/len(mixed_ids):.4f}s")
print(f"   Found: {len(mixed_result) if mixed_result else 0} jobs")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)
print(f"If lookup is fast (<1s), memory is NOT the bottleneck")
print(f"If lookup is slow (>2s), memory IS a bottleneck")
