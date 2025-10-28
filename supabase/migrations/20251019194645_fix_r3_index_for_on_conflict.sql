-- Fix R3 unique index to work with ON CONFLICT
-- PostgreSQL's ON CONFLICT doesn't work with partial indexes (indexes with WHERE clause)
-- We need a full unique index for ON CONFLICT to recognize it

-- Drop the partial index
DROP INDEX IF EXISTS idx_jobs_r3_unique;

-- Create a full unique index without WHERE clause
-- This allows ON CONFLICT (rules_duplicate_r3) to work
CREATE UNIQUE INDEX idx_jobs_r3_unique ON jobs(rules_duplicate_r3);

COMMENT ON INDEX idx_jobs_r3_unique IS 'Full unique index for R3 dedup hash - required for ON CONFLICT';
