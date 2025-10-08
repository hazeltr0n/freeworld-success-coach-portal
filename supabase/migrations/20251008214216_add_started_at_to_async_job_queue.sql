-- Add started_at column to async_job_queue for tracking job execution times
ALTER TABLE async_job_queue
ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITH TIME ZONE;

-- Add index for performance when querying by started_at
CREATE INDEX IF NOT EXISTS idx_async_job_queue_started_at
ON async_job_queue(started_at);
