-- Remove all city rows from location_markets table
-- Now that ZIPs have city_state column populated, city rows are redundant

-- Delete all rows where location_type = 'city'
DELETE FROM location_markets
WHERE location_type = 'city';

-- Add comment documenting the change
COMMENT ON TABLE location_markets IS 'ZIP-centric location table. Each ZIP has city_state and markets columns. City rows removed as of 2025-10-07.';
