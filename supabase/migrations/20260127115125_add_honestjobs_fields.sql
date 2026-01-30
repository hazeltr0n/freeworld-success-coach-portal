-- Add HonestJobs-specific fields to jobs table
-- These fields capture fair chance hiring data from HonestJobs.com

-- HonestJobs original job UUID
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS honestjobs_id TEXT;

-- Number of verified fair chance hires by this employer
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS verified_hires INTEGER DEFAULT 0;

-- Whether employer is explicitly marked as fair chance
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_fair_chance BOOLEAN DEFAULT FALSE;

-- Employer UUID for cross-referencing and deduplication
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS employer_id TEXT;

-- Create index on employer_id for efficient lookups
CREATE INDEX IF NOT EXISTS idx_jobs_employer_id ON jobs(employer_id) WHERE employer_id IS NOT NULL;

-- Create index on verified_hires for sorting by employer reputation
CREATE INDEX IF NOT EXISTS idx_jobs_verified_hires ON jobs(verified_hires DESC) WHERE verified_hires > 0;

-- Create index on is_fair_chance for filtering
CREATE INDEX IF NOT EXISTS idx_jobs_is_fair_chance ON jobs(is_fair_chance) WHERE is_fair_chance = TRUE;

-- Add comment explaining the fields
COMMENT ON COLUMN jobs.honestjobs_id IS 'Original HonestJobs job UUID';
COMMENT ON COLUMN jobs.verified_hires IS 'Number of verified fair chance hires by this employer on HonestJobs';
COMMENT ON COLUMN jobs.is_fair_chance IS 'Employer explicitly marked as fair chance on HonestJobs';
COMMENT ON COLUMN jobs.employer_id IS 'Employer UUID from HonestJobs for cross-referencing';
