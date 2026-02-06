-- Track Free Agent interest in Inside Track jobs
-- When an agent clicks "I'm Interested", we record it here and email the coach

CREATE TABLE IF NOT EXISTS inside_track_interests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- The job they're interested in
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,

    -- The Free Agent expressing interest
    agent_uuid TEXT NOT NULL,
    agent_name TEXT,
    agent_email TEXT,
    agent_phone TEXT,

    -- The coach who posted the job (for email notification)
    coach_username TEXT NOT NULL,

    -- Status tracking
    status TEXT DEFAULT 'new',  -- new, contacted, applied, hired, declined
    coach_notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    contacted_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prevent duplicate interests (one agent per job)
CREATE UNIQUE INDEX IF NOT EXISTS idx_inside_track_interests_unique
ON inside_track_interests(job_id, agent_uuid);

-- Index for coach to see their interested candidates
CREATE INDEX IF NOT EXISTS idx_inside_track_interests_coach
ON inside_track_interests(coach_username, status);

-- Index for looking up by job
CREATE INDEX IF NOT EXISTS idx_inside_track_interests_job
ON inside_track_interests(job_id);
