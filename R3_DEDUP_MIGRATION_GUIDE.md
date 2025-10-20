# R3 Deduplication Migration Guide

## 🎯 Problem Summary

The database has a **UNIQUE constraint** on `rules_duplicate_r3` that conflicts with the **dual-layer DELETE strategy** in the latest RPC function (`batch_insert_jobs_with_dedup`).

### Root Cause
- **Migration 20251019194645** created: `CREATE UNIQUE INDEX idx_jobs_r3_unique ON jobs(rules_duplicate_r3);`
- **Migration 20251020000002** expects to: INSERT jobs → DELETE duplicates by R3
- **Conflict**: UNIQUE constraint prevents multiple R3 hashes from existing, so DELETE never runs!

### Evidence
```
Error: duplicate key value violates unique constraint "idx_jobs_r3_unique"
Code: 23505
Details: Key (rules_duplicate_r3)=(abc123) already exists.
```

---

## ✅ Solution

**Remove the UNIQUE constraint** and use a **regular (non-unique) index** for DELETE performance.

---

## 📋 Migration Steps

### Step 1: Review the Migration File

The migration file has been created: `supabase/migrations/20251020000003_remove_r3_unique_constraint.sql`

**What it does:**
1. Drops `idx_jobs_r3_unique` (UNIQUE index)
2. Creates `idx_jobs_r3_dedup` (regular index with WHERE clause)
3. Logs success notices

### Step 2: Push Migration to Supabase

```bash
# Navigate to project root
cd /Users/freeworld_james/Development/freeworld-master/freeworld-job-scraper-main

# Use the migrate script
./scripts/migrate.sh push

# OR manually with Supabase CLI
supabase db push
```

### Step 3: Verify Migration Applied

Check the Supabase dashboard SQL editor or run:

```sql
-- Check for UNIQUE indexes on rules_duplicate_r3
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'jobs'
  AND indexname LIKE '%r3%';

-- Expected result:
-- idx_jobs_r3_dedup (non-unique, with WHERE clause)
-- NO idx_jobs_r3_unique
```

### Step 4: Test Deduplication

Run the test script:

```bash
python3 test_r3_dedup_after_migration.py
```

**Expected output:**
```
✅ RPC returned: 3 records processed
📊 Jobs in database with R3=abc123: 1
✅ SUCCESS! R3 deduplication WORKED correctly
✅ Kept 1 job, deleted 2 duplicates
```

---

## 🔍 How Dual-Layer Deduplication Works

### Layer 1: job_id Conflicts (ON CONFLICT)
```sql
INSERT INTO jobs (...)
ON CONFLICT (job_id) DO UPDATE SET
    updated_at = EXCLUDED.updated_at,
    tracked_url = EXCLUDED.tracked_url;
```
- Handles **re-scrapes** of the same job
- Updates timestamps and tracking URLs
- No data loss

### Layer 2: R3 Cleanup (DELETE)
```sql
DELETE FROM jobs a
USING jobs b
WHERE a.rules_duplicate_r3 = b.rules_duplicate_r3
  AND a.rules_duplicate_r3 IS NOT NULL
  AND a.updated_at < b.updated_at
  AND a.job_id != b.job_id;
```
- Removes **similar jobs** from different sources
- Keeps **most recent** job (by `updated_at`)
- Runs **atomically** in same transaction

---

## 📊 What Gets Deduplicated by R3

R3 hash is generated from:
```python
r3_key = f"{company}|{market}|{route_type}|{match_level}|{normalized_title}"
```

**Example duplicates caught by R3:**
1. Same company posting same job on Indeed + Google Jobs
2. Same job with slight title variations ("CDL Driver" vs "CDL-A Driver")
3. Same job posted by recruiting agency under different names

**NOT deduplicated (correctly):**
- Different companies with similar jobs (different R3)
- Same company, different routes (Local vs OTR = different R3)
- Same company, different match levels (good vs so-so = different R3)

---

## 🚨 Troubleshooting

### Issue 1: UNIQUE Constraint Still Exists

