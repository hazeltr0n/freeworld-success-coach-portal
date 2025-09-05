#!/usr/bin/env python3
"""
Demo Data Generator for FreeWorld Link Analytics
Creates realistic sample data to showcase the analytics dashboard
"""

import sys
import os
sys.path.append('src')

from link_tracker import LinkTracker
from analytics_dashboard import AnalyticsDashboard
import json
from datetime import datetime, timedelta
import random
import time

def create_sample_job_links():
    """Create a variety of realistic job links for demonstration"""
    
    # Sample job data representing real CDL opportunities
    sample_jobs = [
        # Dallas Market - Local Routes
        {
            'url': 'https://www.indeed.com/viewjob?jk=dallas_local_001',
            'title': 'CDL Class A Driver - Local Deliveries Dallas',
            'company': 'FreeWorld Logistics',
            'market': 'Dallas',
            'route_type': 'Local',
            'match': 'good'
        },
        {
            'url': 'https://www.indeed.com/viewjob?jk=dallas_local_002',
            'title': 'Local CDL Driver - Home Daily',
            'company': 'Texas Transport Co',
            'market': 'Dallas',
            'route_type': 'Local',
            'match': 'good'
        },
        {
            'url': 'https://www.indeed.com/viewjob?jk=dallas_local_003',
            'title': 'Dedicated Route Driver - Dallas Metro',
            'company': 'Metro Freight Solutions',
            'market': 'Dallas',
            'route_type': 'Local',
            'match': 'so-so'
        },
        
        # Houston Market - Mixed Routes
        {
            'url': 'https://www.indeed.com/viewjob?jk=houston_otr_001',
            'title': 'OTR Driver - Premium Miles Houston',
            'company': 'Gulf Coast Trucking',
            'market': 'Houston',
            'route_type': 'OTR',
            'match': 'good'
        },
        {
            'url': 'https://www.indeed.com/viewjob?jk=houston_local_001',
            'title': 'Local CDL Driver - Port of Houston',
            'company': 'Houston Logistics Hub',
            'market': 'Houston',
            'route_type': 'Local',
            'match': 'good'
        },
        {
            'url': 'https://www.indeed.com/viewjob?jk=houston_otr_002',
            'title': 'Regional OTR - Texas Routes',
            'company': 'Lone Star Transport',
            'market': 'Houston',
            'route_type': 'OTR',
            'match': 'so-so'
        },
        
        # Phoenix Market
        {
            'url': 'https://www.indeed.com/viewjob?jk=phoenix_local_001',
            'title': 'CDL Driver - Local Phoenix Delivery',
            'company': 'Desert Express',
            'market': 'Phoenix',
            'route_type': 'Local',
            'match': 'good'
        },
        {
            'url': 'https://www.indeed.com/viewjob?jk=phoenix_otr_001',
            'title': 'Southwest OTR Driver',
            'company': 'Mountain West Freight',
            'market': 'Phoenix',
            'route_type': 'OTR',
            'match': 'so-so'
        },
        
        # Vegas Market
        {
            'url': 'https://www.indeed.com/viewjob?jk=vegas_local_001',
            'title': 'Las Vegas Local CDL Driver',
            'company': 'Nevada Cargo',
            'market': 'Vegas',
            'route_type': 'Local',
            'match': 'good'
        },
        {
            'url': 'https://www.indeed.com/viewjob?jk=vegas_otr_001',
            'title': 'OTR Driver - Western Routes',
            'company': 'Silver State Transport',
            'market': 'Vegas',
            'route_type': 'OTR',
            'match': 'so-so'
        },
        
        # Bay Area
        {
            'url': 'https://www.indeed.com/viewjob?jk=bayarea_local_001',
            'title': 'Bay Area Local CDL Driver',
            'company': 'Golden Gate Logistics',
            'market': 'Bay Area',
            'route_type': 'Local',
            'match': 'good'
        },
        {
            'url': 'https://www.indeed.com/viewjob?jk=bayarea_local_002',
            'title': 'San Francisco Local Delivery Driver',
            'company': 'Pacific Coast Transport',
            'market': 'Bay Area',
            'route_type': 'Local',
            'match': 'so-so'
        },
        
        # Denver Market
        {
            'url': 'https://www.indeed.com/viewjob?jk=denver_local_001',
            'title': 'Denver Local CDL Driver',
            'company': 'Rocky Mountain Freight',
            'market': 'Denver',
            'route_type': 'Local',
            'match': 'good'
        },
        {
            'url': 'https://www.indeed.com/viewjob?jk=denver_otr_001',
            'title': 'Mountain Region OTR Driver',
            'company': 'Colorado Express',
            'market': 'Denver',
            'route_type': 'OTR',
            'match': 'so-so'
        },
        
        # Additional variety jobs
        {
            'url': 'https://www.indeed.com/viewjob?jk=dallas_premium_001',
            'title': 'Premium CDL Position - Top Pay',
            'company': 'Elite Freight Services',
            'market': 'Dallas',
            'route_type': 'Local',
            'match': 'good'
        },
        {
            'url': 'https://www.indeed.com/viewjob?jk=houston_dedicated_001',
            'title': 'Dedicated Account Driver',
            'company': 'Coastal Logistics',
            'market': 'Houston',
            'route_type': 'OTR',
            'match': 'good'
        }
    ]
    
    return sample_jobs

