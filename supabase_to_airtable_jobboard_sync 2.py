#!/usr/bin/env python3
"""
Supabase → Airtable Job Board Sync System
Daily sync that updates Airtable job board with good/so-so quality jobs from last 72 hours.
Automatically deletes jobs older than 72 hours to keep the board fresh.
"""

import os
import sys
import json
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

# Load environment variables from .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try to load Streamlit secrets if running in Streamlit environment
try:
    import streamlit as st
    for k, v in (st.secrets or {}).items():
        if isinstance(v, (str, int, float, bool)):
            os.environ.setdefault(k, str(v))
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/jobboard_sync_log.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SupabaseToAirtableJobSync:
    """Sync quality jobs from Supabase to Airtable job board with auto-cleanup"""
    
    def __init__(self):
        self.supabase_client = None
        self.airtable_client = None
        self.stats = {
            'fetched_from_supabase': 0,
            'created_in_airtable': 0,
            'updated_in_airtable': 0,
            'deleted_old_jobs': 0,
            'errors': 0,
            'skipped': 0
        }
        
    def initialize_clients(self):
        """Initialize Supabase and Airtable clients"""
        try:
            # Supabase setup
            try:
                from supabase_utils import get_client
                self.supabase_client = get_client()
                if not self.supabase_client:
                    raise ValueError("Supabase client initialization failed")
                logger.info("✅ Supabase client initialized")
            except Exception as e:
                logger.error(f"❌ Supabase initialization failed: {str(e)[:100]}...")
                raise
            
            # Airtable setup
            try:
                from pyairtable import Api
                api_key = os.getenv('AIRTABLE_API_KEY')
                if not api_key:
                    raise ValueError("AIRTABLE_API_KEY not found in environment")
                
                base_id = os.getenv('AIRTABLE_BASE_ID')
                # Use the Jobs table for job board
                table_id = os.getenv('AIRTABLE_JOBS_TABLE_ID', os.getenv('AIRTABLE_TABLE_ID'))
                if not base_id or not table_id:
                    raise ValueError("Airtable base/table IDs not configured")
                
                self.airtable_client = Api(api_key).table(base_id, table_id)
                logger.info("✅ Airtable client initialized")
                
            except Exception as e:
                logger.error(f"❌ Airtable initialization failed: {str(e)[:100]}...")
                raise
                
        except Exception as e:
            logger.error(f"❌ Client initialization failed: {type(e).__name__}")
            raise
    
    def fetch_quality_jobs_from_supabase(self, hours: int = 72) -> List[Dict[str, Any]]:
        """Fetch good/so-so quality jobs from Supabase created in the last N hours"""
        try:
            cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
            logger.info(f"🔍 Fetching quality jobs created after {cutoff_time} (last {hours}h)")
            
            # Query Supabase for quality jobs
            response = self.supabase_client.table('jobs').select(
                'job_id, job_title, company, location, job_description, apply_url, salary, '
                'match_level, match_reason, summary, fair_chance, endorsements, route_type, '
                'market, tracked_url, indeed_job_url, created_at, updated_at'
            ).in_('match_level', ['good', 'so-so']).gte('created_at', cutoff_time).order('created_at', desc=True).execute()
            
            jobs = response.data or []
            logger.info(f"📥 Retrieved {len(jobs)} quality jobs from Supabase")
            self.stats['fetched_from_supabase'] = len(jobs)
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Supabase query failed: {str(e)[:100]}...")
            raise
    
    def convert_job_to_airtable_format(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Supabase job record to Airtable format"""
        try:
            # Create Airtable-compatible record
            airtable_record = {
                'Job ID': job.get('job_id', ''),
                'Job Title': job.get('job_title', ''),
                'Company': job.get('company', ''),
                'Location': job.get('location', ''),
                'Market': job.get('market', ''),
                'Description': job.get('job_description', '')[:50000] if job.get('job_description') else '',  # Airtable limit
                'AI Summary': job.get('summary', ''),
                'Apply URL': job.get('apply_url', ''),
                'Tracked URL': job.get('tracked_url', ''),
                'Salary': job.get('salary', ''),
                'Match Quality': job.get('match_level', ''),
                'Match Reason': job.get('match_reason', ''),
                'Route Type': job.get('route_type', ''),
                'Fair Chance': job.get('fair_chance', ''),
                'Endorsements': job.get('endorsements', ''),
                'Indeed URL': job.get('indeed_job_url', ''),
                'Created At': job.get('created_at', ''),
                'Updated At': job.get('updated_at', ''),
            }
            
            # Remove empty fields to reduce Airtable storage
            return {k: v for k, v in airtable_record.items() if v}
            
        except Exception as e:
            logger.error(f"❌ Job conversion failed: {str(e)}")
            raise
    
    def delete_old_jobs_from_airtable(self, hours: int = 72) -> int:
        """Delete jobs older than N hours from Airtable"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            logger.info(f"🗑️ Deleting jobs older than {cutoff_time.isoformat()}")
            
            # Fetch all existing records with Created At field
            existing_records = []
            for record_batch in self.airtable_client.iterate():
                existing_records.extend(record_batch)
            
            # Find records to delete (older than cutoff)
            records_to_delete = []
            for record in existing_records:
                created_at_str = record['fields'].get('Created At')
                if created_at_str:
                    try:
                        # Parse ISO format datetime
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        if created_at < cutoff_time:
                            records_to_delete.append(record['id'])
                    except (ValueError, TypeError):
                        # If can't parse date, consider it old and delete
                        records_to_delete.append(record['id'])
            
            # Delete old records in batches
            deleted_count = 0
            batch_size = 10  # Airtable API limit
            for i in range(0, len(records_to_delete), batch_size):
                batch = records_to_delete[i:i + batch_size]
                try:
                    self.airtable_client.batch_delete(batch)
                    deleted_count += len(batch)
                    logger.info(f"🗑️ Deleted batch of {len(batch)} old jobs")
                except Exception as e:
                    logger.error(f"❌ Failed to delete batch: {str(e)}")
            
            logger.info(f"✅ Deleted {deleted_count} old jobs from Airtable")
            self.stats['deleted_old_jobs'] = deleted_count
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Old job deletion failed: {str(e)[:100]}...")
            return 0
    
    def upsert_job_to_airtable(self, job_record: Dict[str, Any]) -> Tuple[str, str]:
        """Upsert job record to Airtable (create or update based on Job ID)"""
        try:
            job_id = job_record.get('Job ID', '')
            if not job_id:
                raise ValueError("Missing Job ID")
            
            # Check if record already exists
            existing = self.airtable_client.all(formula=f"{{Job ID}} = '{job_id}'")
            
            if existing:
                # Update existing record
                record_id = existing[0]['id']
                self.airtable_client.update(record_id, job_record)
                return 'updated', job_id
            else:
                # Create new record
                self.airtable_client.create(job_record)
                return 'created', job_id
                
        except Exception as e:
            logger.error(f"❌ Airtable upsert failed for job {job_record.get('Job ID', 'unknown')}: {str(e)}")
            raise
    
    def sync_jobs(self, hours: int = 72, dry_run: bool = False) -> Dict[str, Any]:
        """Main sync process"""
        logger.info(f"🚀 Starting {'DRY RUN' if dry_run else 'LIVE'} job board sync (last {hours}h)")
        
        try:
            # Step 1: Clean up old jobs first
            if not dry_run:
                deleted_count = self.delete_old_jobs_from_airtable(hours)
            else:
                logger.info("✓ DRY RUN: Would delete old jobs from Airtable")
            
            # Step 2: Fetch fresh quality jobs from Supabase
            jobs = self.fetch_quality_jobs_from_supabase(hours)
            
            # Step 3: Sync each job to Airtable
            for i, job in enumerate(jobs, 1):
                try:
                    # Convert to Airtable format
                    airtable_record = self.convert_job_to_airtable_format(job)
                    
                    if dry_run:
                        job_title = job.get('job_title', 'Unknown')
                        company = job.get('company', 'Unknown')
                        logger.info(f"✓ [{i}/{len(jobs)}] DRY RUN: Would sync {job_title} at {company}")
                        self.stats['skipped'] += 1
                    else:
                        # Upsert to Airtable
                        action, job_id = self.upsert_job_to_airtable(airtable_record)
                        job_title = job.get('job_title', 'Unknown')[:50]
                        logger.info(f"✅ [{i}/{len(jobs)}] {action.upper()}: {job_title} ({job_id[:8]})")
                        
                        if action == 'created':
                            self.stats['created_in_airtable'] += 1
                        else:
                            self.stats['updated_in_airtable'] += 1
                
                except Exception as e:
                    self.stats['errors'] += 1
                    logger.error(f"❌ [{i}/{len(jobs)}] Failed to sync job: {type(e).__name__}: {str(e)}")
                    continue
            
            # Summary
            logger.info("📊 JOB SYNC SUMMARY:")
            logger.info(f"   Fetched from Supabase: {self.stats['fetched_from_supabase']}")
            logger.info(f"   Created in Airtable: {self.stats['created_in_airtable']}")
            logger.info(f"   Updated in Airtable: {self.stats['updated_in_airtable']}")
            logger.info(f"   Deleted old jobs: {self.stats['deleted_old_jobs']}")
            logger.info(f"   Errors: {self.stats['errors']}")
            logger.info(f"   Skipped (dry run): {self.stats['skipped']}")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"❌ Job sync failed: {type(e).__name__}")
            raise
    
    def validate_sync(self) -> Dict[str, Any]:
        """Validate sync results by checking Airtable record counts"""
        try:
            logger.info("🔍 Validating job sync results...")
            
            # Count total records in Airtable
            all_records = []
            for record_batch in self.airtable_client.iterate():
                all_records.extend(record_batch)
            
            total_jobs = len(all_records)
            
            # Count by market and match quality
            market_counts = {}
            quality_counts = {}
            recent_jobs = 0
            cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
            
            for record in all_records:
                fields = record['fields']
                
                # Count by market
                market = fields.get('Market', 'Unknown')
                market_counts[market] = market_counts.get(market, 0) + 1
                
                # Count by quality
                quality = fields.get('Match Quality', 'Unknown')
                quality_counts[quality] = quality_counts.get(quality, 0) + 1
                
                # Count recent jobs
                created_at_str = fields.get('Created At')
                if created_at_str:
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        if created_at >= cutoff:
                            recent_jobs += 1
                    except (ValueError, TypeError):
                        pass
            
            validation = {
                'total_jobs_in_airtable': total_jobs,
                'recent_jobs_last_72h': recent_jobs,
                'by_market': market_counts,
                'by_quality': quality_counts,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"📊 Validation results:")
            logger.info(f"   Total jobs in Airtable: {total_jobs}")
            logger.info(f"   Recent jobs (72h): {recent_jobs}")
            logger.info(f"   By quality: {quality_counts}")
            logger.info(f"   Top markets: {dict(list(sorted(market_counts.items(), key=lambda x: x[1], reverse=True))[:5])}")
            
            return validation
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {type(e).__name__}")
            return {'error': str(e)}

