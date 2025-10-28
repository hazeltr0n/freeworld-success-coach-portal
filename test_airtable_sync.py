#!/usr/bin/env python3
"""Test script to debug Airtable sync for Johnny Hopkins"""

import os
from dotenv import load_dotenv

load_dotenv()

# Import the sync function
from app import sync_all_agents_airtable_status

# Test with james.hazelton (your actual username)
print("=" * 60)
print("TESTING AIRTABLE SYNC")
print("=" * 60)

result = sync_all_agents_airtable_status(coach_username="james.hazelton")

print(f"\n✅ Sync completed. Synced {result} agents.")
print("=" * 60)
