#!/usr/bin/env python3
"""
Script to populate existing jobs in database with CDL pathway classification
Updates all jobs that don't have career_pathway set to have 'cdl_pathway'
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def populate_cdl_pathways():
    """Update existing jobs to have CDL pathway classification"""

    print("🔄 POPULATE CDL PATHWAYS: Starting database update...")

    try:
        from supabase_utils import get_client

        client = get_client()
        if not client:
            print("❌ Supabase client not available")
            return False

        # First, check current state of database
        print("📊 Checking current database state...")

        # Get all jobs to see current schema
        result = client.table('jobs').select('job_id, career_pathway, classifier_type').limit(10).execute()
        if result.data:
            print(f"📋 Sample jobs found: {len(result.data)}")
            for job in result.data[:3]:
                print(f"   Job ID: {job.get('job_id', 'unknown')[:12]}...")
                print(f"   Career Pathway: {job.get('career_pathway', 'NULL')}")
                print(f"   Classifier Type: {job.get('classifier_type', 'NULL')}")
                print()
        else:
            print("⚠️ No jobs found in database")
            return False

        # Count jobs without career_pathway
        count_result = client.table('jobs').select('job_id', count='exact').is_('career_pathway', 'null').execute()
        null_pathway_count = count_result.count if count_result.count is not None else 0

        print(f"📊 Jobs without career_pathway: {null_pathway_count}")

        # Count jobs with empty career_pathway
        empty_result = client.table('jobs').select('job_id', count='exact').eq('career_pathway', '').execute()
        empty_pathway_count = empty_result.count if empty_result.count is not None else 0

        print(f"📊 Jobs with empty career_pathway: {empty_pathway_count}")

        # Get total job count
        total_result = client.table('jobs').select('job_id', count='exact').execute()
        total_count = total_result.count if total_result.count is not None else 0

        print(f"📊 Total jobs in database: {total_count}")

        if null_pathway_count == 0 and empty_pathway_count == 0:
            print("✅ All jobs already have career_pathway set!")
            return True

        jobs_to_update = null_pathway_count + empty_pathway_count
        print(f"🎯 Will update {jobs_to_update} jobs to have 'cdl_pathway'")

        # Ask for confirmation
        response = input(f"\nUpdate {jobs_to_update} jobs with CDL pathway? (y/N): ")
        if response.lower() != 'y':
            print("❌ Update cancelled")
            return False

        # Update jobs with NULL career_pathway
        if null_pathway_count > 0:
            print(f"🔄 Updating {null_pathway_count} jobs with NULL career_pathway...")

            update_result = client.table('jobs').update({
                'career_pathway': 'cdl_pathway',
                'classifier_type': 'cdl'  # Also set classifier_type if not set
            }).is_('career_pathway', 'null').execute()

            if update_result.data:
                print(f"✅ Updated {len(update_result.data)} jobs with NULL career_pathway")
            else:
                print("⚠️ NULL update returned no data")

        # Update jobs with empty career_pathway
        if empty_pathway_count > 0:
            print(f"🔄 Updating {empty_pathway_count} jobs with empty career_pathway...")

            update_result = client.table('jobs').update({
                'career_pathway': 'cdl_pathway',
                'classifier_type': 'cdl'
            }).eq('career_pathway', '').execute()

            if update_result.data:
                print(f"✅ Updated {len(update_result.data)} jobs with empty career_pathway")
            else:
                print("⚠️ Empty update returned no data")

        # Verify the update
        print("🔍 Verifying updates...")

        verify_result = client.table('jobs').select('job_id', count='exact').eq('career_pathway', 'cdl_pathway').execute()
        cdl_pathway_count = verify_result.count if verify_result.count is not None else 0

        print(f"📊 Jobs now with 'cdl_pathway': {cdl_pathway_count}")

        # Check for remaining NULL/empty
        remaining_null = client.table('jobs').select('job_id', count='exact').is_('career_pathway', 'null').execute()
        remaining_empty = client.table('jobs').select('job_id', count='exact').eq('career_pathway', '').execute()

        remaining_null_count = remaining_null.count if remaining_null.count is not None else 0
        remaining_empty_count = remaining_empty.count if remaining_empty.count is not None else 0

        print(f"📊 Remaining NULL career_pathway: {remaining_null_count}")
        print(f"📊 Remaining empty career_pathway: {remaining_empty_count}")

        if remaining_null_count == 0 and remaining_empty_count == 0:
            print("✅ All jobs now have career_pathway classification!")
            return True
        else:
            print("⚠️ Some jobs still need career_pathway updates")
            return False

    except Exception as e:
        print(f"❌ Error updating database: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_pathway_distribution():
    """Show current distribution of career pathways in database"""

    print("📊 CAREER PATHWAY DISTRIBUTION")
    print("-" * 50)

    try:
        from supabase_utils import get_client

        client = get_client()
        if not client:
            print("❌ Supabase client not available")
            return

        # Get all distinct career pathways
        result = client.table('jobs').select('career_pathway').execute()

        if not result.data:
            print("⚠️ No jobs found in database")
            return

        # Count distribution
        pathway_counts = {}
        for job in result.data:
            pathway = job.get('career_pathway', 'NULL')
            if pathway == '':
                pathway = 'EMPTY'
            pathway_counts[pathway] = pathway_counts.get(pathway, 0) + 1

        # Sort by count
        sorted_pathways = sorted(pathway_counts.items(), key=lambda x: x[1], reverse=True)

        total_jobs = sum(pathway_counts.values())
        print(f"Total jobs: {total_jobs}")
        print()

        for pathway, count in sorted_pathways:
            percentage = (count / total_jobs) * 100
            print(f"{pathway:25} {count:6} ({percentage:5.1f}%)")

    except Exception as e:
        print(f"❌ Error getting pathway distribution: {e}")

def main():
    """Main function with menu"""

    print("🛤️ CDL PATHWAY POPULATION TOOL")
    print("=" * 40)
    print("1. Show current pathway distribution")
    print("2. Populate CDL pathways for existing jobs")
    print("3. Both")
    print()

    choice = input("Choose an option (1-3): ")

    if choice == "1":
        show_pathway_distribution()
    elif choice == "2":
        populate_cdl_pathways()
    elif choice == "3":
        show_pathway_distribution()
        print()
        populate_cdl_pathways()
        print()
        print("📊 UPDATED DISTRIBUTION:")
        show_pathway_distribution()
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()