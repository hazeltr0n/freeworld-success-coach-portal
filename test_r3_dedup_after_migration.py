"""
Test R3 Deduplication After Migration 20251020000003

This script verifies that the dual-layer deduplication strategy works correctly
after removing the UNIQUE constraint on rules_duplicate_r3.

Expected behavior:
1. Insert job with R3 hash "abc123" → Success
2. Insert another job with R3 hash "abc123" → Success (temporarily allows duplicate)
3. RPC DELETE cleanup runs → Keeps newest, deletes oldest
4. Final result: Only 1 job with R3 hash "abc123" exists
"""

import hashlib
from datetime import datetime
from supabase_utils import get_client

def test_r3_deduplication():
    """Test that R3 deduplication works with DELETE strategy"""

    client = get_client()
    if not client:
        print("❌ Supabase client not available")
        return False

    print("=" * 80)
    print("R3 DEDUPLICATION TEST - POST MIGRATION")
    print("=" * 80)

    # Generate unique test R3 hash
    test_timestamp = datetime.now().isoformat()
    test_r3 = hashlib.md5(f"test_dedup_{test_timestamp}".encode()).hexdigest()[:16]

    print(f"\n📋 Test R3 hash: {test_r3}")
    print("-" * 80)

    # Create 3 test jobs with the SAME R3 hash but different job_ids
    test_jobs = []
    for i in range(1, 4):
        job = {
            'job_id': f'test_job_{i}_{test_timestamp}',
            'job_title': f'CDL Driver Test {i}',
            'company': 'Test Transport Co',
            'location': 'Houston, TX',
            'match_level': 'good',
            'route_type': 'Local',
            'rules_duplicate_r1': f'r1_hash_{i}',  # Different R1
            'rules_duplicate_r2': f'r2_hash_{i}',  # Different R2
            'rules_duplicate_r3': test_r3,  # SAME R3 (should deduplicate!)
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }
        test_jobs.append(job)
        print(f"   Job {i}: job_id={job['job_id'][:30]}..., R3={test_r3}")

    # Test 1: Insert all jobs via RPC
    print("\n📤 TEST 1: Inserting 3 jobs with SAME R3 hash via RPC...")
    print("-" * 80)

    try:
        result = client.rpc('batch_insert_jobs_with_dedup', {'p_jobs_data': test_jobs}).execute()

        if result.data is not None:
            inserted_count = result.data if isinstance(result.data, int) else len(test_jobs)
            print(f"   ✅ RPC returned: {inserted_count} records processed")

            # Test 2: Query database to see how many actually exist
            print("\n🔍 TEST 2: Checking database for R3 duplicates...")
            print("-" * 80)

            db_result = client.table('jobs').select('job_id, job_title, created_at').eq('rules_duplicate_r3', test_r3).execute()
            actual_count = len(db_result.data) if db_result.data else 0

            print(f"   📊 Jobs in database with R3={test_r3}: {actual_count}")

            if actual_count == 1:
                print(f"   ✅ SUCCESS! R3 deduplication WORKED correctly")
                print(f"   ✅ Kept 1 job, deleted {len(test_jobs) - 1} duplicates")

                # Show which job was kept
                kept_job = db_result.data[0]
                print(f"\n   📌 Job kept in database:")
                print(f"      job_id: {kept_job['job_id']}")
                print(f"      title: {kept_job['job_title']}")

                success = True

            elif actual_count == len(test_jobs):
                print(f"   ❌ FAILURE! All {actual_count} jobs were inserted (NO deduplication)")
                print(f"   ⚠️  This means the UNIQUE constraint was removed BUT DELETE logic isn't working")
                print(f"   ⚠️  Check that migration 20251020000002 (dual-layer) is the active RPC function")

                success = False

            else:
                print(f"   ⚠️  UNEXPECTED! {actual_count} jobs in database (expected 1 or {len(test_jobs)})")
                success = False

            # Test 3: Cleanup
            print("\n🧹 TEST 3: Cleaning up test data...")
            print("-" * 80)

            cleanup_result = client.table('jobs').delete().eq('rules_duplicate_r3', test_r3).execute()
            deleted_count = len(cleanup_result.data) if cleanup_result.data else 0
            print(f"   ✅ Deleted {deleted_count} test job(s)")

        else:
            print("   ❌ RPC returned no data")
            success = False

    except Exception as e:
        error_str = str(e)

        if 'duplicate key value violates unique constraint' in error_str.lower():
            print(f"   ❌ UNIQUE CONSTRAINT STILL EXISTS!")
            print(f"   ⚠️  Migration 20251020000003 has NOT been applied yet")
            print(f"   📋 Error: {error_str[:200]}")
            success = False
        else:
            print(f"   ❌ Unexpected error: {error_str[:300]}")
            success = False

    print("\n" + "=" * 80)
    if success:
        print("✅ ALL TESTS PASSED - R3 DEDUPLICATION IS WORKING!")
    else:
        print("❌ TESTS FAILED - SEE ERRORS ABOVE")
    print("=" * 80)

    return success

if __name__ == "__main__":
    test_r3_deduplication()
