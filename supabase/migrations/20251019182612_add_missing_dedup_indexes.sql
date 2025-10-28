-- Add missing indexes for deduplication columns
-- The batch_insert_jobs_with_dedup RPC function uses DELETE with WHERE clauses
-- that check rules_duplicate_r1 and job_id, but these columns were not indexed.
-- This causes full table scans and timeout errors (57014) with 3000+ jobs.

-- Add index for R1 deduplication hash lookups
CREATE INDEX IF NOT EXISTS idx_jobs_rules_duplicate_r1 ON jobs(rules_duplicate_r1);

-- Add index for job_id lookups (used in deduplication)
CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON jobs(job_id);

-- Add comments
COMMENT ON INDEX idx_jobs_rules_duplicate_r1 IS 'Index for R1 dedup hash (exact duplicate before AI)';
COMMENT ON INDEX idx_jobs_job_id IS 'Index for job_id lookups (deduplication)';
