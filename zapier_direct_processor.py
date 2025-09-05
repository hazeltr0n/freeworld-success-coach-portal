#!/usr/bin/env python3
"""
Direct Zapier Processing Functions
These functions can be called directly from Zapier Code actions
No server required - just upload these functions to Zapier
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List

def process_outscraper_webhook_in_zapier(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process Outscraper webhook data directly in Zapier Code action
    
    This function is designed to run inside Zapier's Python code environment
    It returns structured data that can be used by subsequent Zapier actions
    """
    
    try:
        # Extract key information
        request_id = webhook_data.get('id')
        status = webhook_data.get('status', 'Unknown')
        raw_data = webhook_data.get('data', [])
        
        if not request_id:
            return {
                'status': 'error',
                'message': 'No request ID in webhook data',
                'jobs_found': 0,
                'quality_jobs': 0
            }
        
        if status.lower() not in ['success', 'completed', 'finished']:
            return {
                'status': 'failed',
                'message': f'Job failed with status: {status}',
                'request_id': request_id,
                'jobs_found': 0,
                'quality_jobs': 0
            }
        
        # Process the job data
        processed_jobs = []
        
        # Flatten nested structure
        all_jobs = []
        for query_results in raw_data:
            if isinstance(query_results, list):
                all_jobs.extend(query_results)
            elif isinstance(query_results, dict):
                all_jobs.append(query_results)
        
        # Convert each job to our format
        for job in all_jobs:
            if not isinstance(job, dict):
                continue
            
            # Extract apply URL
            apply_url = ''
            try:
                apply_options = job.get('apply_options', [])
                if apply_options and isinstance(apply_options, list):
                    apply_url = apply_options[0].get('link', '') if isinstance(apply_options[0], dict) else ''
            except (IndexError, KeyError, AttributeError):
                pass
            
            processed_job = {
                'title': job.get('title', ''),
                'company': job.get('company_name', ''),
                'location': job.get('location', ''),
                'description': job.get('description', ''),
                'salary': job.get('salary', ''),
                'posted_date': job.get('detected_extensions', {}).get('posted_at', '') if isinstance(job.get('detected_extensions'), dict) else '',
                'google_url': job.get('link', ''),
                'apply_url': apply_url,
                'request_id': request_id
            }
            processed_jobs.append(processed_job)
        
        # Simple quality assessment (without AI for now)
        quality_jobs = []
        for job in processed_jobs:
            title = job['title'].lower()
            description = job['description'].lower()
            
            # Basic quality indicators
            is_cdl_job = any(term in title or term in description for term in ['cdl', 'truck driver', 'driver', 'commercial driver'])
            is_not_school_bus = 'school bus' not in title and 'school bus' not in description
            has_salary = bool(job['salary'])
            
            if is_cdl_job and is_not_school_bus:
                quality_jobs.append(job)
        
        return {
            'status': 'success',
            'message': f'Processed {len(processed_jobs)} jobs, {len(quality_jobs)} quality matches',
            'request_id': request_id,
            'jobs_found': len(processed_jobs),
            'quality_jobs': len(quality_jobs),
            'jobs_data': processed_jobs,
            'quality_jobs_data': quality_jobs
        }
        
    except Exception as e:
        return {
            'status': 'error', 
            'message': f'Processing failed: {str(e)}',
            'request_id': request_id if 'request_id' in locals() else 'unknown',
            'jobs_found': 0,
            'quality_jobs': 0
        }

# Zapier-friendly wrapper
def zapier_webhook_handler(input_data):
    """
    Main function to be called from Zapier Code action
    
    In Zapier, use this code:
    
    import requests
    
    # Your webhook data comes in as 'input_data'
    result = zapier_webhook_handler(input_data)
    
    # Return the result for use in subsequent actions
    return result
    """
    return process_outscraper_webhook_in_zapier(input_data)

# Sample Zapier Code action setup
ZAPIER_CODE_TEMPLATE = '''
# Zapier Code Action for Outscraper Webhook Processing
# Copy this code into a Zapier "Code by Zapier" action

def main(input_data):
    """Process Outscraper webhook data"""
    
    # Extract webhook data
    webhook_data = {
        'id': input_data.get('id'),
        'status': input_data.get('status'),
        'data': input_data.get('data', [])
    }
    
    try:
        request_id = webhook_data.get('id')
        status = webhook_data.get('status', 'Unknown')
        raw_data = webhook_data.get('data', [])
        
        if not request_id:
            return {'status': 'error', 'message': 'No request ID'}
        
        if status.lower() not in ['success', 'completed', 'finished']:
            return {'status': 'failed', 'message': f'Job failed: {status}'}
        
        # Process jobs
        all_jobs = []
        for query_results in raw_data:
            if isinstance(query_results, list):
                all_jobs.extend(query_results)
            elif isinstance(query_results, dict):
                all_jobs.append(query_results)
        
        processed_jobs = []
        for job in all_jobs:
            if not isinstance(job, dict):
                continue
                
            # Extract apply URL
            apply_url = ''
            try:
                apply_options = job.get('apply_options', [])
                if apply_options and isinstance(apply_options, list):
                    apply_url = apply_options[0].get('link', '')
            except:
                pass
            
            processed_jobs.append({
                'title': job.get('title', ''),
                'company': job.get('company_name', ''),
                'location': job.get('location', ''),
                'description': job.get('description', ''),
                'salary': job.get('salary', ''),
                'apply_url': apply_url,
                'google_url': job.get('link', ''),
                'posted_date': job.get('detected_extensions', {}).get('posted_at', ''),
                'request_id': request_id
            })
        
        # Basic quality filter
        quality_jobs = []
        for job in processed_jobs:
            title_desc = (job['title'] + ' ' + job['description']).lower()
            if any(term in title_desc for term in ['cdl', 'truck driver', 'driver']) and 'school bus' not in title_desc:
                quality_jobs.append(job)
        
        return {
            'status': 'success',
            'request_id': request_id,
            'total_jobs': len(processed_jobs),
            'quality_jobs_count': len(quality_jobs),
            'quality_jobs': quality_jobs[:10]  # Limit to 10 for Zapier
        }
        
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
'''