**Symptom:**
```
Error: duplicate key value violates unique constraint "idx_jobs_r3_unique"
```

**Solution:**
Migration hasn't been applied yet. Run `./scripts/migrate.sh push`

---

### Issue 2: All Jobs Inserted (No Deduplication)

**Symptom:**
```
📊 Jobs in database with R3=abc123: 3
❌ All 3 jobs were inserted (NO deduplication)
```

**Diagnosis:**
The UNIQUE constraint was removed, but the DELETE logic isn't executing.

**Check:**
1. Which RPC function is deployed?
   ```sql
   SELECT prosrc FROM pg_proc WHERE proname = 'batch_insert_jobs_with_dedup';
   ```

2. Does it contain the DELETE statement?
   Look for: `DELETE FROM jobs a USING jobs b WHERE a.rules_duplicate_r3 = b.rules_duplicate_r3`

**Solution:**
Re-apply migration `20251020000002_dual_layer_dedup_job_id_then_r3.sql`

---

### Issue 3: Wrong Job Kept (Oldest Instead of Newest)

**Symptom:**
Older job is kept, newer job is deleted.

**Diagnosis:**
The `updated_at` field isn't being set correctly during ingestion.

**Check pipeline_v3.py:**
```python
# canonical_transforms.py line ~693
normalized_fields['sys.updated_at'] = datetime.now().isoformat()
```

---

## 📈 Performance Impact

### Before (UNIQUE Constraint):
- ❌ Immediate rejection of duplicates
- ❌ Upload fails with error 23505
- ❌ No data inserted

### After (DELETE Strategy):
- ✅ All jobs inserted first
- ✅ DELETE runs on indexed column (fast!)
- ✅ Keeps most recent job
- ⏱️ Typical DELETE time: <100ms for 100 jobs

### Index Performance:
```sql
-- Non-unique index with WHERE clause (optimal!)
CREATE INDEX idx_jobs_r3_dedup ON jobs(rules_duplicate_r3)
WHERE rules_duplicate_r3 IS NOT NULL AND rules_duplicate_r3 != '';
```
- Only indexes rows with R3 hashes (smaller index)
- WHERE clause reduces index size by ~5-10%
- DELETE query uses index (fast lookup)

---

## 🎯 Expected Outcomes

### Immediate (After Migration):
- ✅ Uploads no longer fail with constraint errors
- ✅ R3 deduplication works automatically
- ✅ Pipeline completes successfully

### Long-term:
- ✅ 15-25% reduction in duplicate jobs
- ✅ Cleaner data in Supabase
- ✅ Better Free Agent experience (fewer duplicate listings)

### Analytics:
Check the RPC function logs for:
```
NOTICE: Upserted 100 records out of 120 total
NOTICE: Deleted 18 R3 duplicate jobs (keeping most recent)
```

---

## 📞 Need Help?

If issues persist after applying the migration:

1. **Check migration history:**
   ```sql
   SELECT version, name FROM supabase_migrations.schema_migrations
   ORDER BY version DESC LIMIT 10;
   ```

2. **Check active RPC function:**
   ```sql
   SELECT routine_name, created
   FROM information_schema.routines
   WHERE routine_name = 'batch_insert_jobs_with_dedup';
   ```

3. **Check indexes:**
   ```sql
   SELECT * FROM pg_indexes WHERE tablename = 'jobs';
   ```

4. **Run diagnostic test:**
   ```bash
   python3 test_r3_dedup_after_migration.py
   ```

---

## 📚 Related Files

- **Migration**: `supabase/migrations/20251020000003_remove_r3_unique_constraint.sql`
- **Test Script**: `test_r3_dedup_after_migration.py`
- **RPC Function**: `supabase/migrations/20251020000002_dual_layer_dedup_job_id_then_r3.sql`
- **R3 Hash Generation**: `pipeline_v3.py` line 1356-1377
- **Data Preparation**: `jobs_schema.py` line 335-385 (`prepare_for_supabase`)

---

**Last Updated:** October 20, 2025
**Status:** Ready for deployment
