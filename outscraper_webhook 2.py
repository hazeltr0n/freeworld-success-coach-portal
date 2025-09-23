#!/usr/bin/env python3
"""
Outscraper Webhook Endpoint for Async Job Completion
Receives notifications when Google Jobs searches complete
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from async_job_manager import AsyncJobManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('outscraper_webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def load_secrets():
    """Load environment variables from secrets file"""
    try:
        import toml
        secrets_path = ".streamlit/secrets.toml"
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            for key, value in secrets.items():
                os.environ[key] = str(value)
            return True
        return False
    except Exception as e:
        logger.error(f"Error loading secrets: {e}")
        return False

# Load secrets on startup
if not load_secrets():
    logger.warning("Could not load secrets - webhook may not work properly")

@app.route('/webhook/outscraper/job-complete', methods=['POST'])
def handle_outscraper_completion():
    """
    Handle Outscraper job completion webhook
    
    Expected payload format from Outscraper:
    {
        "id": "request-id",
        "status": "Success" | "Failed",
        "results_location": "https://api.outscraper.cloud/requests/request-id",
        "data": [...] // actual results if successful
    }
    """
    try:
        # Log the webhook receipt
        logger.info("🔔 Received Outscraper webhook")
        
        # Get the JSON payload
        if not request.is_json:
            logger.error("Webhook payload is not JSON")
            return jsonify({"error": "Expected JSON payload"}), 400
            
        payload = request.get_json()
        logger.info(f"Webhook payload keys: {list(payload.keys())}")
        
        # Extract key information
        request_id = payload.get('id')
        status = payload.get('status', 'Unknown')
        
        if not request_id:
            logger.error("No request ID in webhook payload")
            return jsonify({"error": "Missing request ID"}), 400
        
        logger.info(f"Processing webhook for request: {request_id}, status: {status}")
        
        # Optional: verify webhook secret if configured
        secret_cfg = os.getenv('OUTSCRAPER_WEBHOOK_SECRET')
        if secret_cfg:
            provided = request.headers.get('X-Webhook-Secret') or request.args.get('secret')
            if provided != secret_cfg:
                logger.warning("Invalid webhook secret")
                return jsonify({"error": "Unauthorized"}), 401

        # Initialize async job manager
        manager = AsyncJobManager()
        
        # Find the job by request_id
        pending_jobs = manager.get_pending_jobs()
        target_job = None
        
        for job in pending_jobs:
            if job.request_id == request_id:
                target_job = job
                break
        
        if not target_job:
            logger.warning(f"No pending job found for request_id: {request_id}")
            # Still return success - job might have been processed already
            return jsonify({"status": "ok", "message": "Job not found (possibly already processed)"}), 200
        
        logger.info(f"Found job {target_job.id} for request {request_id}")
        
        if status.lower() in ['success', 'completed', 'finished']:
            # Job completed successfully - process it
            logger.info(f"Processing successful completion of job {target_job.id}")
            
            try:
                # Mark as processing
                try:
                    manager.update_job(target_job.id, {
                        'status': 'processing',
                        'submitted_at': target_job.submitted_at.isoformat() if target_job.submitted_at else None
                    })
                except Exception:
                    pass

                # If Outscraper included data, process inline to avoid extra polling
                data = payload.get('data')
                if isinstance(data, list) and len(data) > 0:
                    logger.info(f"Inline processing {len(data)} result chunk(s) from webhook payload")
                    try:
                        # Build DataFrame from payload using manager utility
                        jobs_df = manager.process_google_results(data, target_job.search_params)

                        # Store all scraped jobs
                        manager.store_all_jobs_supabase(jobs_df, source='google', job=target_job)

                        # Classify
                        try:
                            from job_classifier import JobClassifier
                            classifier = JobClassifier()
                            classified_df = classifier.classify_batch(jobs_df)
                        except Exception as e:
                            logger.error(f"Classification failed: {e}")
                            classified_df = jobs_df.copy()
                            classified_df['ai.match'] = 'error'
                            classified_df['ai.summary'] = 'Classification failed'

                        # Insert into memory DB
                        try:
                            from job_memory_db import JobMemoryDB
                            memory_db = JobMemoryDB()
                            memory_db.insert_jobs(classified_df)
                        except Exception as e:
                            logger.error(f"Memory DB insert failed: {e}")

                        # Quality subset
                        quality_jobs = classified_df[classified_df.get('ai.match', 'error').isin(['good', 'so-so'])]

                        # Optional Airtable sync
                        airtable_count = 0
                        if len(quality_jobs) > 0:
                            try:
                                from airtable_uploader import sync_jobs_to_airtable
                                airtable_count = sync_jobs_to_airtable(quality_jobs, target_job.coach_username)
                            except Exception as e:
                                logger.error(f"Airtable sync failed: {e}")

                        # Update job status and notify
                        manager.update_job(target_job.id, {
                            'status': 'completed',
                            'result_count': len(jobs_df),
                            'quality_job_count': len(quality_jobs),
                            'completed_at': datetime.now().isoformat()
                        })

                        loc = target_job.search_params.get('location', 'Unknown')
                        manager.notify_coach(
                            target_job.coach_username,
                            f"✅ Google search for {loc} complete! {len(quality_jobs)} quality jobs ready. Search any location to see them!",
                            'search_complete',
                            target_job.id
                        )
                    except Exception as e:
                        logger.error(f"Inline processing error: {e}")
                        # Fallback to manager polling
                        manager.process_completed_google_job(target_job.id)
                else:
                    # No inline data; use manager to poll results
                    manager.process_completed_google_job(target_job.id)
                logger.info(f"✅ Successfully processed job {target_job.id}")
                
                return jsonify({
                    "status": "ok", 
                    "message": f"Job {target_job.id} processed successfully",
                    "job_id": target_job.id,
                    "request_id": request_id
                }), 200
                
            except Exception as e:
                logger.error(f"Error processing job {target_job.id}: {e}")
                
                # Mark job as failed
                manager.update_job(target_job.id, {
                    'status': 'failed',
                    'completed_at': datetime.now().isoformat(),
                    'error_message': f'Processing error: {str(e)}'
                })
                
                # Notify coach of failure
                manager.notify_coach(
                    target_job.coach_username,
                    f"❌ Google Jobs search failed during processing: {str(e)}",
                    'error',
                    target_job.id
                )
                
                return jsonify({
                    "status": "error",
                    "message": f"Failed to process job {target_job.id}: {str(e)}"
                }), 500
        
        elif status.lower() in ['failed', 'error']:
            # Job failed - mark as failed
            logger.info(f"Marking job {target_job.id} as failed")
            
            error_message = payload.get('error', 'Job failed on Outscraper side')
            
            manager.update_job(target_job.id, {
                'status': 'failed',
                'completed_at': datetime.now().isoformat(),
                'error_message': error_message
            })
            
            # Notify coach of failure
            manager.notify_coach(
                target_job.coach_username,
                f"❌ Google Jobs search failed: {error_message}",
                'error',
                target_job.id
            )
            
            logger.info(f"Job {target_job.id} marked as failed: {error_message}")
            
            return jsonify({
                "status": "ok",
                "message": f"Job {target_job.id} marked as failed",
                "job_id": target_job.id,
                "error": error_message
            }), 200
        
        else:
            logger.warning(f"Unknown status '{status}' for request {request_id}")
            return jsonify({
                "status": "ok",
                "message": f"Unknown status: {status}"
            }), 200
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/webhook/outscraper/health', methods=['GET'])
def health_check():
    """Health check endpoint for webhook service"""
    return jsonify({
        "status": "healthy",
        "service": "outscraper-webhook",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/webhook/outscraper/status', methods=['GET'])
def webhook_status():
    """Status endpoint showing webhook configuration"""
    try:
        # Load secrets and check AsyncJobManager
        if not load_secrets():
            return jsonify({"error": "Could not load secrets"}), 500
            
        manager = AsyncJobManager()
        pending_count = len(manager.get_pending_jobs())
        completed_count = len(manager.get_completed_jobs(limit=10))
        
        return jsonify({
            "status": "active",
            "webhook_url": request.base_url.replace('/status', '/job-complete'),
            "pending_jobs": pending_count,
            "recent_completed_jobs": completed_count,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Status check failed: {str(e)}"}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Outscraper Webhook Service")
    logger.info("Webhook endpoint: /webhook/outscraper/job-complete")
    logger.info("Health check: /webhook/outscraper/health")
    logger.info("Status check: /webhook/outscraper/status")
    
    # Run in production mode
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('WEBHOOK_PORT', 5000)),
        debug=False,
        threaded=True
    )
