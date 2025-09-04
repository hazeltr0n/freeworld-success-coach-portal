#!/usr/bin/env python3
"""
Generate test click events in Supabase to simulate Free Agent engagement.

This script creates realistic click data for testing analytics dashboard and
demonstrating system functionality.

Usage:
    python generate_test_clicks.py --count 50
    python generate_test_clicks.py --count 100 --days-back 30
"""

import argparse
import json
import random
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict

try:
    from supabase_utils import get_client
except ImportError:
    print("Error: Could not import supabase_utils. Make sure it's in the same directory.")
    exit(1)


class ClickEventGenerator:
    """Generate realistic click events for Free Agents"""
    
    def __init__(self):
        # Realistic Free Agent names and profiles
        self.free_agents = [
            {"id": "FA001-2024", "name": "Marcus Johnson", "location": "Dallas, TX"},
            {"id": "FA002-2024", "name": "James Rodriguez", "location": "Houston, TX"},
            {"id": "FA003-2024", "name": "David Thompson", "location": "Dallas, TX"},
            {"id": "FA004-2024", "name": "Michael Davis", "location": "Fort Worth, TX"},
            {"id": "FA005-2024", "name": "Robert Wilson", "location": "Houston, TX"},
            {"id": "FA006-2024", "name": "Christopher Brown", "location": "San Antonio, TX"},
            {"id": "FA007-2024", "name": "Antonio Martinez", "location": "Dallas, TX"},
            {"id": "FA008-2024", "name": "Kevin Anderson", "location": "Houston, TX"},
            {"id": "FA009-2024", "name": "Luis Garcia", "location": "Austin, TX"},
            {"id": "FA010-2024", "name": "Thomas Lee", "location": "Dallas, TX"},
            {"id": "FA011-2024", "name": "Carlos Hernandez", "location": "Houston, TX"},
            {"id": "FA012-2024", "name": "Daniel White", "location": "Plano, TX"},
            {"id": "FA013-2024", "name": "Jose Lopez", "location": "Irving, TX"},
            {"id": "FA014-2024", "name": "Matthew Taylor", "location": "Garland, TX"},
            {"id": "FA015-2024", "name": "Anthony Clark", "location": "Mesquite, TX"},
        ]
        
        # Coaching staff
        self.coaches = [
            "hazeltr0n", "admin", "sarah.jones", "mike.thompson", "jessica.davis"
        ]
        
        # Markets where jobs are posted
        self.markets = ["Dallas", "Houston", "Austin", "San Antonio", "Fort Worth"]
        
        # Route types for CDL jobs
        self.route_types = ["local", "regional", "otr"]
        
        # Match quality levels
        self.match_levels = ["good", "so-so", "bad"]
        
        # Fair chance status
        self.fair_chance = [True, False]
        
        # Companies hiring
        self.companies = [
            "Southwest Logistics", "Texas Freight Co", "Lone Star Transport",
            "Dallas Delivery Solutions", "Houston Hauling", "Austin Express",
            "FreeWorld Partner Co", "Elite Trucking TX", "Premier Transport",
            "Reliable Routes LLC", "Quick Cargo Inc", "Texas Truck Lines"
        ]
    
    def generate_click_events(self, count: int, days_back: int = 7) -> List[Dict]:
        """Generate realistic click events"""
        events = []
        now = datetime.now(timezone.utc)
        
        for i in range(count):
            # Random time in the last N days (weighted toward recent)
            days_ago = random.triangular(0, days_back, 0)  # More recent events more likely
            clicked_at = now - timedelta(days=days_ago, 
                                        hours=random.randint(0, 23),
                                        minutes=random.randint(0, 59))
            
            # Select random Free Agent (some Free Agents click more than others)
            agent = random.choices(
                self.free_agents, 
                weights=[3, 2, 4, 1, 3, 1, 2, 3, 1, 4, 2, 2, 1, 2, 1], 
                k=1
            )[0]
            
            # Select coach (hazeltr0n gets most activity)
            coach = random.choices(
                self.coaches,
                weights=[40, 10, 15, 20, 15],  # hazeltr0n gets 40% of clicks
                k=1
            )[0]
            
            # Generate realistic job data
            market = random.choices(
                self.markets,
                weights=[35, 30, 15, 10, 10],  # Dallas and Houston most active
                k=1
            )[0]
            
            route_type = random.choices(
                self.route_types,
                weights=[50, 30, 20],  # Local routes most popular
                k=1
            )[0]
            
            match_level = random.choices(
                self.match_levels,
                weights=[60, 25, 15],  # Most clicks on good jobs
                k=1
            )[0]
            
            fair = random.choice(self.fair_chance)
            company = random.choice(self.companies)
            
            # Create unique short ID
            short_id = f"fw{clicked_at.strftime('%m%d')}{random.randint(100, 999)}"
            
            # Create click event
            event = {
                "short_id": short_id,
                "clicked_at": clicked_at.isoformat(),
                "coach": coach,
                "market": market,
                "route": route_type,
                "match": match_level,
                "fair": fair,
                "candidate_id": agent["id"],
                "candidate_name": agent["name"],
                "candidate_location": agent["location"],
                "company": company,
                "original_url": f"https://indeed.com/viewjob?jk={random.randint(100000, 999999)}",
                "user_agent": "Mozilla/5.0 (Mobile; Free Agent App)",
                "referrer": "https://freeworld.org"
            }
            
            events.append(event)
        
        # Sort by timestamp (oldest first for realistic insertion)
        events.sort(key=lambda x: x["clicked_at"])
        return events
    
    def generate_candidate_clicks(self, events: List[Dict]) -> List[Dict]:
        """Generate candidate click aggregates from events"""
        candidate_totals = {}
        
        for event in events:
            candidate_id = event["candidate_id"]
            candidate_name = event["candidate_name"]
            
            if candidate_id not in candidate_totals:
                candidate_totals[candidate_id] = {
                    "candidate_id": candidate_id,
                    "candidate_name": candidate_name,
                    "clicks": 0,
                    "last_click": event["clicked_at"]
                }
            
            candidate_totals[candidate_id]["clicks"] += 1
            # Update last_click if this event is more recent
            if event["clicked_at"] > candidate_totals[candidate_id]["last_click"]:
                candidate_totals[candidate_id]["last_click"] = event["clicked_at"]
        
        return list(candidate_totals.values())


