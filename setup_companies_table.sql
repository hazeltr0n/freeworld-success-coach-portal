-- Companies Rollup Table Setup
-- Run this SQL in your Supabase dashboard to create the companies table

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL,
    normalized_company_name TEXT NOT NULL,
    total_jobs INTEGER DEFAULT 0,
    active_jobs INTEGER DEFAULT 0,
    fair_chance_jobs INTEGER DEFAULT 0,
    has_fair_chance BOOLEAN DEFAULT FALSE,
    markets TEXT[] DEFAULT ARRAY[]::TEXT[],
    job_titles TEXT[] DEFAULT ARRAY[]::TEXT[],
    route_types TEXT[] DEFAULT ARRAY[]::TEXT[],
    quality_breakdown JSONB DEFAULT '{}'::JSONB,
    oldest_job_date TIMESTAMPTZ,
    newest_job_date TIMESTAMPTZ,
    avg_salary_min NUMERIC,
    avg_salary_max NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(normalized_company_name);
CREATE INDEX IF NOT EXISTS idx_companies_fair_chance ON companies(has_fair_chance);
CREATE INDEX IF NOT EXISTS idx_companies_active_jobs ON companies(active_jobs);
CREATE INDEX IF NOT EXISTS idx_companies_updated ON companies(updated_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_companies_updated_at ON companies;
CREATE TRIGGER update_companies_updated_at 
    BEFORE UPDATE ON companies 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add RLS policies if needed
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read companies data
CREATE POLICY "Allow authenticated users to read companies" ON companies
    FOR SELECT USING (auth.role() = 'authenticated');

-- Allow service role to manage companies data  
CREATE POLICY "Allow service role to manage companies" ON companies
    FOR ALL USING (auth.role() = 'service_role');