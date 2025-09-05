#!/usr/bin/env python3
"""
Simulate clicks on the created short links to generate real analytics data
"""

import webbrowser
import time
import json
import random

def simulate_clicks():
    """Open some of the created short links in browser to generate real click data"""
    
    # Load the tracking data to get the created links
    try:
        with open('data/link_tracking_log.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ No tracking data found. Run demo_data_generator.py first.")
        return
    
    links = data.get('links_created', [])
    if not links:
        print("❌ No links found in tracking data.")
        return
    
    # Get unique short URLs
    unique_links = {}
    for link in links:
        short_url = link.get('short_url', '')
        if short_url and short_url.startswith('https://freeworldjobs.short.gy/'):
            unique_links[short_url] = link
    
    if not unique_links:
        print("❌ No valid short URLs found.")
        return
    
    print(f"🎯 Found {len(unique_links)} unique short links to click")
    print("🖱️  Simulating Free Agent clicks...")
    
    # Select a random sample of links to click
    links_to_click = random.sample(list(unique_links.items()), min(8, len(unique_links)))
    
    print(f"\n📊 Opening {len(links_to_click)} links to generate real click data:")
    
    for i, (short_url, link_data) in enumerate(links_to_click, 1):
        metadata = link_data.get('metadata', {})
        title = metadata.get('title', 'Unknown Job')
        market = metadata.get('market', 'Unknown')
        
        print(f"  {i}. {title} ({market})")
        print(f"     🔗 {short_url}")
        
        # Open in browser (this generates real clicks in Short.io analytics)
        webbrowser.open(short_url)
        
        # Small delay between clicks to be more realistic
        time.sleep(2)
    
    print(f"\n✅ Successfully clicked {len(links_to_click)} links!")
    print("📈 These clicks will show up in Short.io analytics")
    print("🕐 Note: Analytics may take a few minutes to update")
    
    # Now test if we can retrieve the analytics
    print("\n🔍 Testing analytics retrieval...")
    
    import sys
    sys.path.append('src')
    from link_tracker import LinkTracker
    
    tracker = LinkTracker()
    
    # Try to get analytics for one of the clicked links
    test_link = links_to_click[0][0]
    print(f"📊 Checking analytics for: {test_link}")
    
    analytics = tracker.get_link_analytics(test_link)
    if analytics:
        print(f"✅ Analytics retrieved successfully!")
        print(f"📈 Total clicks: {analytics.get('totalClicks', 'N/A')}")
    else:
        print("ℹ️  Analytics not yet available (may take a few minutes)")
    
    print("\n" + "="*50)
    print("🎉 Click simulation complete!")
    print("🚀 Launch the analytics dashboard to see the results")
    print("="*50)

if __name__ == "__main__":
    simulate_clicks()