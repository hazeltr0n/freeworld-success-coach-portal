-- Add scheduled_run_at field to async_job_queue table
-- This field stores when a scheduled job should actually be executed

-- Add the new column (nullable for existing records)
ALTER TABLE async_job_queue
ADD COLUMN scheduled_run_at TIMESTAMPTZ NULL;

-- Add index for efficient querying of ready jobs
CREATE INDEX idx_async_job_queue_scheduled_ready
ON async_job_queue (status, scheduled_run_at)
WHERE status = 'scheduled' AND scheduled_run_at IS NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN async_job_queue.scheduled_run_at IS 'When this scheduled job should be executed (UTC)';