#!/usr/bin/env python3
"""
Airtable → Supabase Free Agent Sync Tool
Securely syncs Free Agent data from Airtable to Supabase with data validation,
conflict resolution, and comprehensive logging.
"""

import os
import sys
import json
import hashlib
import logging
from datetime import datetime, timezone
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
    # Mirror st.secrets into env variables
    for k, v in (st.secrets or {}).items():
        if isinstance(v, (str, int, float, bool)):
            os.environ.setdefault(k, str(v))
except ImportError:
    pass  # Not running in Streamlit environment

# Configure secure logging (no sensitive data)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/sync_log.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SecureAirtableSupabaseSync:
    """Secure sync tool for Free Agent data migration"""
    
    def __init__(self):
        self.airtable_client = None
        self.supabase_client = None
        self.stats = {
            'total_records': 0,
            'created': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }
        
    def initialize_clients(self):
        """Initialize Airtable and Supabase clients with secure credential handling"""
        try:
            # Airtable setup
            try:
                from pyairtable import Api
                api_key = os.getenv('AIRTABLE_API_KEY')
                if not api_key:
                    raise ValueError("AIRTABLE_API_KEY not found in environment")
                
                base_id = os.getenv('AIRTABLE_BASE_ID')
                # Use the Free Agents table specifically
                table_id = os.getenv('AIRTABLE_CANDIDATES_TABLE_ID', os.getenv('AIRTABLE_TABLE_ID'))
                if not base_id or not table_id:
                    raise ValueError("Airtable base/table IDs not configured")
                
                self.airtable_client = Api(api_key).table(base_id, table_id)
                logger.info("✅ Airtable client initialized")
                
            except Exception as e:
                logger.error(f"❌ Airtable initialization failed: {str(e)[:100]}...")
                raise
            
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
                
        except Exception as e:
            logger.error(f"❌ Client initialization failed: {type(e).__name__}")
            raise
    
    def sanitize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize and validate Airtable record for Supabase insertion"""
        fields = record.get('fields', {})
        
        # Extract and validate required fields using correct Airtable → Supabase field mapping
        sanitized = {
            'agent_uuid': str(fields.get('uuid', '')).strip(),
            'agent_name': str(fields.get('fullName', '')).strip(),
            'agent_email': str(fields.get('email', '')).strip().lower() if fields.get('email') else None,
            'agent_city': str(fields.get('city', '')).strip() if fields.get('city') else None,
            'agent_state': str(fields.get('state', '')).strip() if fields.get('state') else None,
            'coach_username': 'imported',  # Default coach for imported records
            'is_active': True,  # Default to active
            'search_config': {  # Default search configuration
                'location': 'Houston',
                'route_filter': 'both',
                'fair_chance_only': False,
                'max_jobs': 25,
                'experience_level': 'both'
            },
            'custom_url': '',  # Empty custom URL initially
            'last_accessed': 'NOW()'  # Current timestamp
        }
        
        # Validate required fields
        if not sanitized['agent_uuid'] or not sanitized['agent_name']:
            raise ValueError("Missing required fields: UUID or Name")
        
        if not sanitized['coach_username']:
            raise ValueError("Missing coach assignment")
        
        # Set location in search_config based on available city/state
        if sanitized['agent_city'] and sanitized['agent_state']:
            sanitized['search_config']['location'] = f"{sanitized['agent_city']}, {sanitized['agent_state']}"
        elif sanitized['agent_city']:
            sanitized['search_config']['location'] = sanitized['agent_city']
        
        return sanitized
    
    def _sanitize_phone(self, phone: str) -> Optional[str]:
        """Sanitize phone number (remove formatting but don't validate format)"""
        if not phone:
            return None
        
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, str(phone)))
        
        # Return None if no digits found
        if not digits_only:
            return None
            
        # Return as-is (don't validate format for privacy)
        return digits_only[-10:] if len(digits_only) >= 10 else digits_only
    
    def _sanitize_status(self, status: str) -> str:
        """Sanitize and validate status field"""
        valid_statuses = ['active', 'inactive', 'placed']
        status_clean = str(status).lower().strip()
        return status_clean if status_clean in valid_statuses else 'active'
    
    def fetch_airtable_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch records from Airtable with pagination and error handling"""
        try:
            logger.info(f"🔍 Fetching up to {limit} records from Airtable...")
            
            # Fetch with pagination
            all_records = []
            for records in self.airtable_client.iterate(page_size=min(limit, 100)):
                all_records.extend(records)
                if len(all_records) >= limit:
                    break
            
            # Limit to requested amount
            all_records = all_records[:limit]
            
            logger.info(f"📥 Retrieved {len(all_records)} records from Airtable")
            return all_records
            
        except Exception as e:
            logger.error(f"❌ Airtable fetch failed: {str(e)[:100]}...")
            raise
    
    def upsert_to_supabase(self, record: Dict[str, Any]) -> Tuple[str, str]:
        """Upsert record to Supabase with conflict resolution"""
        try:
            # Check if record exists
            existing = self.supabase_client.table('agent_profiles').select('*').eq('agent_uuid', record['agent_uuid']).execute()
            
            if existing.data:
                # Update existing record
                result = self.supabase_client.table('agent_profiles').update(record).eq('agent_uuid', record['agent_uuid']).execute()
                return 'updated', record['agent_uuid']
            else:
                # Insert new record
                result = self.supabase_client.table('agent_profiles').insert(record).execute()
                return 'created', record['agent_uuid']
                
        except Exception as e:
            # Log error without exposing sensitive data
            error_hash = hashlib.md5(str(e).encode()).hexdigest()[:8]
            logger.error(f"❌ Supabase upsert failed for record {record.get('agent_uuid', 'unknown')} (error #{error_hash})")
            raise
    
    def sync_records(self, limit: int = 100, dry_run: bool = False) -> Dict[str, Any]:
        """Main sync process with comprehensive error handling"""
        logger.info(f"🚀 Starting {'DRY RUN' if dry_run else 'LIVE'} sync (limit: {limit})")
        
        try:
            # Fetch from Airtable
            airtable_records = self.fetch_airtable_records(limit)
            self.stats['total_records'] = len(airtable_records)
            
            # Process each record
            for i, record in enumerate(airtable_records, 1):
                try:
                    # Sanitize data
                    sanitized = self.sanitize_record(record)
                    
                    if dry_run:
                        logger.info(f"✓ [{i}/{len(airtable_records)}] DRY RUN: Would sync {sanitized['agent_name']} ({sanitized['agent_uuid']})")
                        self.stats['skipped'] += 1
                    else:
                        # Upsert to Supabase
                        action, uuid = self.upsert_to_supabase(sanitized)
                        logger.info(f"✅ [{i}/{len(airtable_records)}] {action.upper()}: {sanitized['agent_name']} ({uuid})")
                        
                        if action == 'created':
                            self.stats['created'] += 1
                        else:
                            self.stats['updated'] += 1
                
                except Exception as e:
                    self.stats['errors'] += 1
                    # Log error with more detail for debugging
                    logger.error(f"❌ [{i}/{len(airtable_records)}] Failed to process record: {type(e).__name__}: {str(e)}")
                    
                    # For dry runs, show the record structure to help debug
                    if dry_run:
                        logger.info(f"   Record fields: {list(record.get('fields', {}).keys())}")
                    
                    # Continue processing other records
                    continue
            
            # Summary
            logger.info("📊 SYNC SUMMARY:")
            logger.info(f"   Total Records: {self.stats['total_records']}")
            logger.info(f"   Created: {self.stats['created']}")
            logger.info(f"   Updated: {self.stats['updated']}")
            logger.info(f"   Errors: {self.stats['errors']}")
            logger.info(f"   Skipped: {self.stats['skipped']}")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"❌ Sync process failed: {type(e).__name__}")
            raise
    
    def validate_sync(self) -> Dict[str, Any]:
        """Validate sync results by comparing record counts"""
        try:
            logger.info("🔍 Validating sync results...")
            
            # Count records in Supabase
            supabase_count = self.supabase_client.table('agent_profiles').select('id', count='exact').execute()
            total_supabase = len(supabase_count.data) if supabase_count.data else 0
            
            # Count by coach
            coaches_result = self.supabase_client.table('agent_profiles').select('coach_username').execute()
            coach_counts = {}
            for record in coaches_result.data:
                coach = record.get('coach_username', 'unknown')
                coach_counts[coach] = coach_counts.get(coach, 0) + 1
            
            validation = {
                'total_in_supabase': total_supabase,
                'by_coach': coach_counts,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"📊 Validation results: {total_supabase} total records")
            for coach, count in coach_counts.items():
                logger.info(f"   {coach}: {count} agents")
            
            return validation
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {type(e).__name__}")
            return {'error': str(e)}

def main():
    """Command-line interface for sync tool"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync Free Agents from Airtable to Supabase')
    parser.add_argument('--limit', type=int, default=100, help='Maximum records to sync')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying data')
    parser.add_argument('--validate', action='store_true', help='Validate sync results')
    
    args = parser.parse_args()
    
    try:
        syncer = SecureAirtableSupabaseSync()
        syncer.initialize_clients()
        
        if args.validate:
            syncer.validate_sync()
        else:
            syncer.sync_records(limit=args.limit, dry_run=args.dry_run)
            
    except Exception as e:
        logger.error(f"❌ Sync failed: {type(e).__name__}")
        sys.exit(1)

if __name__ == '__main__':
    main()