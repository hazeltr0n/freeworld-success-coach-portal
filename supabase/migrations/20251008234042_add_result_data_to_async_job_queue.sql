-- Add result_data column to async_job_queue for storing job execution results
ALTER TABLE async_job_queue
ADD COLUMN IF NOT EXISTS result_data JSONB;

-- Add comment explaining the column
COMMENT ON COLUMN async_job_queue.result_data IS 'Stores job execution results including job count and summary message';