def insert_click_events(events: List[Dict]) -> bool:
    """Insert click events into Supabase"""
    client = get_client()
    if not client:
        print("❌ Could not connect to Supabase. Check SUPABASE_URL and SUPABASE_ANON_KEY.")
        return False
    
    try:
        print(f"📤 Inserting {len(events)} click events...")
        
        # Insert in batches to avoid timeouts
        batch_size = 50
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            result = client.table("click_events").insert(batch).execute()
            
            if hasattr(result, 'data') and result.data:
                print(f"   ✅ Inserted batch {i//batch_size + 1}: {len(batch)} events")
            else:
                print(f"   ⚠️ Batch {i//batch_size + 1} may have failed")
            
            # Small delay between batches
            time.sleep(0.2)
        
        print(f"✅ Successfully inserted {len(events)} click events")
        return True
    
    except Exception as e:
        print(f"❌ Failed to insert click events: {e}")
        return False


def insert_candidate_clicks(candidates: List[Dict]) -> bool:
    """Insert/update candidate click totals in Supabase"""
    client = get_client()
    if not client:
        print("❌ Could not connect to Supabase.")
        return False
    
    try:
        print(f"📤 Upserting {len(candidates)} candidate click totals...")
        
        result = client.table("candidate_clicks").upsert(
            candidates, 
            on_conflict="candidate_id"
        ).execute()
        
        if hasattr(result, 'data') and result.data:
            print(f"✅ Successfully updated {len(result.data)} candidate records")
        else:
            print("✅ Candidate clicks updated")
        
        return True
    
    except Exception as e:
        print(f"❌ Failed to insert candidate clicks: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate test click events for FreeWorld")
    parser.add_argument("--count", type=int, default=100, 
                       help="Number of click events to generate (default: 100)")
    parser.add_argument("--days-back", type=int, default=30,
                       help="Generate clicks from last N days (default: 30)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show events that would be created without inserting")
    
    args = parser.parse_args()
    
    print("🎯 FreeWorld Test Click Event Generator")
    print("="*50)
    print(f"Generating {args.count} click events from last {args.days_back} days")
    print()
    
    generator = ClickEventGenerator()
    
    # Generate events
    print("🔄 Generating click events...")
    events = generator.generate_click_events(args.count, args.days_back)
    
    # Generate candidate aggregates
    print("🔄 Calculating candidate click totals...")
    candidates = generator.generate_candidate_clicks(events)
    
    if args.dry_run:
        print("📋 DRY RUN - Sample events that would be created:")
        print("\n--- Sample Click Events ---")
        for event in events[:5]:
            print(json.dumps(event, indent=2, default=str))
        
        print(f"\n--- Candidate Totals ({len(candidates)} total) ---")
        for candidate in sorted(candidates, key=lambda x: x["clicks"], reverse=True)[:5]:
            print(f"{candidate['candidate_name']}: {candidate['clicks']} clicks")
        
        print(f"\n📊 Would create {len(events)} events and update {len(candidates)} candidates")
        return
    
    # Insert into Supabase
    print("💾 Inserting into Supabase...")
    
    events_success = insert_click_events(events)
    candidates_success = insert_candidate_clicks(candidates)
    
    if events_success and candidates_success:
        print("\n🎉 SUCCESS! Test data created successfully")
        print(f"📊 Created {len(events)} click events for {len(candidates)} Free Agents")
        
        # Show top clickers
        top_clickers = sorted(candidates, key=lambda x: x["clicks"], reverse=True)[:5]
        print("\n🏆 Top Free Agents by clicks:")
        for i, candidate in enumerate(top_clickers, 1):
            print(f"   {i}. {candidate['candidate_name']}: {candidate['clicks']} clicks")
        
        print(f"\n💡 View analytics in the Streamlit app admin panel!")
    else:
        print("\n❌ Some operations failed. Check the error messages above.")


if __name__ == "__main__":
    main()