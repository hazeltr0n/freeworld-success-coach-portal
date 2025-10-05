-- Add employer_uuid field to companies table for matching with internal employer database
ALTER TABLE companies ADD COLUMN IF NOT EXISTS employer_uuid UUID;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_companies_employer_uuid ON companies(employer_uuid);

-- Add comment
COMMENT ON COLUMN companies.employer_uuid IS 'UUID linking to internal employer database';
