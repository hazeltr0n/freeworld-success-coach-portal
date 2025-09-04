#!/usr/bin/env python3
"""
Generate realistic click data for Free Agents to test click analytics
Creates a week-long pattern of job application activity
"""

import os
import random
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

load_dotenv()

# Free Agent profiles
FREE_AGENTS = {
    "benjamin": {
        "uuid": "59bd7baa-1efb-11ef-937f-de2fe15254ef",
        "name": "Benjamin Bechtolsheim",
        "profile": "lazy",  # Clicks few jobs, inconsistent pattern
        "click_rate": 0.15,  # Clicks only 15% of available jobs
        "repeat_rate": 0.05,  # Rarely clicks same job multiple times
        "daily_sessions": [0, 1],  # 0-1 sessions per day
        "session_length": [2, 8]   # 2-8 jobs per session
    },
    "oneal": {
        "uuid": "59b44837-1efb-11ef-937f-de2fe15254ef", 
        "name": "O'Neal Heard",
        "profile": "active",  # Clicks tons of jobs, very engaged
        "click_rate": 0.85,  # Clicks 85% of available jobs
        "repeat_rate": 0.35,  # Often clicks same job multiple times
        "daily_sessions": [2, 5],  # 2-5 sessions per day
        "session_length": [8, 25]  # 8-25 jobs per session
    }
}

def get_supabase_client():
    """Initialize Supabase client"""
    from supabase import create_client
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError("Missing Supabase credentials in .env file")
    
    return create_client(supabase_url, supabase_key)

def get_job_links_for_agent(agent_uuid):
    """Get job links for a specific agent from Supabase"""
    supabase = get_supabase_client()
    
    # Get jobs for this agent
    response = supabase.table('jobs').select('*').eq('free_agent_uuid', agent_uuid).execute()
    
    jobs = response.data if response.data else []
    print(f"Found {len(jobs)} jobs for agent {agent_uuid}")
    
    # Extract short links
    job_links = []
    for job in jobs:
        if job.get('short_link'):
            job_links.append({
                'job_id': job['job_id'],
                'short_link': job['short_link'],
                'title': job.get('title', 'Unknown Job'),
                'company': job.get('company', 'Unknown Company')
            })
    
    print(f"Found {len(job_links)} jobs with short links")
    return job_links

def generate_click_timestamps(days_back=7):
    """Generate realistic timestamps over the past week"""
    now = datetime.now()
    timestamps = []
    
    for day in range(days_back):
        # Generate clicks throughout each day
        day_start = now - timedelta(days=day)
        
        # Random times throughout the day (biased toward evening/weekend activity)
        for _ in range(random.randint(0, 8)):  # 0-8 clicks per day
            hour = random.choices(
                range(24),
                weights=[1,1,1,1,1,2,3,4,5,6,7,8,8,9,10,12,14,16,18,20,15,12,8,4]
            )[0]
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            timestamp = day_start.replace(hour=hour, minute=minute, second=second)
            timestamps.append(timestamp)
    
    return sorted(timestamps)

def simulate_click(short_link, agent_info, timestamp):
    """Simulate a click on a short link at specific timestamp"""
    try:
        # Make HTTP request to short link (this should trigger tracking)
        headers = {
            'User-Agent': f'FreeWorldApp/1.0 ({agent_info["name"]} Testing)',
            'X-Timestamp': timestamp.isoformat()
        }
        
        # Don't actually follow redirects to avoid spamming Indeed
        response = requests.head(short_link, allow_redirects=False, timeout=5, headers=headers)
        
        return {
            'success': True,
            'status': response.status_code,
            'timestamp': timestamp
        }
        
    except Exception as e:
        print(f"Error clicking {short_link}: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': timestamp
        }

