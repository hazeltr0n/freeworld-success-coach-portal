import pandas as pd
import re

class RouteClassifier:
    """Classifies trucking jobs as Local, OTR, or Unknown based on job content"""
    
    def __init__(self):
        # Keywords that indicate local routes
        self.local_keywords = [
            "home daily", "daily home time", "day cab", "local", "shuttle driver", 
            "bus driver", "school bus", "paratransit", "dump truck", "yard driver", 
            "yard hostler", "ready mix", "sanitation", "garbage collection", "waste", 
            "port driver", "drayage", "container hauling", "roll-off", "belly dump",
            "student transport", "pupil transport", "isd", "airport shuttle", "airport",
            "construction", "concrete", "mixer", "home every night", "home nightly",
            "monday-friday", "monday through friday", "specific daily schedule"
        ]
        
        # Keywords that indicate over-the-road routes
        self.otr_keywords = [
            "otr", "over the road", "regional", "home weekly", "home bi-weekly", 
            "home every week", "home every 2 weeks", "home time", "lower 48 states", 
            "nationwide", "coast to coast", "mileage pay", "cpm", "per mile", 
            "paid by the mile", "team driver", "rider policy", "pet policy", 
            "pets allowed", "fridge", "inverter", "sleeper cab", "long haul",
            "cross country", "48 states", "weeks out", "away from home", "on the road"
        ]
        
        # Known OTR carriers
        self.known_otr_carriers = [
            'crst', 'stevens', 'swift', 'prime inc', 'jb hunt', 'schneider', 
            'werner', 'covenant', 'marten'
        ]
    
    def classify_route_type(self, title, description, company):
        """
        Classify a job as Local, OTR, or Unknown route type
        
        Args:
            title (str): Job title
            description (str): Job description
            company (str): Company name
            
        Returns:
            str: "Local", "OTR", "Local and OTR", or "Unknown"
        """
        combined_text = f"{title} {description}".lower()
        company_text = str(company).lower()

        # Check for specific indicators
        local_matches = any(keyword in combined_text for keyword in self.local_keywords)
        otr_matches = any(keyword in combined_text for keyword in self.otr_keywords)
        
        # Special case patterns
        pet_rider_match = "pet" in combined_text and "rider" in combined_text
        team_driver_match = "team driver" in combined_text
        lower_48_match = "lower 48 states" in combined_text
        regional_match = "regional" in combined_text and "home daily" not in combined_text
        long_home_time_match = "home every 12 days" in combined_text or "out 12 days" in combined_text
        known_otr_carrier = any(name in company_text for name in self.known_otr_carriers)
        yard_driver_match = "yard driver" in combined_text or "yard hostler" in combined_text
        
        # Pay pattern analysis (critical insight from expert)
        import re
        hourly_pay_match = bool(re.search(r'\$\d+\.?\d*\s*/\s*hour|\$\d+\.?\d*\s*per\s*hour|\$\d+\.?\d*\s*hr', combined_text))
        mileage_pay_match = bool(re.search(r'\$\d+\.?\d*\s*cpm|per mile|\$/mile|\$\.\d+\s*per\s*mile', combined_text))
        weekly_pay_match = bool(re.search(r'\$\d+,?\d*\s*-?\s*\$?\d+,?\d*\s*/?\s*week', combined_text))
        
        # Job title analysis (strong indicators)
        title_text = str(title).lower()
        local_title_match = "local" in title_text and "otr" not in title_text  # Don't override if OTR also mentioned
        airport_title_match = "airport" in title_text or "shuttle" in title_text
        otr_title_match = "otr" in title_text or "over the road" in title_text
        
        # Schedule pattern analysis
        weekday_schedule_match = bool(re.search(r'monday\s*-?\s*friday|m-f|monday through friday', combined_text))
        specific_hours_match = bool(re.search(r'\d+:\d+\s*(am|pm|a\.m\.|p\.m\.)', combined_text))

        # Classification logic (prioritize high-confidence patterns)
        
        # HIGHEST PRIORITY: Job titles (most reliable indicator)
        if otr_title_match:
            return "OTR"  # "OTR" in title overrides everything
        if yard_driver_match:
            return "Local"
        if local_title_match or airport_title_match:
            return "Local"  # Job title gives it away
            
        # SECOND PRIORITY: Pay patterns (your expert insight)
        if hourly_pay_match and not otr_matches:
            return "Local"  # Expert insight: hourly pay = Local (but not if OTR signals)
        
        # THIRD PRIORITY: Other OTR indicators
        if team_driver_match or lower_48_match or regional_match or long_home_time_match:
            return "OTR"
        if (mileage_pay_match or weekly_pay_match) and not local_matches:
            return "OTR"  # Expert insight: mileage/weekly pay = OTR
        if known_otr_carrier and not local_matches:
            return "OTR"
            
        # Standard keyword matching
        if otr_matches or pet_rider_match:
            return "OTR" if not local_matches else "Unknown"  # Changed from "Local and OTR"
        elif local_matches:
            return "Local"
        
        return "Unknown"
    
    def classify_jobs_dataframe(self, df):
        """
        Add route_type column to a DataFrame of jobs
        
        Args:
            df (pd.DataFrame): DataFrame with job_title, job_description, company columns
            
        Returns:
            pd.DataFrame: DataFrame with added route_type column
        """
        # Don't copy - modify in place to preserve all existing data
        df['route_type'] = df.apply(
            lambda row: self.classify_route_type(
                row.get('job_title', ''), 
                row.get('job_description', ''), 
                row.get('company', '')
            ), 
            axis=1
        )
        return df
    
    def get_route_type_summary(self, df):
        """Get summary statistics of route types"""
        if 'route_type' not in df.columns:
            return "No route_type column found. Run classify_jobs_dataframe first."
        
        summary = df['route_type'].value_counts()
        total = len(df)
        
        result = "📊 Route Type Summary:\n"
        for route_type, count in summary.items():
            percentage = (count / total) * 100
            emoji = "🏠" if route_type == "Local" else "🛣️" if route_type == "OTR" else "❓"
            result += f"  {emoji} {route_type}: {count} ({percentage:.1f}%)\n"
        
        return result

if __name__ == "__main__":
    # Test the route classifier
    classifier = RouteClassifier()
    
    # Test data
    test_jobs = [
        {
            'job_title': 'Local CDL Driver - Home Daily',
            'job_description': 'Drive delivery trucks in the Dallas area. Home every night.',
            'company': 'Local Delivery Co'
        },
        {
            'job_title': 'OTR CDL Driver',
            'job_description': 'Long haul driving across lower 48 states. Pet policy available.',
            'company': 'Swift Transportation'
        },
        {
            'job_title': 'Regional Driver',
            'job_description': 'Home weekly. Cover 3 state area.',
            'company': 'ABC Trucking'
        }
    ]
    
    # Test individual classification
    print("Individual classification tests:")
    for job in test_jobs:
        route_type = classifier.classify_route_type(
            job['job_title'], 
            job['job_description'], 
            job['company']
        )
        print(f"  {job['job_title']} → {route_type}")
    
    # Test DataFrame classification
    print("\nDataFrame classification test:")
    df = pd.DataFrame(test_jobs)
    df = classifier.classify_jobs_dataframe(df)
    print(classifier.get_route_type_summary(df))