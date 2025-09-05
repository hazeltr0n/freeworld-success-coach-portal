#!/usr/bin/env python3
"""
Zapier Webhook Processor for Outscraper Integration
Processes webhook data received from Zapier when Outscraper jobs complete
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from async_job_manager import AsyncJobManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zapier_webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ZapierWebhookProcessor:
    """
    Processes Outscraper completion data received via Zapier webhook
    This acts as a standalone processor that can be called by various triggers
    """
    
    def __init__(self):
        self.load_secrets()
        self.manager = AsyncJobManager()
    
    def load_secrets(self):
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
    
    def process_outscraper_completion(self, webhook_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Process Outscraper job completion from Zapier webhook data
        
        Args:
            webhook_data: Dictionary containing webhook payload from Zapier
            
        Returns:
            Dictionary with processing result
        """
        try:
            logger.info("🔔 Processing Outscraper completion from Zapier")
            logger.info(f"Webhook data keys: {list(webhook_data.keys())}")
            
            # Extract key information - Zapier may modify field names
            request_id = self._extract_request_id(webhook_data)
            status = self._extract_status(webhook_data)
            data = self._extract_results_data(webhook_data)
            
            if not request_id:
                error_msg = "No request ID found in webhook data"
                logger.error(error_msg)
                return {"status": "error", "message": error_msg}
            
            logger.info(f"Processing request: {request_id}, status: {status}")
            
            # Find the job by request_id
            target_job = self._find_job_by_request_id(request_id)
            if not target_job:
                warning_msg = f"No pending job found for request_id: {request_id}"
                logger.warning(warning_msg)
                return {"status": "warning", "message": warning_msg}
            
            logger.info(f"Found job {target_job.id} for request {request_id}")
            
            if status.lower() in ['success', 'completed', 'finished']:
                return self._process_successful_completion(target_job, data)
            elif status.lower() in ['failed', 'error']:
                return self._process_failed_completion(target_job, webhook_data)
            else:
                warning_msg = f"Unknown status '{status}' for request {request_id}"
                logger.warning(warning_msg)
                return {"status": "warning", "message": warning_msg}
                
        except Exception as e:
            error_msg = f"Webhook processing error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
    
    def _extract_request_id(self, webhook_data: Dict[str, Any]) -> Optional[str]:
        """Extract request ID from various possible field names"""
        possible_fields = ['id', 'request_id', 'requestId', 'outscraper_id', 'job_id']
        for field in possible_fields:
            if field in webhook_data:
                return str(webhook_data[field])
        return None
    
    def _extract_status(self, webhook_data: Dict[str, Any]) -> str:
        """Extract status from webhook data"""
        possible_fields = ['status', 'job_status', 'state']
        for field in possible_fields:
            if field in webhook_data:
                return str(webhook_data[field])
        return 'Unknown'
    
    def _extract_results_data(self, webhook_data: Dict[str, Any]) -> Optional[list]:
        """Extract results data if present in webhook"""
        possible_fields = ['data', 'results', 'job_results', 'response_data']
        for field in possible_fields:
            if field in webhook_data and isinstance(webhook_data[field], list):
                return webhook_data[field]
        return None
    
    def _find_job_by_request_id(self, request_id: str):
        """Find pending job by request ID"""
        pending_jobs = self.manager.get_pending_jobs()
        for job in pending_jobs:
            if job.request_id == request_id:
                return job
        return None
    
    def _process_successful_completion(self, target_job, data: Optional[list]) -> Dict[str, str]:
        """Process successful job completion"""
        try:
            logger.info(f"Processing successful completion of job {target_job.id}")
            
            # Mark as processing
            self.manager.update_job(target_job.id, {
                'status': 'processing',
                'submitted_at': target_job.submitted_at.isoformat() if target_job.submitted_at else None
            })
            
            if data and isinstance(data, list) and len(data) > 0:
                # Process inline data from webhook
                logger.info(f"Processing {len(data)} result chunks from webhook")
                self._process_inline_data(target_job, data)
            else:
                # Fallback to polling Outscraper API
                logger.info("No inline data, polling Outscraper API")
                self.manager.process_completed_async_job(target_job.id)
            
            return {
                "status": "success",
                "message": f"Job {target_job.id} processed successfully",
                "job_id": str(target_job.id)
            }
            
        except Exception as e:
            error_msg = f"Error processing job {target_job.id}: {str(e)}"
            logger.error(error_msg)
            
            # Mark job as failed
            self.manager.update_job(target_job.id, {
                'status': 'failed',
                'completed_at': datetime.now().isoformat(),
                'error_message': f'Processing error: {str(e)}'
            })
            
            # Notify coach of failure
            self.manager.notify_coach(
                target_job.coach_username,
                f"❌ Job search failed during processing: {str(e)}",
                'error',
                target_job.id
            )
            
            return {"status": "error", "message": error_msg}
    
    def _process_inline_data(self, target_job, data: list):
        """Process job results data directly from webhook"""
        try:
            # Convert results to DataFrame using manager
            if target_job.job_type == 'google_jobs':
                jobs_df = self.manager.process_google_results(data, target_job.search_params)
            elif target_job.job_type == 'indeed_jobs':
                jobs_df = self.manager.process_indeed_results(data, target_job.search_params)
            else:
                raise Exception(f"Unknown job type: {target_job.job_type}")
            
            if len(jobs_df) == 0:
                logger.warning("No jobs found in results data")
                self.manager.update_job(target_job.id, {
                    'status': 'completed',
                    'result_count': 0,
                    'quality_job_count': 0,
                    'completed_at': datetime.now().isoformat()
                })
                return
            
            # Complete processing pipeline
            self.manager._complete_job_processing(target_job.id, target_job, jobs_df)
            
        except Exception as e:
            logger.error(f"Inline data processing failed: {e}")
            raise
    
    def _process_failed_completion(self, target_job, webhook_data: Dict[str, Any]) -> Dict[str, str]:
        """Process failed job completion"""
        logger.info(f"Processing failed completion of job {target_job.id}")
        
        error_message = webhook_data.get('error', 'Job failed on Outscraper side')
        
        self.manager.update_job(target_job.id, {
            'status': 'failed',
            'completed_at': datetime.now().isoformat(),
            'error_message': str(error_message)
        })
        
        # Notify coach of failure
        job_type_display = "Google Jobs" if target_job.job_type == 'google_jobs' else "Indeed Jobs"
        self.manager.notify_coach(
            target_job.coach_username,
            f"❌ {job_type_display} search failed: {error_message}",
            'error',
            target_job.id
        )
        
        return {
            "status": "handled",
            "message": f"Job {target_job.id} marked as failed",
            "error": str(error_message)
        }

