-- Enhanced Feedback System Schema
-- Adds intelligent feedback tracking with expiry and counters

-- 1. Jobs Table - Add feedback tracking columns
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_flagged BOOLEAN DEFAULT FALSE;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS feedback_expired_links INTEGER DEFAULT 0;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS feedback_likes INTEGER DEFAULT 0;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS last_expired_feedback_at TIMESTAMPTZ;

-- 2. Add indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_jobs_flagged ON jobs (job_flagged);
CREATE INDEX IF NOT EXISTS idx_jobs_expired_feedback ON jobs (last_expired_feedback_at);
CREATE INDEX IF NOT EXISTS idx_jobs_match_flagged ON jobs (match_level, job_flagged);

-- 3. Agent Profiles Table - Add application tracking
ALTER TABLE agent_profiles ADD COLUMN IF NOT EXISTS total_applications INTEGER DEFAULT 0;
ALTER TABLE agent_profiles ADD COLUMN IF NOT EXISTS last_application_at TIMESTAMPTZ;

-- 4. Add comments for documentation
COMMENT ON COLUMN jobs.job_flagged IS 'TRUE for jobs with permanent negative feedback (requires_experience, not_fair_chance_friendly)';
COMMENT ON COLUMN jobs.feedback_expired_links IS 'Counter for temporary negative feedback (job_expired). Expires after 72 hours.';
COMMENT ON COLUMN jobs.feedback_likes IS 'Counter for positive feedback (i_like_this_job, i_applied_to_this_job)';
COMMENT ON COLUMN jobs.last_expired_feedback_at IS 'Timestamp of last expired link feedback. Used for 72-hour expiry logic.';
COMMENT ON COLUMN agent_profiles.total_applications IS 'Total number of job applications submitted by this agent';
COMMENT ON COLUMN agent_profiles.last_application_at IS 'Timestamp of most recent job application';