def generate_demo_data():
    """Generate comprehensive demo data for the analytics dashboard"""
    
    print("🎬 Creating Demo Data for FreeWorld Link Analytics Dashboard")
    print("=" * 60)
    
    # Initialize tracker and dashboard
    tracker = LinkTracker()
    dashboard = AnalyticsDashboard()
    
    # Get sample jobs
    sample_jobs = create_sample_job_links()
    
    print(f"📊 Creating {len(sample_jobs)} tracked links...")
    
    created_links = []
    
    # Create links and log them with realistic timestamps
    for i, job in enumerate(sample_jobs):
        print(f"  {i+1:2d}. Creating link for: {job['title'][:40]}...")
        
        # Create the short link
        tags = [
            'freeworld',
            'job',
            job['market'].lower().replace(' ', '_'),
            job['route_type'].lower(),
            job['match'].replace('-', '_')
        ]
        
        short_url = tracker.create_short_link(
            original_url=job['url'],
            title=f"{job['title']} - {job['company']}",
            tags=tags
        )
        
        if short_url and short_url != job['url']:
            created_links.append({
                'original_url': job['url'],
                'short_url': short_url,
                'job_data': job
            })
            print(f"      ✅ Created: {short_url}")
        else:
            print(f"      ❌ Failed to create link")
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    print(f"\n✅ Successfully created {len(created_links)} tracked links!")
    
    # Now create realistic historical data with varied timestamps
    print("\n📅 Generating historical tracking data...")
    
    # Clear existing data to start fresh
    dashboard.analytics_data = {
        "links_created": [],
        "summary": {}
    }
    
    # Generate data over the past 2 weeks with realistic patterns
    now = datetime.now()
    
    for days_ago in range(14, 0, -1):
        # More links created on weekdays, fewer on weekends
        day_of_week = (now - timedelta(days=days_ago)).weekday()
        is_weekend = day_of_week >= 5
        
        # Number of links created per day (fewer on weekends)
        links_per_day = random.randint(1, 3) if is_weekend else random.randint(3, 8)
        
        # Select random jobs for this day
        daily_jobs = random.sample(created_links, min(links_per_day, len(created_links)))
        
        for link_data in daily_jobs:
            # Create realistic timestamp within the day
            hours_offset = random.randint(8, 18)  # Business hours
            minutes_offset = random.randint(0, 59)
            
            timestamp = now - timedelta(days=days_ago, hours=24-hours_offset, minutes=minutes_offset)
            
            # Create the analytics entry
            job = link_data['job_data']
            metadata = {
                "title": job['title'],
                "company": job['company'],
                "market": job['market'],
                "route_type": job['route_type'],
                "match": job['match'],
                "tags": [
                    'freeworld',
                    'job', 
                    job['market'].lower().replace(' ', '_'),
                    job['route_type'].lower(),
                    job['match'].replace('-', '_')
                ]
            }
            
            # Add to dashboard data with custom timestamp
            link_entry = {
                "timestamp": timestamp.isoformat(),
                "original_url": link_data['original_url'],
                "short_url": link_data['short_url'],
                "metadata": metadata,
                "clicks": random.randint(0, 15)  # Simulate some click data
            }
            
            dashboard.analytics_data["links_created"].append(link_entry)
    
    # Update summary stats
    dashboard.update_summary_stats()
    
    # Add some realistic click patterns
    print("\n🖱️  Adding realistic click patterns...")
    
    for link in dashboard.analytics_data["links_created"]:
        # Good matches get more clicks, local routes get more clicks
        base_clicks = 2
        
        if link["metadata"]["match"] == "good":
            base_clicks += random.randint(3, 8)
        elif link["metadata"]["match"] == "so-so":
            base_clicks += random.randint(1, 4)
        
        if link["metadata"]["route_type"] == "Local":
            base_clicks += random.randint(2, 5)
        
        # Dallas market tends to perform better
        if link["metadata"]["market"] == "Dallas":
            base_clicks += random.randint(1, 4)
        
        link["clicks"] = base_clicks + random.randint(0, 3)
    
    # Save the demo data
    dashboard.save_local_tracking_data()
    
    print(f"📊 Generated {len(dashboard.analytics_data['links_created'])} historical link entries")
    print(f"📈 Total links: {dashboard.analytics_data['summary']['total_links']}")
    print(f"📅 Links today: {dashboard.analytics_data['summary']['links_today']}")
    print(f"📅 Links this week: {dashboard.analytics_data['summary']['links_this_week']}")
    
    # Calculate some interesting stats
    total_clicks = sum(link.get('clicks', 0) for link in dashboard.analytics_data['links_created'])
    avg_clicks = total_clicks / len(dashboard.analytics_data['links_created']) if dashboard.analytics_data['links_created'] else 0
    
    print(f"🎯 Total clicks: {total_clicks}")
    print(f"📊 Average clicks per link: {avg_clicks:.1f}")
    
    # Show market breakdown
    market_stats = {}
    for link in dashboard.analytics_data['links_created']:
        market = link["metadata"]["market"]
        if market not in market_stats:
            market_stats[market] = {'links': 0, 'clicks': 0}
        market_stats[market]['links'] += 1
        market_stats[market]['clicks'] += link.get('clicks', 0)
    
    print("\n🏢 Market Performance:")
    for market, stats in sorted(market_stats.items(), key=lambda x: x[1]['clicks'], reverse=True):
        ctr = (stats['clicks'] / stats['links']) if stats['links'] > 0 else 0
        print(f"   {market:12} | {stats['links']:2d} links | {stats['clicks']:3d} clicks | {ctr:.1f} avg")
    
    print("\n" + "=" * 60)
    print("🎉 Demo data generation complete!")
    print("🚀 Launch the analytics dashboard to see the results:")
    print("   python3 src/analytics_dashboard.py")
    print("=" * 60)
    
    return dashboard

def launch_demo_dashboard():
    """Generate demo data and launch the analytics dashboard"""
    # Generate the demo data first
    dashboard = generate_demo_data()
    
    print("\n🚀 Launching Analytics Dashboard with Demo Data...")
    
    # Show the dashboard
    dashboard.show_dashboard()

if __name__ == "__main__":
    launch_demo_dashboard()