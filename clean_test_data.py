#!/usr/bin/env python3
"""
Clean up test click events from Supabase.

Usage:
    python clean_test_data.py --confirm
    python clean_test_data.py --older-than-days 7 --confirm
"""

import argparse
from datetime import datetime, timedelta, timezone
from supabase_utils import get_client


def clean_test_click_events(older_than_days: int = None, confirm: bool = False) -> bool:
    """Remove test click events from Supabase"""
    client = get_client()
    if not client:
        print("❌ Could not connect to Supabase. Check credentials.")
        return False
    
    try:
        # Build query
        query = client.table("click_events")
        
        if older_than_days:
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).isoformat()
            query = query.lt("clicked_at", cutoff_date)
            print(f"🔍 Targeting click events older than {older_than_days} days (before {cutoff_date})")
        else:
            print("🔍 Targeting ALL click events")
        
        # First, count what we'll delete
        count_result = query.select("short_id", count="exact").execute()
        count = getattr(count_result, 'count', 0)
        
        if count == 0:
            print("✅ No click events found to delete")
            return True
        
        print(f"⚠️  Found {count} click events to delete")
        
        if not confirm:
            print("❌ Add --confirm flag to proceed with deletion")
            return False
        
        # Delete the events
        print("🗑️ Deleting click events...")
        result = query.delete().execute()
        
        print(f"✅ Successfully deleted click events")
        return True
    
    except Exception as e:
        print(f"❌ Failed to clean click events: {e}")
        return False


def clean_test_candidate_clicks(confirm: bool = False) -> bool:
    """Remove test candidate click totals"""
    client = get_client()
    if not client:
        return False
    
    try:
        # Count candidates to delete
        count_result = client.table("candidate_clicks").select("candidate_id", count="exact").execute()
        count = getattr(count_result, 'count', 0)
        
        if count == 0:
            print("✅ No candidate click records found to delete")
            return True
        
        print(f"⚠️  Found {count} candidate click records to delete")
        
        if not confirm:
            print("❌ Add --confirm flag to proceed with deletion")
            return False
        
        print("🗑️ Deleting candidate click records...")
        result = client.table("candidate_clicks").delete().neq("candidate_id", "").execute()
        
        print(f"✅ Successfully deleted candidate click records")
        return True
    
    except Exception as e:
        print(f"❌ Failed to clean candidate clicks: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Clean up test data from Supabase")
    parser.add_argument("--older-than-days", type=int,
                       help="Only delete events older than N days")
    parser.add_argument("--confirm", action="store_true",
                       help="Confirm deletion (required to actually delete)")
    parser.add_argument("--events-only", action="store_true",
                       help="Only clean click events, not candidate totals")
    
    args = parser.parse_args()
    
    print("🧹 FreeWorld Test Data Cleanup")
    print("="*40)
    
    if not args.confirm:
        print("⚠️  DRY RUN MODE - No data will be deleted")
        print("   Add --confirm flag to actually delete data")
        print()
    
    # Clean click events
    events_success = clean_test_click_events(args.older_than_days, args.confirm)
    
    # Clean candidate clicks (unless events-only)
    candidates_success = True
    if not args.events_only:
        candidates_success = clean_test_candidate_clicks(args.confirm)
    
    if events_success and candidates_success:
        if args.confirm:
            print("\n🎉 Cleanup completed successfully!")
        else:
            print("\n💡 Run with --confirm to actually delete the data")
    else:
        print("\n❌ Some cleanup operations failed")


if __name__ == "__main__":
    main()