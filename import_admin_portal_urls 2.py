#!/usr/bin/env python3
"""
Import Admin Portal URLs from Airtable to Supabase
Syncs the "Admin Portal Record" field from Airtable to agent_profiles.admin_portal_url in Supabase
"""

import os
import sys
from typing import List, Dict, Any, Tuple
import logging

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try to load Streamlit secrets if available
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/admin_portal_import.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AdminPortalImporter:
    """Import admin portal URLs from Airtable to Supabase"""
    
    def __init__(self):
        self.airtable_client = None
        self.supabase_client = None
        self.stats = {
            'airtable_records': 0,
            'supabase_agents': 0,
            'matched_agents': 0,
            'updated_agents': 0,
            'errors': 0
        }
        
    def initialize_clients(self):
        """Initialize Airtable and Supabase clients"""
        try:
            # Airtable setup
            try:
                from pyairtable import Api
                api_key = os.getenv('AIRTABLE_API_KEY')
                base_id = os.getenv('AIRTABLE_BASE_ID')
                # Use the Free Agents/Candidates table
                table_id = os.getenv('AIRTABLE_CANDIDATES_TABLE_ID', os.getenv('AIRTABLE_TABLE_ID'))
                
                if not all([api_key, base_id, table_id]):
                    raise ValueError("Missing Airtable configuration (API_KEY, BASE_ID, or TABLE_ID)")
                
                self.airtable_client = Api(api_key).table(base_id, table_id)
                logger.info("✅ Airtable client initialized")
                
            except Exception as e:
                logger.error(f"❌ Airtable initialization failed: {e}")
                raise
            
            # Supabase setup
            try:
                from supabase_utils import get_client
                self.supabase_client = get_client()
                if not self.supabase_client:
                    raise ValueError("Supabase client initialization failed")
                logger.info("✅ Supabase client initialized")
                
            except Exception as e:
                logger.error(f"❌ Supabase initialization failed: {e}")
                raise
                
        except Exception as e:
            logger.error(f"❌ Client initialization failed: {e}")
            raise
    
    def fetch_airtable_admin_portals(self) -> Dict[str, str]:
        """Fetch admin portal URLs from Airtable, keyed by agent UUID"""
        try:
            logger.info("🔍 Fetching admin portal data from Airtable...")
            
            # Fetch all records with UUID and Admin Portal Record fields
            admin_portals = {}
            processed_count = 0
            
            for records_batch in self.airtable_client.iterate():
                for record in records_batch:
                    processed_count += 1
                    fields = record.get('fields', {})
                    
                    # Get UUID and Admin Portal Record
                    agent_uuid = fields.get('uuid', '').strip()
                    admin_portal_url = fields.get('Admin Portal Record', '').strip()
                    agent_name = fields.get('fullName', 'Unknown')
                    
                    if agent_uuid and admin_portal_url:
                        admin_portals[agent_uuid] = admin_portal_url
                        logger.info(f"📝 Found admin portal for {agent_name} ({agent_uuid[:8]}...): {admin_portal_url[:50]}...")
                    elif agent_uuid:
                        logger.info(f"⚪ No admin portal for {agent_name} ({agent_uuid[:8]}...)")
            
            self.stats['airtable_records'] = processed_count
            logger.info(f"📥 Processed {processed_count} Airtable records")
            logger.info(f"🔗 Found {len(admin_portals)} admin portal URLs")
            
            return admin_portals
            
        except Exception as e:
            logger.error(f"❌ Airtable fetch failed: {e}")
            raise
    
    def get_supabase_agents(self) -> List[Dict]:
        """Get all active agents from Supabase"""
        try:
            logger.info("🔍 Fetching agents from Supabase...")
            
            result = self.supabase_client.table('agent_profiles').select(
                'agent_uuid, agent_name, admin_portal_url, coach_username'
            ).eq('is_active', True).execute()
            
            agents = result.data or []
            self.stats['supabase_agents'] = len(agents)
            logger.info(f"📥 Found {len(agents)} active agents in Supabase")
            
            return agents
            
        except Exception as e:
            logger.error(f"❌ Supabase fetch failed: {e}")
            raise
    
    def update_agent_admin_portal(self, agent_uuid: str, admin_portal_url: str) -> bool:
        """Update a single agent's admin portal URL in Supabase"""
        try:
            result = self.supabase_client.table('agent_profiles').update({
                'admin_portal_url': admin_portal_url
            }).eq('agent_uuid', agent_uuid).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to update agent {agent_uuid}: {e}")
            return False
    
    def import_admin_portals(self, dry_run: bool = False) -> Dict[str, Any]:
        """Main import process"""
        logger.info(f"🚀 Starting {'DRY RUN' if dry_run else 'LIVE'} admin portal import")
        
        try:
            # Step 1: Get admin portal URLs from Airtable
            airtable_portals = self.fetch_airtable_admin_portals()
            
            # Step 2: Get all agents from Supabase
            supabase_agents = self.get_supabase_agents()
            
            # Step 3: Match and update
            for agent in supabase_agents:
                agent_uuid = agent['agent_uuid']
                agent_name = agent['agent_name']
                current_portal = agent.get('admin_portal_url', '')
                
                if agent_uuid in airtable_portals:
                    new_portal_url = airtable_portals[agent_uuid]
                    self.stats['matched_agents'] += 1
                    
                    # Check if update is needed
                    if current_portal != new_portal_url:
                        if dry_run:
                            logger.info(f"📋 DRY RUN: Would update {agent_name}")
                            logger.info(f"   Current: {current_portal or '(empty)'}")
                            logger.info(f"   New:     {new_portal_url}")
                        else:
                            logger.info(f"🔄 Updating {agent_name} ({agent_uuid[:8]}...)")
                            success = self.update_agent_admin_portal(agent_uuid, new_portal_url)
                            if success:
                                self.stats['updated_agents'] += 1
                                logger.info(f"✅ Updated {agent_name}")
                            else:
                                self.stats['errors'] += 1
                                logger.error(f"❌ Failed to update {agent_name}")
                    else:
                        logger.info(f"✓ {agent_name}: Already up to date")
                else:
                    logger.info(f"⚪ {agent_name}: No admin portal in Airtable")
            
            # Summary
            logger.info("📊 IMPORT SUMMARY:")
            logger.info(f"   Airtable Records: {self.stats['airtable_records']}")
            logger.info(f"   Supabase Agents: {self.stats['supabase_agents']}")
            logger.info(f"   Matched Agents: {self.stats['matched_agents']}")
            logger.info(f"   Updated Agents: {self.stats['updated_agents']}")
            logger.info(f"   Errors: {self.stats['errors']}")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"❌ Import process failed: {e}")
            raise

def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import admin portal URLs from Airtable to Supabase')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without updating data')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        importer = AdminPortalImporter()
        importer.initialize_clients()
        stats = importer.import_admin_portals(dry_run=args.dry_run)
        
        if stats['errors'] == 0:
            logger.info("🎉 Import completed successfully!")
        else:
            logger.warning(f"⚠️ Import completed with {stats['errors']} errors")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()