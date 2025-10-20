-- Remove UNIQUE constraint on rules_duplicate_r3 to enable dual-layer deduplication
--
-- PROBLEM: Migration 20251019194645 created a UNIQUE index on rules_duplicate_r3,
-- which conflicts with the dual-layer DELETE strategy in batch_insert_jobs_with_dedup.
-- The DELETE approach requires temporary duplicates to exist before cleanup.
--
-- SOLUTION: Drop the UNIQUE index and use a regular (non-unique) index instead.
-- The RPC function will handle deduplication via DELETE after INSERT.

-- Step 1: Remove the conflicting UNIQUE constraint
DROP INDEX IF EXISTS idx_jobs_r3_unique;

-- Step 2: Ensure regular (non-unique) index exists for DELETE performance
-- This index improves performance of the DELETE query in batch_insert_jobs_with_dedup
CREATE INDEX IF NOT EXISTS idx_jobs_r3_dedup ON jobs(rules_duplicate_r3)
WHERE rules_duplicate_r3 IS NOT NULL AND rules_duplicate_r3 != '';

-- Step 3: Add documentation
COMMENT ON INDEX idx_jobs_r3_dedup IS 'Non-unique R3 index for DELETE-based dedup (dual-layer strategy)';

-- Log the change for migration history
DO $$
BEGIN
    RAISE NOTICE '✅ Removed UNIQUE constraint on rules_duplicate_r3';
    RAISE NOTICE '✅ Created non-unique index for DELETE-based deduplication';
    RAISE NOTICE '📊 Dual-layer dedup strategy: Layer 1=job_id conflicts, Layer 2=R3 DELETE cleanup';
END $$;
