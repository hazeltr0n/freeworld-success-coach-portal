-- Add apply_instructions column for Inside Track jobs without a URL
-- Used for jobs where applicants need to call a phone number or show up in person

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS apply_instructions TEXT;

-- Add comment describing the column purpose
COMMENT ON COLUMN jobs.apply_instructions IS 'For jobs without apply URL - contains phone number to call or address to visit';
