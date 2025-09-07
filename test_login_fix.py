#!/usr/bin/env python3
"""
Test login system and create default coaches if needed
"""

import sys
import os

# Add current directory to path
sys.path.append('.')

def test_login():
    print("🔐 TESTING LOGIN SYSTEM")
    print("=" * 50)
    
    # Import our user management
    try:
        from user_management import CoachManager
        print("✅ Successfully imported CoachManager")
    except Exception as e:
        print(f"❌ Failed to import CoachManager: {e}")
        return
    
    # Initialize coach manager
    try:
        coach_manager = CoachManager()
        print("✅ Successfully initialized CoachManager")
    except Exception as e:
        print(f"❌ Failed to initialize CoachManager: {e}")
        return
    
    # Check current coaches
    print(f"\n📋 CURRENT COACHES ({len(coach_manager.coaches)}):")
    for username, coach in coach_manager.coaches.items():
        print(f"  - {username}: {coach.full_name} ({coach.role})")
    
    # If no coaches, create defaults
    if not coach_manager.coaches:
        print("\n⚠️ No coaches found! Creating default coaches...")
        try:
            coach_manager.create_default_coaches()
            print(f"✅ Created default coaches: {list(coach_manager.coaches.keys())}")
        except Exception as e:
            print(f"❌ Failed to create default coaches: {e}")
            return
    
    # Test admin login
    print(f"\n🧪 TESTING ADMIN LOGIN")
    try:
        admin_coach = coach_manager.authenticate("admin", "admin123")
        if admin_coach:
            print(f"✅ Admin login successful: {admin_coach.full_name}")
        else:
            print("❌ Admin login failed")
    except Exception as e:
        print(f"❌ Admin login error: {e}")
    
    # Test sample coach login if exists
    if "sarah.johnson" in coach_manager.coaches:
        print(f"\n🧪 TESTING SARAH.JOHNSON LOGIN")
        try:
            coach = coach_manager.authenticate("sarah.johnson", "coach123")
            if coach:
                print(f"✅ Sarah login successful: {coach.full_name}")
            else:
                print("❌ Sarah login failed")
        except Exception as e:
            print(f"❌ Sarah login error: {e}")

if __name__ == "__main__":
    test_login()