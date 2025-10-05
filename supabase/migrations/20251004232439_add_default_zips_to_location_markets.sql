-- Add default_zips array to location_markets for fallback when jobs have no ZIP
-- Will be populated from most common ZIPs per city from existing job data

ALTER TABLE location_markets ADD COLUMN IF NOT EXISTS default_zips TEXT[];

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_location_markets_default_zips ON location_markets USING GIN (default_zips);

-- Comments
COMMENT ON COLUMN location_markets.default_zips IS 'Array of default ZIP codes for this location (fallback when job has no ZIP)';
