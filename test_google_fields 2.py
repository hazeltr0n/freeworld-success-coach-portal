import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_google_careers_fields():
    api_key = os.getenv('OUTSCRAPER_API_KEY')
    headers = {'X-API-KEY': api_key}
    
    url = "https://api.outscraper.cloud/google-search-careers"
    params = {
        'query': 'CDL driver Dallas TX',
        'pagesPerQuery': 1,
        'async': 'false'
    }
    
    print("Testing Google Careers to see field structure...")
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Google Careers response structure:")
        print(json.dumps(data, indent=2)[:1000] + "...")
        
        # Look for actual job data
        if data.get('data') and len(data['data']) > 0:
            first_result = data['data'][0]
            if isinstance(first_result, list) and len(first_result) > 0:
                first_job = first_result[0]
                print("\n📋 First job fields:")
                for key, value in first_job.items():
                    print(f"  {key}: {str(value)[:100]}...")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_google_careers_fields()