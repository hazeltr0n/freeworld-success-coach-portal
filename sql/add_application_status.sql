-- Add application_status column to job_feedback table
ALTER TABLE job_feedback
ADD COLUMN IF NOT EXISTS application_status TEXT DEFAULT 'applied'
CHECK (application_status IN ('applied', 'haven''t heard back', 'rejected', 'hired'));

-- Create index for status filtering
CREATE INDEX IF NOT EXISTS idx_job_feedback_status ON job_feedback(application_status);

-- Update existing records to default status
UPDATE job_feedback
SET application_status = 'applied'
WHERE application_status IS NULL;
