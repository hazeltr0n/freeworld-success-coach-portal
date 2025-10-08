-- Fix batch_insert_jobs_with_dedup function to include all fields
CREATE OR REPLACE FUNCTION batch_insert_jobs_with_dedup(p_jobs_data JSONB)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    inserted_count INTEGER := 0;
    total_count INTEGER := 0;
BEGIN
    -- Count total records in input
    SELECT jsonb_array_length(p_jobs_data) INTO total_count;

    -- Log the operation
    RAISE NOTICE 'Processing % job records for deduplication', total_count;

    -- Single bulk insert with deduplication logic
    INSERT INTO jobs (
        job_id, job_title, company, location, zip_code, job_description, apply_url, salary,
        match_level, match_reason, summary, fair_chance, endorsements, route_type,
        career_pathway, training_provided,
        market, tracked_url, indeed_job_url, search_query, source, filter_reason,
        classification_source, classified_at, created_at, updated_at,
        rules_duplicate_r1, rules_duplicate_r2, clean_apply_url, job_id_hash
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
        (job_record->>'clean_apply_url')::TEXT,
        (job_record->>'job_id_hash')::TEXT
    FROM jsonb_array_elements(p_jobs_data) as job_record
    WHERE NOT EXISTS (
        -- Check for duplicates using multiple keys
        SELECT 1 FROM jobs j WHERE (
            -- Exact job_id match
            (j.job_id IS NOT NULL AND j.job_id = (job_record->>'job_id')::TEXT)
            OR
            -- Rule-based duplicate match (r1)
            (j.rules_duplicate_r1 IS NOT NULL
             AND j.rules_duplicate_r1 != ''
             AND j.rules_duplicate_r1 = (job_record->>'rules_duplicate_r1')::TEXT)
            OR
            -- Rule-based duplicate match (r2)
            (j.rules_duplicate_r2 IS NOT NULL
             AND j.rules_duplicate_r2 != ''
             AND j.rules_duplicate_r2 = (job_record->>'rules_duplicate_r2')::TEXT)
            OR
            -- Apply URL match
            (j.clean_apply_url IS NOT NULL
             AND j.clean_apply_url != ''
             AND LENGTH(j.clean_apply_url) > 10
             AND j.clean_apply_url = (job_record->>'clean_apply_url')::TEXT)
            OR
            -- Hash match
            (j.job_id_hash IS NOT NULL
             AND j.job_id_hash != ''
             AND j.job_id_hash = (job_record->>'job_id_hash')::TEXT)
        )
    );

    -- Get count of inserted records
    GET DIAGNOSTICS inserted_count = ROW_COUNT;

    -- Log results
    RAISE NOTICE 'Inserted % new records out of % total (% duplicates skipped)',
                 inserted_count, total_count, (total_count - inserted_count);

    RETURN inserted_count;
END;
$$;
