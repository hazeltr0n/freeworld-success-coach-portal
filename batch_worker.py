#!/usr/bin/env python3
"""
Batch Worker - Autonomous scheduled batch executor
Runs continuously and polls for 'submitted' batches to execute them offline.

This worker runs independently from the Streamlit app and ensures scheduled
batches execute even when no one is actively using the application.

Architecture:
1. Edge Function (triggered by pg_cron every hour) marks batches as 'submitted'
2. This worker continuously polls for 'submitted' batches
3. Worker executes batches using AsyncJobManager
4. Worker updates batch status to 'completed' or 'failed'

Usage:
    python batch_worker.py

Deploy alongside the main Streamlit app as a separate background process.
"""

import time
import logging
from datetime import datetime
from typing import Dict, Any
import traceback

from async_job_manager import AsyncJobManager
from job_memory_db import JobMemoryDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Worker configuration
POLL_INTERVAL_SECONDS = 60  # Check for new batches every 60 seconds
MAX_CONCURRENT_BATCHES = 3  # Maximum number of batches to process in parallel
BATCH_TIMEOUT_SECONDS = 600  # 10 minutes max per batch

class BatchWorker:
    """Autonomous worker that executes scheduled batches"""

    def __init__(self):
        """Initialize the batch worker"""
        self.manager = AsyncJobManager()
        self.memory = JobMemoryDB()
        self.running = True
        logger.info("🤖 Batch Worker initialized")

    def get_submitted_batches(self):
        """Retrieve all batches marked as 'submitted' and ready to execute"""
        try:
            result = self.memory.supabase.table('async_job_queue')\
                .select('*')\
                .eq('status', 'submitted')\
                .order('submitted_at', desc=False)\
                .limit(MAX_CONCURRENT_BATCHES)\
                .execute()

            return result.data if result.data else []
        except Exception as e:
            logger.error(f"❌ Error querying submitted batches: {e}")
            return []

    def execute_batch(self, job_data: Dict[str, Any]) -> bool:
        """
        Execute a single batch job

        Args:
            job_data: Job record from async_job_queue table

        Returns:
            True if successful, False if failed
        """
        job_id = job_data['id']
        job_type = job_data['job_type']
        coach_username = job_data['coach_username']
        search_params = job_data.get('search_params', {})

        logger.info(f"🚀 Executing batch {job_id} ({job_type}) for coach {coach_username}")

        try:
            # Mark as processing
            self.memory.supabase.table('async_job_queue')\
                .update({'status': 'processing', 'started_at': datetime.utcnow().isoformat()})\
                .eq('id', job_id)\
                .execute()

            # Execute based on job type
            if job_type == 'driver_pulse':
                result = self.manager.submit_driver_pulse_search(search_params, coach_username)
            elif job_type == 'google_jobs':
                result = self.manager.submit_google_search(search_params, coach_username)
            elif job_type == 'indeed_jobs':
                result = self.manager.submit_indeed_search(search_params, coach_username)
            else:
                raise ValueError(f"Unknown job type: {job_type}")

            # Mark as completed
            self.memory.supabase.table('async_job_queue')\
                .update({
                    'status': 'completed',
                    'completed_at': datetime.utcnow().isoformat(),
                    'result_count': result.get('total_jobs', 0),
                    'quality_job_count': result.get('quality_jobs', 0)
                })\
                .eq('id', job_id)\
                .execute()

            logger.info(f"✅ Batch {job_id} completed: {result.get('quality_jobs', 0)} quality jobs")
            return True

        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            logger.error(f"❌ Batch {job_id} failed: {e}")

            # Mark as failed
            try:
                self.memory.supabase.table('async_job_queue')\
                    .update({
                        'status': 'failed',
                        'completed_at': datetime.utcnow().isoformat(),
                        'error_message': error_msg[:1000]  # Limit error message length
                    })\
                    .eq('id', job_id)\
                    .execute()
            except Exception as update_error:
                logger.error(f"❌ Failed to update batch {job_id} status: {update_error}")

            return False

    def run(self):
        """Main worker loop - runs continuously"""
        logger.info(f"🏃 Batch Worker started (polling every {POLL_INTERVAL_SECONDS}s)")

        while self.running:
            try:
                # Check for submitted batches
                batches = self.get_submitted_batches()

                if batches:
                    logger.info(f"📋 Found {len(batches)} batch(es) to execute")

                    for batch in batches:
                        self.execute_batch(batch)
                else:
                    # Only log every 10th poll to avoid spam
                    if int(time.time()) % (POLL_INTERVAL_SECONDS * 10) == 0:
                        logger.debug("📭 No batches pending")

                # Wait before next poll
                time.sleep(POLL_INTERVAL_SECONDS)

            except KeyboardInterrupt:
                logger.info("⚠️ Received shutdown signal")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ Worker error: {e}")
                logger.error(traceback.format_exc())
                # Continue running even if there's an error
                time.sleep(POLL_INTERVAL_SECONDS)

        logger.info("🛑 Batch Worker stopped")

def main():
    """Entry point for batch worker"""
    worker = BatchWorker()
    worker.run()

if __name__ == "__main__":
    main()
