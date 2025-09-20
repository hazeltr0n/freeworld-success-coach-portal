#!/usr/bin/env python3
"""
Check current pathway distribution in database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_pathway_distribution():
    """Check current career pathway distribution"""

    try:
        from supabase_utils import get_client

        client = get_client()
        if not client:
            print("❌ Supabase client not available")
            return False

        print("📊 Current Career Pathway Distribution:")
        print("=" * 50)

        # Get all jobs with their career_pathway values
        result = client.table('jobs').select('career_pathway').execute()

        if not result.data:
            print("⚠️ No jobs found in database")
            return

        # Count distribution
        pathway_counts = {}
        total_jobs = len(result.data)

        for job in result.data:
            pathway = job.get('career_pathway')
            if pathway is None:
                pathway = 'NULL'
            elif pathway == '':
                pathway = 'EMPTY'

            pathway_counts[pathway] = pathway_counts.get(pathway, 0) + 1

        # Sort by count
        sorted_pathways = sorted(pathway_counts.items(), key=lambda x: x[1], reverse=True)

        print(f"Total jobs: {total_jobs}")
        print()

        for pathway, count in sorted_pathways:
            percentage = (count / total_jobs) * 100
            print(f"{pathway:25} {count:6} ({percentage:5.1f}%)")

        print()

        # Check for jobs that need CDL pathway update
        needs_update = pathway_counts.get('NULL', 0) + pathway_counts.get('EMPTY', 0)
        if needs_update > 0:
            print(f"🎯 {needs_update} jobs need to be updated to 'cdl_pathway'")
        else:
            print("✅ All jobs have career_pathway values set")

        return True

    except Exception as e:
        print(f"❌ Error checking pathways: {e}")
        return False

if __name__ == "__main__":
    check_pathway_distribution()