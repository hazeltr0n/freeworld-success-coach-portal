import re
from bs4 import BeautifulSoup
import html
import pandas as pd

class FieldNormalizer:
    def __init__(self):
        # Common company name variations to normalize
        self.company_suffixes = [
            r'\s+inc\.?$', r'\s+llc\.?$', r'\s+corp\.?$', r'\s+ltd\.?$',
            r'\s+company$', r'\s+co\.?$', r'\s+corporation$'
        ]
        
        # State name to abbreviation mapping
        self.state_abbreviations = {
            'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
            'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA',
            'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA',
            'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
            'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
            'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH',
            'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC',
            'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA',
            'rhode island': 'RI', 'south carolina': 'SC', 'south dakota': 'SD', 'tennessee': 'TN',
            'texas': 'TX', 'utah': 'UT', 'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA',
            'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY', 'district of columbia': 'DC'
        }
        
        # Valid state abbreviations
        self.valid_states = set(self.state_abbreviations.values())
    
    def clean_html(self, text):
        """Remove HTML tags and decode HTML entities"""
        if not isinstance(text, str):
            return str(text) if text else ""
        
        # First decode HTML entities
        text = html.unescape(text)
        
        # Remove HTML tags using BeautifulSoup
        soup = BeautifulSoup(text, 'html.parser')
        clean_text = soup.get_text()
        
        # Clean up extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text
    
    def normalize_company_name(self, company):
        """Normalize company names for better matching"""
        if not isinstance(company, str):
            return str(company) if company else ""
        
        # Clean and lowercase
        normalized = company.lower().strip()
        
        # Remove common suffixes
        for suffix_pattern in self.company_suffixes:
            normalized = re.sub(suffix_pattern, '', normalized, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def normalize_location(self, location):
        """Normalize location to City, ST format (enhanced from Colab version)"""
        if not isinstance(location, str):
            return str(location) if location else ""
        
        return self.clean_location_city_state_only(location)
    
    def clean_location_city_state_only(self, location):
        """Advanced location cleaning from Colab version"""
        if pd.isnull(location) if 'pd' in globals() else location is None:
            return ""

        location = str(location).strip().lower()

        # Step 1: Translate known non-English city names
        foreign_city_map = {
            "グランドプレーリー": "grand prairie",
            "アーリントン": "arlington", 
            "ダラス": "dallas",
            "ヒューストン": "houston",
            # Add more as needed
        }
        for jp, en in foreign_city_map.items():
            location = location.replace(jp, en)

        # Step 2: Remove foreign "USA" phrases
        foreign_us_terms = [
            r'estados unidos', r'états-unis', r'verenigde staten',
            r'united states', r'アメリカ合衆国'
        ]
        for term in foreign_us_terms:
            location = re.sub(term, '', location)

        # Step 3: Clean non-ASCII + normalize spacing
        location = re.sub(r'[^\x00-\x7F]+', '', location)
        location = re.sub(r'\s+', ' ', location).strip()

        # Step 4: Remove ZIP codes more aggressively
        location = re.sub(r'\s+\d{5}(-\d{4})?$', '', location).strip()
        location = re.sub(r'\s+\d{5}$', '', location).strip()

        # Step 5: Extract city and state
        parts = [p.strip() for p in location.split(',')]
        if len(parts) >= 2:
            city = parts[0].title()
            state_part = parts[1].lower().strip()
            
            # Remove any remaining ZIP codes from state part
            state_part = re.sub(r'\s+\d{5}(-\d{4})?$', '', state_part).strip()
            state_part = re.sub(r'\s+\d{5}$', '', state_part).strip()

            # Step 6: Normalize full state names to abbreviations
            state = self.state_abbreviations.get(state_part, state_part.upper())
            return f"{city}, {state}"
        elif len(parts) == 1:
            # Handle single part that might be "City State ZIP"
            single_part = parts[0].strip()
            # Try to extract city and state from single string like "Dallas TX 75201"
            match = re.match(r'^(.+?)\s+([a-z]{2})\s*\d*$', single_part, re.IGNORECASE)
            if match:
                city = match.group(1).title()
                state = match.group(2).upper()
                return f"{city}, {state}"
            else:
                return single_part.title()
        else:
            return ""
    
    def _extract_city_state(self, location_str):
        """Extract city and state from location string"""
        # Remove extra whitespace
        location_str = re.sub(r'\s+', ' ', location_str).strip()
        
        # Pattern 1: City, ST (state abbreviation)
        match = re.search(r'^(.+?),\s*([A-Z]{2})$', location_str)
        if match:
            city = match.group(1).strip()
            state = match.group(2).upper()
            if state in self.valid_states:
                return self._title_case_city(city), state
        
        # Pattern 2: City, State Name
        match = re.search(r'^(.+?),\s*(.+?)$', location_str)
        if match:
            city = match.group(1).strip()
            state_name = match.group(2).strip().lower()
            
            # Check if it's a full state name
            if state_name in self.state_abbreviations:
                return self._title_case_city(city), self.state_abbreviations[state_name]
            
            # Check if it's already an abbreviation
            state_abbrev = state_name.upper()
            if state_abbrev in self.valid_states:
                return self._title_case_city(city), state_abbrev
        
        # Pattern 3: Just state name or abbreviation (no city)
        location_lower = location_str.lower().strip()
        if location_lower in self.state_abbreviations:
            return "", self.state_abbreviations[location_lower]
        
        if location_str.upper() in self.valid_states:
            return "", location_str.upper()
        
        # Couldn't parse - return None, None
        return None, None
    
    def _title_case_city(self, city):
        """Convert city name to proper title case"""
        # Handle special cases like "St. Louis", "Las Vegas", etc.
        words = city.split()
        title_words = []
        
        for word in words:
            # Handle abbreviations like St., Mt., etc.
            if word.lower() in ['st.', 'mt.', 'ft.']:
                title_words.append(word.title())
            # Handle prepositions and articles
            elif word.lower() in ['of', 'the', 'and', 'in', 'on', 'at', 'by', 'for']:
                title_words.append(word.lower())
            else:
                title_words.append(word.title())
        
        return ' '.join(title_words)
    
    def normalize_job_title(self, title):
        """Normalize job titles for better matching"""
        if not isinstance(title, str):
            return str(title) if title else ""
        
        # Clean basic formatting
        normalized = title.strip()
        
        # Remove common prefixes/suffixes that don't affect job matching
        # Remove salary ranges in titles
        normalized = re.sub(r'\$[\d,]+[-\s]*\$?[\d,]*\s*/?(?:year|yr|hour|hr)?', '', normalized, flags=re.IGNORECASE)
        
        # Remove "urgent" and similar indicators
        normalized = re.sub(r'\b(urgent|immediate|asap)\b', '', normalized, flags=re.IGNORECASE)
        
        # Clean up whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def normalize_job_record(self, job_record):
        """Normalize all fields in a job record"""
        normalized = job_record.copy()
        
        # Clean HTML from description
        if 'job_description' in normalized:
            normalized['job_description'] = self.clean_html(normalized['job_description'])
        
        # Normalize key fields
        if 'company' in normalized:
            normalized['company'] = self.normalize_company_name(normalized['company'])
            # Keep original for display purposes
            normalized['company_original'] = job_record.get('company', '')
        
        if 'location' in normalized:
            normalized['location'] = self.normalize_location(normalized['location'])
            normalized['location_original'] = job_record.get('location', '')
        
        if 'job_title' in normalized:
            normalized['job_title'] = self.normalize_job_title(normalized['job_title'])
            normalized['job_title_original'] = job_record.get('job_title', '')
        
        return normalized
    
    def normalize_job_list(self, jobs_list):
        """Normalize a list of job records"""
        return [self.normalize_job_record(job) for job in jobs_list]

if __name__ == "__main__":
    # Test the normalizer with various location formats
    normalizer = FieldNormalizer()
    
    test_locations = [
        'Dallas, TX 75201',
        'Houston, Texas',
        'Austin, TX, USA',
        'San Antonio, TX (Remote)',
        'Phoenix, Arizona 85001-1234',
        'Los Angeles, CA, United States',
        'New York, NY',
        'Miami, FL 33101',
        'Chicago, Illinois',
        'Atlanta, GA, USA (Remote)'
    ]
    
    print("Location normalization test:")
    for location in test_locations:
        normalized = normalizer.normalize_location(location)
        print(f"  '{location}' → '{normalized}'")
    
    print("\nFull job normalization test:")
    test_job = {
        'job_title': 'CDL Driver - URGENT! $75,000/year',
        'company': 'ABC Trucking Inc.',
        'location': 'Dallas, TX 75201, USA',
        'job_description': '<p>We need <strong>CDL drivers</strong> immediately!</p><br/>Great benefits &amp; pay.'
    }
    
    print("Original job:")
    for key, value in test_job.items():
        print(f"  {key}: {value}")
    
    normalized = normalizer.normalize_job_record(test_job)
    
    print("\nNormalized job:")
    for key, value in normalized.items():
        print(f"  {key}: {value}")