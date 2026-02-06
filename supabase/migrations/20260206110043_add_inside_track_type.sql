-- Add inside_track_type to distinguish between partner opps and direct listings
-- partner_opportunity: Company hidden, apply goes to interest form
-- inside_track: Shows real company, links directly to job posting

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS inside_track_type TEXT DEFAULT 'inside_track';

-- Add comment for documentation
COMMENT ON COLUMN jobs.inside_track_type IS 'Type of inside track job: partner_opportunity (anonymous, interest form) or inside_track (direct link)';
