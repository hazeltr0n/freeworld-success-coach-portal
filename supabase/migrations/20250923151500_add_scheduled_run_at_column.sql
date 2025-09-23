-- Add scheduled_run_at column to async_job_queue table
-- This column is needed for scheduling jobs to run at specific times

ALTER TABLE async_job_queue
ADD COLUMN IF NOT EXISTS scheduled_run_at TIMESTAMPTZ;

-- Add index on scheduled_run_at for efficient querying of scheduled jobs
CREATE INDEX IF NOT EXISTS idx_async_job_queue_scheduled_run_at
ON async_job_queue (scheduled_run_at)
WHERE scheduled_run_at IS NOT NULL;

-- Add comment to document the column purpose
COMMENT ON COLUMN async_job_queue.scheduled_run_at IS 'Timestamp when the job should be executed (for scheduled jobs)';