#!/usr/bin/env python3
"""
Free Agent Lookup Service (Supabase-first)
Fetches Free Agent data from Supabase agent_profiles to populate agent.* fields.
Explicitly avoids Airtable lookups inside the pipeline/app paths.
"""

import os
import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class FreeAgentLookup:
    """Handles Free Agent data lookup from Supabase (no Airtable)"""
    
    def __init__(self):
        """Initialize Free Agent lookup using environment variables.
        
        Supabase env vars (via supabase-py):
          - SUPABASE_URL
          - SUPABASE_ANON_KEY
        """
        # No Airtable initialization; use Supabase client lazily via supabase_utils
        self.api = None
        self.table = None
    
    def get_agent_by_uuid(self, agent_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Get Free Agent data by UUID (Supabase)
        
        Args:
            agent_uuid: Free Agent UUID from environment or selection
            
        Returns:
            Dict with canonical agent.* fields or None if not found
        """
        if not agent_uuid:
            return None
        try:
            from supabase_utils import get_client  # type: ignore
            client = get_client()
            if client is None:
                return None
            res = client.table('agent_profiles').select(
                'agent_uuid, agent_name, agent_email, agent_city, agent_state, coach_username'
            ).eq('agent_uuid', agent_uuid).eq('is_active', True).limit(1).execute()
            row = (res.data or [None])[0]
            if not row:
                logger.warning(f"Free Agent not found in Supabase: {agent_uuid}")
                return None
            return self._map_supabase_to_canonical(row)
        except Exception as e:
            logger.error(f"Error looking up Free Agent (Supabase) {agent_uuid}: {e}")
            return None
    
    def get_agent_by_name(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get Free Agent data by name (Supabase)
        
        Args:
            agent_name: Free Agent full name
            
        Returns:
            Dict with canonical agent.* fields or None if not found
        """
        if not agent_name:
            return None
        try:
            from supabase_utils import get_client  # type: ignore
            client = get_client()
            if client is None:
                return None
            res = client.table('agent_profiles').select(
                'agent_uuid, agent_name, agent_email, agent_city, agent_state, coach_username'
            ).ilike('agent_name', agent_name).eq('is_active', True).limit(1).execute()
            row = (res.data or [None])[0]
            if not row:
                logger.warning(f"Free Agent not found by name in Supabase: {agent_name}")
                return None
            return self._map_supabase_to_canonical(row)
        except Exception as e:
            logger.error(f"Error looking up Free Agent by name (Supabase) {agent_name}: {e}")
            return None
    
    def _map_supabase_to_canonical(self, row: Dict[str, Any]) -> Dict[str, str]:
        """Map Supabase agent_profiles row to canonical agent.* schema"""
        full_name = (row.get('agent_name') or '').strip()
        first_name = full_name.split()[0] if full_name else ''
        last_name = ' '.join(full_name.split()[1:]) if full_name and len(full_name.split()) > 1 else ''
        return {
            'agent.uuid': row.get('agent_uuid', '') or '',
            'agent.name': full_name,
            'agent.first_name': first_name,
            'agent.last_name': last_name,
            'agent.email': row.get('agent_email', '') or '',
            'agent.phone': '',
            'agent.city': row.get('agent_city', '') or '',
            'agent.state': row.get('agent_state', '') or '',
            'agent.coach_name': '',  # not stored in row; provided by UI
            'agent.coach_username': row.get('coach_username', '') or '',
            'agent.preferred_route': 'Both',
            'agent.experience_years': '0',
            'agent.endorsements_held': '',
            'agent.notes': 'Free Agent data from Supabase',
            'agent.last_contact': datetime.now().strftime('%Y-%m-%d'),
            'agent.status': 'Active'
        }
    
    def get_agent_data_from_environment(self) -> Optional[Dict[str, str]]:
        """
        Get Free Agent data from environment variables (for terminal usage)
        
        Returns:
            Dict with agent.* fields from env vars, or None if no agent specified
        """
        candidate_id = os.getenv('FREEWORLD_CANDIDATE_ID', '').strip()
        candidate_name = os.getenv('FREEWORLD_CANDIDATE_NAME', '').strip()
        coach_name = os.getenv('FREEWORLD_COACH_NAME', '').strip()
        coach_username = os.getenv('FREEWORLD_COACH_USERNAME', '').strip()
        
        # Supabase-first lookups
        if candidate_id:
            agent_data = self.get_agent_by_uuid(candidate_id)
            if agent_data:
                return agent_data
        if candidate_name:
            agent_data = self.get_agent_by_name(candidate_name)
            if agent_data:
                return agent_data
        
        # Fallback: build from environment variables if no Airtable lookup worked
        if candidate_name or candidate_id:
            logger.info("Building Free Agent data from environment variables")
            return {
                'agent.uuid': candidate_id,
                'agent.name': candidate_name,
                'agent.first_name': candidate_name.split()[0] if candidate_name else '',
                'agent.last_name': candidate_name.split()[-1] if candidate_name and ' ' in candidate_name else '',
                'agent.email': '',
                'agent.phone': '',
                'agent.city': '',
                'agent.state': '',
                'agent.coach_name': coach_name,
                'agent.coach_username': coach_username,
                'agent.preferred_route': 'Both',
                'agent.experience_years': '0',
                'agent.endorsements_held': '',
                'agent.notes': 'Free Agent data from environment variables',
                'agent.last_contact': datetime.now().strftime('%Y-%m-%d'),
                'agent.status': 'Active'
            }
        
        return None

# Convenience function for easy imports
def get_free_agent_data(candidate_id: str = None, candidate_name: str = None) -> Optional[Dict[str, str]]:
    """
    Quick lookup function for Free Agent data
    
    Args:
        candidate_id: Free Agent UUID (optional)
        candidate_name: Free Agent name (optional)
        
    Returns:
        Dict with agent.* canonical fields or None
    """
    lookup = FreeAgentLookup()
    if candidate_id:
        return lookup.get_agent_by_uuid(candidate_id)
    if candidate_name:
        return lookup.get_agent_by_name(candidate_name)
    return lookup.get_agent_data_from_environment()

def main():
    """Test the Free Agent lookup service"""
    print("🧪 Free Agent Lookup Service Test")
    print("=" * 50)
    
    lookup = FreeAgentLookup()
    
    if not lookup.table:
        print("❌ Airtable not configured")
        return
    
    # Test environment variable lookup
    print("\n🔍 Testing environment variable lookup...")
    env_data = lookup.get_agent_data_from_environment()
    
    if env_data:
        print(f"✅ Found Free Agent: {env_data['agent.name']}")
        print(f"   UUID: {env_data['agent.uuid']}")
        print(f"   Coach: {env_data['agent.coach_name']}")
    else:
        print("ℹ️ No Free Agent data in environment variables")
        print("   Set FREEWORLD_CANDIDATE_ID or FREEWORLD_CANDIDATE_NAME to test")

if __name__ == "__main__":
    main()
