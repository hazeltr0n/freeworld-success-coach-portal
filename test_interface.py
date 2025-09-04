#!/usr/bin/env python3
"""
FreeWorld Job Scraper - Comprehensive Test Interface
Test ANY part of the pipeline with full custom location support
Uses the same JobSearchForm core as GUI and Terminal for automatic feature parity
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.dirname(__file__))

from job_search_form_standalone import JobSearchForm
from cost_calculator import CostCalculator

class TestInterface:
    """Comprehensive test interface with full pipeline component testing"""
    
    def __init__(self):
        """Initialize with same core as GUI and Terminal"""
        self.job_form = JobSearchForm()
        self.calculator = CostCalculator()
        
        print("🧪 FreeWorld Job Scraper - Test Interface")
        print("✅ Same core as GUI and Terminal (automatic feature parity)")
        print(f"🗺️ Markets: {len(self.job_form.MARKET_SEARCH_QUERIES)} available")
        print("📍 Custom location support: ENABLED")
        
    def test_scraping(self, market=None, custom_location=None, limit=5, terms="CDL driver"):
        """Test job scraping with market or custom location"""
        print(f"\n🔍 === TESTING JOB SCRAPING ===")
        
        # Determine location
        if custom_location:
            location = custom_location
            location_name = f"Custom: {custom_location}"
        elif market:
            if market.title() in self.job_form.MARKET_SEARCH_QUERIES:
                location = self.job_form.MARKET_SEARCH_QUERIES[market.title()]
                location_name = f"Market: {market}"
            else:
                print(f"❌ Unknown market: {market}")
                print(f"Available: {', '.join(self.job_form.MARKET_SEARCH_QUERIES.keys())}")
                return False
        else:
            print("❌ Must specify --market or --custom-location")
            return False
            
        print(f"📍 Location: {location_name}")
        print(f"🎯 Target: {limit} jobs")
        print(f"🔍 Terms: {terms}")
        
        try:
            # Use job form's scraper
            search_terms = [term.strip() for term in terms.split(',')]
            indeed_url = self.job_form.build_indeed_url(search_terms[0], location, "50")
            
            print(f"🌐 Indeed URL: {indeed_url}")
            
            # Scrape jobs
            raw_jobs = self.job_form.scraper.scrape_jobs(
                search_terms, 
                location, 
                limit, 
                no_experience=True
            )
            
            if raw_jobs:
                print(f"✅ Scraped {len(raw_jobs)} jobs")
                print(f"   Sample job titles:")
                for i, job in enumerate(raw_jobs[:3]):
                    print(f"   {i+1}. {job.get('title', 'No title')} - {job.get('company', 'No company')}")
                return raw_jobs
            else:
                print("❌ No jobs found")
                return False
                
        except Exception as e:
            print(f"💥 Scraping error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_supabase_cache(self, job_ids=None, location=None, hours=72):
        """Test Supabase memory/cache system"""
        print(f"\n🧠 === TESTING SUPABASE CACHE ===")
        
        if not hasattr(self.job_form, 'pipeline') or not hasattr(self.job_form.pipeline, 'memory_classifier'):
            print("❌ Memory classifier not available")
            return False
            
        classifier = self.job_form.pipeline.memory_classifier
        
        if job_ids:
            # Test specific job IDs
            print(f"🔍 Checking {len(job_ids)} specific job IDs...")
            cache_results = classifier.memory_db.check_job_memory(job_ids, hours)
            
            found = len([jid for jid in job_ids if jid in cache_results])
            print(f"✅ Found {found}/{len(job_ids)} jobs in cache")
            
            return cache_results
            
        elif location:
            # Test location-based cache
            print(f"📍 Checking cache for location: {location}")
            print(f"⏰ Looking back {hours} hours")
            
            quality_jobs = classifier.memory_db.get_quality_jobs_for_count_reduction(location, hours)
            print(f"✅ Found {len(quality_jobs)} quality jobs in cache")
            
            if quality_jobs:
                # Show breakdown
                matches = {}
                for job in quality_jobs:
                    match = job.get('match', 'unknown')
                    matches[match] = matches.get(match, 0) + 1
                
                print("   Quality breakdown:")
                for match, count in matches.items():
                    print(f"   - {match}: {count} jobs")
                    
            return quality_jobs
            
        else:
            # General cache stats
            print("📊 Getting general cache statistics...")
            stats = classifier.get_hybrid_memory_stats()
            
            print("✅ Cache statistics:")
            for key, value in stats.items():
                print(f"   - {key}: {value}")
                
            return stats
    
    def test_classification(self, csv_path=None, jobs_data=None, limit=3):
        """Test AI job classification (only for non-cached jobs)"""
        print(f"\n🤖 === TESTING JOB CLASSIFICATION ===")
        
        # Load or use provided data
        if csv_path and os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            print(f"📄 Loaded {len(df)} jobs from {csv_path}")
        elif jobs_data:
            df = pd.DataFrame(jobs_data)
            print(f"📊 Using {len(df)} provided jobs")
        else:
            print("❌ No data provided - need --csv or scraped jobs")
            return False
            
        # Take limited sample for testing
        test_df = df.head(limit).copy()
        print(f"🎯 Testing classification on {len(test_df)} jobs")
        
        try:
            # Check memory first (90% cost reduction!)
            if hasattr(self.job_form, 'pipeline') and hasattr(self.job_form.pipeline, 'memory_classifier'):
                classifier = self.job_form.pipeline.memory_classifier
                
                # Check cache
                job_ids = test_df.get('job_id', []).tolist()
                if job_ids:
                    cached_results = classifier.memory_db.check_job_memory(job_ids)
                    cached_count = len([jid for jid in job_ids if jid in cached_results])
                    print(f"🧠 Found {cached_count}/{len(job_ids)} jobs in cache (cost savings!)")
                
                # Classify with memory system
                result = classifier.classify_jobs_with_memory(test_df)
                
                if 'classified_jobs' in result:
                    classified_df = result['classified_jobs']
                    print(f"✅ Classified {len(classified_df)} jobs")
                    
                    # Show results
                    match_counts = classified_df['match'].value_counts()
                    print("   Classification results:")
                    for match, count in match_counts.items():
                        print(f"   - {match}: {count} jobs")
                        
                    # Show sample
                    print("   Sample classifications:")
                    for idx, row in classified_df.head(3).iterrows():
                        title = row.get('title', 'No title')[:50]
                        match = row.get('match', 'unknown')
                        cached = row.get('included_previous_classification', False)
                        cache_status = "CACHED" if cached else "NEW"
                        print(f"   - {title}... → {match} ({cache_status})")
                        
                    return classified_df
                else:
                    print("❌ Classification failed")
                    return False
            else:
                print("❌ Memory classifier not available")
                return False
                
        except Exception as e:
            print(f"💥 Classification error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_fair_chance(self, csv_path=None, jobs_data=None, limit=5):
        """Test fair chance detection"""
        print(f"\n⚖️ === TESTING FAIR CHANCE DETECTION ===")
        
        # Load data
        if csv_path and os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            print(f"📄 Loaded {len(df)} jobs from {csv_path}")
        elif jobs_data:
            df = pd.DataFrame(jobs_data)
        else:
            print("❌ No data provided")
            return False
            
        test_df = df.head(limit).copy()
        print(f"🎯 Testing on {len(test_df)} jobs")
        
        try:
            # Use pipeline's fair chance detection
            if hasattr(self.job_form, 'pipeline'):
                pipeline = self.job_form.pipeline
                
                # Apply fair chance detection
                result_df = pipeline.apply_fair_chance_detection(test_df)
                
                if 'fair_chance' in result_df.columns:
                    fair_chance_counts = result_df['fair_chance'].value_counts()
                    print("✅ Fair chance detection results:")
                    for status, count in fair_chance_counts.items():
                        print(f"   - {status}: {count} jobs")
                        
                    # Show samples
                    print("   Sample results:")
                    for idx, row in result_df.head(3).iterrows():
                        title = row.get('title', 'No title')[:40]
                        fc_status = row.get('fair_chance', 'unknown')
                        print(f"   - {title}... → {fc_status}")
                        
                    return result_df
                else:
                    print("❌ Fair chance detection failed")
                    return False
            else:
                print("❌ Pipeline not available")
                return False
                
        except Exception as e:
            print(f"💥 Fair chance detection error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_endorsements(self, csv_path=None, jobs_data=None, limit=5):
        """Test CDL endorsement detection"""
        print(f"\n🏅 === TESTING ENDORSEMENT DETECTION ===")
        
        # Load data
        if csv_path and os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            print(f"📄 Loaded {len(df)} jobs from {csv_path}")
        elif jobs_data:
            df = pd.DataFrame(jobs_data)
        else:
            print("❌ No data provided")
            return False
            
        test_df = df.head(limit).copy()
        print(f"🎯 Testing on {len(test_df)} jobs")
        
        try:
            # Use pipeline's endorsement detection
            if hasattr(self.job_form, 'pipeline'):
                pipeline = self.job_form.pipeline
                
                # Apply endorsement detection
                result_df = pipeline.apply_endorsement_detection(test_df)
                
                if 'endorsements' in result_df.columns:
                    endorsement_counts = result_df['endorsements'].value_counts()
                    print("✅ Endorsement detection results:")
                    for endorsement, count in endorsement_counts.items():
                        print(f"   - {endorsement}: {count} jobs")
                        
                    # Show samples
                    print("   Sample results:")
                    for idx, row in result_df.head(3).iterrows():
                        title = row.get('title', 'No title')[:40]
                        endorsements = row.get('endorsements', 'unknown')
                        print(f"   - {title}... → {endorsements}")
                        
                    return result_df
                else:
                    print("❌ Endorsement detection failed")
                    return False
            else:
                print("❌ Pipeline not available")
                return False
                
        except Exception as e:
            print(f"💥 Endorsement detection error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_storage_systems(self, jobs_df, test_supabase=True, test_airtable=True):
        """Test both Supabase and Airtable storage"""
        print(f"\n💾 === TESTING STORAGE SYSTEMS ===")
        
        if jobs_df is None or len(jobs_df) == 0:
            print("❌ No jobs data provided")
            return False
            
        results = {}
        
        # Test Supabase storage (all jobs)
        if test_supabase:
            print(f"🗃️ Testing Supabase storage (all {len(jobs_df)} jobs)...")
            try:
                if hasattr(self.job_form, 'pipeline') and hasattr(self.job_form.pipeline, 'memory_classifier'):
                    classifier = self.job_form.pipeline.memory_classifier
                    supabase_result = classifier.memory_db.store_classifications(jobs_df)
                    
                    if supabase_result:
                        print("✅ Supabase storage successful")
                        results['supabase'] = True
                    else:
                        print("❌ Supabase storage failed")
                        results['supabase'] = False
                else:
                    print("⚠️ Supabase storage not available")
                    results['supabase'] = None
                    
            except Exception as e:
                print(f"💥 Supabase storage error: {e}")
                results['supabase'] = False
        
        # Test Airtable upload (quality jobs only)
        if test_airtable:
            quality_jobs = jobs_df[jobs_df.get('match', '').isin(['good', 'so-so'])] if 'match' in jobs_df.columns else jobs_df
            print(f"📤 Testing Airtable upload ({len(quality_jobs)} quality jobs from {len(jobs_df)} total)...")
            
            try:
                if hasattr(self.job_form, 'pipeline') and hasattr(self.job_form.pipeline, 'memory_classifier'):
                    classifier = self.job_form.pipeline.memory_classifier
                    airtable_result = classifier.upload_quality_jobs_to_airtable(jobs_df)
                    
                    if airtable_result.get('success'):
                        uploaded_count = airtable_result.get('uploaded_count', 0)
                        print(f"✅ Airtable upload successful ({uploaded_count} jobs)")
                        results['airtable'] = uploaded_count
                    else:
                        message = airtable_result.get('message', 'Unknown error')
                        print(f"❌ Airtable upload failed: {message}")
                        results['airtable'] = False
                else:
                    print("⚠️ Airtable upload not available")
                    results['airtable'] = None
                    
            except Exception as e:
                print(f"💥 Airtable upload error: {e}")
                results['airtable'] = False
        
        return results
    
    def test_pdf_generation(self, csv_path=None, jobs_data=None, output_path=None):
        """Test PDF generation with badges"""
        print(f"\n📄 === TESTING PDF GENERATION ===")
        
        # Load data
        if csv_path and os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            print(f"📄 Loaded {len(df)} jobs from {csv_path}")
        elif jobs_data is not None:
            df = pd.DataFrame(jobs_data)
            print(f"📊 Using {len(df)} provided jobs")
        else:
            print("❌ No data provided - need --csv or jobs data")
            return False
            
        # Generate output path if not provided
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"data/TEST_PDF_{timestamp}.pdf"
        
        print(f"🎯 Generating PDF: {output_path}")
        
        try:
            # Use job form's PDF generator
            from pdf_generator import PDFJobListGenerator
            
            pdf_gen = PDFJobListGenerator(enable_link_tracking=False)
            
            result = pdf_gen.generate_pdf(
                df,
                output_path,
                title="Test Interface - PDF Generation Test",
                route_filter="both",
                market="Test Location"
            )
            
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / 1024  # KB
                print(f"✅ PDF generated successfully ({file_size:.1f} KB)")
                print(f"   Location: {output_path}")
                return output_path
            else:
                print("❌ PDF generation failed - file not created")
                return False
                
        except Exception as e:
            print(f"💥 PDF generation error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_full_pipeline(self, market=None, custom_location=None, limit=10, route_filter="both"):
        """Test complete pipeline end-to-end with custom location support"""
        print(f"\n🚀 === TESTING FULL PIPELINE ===")
        
        # Determine location
        if custom_location:
            location = custom_location
            location_name = f"Custom: {custom_location}"
            markets = ["Custom"]
            locations = [custom_location]
        elif market:
            if market.title() in self.job_form.MARKET_SEARCH_QUERIES:
                location = self.job_form.MARKET_SEARCH_QUERIES[market.title()]
                location_name = f"Market: {market}"
                markets = [market.title()]
                locations = [location]
            else:
                print(f"❌ Unknown market: {market}")
                return False
        else:
            print("❌ Must specify --market or --custom-location")
            return False
            
        print(f"📍 Location: {location_name}")
        print(f"🎯 Limit: {limit} jobs")
        print(f"🛣️ Route filter: {route_filter}")
        
        try:
            # Calculate estimated cost
            estimated_cost = self.calculator.calculate_total_cost(limit)
            print(f"💰 Estimated cost: ${estimated_cost:.4f}")
            
            # Run full search (same as GUI/Terminal)
            mode_info = {"mode": "test", "limit": limit, "use_multi_search": False}
            
            result = self.job_form.run_search(
                target_markets=markets,
                locations=locations,
                mode_info=mode_info,
                search_terms=["CDL driver"],
                route_filter=route_filter,
                airtable_upload=False,  # Skip for testing
                market_name=location_name.split(": ")[1] if ": " in location_name else location_name,
                custom_location=custom_location
            )
            
            if result:
                print("✅ Full pipeline completed successfully!")
                return result
            else:
                print("❌ Full pipeline failed")
                return False
                
        except Exception as e:
            print(f"💥 Full pipeline error: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    parser = argparse.ArgumentParser(description='FreeWorld Job Scraper - Comprehensive Test Interface')
    
    # Location options (same as Terminal and GUI)
    parser.add_argument('--market', help='Target market (houston, dallas, etc.)')
    parser.add_argument('--custom-location', help='Custom location (90210, Austin TX, etc.)')
    
    # Test type options
    parser.add_argument('--scrape', action='store_true', help='Test job scraping')
    parser.add_argument('--cache', action='store_true', help='Test Supabase cache system')
    parser.add_argument('--classify', action='store_true', help='Test AI classification')
    parser.add_argument('--fair-chance', action='store_true', help='Test fair chance detection')
    parser.add_argument('--endorsements', action='store_true', help='Test endorsement detection')
    parser.add_argument('--storage', action='store_true', help='Test storage systems (Supabase + Airtable)')
    parser.add_argument('--pdf', action='store_true', help='Test PDF generation')
    parser.add_argument('--full', action='store_true', help='Test full pipeline')
    
    # Data options
    parser.add_argument('--csv', help='CSV file for testing')
    parser.add_argument('--limit', type=int, default=10, help='Job limit for testing (default: 10)')
    parser.add_argument('--terms', default='CDL driver', help='Search terms (default: "CDL driver")')
    parser.add_argument('--route', choices=['local', 'regional', 'otr', 'both'], default='both', help='Route filter')
    
    args = parser.parse_args()
    
    # Initialize test interface
    test = TestInterface()
    
    # Validate location arguments
    if (args.scrape or args.full) and not (args.market or args.custom_location):
        print("❌ Scraping and full pipeline tests require --market or --custom-location")
        return
    
    # Run requested tests
    results = {}
    
    if args.scrape:
        results['scrape'] = test.test_scraping(
            market=args.market,
            custom_location=args.custom_location,
            limit=args.limit,
            terms=args.terms
        )
        
    if args.cache:
        results['cache'] = test.test_supabase_cache(
            location=args.custom_location or (
                test.job_form.MARKET_SEARCH_QUERIES[args.market.title()] 
                if args.market and args.market.title() in test.job_form.MARKET_SEARCH_QUERIES 
                else None
            )
        )
        
    if args.classify:
        results['classify'] = test.test_classification(
            csv_path=args.csv,
            limit=args.limit
        )
        
    if args.fair_chance:
        results['fair_chance'] = test.test_fair_chance(
            csv_path=args.csv,
            limit=args.limit
        )
        
    if args.endorsements:
        results['endorsements'] = test.test_endorsements(
            csv_path=args.csv,
            limit=args.limit
        )
        
    if args.storage and args.csv:
        df = pd.read_csv(args.csv)
        results['storage'] = test.test_storage_systems(df.head(args.limit))
        
    if args.pdf:
        results['pdf'] = test.test_pdf_generation(csv_path=args.csv)
        
    if args.full:
        results['full_pipeline'] = test.test_full_pipeline(
            market=args.market,
            custom_location=args.custom_location,
            limit=args.limit,
            route_filter=args.route
        )
    
    # If no specific tests requested, show available options
    if not any([args.scrape, args.cache, args.classify, args.fair_chance, 
                args.endorsements, args.storage, args.pdf, args.full]):
        print("\n📋 === AVAILABLE TESTS ===")
        print("🔍 --scrape: Test job scraping (requires --market or --custom-location)")
        print("🧠 --cache: Test Supabase cache system") 
        print("🤖 --classify: Test AI classification (requires --csv)")
        print("⚖️ --fair-chance: Test fair chance detection (requires --csv)")
        print("🏅 --endorsements: Test endorsement detection (requires --csv)")
        print("💾 --storage: Test storage systems (requires --csv)")
        print("📄 --pdf: Test PDF generation (requires --csv)")
        print("🚀 --full: Test complete pipeline (requires --market or --custom-location)")
        print("\n📍 Location options:")
        print("   --market houston (or dallas, vegas, etc.)")
        print("   --custom-location 'Austin, TX' (or ZIP codes, cities, states)")
        print("\n📊 Example commands:")
        print("   python src/test_interface.py --scrape --custom-location 'Phoenix, AZ' --limit 5")
        print("   python src/test_interface.py --full --market houston --limit 20")
        print("   python src/test_interface.py --pdf --csv data/some_jobs.csv")
    
    # Summary
    if results:
        print(f"\n📊 === TEST RESULTS SUMMARY ===")
        for test_name, result in results.items():
            if result:
                print(f"✅ {test_name}: SUCCESS")
            else:
                print(f"❌ {test_name}: FAILED")

if __name__ == "__main__":
    main()