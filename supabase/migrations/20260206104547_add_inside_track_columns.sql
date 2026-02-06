-- Add columns for Inside Track (partner) jobs
-- These jobs are manually added by coaches and appear at the top of Free Agent feeds

-- Partner contact name (e.g., "John Smith at ABC Trucking")
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS partner_name TEXT;

-- Internal notes for coaches (not shown to Free Agents)
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS partner_notes TEXT;

-- Coach who created/manages this job
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS success_coach TEXT;

-- Expiration date for inside track jobs
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;

-- Create index for querying inside track jobs by coach
CREATE INDEX IF NOT EXISTS idx_jobs_inside_track_coach
ON jobs(success_coach)
WHERE source = 'inside_track';

-- Create index for querying visible inside track jobs by market
CREATE INDEX IF NOT EXISTS idx_jobs_inside_track_market
ON jobs(market, source)
WHERE source = 'inside_track' AND filter_reason = 'included: inside_track';
