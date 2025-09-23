-- Delete all jobs created today from Supabase
-- Run this in the Supabase SQL Editor

-- First, check how many jobs would be deleted (SAFE - READ ONLY)
SELECT 
    DATE(created_at) as creation_date,
    COUNT(*) as job_count,
    MIN(created_at) as earliest,
    MAX(created_at) as latest
FROM jobs 
WHERE DATE(created_at) = CURRENT_DATE
GROUP BY DATE(created_at);

-- Show sample of jobs that would be deleted
SELECT 
    id,
    job_title,
    company,
    market,
    match_level,
    created_at
FROM jobs 
WHERE DATE(created_at) = CURRENT_DATE
ORDER BY created_at DESC
LIMIT 10;

-- UNCOMMENT THE LINES BELOW TO ACTUALLY DELETE (DESTRUCTIVE)
-- WARNING: This will permanently delete all jobs created today!

/*
-- Delete all jobs created today
DELETE FROM jobs 
WHERE DATE(created_at) = CURRENT_DATE;

-- Check final count
SELECT COUNT(*) as remaining_jobs FROM jobs;
*/

-- Alternative: Delete jobs created in the last 24 hours
/*
DELETE FROM jobs 
WHERE created_at >= NOW() - INTERVAL '24 hours';
*/