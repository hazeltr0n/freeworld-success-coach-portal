-- Fix ON CONFLICT clause to use job_id (primary key) instead of rules_duplicate_r3
-- The R3 deduplication happens in application layer BEFORE upload
-- The RPC just needs to handle job_id conflicts (fresh vs memory jobs)

CREATE OR REPLACE FUNCTION batch_insert_jobs_with_dedup(p_jobs_data JSONB)
RETURNS INTEGER
LANGUAGE plpgsql
SET statement_timeout = '300s'  -- 5 minute timeout
AS $$
DECLARE
    inserted_count INTEGER := 0;
    total_count INTEGER := 0;
BEGIN
    -- Count total records in input
    SELECT jsonb_array_length(p_jobs_data) INTO total_count;

    -- Log the operation
    RAISE NOTICE 'Processing % job records for upsert', total_count;

    -- INSERT with ON CONFLICT on PRIMARY KEY (job_id)
    -- This handles both fresh jobs (INSERT) and memory refreshes (UPDATE)
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
    FROM jsonb_array_elements(p_jobs_data) as job_record
    ON CONFLICT (job_id) DO UPDATE SET
        -- Update timestamp fields for memory refreshes
        updated_at = EXCLUDED.updated_at,
        classified_at = EXCLUDED.classified_at,
        tracked_url = EXCLUDED.tracked_url;

    -- Get count of inserted/updated records
    GET DIAGNOSTICS inserted_count = ROW_COUNT;

    -- Log results
    RAISE NOTICE 'Upserted % records out of % total', inserted_count, total_count;

    RETURN inserted_count;
END;
$$;

COMMENT ON FUNCTION batch_insert_jobs_with_dedup IS 'Batch upsert jobs by job_id (R3 dedup in app layer)';
