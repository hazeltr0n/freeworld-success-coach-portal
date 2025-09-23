#!/usr/bin/env python3
"""
Google Jobs Background Scheduler
Runs independently to continuously populate Supabase with fresh Google Jobs
No user engagement required - just runs in background and stores quality jobs
"""

import time
import schedule
import logging
from datetime import datetime
from google_jobs_storage import GoogleJobsStorage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('google_jobs_scheduler.log'),
        logging.StreamHandler()
    ]
)

class GoogleJobsScheduler:
    def __init__(self):
        self.storage = GoogleJobsStorage()
        self.target_locations = [
            "Houston, TX",
            "Dallas, TX", 
            "Austin, TX",
            "San Antonio, TX",
            "Phoenix, AZ",
            "Las Vegas, NV",
            "Denver, CO",
            "Newark, NJ"
        ]
        
    def run_location_harvest(self, location):
        """Harvest Google Jobs for a single location"""
        try:
            logging.info(f"🔍 Starting Google Jobs harvest for {location}")
            
            stored_count = self.storage.scrape_and_store_google_jobs(
                location=location,
                search_terms="CDL Driver",
                limit=100  # Get reasonable number of jobs
            )
            
            logging.info(f"✅ {location}: Stored {stored_count} quality jobs")
            return stored_count
            
        except Exception as e:
            logging.error(f"❌ {location} harvest failed: {e}")
            return 0
    
    def run_full_harvest_cycle(self):
        """Run full harvest cycle across all target locations"""
        logging.info("🚀 STARTING FULL GOOGLE JOBS HARVEST CYCLE")
        logging.info("=" * 60)
        
        total_stored = 0
        successful_locations = 0
        
        for location in self.target_locations:
            stored = self.run_location_harvest(location)
            total_stored += stored
            
            if stored > 0:
                successful_locations += 1
                
            # Add delay between locations to be respectful to API
            time.sleep(10)
        
        logging.info("=" * 60)
        logging.info(f"🎉 HARVEST CYCLE COMPLETE")
        logging.info(f"📊 Results: {successful_locations}/{len(self.target_locations)} locations successful")
        logging.info(f"💾 Total jobs stored: {total_stored}")
        logging.info(f"⏰ Next cycle: {datetime.now().strftime('%H:%M:%S')}")
        
        return total_stored

def main():
    """Run the background scheduler"""
    scheduler = GoogleJobsScheduler()
    
    logging.info("🤖 Google Jobs Background Scheduler Starting")
    logging.info("📅 Schedule: Every 6 hours")
    logging.info("📍 Target locations: 8 markets")
    logging.info("🔄 Running continuously...")
    
    # Schedule job every 6 hours
    schedule.every(6).hours.do(scheduler.run_full_harvest_cycle)
    
    # Run once immediately on startup
    logging.info("🚀 Running initial harvest cycle...")
    scheduler.run_full_harvest_cycle()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()