import os
import sys
import glob
import argparse
from dotenv import load_dotenv
from pipeline import FreeWorldJobPipeline

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='🚛 FreeWorld CDL Job Scraper - Full Pipeline')
    parser.add_argument('--mode', choices=['pipeline', 'test'], default='pipeline', 
                       help='Run mode: pipeline (process files) or test (API test)')
    parser.add_argument('--files', nargs='+', 
                       help='Input files to process (CSV or Excel)')
    parser.add_argument('--output', default='freeworld_jobs',
                       help='Output file prefix')
    parser.add_argument('--auto', action='store_true',
                       help='Auto-process all CSV/Excel files in data/ directory')
    
    args = parser.parse_args()
    
    if args.mode == 'test':
        test_apis()
        return
    
    # Pipeline mode
    print("🚛 FreeWorld CDL Job Scraper - Full Pipeline")
    print("=" * 50)
    
    # Determine input files
    input_files = []
    
    if args.auto:
        # Auto-discover files in data directory
        data_files = glob.glob("data/*.csv") + glob.glob("data/*.xlsx") + glob.glob("data/*.xls")
        if data_files:
            input_files = data_files
            print(f"📁 Auto-discovered {len(input_files)} files in data/ directory")
        else:
            print("❌ No CSV or Excel files found in data/ directory")
            return
    elif args.files:
        # Use specified files
        input_files = args.files
        print(f"📁 Processing {len(input_files)} specified files")
        
        # Validate files exist
        missing_files = [f for f in input_files if not os.path.exists(f)]
        if missing_files:
            print(f"❌ Files not found: {missing_files}")
            return
    else:
        print("❌ No input files specified. Use --files or --auto")
        print("Examples:")
        print("  python main.py --auto")
        print("  python main.py --files data/jobs1.csv data/jobs2.xlsx")
        return
    
    # Run the pipeline
    pipeline = FreeWorldJobPipeline()
    
    try:
        results = pipeline.run_full_pipeline(input_files, args.output)
        
        if results:
            print(f"\n🎉 Pipeline completed successfully!")
            print(f"📊 Summary: {results['summary']['final_count']} final jobs from {results['summary']['initial_count']} initial jobs")
            print(f"📈 Retention rate: {results['summary']['retention_rate']:.1f}%")
            print(f"📁 Output files:")
            for file_type, file_path in results['files'].items():
                if file_path:
                    print(f"  {file_type}: {file_path}")
        else:
            print("❌ Pipeline failed - no results generated")
            
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        sys.exit(1)

def test_apis():
    """Test the Outscraper APIs"""
    import requests
    
    api_key = os.getenv('OUTSCRAPER_API_KEY')
    if not api_key:
        print("❌ OUTSCRAPER_API_KEY not found in environment")
        return
    
    headers = {'X-API-KEY': api_key}
    
    print("🚛 Testing FreeWorld Job APIs...")
    
    # Test Indeed API
    print("\n1️⃣ Testing Indeed API...")
    indeed_url = "https://api.outscraper.cloud/indeed-search"
    indeed_params = {
        'query': 'https://www.indeed.com/jobs?q=CDL+driver&l=Dallas%2C+TX',
        'limit': 5,
        'async': 'false'
    }
    
    try:
        indeed_response = requests.get(indeed_url, headers=headers, params=indeed_params, timeout=30)
        print(f"Indeed Status: {indeed_response.status_code}")
        
        if indeed_response.status_code == 200:
            data = indeed_response.json()
            if data.get('data') and len(data['data'][0]) > 0:
                jobs = data['data'][0]
                print(f"✅ Found {len(jobs)} Indeed jobs")
                
                # Show first job
                first_job = jobs[0]
                print(f"  First job: {first_job.get('title', 'N/A')}")
                print(f"  Company: {first_job.get('company', 'N/A')}")
                print(f"  Location: {first_job.get('formattedLocation', 'N/A')}")
            else:
                print("❌ No jobs found in Indeed response")
        else:
            print(f"❌ Indeed API error: {indeed_response.text[:200]}")
    except Exception as e:
        print(f"❌ Indeed API exception: {e}")
    
    # Test Google Careers API  
    print("\n2️⃣ Testing Google Careers API...")
    careers_url = "https://api.outscraper.cloud/google-search-careers"
    careers_params = {
        'query': 'CDL driver Dallas TX',
        'async': 'false'
    }
    
    try:
        careers_response = requests.get(careers_url, headers=headers, params=careers_params, timeout=30)
        print(f"Google Careers Status: {careers_response.status_code}")
        
        if careers_response.status_code == 200:
            print("✅ Google Careers API working")
        else:
            print(f"❌ Google Careers error: {careers_response.text[:200]}")
    except Exception as e:
        print(f"❌ Google Careers API exception: {e}")

if __name__ == "__main__":
    main()