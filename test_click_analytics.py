#!/usr/bin/env python3
"""
Test script to check for click analytics after links have been clicked
"""

import sys
sys.path.append('src')
from link_tracker import LinkTracker
import time

def test_click_analytics():
    """Check if we can retrieve click data for our test links"""
    
    print("🔍 Testing Click Analytics Detection...")
    print("=" * 50)
    
    tracker = LinkTracker()
    
    # Test links that should have been clicked
    test_links = [
        "https://freeworldjobs.short.gy/VvEepq",  # CDL Driver Jobs Dallas
        "https://freeworldjobs.short.gy/1Z3UVD",  # Local Routes
        "https://freeworldjobs.short.gy/vWetAC"   # OTR Driver
    ]
    
    print(f"📊 Checking analytics for {len(test_links)} links...\n")
    
    for i, link in enumerate(test_links, 1):
        print(f"{i}. Checking: {link}")
        
        try:
            analytics = tracker.get_link_analytics(link)
            
            if analytics:
                clicks = analytics.get('totalClicks', 0)
                print(f"   ✅ SUCCESS: {clicks} clicks detected!")
                
                # Show additional analytics if available
                if 'clicksToday' in analytics:
                    print(f"   📅 Today: {analytics.get('clicksToday', 0)} clicks")
                if 'clicksThisWeek' in analytics:
                    print(f"   📅 This week: {analytics.get('clicksThisWeek', 0)} clicks")
                    
                print(f"   📊 Full data: {analytics}")
                
            else:
                print(f"   ❌ No analytics data available yet")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    # Also try domain-level analytics
    print("🌐 Checking domain-level analytics...")
    try:
        domain_analytics = tracker.get_domain_analytics()
        if domain_analytics:
            print(f"✅ Domain analytics available!")
            print(f"📊 Data: {domain_analytics}")
        else:
            print("❌ No domain analytics available")
    except Exception as e:
        print(f"❌ Domain analytics error: {e}")
    
    print("\n" + "=" * 50)
    print("📝 NOTE: If analytics show 0 clicks, it might take a few minutes")
    print("for Short.io to update their statistics, or the analytics API")
    print("might not be fully available yet.")
    print("=" * 50)

if __name__ == "__main__":
    test_click_analytics()