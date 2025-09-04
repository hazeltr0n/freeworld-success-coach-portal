import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Add your OpenAI API key to .env file
openai_key = os.getenv('OPENAI_API_KEY')

if openai_key:
    print("✅ OpenAI key found")
    client = OpenAI(api_key=openai_key)
    
    # Test a simple classification
    test_job = {
        'title': 'CDL Driver',
        'company': 'ABC Trucking', 
        'description': 'We need CDL-A drivers. No experience required, we will train you.'
    }
    
    print("Testing job classification...")
    # Your classification logic would go here
    
else:
    print("❌ No OpenAI key found")
    print("Add OPENAI_API_KEY to your .env file")