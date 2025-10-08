-- Add recurring_batch_group_id to track which batches belong to the same recurring schedule
ALTER TABLE async_job_queue
ADD COLUMN IF NOT EXISTS recurring_batch_group_id UUID;

-- Create index for faster grouping queries
CREATE INDEX IF NOT EXISTS idx_async_job_queue_recurring_group
ON async_job_queue(recurring_batch_group_id)
WHERE recurring_batch_group_id IS NOT NULL;

-- Add comment
COMMENT ON COLUMN async_job_queue.recurring_batch_group_id IS
'Groups batches that belong to the same recurring schedule. All runs from the same recurring batch share this ID.';
