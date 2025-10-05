-- Create location_markets library table for city/ZIP to market mappings
-- Supports multiple markets per location (e.g., Stockton to [Stockton, Bay Area])

CREATE TABLE IF NOT EXISTS location_markets (
    id SERIAL PRIMARY KEY,
    location_string TEXT NOT NULL,  -- "city, st" or ZIP code
    location_type TEXT NOT NULL CHECK (location_type IN ('city', 'zip', 'coordinate')),
    markets TEXT[] NOT NULL,  -- Array of market names
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(location_string, location_type)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_location_markets_location_string ON location_markets(location_string);
CREATE INDEX IF NOT EXISTS idx_location_markets_location_type ON location_markets(location_type);

-- Spatial index for coordinate-based searches (if we need it later)
CREATE INDEX IF NOT EXISTS idx_location_markets_coordinates ON location_markets(latitude, longitude);

-- Comments
COMMENT ON TABLE location_markets IS 'Library of location to market mappings supporting multiple markets per location';
COMMENT ON COLUMN location_markets.location_string IS 'Location identifier: "city, st" or ZIP code';
COMMENT ON COLUMN location_markets.location_type IS 'Type of location: city, zip, or coordinate';
COMMENT ON COLUMN location_markets.markets IS 'Array of market names this location belongs to';

-- Seed data from existing MarketMapper (1,376 city mappings)
-- We'll populate this via Python script after migration

-- Function to lookup markets by location
CREATE OR REPLACE FUNCTION get_markets_for_location(loc TEXT, loc_type TEXT DEFAULT 'city')
RETURNS TEXT[] AS $$
DECLARE
    market_array TEXT[];
BEGIN
    SELECT markets INTO market_array
    FROM location_markets
    WHERE location_string = LOWER(loc) AND location_type = loc_type;

    RETURN COALESCE(market_array, ARRAY[]::TEXT[]);
END;
$$ LANGUAGE plpgsql;
