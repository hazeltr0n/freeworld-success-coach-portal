-- Create job_feedback table for Free Agent job quality feedback
CREATE TABLE job_feedback (
    id SERIAL PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    job_id TEXT,
    job_url TEXT NOT NULL,
    job_title TEXT,
    company TEXT,
    feedback_type TEXT DEFAULT 'job_expired' CHECK (feedback_type IN ('job_expired', 'requires_experience', 'not_fair_chance_friendly', 'i_like_this_job', 'i_applied_to_this_job')),
    location TEXT,
    coach TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for fast lookups by candidate
CREATE INDEX idx_job_feedback_candidate_id ON job_feedback(candidate_id);

-- Create index for fast lookups by job ID
CREATE INDEX idx_job_feedback_job_id ON job_feedback(job_id);

-- Create index for fast lookups by job URL (to avoid showing reported jobs)
CREATE INDEX idx_job_feedback_job_url ON job_feedback(job_url);

-- Create index for coach analytics
CREATE INDEX idx_job_feedback_coach ON job_feedback(coach);

-- Create index for date-based queries
CREATE INDEX idx_job_feedback_created_at ON job_feedback(created_at);

-- Enable Row Level Security
ALTER TABLE job_feedback ENABLE ROW LEVEL SECURITY;

-- Create policy to allow inserting feedback
CREATE POLICY "Allow feedback insertion" ON job_feedback
FOR INSERT WITH CHECK (true);

-- Create policy to allow reading feedback for analytics
CREATE POLICY "Allow feedback reading" ON job_feedback  
FOR SELECT USING (true);