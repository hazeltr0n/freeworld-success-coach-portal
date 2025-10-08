-- Add cbsa column to location_markets table
ALTER TABLE location_markets
ADD COLUMN IF NOT EXISTS cbsa TEXT;

-- Create index for faster CBSA lookups
CREATE INDEX IF NOT EXISTS idx_location_markets_cbsa
ON location_markets(cbsa);

-- Add comment
COMMENT ON COLUMN location_markets.cbsa IS 'Core-Based Statistical Area (CBSA) - metropolitan area designation';
