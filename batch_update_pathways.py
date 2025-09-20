#!/usr/bin/env python3
"""
Batch update CDL jobs from 'cdl' to 'cdl_pathway' in smaller chunks
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def batch_update_cdl_pathways(batch_size=100):
    """Update CDL jobs in batches to avoid timeout"""

    try:
        from supabase_utils import get_client

        client = get_client()
        if not client:
            print("❌ Supabase client not available")
            return False

        print(f"🔄 Batch updating CDL jobs from 'cdl' to 'cdl_pathway' in chunks of {batch_size}...")

        total_updated = 0
        batch_num = 0

        while True:
            batch_num += 1
            print(f"\n📦 Processing batch {batch_num}...")

            # Get a batch of jobs with career_pathway = 'cdl'
            result = client.table('jobs').select('job_id').eq('career_pathway', 'cdl').limit(batch_size).execute()

            if not result.data or len(result.data) == 0:
                print("✅ No more jobs to update!")
                break

            batch_jobs = result.data
            print(f"   Found {len(batch_jobs)} jobs in this batch")

            # Get the job_ids for this batch
            job_ids = [job['job_id'] for job in batch_jobs]

            # Update this batch
            update_result = client.table('jobs').update({
                'career_pathway': 'cdl_pathway'
            }).in_('job_id', job_ids).execute()

            if update_result.data:
                updated_count = len(update_result.data)
                total_updated += updated_count
                print(f"   ✅ Updated {updated_count} jobs in batch {batch_num}")
            else:
                print(f"   ⚠️ No jobs updated in batch {batch_num}")

            # Small delay to avoid overwhelming the database
            time.sleep(0.5)

            # Safety check - don't run forever
            if batch_num > 100:
                print("⚠️ Safety limit reached (100 batches), stopping")
                break

        print(f"\n🎉 Batch update completed!")
        print(f"📊 Total jobs updated: {total_updated}")

        # Verify the results
        cdl_remaining = client.table('jobs').select('job_id', count='exact').eq('career_pathway', 'cdl').execute()
        cdl_pathway_count = client.table('jobs').select('job_id', count='exact').eq('career_pathway', 'cdl_pathway').execute()

        remaining = cdl_remaining.count if cdl_remaining.count is not None else 0
        updated_total = cdl_pathway_count.count if cdl_pathway_count.count is not None else 0

        print(f"📈 Final results:")
        print(f"   Jobs with 'cdl_pathway': {updated_total}")
        print(f"   Jobs still with 'cdl': {remaining}")

        if remaining == 0:
            print("✅ All CDL jobs successfully updated to 'cdl_pathway'!")
        else:
            print(f"⚠️ {remaining} jobs still need updating")

        return True

    except Exception as e:
        print(f"❌ Error in batch update: {e}")
        return False

if __name__ == "__main__":
    batch_update_cdl_pathways()