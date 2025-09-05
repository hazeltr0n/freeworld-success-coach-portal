#!/usr/bin/env python3
"""
Setup Auto-Deduplication for Supabase

This script installs the automatic deduplication system in your Supabase database.
After setup, every job upload will automatically trigger duplicate cleanup.

Usage:
    python3 setup_auto_dedup.py --install
    python3 setup_auto_dedup.py --status
    python3 setup_auto_dedup.py --disable
    python3 setup_auto_dedup.py --enable
"""

import argparse
import sys
import os

# Load environment variables
try:
    from tools.secrets_loader import load_local_secrets_to_env
    load_local_secrets_to_env()
except Exception:
    pass

def get_supabase_client():
    """Initialize Supabase client"""
    try:
        from supabase_utils import get_client
        return get_client()
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        return None

def install_auto_dedup(supabase):
    """Install the auto-deduplication system"""
    try:
        print("🔧 Installing auto-deduplication system...")
        
        # Check if deduplication functions exist
        print("1/3 Checking for deduplication functions...")
        try:
            result = supabase.rpc('analyze_duplicate_jobs').execute()
            print("   ✅ Deduplication functions found")
        except Exception:
            print("   ❌ Deduplication functions not found!")
            print("   📋 Please run supabase_dedup_function.sql first in Supabase SQL Editor")
            return False
        
        # Install trigger system (read from SQL file)
        print("2/3 Installing trigger system...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        trigger_sql_path = os.path.join(script_dir, 'supabase_auto_dedup_trigger.sql')
        
        if not os.path.exists(trigger_sql_path):
            print(f"   ❌ Trigger SQL file not found: {trigger_sql_path}")
            return False
        
        with open(trigger_sql_path, 'r') as f:
            trigger_sql = f.read()
        
        # Execute the trigger installation SQL
        # Note: Supabase Python client doesn't support direct SQL execution
        # This needs to be run manually in Supabase SQL Editor
        print("   ⚠️  Manual step required:")
        print("   📋 Please run supabase_auto_dedup_trigger.sql in Supabase SQL Editor")
        print("   📋 This will create the automatic trigger system")
        
        # Check if trigger was installed (after manual step)
        print("3/3 Checking trigger status...")
        try:
            result = supabase.rpc('check_auto_dedup_status').execute()
            if result.data:
                print("   ✅ Auto-dedup trigger is active")
                return True
            else:
                print("   ⚠️  Trigger not yet installed (run SQL file manually)")
                return False
        except Exception as e:
            print(f"   ⚠️  Could not check trigger status: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def check_status(supabase):
    """Check auto-dedup system status"""
    try:
        print("🔍 Checking auto-deduplication status...")
        
        # Check functions
        try:
            result = supabase.rpc('analyze_duplicate_jobs').execute()
            print("✅ Deduplication functions: Available")
        except Exception:
            print("❌ Deduplication functions: Not found")
            return False
        
        # Check trigger
        try:
            result = supabase.rpc('check_auto_dedup_status').execute()
            if result.data and len(result.data) > 0:
                trigger_info = result.data[0]
                status = "ENABLED" if trigger_info['trigger_enabled'] else "DISABLED"
                print(f"✅ Auto-dedup trigger: {status}")
                print(f"   Timing: {trigger_info['trigger_timing']}")
                print(f"   Level: {trigger_info['trigger_level']}")
            else:
                print("❌ Auto-dedup trigger: Not installed")
                return False
        except Exception as e:
            print(f"❌ Trigger status check failed: {e}")
            return False
        
        # Check recent activity
        try:
            result = supabase.rpc('view_auto_dedup_history', {'days_back': 7}).execute()
            if result.data:
                print(f"📊 Recent activity: {len(result.data)} cleanup operations in last 7 days")
                if len(result.data) > 0:
                    latest = result.data[0]
                    print(f"   Latest: {latest['triggered_at']} - removed {latest['jobs_removed']} jobs")
            else:
                print("📊 Recent activity: No cleanup operations logged")
        except Exception:
            print("📊 Recent activity: Could not retrieve history")
        
        return True
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False

def disable_auto_dedup(supabase):
    """Disable auto-deduplication trigger"""
    try:
        print("🛑 Disabling auto-deduplication trigger...")
        result = supabase.rpc('disable_auto_dedup').execute()
        
        if result.data:
            print(f"✅ {result.data}")
            return True
        else:
            print("⚠️ Unexpected result from disable function")
            return False
            
    except Exception as e:
        print(f"❌ Failed to disable trigger: {e}")
        return False

def enable_auto_dedup(supabase):
    """Enable auto-deduplication trigger"""
    try:
        print("▶️ Enabling auto-deduplication trigger...")
        result = supabase.rpc('enable_auto_dedup').execute()
        
        if result.data:
            print(f"✅ {result.data}")
            return True
        else:
            print("⚠️ Unexpected result from enable function")
            return False
            
    except Exception as e:
        print(f"❌ Failed to enable trigger: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Setup auto-deduplication for Supabase")
    parser.add_argument("--install", action="store_true", help="Install auto-dedup system")
    parser.add_argument("--status", action="store_true", help="Check system status")
    parser.add_argument("--disable", action="store_true", help="Disable auto-dedup trigger")
    parser.add_argument("--enable", action="store_true", help="Enable auto-dedup trigger")
    
    args = parser.parse_args()
    
    # Validate arguments
    actions = [args.install, args.status, args.disable, args.enable]
    if sum(actions) != 1:
        print("❌ Must specify exactly one action: --install, --status, --disable, or --enable")
        return 1
    
    # Initialize Supabase
    supabase = get_supabase_client()
    if not supabase:
        return 1
    
    print("🗄️  SUPABASE AUTO-DEDUPLICATION SETUP")
    print("=" * 45)
    
    try:
        if args.install:
            success = install_auto_dedup(supabase)
        elif args.status:
            success = check_status(supabase)
        elif args.disable:
            success = disable_auto_dedup(supabase)
        elif args.enable:
            success = enable_auto_dedup(supabase)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Setup script failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())