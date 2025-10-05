-- Add parent_company_id field to companies table for company hierarchy
-- This allows child companies to roll up to a parent company automatically

ALTER TABLE companies ADD COLUMN IF NOT EXISTS parent_company_id INTEGER;

-- Add foreign key constraint (parent must be a valid company)
ALTER TABLE companies
ADD CONSTRAINT fk_parent_company
FOREIGN KEY (parent_company_id)
REFERENCES companies(id)
ON DELETE SET NULL;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_companies_parent_company_id ON companies(parent_company_id);

-- Add canonical_company_name field (denormalized for performance)
-- This is the name of the parent company (or self if no parent)
ALTER TABLE companies ADD COLUMN IF NOT EXISTS canonical_company_name TEXT;

-- Add comments
COMMENT ON COLUMN companies.parent_company_id IS 'ID of parent company if this is a child/variant company name';
COMMENT ON COLUMN companies.canonical_company_name IS 'Canonical company name (parent company name or self if no parent)';

-- Create a function to get canonical company name
CREATE OR REPLACE FUNCTION get_canonical_company_name(company_id INTEGER)
RETURNS TEXT AS $$
DECLARE
    parent_id INTEGER;
    parent_name TEXT;
BEGIN
    -- Get parent_company_id
    SELECT parent_company_id INTO parent_id FROM companies WHERE id = company_id;

    -- If has parent, return parent's name
    IF parent_id IS NOT NULL THEN
        SELECT company_name INTO parent_name FROM companies WHERE id = parent_id;
        RETURN parent_name;
    ELSE
        -- Otherwise return own name
        SELECT company_name INTO parent_name FROM companies WHERE id = company_id;
        RETURN parent_name;
    END IF;
END;
$$ LANGUAGE plpgsql;
