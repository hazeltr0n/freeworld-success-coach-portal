-- CRITICAL FIX: Add missing id column to jobs table
-- This must be run in Supabase SQL Editor to fix "column id does not exist" error

-- Step 1: Add the missing id SERIAL PRIMARY KEY column to the jobs table
-- This will auto-populate existing rows with sequential IDs
ALTER TABLE jobs ADD COLUMN id SERIAL PRIMARY KEY;

-- Step 2: Verify the fix worked
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'jobs' 
AND column_name IN ('id', 'job_id')
ORDER BY ordinal_position;

-- Step 3: Test insert (optional verification)
-- INSERT INTO jobs (job_id, job_title, company, location, apply_url, match_level, market) 
-- VALUES ('TEST_ID_FIX_12345', 'Test Job', 'Test Company', 'Test Location', 'https://test.com', 'good', 'Test Market');

-- Step 4: Clean up test (optional)
-- DELETE FROM jobs WHERE job_id = 'TEST_ID_FIX_12345';

-- Expected result: jobs table should now have both:
-- - id: SERIAL PRIMARY KEY (auto-increment integer)
-- - job_id: TEXT (existing business key)