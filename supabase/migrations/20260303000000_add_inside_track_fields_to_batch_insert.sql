-- Add Inside Track fields to batch_insert_jobs_with_dedup function
-- These fields are optional (NULL for regular scraped jobs)

CREATE OR REPLACE FUNCTION batch_insert_jobs_with_dedup(p_jobs_data JSONB)
RETURNS INTEGER
LANGUAGE plpgsql
SET statement_timeout = '300s'  -- 5 minute timeout
AS $$
DECLARE
    inserted_count INTEGER := 0;
    total_count INTEGER := 0;
    deleted_r3_dupes INTEGER := 0;
BEGIN
    -- Count total records in input
    SELECT jsonb_array_length(p_jobs_data) INTO total_count;

    -- Log the operation
    RAISE NOTICE 'Processing % job records for upsert', total_count;

    -- LAYER 1: INSERT with ON CONFLICT on job_id (PRIMARY KEY)
    -- Handles same job being re-scraped with updated/different classification
    INSERT INTO jobs (
        job_id, job_title, company, location, zip_code, job_description, apply_url, salary,
        match_level, match_reason, summary, fair_chance, endorsements, route_type,
        career_pathway, training_provided,
        market, tracked_url, indeed_job_url, search_query, source, filter_reason,
        classification_source, classified_at, created_at, updated_at,
        rules_duplicate_r1, rules_duplicate_r2, rules_duplicate_r3,
        clean_apply_url, job_id_hash,
        -- Inside Track fields (optional, NULL for regular jobs)
        inside_track_type, success_coach, partner_name, partner_notes, expires_at
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
        (job_record->>'job_id_hash')::TEXT,
        -- Inside Track fields (will be NULL if not in JSONB)
        (job_record->>'inside_track_type')::TEXT,
        (job_record->>'success_coach')::TEXT,
        (job_record->>'partner_name')::TEXT,
        (job_record->>'partner_notes')::TEXT,
        (job_record->>'expires_at')::TIMESTAMPTZ
    FROM jsonb_array_elements(p_jobs_data) as job_record
    ON CONFLICT (job_id) DO UPDATE SET
        -- Update ALL fields when same job_id is re-uploaded
        job_title = EXCLUDED.job_title,
        company = EXCLUDED.company,
        location = EXCLUDED.location,
        zip_code = EXCLUDED.zip_code,
        job_description = EXCLUDED.job_description,
        apply_url = EXCLUDED.apply_url,
        salary = EXCLUDED.salary,
        match_level = EXCLUDED.match_level,
        match_reason = EXCLUDED.match_reason,
        summary = EXCLUDED.summary,
        fair_chance = EXCLUDED.fair_chance,
        endorsements = EXCLUDED.endorsements,
        route_type = EXCLUDED.route_type,
        career_pathway = EXCLUDED.career_pathway,
        training_provided = EXCLUDED.training_provided,
        market = EXCLUDED.market,
        tracked_url = EXCLUDED.tracked_url,
        indeed_job_url = EXCLUDED.indeed_job_url,
        search_query = EXCLUDED.search_query,
        source = EXCLUDED.source,
        filter_reason = EXCLUDED.filter_reason,
        classification_source = EXCLUDED.classification_source,
        classified_at = EXCLUDED.classified_at,
        updated_at = EXCLUDED.updated_at,
        rules_duplicate_r1 = EXCLUDED.rules_duplicate_r1,
        rules_duplicate_r2 = EXCLUDED.rules_duplicate_r2,
        rules_duplicate_r3 = EXCLUDED.rules_duplicate_r3,
        clean_apply_url = EXCLUDED.clean_apply_url,
        job_id_hash = EXCLUDED.job_id_hash,
        -- Inside Track fields (only update if new value is not NULL)
        inside_track_type = COALESCE(EXCLUDED.inside_track_type, jobs.inside_track_type),
        success_coach = COALESCE(EXCLUDED.success_coach, jobs.success_coach),
        partner_name = COALESCE(EXCLUDED.partner_name, jobs.partner_name),
        partner_notes = COALESCE(EXCLUDED.partner_notes, jobs.partner_notes),
        expires_at = COALESCE(EXCLUDED.expires_at, jobs.expires_at);

    -- Get count of inserted/updated records
    GET DIAGNOSTICS inserted_count = ROW_COUNT;

    RAISE NOTICE 'Upserted % records out of % total', inserted_count, total_count;

    -- LAYER 2: R3 Deduplication - Remove duplicate R3 hashes, keep most recent
    -- Skip dedup for inside_track jobs (they don't have R3 hashes)
    DELETE FROM jobs a
    USING jobs b
    WHERE a.rules_duplicate_r3 = b.rules_duplicate_r3
      AND a.rules_duplicate_r3 IS NOT NULL
      AND a.updated_at < b.updated_at
      AND a.job_id != b.job_id;

    GET DIAGNOSTICS deleted_r3_dupes = ROW_COUNT;

    RAISE NOTICE 'Deleted % R3 duplicate jobs (keeping most recent)', deleted_r3_dupes;

    RETURN inserted_count;
END;
$$;

COMMENT ON FUNCTION batch_insert_jobs_with_dedup IS 'Dual-layer dedup with Inside Track support: job_id conflict handling + R3 cleanup';