def generate_realistic_activity(agent_key, job_links):
    """Generate realistic click activity for an agent"""
    agent = FREE_AGENTS[agent_key]
    print(f"\n🎯 Generating clicks for {agent['name']} ({agent['profile']} profile)")
    
    # Generate base timestamps
    all_timestamps = generate_click_timestamps(days_back=7)
    
    # Select jobs to click based on agent profile
    jobs_to_click = random.sample(
        job_links, 
        min(len(job_links), int(len(job_links) * agent['click_rate']))
    )
    
    print(f"   📊 Will click {len(jobs_to_click)} out of {len(job_links)} jobs ({agent['click_rate']*100:.0f}%)")
    
    click_events = []
    
    for job in jobs_to_click:
        # Number of times to click this job
        click_count = 1
        if random.random() < agent['repeat_rate']:
            click_count = random.randint(2, 5)  # Multiple clicks
        
        # Assign timestamps for this job
        job_timestamps = random.sample(all_timestamps, min(len(all_timestamps), click_count))
        
        for timestamp in job_timestamps:
            click_events.append({
                'job': job,
                'timestamp': timestamp,
                'agent': agent
            })
    
    # Sort by timestamp
    click_events.sort(key=lambda x: x['timestamp'])
    
    print(f"   🖱️  Generated {len(click_events)} total click events")
    return click_events

def execute_click_simulation(click_events, dry_run=True):
    """Execute the click simulation"""
    print(f"\n🚀 {'DRY RUN:' if dry_run else 'EXECUTING:'} {len(click_events)} click events")
    
    successful_clicks = 0
    failed_clicks = 0
    
    for i, event in enumerate(click_events, 1):
        job = event['job']
        timestamp = event['timestamp']
        agent = event['agent']
        
        print(f"   [{i:3d}/{len(click_events)}] {timestamp.strftime('%m/%d %H:%M')} - "
              f"{agent['name'][:10]} -> {job['title'][:30]}...")
        
        if not dry_run:
            result = simulate_click(job['short_link'], agent, timestamp)
            if result['success']:
                successful_clicks += 1
            else:
                failed_clicks += 1
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
    
    if not dry_run:
        print(f"\n✅ Completed: {successful_clicks} successful, {failed_clicks} failed")
    else:
        print(f"\n📋 Dry run completed - would execute {len(click_events)} clicks")

def main():
    """Main execution function"""
    print("🎬 FreeWorld Click Data Generator")
    print("=" * 50)
    
    # Get job links for both agents
    benjamin_jobs = get_job_links_for_agent(FREE_AGENTS['benjamin']['uuid'])
    oneal_jobs = get_job_links_for_agent(FREE_AGENTS['oneal']['uuid'])
    
    if not benjamin_jobs and not oneal_jobs:
        print("❌ No jobs found for either agent. Make sure they have job lists generated first.")
        return
    
    # Generate click patterns
    all_click_events = []
    
    if benjamin_jobs:
        benjamin_clicks = generate_realistic_activity('benjamin', benjamin_jobs)
        all_click_events.extend(benjamin_clicks)
    
    if oneal_jobs:
        oneal_clicks = generate_realistic_activity('oneal', oneal_jobs)
        all_click_events.extend(oneal_clicks)
    
    # Sort all events by timestamp
    all_click_events.sort(key=lambda x: x['timestamp'])
    
    # Show summary
    print(f"\n📈 SUMMARY:")
    print(f"   Benjamin: {len([e for e in all_click_events if e['agent']['name'].startswith('Benjamin')])} clicks")
    print(f"   O'Neal:   {len([e for e in all_click_events if e['agent']['name'].startswith('O')])} clicks")
    print(f"   Total:    {len(all_click_events)} clicks over 7 days")
    
    # Execute dry run first
    execute_click_simulation(all_click_events, dry_run=True)
    
    # Ask for confirmation
    response = input("\n🤔 Execute real clicks? (y/N): ").strip().lower()
    if response == 'y':
        print("🎯 Executing real click simulation...")
        execute_click_simulation(all_click_events, dry_run=False)
    else:
        print("🛑 Cancelled - no real clicks generated")

if __name__ == "__main__":
    main()