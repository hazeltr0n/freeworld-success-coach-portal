"""
Top-level async polling helper that avoids editing vendored core code.
Polls pending Google and Indeed async jobs each call and processes completed ones
using the AsyncJobManager.
"""

from typing import Optional, Tuple

def poll_pending_jobs(coach_username: Optional[str] = None, max_checks: int = 50) -> Tuple[int, int, int]:
    """Poll pending Google and Indeed Jobs and process completed ones.

    Returns (processed, still_pending, failed)
    """
    try:
        from async_job_manager import AsyncJobManager  # Prefer top-level manager
    except Exception:
        return (0, 0, 0)

    mgr = AsyncJobManager()
    processed = 0
    pending = 0
    failed = 0
    try:
        jobs = mgr.get_pending_jobs(coach_username)
        for job in jobs[:max_checks]:
            if job.job_type not in ['google_jobs', 'indeed_jobs'] or not job.request_id:
                pending += 1
                continue
            res = mgr.get_async_results(job.request_id)
            if not res:
                # Mark as processing to reflect progress in UI
                try:
                    if job.status == 'submitted':
                        mgr.update_job(job.id, {'status': 'processing'})
                except Exception:
                    pass
                pending += 1
                continue
            status = str(res.get('status', '')).lower()
            if status in ['completed', 'success', 'finished']:
                try:
                    mgr.process_completed_async_job(job.id)
                    processed += 1
                except Exception:
                    failed += 1
            elif status in ['failed', 'error']:
                try:
                    mgr.update_job(job.id, {
                        'status': 'failed',
                        'error_message': res.get('error', 'Outscraper reported failure')
                    })
                except Exception:
                    pass
                failed += 1
            else:
                pending += 1
    except Exception:
        pass
    return (processed, pending, failed)
