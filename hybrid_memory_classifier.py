"""
Hybrid Memory Classifier
Uses Supabase for classification memory + Airtable for final storage
Reduces Airtable API usage by 90% while maintaining multi-user access
"""
import pandas as pd
import logging
from typing import Dict, List
from job_classifier import JobClassifier
from job_memory_db import JobMemoryDB
from airtable_uploader import AirtableUploader

logger = logging.getLogger(__name__)

class HybridMemoryClassifier:
    """Enhanced job classifier with Supabase memory + Airtable final storage"""
    
    def __init__(self):
        self.ai_classifier = JobClassifier()
        self.memory_db = JobMemoryDB()
        self.airtable = None
        
    def _init_airtable(self):
        """Initialize Airtable connection if not already done (for final storage only)"""
        if self.airtable is None:
            try:
                from dotenv import load_dotenv
                load_dotenv()
                self.airtable = AirtableUploader()
            except Exception as e:
                logger.warning(f"Could not initialize Airtable connection: {e}")
                self.airtable = None
    
    def classify_with_hybrid_memory(self, df: pd.DataFrame, memory_hours: int = 168, upload_to_airtable: bool = False) -> pd.DataFrame:
        """
        Classify jobs using Supabase memory to avoid re-classifying known jobs.
        Only stores good/so-so jobs in Airtable.
        
        Args:
            df: DataFrame with jobs to classify
            memory_hours: Hours to look back for job memory (default 168 = 7 days)
            
        Returns:
            DataFrame with classifications
        """
        
        # Only process jobs that haven't been filtered out (final_status == "included")
        if 'final_status' in df.columns:
            unfiltered_df = df[df['final_status'] == "included"].copy()
            filtered_df = df[df['final_status'].str.startswith("filtered:")].copy()
        else:
            unfiltered_df = df.copy()
            filtered_df = pd.DataFrame()
        
        # Generate job IDs for memory checking
        unfiltered_df = self._ensure_job_ids(unfiltered_df)
        job_ids = unfiltered_df['job_id'].tolist()
        
        # Check Supabase memory database
        job_memory = self.memory_db.check_job_memory(job_ids, memory_hours)
        
        # Split jobs into known and new
        known_job_ids = set(job_memory.keys())
        unfiltered_df['is_known'] = unfiltered_df['job_id'].isin(known_job_ids)
        
        known_jobs_df = unfiltered_df[unfiltered_df['is_known']].copy()
        new_jobs_df = unfiltered_df[~unfiltered_df['is_known']].copy()
        
        print(f"   💰 API savings: {len(known_jobs_df)} jobs = ${len(known_jobs_df) * 0.0003:.4f}")
        
        # Process known jobs (use cached classifications)
        if len(known_jobs_df) > 0:
            known_jobs_df = self._apply_memory_classifications(known_jobs_df, job_memory)
            # Mark these jobs as from memory (don't store in Supabase again)
            known_jobs_df['is_fresh_job'] = False
        
        # Process new jobs (AI classification)
        if len(new_jobs_df) > 0:
            print(f"   🤖 Running AI classification on {len(new_jobs_df)} new jobs...")
            new_jobs_df = self.ai_classifier.classify_jobs(new_jobs_df)
            # Mark these jobs as fresh for later Supabase storage
            new_jobs_df['is_fresh_job'] = True
            
            # Note: Supabase storage now happens at end of pipeline with complete data
            # This ensures all pipeline processing (route classification, filtering, etc.) gets stored
                
            # Upload fresh quality jobs to Airtable (good/so-so only)
            if upload_to_airtable:
                quality_jobs = new_jobs_df[new_jobs_df['match'].isin(['good', 'so-so'])].copy()
                if len(quality_jobs) > 0:
                    print(f"   📤 Uploading {len(quality_jobs)} fresh quality jobs to Airtable...")
                    try:
                        from airtable_uploader import AirtableUploader
                        uploader = AirtableUploader()
                        result = uploader.upload_jobs(quality_jobs)
                        if result['success']:
                            print(f"   🚀 {result['message']}")
                        else:
                            print(f"   ❌ Airtable upload failed: {result['message']}")
                    except Exception as e:
                        print(f"   ❌ Airtable upload error: {e}")
                else:
                    print(f"   ℹ️ No fresh quality jobs to upload to Airtable")
        
        # Combine known and new jobs
        if len(known_jobs_df) > 0 and len(new_jobs_df) > 0:
            combined_df = pd.concat([known_jobs_df, new_jobs_df], ignore_index=True)
        elif len(known_jobs_df) > 0:
            combined_df = known_jobs_df
        elif len(new_jobs_df) > 0:
            combined_df = new_jobs_df
        else:
            combined_df = pd.DataFrame()
        
        # Clean up temporary columns
        combined_df = combined_df.drop(columns=['is_known'], errors='ignore')
        
        # Combine with filtered jobs to return complete dataset
        if len(filtered_df) > 0:
            final_df = pd.concat([combined_df, filtered_df], ignore_index=True)
        else:
            final_df = combined_df
        
        print(f"   🎯 Final result: {len(final_df)} total jobs")
        print(f"      • {len(new_jobs_df)} newly classified")
        print(f"      • {len(known_jobs_df)} from memory database")
        if len(filtered_df) > 0:
            print(f"      • {len(filtered_df)} filtered jobs preserved")
        
        return final_df
    
    def upload_quality_jobs_to_airtable(self, df: pd.DataFrame) -> Dict:
        """
        Upload only good and so-so jobs to Airtable (final storage)
        This reduces Airtable usage by ~70% compared to uploading all jobs
        
        Args:
            df: DataFrame with all classified jobs
            
        Returns:
            Upload results
        """
        self._init_airtable()
        
        if not self.airtable or not self.airtable.table:
            return {
                'success': False,
                'message': 'Airtable not connected - quality jobs not uploaded',
                'total_jobs': len(df),
                'uploaded_count': 0
            }
        
        # Filter for only good and so-so jobs
        quality_jobs = df[df['match'].isin(['good', 'so-so'])].copy()
        
        if len(quality_jobs) == 0:
            return {
                'success': True,
                'message': 'No quality jobs to upload to Airtable',
                'total_jobs': len(df),
                'quality_jobs': 0,
                'uploaded_count': 0
            }
        
        print(f"📤 Uploading {len(quality_jobs)} quality jobs to Airtable (filtered from {len(df)} total)")
        quality_breakdown = quality_jobs['match'].value_counts()
        print(f"   Quality breakdown: {quality_breakdown.to_dict()}")
        
        # Upload to Airtable
        result = self.airtable.upload_jobs(quality_jobs)
        
        if result.get('success'):
            print(f"✅ Successfully uploaded {result.get('uploaded_count', 0)} quality jobs to Airtable")
        else:
            print(f"❌ Airtable upload failed: {result.get('message', 'Unknown error')}")
        
        return result
    
    def get_count_reduction_info(self, location: str, target_count: int, hours: int = 72) -> Dict:
        """
        Get count reduction info using memory database instead of Airtable
        This avoids API calls for the analysis
        
        Args:
            location: Location to check (e.g., "Dallas, TX")
            target_count: Target number of jobs needed (e.g., 1000)
            hours: Hours to look back for quality jobs (default 72)
            
        Returns:
            Dict with reduction info: existing_jobs, jobs_to_scrape, cost_savings
        """
        # Get recent quality jobs from memory database
        quality_jobs = self.memory_db.get_quality_jobs_for_count_reduction(location, hours)
        existing_count = len(quality_jobs)
        
        # Calculate how many jobs we still need to scrape
        jobs_to_scrape = max(0, target_count - existing_count)
        
        # Calculate cost savings ($0.0003 per job for GPT-4o Mini)
        jobs_saved = min(existing_count, target_count)
        cost_savings = jobs_saved * 0.0003
        
        return {
            'reduction_available': True,
            'existing_jobs': existing_count,
            'jobs_to_scrape': jobs_to_scrape,
            'jobs_saved': jobs_saved,
            'cost_savings': cost_savings,
            'quality_jobs': quality_jobs,
            'hours_lookback': hours,
            'source': 'memory_database'
        }
    
    def cleanup_old_data(self, days: int = 7) -> bool:
        """Clean up old data from memory database to save space"""
        print(f"🧹 Cleaning up memory database records older than {days} days...")
        return self.memory_db.cleanup_old_records(days)
    
    def get_hybrid_memory_stats(self) -> Dict:
        """Get statistics about hybrid memory system"""
        stats = self.memory_db.get_memory_stats()
        
        # Add Airtable info if available
        self._init_airtable()
        if self.airtable and self.airtable.table:
            airtable_test = self.airtable.test_connection()
            stats['airtable_available'] = airtable_test.get('success', False)
        else:
            stats['airtable_available'] = False
        
        return stats
    
    def classify_jobs(self, df: pd.DataFrame) -> pd.DataFrame:
        """Main classification method - uses hybrid memory by default"""
        return self.classify_with_hybrid_memory(df)
    
    def _ensure_job_ids(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure job_id column exists for memory checking"""
        if 'job_id' not in df.columns:
            # Generate job IDs using same logic as file_processor
            import hashlib
            def generate_job_id(row):
                base_string = f"{str(row.get('company', '')).lower().strip()}|{str(row.get('location', '')).lower().strip()}|{str(row.get('job_title', '')).lower().strip()}"
                return hashlib.md5(base_string.encode()).hexdigest()
            
            df['job_id'] = df.apply(generate_job_id, axis=1)
        
        return df
    
    def _apply_memory_classifications(self, df: pd.DataFrame, job_memory: Dict[str, Dict]) -> pd.DataFrame:
        """Apply cached classifications from memory database"""
        for idx, row in df.iterrows():
            job_id = row['job_id']
            if job_id in job_memory:
                memory_data = job_memory[job_id]
                
                # Apply cached classification fields
                df.at[idx, 'match'] = memory_data.get('match', 'unknown')
                df.at[idx, 'reason'] = memory_data.get('reason', '')
                df.at[idx, 'summary'] = memory_data.get('summary', '')
                
                # Handle route_type: preserve existing classification, or use memory, or classify fresh
                existing_route = df.at[idx, 'route_type'] if 'route_type' in df.columns else 'Unknown'
                memory_route = memory_data.get('route_type', 'unknown')
                
                if existing_route and existing_route not in ['Unknown', 'unknown', '']:
                    # Keep existing route classification (already classified in pipeline)
                    pass
                elif memory_route and memory_route not in ['unknown', 'Unknown', '']:
                    # Use stored memory route classification
                    df.at[idx, 'route_type'] = memory_route
                else:
                    # No good route data - run route classifier on memory job
                    from route_classifier import RouteClassifier
                    route_classifier = RouteClassifier()
                    fresh_route = route_classifier.classify_route_type(
                        row.get('job_title', ''),
                        row.get('job_description', ''),
                        row.get('company', '')
                    )
                    df.at[idx, 'route_type'] = fresh_route
                    
                df.at[idx, 'fair_chance'] = memory_data.get('fair_chance', 'unknown')
                df.at[idx, 'endorsements'] = memory_data.get('endorsements', 'unknown')
                df.at[idx, 'career_pathway'] = memory_data.get('career_pathway', 'cdl_pathway')
                df.at[idx, 'training_provided'] = memory_data.get('training_provided', False)

                # Special final_status for jobs from memory
                original_status = memory_data.get('final_status', 'included')
                if original_status == 'included':
                    df.at[idx, 'final_status'] = 'included_from_memory'
                else:
                    df.at[idx, 'final_status'] = f'{original_status}_from_memory'
        
        return df