def create_supabase_edge_function():
    """Generate Supabase Edge Function code for daily automation"""
    edge_function_code = '''
import { serve } from "https://deno.land/std@0.177.0/http/server.ts"

serve(async (req) => {
  try {
    // This would call the Python sync script
    // For now, return a placeholder response
    const response = {
      success: true,
      message: "Job board sync completed",
      timestamp: new Date().toISOString()
    }
    
    return new Response(
      JSON.stringify(response),
      { headers: { "Content-Type": "application/json" } }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ 
        success: false, 
        error: error.message,
        timestamp: new Date().toISOString()
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    )
  }
})

/*
To set up daily automation:

1. Create this as a Supabase Edge Function
2. Set up a cron job to call it daily:
   - Use GitHub Actions with cron schedule
   - Or use external service like Vercel Cron
   - Or use pg_cron in Supabase

3. Example GitHub Actions workflow (.github/workflows/daily-job-sync.yml):

name: Daily Job Board Sync
on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM UTC
  workflow_dispatch:  # Allow manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python supabase_to_airtable_jobboard_sync.py --hours 72
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}
          AIRTABLE_API_KEY: ${{ secrets.AIRTABLE_API_KEY }}
          AIRTABLE_BASE_ID: ${{ secrets.AIRTABLE_BASE_ID }}
          AIRTABLE_JOBS_TABLE_ID: ${{ secrets.AIRTABLE_JOBS_TABLE_ID }}
*/
'''
    return edge_function_code

def main():
    """Command-line interface for job board sync"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync quality jobs from Supabase to Airtable job board')
    parser.add_argument('--hours', type=int, default=72, help='Hours lookback for jobs (default: 72)')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying data')
    parser.add_argument('--validate', action='store_true', help='Validate sync results')
    parser.add_argument('--generate-edge-function', action='store_true', help='Generate Supabase Edge Function code')
    
    args = parser.parse_args()
    
    try:
        if args.generate_edge_function:
            print("📄 Supabase Edge Function code:")
            print("=" * 50)
            print(create_supabase_edge_function())
            return
        
        syncer = SupabaseToAirtableJobSync()
        syncer.initialize_clients()
        
        if args.validate:
            syncer.validate_sync()
        else:
            syncer.sync_jobs(hours=args.hours, dry_run=args.dry_run)
            
    except Exception as e:
        logger.error(f"❌ Sync failed: {type(e).__name__}")
        sys.exit(1)

if __name__ == '__main__':
    main()