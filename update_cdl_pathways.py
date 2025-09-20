#!/usr/bin/env python3
"""
Simple script to update existing CDL jobs with career_pathway = 'cdl_pathway'
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def update_cdl_jobs():
    """Update existing CDL jobs to have career_pathway = 'cdl_pathway'"""

    try:
        from supabase_utils import get_client

        client = get_client()
        if not client:
            print("❌ Supabase client not available")
            return False

        print("🔄 Updating CDL jobs with career_pathway = 'cdl_pathway'...")

        # Update all jobs that have career_pathway = 'cdl' to 'cdl_pathway'
        result = client.table('jobs').update({
            'career_pathway': 'cdl_pathway'
        }).eq('career_pathway', 'cdl').execute()

        if result.data:
            updated_count = len(result.data)
            print(f"✅ Updated {updated_count} jobs with career_pathway = 'cdl_pathway'")
        else:
            print("ℹ️ No jobs needed updating (all already have career_pathway set)")

        # Verify the update
        total_cdl = client.table('jobs').select('job_id', count='exact').eq('career_pathway', 'cdl_pathway').execute()
        cdl_count = total_cdl.count if total_cdl.count is not None else 0

        total_jobs = client.table('jobs').select('job_id', count='exact').execute()
        total_count = total_jobs.count if total_jobs.count is not None else 0

        print(f"📊 Results: {cdl_count} jobs now have 'cdl_pathway' out of {total_count} total jobs")

        return True

    except Exception as e:
        print(f"❌ Error updating jobs: {e}")
        return False

if __name__ == "__main__":
    update_cdl_jobs()