-- Change deduplication to DELETE old job + INSERT new job
-- This ensures jobs get fresh timestamps AND updated content (salary, description, etc.)
-- Better practice: always have the latest version of the job

CREATE OR REPLACE FUNCTION batch_insert_jobs_with_dedup(p_jobs_data JSONB)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    inserted_count INTEGER := 0;
    deleted_count INTEGER := 0;
    total_count INTEGER := 0;
BEGIN
    -- Count total records in input
    SELECT jsonb_array_length(p_jobs_data) INTO total_count;

    -- Log the operation
    RAISE NOTICE 'Processing % job records for R3 deduplication with delete+insert', total_count;

    -- Step 1: Delete any existing duplicates (by R3, R1, or job_id)
    -- This is done in bulk using a subquery for performance
    WITH incoming_hashes AS (
        SELECT DISTINCT
            (job_record->>'rules_duplicate_r3')::TEXT as r3,
            (job_record->>'rules_duplicate_r1')::TEXT as r1,
            (job_record->>'job_id')::TEXT as jid
        FROM jsonb_array_elements(p_jobs_data) as job_record
    )
    DELETE FROM jobs j
    USING incoming_hashes i
    WHERE (
        -- R3 match
        (j.rules_duplicate_r3 IS NOT NULL
         AND j.rules_duplicate_r3 != ''
         AND j.rules_duplicate_r3 = i.r3)
        OR
        -- R1 match
        (j.rules_duplicate_r1 IS NOT NULL
         AND j.rules_duplicate_r1 != ''
         AND j.rules_duplicate_r1 = i.r1)
        OR
        -- job_id match
        (j.job_id IS NOT NULL
         AND j.job_id = i.jid)
    );

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Step 2: Insert all incoming jobs (duplicates already deleted)
    INSERT INTO jobs (
        job_id, job_title, company, location, zip_code, job_description, apply_url, salary,
        match_level, match_reason, summary, fair_chance, endorsements, route_type,
        career_pathway, training_provided,
        market, tracked_url, indeed_job_url, search_query, source, filter_reason,
        classification_source, classified_at, created_at, updated_at,
        rules_duplicate_r1, rules_duplicate_r2, rules_duplicate_r3,
        clean_apply_url, job_id_hash
    )
    SELECT
        (job_record->>'job_id')::TEXT,
        (job_record->>'job_title')::TEXT,
        (job_record->>'company')::TEXT,
        (job_record->>'location')::TEXT,
        (job_record->>'zip_code')::TEXT,
        (job_record->>'job_description')::TEXT,
        (job_record->>'apply_url')::TEXT,
        (job_record->>'salary')::TEXT,
        (job_record->>'match_level')::TEXT,
        (job_record->>'match_reason')::TEXT,
        (job_record->>'summary')::TEXT,
        (job_record->>'fair_chance')::TEXT,
        (job_record->>'endorsements')::TEXT,
        (job_record->>'route_type')::TEXT,
        (job_record->>'career_pathway')::TEXT,
        (job_record->>'training_provided')::BOOLEAN,
        (job_record->>'market')::TEXT,
        (job_record->>'tracked_url')::TEXT,
        (job_record->>'indeed_job_url')::TEXT,
        (job_record->>'search_query')::TEXT,
        (job_record->>'source')::TEXT,
        (job_record->>'filter_reason')::TEXT,
        (job_record->>'classification_source')::TEXT,
        COALESCE((job_record->>'classified_at')::TIMESTAMPTZ, NOW()),
        COALESCE((job_record->>'created_at')::TIMESTAMPTZ, NOW()),
        COALESCE((job_record->>'updated_at')::TIMESTAMPTZ, NOW()),
        (job_record->>'rules_duplicate_r1')::TEXT,
        (job_record->>'rules_duplicate_r2')::TEXT,
        (job_record->>'rules_duplicate_r3')::TEXT,
        (job_record->>'clean_apply_url')::TEXT,
        (job_record->>'job_id_hash')::TEXT
    FROM jsonb_array_elements(p_jobs_data) as job_record;

    -- Get count of inserted records
    GET DIAGNOSTICS inserted_count = ROW_COUNT;

    -- Log results
    RAISE NOTICE 'Deleted % duplicates, inserted % jobs out of % total',
                 deleted_count, inserted_count, total_count;

    RETURN inserted_count;
END;
$$;
