-- Optimize batch_insert_jobs_with_dedup by avoiding JSON extraction in CTE
-- The slow part was extracting JSON fields in the DELETE CTE
-- New approach: Simple upsert based on a single unique constraint

-- First, add a unique constraint on rules_duplicate_r3 (most specific dedup key)
CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_r3_unique ON jobs(rules_duplicate_r3)
WHERE rules_duplicate_r3 IS NOT NULL AND rules_duplicate_r3 != '';

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
    RAISE NOTICE 'Processing % job records for R3 deduplication', total_count;

    -- Simple INSERT with ON CONFLICT for R3 deduplication
    -- This is MUCH faster than DELETE + INSERT
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
    ON CONFLICT (rules_duplicate_r3) DO UPDATE SET
        updated_at = EXCLUDED.updated_at,
        tracked_url = EXCLUDED.tracked_url,
        classified_at = EXCLUDED.classified_at;

    -- Get count of inserted/updated records
    GET DIAGNOSTICS inserted_count = ROW_COUNT;

    -- Log results
    RAISE NOTICE 'Upserted % records out of % total', inserted_count, total_count;

    RETURN inserted_count;
END;
$$;
