#!/usr/bin/env python3
"""
Location Normalizer for Search Queries
Standardizes location formats to "City, ST" for consistent search results.
Replaces foreign language locations with search query location format.
"""

import re
from typing import Optional

class LocationNormalizer:
    """
    Normalizes location strings to standard "City, ST" format using search query location.
    Detects non-ASCII characters and replaces with normalized search location.
    """
    
    def __init__(self):
        # US State abbreviation mapping
        self.state_map = {
            'california': 'CA', 'texas': 'TX', 'nevada': 'NV', 'florida': 'FL',
            'new york': 'NY', 'illinois': 'IL', 'pennsylvania': 'PA', 'ohio': 'OH',
            'georgia': 'GA', 'north carolina': 'NC', 'michigan': 'MI', 'new jersey': 'NJ',
            'virginia': 'VA', 'washington': 'WA', 'arizona': 'AZ', 'massachusetts': 'MA',
            'tennessee': 'TN', 'indiana': 'IN', 'missouri': 'MO', 'maryland': 'MD',
            'wisconsin': 'WI', 'colorado': 'CO', 'minnesota': 'MN', 'south carolina': 'SC',
            'alabama': 'AL', 'louisiana': 'LA', 'kentucky': 'KY', 'oregon': 'OR',
            'oklahoma': 'OK', 'connecticut': 'CT', 'utah': 'UT', 'iowa': 'IA',
            'arkansas': 'AR', 'mississippi': 'MS', 'kansas': 'KS', 'new mexico': 'NM',
            'nebraska': 'NE', 'west virginia': 'WV', 'idaho': 'ID', 'hawaii': 'HI',
            'new hampshire': 'NH', 'maine': 'ME', 'montana': 'MT', 'rhode island': 'RI',
            'delaware': 'DE', 'south dakota': 'SD', 'north dakota': 'ND', 'alaska': 'AK',
            'vermont': 'VT', 'wyoming': 'WY'
        }
    
    def has_non_ascii(self, text: str) -> bool:
        """Check if text contains non-ASCII characters (foreign language)."""
        if not text or not isinstance(text, str):
            return False
        return any(ord(char) > 127 for char in text)
    
    def normalize_location_format(self, location: str) -> str:
        """
        Normalize location to "City, ST" format.
        
        Args:
            location: Location string to normalize
            
        Returns:
            Normalized location in "City, ST" format
        """
        if not location or not isinstance(location, str):
            return location
        
        # Clean up the location
        location = location.strip()
        
        # Split by comma and clean parts
        parts = [part.strip() for part in location.split(',')]
        
        if len(parts) >= 2:
            city = parts[0]
            state_part = parts[1].lower().strip()
            
            # Check if state needs abbreviation
            if state_part in self.state_map:
                return f"{city}, {self.state_map[state_part]}"
            elif len(state_part) == 2 and state_part.upper() in self.state_map.values():
                return f"{city}, {state_part.upper()}"
        
        return location
    
    def normalize_job_location(self, job_location: str, search_location: str) -> str:
        """
        Main normalization function: replace foreign locations with search location format.
        
        Args:
            job_location: Original job location (might be foreign language)
            search_location: Search query location (e.g., "Dallas, TX")
            
        Returns:
            Normalized location - search location if foreign detected, otherwise normalized job location
        """
        if not job_location:
            return job_location
        
        # If job location has foreign characters, use search location format
        if self.has_non_ascii(job_location):
            normalized_search = self.normalize_location_format(search_location)
            return normalized_search if normalized_search else search_location
        
        # Otherwise just normalize the English location
        return self.normalize_location_format(job_location)
    
    def process_dataframe_locations(self, df, location_column: str, search_location: str) -> int:
        """
        Process all locations in a DataFrame using search location for foreign languages.
        
        Args:
            df: DataFrame containing job data
            search_location: Search query location (e.g., "Dallas, TX") 
            location_column: Name of the location column to process
            
        Returns:
            Number of locations normalized/replaced
        """
        if location_column not in df.columns:
            return 0
        
        normalized_count = 0
        normalized_search = self.normalize_location_format(search_location)
        
        for idx, row in df.iterrows():
            original_location = row[location_column]
            processed_location = self.normalize_job_location(original_location, search_location)
            
            if processed_location != original_location:
                df.loc[idx, location_column] = processed_location
                normalized_count += 1
        
        return normalized_count


def test_location_normalizer():
    """Test the LocationNormalizer"""
    print("Testing LocationNormalizer...")
    
    normalizer = LocationNormalizer()
    search_location = "Dallas, TX"  # What user searched for
    
    # Test job locations (some foreign, some English)
    test_locations = [
        "アメリカ合衆国 Nevada, ボールダー・シティ",  # Japanese → should become "Dallas, TX"
        "Los Angeles, California, Estados Unidos",     # Spanish → should become "Dallas, TX" 
        "カリフォルニア州ロサンゼルス",                  # Japanese → should become "Dallas, TX"
        "Houston, Texas",                              # English → should become "Houston, TX"
        "Dallas, TX",                                  # Already correct → stays same
        "New York, NY",                                # English, correct → stays same
        "フロリダ州マイアミ"                           # Japanese → should become "Dallas, TX"
    ]
    
    print(f"\n🔍 Search Location: '{search_location}'")
    print("=" * 60)
    
    for job_location in test_locations:
        result = normalizer.normalize_job_location(job_location, search_location)
        has_foreign = normalizer.has_non_ascii(job_location)
        status = "🌐" if has_foreign else "📍"
        
        print(f"{status} Job Location: '{job_location}'")
        print(f"    Result: '{result}'")
        
        if has_foreign:
            print(f"    ✅ Foreign language detected → used search location")
        elif result != job_location:
            print(f"    ✅ Normalized format")
        else:
            print(f"    ➡️  No change needed")
        print()
    
    print("✅ Location normalization test complete!")


if __name__ == "__main__":
    test_location_normalizer()