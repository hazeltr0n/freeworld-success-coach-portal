"""
Async Job Manager for FreeWorld Success Coach Portal
Handles lifecycle of async Google Jobs searches with proper data routing
"""

import os
import json
import time
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import pandas as pd

try:
    from supabase_utils import get_client
except Exception:
    get_client = None

@dataclass
class AsyncJob:
    id: int
    scheduled_search_id: Optional[int]
    coach_username: str
    job_type: str  # 'google_jobs', 'indeed_jobs'
    request_id: Optional[str]  # Outscraper async request ID
    status: str  # 'pending', 'submitted', 'processing', 'completed', 'failed'
    search_params: Dict
    submitted_at: Optional[datetime]
    completed_at: Optional[datetime] 
    result_count: int
    quality_job_count: int
    error_message: Optional[str]
    csv_filename: Optional[str]  # Generated CSV filename for download
    created_at: datetime

@dataclass
class CoachNotification:
    id: int
    coach_username: str
    message: str
    type: str  # 'search_complete', 'error', 'info', 'search_submitted'
    async_job_id: Optional[int]
    is_read: bool
    created_at: datetime

class AsyncJobManager:
    def __init__(self):
        self.supabase_client = get_client()
        self.outscraper_api_key = os.getenv('OUTSCRAPER_API_KEY')
        self.google_jobs_url = "https://api.outscraper.com/google-search-jobs"
        self.indeed_jobs_url = "https://api.outscraper.com/indeed-jobs"
        
    def create_job_entry(self, coach_username: str, job_type: str, search_params: Dict) -> AsyncJob:
        """Create new async job entry in database"""
        if not self.supabase_client:
            raise Exception("Supabase client not available")
            
        job_data = {
            'coach_username': coach_username,
            'job_type': job_type,
            'search_params': search_params,
            'status': 'pending',
            'result_count': 0,
            'quality_job_count': 0,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = self.supabase_client.table('async_job_queue').insert(job_data).execute()
        if result.data and len(result.data) > 0:
            job_record = result.data[0]
            return AsyncJob(
                id=job_record['id'],
                scheduled_search_id=job_record.get('scheduled_search_id'),
                coach_username=job_record['coach_username'],
                job_type=job_record['job_type'],
                request_id=job_record.get('request_id'),
                status=job_record['status'],
                search_params=job_record['search_params'],
                submitted_at=job_record.get('submitted_at'),
                completed_at=job_record.get('completed_at'),
                result_count=job_record['result_count'],
                quality_job_count=job_record['quality_job_count'],
                error_message=job_record.get('error_message'),
                csv_filename=job_record.get('csv_filename'),
                created_at=datetime.fromisoformat(job_record['created_at'].replace('Z', '+00:00'))
            )
        else:
            raise Exception("Failed to create job entry")
    
    def update_job(self, job_id: int, updates: Dict) -> bool:
        """Update job status and metadata"""
        if not self.supabase_client:
            return False
            
        try:
            # Some PostgREST setups don't return updated rows by default; treat no-exception as success.
            self.supabase_client.table('async_job_queue').update(updates).eq('id', job_id).execute()
            return True
        except Exception as e:
            print(f"Error updating job {job_id}: {e}")
            return False
    
    def delete_job(self, job_id: int) -> bool:
        """Delete a job from the queue"""
        if not self.supabase_client:
            return False
            
        try:
            self.supabase_client.table('async_job_queue').delete().eq('id', job_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting job {job_id}: {e}")
            return False
    
    def submit_google_search(self, search_params: Dict, coach_username: str) -> AsyncJob:
        """Submit async Google Jobs search - ALWAYS fresh"""
        # Create job queue entry
        job = self.create_job_entry(coach_username, 'google_jobs', search_params)
        
        try:
            # Handle comma-separated search terms
            search_terms_raw = search_params['search_terms']
            location = search_params['location']
            
            # Split search terms by comma and clean them
            search_terms_list = [term.strip() for term in search_terms_raw.split(',') if term.strip()]
            
            # Use the first search term for the primary query (Outscraper async only supports single query)
            # TODO: Future enhancement could submit multiple async jobs for each term
            primary_term = search_terms_list[0] if search_terms_list else search_terms_raw
            
            # Submit to Outscraper with async=true and webhook
            headers = {'X-API-KEY': self.outscraper_api_key}
            params = {
                'query': f"{primary_term} {location}",
                'limit': search_params.get('limit', 500),
                'async': 'true',  # Key parameter for background processing
                'webhook': os.getenv('OUTSCRAPER_WEBHOOK_URL')  # Webhook for completion notifications
            }
            
            # Remove webhook if not configured
            if not params['webhook']:
                del params['webhook']
            
            response = requests.get(self.google_jobs_url, params=params, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Outscraper returns 'id' field for async requests
            request_id = result.get('request_id') or result.get('id')
            if request_id:
                # Update job with request_id
                self.update_job(job.id, {
                    'request_id': request_id,
                    'status': 'submitted',
                    'submitted_at': datetime.now(timezone.utc).isoformat()
                })
                
                # Create notification for coach
                self.notify_coach(
                    coach_username,
                    f"🔄 Google Jobs search submitted for {search_params['location']}! Check back in 2-3 minutes.",
                    'search_submitted',
                    job.id
                )
                
                # Update the job object for return
                job.request_id = request_id
                job.status = 'submitted'
                job.submitted_at = datetime.now(timezone.utc)
                
                return job
            else:
                raise Exception(f"No request_id/id in response: {result}")
                
        except Exception as e:
            # Update job with error
            self.update_job(job.id, {
                'status': 'failed',
                'error_message': str(e),
                'completed_at': datetime.now(timezone.utc).isoformat()
            })
            
            # Notify coach of error
            self.notify_coach(
                coach_username,
                f"❌ Google Jobs search failed: {str(e)}",
                'error',
                job.id
            )
            
            raise e
    
    def submit_indeed_search(self, search_params: Dict, coach_username: str) -> AsyncJob:
        """Submit async Indeed Jobs search via Outscraper"""
        # Create job queue entry
        job = self.create_job_entry(coach_username, 'indeed_jobs', search_params)
        
        try:
            # Submit to Outscraper Indeed API with async=true and webhook
            headers = {'X-API-KEY': self.outscraper_api_key}
            params = {
                'query': search_params['search_terms'],
                'location': search_params['location'],
                'limit': search_params.get('limit', 500),
                'async': 'true',  # Key parameter for background processing
                'webhook': os.getenv('OUTSCRAPER_WEBHOOK_URL')  # Webhook for completion notifications
            }
            
            # Remove webhook if not configured
            if not params['webhook']:
                del params['webhook']
            
            response = requests.get(self.indeed_jobs_url, params=params, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Outscraper returns 'id' field for async requests
            request_id = result.get('request_id') or result.get('id')
            if request_id:
                # Update job with request_id
                self.update_job(job.id, {
                    'request_id': request_id,
                    'status': 'submitted',
                    'submitted_at': datetime.now(timezone.utc).isoformat()
                })
                
                # Create notification for coach
                self.notify_coach(
                    coach_username,
                    f"🔄 Indeed Jobs search submitted for {search_params['location']}! Check back in 2-3 minutes.",
                    'search_submitted',
                    job.id
                )
                
                # Update the job object for return
                job.request_id = request_id
                job.status = 'submitted'
                job.submitted_at = datetime.now(timezone.utc)
                
                return job
            else:
                raise Exception(f"No request_id/id in response: {result}")
                
        except Exception as e:
            # Update job with error
            self.update_job(job.id, {
                'status': 'failed',
                'error_message': str(e),
                'completed_at': datetime.now(timezone.utc).isoformat()
            })
            
            # Notify coach of error
            self.notify_coach(
                coach_username,
                f"❌ Indeed Jobs search failed: {str(e)}",
                'error',
                job.id
            )
            
            raise e
    
    def check_job_status(self, job_id: int) -> Optional[AsyncJob]:
        """Check status of async job"""
        if not self.supabase_client:
            return None
            
        try:
            result = self.supabase_client.table('async_job_queue').select('*').eq('id', job_id).execute()
            if result.data and len(result.data) > 0:
                job_record = result.data[0]
                return AsyncJob(
                    id=job_record['id'],
                    scheduled_search_id=job_record.get('scheduled_search_id'),
                    coach_username=job_record['coach_username'],
                    job_type=job_record['job_type'],
                    request_id=job_record.get('request_id'),
                    status=job_record['status'],
                    search_params=job_record['search_params'],
                    submitted_at=datetime.fromisoformat(job_record['submitted_at'].replace('Z', '+00:00')) if job_record.get('submitted_at') else None,
                    completed_at=datetime.fromisoformat(job_record['completed_at'].replace('Z', '+00:00')) if job_record.get('completed_at') else None,
                    result_count=job_record['result_count'],
                    quality_job_count=job_record['quality_job_count'],
                    error_message=job_record.get('error_message'),
                    csv_filename=job_record.get('csv_filename'),
                    created_at=datetime.fromisoformat(job_record['created_at'].replace('Z', '+00:00'))
                )
        except Exception as e:
            print(f"Error checking job {job_id}: {e}")
            return None
    
    def get_async_results(self, request_id: str) -> Optional[Dict]:
        """Poll for async job results from Outscraper"""
        try:
            headers = {'X-API-KEY': self.outscraper_api_key}
            url = f"https://api.outscraper.com/requests/{request_id}"
            print(f"🔍 Polling Outscraper API: {url}")
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            print(f"📊 Outscraper response status: {result.get('status', 'unknown')}")
            
            # Check if the job is completed
            if result.get('status') == 'Success' and result.get('data'):
                print(f"✅ Job {request_id} completed with {len(result.get('data', []))} results")
                return result
            elif result.get('status') in ['In Progress', 'Pending']:
                print(f"⏳ Job {request_id} still processing...")
                return None
            elif result.get('status') == 'Error':
                print(f"❌ Job {request_id} failed with error: {result.get('error', 'Unknown error')}")
                return result  # Return the error result so it can be handled
            else:
                print(f"🤔 Unexpected status for job {request_id}: {result.get('status')}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout polling for {request_id}")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"🌐 HTTP error polling for {request_id}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error getting async results for {request_id}: {e}")
            return None
    
    def retrieve_completed_async_job(self, job_id: int) -> Dict:
        """Retrieve raw results from Outscraper and save raw CSV; update status to 'retrieved'.
        Returns a dict with keys: {'ready': bool, 'rows': int, 'message': str, 'raw_csv': str or ''}
        """
        job = self.check_job_status(job_id)
        if not job or not job.request_id:
            return {'ready': False, 'rows': 0, 'message': 'Invalid job or missing request_id', 'raw_csv': ''}

        res = self.get_async_results(job.request_id)
        if not res:
            return {'ready': False, 'rows': 0, 'message': 'Batch not ready yet', 'raw_csv': ''}
        if res.get('status') == 'Error':
            self.update_job(job_id, {
                'status': 'failed',
                'error_message': f"Outscraper error: {res.get('error','Unknown')}",
                'completed_at': datetime.now(timezone.utc).isoformat()
            })
            return {'ready': False, 'rows': 0, 'message': 'Outscraper reported error', 'raw_csv': ''}

        # Flatten raw results list
        try:
            all_jobs = []
            for block in res.get('data', []):
                if isinstance(block, list):
                    all_jobs.extend(block)
                elif isinstance(block, dict):
                    all_jobs.append(block)
            # Minimal flatten to CSV-friendly dataframe
            rows = []
            for j in all_jobs:
                if not isinstance(j, dict):
                    continue
                det = j.get('detected_extensions', {}) if isinstance(j.get('detected_extensions'), dict) else {}
                apply_url = ''
                try:
                    ao = j.get('apply_options', [])
                    if ao and isinstance(ao, list) and isinstance(ao[0], dict):
                        apply_url = ao[0].get('link', '')
                except Exception:
                    pass
                rows.append({
                    'title': j.get('title', ''),
                    'company_name': j.get('company_name', ''),
                    'location': j.get('location', ''),
                    'link': j.get('link', ''),
                    'apply_url': apply_url,
                    'description': j.get('description', ''),
                    'salary': j.get('salary', ''),
                    'posted_at': det.get('posted_at', '')
                })
            import pandas as pd
            raw_df = pd.DataFrame(rows)
            os.makedirs('data/async_batches', exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            raw_filename = f"{job.id}_raw_{ts}.csv"
            raw_path = os.path.join('data/async_batches', raw_filename)
            raw_df.to_csv(raw_path, index=False, encoding='utf-8')

            # Update job as retrieved
            self.update_job(job_id, {
                'status': 'retrieved',
                'result_count': len(raw_df),
                'completed_at': datetime.now(timezone.utc).isoformat()
            })
            return {'ready': True, 'rows': len(raw_df), 'message': 'Retrieved', 'raw_csv': raw_filename}
        except Exception as e:
            print(f"Raw retrieve failed: {e}")
            return {'ready': False, 'rows': 0, 'message': str(e), 'raw_csv': ''}

    def process_completed_async_job(self, job_id: int):
        """Process an async job (Google or Indeed) already retrieved or directly if Outscraper result is ready.
        Generates full DF CSV and Parquet and updates status to 'processed'.
        """
        job = self.check_job_status(job_id)
        if not job or not job.request_id:
            return
            
        # Get results from Outscraper
        results = self.get_async_results(job.request_id)
        if not results:
            # Not ready — keep status as is
            return
            
        # Handle error status from Outscraper
        if results.get('status') == 'Error':
            error_msg = results.get('error', 'Unknown error from Outscraper')
            self.update_job(job_id, {
                'status': 'failed',
                'error_message': f'Outscraper error: {error_msg}',
                'completed_at': datetime.now(timezone.utc).isoformat()
            })
            
            job_type_display = "Google Jobs" if job.job_type == 'google_jobs' else "Indeed Jobs"
            self.notify_coach(
                job.coach_username,
                f"❌ {job_type_display} search failed: {error_msg}",
                'error',
                job_id
            )
            return
            
        if results.get('status') == 'Success' and results.get('data'):
            try:
                # Process results based on job type
                if job.job_type == 'google_jobs':
                    jobs_df = self.process_google_results(results['data'], job.search_params)
                elif job.job_type == 'indeed_jobs':
                    jobs_df = self.process_indeed_results(results['data'], job.search_params)
                else:
                    raise Exception(f"Unknown job type: {job.job_type}")
                
                # If no jobs, mark as processed with zero counts
                if len(jobs_df) == 0:
                    self.update_job(job_id, {
                        'status': 'processed',
                        'result_count': 0,
                        'quality_job_count': 0,
                        'completed_at': datetime.now(timezone.utc).isoformat()
                    })
                    return
                
                # Continue with the rest of the processing...
                # Store jobs, run classification, etc.
                self._complete_job_processing(job_id, job, jobs_df)
                
            except Exception as e:
                print(f"❌ Error processing async job {job_id}: {e}")
                self.update_job(job_id, {
                    'status': 'failed',
                    'error_message': str(e),
                    'completed_at': datetime.now(timezone.utc).isoformat()
                })
                
                job_type_display = "Google Jobs" if job.job_type == 'google_jobs' else "Indeed Jobs"
                self.notify_coach(
                    job.coach_username,
                    f"❌ {job_type_display} processing failed: {str(e)}",
                    'error',
                    job_id
                )
    
    def _complete_job_processing(self, job_id: int, job: AsyncJob, jobs_df: pd.DataFrame):
        """Complete the processing of a job after results have been converted to DataFrame"""
        try:
            # 1. Store ALL scraped jobs in Supabase
            source = 'google' if job.job_type == 'google_jobs' else 'indeed'
            self.store_all_jobs_supabase(jobs_df, source=source, job=job)
            
            # 2. Import classifier and run AI classification (map to expected fields)
            try:
                from jobs_schema import generate_job_id
                from job_classifier import JobClassifier
                classifier = JobClassifier()
                df_cls = pd.DataFrame()
                df_cls['job_title'] = jobs_df.get('source.title', jobs_df.get('title', ''))
                df_cls['company'] = jobs_df.get('source.company', jobs_df.get('company', ''))
                df_cls['location'] = jobs_df.get('source.location', jobs_df.get('location', ''))
                df_cls['job_description'] = jobs_df.get('source.description', jobs_df.get('description', ''))
                df_cls['job_id'] = df_cls.apply(lambda r: generate_job_id(str(r['company']), str(r['location']), str(r['job_title'])), axis=1)
                # Classify and map outputs into ai.* on a copy of jobs_df
                classified_df = classifier.classify_jobs(df_cls.copy())
                # Merge ai.* columns onto the original jobs_df by order (rows preserved)
                jobs_df = jobs_df.copy()
                jobs_df['ai.match'] = classified_df['match']
                jobs_df['ai.reason'] = classified_df['reason']
                jobs_df['ai.summary'] = classified_df['summary']
                jobs_df['ai.route_type'] = classified_df['route_type']
                jobs_df['ai.fair_chance'] = classified_df['fair_chance']
                jobs_df['ai.endorsements'] = classified_df['endorsements']
            except Exception as e:
                print(f"Classification failed: {e}")
                jobs_df = jobs_df.copy()
                jobs_df['ai.match'] = 'error'
                jobs_df['ai.summary'] = 'Classification failed'
            
            # 3. Store in memory database for future searches
            try:
                from job_memory_db import JobMemoryDB
                memory_db = JobMemoryDB()
                # Build minimal canonical frame for storage
                canon = pd.DataFrame()
                # Use same job_id generation
                canon['id.job'] = df_cls['job_id'] if 'df_cls' in locals() and 'job_id' in df_cls.columns else jobs_df.index.map(str)
                canon['source.title'] = jobs_df.get('source.title', '')
                canon['source.company'] = jobs_df.get('source.company', '')
                # Normalize location to canonical raw
                canon['source.location_raw'] = jobs_df.get('source.location', jobs_df.get('location', ''))
                canon['source.description_raw'] = jobs_df.get('source.description', jobs_df.get('description', ''))
                canon['source.indeed_url'] = jobs_df.get('source.indeed_url', '')
                canon['source.apply_url'] = jobs_df.get('source.apply_url', jobs_df.get('source.google_url', ''))
                canon['ai.match'] = jobs_df.get('ai.match', '')
                canon['ai.reason'] = jobs_df.get('ai.reason', '')
                canon['ai.summary'] = jobs_df.get('ai.summary', '')
                canon['ai.route_type'] = jobs_df.get('ai.route_type', '')
                canon['ai.fair_chance'] = jobs_df.get('ai.fair_chance', '')
                canon['ai.endorsements'] = jobs_df.get('ai.endorsements', '')
                memory_db.store_classifications(canon)
            except Exception as e:
                print(f"Memory DB insert failed: {e}")
            
            # 4. Generate tracked URLs for quality jobs
            print("🔗 Generating tracked URLs for quality jobs...")
            try:
                from link_tracker import LinkTracker
                tracker = LinkTracker()
                
                if tracker.is_available:
                    # Generate tracked URLs for all quality jobs
                    quality_mask = jobs_df.get('ai.match', 'error').isin(['good', 'so-so'])
                    quality_indices = jobs_df[quality_mask].index
                    
                    for idx in quality_indices:
                        # Get the original URL (consolidated from apply_url, indeed_url, etc.)
                        original_url = jobs_df.loc[idx, 'source.apply_url'] if 'source.apply_url' in jobs_df.columns else ''
                        if not original_url:
                            original_url = jobs_df.loc[idx, 'source.indeed_url'] if 'source.indeed_url' in jobs_df.columns else ''
                        if not original_url:
                            original_url = jobs_df.loc[idx, 'source.google_url'] if 'source.google_url' in jobs_df.columns else ''
                        
                        if original_url and len(original_url.strip()) > 10:
                            # Create job title for the link
                            job_title = jobs_df.loc[idx, 'source.title'] if 'source.title' in jobs_df.columns else f"Job {idx}"
                            job_location = jobs_df.loc[idx, 'source.location'] if 'source.location' in jobs_df.columns else 'Unknown'
                            
                            # Generate tracking tags
                            tags = [
                                f"coach:{job.coach_username}",
                                f"source:async_{job.job_type}",
                                f"location:{job_location[:20]}"  # Truncate long locations
                            ]
                            
                            try:
                                tracked_url = tracker.create_short_link(
                                    original_url,
                                    title=f"{job_title} - {job_location}",
                                    tags=tags
                                )
                                
                                if tracked_url and tracked_url != original_url:
                                    # Add tracked_url column if it doesn't exist
                                    if 'meta.tracked_url' not in jobs_df.columns:
                                        jobs_df['meta.tracked_url'] = ''
                                    jobs_df.loc[idx, 'meta.tracked_url'] = tracked_url
                                    
                            except Exception as e:
                                print(f"Failed to create tracked URL for job {idx}: {e}")
                                
                    print(f"✅ Generated tracked URLs for {len(quality_indices)} quality jobs")
                else:
                    print("⚠️ LinkTracker not available, skipping URL generation")
            except Exception as e:
                print(f"❌ Link generation failed: {e}")
            
            # 5. Extract quality jobs (good/so-so) for Airtable  
            quality_jobs = jobs_df[jobs_df.get('ai.match', 'error').isin(['good', 'so-so'])]
            
            airtable_count = 0
            if len(quality_jobs) > 0:
                # 6. Sync quality jobs to Airtable (fresh jobs only)
                try:
                    from airtable_uploader import sync_jobs_to_airtable
                    airtable_count = sync_jobs_to_airtable(quality_jobs, job.coach_username)
                except Exception as e:
                    print(f"Airtable sync failed: {e}")
            
            # 7. Generate CSV file for download (ALL rows)
            csv_filename = None
            try:
                # Use jobs_df (source.* + ai.*) so CSV includes all rows
                csv_filename = self._generate_csv_file(job_id, job, jobs_df, quality_jobs)
                print(f"✅ CSV generated: {csv_filename}")
            except Exception as e:
                print(f"CSV generation failed: {e}")
            
            # 8. Generate Parquet file containing ALL classified rows
            try:
                import os
                pq_dir = "data/async_batches"
                os.makedirs(pq_dir, exist_ok=True)
                pq_path = os.path.join(pq_dir, f"{job.id}_results.parquet")
                # Save the enriched jobs_df (with ai.*) to Parquet
                jobs_df.to_parquet(pq_path, index=False)
                print(f"📦 Parquet saved: {pq_path}")
            except Exception as e:
                print(f"Parquet generation failed: {e}")
            
            # Update job status
            job_update = {
                'status': 'processed',
                'result_count': len(jobs_df),
                'quality_job_count': len(quality_jobs),
                'completed_at': datetime.now(timezone.utc).isoformat()
            }
            # Avoid updating csv_filename if the column doesn't exist in the Supabase schema
            
            self.update_job(job_id, job_update)
            
            # Notify coach
            location = job.search_params.get('location', 'Unknown')
            job_type_display = "Google Jobs" if job.job_type == 'google_jobs' else "Indeed Jobs"
            self.notify_coach(
                job.coach_username,
                f"✅ {job_type_display} search for {location} complete! {len(quality_jobs)} quality jobs ready. Search any location to see them!",
                'search_complete',
                job_id
            )
            
        except Exception as e:
            self.update_job(job_id, {
                'status': 'failed',
                'error_message': f'Processing failed: {str(e)}',
                'completed_at': datetime.now(timezone.utc).isoformat()
            })
            
            job_type_display = "Google Jobs" if job.job_type == 'google_jobs' else "Indeed Jobs"
            self.notify_coach(
                job.coach_username,
                f"❌ {job_type_display} search processing failed: {str(e)}",
                'error',
                job_id
            )
    
    def _generate_csv_file(self, job_id: int, job: AsyncJob, all_rows_df: pd.DataFrame, quality_jobs: pd.DataFrame) -> str:
        """Generate CSV file for async batch download (ALL jobs, not just quality).
        all_rows_df should be the full jobs_df with source.* and ai.* columns.
        """
        import os
        
        # Create CSV directory if it doesn't exist
        csv_dir = "data/async_batches"
        os.makedirs(csv_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        location = job.search_params.get('location', 'Unknown').replace(' ', '_').replace(',', '')
        job_type = 'google' if job.job_type == 'google_jobs' else 'indeed'
        csv_filename = f"async_{job_type}_{location}_{timestamp}_job{job_id}.csv"
        csv_path = os.path.join(csv_dir, csv_filename)
        
        # Prepare data for CSV - include ALL jobs to validate pipeline output
        # Select key columns for download
        # Favor explicit apply URLs for Google/Indeed, fall back gracefully
        url_column = 'source.apply_url' if 'source.apply_url' in all_rows_df.columns else (
            'source.google_url' if 'source.google_url' in all_rows_df.columns else (
                'source.indeed_url' if 'source.indeed_url' in all_rows_df.columns else None
            )
        )
        csv_columns = [
            'source.title', 'source.company', 'source.location', 'source.salary',
            'ai.match', 'ai.summary', 'ai.route_type',
        ] + ([url_column] if url_column else []) + ['source.posted_date']

        # Filter to available columns
        available_columns = [col for col in csv_columns if col in all_rows_df.columns]
        csv_data = all_rows_df[available_columns].copy() if available_columns else all_rows_df.copy()

        # Rename columns for readability where present
        column_rename = {
            'source.title': 'Job Title',
            'source.company': 'Company',
            'source.location': 'Location', 
            'source.salary': 'Salary',
            'ai.match': 'Match Quality',
            'ai.summary': 'AI Summary',
            'ai.route_type': 'Route Type',
            'source.apply_url': 'Apply URL',
            'source.google_url': 'Apply URL',
            'source.indeed_url': 'Apply URL',
            'source.posted_date': 'Posted Date'
        }
        rename_dict = {k: v for k, v in column_rename.items() if k in csv_data.columns}
        if rename_dict:
            csv_data = csv_data.rename(columns=rename_dict)
        
        # Save to CSV
        csv_data.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"📄 CSV saved: {csv_path} ({len(csv_data)} rows)")
        
        return csv_filename
    
    def process_completed_google_job(self, job_id: int):
        """Process completed async Google job with proper data routing - DEPRECATED: Use process_completed_async_job"""
        job = self.check_job_status(job_id)
        if not job or not job.request_id:
            return
            
        # Get results from Outscraper
        results = self.get_async_results(job.request_id)
        if not results:
            self.update_job(job_id, {
                'status': 'failed',
                'error_message': 'Failed to retrieve results from Outscraper',
                'completed_at': datetime.now(timezone.utc).isoformat()
            })
            return
            
        # Handle error status from Outscraper
        if results.get('status') == 'Error':
            error_msg = results.get('error', 'Unknown error from Outscraper')
            self.update_job(job_id, {
                'status': 'failed',
                'error_message': f'Outscraper error: {error_msg}',
                'completed_at': datetime.now(timezone.utc).isoformat()
            })
            
            self.notify_coach(
                job.coach_username,
                f"❌ Google search failed: {error_msg}",
                'error',
                job_id
            )
            return
            
        if results.get('status') == 'Success' and results.get('data'):
            try:
                # Process results into DataFrame
                jobs_df = self.process_google_results(results['data'], job.search_params)
                
                # Handle case where no jobs were found
                if len(jobs_df) == 0:
                    print("📭 No jobs found in Google search results")
                    self.update_job(job_id, {
                        'status': 'completed',
                        'result_count': 0,
                        'quality_job_count': 0,
                        'completed_at': datetime.now(timezone.utc).isoformat()
                    })
                    
                    self.notify_coach(
                        job.coach_username,
                        f"🔍 Google search for {job.search_params.get('location', 'Unknown')} completed but found no jobs. Try different search terms or location.",
                        'search_complete',
                        job_id
                    )
                    return
                
                # 1. Store ALL scraped jobs in Supabase
                self.store_all_jobs_supabase(jobs_df, source='google', job=job)
                
                # 2. Import classifier and run AI classification
                try:
                    from job_classifier import JobClassifier
                    classifier = JobClassifier()
                    classified_df = classifier.classify_batch(jobs_df)
                except Exception as e:
                    print(f"Classification failed: {e}")
                    classified_df = jobs_df.copy()
                    classified_df['ai.match'] = 'error'
                    classified_df['ai.summary'] = 'Classification failed'
                
                # 3. Store in memory database for future searches
                try:
                    from job_memory_db import JobMemoryDB
                    memory_db = JobMemoryDB()
                    memory_db.insert_jobs(classified_df)
                except Exception as e:
                    print(f"Memory DB insert failed: {e}")
                
                # 4. Extract quality jobs (good/so-so) for Airtable
                quality_jobs = classified_df[
                    classified_df.get('ai.match', 'error').isin(['good', 'so-so'])
                ]
                
                airtable_count = 0
                if len(quality_jobs) > 0:
                    # 5. Sync quality jobs to Airtable (fresh jobs only)
                    try:
                        from airtable_uploader import sync_jobs_to_airtable
                        airtable_count = sync_jobs_to_airtable(quality_jobs, job.coach_username)
                    except Exception as e:
                        print(f"Airtable sync failed: {e}")
                
                # Update job status
                self.update_job(job_id, {
                    'status': 'completed',
                    'result_count': len(jobs_df),
                    'quality_job_count': len(quality_jobs),
                    'completed_at': datetime.now(timezone.utc).isoformat()
                })
                
                # Notify coach
                location = job.search_params.get('location', 'Unknown')
                self.notify_coach(
                    job.coach_username,
                    f"✅ Google search for {location} complete! {len(quality_jobs)} quality jobs ready. Search any location to see them!",
                    'search_complete',
                    job_id
                )
                
            except Exception as e:
                self.update_job(job_id, {
                    'status': 'failed',
                    'error_message': f'Processing failed: {str(e)}',
                    'completed_at': datetime.now(timezone.utc).isoformat()
                })
                
                self.notify_coach(
                    job.coach_username,
                    f"❌ Google search processing failed: {str(e)}",
                    'error',
                    job_id
                )
    
    def process_google_results(self, raw_data: List, search_params: Dict) -> pd.DataFrame:
        """Convert raw Google Jobs API results to canonical DataFrame
        
        Google Jobs API returns: [[job1, job2, ...]] or [[]] for empty results
        We need to flatten this structure and handle empty results gracefully.
        """
        jobs = []
        current_time = datetime.now(timezone.utc)
        
        # Flatten nested list structure from Google Jobs API
        all_jobs = []
        for query_results in raw_data:
            if isinstance(query_results, list):
                all_jobs.extend(query_results)
            elif isinstance(query_results, dict):
                all_jobs.append(query_results)
        
        print(f"📊 Processing {len(all_jobs)} Google Jobs results")
        
        for job in all_jobs:
            if not isinstance(job, dict):
                continue
                
            # Extract apply URL safely
            apply_url = ''
            try:
                apply_options = job.get('apply_options', [])
                if apply_options and isinstance(apply_options, list):
                    apply_url = apply_options[0].get('link', '') if isinstance(apply_options[0], dict) else ''
            except (IndexError, KeyError, AttributeError):
                pass
            
            job_record = {
                # Source identification
                'source.platform': 'google',
                'source.title': job.get('title', ''),
                'source.company': job.get('company_name', ''),
                'source.location': job.get('location', ''),
                'source.description': job.get('description', ''),
                'source.salary': job.get('salary', ''),
                'source.posted_date': job.get('detected_extensions', {}).get('posted_at', '') if isinstance(job.get('detected_extensions'), dict) else '',
                'source.google_url': job.get('link', ''),
                'source.apply_url': apply_url,
                
                # System metadata
                'sys.scraped_at': current_time.isoformat(),
                'sys.run_id': f"async_{current_time.strftime('%Y%m%d_%H%M%S')}",
                'sys.is_fresh_job': True,
                'sys.hash': self.generate_job_hash(job),
                
                # Search metadata
                'meta.search_terms': search_params.get('search_terms', ''),
                'meta.location': search_params.get('location', ''),
                'meta.coach': search_params.get('coach_username', ''),
            }
            jobs.append(job_record)
        
        print(f"✅ Converted {len(jobs)} jobs to canonical format")
        return pd.DataFrame(jobs)
    
    def process_indeed_results(self, raw_data: List, search_params: Dict) -> pd.DataFrame:
        """Convert raw Indeed Jobs API results to canonical DataFrame
        
        Indeed Jobs API returns: [[job1, job2, ...]] or [[]] for empty results
        Similar structure to Google but with different field names.
        """
        jobs = []
        current_time = datetime.now(timezone.utc)
        
        # Flatten nested list structure from Indeed Jobs API
        all_jobs = []
        for query_results in raw_data:
            if isinstance(query_results, list):
                all_jobs.extend(query_results)
            elif isinstance(query_results, dict):
                all_jobs.append(query_results)
        
        print(f"📊 Processing {len(all_jobs)} Indeed Jobs results")
        
        for job in all_jobs:
            if not isinstance(job, dict):
                continue
            
            job_record = {
                # Source identification
                'source.platform': 'indeed',
                'source.title': job.get('title', ''),
                'source.company': job.get('company', ''),
                'source.location': job.get('location', ''),
                'source.description': job.get('description', ''),
                'source.salary': job.get('salary', ''),
                'source.posted_date': job.get('date', ''),
                'source.url': job.get('link', ''),
                
                # System metadata  
                'sys.scraped_at': current_time.isoformat(),
                'sys.run_id': f"async_{current_time.strftime('%Y%m%d_%H%M%S')}",
                'sys.is_fresh_job': True,
                'sys.hash': self.generate_indeed_job_hash(job),
                
                # Search metadata
                'meta.search_terms': search_params.get('search_terms', ''),
                'meta.location': search_params.get('location', ''),
                'meta.coach': search_params.get('coach_username', ''),
            }
            jobs.append(job_record)
        
        print(f"✅ Converted {len(jobs)} Indeed jobs to canonical format")
        return pd.DataFrame(jobs)
    
    def generate_job_hash(self, job: Dict) -> str:
        """Generate unique hash for job deduplication (Google Jobs)"""
        import hashlib
        key_fields = [
            job.get('title', ''),
            job.get('company_name', ''),
            job.get('location', ''),
            job.get('link', '')
        ]
        combined = '|'.join(str(field) for field in key_fields)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def generate_indeed_job_hash(self, job: Dict) -> str:
        """Generate unique hash for job deduplication (Indeed Jobs)"""
        import hashlib
        key_fields = [
            job.get('title', ''),
            job.get('company', ''),  # Indeed uses 'company' not 'company_name'
            job.get('location', ''),
            job.get('link', '')
        ]
        combined = '|'.join(str(field) for field in key_fields)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def store_all_jobs_supabase(self, jobs_df: pd.DataFrame, source: str, job: AsyncJob):
        """Store ALL scraped jobs in Supabase for comprehensive tracking"""
        if not self.supabase_client:
            return
            
        records = []
        for _, job_row in jobs_df.iterrows():
            records.append({
                'job_hash': job_row.get('sys.hash'),
                'source': source,
                'scraped_at': job_row.get('sys.scraped_at'),
                'search_params': {
                    'terms': job_row.get('meta.search_terms'),
                    'location': job_row.get('meta.location'),
                    'coach': job_row.get('meta.coach')
                },
                'job_data': job_row.to_dict(),
                'ai_classification': {
                    'match': job_row.get('ai.match'),
                    'summary': job_row.get('ai.summary'),
                    'route_type': job_row.get('ai.route_type')
                }
            })
        
        try:
            # Bulk insert to Supabase (upsert to handle duplicates)
            self.supabase_client.table('all_scraped_jobs').upsert(
                records, 
                on_conflict='job_hash'
            ).execute()
        except Exception as e:
            print(f"Failed to store jobs in Supabase: {e}")
    
    def notify_coach(self, coach_username: str, message: str, notification_type: str, job_id: Optional[int] = None):
        """Create notification for coach"""
        if not self.supabase_client:
            return
            
        notification = {
            'coach_username': coach_username,
            'message': message,
            'type': notification_type,
            'async_job_id': job_id,
            'is_read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            self.supabase_client.table('coach_notifications').insert(notification).execute()
        except Exception as e:
            print(f"Failed to create notification: {e}")
    
    def get_coach_notifications(self, coach_username: str, limit: int = 10) -> List[CoachNotification]:
        """Get recent notifications for coach"""
        if not self.supabase_client:
            return []
            
        try:
            result = self.supabase_client.table('coach_notifications')\
                .select('*')\
                .eq('coach_username', coach_username)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
                
            notifications = []
            for record in result.data or []:
                notifications.append(CoachNotification(
                    id=record['id'],
                    coach_username=record['coach_username'],
                    message=record['message'],
                    type=record['type'],
                    async_job_id=record.get('async_job_id'),
                    is_read=record['is_read'],
                    created_at=datetime.fromisoformat(record['created_at'].replace('Z', '+00:00'))
                ))
            
            return notifications
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []
    
    def mark_notification_read(self, notification_id: int) -> bool:
        """Mark notification as read"""
        if not self.supabase_client:
            return False
            
        try:
            result = self.supabase_client.table('coach_notifications')\
                .update({'is_read': True})\
                .eq('id', notification_id)\
                .execute()
            return result.data is not None and len(result.data) > 0
        except Exception as e:
            print(f"Error marking notification read: {e}")
            return False
    
    def get_pending_jobs(self, coach_username: Optional[str] = None) -> List[AsyncJob]:
        """Get pending/processing async jobs"""
        if not self.supabase_client:
            return []
            
        try:
            query = self.supabase_client.table('async_job_queue')\
                .select('*')\
                .in_('status', ['pending', 'submitted', 'processing'])
                
            if coach_username:
                query = query.eq('coach_username', coach_username)
                
            # Server-side order by created_at desc for a stable starting set
            result = query.order('created_at', desc=True).execute()
            
            jobs = []
            for record in result.data or []:
                jobs.append(AsyncJob(
                    id=record['id'],
                    scheduled_search_id=record.get('scheduled_search_id'),
                    coach_username=record['coach_username'],
                    job_type=record['job_type'],
                    request_id=record.get('request_id'),
                    status=record['status'],
                    search_params=record['search_params'],
                    submitted_at=datetime.fromisoformat(record['submitted_at'].replace('Z', '+00:00')) if record.get('submitted_at') else None,
                    completed_at=datetime.fromisoformat(record['completed_at'].replace('Z', '+00:00')) if record.get('completed_at') else None,
                    result_count=record['result_count'],
                    quality_job_count=record['quality_job_count'],
                    error_message=record.get('error_message'),
                    csv_filename=record.get('csv_filename'),
                    created_at=datetime.fromisoformat(record['created_at'].replace('Z', '+00:00'))
                ))
            
            # Client-side stable ordering: processing -> submitted -> pending,
            # then by submitted_at (oldest first), then by created_at (oldest first)
            def sort_key(j: AsyncJob):
                status_rank = {'processing': 0, 'submitted': 1, 'pending': 2}
                r = status_rank.get(getattr(j, 'status', ''), 3)
                sa = j.submitted_at or j.created_at
                ca = j.created_at
                return (r, sa or ca, ca)
            jobs.sort(key=sort_key)
            return jobs
        except Exception as e:
            print(f"Error getting pending jobs: {e}")
            return []
    
    def get_completed_jobs(self, coach_username: Optional[str] = None, limit: int = 50) -> List[AsyncJob]:
        """Get processed/complete async jobs"""
        if not self.supabase_client:
            return []
            
        try:
            query = self.supabase_client.table('async_job_queue')\
                .select('*')\
                .in_('status', ['processed','completed'])
                
            if coach_username:
                query = query.eq('coach_username', coach_username)
                
            # Server-side by completed_at desc
            result = query.order('completed_at', desc=True).limit(limit).execute()
            
            jobs = []
            for record in result.data or []:
                jobs.append(AsyncJob(
                    id=record['id'],
                    scheduled_search_id=record.get('scheduled_search_id'),
                    coach_username=record['coach_username'],
                    job_type=record['job_type'],
                    request_id=record.get('request_id'),
                    status=record['status'],
                    search_params=record['search_params'],
                    submitted_at=datetime.fromisoformat(record['submitted_at'].replace('Z', '+00:00')) if record.get('submitted_at') else None,
                    completed_at=datetime.fromisoformat(record['completed_at'].replace('Z', '+00:00')) if record.get('completed_at') else None,
                    result_count=record['result_count'],
                    quality_job_count=record['quality_job_count'],
                    error_message=record.get('error_message'),
                    csv_filename=record.get('csv_filename'),
                    created_at=datetime.fromisoformat(record['created_at'].replace('Z', '+00:00'))
                ))
            
            # Tie-breaker client-side by id desc to keep newest first deterministically
            jobs.sort(key=lambda j: (j.completed_at or j.created_at, j.id), reverse=True)
            return jobs
        except Exception as e:
            print(f"Error getting completed jobs: {e}")
            return []

    def get_retrieved_jobs(self, coach_username: Optional[str] = None, limit: int = 50) -> List[AsyncJob]:
        """Get retrieved async jobs (raw results saved, not processed)"""
        if not self.supabase_client:
            return []
        try:
            query = self.supabase_client.table('async_job_queue')\
                .select('*')\
                .eq('status', 'retrieved')
            if coach_username:
                query = query.eq('coach_username', coach_username)
            result = query.order('completed_at', desc=True).limit(limit).execute()
            jobs: List[AsyncJob] = []
            for record in result.data or []:
                jobs.append(AsyncJob(
                    id=record['id'],
                    scheduled_search_id=record.get('scheduled_search_id'),
                    coach_username=record['coach_username'],
                    job_type=record['job_type'],
                    request_id=record.get('request_id'),
                    status=record['status'],
                    search_params=record['search_params'],
                    submitted_at=datetime.fromisoformat(record['submitted_at'].replace('Z', '+00:00')) if record.get('submitted_at') else None,
                    completed_at=datetime.fromisoformat(record['completed_at'].replace('Z', '+00:00')) if record.get('completed_at') else None,
                    result_count=record['result_count'],
                    quality_job_count=record['quality_job_count'],
                    error_message=record.get('error_message'),
                    csv_filename=record.get('csv_filename'),
                    created_at=datetime.fromisoformat(record['created_at'].replace('Z', '+00:00'))
                ))
            return jobs
        except Exception as e:
            print(f"Error getting retrieved jobs: {e}")
            return []
    
    def get_failed_jobs(self, coach_username: Optional[str] = None, limit: int = 50) -> List[AsyncJob]:
        """Get failed async jobs"""
        if not self.supabase_client:
            return []
            
        try:
            query = self.supabase_client.table('async_job_queue')\
                .select('*')\
                .eq('status', 'failed')
                
            if coach_username:
                query = query.eq('coach_username', coach_username)
                
            result = query.order('created_at', desc=True).limit(limit).execute()
            
            jobs = []
            for record in result.data or []:
                jobs.append(AsyncJob(
                    id=record['id'],
                    scheduled_search_id=record.get('scheduled_search_id'),
                    coach_username=record['coach_username'],
                    job_type=record['job_type'],
                    request_id=record.get('request_id'),
                    status=record['status'],
                    search_params=record['search_params'],
                    submitted_at=datetime.fromisoformat(record['submitted_at'].replace('Z', '+00:00')) if record.get('submitted_at') else None,
                    completed_at=datetime.fromisoformat(record['completed_at'].replace('Z', '+00:00')) if record.get('completed_at') else None,
                    result_count=record['result_count'],
                    quality_job_count=record['quality_job_count'],
                    error_message=record.get('error_message'),
                    csv_filename=record.get('csv_filename'),
                    created_at=datetime.fromisoformat(record['created_at'].replace('Z', '+00:00'))
                ))
            
            return jobs
        except Exception as e:
            print(f"Error getting failed jobs: {e}")
            return []
    
    def check_pending_google_jobs_in_market(self, location: str) -> List[AsyncJob]:
        """Check if there are pending Google Jobs searches for the same market"""
        if not self.supabase_client:
            return []
            
        try:
            # Get all pending Google Jobs
            query = self.supabase_client.table('async_job_queue')\
                .select('*')\
                .eq('job_type', 'google_jobs')\
                .in_('status', ['pending', 'submitted', 'processing'])
                
            # Start with server-side order by created_at desc
            result = query.order('created_at', desc=True).execute()
            
            # Filter by location match
            matching_jobs = []
            location_lower = location.lower().strip()
            
            for record in result.data or []:
                search_params = record.get('search_params', {})
                job_location = search_params.get('location', '').lower().strip()
                
                # Simple location matching - could be enhanced with fuzzy matching
                if location_lower in job_location or job_location in location_lower:
                    matching_jobs.append(AsyncJob(
                        id=record['id'],
                        scheduled_search_id=record.get('scheduled_search_id'),
                        coach_username=record['coach_username'],
                        job_type=record['job_type'],
                        request_id=record.get('request_id'),
                        status=record['status'],
                        search_params=record['search_params'],
                        submitted_at=datetime.fromisoformat(record['submitted_at'].replace('Z', '+00:00')) if record.get('submitted_at') else None,
                        completed_at=datetime.fromisoformat(record['completed_at'].replace('Z', '+00:00')) if record.get('completed_at') else None,
                        result_count=record['result_count'],
                        quality_job_count=record['quality_job_count'],
                        error_message=record.get('error_message'),
                        created_at=datetime.fromisoformat(record['created_at'].replace('Z', '+00:00'))
                    ))
            
            # Sort by status priority and submission time (oldest first) so the longest running appear first
            def sort_key(j: AsyncJob):
                status_rank = {'processing': 0, 'submitted': 1, 'pending': 2}
                r = status_rank.get(getattr(j, 'status', ''), 3)
                sa = j.submitted_at or j.created_at
                return (r, sa or j.created_at)
            matching_jobs.sort(key=sort_key)
            return matching_jobs
        except Exception as e:
            print(f"Error checking pending Google jobs: {e}")
            return []
