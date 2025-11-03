#!/usr/bin/env python3
"""
Fix Google JSON array URLs in Supabase

Finds all jobs with malformed Google URLs (JSON arrays) and extracts the first valid URL.
Prioritizes direct company websites over job boards.
"""

import json
import re
from typing import Optional
from supabase_utils import get_client


def extract_url_from_google_format(url_string: str) -> Optional[str]:
    """
    Extract first valid URL from Google's JSON array format

    Args:
        url_string: Either a normal URL or Google JSON array like:
                   [{'apply_url:': 'https://...', 'apply_company': 'ZipRecruiter'}, ...]

    Returns:
        Clean URL string, or None if parsing fails
    """
    # If it's already a normal URL, return it
    if not isinstance(url_string, str):
        return None

    if not url_string.startswith('[{'):
        # Already a normal URL
        return url_string

    try:
        # Try parsing as JSON first
        url_data = json.loads(url_string)

        if not url_data or len(url_data) == 0:
            return None

        # Prioritize direct company websites over job boards
        job_boards = {'Indeed', 'LinkedIn', 'SimplyHired', 'ZipRecruiter', 'Monster',
                     'Glassdoor', 'CareerBuilder', 'Snagajob', 'WhatJobs', 'JobGet'}

        # First pass: look for non-job-board URLs
        for url_obj in url_data:
            if isinstance(url_obj, dict):
                apply_company = url_obj.get('apply_company', '')
                if apply_company not in job_boards:
                    url = url_obj.get('apply_url:', '') or url_obj.get('apply_url', '')
                    if url and url.startswith(('http://', 'https://')):
                        print(f"      🏢 Prioritizing direct company: {apply_company}")
                        return url

        # Second pass: use first available URL (likely a job board)
        first_url_obj = url_data[0]
        if isinstance(first_url_obj, dict):
            url = first_url_obj.get('apply_url:', '') or first_url_obj.get('apply_url', '')
            apply_company = first_url_obj.get('apply_company', 'Unknown')
            if url and url.startswith(('http://', 'https://')):
                print(f"      📋 Using job board: {apply_company}")
                return url

        return None

    except json.JSONDecodeError:
        # If JSON parsing fails, try regex extraction as fallback
        match = re.search(r"'apply_url:?':\s*'([^']+)'", url_string)
        if match:
            extracted_url = match.group(1)
            if extracted_url.startswith(('http://', 'https://')):
                print(f"      🔧 Extracted via regex")
                return extracted_url

        return None
    except Exception as e:
        print(f"      ❌ Error parsing URL: {e}")
        return None


def fix_google_urls():
    """Fix all Google JSON array URLs in Supabase"""

    client = get_client()
    if not client:
        print("❌ Could not connect to Supabase")
        return

    print(f"\n{'='*80}")
    print(f"🔧 FIXING GOOGLE URLS IN SUPABASE")
    print(f"{'='*80}\n")

    # Find all jobs with malformed URLs (starts with '[{')
    print("📋 Searching for jobs with malformed Google URLs...")

    try:
        # Query 1: Jobs where tracked_url starts with '[{' (malformed JSON arrays)
        print("📋 Searching for malformed JSON array URLs...")
        result1 = client.table('jobs')\
            .select('job_id, tracked_url')\
            .like('tracked_url', '[{%')\
            .execute()

        malformed_urls = result1.data or []
        print(f"   Found {len(malformed_urls)} jobs with JSON array URLs")

        # Query 2: Jobs where tracked_url is NULL or empty
        print("📋 Searching for empty tracked URLs...")
        result2 = client.table('jobs')\
            .select('job_id, tracked_url')\
            .is_('tracked_url', 'null')\
            .execute()

        result3 = client.table('jobs')\
            .select('job_id, tracked_url')\
            .eq('tracked_url', '')\
            .execute()

        empty_urls = (result2.data or []) + (result3.data or [])
        print(f"   Found {len(empty_urls)} jobs with empty tracked URLs")

        # Combine both lists
        jobs_to_fix = malformed_urls + empty_urls

        if not jobs_to_fix:
            print("✅ No URLs need fixing! All URLs are clean.")
            return

        print(f"\n🔍 Total jobs to fix: {len(jobs_to_fix)}\n")

        fixed_count = 0
        failed_count = 0

        for i, job in enumerate(jobs_to_fix, 1):
            job_id = job['job_id']
            malformed_url = job.get('tracked_url', '')

            print(f"[{i}/{len(jobs_to_fix)}] Processing job {job_id[:8]}...")

            clean_url = None

            # Case 1: Empty or NULL tracked_url - need to fetch apply_url from job
            if not malformed_url or malformed_url in ['', 'null', None]:
                print(f"      Empty tracked_url - fetching apply_url from database...")

                # Fetch the job's apply_url field
                job_data = client.table('jobs')\
                    .select('apply_url')\
                    .eq('job_id', job_id)\
                    .execute()

                if job_data.data and len(job_data.data) > 0:
                    apply_url = job_data.data[0].get('apply_url', '')

                    if apply_url:
                        # Check if apply_url is also malformed
                        if apply_url.startswith('[{'):
                            clean_url = extract_url_from_google_format(apply_url)
                            if clean_url:
                                print(f"      🔧 Extracted from malformed apply_url")
                        else:
                            clean_url = apply_url
                            print(f"      ✅ Using clean apply_url")
                    else:
                        print(f"      ❌ No apply_url available")
                else:
                    print(f"      ❌ Job not found in database")

            # Case 2: Malformed JSON array URL
            elif malformed_url.startswith('[{'):
                print(f"      Original: {malformed_url[:80]}...")
                clean_url = extract_url_from_google_format(malformed_url)

            # Case 3: Already clean URL
            else:
                print(f"      Already clean URL, skipping")
                continue

            # Update if we got a clean URL
            if clean_url and clean_url.startswith(('http://', 'https://')):
                update_data = {'tracked_url': clean_url}
                client.table('jobs').update(update_data).eq('job_id', job_id).execute()
                print(f"      ✅ Fixed: {clean_url[:80]}...")
                fixed_count += 1
            else:
                print(f"      ❌ Could not extract valid URL")
                failed_count += 1

            print()

        print(f"\n{'='*80}")
        print(f"📊 SUMMARY")
        print(f"{'='*80}")
        print(f"✅ Fixed: {fixed_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📝 Total processed: {len(jobs_to_fix)}")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"❌ Error during URL fix: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    fix_google_urls()