def process_zapier_webhook(webhook_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Standalone function to process Zapier webhook data
    Can be called from various triggers (HTTP endpoint, file processing, etc.)
    """
    processor = ZapierWebhookProcessor()
    return processor.process_outscraper_completion(webhook_data)

def test_webhook_processing():
    """Test the webhook processing with sample data"""
    logger.info("🧪 Testing webhook processing with sample data")
    
    # Sample webhook data that might come from Zapier
    test_data = {
        "id": "test-request-123",
        "status": "Success",
        "data": [
            [{
                "title": "CDL Driver - Local Routes",
                "company_name": "Test Transport Co",
                "location": "Houston, TX",
                "description": "Local CDL driving position...",
                "salary": "$55,000 - $65,000",
                "link": "https://example.com/job/123",
                "apply_options": [{"link": "https://example.com/apply/123"}],
                "detected_extensions": {"posted_at": "2 days ago"}
            }]
        ]
    }
    
    result = process_zapier_webhook(test_data)
    logger.info(f"Test result: {result}")
    return result

if __name__ == '__main__':
    logger.info("🚀 Zapier Webhook Processor")
    
    # Run test if no arguments
    import sys
    if len(sys.argv) == 1:
        test_webhook_processing()
    elif sys.argv[1] == '--test':
        test_webhook_processing()
    else:
        logger.info("Usage: python zapier_webhook_processor.py [--test]")