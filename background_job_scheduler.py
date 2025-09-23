#!/usr/bin/env python3
"""
FreeWorld Background Job Scheduler - The Real Deal
==================================================

This is the actual backbone that makes "Save for Later" work.
Runs independently of the Streamlit app to process scheduled jobs 24/7.

Usage:
    python background_job_scheduler.py

Features:
- Processes scheduled Indeed and Google Jobs
- Handles recurring schedules (daily, weekly)
- Proper error handling and logging
- Never stops running (daemon mode)
- Keeps the job pipeline flowing automatically
"""

import os
import sys
import time
import logging
import traceback
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import signal

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our job management system
try:
    from async_job_manager import AsyncJobManager, AsyncJob
    from supabase_utils import get_client
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("Make sure you're running from the correct directory with all dependencies installed")
    sys.exit(1)

class BackgroundJobScheduler:
    def __init__(self):
        self.running = True
        self.job_manager = AsyncJobManager()
        self.supabase_client = get_client()
        self.check_interval = 60  # Check every 60 seconds

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('background_scheduler.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info("🚀 Background Job Scheduler initialized")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"📥 Received signal {signum}, shutting down gracefully...")
        self.running = False

    def get_ready_scheduled_jobs(self) -> List[AsyncJob]:
        """Get all scheduled jobs that are ready to run"""
        if not self.supabase_client:
            self.logger.error("❌ Supabase client not available")
            return []

        try:
            now = datetime.now(timezone.utc)

            # Query for scheduled jobs that are ready to run
            result = self.supabase_client.table('async_job_queue').select('*').eq('status', 'scheduled').execute()

            ready_jobs = []
            for job_data in result.data:
                # Check if job has a scheduled_run_at time
                scheduled_run_at = job_data.get('scheduled_run_at')
                if not scheduled_run_at:
                    continue

                # Parse the scheduled time
                try:
                    run_time = datetime.fromisoformat(scheduled_run_at.replace('Z', '+00:00'))
                    if run_time <= now:
                        # Convert to AsyncJob object
                        job = AsyncJob(
                            id=job_data['id'],
                            scheduled_search_id=job_data.get('scheduled_search_id'),
                            coach_username=job_data['coach_username'],
                            job_type=job_data['job_type'],
                            request_id=job_data.get('request_id'),
                            status=job_data['status'],
                            search_params=job_data['search_params'],
                            submitted_at=job_data.get('submitted_at'),
                            completed_at=job_data.get('completed_at'),
                            result_count=job_data['result_count'],
                            quality_job_count=job_data['quality_job_count'],
                            error_message=job_data.get('error_message'),
                            csv_filename=job_data.get('csv_filename'),
                            created_at=datetime.fromisoformat(job_data['created_at'].replace('Z', '+00:00'))
                        )
                        ready_jobs.append(job)
                except ValueError as e:
                    self.logger.warning(f"⚠️ Invalid scheduled_run_at format for job {job_data['id']}: {e}")

            return ready_jobs

        except Exception as e:
            self.logger.error(f"❌ Error getting ready scheduled jobs: {e}")
            return []

    def execute_indeed_job(self, job: AsyncJob) -> bool:
        """Execute a scheduled Indeed job"""
        try:
            self.logger.info(f"🔄 Executing Indeed job {job.id} for {job.coach_username}")

            # Update status to processing
            self.job_manager.update_job(job.id, {
                'status': 'processing',
                'submitted_at': datetime.now(timezone.utc).isoformat()
            })

            # Execute the Indeed search using the same logic as submit_indeed_search
            from pipeline_wrapper import StreamlitPipelineWrapper
            pipeline = StreamlitPipelineWrapper()

            # Convert search params to pipeline format
            pipeline_params = {
                'mode': job.search_params.get('mode', 'sample'),
                'location': job.search_params['location'],
                'search_terms': job.search_params['search_terms'],
                'search_radius': job.search_params.get('search_radius', 50),
                'exact_location': job.search_params.get('exact_location', False),
                'force_fresh': True,
                'force_fresh_classification': job.search_params.get('force_fresh_classification', False),
                'no_experience': job.search_params.get('no_experience', True),
                'memory_only': False,
                'search_sources': {'indeed': True, 'google': False},
                'search_strategy': 'fresh_first',
                'push_to_airtable': False,
                'generate_pdf': False,
                'generate_csv': False,
                'candidate_id': '',
                'candidate_name': '',
                'max_jobs': job.search_params.get('limit', 250),
                'coach_username': job.coach_username
            }

            self.logger.info(f"📋 Running pipeline for {job.coach_username}: {pipeline_params['location']} - {pipeline_params['search_terms']}")

            # Run the pipeline
            df, metadata = pipeline.run_pipeline(pipeline_params)

            if metadata.get('success', False) and df is not None and not df.empty:
                result_count = len(df)
                quality_count = len(df[df.get('ai.match', '') == 'good']) if 'ai.match' in df.columns else 0

                self.logger.info(f"✅ Indeed job {job.id} completed: {result_count} jobs found, {quality_count} quality jobs")

                # Store results
                try:
                    self.job_manager.store_scraped_jobs(df, job.coach_username)
                    self.logger.info(f"📊 Stored {result_count} jobs to Supabase for {job.coach_username}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to store jobs to Supabase for job {job.id}: {e}")

                # Update job as completed
                self.job_manager.update_job(job.id, {
                    'status': 'completed',
                    'completed_at': datetime.now(timezone.utc).isoformat(),
                    'result_count': result_count,
                    'quality_job_count': quality_count
                })

                # Send notification to coach
                self.job_manager.notify_coach(
                    job.coach_username,
                    f"✅ Scheduled Indeed search completed: {result_count} jobs found ({quality_count} quality)",
                    'search_complete',
                    job.id
                )

                return True

            else:
                # Job failed
                error_msg = metadata.get('error_message', 'Unknown error during pipeline execution')
                self.logger.error(f"❌ Indeed job {job.id} failed: {error_msg}")

                self.job_manager.update_job(job.id, {
                    'status': 'failed',
                    'completed_at': datetime.now(timezone.utc).isoformat(),
                    'error_message': error_msg
                })

                self.job_manager.notify_coach(
                    job.coach_username,
                    f"❌ Scheduled Indeed search failed: {error_msg}",
                    'error',
                    job.id
                )

                return False

        except Exception as e:
            error_msg = f"Exception during Indeed job execution: {str(e)}"
            self.logger.error(f"❌ Error executing Indeed job {job.id}: {error_msg}")
            self.logger.error(traceback.format_exc())

            self.job_manager.update_job(job.id, {
                'status': 'failed',
                'completed_at': datetime.now(timezone.utc).isoformat(),
                'error_message': error_msg
            })

            self.job_manager.notify_coach(
                job.coach_username,
                f"❌ Scheduled Indeed search failed: {error_msg}",
                'error',
                job.id
            )

            return False

    def execute_google_job(self, job: AsyncJob) -> bool:
        """Execute a scheduled Google job using async submission"""
        try:
            self.logger.info(f"🌐 Executing Google job {job.id} for {job.coach_username}")

            # For Google jobs, we submit them to the async system
            # The webhook will handle completion
            submitted_job = self.job_manager.submit_google_search(job.search_params, job.coach_username)

            # Update the original scheduled job to mark it as submitted
            self.job_manager.update_job(job.id, {
                'status': 'submitted_async',
                'submitted_at': datetime.now(timezone.utc).isoformat(),
                'request_id': submitted_job.request_id
            })

            self.logger.info(f"✅ Google job {job.id} submitted to async system with request_id: {submitted_job.request_id}")

            self.job_manager.notify_coach(
                job.coach_username,
                f"🌐 Scheduled Google Jobs search submitted for processing (2-5 min)",
                'search_submitted',
                job.id
            )

            return True

        except Exception as e:
            error_msg = f"Exception during Google job submission: {str(e)}"
            self.logger.error(f"❌ Error executing Google job {job.id}: {error_msg}")
            self.logger.error(traceback.format_exc())

            self.job_manager.update_job(job.id, {
                'status': 'failed',
                'completed_at': datetime.now(timezone.utc).isoformat(),
                'error_message': error_msg
            })

            self.job_manager.notify_coach(
                job.coach_username,
                f"❌ Scheduled Google search failed: {error_msg}",
                'error',
                job.id
            )

            return False

    def handle_recurring_job(self, job: AsyncJob) -> bool:
        """Handle recurring schedules by creating the next job instance"""
        try:
            search_params = job.search_params
            frequency = search_params.get('frequency', 'once')

            if frequency == 'once':
                # One-time job, nothing to reschedule
                return True

            # Calculate next run time
            from datetime import datetime, timezone, timedelta

            run_time_str = search_params.get('time', '02:00')
            days = search_params.get('days', [])

            now = datetime.now(timezone.utc)

            if frequency == 'daily':
                # Schedule for next day at the same time
                next_run = now.replace(
                    hour=int(run_time_str.split(':')[0]),
                    minute=int(run_time_str.split(':')[1]),
                    second=0, microsecond=0
                ) + timedelta(days=1)

            elif frequency == 'weekly':
                # Find next occurrence of the specified days
                # For now, schedule for next week (could be enhanced to find next matching day)
                next_run = now.replace(
                    hour=int(run_time_str.split(':')[0]),
                    minute=int(run_time_str.split(':')[1]),
                    second=0, microsecond=0
                ) + timedelta(days=7)
            else:
                # Unknown frequency, don't reschedule
                return True

            # Create new scheduled job
            new_search_params = search_params.copy()
            new_job_data = {
                'coach_username': job.coach_username,
                'job_type': job.job_type,
                'search_params': new_search_params,
                'status': 'scheduled',
                'result_count': 0,
                'quality_job_count': 0,
                'created_at': now.isoformat(),
                'scheduled_run_at': next_run.isoformat()
            }

            result = self.supabase_client.table('async_job_queue').insert(new_job_data).execute()

            if result.data:
                new_job_id = result.data[0]['id']
                self.logger.info(f"🔄 Created recurring job {new_job_id} for {job.coach_username} (next run: {next_run})")
                return True
            else:
                self.logger.error(f"❌ Failed to create recurring job for {job.coach_username}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error handling recurring job {job.id}: {e}")
            return False

    def process_ready_jobs(self):
        """Main job processing loop"""
        ready_jobs = self.get_ready_scheduled_jobs()

        if not ready_jobs:
            return

        self.logger.info(f"📋 Found {len(ready_jobs)} ready scheduled jobs")

        for job in ready_jobs:
            try:
                self.logger.info(f"🎯 Processing job {job.id} ({job.job_type}) for {job.coach_username}")

                success = False
                if job.job_type == 'indeed_jobs':
                    success = self.execute_indeed_job(job)
                elif job.job_type == 'google_jobs':
                    success = self.execute_google_job(job)
                else:
                    self.logger.warning(f"⚠️ Unknown job type: {job.job_type}")
                    continue

                # Handle recurring schedules
                if success:
                    self.handle_recurring_job(job)

            except Exception as e:
                self.logger.error(f"❌ Error processing job {job.id}: {e}")
                self.logger.error(traceback.format_exc())

                # Mark job as failed
                self.job_manager.update_job(job.id, {
                    'status': 'failed',
                    'completed_at': datetime.now(timezone.utc).isoformat(),
                    'error_message': str(e)
                })

    def run(self):
        """Main scheduler loop - runs forever"""
        self.logger.info("🚀 Background Job Scheduler starting...")
        self.logger.info(f"⏰ Checking for scheduled jobs every {self.check_interval} seconds")

        while self.running:
            try:
                start_time = time.time()

                # Process ready jobs
                self.process_ready_jobs()

                # Calculate sleep time (accounting for processing time)
                processing_time = time.time() - start_time
                sleep_time = max(0, self.check_interval - processing_time)

                if sleep_time > 0:
                    time.sleep(sleep_time)

            except KeyboardInterrupt:
                self.logger.info("⏹️ Received interrupt signal, shutting down...")
                break
            except Exception as e:
                self.logger.error(f"❌ Unexpected error in main loop: {e}")
                self.logger.error(traceback.format_exc())
                time.sleep(self.check_interval)  # Sleep before retrying

        self.logger.info("🔚 Background Job Scheduler stopped")

def main():
    """Main entry point"""
    print("🚀 FreeWorld Background Job Scheduler")
    print("=====================================")
    print("This process will run continuously to execute scheduled jobs.")
    print("Press Ctrl+C to stop.")
    print("")

    try:
        scheduler = BackgroundJobScheduler()
        scheduler.run()
    except KeyboardInterrupt:
        print("\n⏹️ Scheduler stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()