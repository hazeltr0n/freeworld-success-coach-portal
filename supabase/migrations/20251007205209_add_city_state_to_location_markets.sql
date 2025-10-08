-- Add city_state column to location_markets table
-- This will store "City, ST" format for ZIP code rows

ALTER TABLE location_markets
ADD COLUMN IF NOT EXISTS city_state TEXT;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_location_markets_city_state ON location_markets(city_state);

-- Add comment
COMMENT ON COLUMN location_markets.city_state IS 'City and state in "City, ST" format for ZIP code locations';
