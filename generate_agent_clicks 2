#!/usr/bin/env python3
"""
Generate realistic click data for Benjamin and O'Neal using their actual CSV files
"""

import pandas as pd
import random
import time
from datetime import datetime, timedelta
import requests

# Agent profiles with UUIDs
AGENTS = {
    "benjamin": {
        "uuid": "59bd7baa-1efb-11ef-937f-de2fe15254ef",
        "name": "Benjamin Bechtolsheim", 
        "csv": "/workspaces/freeworld-success-coach-portal/freeworld_jobs_Bay Area_20250829_061223.csv",
        "profile": "lazy",
        "click_rate": 0.15,      # Only clicks 15% of jobs
        "repeat_rate": 0.05,     # Rarely clicks same job twice
        "daily_activity": [0, 1] # 0-1 session per day
    },
    "oneal": {
        "uuid": "59b44837-1efb-11ef-937f-de2fe15254ef",
        "name": "O'Neal Heard",
        "csv": "/workspaces/freeworld-success-coach-portal/freeworld_jobs_Stockton_20250829_061025.csv", 
        "profile": "active",
        "click_rate": 0.85,      # Clicks 85% of jobs
        "repeat_rate": 0.35,     # Often clicks jobs multiple times  
        "daily_activity": [2, 5] # 2-5 sessions per day
    }
}

def load_agent_jobs(agent_key):
    """Load good/so-so jobs with short links for an agent"""
    agent = AGENTS[agent_key]
    df = pd.read_csv(agent['csv'])
    
    # Filter to good/so-so jobs with short links
    jobs = df[
        df['ai.match'].isin(['good', 'so-so']) & 
        df['meta.tracked_url'].notna() & 
        (df['meta.tracked_url'] != '')
    ]
    
    print(f"{agent['name']}: {len(jobs)} good/so-so jobs with short links")
    return jobs

def generate_week_timestamps():
    """Generate realistic timestamps over past 7 days"""
    now = datetime.now()
    timestamps = []
    
    for day in range(7):  # Past 7 days
        day_start = now - timedelta(days=day)
        
        # Random activity times (biased toward evenings/weekends) 
        activity_hours = [
            6,7,8,          # Morning (light)
            12,13,          # Lunch (medium)
            17,18,19,20,21, # Evening (heavy)
            22,23           # Night (medium)
        ]
        
        # More clicks on weekends
        if day_start.weekday() >= 5:  # Weekend
            daily_clicks = random.randint(3, 12)
        else:  # Weekday  
            daily_clicks = random.randint(1, 6)
            
        for _ in range(daily_clicks):
            hour = random.choice(activity_hours)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            timestamp = day_start.replace(hour=hour, minute=minute, second=second)
            timestamps.append(timestamp)
    
    return sorted(timestamps)

def simulate_realistic_clicks(agent_key):
    """Generate realistic click pattern for an agent"""
    agent = AGENTS[agent_key]
    jobs = load_agent_jobs(agent_key)
    
    if len(jobs) == 0:
        print(f"No jobs found for {agent['name']}")
        return []
    
    # Select jobs to click based on profile
    num_to_click = int(len(jobs) * agent['click_rate'])
    jobs_to_click = jobs.sample(n=min(num_to_click, len(jobs)))
    
    print(f"{agent['name']} will click {len(jobs_to_click)} out of {len(jobs)} jobs ({agent['click_rate']*100:.0f}%)")
    
    # Generate timestamps
    all_timestamps = generate_week_timestamps()
    
    click_events = []
    
    for _, job in jobs_to_click.iterrows():
        # Determine how many times to click this job
        click_count = 1
        if random.random() < agent['repeat_rate']:
            click_count = random.randint(2, 4)  # 2-4 repeat clicks
        
        # Assign timestamps for this job
        job_timestamps = random.sample(all_timestamps, min(len(all_timestamps), click_count))
        
        for timestamp in job_timestamps:
            click_events.append({
                'agent': agent['name'],
                'uuid': agent['uuid'],
                'job_title': job['source.title'],
                'company': job['source.company'],
                'short_link': job['meta.tracked_url'],
                'timestamp': timestamp,
                'match_quality': job['ai.match']
            })
    
    # Sort by timestamp
    click_events.sort(key=lambda x: x['timestamp'])
    
    print(f"Generated {len(click_events)} click events for {agent['name']}")
    return click_events

def execute_click_events(click_events, dry_run=True):
    """Execute the click events (or show what would be executed)"""
    print(f"\n{'🔍 DRY RUN:' if dry_run else '🚀 EXECUTING:'} {len(click_events)} click events")
    
    for i, event in enumerate(click_events, 1):
        timestamp_str = event['timestamp'].strftime('%m/%d %H:%M')
        agent_name = event['agent'][:8]
        job_title = event['job_title'][:40]
        
        print(f"  [{i:3d}] {timestamp_str} | {agent_name} -> {job_title}... ({event['match_quality']})")
        
        if not dry_run:
            try:
                # Make HEAD request to trigger click tracking
                headers = {
                    'User-Agent': f'FreeWorldApp/1.0 ({event["agent"]} Click Simulation)',
                    'X-Agent-UUID': event['uuid']
                }
                response = requests.head(event['short_link'], timeout=5, headers=headers, allow_redirects=False)
                print(f"    ✅ {response.status_code}")
                time.sleep(0.2)  # Small delay
            except Exception as e:
                print(f"    ❌ {e}")

def main():
    print("🎬 FreeWorld Agent Click Simulator")
    print("=" * 50)
    
    # Generate clicks for both agents
    benjamin_clicks = simulate_realistic_clicks('benjamin')
    oneal_clicks = simulate_realistic_clicks('oneal')
    
    # Combine and sort all events
    all_clicks = benjamin_clicks + oneal_clicks
    all_clicks.sort(key=lambda x: x['timestamp'])
    
    print(f"\n📊 SUMMARY:")
    print(f"  Benjamin: {len(benjamin_clicks)} clicks (lazy profile)")
    print(f"  O'Neal:   {len(oneal_clicks)} clicks (active profile)")  
    print(f"  Total:    {len(all_clicks)} clicks over 7 days")
    
    # Show dry run
    execute_click_events(all_clicks, dry_run=True)
    
    # Execute the wet run
    print("🎯 Executing click simulation...")
    execute_click_events(all_clicks, dry_run=False)
    print("✅ Click simulation completed!")

if __name__ == "__main__":
    main()