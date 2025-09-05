"""
Advanced Job Quality Filtering System

Implements machine learning-based quality detection, company reputation scoring,
salary validation, and job description quality assessment.
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from pathlib import Path

@dataclass
class CompanyProfile:
    """Company reputation and quality profile"""
    name: str
    reputation_score: float  # 0-1 scale
    known_good: bool
    known_bad: bool
    salary_reliability: float  # 0-1 scale
    job_quality_score: float  # 0-1 scale
    flags: List[str]  # Warning flags

@dataclass
class JobQualityScore:
    """Comprehensive job quality assessment"""
    overall_score: float  # 0-1 scale
    company_score: float
    salary_score: float
    description_score: float
    title_score: float
    location_score: float
    flags: List[str]
    recommendations: List[str]

class AdvancedJobFilter:
    """Advanced filtering system with ML-based quality detection"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Load company profiles and quality data
        self.company_profiles = self._load_company_profiles()
        self.suspicious_patterns = self._load_suspicious_patterns()
        self.quality_keywords = self._load_quality_keywords()
        
        # Salary validation parameters
        self.salary_ranges = {
            'CDL-A': {'min': 45000, 'max': 120000, 'median': 65000},
            'CDL-B': {'min': 35000, 'max': 80000, 'median': 50000},
            'Local': {'min': 40000, 'max': 85000, 'median': 55000},
            'OTR': {'min': 50000, 'max': 120000, 'median': 70000},
            'Regional': {'min': 45000, 'max': 90000, 'median': 60000}
        }
    
    def _load_company_profiles(self) -> Dict[str, CompanyProfile]:
        """Load company reputation profiles"""
        # In a real system, this would load from database or ML model
        known_good_companies = {
            'swift transportation', 'werner enterprises', 'schneider', 'jb hunt',
            'prime inc', 'roehl transport', 'knight transportation', 'maverick',
            'crete carrier', 'system transport', 'stevens transport'
        }
        
        known_bad_companies = {
            'cr england', 'western express', 'swift (owner operator)', 
            'lease purchase', 'owner operator opportunity'
        }
        
        suspicious_terms = {
            'make $5000 weekly', 'no experience necessary', 'easy money',
            'work from home', 'immediate hire', 'guaranteed income'
        }
        
        profiles = {}
        
        # Create profiles for known good companies
        for company in known_good_companies:
            profiles[company.lower()] = CompanyProfile(
                name=company,
                reputation_score=0.8,
                known_good=True,
                known_bad=False,
                salary_reliability=0.9,
                job_quality_score=0.8,
                flags=[]
            )
        
        # Create profiles for known problematic companies
        for company in known_bad_companies:
            profiles[company.lower()] = CompanyProfile(
                name=company,
                reputation_score=0.3,
                known_good=False,
                known_bad=True,
                salary_reliability=0.4,
                job_quality_score=0.3,
                flags=['known_problematic']
            )
        
        return profiles
    
    def _load_suspicious_patterns(self) -> Dict[str, List[str]]:
        """Load patterns that indicate low-quality jobs"""
        return {
            'unrealistic_salary': [
                r'\$[5-9]\d{3,}.*week', r'\$[1-9]\d{4,}.*week',
                r'\$200.*day', r'\$300.*day', r'\$400.*day'
            ],
            'vague_requirements': [
                r'no experience.*necessary', r'immediate.*start',
                r'guaranteed.*income', r'easy.*money'
            ],
            'lease_purchase_scams': [
                r'lease.*purchase', r'owner.*operator.*opportunity',
                r'be.*your.*own.*boss', r'truck.*ownership'
            ],
            'training_mills': [
                r'paid.*training.*immediate', r'fast.*track.*cdl',
                r'get.*cdl.*fast', r'quick.*training'
            ],
            'location_spam': [
                r'multiple.*locations', r'nationwide.*hiring',
                r'all.*states', r'50.*states'
            ]
        }
    
    def _load_quality_keywords(self) -> Dict[str, List[str]]:
        """Load keywords that indicate job quality"""
        return {
            'benefits_good': [
                'health insurance', 'dental', 'vision', '401k', 'retirement',
                'paid vacation', 'pto', 'per diem', 'bonuses'
            ],
            'equipment_good': [
                'new trucks', '2023', '2024', 'automatic transmission',
                'apu', 'inverter', 'comfortable', 'modern fleet'
            ],
            'schedule_good': [
                'home weekly', 'home weekends', 'local', 'regional',
                'predictable schedule', 'no forced dispatch'
            ],
            'pay_structure_good': [
                'per mile', 'hourly', 'salary', 'percentage',
                'performance bonus', 'safety bonus'
            ]
        }
    
    def assess_job_quality(self, job_row: pd.Series) -> JobQualityScore:
        """Comprehensive job quality assessment"""
        company_name = str(job_row.get('source.company', '')).lower()
        job_title = str(job_row.get('source.title', '')).lower()
        description = str(job_row.get('source.description', '')).lower()
        salary_text = str(job_row.get('source.salary', '')).lower()
        location = str(job_row.get('source.location', '')).lower()
        
        # Component scores
        company_score = self._assess_company_quality(company_name)
        salary_score = self._assess_salary_quality(salary_text, job_title)
        description_score = self._assess_description_quality(description)
        title_score = self._assess_title_quality(job_title)
        location_score = self._assess_location_quality(location)
        
        # Collect flags and recommendations
        flags = []
        recommendations = []
        
        # Check for suspicious patterns
        for pattern_type, patterns in self.suspicious_patterns.items():
            for pattern in patterns:
                if re.search(pattern, description + ' ' + job_title + ' ' + salary_text):
                    flags.append(f'suspicious_{pattern_type}')
        
        # Generate recommendations
        if company_score < 0.5:
            recommendations.append("Research company reputation before applying")
        if salary_score < 0.4:
            recommendations.append("Verify salary claims - may be unrealistic")
        if description_score < 0.5:
            recommendations.append("Job description may lack important details")
        
        # Calculate overall score (weighted average)
        overall_score = (
            company_score * 0.3 +
            salary_score * 0.25 +
            description_score * 0.25 +
            title_score * 0.1 +
            location_score * 0.1
        )
        
        # Apply flags penalty
        flag_penalty = min(0.3, len(flags) * 0.1)
        overall_score = max(0.0, overall_score - flag_penalty)
        
        return JobQualityScore(
            overall_score=overall_score,
            company_score=company_score,
            salary_score=salary_score,
            description_score=description_score,
            title_score=title_score,
            location_score=location_score,
            flags=flags,
            recommendations=recommendations
        )
    
    def _assess_company_quality(self, company_name: str) -> float:
        """Assess company reputation and quality"""
        if not company_name or company_name == 'nan':
            return 0.5  # Neutral for unknown
        
        # Direct company profile lookup
        if company_name in self.company_profiles:
            return self.company_profiles[company_name].reputation_score
        
        # Partial matching for known companies
        for known_company, profile in self.company_profiles.items():
            if known_company in company_name or company_name in known_company:
                return profile.reputation_score * 0.8  # Slight penalty for partial match
        
        # Check for suspicious company name patterns
        suspicious_indicators = [
            'llc', 'inc', 'hiring now', 'immediate', 'nationwide',
            'transportation services', 'logistics', 'freight'
        ]
        
        score = 0.6  # Default neutral
        
        # Penalty for overly generic names
        generic_count = sum(1 for indicator in suspicious_indicators if indicator in company_name)
        if generic_count >= 2:
            score -= 0.2
        
        return max(0.1, min(1.0, score))
    
    def _assess_salary_quality(self, salary_text: str, job_title: str) -> float:
        """Assess salary information quality and realism"""
        if not salary_text or salary_text == 'nan':
            return 0.5  # Neutral for missing salary
        
        score = 0.7  # Start with good score
        
        # Extract salary numbers
        salary_numbers = re.findall(r'\$?[\d,]+', salary_text)
        if not salary_numbers:
            return 0.3  # Poor score for no salary info
        
        # Convert to numbers
        try:
            amounts = []
            for num_str in salary_numbers:
                clean_num = re.sub(r'[,$]', '', num_str)
                if clean_num.isdigit():
                    amounts.append(int(clean_num))
        except:
            return 0.4
        
        if not amounts:
            return 0.4
        
        # Check against realistic ranges
        max_amount = max(amounts)
        
        # Determine job type for salary comparison
        job_type = 'CDL-A'  # Default
        if 'local' in job_title:
            job_type = 'Local'
        elif 'otr' in job_title or 'over the road' in job_title:
            job_type = 'OTR'
        elif 'regional' in job_title:
            job_type = 'Regional'
        
        expected_range = self.salary_ranges.get(job_type, self.salary_ranges['CDL-A'])
        
        # Weekly salary checks
        if 'week' in salary_text:
            weekly_amount = max_amount
            annual_equivalent = weekly_amount * 52
            
            if annual_equivalent > expected_range['max'] * 1.5:
                score -= 0.4  # Probably unrealistic
            elif annual_equivalent < expected_range['min']:
                score -= 0.2  # Below market rate
        
        # Monthly salary checks
        elif 'month' in salary_text:
            monthly_amount = max_amount
            annual_equivalent = monthly_amount * 12
            
            if annual_equivalent > expected_range['max'] * 1.5:
                score -= 0.4
            elif annual_equivalent < expected_range['min']:
                score -= 0.2
        
        # Annual salary checks
        elif max_amount > 20000:  # Assume it's annual
            if max_amount > expected_range['max'] * 1.5:
                score -= 0.4
            elif max_amount < expected_range['min']:
                score -= 0.2
        
        # Check for unrealistic promises
        unrealistic_patterns = [
            r'\$5000.*week', r'\$6000.*week', r'\$200.*day',
            r'guaranteed.*\$', r'up.*to.*\$[5-9]\d{3}'
        ]
        
        for pattern in unrealistic_patterns:
            if re.search(pattern, salary_text):
                score -= 0.3
                break
        
        return max(0.1, min(1.0, score))
    
    def _assess_description_quality(self, description: str) -> float:
        """Assess job description quality and completeness"""
        if not description or description == 'nan':
            return 0.2
        
        score = 0.5  # Start neutral
        
        # Length check - good descriptions are detailed
        word_count = len(description.split())
        if word_count > 200:
            score += 0.2
        elif word_count < 50:
            score -= 0.2
        
        # Check for quality indicators
        quality_indicators = 0
        for category, keywords in self.quality_keywords.items():
            if any(keyword in description for keyword in keywords):
                quality_indicators += 1
        
        # Bonus for comprehensive information
        if quality_indicators >= 3:
            score += 0.3
        elif quality_indicators >= 2:
            score += 0.1
        
        # Check for red flags
        red_flags = [
            'no experience necessary', 'immediate start', 'guaranteed income',
            'easy money', 'make money fast', 'work from home'
        ]
        
        red_flag_count = sum(1 for flag in red_flags if flag in description)
        score -= red_flag_count * 0.15
        
        # Grammar and professionalism check (basic)
        if description.count('!') > 3:
            score -= 0.1  # Too many exclamation points
        
        if description.isupper():
            score -= 0.2  # All caps is unprofessional
        
        return max(0.1, min(1.0, score))
    
    def _assess_title_quality(self, job_title: str) -> float:
        """Assess job title quality and specificity"""
        if not job_title or job_title == 'nan':
            return 0.3
        
        score = 0.6  # Start with decent score
        
        # Good title indicators
        good_indicators = [
            'cdl', 'driver', 'truck driver', 'local', 'regional', 'otr',
            'class a', 'experienced', 'company driver'
        ]
        
        good_count = sum(1 for indicator in good_indicators if indicator in job_title)
        score += good_count * 0.1
        
        # Bad title indicators
        bad_indicators = [
            'make money', 'easy', 'immediate', 'guaranteed',
            'owner operator', 'lease purchase'
        ]
        
        bad_count = sum(1 for indicator in bad_indicators if indicator in job_title)
        score -= bad_count * 0.2
        
        # Length and specificity
        if len(job_title) > 80:
            score -= 0.1  # Too long, probably spam
        elif len(job_title) < 10:
            score -= 0.2  # Too short, not descriptive
        
        return max(0.1, min(1.0, score))
    
    def _assess_location_quality(self, location: str) -> float:
        """Assess location specificity and validity"""
        if not location or location == 'nan':
            return 0.4
        
        score = 0.7  # Start with good score
        
        # Check for specific location indicators
        if ',' in location:  # City, State format
            score += 0.1
        
        # Check for vague locations (red flags)
        vague_patterns = [
            'nationwide', 'multiple locations', 'various locations',
            'all states', '50 states', 'usa', 'united states'
        ]
        
        for pattern in vague_patterns:
            if pattern in location:
                score -= 0.3
                break
        
        # State abbreviation check
        state_abbreviations = [
            'al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga',
            'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md',
            'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj',
            'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc',
            'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 'wy'
        ]
        
        location_words = location.lower().split()
        has_state = any(word in state_abbreviations for word in location_words)
        if has_state:
            score += 0.1
        
        return max(0.1, min(1.0, score))
    
    def filter_dataframe(self, df: pd.DataFrame, min_quality_score: float = 0.6) -> pd.DataFrame:
        """Filter DataFrame based on advanced quality scoring"""
        if df.empty:
            return df
        
        self.logger.info(f"Applying advanced quality filtering to {len(df)} jobs")
        
        # Calculate quality scores for all jobs
        quality_scores = []
        detailed_scores = []
        
        for idx, row in df.iterrows():
            quality_assessment = self.assess_job_quality(row)
            quality_scores.append(quality_assessment.overall_score)
            detailed_scores.append(quality_assessment)
        
        # Add quality columns to DataFrame
        df_filtered = df.copy()
        df_filtered['quality.overall_score'] = quality_scores
        df_filtered['quality.company_score'] = [s.company_score for s in detailed_scores]
        df_filtered['quality.salary_score'] = [s.salary_score for s in detailed_scores]
        df_filtered['quality.description_score'] = [s.description_score for s in detailed_scores]
        df_filtered['quality.flags'] = [','.join(s.flags) for s in detailed_scores]
        df_filtered['quality.recommendations'] = [','.join(s.recommendations) for s in detailed_scores]
        
        # Filter based on minimum quality score
        high_quality_df = df_filtered[df_filtered['quality.overall_score'] >= min_quality_score]
        
        filtered_count = len(df) - len(high_quality_df)
        self.logger.info(f"Filtered out {filtered_count} low-quality jobs")
        self.logger.info(f"Remaining jobs: {len(high_quality_df)}")
        
        return high_quality_df
    
    def generate_quality_report(self, df: pd.DataFrame) -> Dict:
        """Generate quality assessment report for job dataset"""
        if df.empty:
            return {"error": "No jobs to analyze"}
        
        quality_scores = []
        flag_counts = {}
        
        for idx, row in df.iterrows():
            assessment = self.assess_job_quality(row)
            quality_scores.append(assessment.overall_score)
            
            for flag in assessment.flags:
                flag_counts[flag] = flag_counts.get(flag, 0) + 1
        
        avg_quality = np.mean(quality_scores)
        quality_distribution = {
            'excellent': sum(1 for s in quality_scores if s >= 0.8),
            'good': sum(1 for s in quality_scores if 0.6 <= s < 0.8),
            'fair': sum(1 for s in quality_scores if 0.4 <= s < 0.6),
            'poor': sum(1 for s in quality_scores if s < 0.4)
        }
        
        return {
            'total_jobs': len(df),
            'average_quality_score': avg_quality,
            'quality_distribution': quality_distribution,
            'common_issues': sorted(flag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            'recommendations': self._generate_dataset_recommendations(avg_quality, flag_counts)
        }
    
    def _generate_dataset_recommendations(self, avg_quality: float, flag_counts: Dict) -> List[str]:
        """Generate recommendations for improving job dataset quality"""
        recommendations = []
        
        if avg_quality < 0.5:
            recommendations.append("Dataset quality is below average - consider refining job sources")
        
        # Check for common issues
        if 'suspicious_unrealistic_salary' in flag_counts and flag_counts['suspicious_unrealistic_salary'] > 5:
            recommendations.append("Many jobs have unrealistic salary claims - implement salary validation")
        
        if 'suspicious_lease_purchase_scams' in flag_counts:
            recommendations.append("Detected lease-purchase opportunities - these often exploit drivers")
        
        if avg_quality > 0.7:
            recommendations.append("Good job quality overall - current filtering is working well")
        
        return recommendations

def main():
    """Test advanced job filtering"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced Job Quality Filter')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode')
    parser.add_argument('--sample-size', type=int, default=100, help='Sample size for testing')
    
    args = parser.parse_args()
    
    if args.test_mode:
        # Create test data
        test_jobs = pd.DataFrame({
            'source.title': [
                'CDL-A Driver - Local Route',
                'Make $5000 Weekly - Owner Operator',
                'Experienced Truck Driver - Swift Transportation',
                'IMMEDIATE HIRE!!! MAKE MONEY NOW!!!',
                'Regional CDL Driver - Home Weekends'
            ],
            'source.company': [
                'Local Logistics LLC',
                'Owner Operator Express',
                'Swift Transportation',
                'Fast Cash Trucking',
                'Werner Enterprises'
            ],
            'source.description': [
                'Looking for experienced CDL-A drivers for local routes. Competitive pay, health insurance, home daily.',
                'BE YOUR OWN BOSS! Lease purchase opportunity! Make $5000 per week guaranteed! No money down!',
                'Swift Transportation is hiring experienced drivers. Comprehensive benefits, modern equipment, safety bonuses.',
                'MAKE MONEY FAST!!! No experience necessary! Immediate start! Easy money!',
                'Regional position with Werner. Home weekends, per diem, 401k, paid vacation. Modern fleet.'
            ],
            'source.salary': [
                '$60,000 - $75,000 annually',
                '$5,000 per week guaranteed',
                '$0.55 per mile',
                '$200 per day easy money',
                '$65,000 yearly'
            ]
        })
        
        # Test the filter
        filter_system = AdvancedJobFilter()
        
        print("🧪 Testing Advanced Job Filter")
        print("=" * 50)
        
        for idx, row in test_jobs.iterrows():
            assessment = filter_system.assess_job_quality(row)
            print(f"\nJob {idx + 1}: {row['source.title']}")
            print(f"Overall Score: {assessment.overall_score:.2f}")
            print(f"Company Score: {assessment.company_score:.2f}")
            print(f"Salary Score: {assessment.salary_score:.2f}")
            print(f"Description Score: {assessment.description_score:.2f}")
            if assessment.flags:
                print(f"Flags: {', '.join(assessment.flags)}")
            if assessment.recommendations:
                print(f"Recommendations: {', '.join(assessment.recommendations)}")
        
        # Generate report
        report = filter_system.generate_quality_report(test_jobs)
        print(f"\n📊 Dataset Quality Report")
        print(f"Average Quality: {report['average_quality_score']:.2f}")
        print(f"Distribution: {report['quality_distribution']}")

if __name__ == '__main__':
    main()