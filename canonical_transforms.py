"""
Canonical Transform Functions for FreeWorld Job Scraper
Pure functions that operate on the single canonical DataFrame
Each function only adds/updates its namespace - no deletions or overwrites
"""

import pandas as pd
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from jobs_schema import (
    ensure_schema, generate_job_id, COLUMN_REGISTRY, FIELD_POLICIES
)

# ==============================================================================
# SALARY PROCESSING HELPERS
# ==============================================================================

def _extract_salary_text(salary_snippet) -> str:
    """Extract basic salary text from Indeed's salarySnippet"""
    if not salary_snippet or not isinstance(salary_snippet, dict):
        return ''
    
    # Try to get text representation
    if 'text' in salary_snippet:
        return str(salary_snippet['text'])
    
    # Fallback: construct from other fields
    if 'baseSalary' in salary_snippet and salary_snippet['baseSalary']:
        base = salary_snippet['baseSalary']
        if 'range' in base and base['range']:
            min_val = base['range'].get('min', '')
            max_val = base['range'].get('max', '')
            unit = base.get('unitOfWork', '').lower()
            currency = salary_snippet.get('currencyCode', 'USD')
            
            if min_val and max_val:
                return f"${min_val}-${max_val} per {unit}"
            elif min_val:
                return f"${min_val} per {unit}"
    
    return ''

def _extract_salary_fields(salary_snippet) -> Dict[str, Any]:
    """Extract rich salary data from Indeed's salarySnippet for normalization"""
    fields = {}
    
    if not salary_snippet or not isinstance(salary_snippet, dict):
        return fields
    
    # Extract base salary (employer-provided)
    if 'baseSalary' in salary_snippet and salary_snippet['baseSalary']:
        base = salary_snippet['baseSalary']
        if 'range' in base and base['range']:
            fields['salary_base_min'] = base['range'].get('min', '')
            fields['salary_base_max'] = base['range'].get('max', '')
        fields['salary_base_unit'] = base.get('unitOfWork', '')
        fields['salary_base_currency'] = salary_snippet.get('currencyCode', '')
    
    # Extract estimated salary (Indeed's algorithm)
    if 'estimated' in salary_snippet and salary_snippet['estimated']:
        est = salary_snippet['estimated']
        if 'baseSalary' in est and est['baseSalary']:
            est_base = est['baseSalary']
            if 'range' in est_base and est_base['range']:
                fields['salary_estimated_min'] = est_base['range'].get('min', '')
                fields['salary_estimated_max'] = est_base['range'].get('max', '')
            fields['salary_estimated_unit'] = est_base.get('unitOfWork', '')
            fields['salary_estimated_currency'] = est.get('currencyCode', '')
    
    return fields

# ==============================================================================
# STAGE 1: INGESTION TRANSFORMS
# ==============================================================================

def transform_ingest_outscraper(raw_data: List[Dict], run_id: str) -> pd.DataFrame:
    """
    Convert raw Outscraper API data to canonical DataFrame format
    
    Args:
        raw_data: List of job dictionaries from Outscraper
        run_id: Unique identifier for this pipeline run
        
    Returns:
        DataFrame with source.* fields populated
    """
    if not raw_data:
        return ensure_schema(pd.DataFrame())
    
    df = pd.DataFrame(raw_data)
    
    # Debug: show what fields Indeed actually returns
    if len(df) > 0:
        print(f"🔍 Raw Indeed fields: {list(df.columns)}")
        if len(df) > 0:
            print(f"🔍 Sample row: title='{df.iloc[0].get('title', 'NOT_FOUND')}' company='{df.iloc[0].get('company', 'NOT_FOUND')}' formattedLocation='{df.iloc[0].get('formattedLocation', 'NOT_FOUND')}'")
    
    # Generate job IDs BEFORE schema enforcement (while we still have raw Indeed fields)
    job_ids = []
    debug_count = 0
    for _, row in df.iterrows():
        # Use raw Indeed field names directly
        company = str(row.get('company', ''))
        location = str(row.get('formattedLocation', ''))  
        title = str(row.get('title', ''))
        
        job_id = generate_job_id(company, location, title)
        job_ids.append(job_id)
        
        # Debug first few job IDs
        if debug_count < 5:
            print(f"🔍 Job ID #{debug_count + 1}:")
            print(f"    Company: '{company}' (len={len(company)})")
            print(f"    Location: '{location}' (len={len(location)})")  
            print(f"    Title: '{title}' (len={len(title)})")
            print(f"    MD5: {job_id}")
            debug_count += 1
    
    # Check for duplicates in raw job IDs
    unique_ids = len(set(job_ids))
    print(f"🔍 Job ID uniqueness: {unique_ids} unique out of {len(job_ids)} total")
    
    # Define field mapping for Indeed/Outscraper format
    source_mapping = {
        'title': 'source.title',
        'company': 'source.company',
        'snippet': 'source.description_raw',
        'formattedLocation': 'source.location_raw',
        'viewJobLink': 'source.url',  # Single unified URL field
        'salarySnippet': 'source.salary_raw',  # Will be processed separately
    }
    
    # Map raw API fields to canonical schema BEFORE schema enforcement
    print(f"🔍 Field Mapping Debug:")
    print(f"    Available Indeed fields: {list(df.columns)}")
    mapped_count = 0
    for api_field, canonical_field in source_mapping.items():
        if api_field in df.columns:
            df[canonical_field] = df[api_field].fillna('')
            mapped_count += 1
            print(f"    ✅ Mapped {api_field} → {canonical_field}")
        else:
            print(f"    ❌ Missing {api_field} (would map to {canonical_field})")
    print(f"    Total mappings: {mapped_count}/{len(source_mapping)}")
    
    # Apply schema enforcement AFTER field mapping
    df = ensure_schema(df)
    
    # Set the job IDs directly to the canonical field
    df['id.job'] = job_ids
    print(f"✅ Set {len(job_ids)} unique job IDs directly to canonical field")
    
    # Handle Indeed's complex salarySnippet structure
    if 'salarySnippet' in df.columns:
        df['source.salary_raw'] = df['salarySnippet'].apply(_extract_salary_text)
        
        # Extract rich salary data for normalization
        salary_fields = df['salarySnippet'].apply(_extract_salary_fields)
        for field, values in salary_fields.items():
            if field in df.columns:  # Only set if column exists in schema
                df[field] = values
    
    # Job IDs were already set above - no fallbacks needed
    
    # Detect actual source platform (Indeed vs Google) from raw data
    def detect_source_platform(row):
        # Check URL patterns or other indicators to determine if job came from Indeed or Google
        url = str(row.get('url', '') or row.get('link', ''))
        if 'indeed.com' in url.lower():
            return 'indeed'
        elif 'google.com' in url.lower() or 'jobs.google.com' in url.lower():
            return 'google'
        else:
            # Default to Indeed since most Outscraper jobs come from Indeed
            return 'indeed'
    
    # Apply source detection
    df['id.source'] = df.apply(detect_source_platform, axis=1)
    
    # Set metadata
    current_time = datetime.now().isoformat()
    return df.assign(**{
        'id.source_row': range(len(df)),
        'route.stage': 'ingested',
        'sys.created_at': current_time,
        'sys.updated_at': current_time,
        'sys.run_id': run_id,
        'sys.is_fresh_job': True,
        'sys.version': '3.0',
    })

def transform_ingest_google(raw_data: List[Dict], run_id: str) -> pd.DataFrame:
    """
    Convert raw Google Jobs API data to canonical DataFrame format
    
    Args:
        raw_data: List of job dictionaries from Google Jobs API
        run_id: Unique identifier for this pipeline run
        
    Returns:
        DataFrame with source.* fields populated
    """
    if not raw_data:
        return ensure_schema(pd.DataFrame())
    
    df = pd.DataFrame(raw_data)
    
    # Debug: show what fields Google actually returns
    if len(df) > 0:
        print(f"🔍 Raw Google fields: {list(df.columns)}")
        if len(df) > 0:
            print(f"🔍 Sample row: title='{df.iloc[0].get('title', 'NOT_FOUND')}' company='{df.iloc[0].get('company', 'NOT_FOUND')}' location='{df.iloc[0].get('location', 'NOT_FOUND')}'")
    
    # Generate job IDs BEFORE schema enforcement (while we still have raw Google fields)
    job_ids = []
    debug_count = 0
    for _, row in df.iterrows():
        # Use raw Google field names directly
        company = str(row.get('company', ''))
        location = str(row.get('location', ''))  
        title = str(row.get('title', ''))
        
        job_id = generate_job_id(company, location, title)
        job_ids.append(job_id)
        
        # Debug first few job IDs
        if debug_count < 3:
            print(f"🔍 Google Job ID #{debug_count + 1}:")
            print(f"    Company: '{company}' (len={len(company)})")
            print(f"    Location: '{location}' (len={len(location)})")  
            print(f"    Title: '{title}' (len={len(title)})")
            print(f"    MD5: {job_id}")
            debug_count += 1
    
    # Check for duplicates in raw job IDs
    unique_ids = len(set(job_ids))
    print(f"🔍 Google Job ID uniqueness: {unique_ids} unique out of {len(job_ids)} total")
    
    # Define field mapping for Google Jobs format
    google_mapping = {
        'title': 'source.title',
        'company': 'source.company',
        'location': 'source.location_raw',
        'description': 'source.description_raw',
        'apply_urls': 'source.url',  # Single unified URL field - will be processed separately
        'salary': 'source.salary_raw',
        'posted_date': 'source.posted_date'
    }
    
    # Map raw API fields to canonical schema BEFORE schema enforcement
    print(f"🔍 Google Field Mapping Debug:")
    print(f"    Available Google fields: {list(df.columns)}")
    mapped_count = 0
    for google_field, canonical_field in google_mapping.items():
        if google_field in df.columns:
            if google_field == 'apply_urls':
                # Extract first URL from JSON array structure and store in unified source.url field
                def extract_first_url(x):
                    try:
                        if pd.isna(x):
                            return ''
                        if isinstance(x, str) and x == '':
                            return ''
                        if hasattr(x, '__len__') and len(x) == 0:
                            return ''
                    except (ValueError, TypeError):
                        # Handle pandas array comparison issues
                        pass
                    
                    try:
                        # Parse JSON string containing array of URL objects
                        import json
                        if isinstance(x, str):
                            url_data = json.loads(x)
                        elif isinstance(x, list):
                            url_data = x
                        else:
                            return ''
                        
                        # Handle different URL data formats
                        if url_data and len(url_data) > 0:
                            # Handle simple string arrays (like our test data)
                            if isinstance(url_data[0], str):
                                return url_data[0]  # Return first URL string
                            
                            # Handle complex URL objects with apply_company info
                            # Known job board companies to deprioritize
                            job_boards = {'Indeed', 'LinkedIn', 'SimplyHired', 'ZipRecruiter', 'Monster', 'Glassdoor', 'CareerBuilder'}
                            
                            # First, look for direct company websites (not job boards)
                            for url_obj in url_data:
                                if isinstance(url_obj, dict):
                                    apply_company = url_obj.get('apply_company', '')
                                    if apply_company not in job_boards:
                                        url = url_obj.get('apply_url:', '') or url_obj.get('apply_url', '')
                                        if url:
                                            print(f"    🏢 Prioritizing direct company link: {apply_company}")
                                            return url
                            
                            # Fallback: use the first available URL (likely a job board)
                            first_url_obj = url_data[0]
                            if isinstance(first_url_obj, dict):
                                url = first_url_obj.get('apply_url:', '') or first_url_obj.get('apply_url', '')
                                apply_company = first_url_obj.get('apply_company', 'Unknown')
                                print(f"    📋 Using job board link: {apply_company}")
                                return url if url else ''
                            else:
                                return str(first_url_obj)  # Simple string URL
                        else:
                            return ''
                            
                    except (json.JSONDecodeError, KeyError, TypeError) as e:
                        print(f"⚠️ URL parsing error: {e}, raw value: {repr(x)}")
                        return ''
                
                df[canonical_field] = df[google_field].apply(extract_first_url)
            else:
                df[canonical_field] = df[google_field].fillna('')
            mapped_count += 1
            print(f"    ✅ Mapped {google_field} → {canonical_field}")
        else:
            print(f"    ❌ Missing {google_field} (would map to {canonical_field})")
    print(f"    Total mappings: {mapped_count}/{len(google_mapping)}")
    
    # Apply schema enforcement AFTER field mapping
    df = ensure_schema(df)
    
    # Set Google-specific job IDs directly to canonical field
    df['id.job'] = job_ids
    print(f"✅ Set {len(job_ids)} unique job IDs directly to canonical field")
    
    # Additional Google-specific metadata
    current_time = datetime.now().isoformat()  # Fixed: Consistent datetime format
    df = df.assign(**{
        'id.source': 'google',
        'id.source_row': range(len(df)),
        'route.stage': 'ingested',
        'sys.created_at': current_time,
        'sys.updated_at': current_time,
        'sys.run_id': run_id,
        'sys.is_fresh_job': True,
        'sys.version': '3.0',
    })
    
    print(f"✅ Google Jobs ingestion transform complete: {len(df)} jobs")
    return df

def transform_ingest_memory(memory_data: List[Dict], run_id: str) -> pd.DataFrame:
    """
    Convert memory database records to canonical DataFrame format
    
    Args:
        memory_data: List of job dictionaries from Supabase
        run_id: Current pipeline run identifier
        
    Returns:
        DataFrame with existing classifications preserved
    """
    if not memory_data:
        return ensure_schema(pd.DataFrame())
    
    df = pd.DataFrame(memory_data)
    
    # Map Supabase fields back to canonical schema BEFORE calling ensure_schema
    # (ensure_schema removes original columns, so we must do mapping first)
    memory_mapping = {
        'job_id': 'id.job',
        'job_title': 'source.title',
        'company': 'source.company',
        'location': 'source.location_raw',
        'job_description': 'source.description_raw',
        'salary': 'source.salary_raw',
        # AI fields (support both legacy and canonical keys)
        'match_level': 'ai.match',
        'match': 'ai.match',
        'match_reason': 'ai.reason',
        'reason': 'ai.reason',
        'summary': 'ai.summary',
        'fair_chance': 'ai.fair_chance',
        'endorsements': 'ai.endorsements',
        'route_type': 'ai.route_type',
        # Meta
        'market': 'meta.market',
        'tracked_url': 'meta.tracked_url',
        # System
        'classified_at': 'sys.classified_at',
        'classification_source': 'sys.classification_source'
    }
    
    # Fill fields from memory (do this before ensure_schema removes original columns)
    for memory_field, canonical_field in memory_mapping.items():
        if memory_field in df.columns:
            df[canonical_field] = df[memory_field].fillna('')
    
    # Consolidate URLs into single source.url field
    # Priority: apply_url (direct) -> indeed_job_url
    apply_urls = pd.Series(df.get('apply_url', ''))
    indeed_urls = pd.Series(df.get('indeed_job_url', ''))
    
    # Use first non-empty URL
    df['source.url'] = apply_urls.replace('', pd.NA).fillna(
        indeed_urls.replace('', pd.NA).fillna('')
    )
    
    print(f"🔗 Consolidated URLs: {len(df[df['source.url'] != ''])} jobs have URLs")
    
    # Now apply schema (this will preserve the mapped canonical fields)
    df = ensure_schema(df)
    
    # Set metadata for memory jobs
    current_time = datetime.now().isoformat()
    # Ensure classification source set for memory if missing
    if 'sys.classification_source' in df.columns:
        missing_src = df['sys.classification_source'].isna() | (df['sys.classification_source'] == '')
        df.loc[missing_src, 'sys.classification_source'] = 'supabase_memory'

    return df.assign(**{
        'id.source': 'memory',
        'route.stage': 'classified',
        'sys.updated_at': current_time,
        'sys.run_id': run_id,
        'sys.is_fresh_job': False,
        'sys.version': '3.0',
    })

# ==============================================================================
# STAGE 2: NORMALIZATION TRANSFORMS  
# ==============================================================================

def transform_normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize and clean job data - fills norm.* fields only
    
    Args:
        df: Canonical DataFrame with source.* fields populated
        
    Returns:
        DataFrame with norm.* fields added
    """
    
    # Handle empty DataFrame
    if len(df) == 0:
        return df
        
    def clean_html(text: str) -> str:
        """Remove HTML tags and normalize whitespace"""
        if pd.isna(text) or text == '':
            return ''
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', str(text))
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        # Clean up common artifacts
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
        return text.strip()
    
    def parse_location(location: str) -> Tuple[str, str, str]:
        """Parse location into city, state, full format"""
        if pd.isna(location) or location == '':
            return '', '', ''
        
        location = str(location).strip()
        
        # Handle "City, State ZIP" format
        if ',' in location:
            parts = location.split(',')
            city = parts[0].strip()
            state_part = parts[1].strip() if len(parts) > 1 else ''
            
            # Extract state from "State ZIP" format
            state_match = re.match(r'^([A-Z]{2})', state_part)
            state = state_match.group(1) if state_match else state_part[:2].upper()
            
            return city, state, f"{city}, {state}"
        else:
            # Single word - assume it's a city
            return location, '', location
    
    def parse_salary(salary_text: str) -> Dict[str, Any]:
        """Parse salary text into structured components"""
        if pd.isna(salary_text) or salary_text == '':
            return {
                'display': '',
                'min': None,
                'max': None,
                'unit': None,  # Use None instead of empty string for validation
                'currency': 'USD'
            }
        
        salary_text = str(salary_text).strip()
        
        # Handle JSON salary data from Indeed/Outscraper
        if salary_text.startswith('{') and 'baseSalary' in salary_text:
            try:
                import ast
                salary_dict = ast.literal_eval(salary_text)
                base_salary = salary_dict.get('baseSalary', {})
                if isinstance(base_salary, dict):
                    salary_range = base_salary.get('range', {})
                    if isinstance(salary_range, dict):
                        min_val = salary_range.get('min')
                        max_val = salary_range.get('max')
                        # Map unitOfWork to valid schema values
                        raw_unit = base_salary.get('unitOfWork', 'YEAR').upper()
                        unit_mapping = {
                            'HOUR': 'hour', 'HOURLY': 'hour', 'HR': 'hour',
                            'WEEK': 'week', 'WEEKLY': 'week', 'WK': 'week',
                            'MONTH': 'month', 'MONTHLY': 'month', 'MON': 'month',
                            'YEAR': 'year', 'YEARLY': 'year', 'ANNUAL': 'year', 'YR': 'year'
                        }
                        unit = unit_mapping.get(raw_unit, 'year')
                        currency = salary_dict.get('currencyCode', 'USD')
                        
                        # Create display text
                        if min_val and max_val:
                            display = f"${min_val:,} - ${max_val:,} per {unit}"
                        elif min_val:
                            display = f"${min_val:,} per {unit}"
                        else:
                            display = ""
                        
                        return {
                            'display': display,
                            'min': min_val,
                            'max': max_val,
                            'unit': unit,
                            'currency': currency
                        }
            except (ValueError, SyntaxError, KeyError):
                pass
        
        # Extract numbers using regex (fallback for simple salary strings)
        numbers = re.findall(r'[\d,]+(?:\.\d{2})?', salary_text)
        numbers = [float(n.replace(',', '')) for n in numbers if n and n.strip() and ',' not in n.strip()]
        
        # Determine unit
        if 'hour' in salary_text.lower():
            unit = 'hour'
        elif 'week' in salary_text.lower():
            unit = 'week'
        elif 'month' in salary_text.lower():
            unit = 'month'
        elif 'year' in salary_text.lower():
            unit = 'year'
        else:
            unit = 'year'  # Default assumption
        
        # Set min/max
        if len(numbers) >= 2:
            salary_min, salary_max = min(numbers), max(numbers)
        elif len(numbers) == 1:
            salary_min = salary_max = numbers[0]
        else:
            salary_min = salary_max = None
        
        return {
            'display': salary_text,
            'min': salary_min,
            'max': salary_max,
            'unit': unit,
            'currency': 'USD'
        }
    
    # Debug: Check source fields before normalization
    if len(df) > 0:
        sample_row = df.iloc[0]
        print(f"🔍 Normalize Debug - Source fields:")
        print(f"    source.title: '{sample_row.get('source.title', 'MISSING')}' (len={len(str(sample_row.get('source.title', '')))})")
        print(f"    source.company: '{sample_row.get('source.company', 'MISSING')}' (len={len(str(sample_row.get('source.company', '')))})")
        print(f"    source.description_raw: '{str(sample_row.get('source.description_raw', 'MISSING'))[:50]}...' (len={len(str(sample_row.get('source.description_raw', '')))})")
    
    # Apply normalization transforms
    normalized_fields = {}
    
    # Clean text fields
    normalized_fields['norm.title'] = df['source.title'].apply(clean_html)
    normalized_fields['norm.company'] = df['source.company'].apply(clean_html)
    normalized_fields['norm.description'] = df['source.description_raw'].apply(clean_html)
    
    # Parse locations
    location_data = df['source.location_raw'].apply(parse_location)
    normalized_fields['norm.city'] = location_data.apply(lambda x: x[0])
    normalized_fields['norm.state'] = location_data.apply(lambda x: x[1])
    normalized_fields['norm.location'] = location_data.apply(lambda x: x[2])
    
    # Parse salaries
    salary_data = df['source.salary_raw'].apply(parse_salary)
    normalized_fields['norm.salary_display'] = salary_data.apply(lambda x: x['display'])
    normalized_fields['norm.salary_min'] = salary_data.apply(lambda x: x['min'])
    normalized_fields['norm.salary_max'] = salary_data.apply(lambda x: x['max'])
    normalized_fields['norm.salary_unit'] = salary_data.apply(lambda x: x['unit'])
    normalized_fields['norm.salary_currency'] = salary_data.apply(lambda x: x['currency'])
    
    # Initialize QA fields during normalization
    current_date = datetime.now().date().isoformat()
    normalized_fields['qa.last_validated_at'] = current_date
    normalized_fields['qa.missing_required_fields'] = False  # TODO: implement actual validation
    normalized_fields['qa.flags'] = ''  # JSON list of validation issues
    normalized_fields['qa.data_quality_score'] = 1.0  # TODO: implement scoring
    
    # Update stage and timestamp
    normalized_fields['route.stage'] = 'normalized'
    current_time = datetime.now().isoformat()
    normalized_fields['sys.updated_at'] = current_time
    normalized_fields['sys.created_at'] = current_time  # Set created_at during first processing
    
    return df.assign(**normalized_fields)

# ==============================================================================
# STAGE 3: BUSINESS RULES TRANSFORMS
# ==============================================================================

def transform_business_rules(df: pd.DataFrame, filter_settings: Dict[str, bool] = None) -> pd.DataFrame:
    """
    Apply business rules and filters - fills rules.* fields only
    
    Args:
        df: DataFrame with norm.* fields populated
        filter_settings: Dict of filter names to enabled/disabled state
        
    Returns:
        DataFrame with rules.* fields added
    """
    if filter_settings is None:
        filter_settings = {
            'owner_op': True,
            'school_bus': True,
            'spam_filter': True,
            'experience_filter': True,
        }
    
    # Handle empty DataFrame  
    if len(df) == 0:
        return df
        
    def detect_owner_operator(description: str, title: str) -> bool:
        """Detect owner-operator positions (title-based detection only)"""
        title_lower = title.lower()
        description_lower = description.lower()
        
        # Skip mixed postings that hire both company drivers AND owner-operators
        if any(term in title_lower for term in [
            'drivers', 'driver', 'cdl', 'company driver'
        ]) and any(term in title_lower for term in [
            'owner operator', 'owner-operator'
        ]):
            return False  # Mixed posting - treat as company driver job
        
        # Strong title indicators - owner-op EXCLUSIVE positions only
        if any(pattern in title_lower for pattern in [
            'owner operator', 'owner-operator', 'fleet owner'
        ]):
            return True
        
        # Must own equipment (exclusive owner-op requirements)
        own_equipment_patterns = [
            'must own truck', 'must own tractor', 'must own trailer',
            'must have truck', 'must have tractor', 'must have trailer',
            'need own truck', 'need own tractor'
        ]
        if any(pattern in description_lower for pattern in own_equipment_patterns):
            return True
        
        # Only flag if clearly exclusive to owner-ops (not company driver positions with options)
        text = f"{title_lower} {description_lower}"
        
        # Skip if mentions company drivers (indicates mixed position)
        if 'company' in text:
            return False
        
        return False
    
    def detect_school_bus(description: str, title: str) -> bool:
        """Detect school bus driver positions"""
        text = f"{title} {description}".lower()
        return 'school bus' in text
    
    
    def detect_spam_source(company: str, description: str) -> bool:
        """Detect spam job postings"""
        spam_indicators = [
            'make money from home', 'work from home opportunity',
            'no experience necessary - will train', 'easy money',
            'MLM', 'multi-level marketing', 'pyramid'
        ]
        
        text = f"{company} {description}".lower()
        return any(indicator in text for indicator in spam_indicators)
    
    def generate_dedup_keys(row: pd.Series, market: str) -> Dict[str, str]:
        """Generate deduplication keys - CONSERVATIVE approach to handle empty fields"""
        company = str(row.get('norm.company', '') or row.get('source.company', '')).lower().strip()
        title = str(row.get('norm.title', '') or row.get('source.title', '')).lower().strip()
        location = str(row.get('norm.location', '') or row.get('source.location_raw', '')).lower().strip()
        
        # SAFETY CHECK: If company OR title is empty, make key unique by adding job index
        if not company or not title:
            # Use job_id or row index to make empty jobs unique
            unique_id = str(row.get('id.job', row.name if hasattr(row, 'name') else 'unknown'))
            company = company or f'empty_company_{unique_id}'
            title = title or f'empty_title_{unique_id}'
        
        # Debug first few rows to verify field availability
        if hasattr(generate_dedup_keys, 'debug_count'):
            generate_dedup_keys.debug_count += 1
        else:
            generate_dedup_keys.debug_count = 1
            
        if generate_dedup_keys.debug_count <= 3:
            print(f"🔍 DEDUP KEY #{generate_dedup_keys.debug_count}: company='{company}' title='{title}' market='{market}'")
            available_fields = [col for col in row.index if 'company' in col.lower() or 'title' in col.lower() or 'market' in col.lower()]
            print(f"   Available fields: {available_fields}")
        
        # Round 1: Company + Title + Market (market is vital ingredient!)
        r1_key = f"{company}|{title}|{market.lower()}"
        
        # Round 2: Company + Location (city-based deduplication - less aggressive)
        r2_key = f"{company}|{location}"
        
        return {
            'rules.duplicate_r1': hashlib.md5(r1_key.encode()).hexdigest()[:16],
            'rules.duplicate_r2': hashlib.md5(r2_key.encode()).hexdigest()[:16]
        }
    
    # Debug: Check what data we have in source AND norm fields
    if len(df) > 0:
        sample_row = df.iloc[0]
        print(f"🔍 Source Fields Debug:")
        print(f"    source.title: '{sample_row.get('source.title', 'MISSING')}' (len={len(str(sample_row.get('source.title', '')))})")
        print(f"    source.company: '{sample_row.get('source.company', 'MISSING')}' (len={len(str(sample_row.get('source.company', '')))})")
        print(f"    source.description_raw: '{str(sample_row.get('source.description_raw', 'MISSING'))[:50]}...' (len={len(str(sample_row.get('source.description_raw', '')))})")
        print(f"🔍 Norm Fields Debug:")
        print(f"    norm.title: '{sample_row.get('norm.title', 'MISSING')}' (len={len(str(sample_row.get('norm.title', '')))})")
        print(f"    norm.company: '{sample_row.get('norm.company', 'MISSING')}' (len={len(str(sample_row.get('norm.company', '')))})")
        print(f"    norm.description: '{str(sample_row.get('norm.description', 'MISSING'))[:50]}...' (len={len(str(sample_row.get('norm.description', '')))})")
    
    # Apply business rules ONLY to fresh jobs (don't overwrite memory job rules)
    rules_fields = {}
    
    # Owner-operator detection (only for fresh jobs)
    def apply_owner_op_rule(row):
        if not filter_settings.get('owner_op', True):
            # Filter disabled, don't mark as owner-op
            return False
        if row.get('sys.is_fresh_job', True) == False:
            # Keep existing value for memory jobs
            return row.get('rules.is_owner_op', False)
        else:
            # Apply new detection for fresh jobs
            return detect_owner_operator(row['norm.description'], row['norm.title'])
    
    rules_fields['rules.is_owner_op'] = df.apply(apply_owner_op_rule, axis=1)
    
    # School bus detection (only for fresh jobs)
    def apply_school_bus_rule(row):
        if not filter_settings.get('school_bus', True):
            # Filter disabled, don't mark as school bus
            return False
        if row.get('sys.is_fresh_job', True) == False:
            return row.get('rules.is_school_bus', False)
        else:
            return detect_school_bus(row['norm.description'], row['norm.title'])
    
    rules_fields['rules.is_school_bus'] = df.apply(apply_school_bus_rule, axis=1)
    
    # Experience requirements - REMOVED (LLM handles this in AI classification)
    rules_fields['rules.has_experience_req'] = False  # Always False, not used
    rules_fields['rules.experience_years_min'] = 0.0  # Always 0, not used
    
    # Spam detection (only for fresh jobs)
    def apply_spam_rule(row):
        if not filter_settings.get('spam_filter', True):
            # Filter disabled, don't mark as spam
            return False
        if row.get('sys.is_fresh_job', True) == False:
            return row.get('rules.is_spam_source', False)
        else:
            return detect_spam_source(row['norm.company'], row['norm.description'])
    
    rules_fields['rules.is_spam_source'] = df.apply(apply_spam_rule, axis=1)
    
    # Deduplication keys (requires market to be set)
    market = df['meta.market'].iloc[0] if len(df) > 0 and 'meta.market' in df.columns else 'Unknown'
    print(f"🔍 DEDUP DEBUG: Using market='{market}' for deduplication key generation")
    dedup_data = df.apply(lambda row: generate_dedup_keys(row, market), axis=1)
    rules_fields['rules.duplicate_r1'] = dedup_data.apply(lambda x: x['rules.duplicate_r1'])
    rules_fields['rules.duplicate_r2'] = dedup_data.apply(lambda x: x['rules.duplicate_r2'])
    
    # Mark jobs as ready for AI classification if they pass ALL filters
    # ONLY fresh jobs that aren't spam/owner-op/school-bus need classification
    # Memory jobs already classified, duplicates filtered in next stage
    rules_fields['route.ready_for_ai'] = (
        (df['sys.is_fresh_job'] == True) &  # Memory jobs = False, so excluded
        (~rules_fields['rules.is_spam_source']) &
        (~rules_fields['rules.is_owner_op']) &
        (~rules_fields['rules.is_school_bus'])
        # Deduplication stage will set duplicates to route.ready_for_ai = False
    )
    
    # Update stage and timestamp
    rules_fields['route.stage'] = 'business_rules_applied'
    rules_fields['sys.updated_at'] = datetime.now().isoformat()
    
    return df.assign(**rules_fields)

# ==============================================================================
# STAGE 4: AI CLASSIFICATION TRANSFORM
# ==============================================================================

def transform_ai_classification(df: pd.DataFrame, ai_results: Dict[str, Dict], job_ids_classified: set = None) -> pd.DataFrame:
    """
    Apply AI classification results - fills ai.* fields only
    
    Args:
        df: DataFrame with jobs ready for classification
        ai_results: Dictionary mapping job_id to AI classification results
        
    Returns:
        DataFrame with ai.* fields populated
    """
    def apply_ai_result(job_id: str) -> Dict[str, Any]:
        """Apply AI result for a specific job"""
        # Only apply AI classification to jobs that were actually sent for classification
        if job_ids_classified is not None and job_id not in job_ids_classified:
            # This job was not sent for AI classification - leave ai fields empty/None
            return {
                'ai.match': None,
                'ai.reason': None,
                'ai.summary': None,
                'ai.normalized_location': None,
                'ai.fair_chance': None,
                'ai.endorsements': None,
                'ai.route_type': None
            }
        
        if job_id not in ai_results:
            return {
                'ai.match': 'error',
                'ai.reason': 'Missing from AI response',
                'ai.summary': 'Job not classified by AI',
                'ai.normalized_location': '',
                'ai.fair_chance': 'no_requirements_mentioned',
                'ai.endorsements': 'none_required',
                'ai.route_type': 'Unknown'
            }
        
        result = ai_results[job_id]
        return {
            'ai.match': result.get('match', 'error'),
            'ai.reason': result.get('reason', 'No reason provided'),
            'ai.summary': result.get('summary', 'No summary provided'),
            'ai.normalized_location': result.get('normalized_location', ''),
            'ai.fair_chance': result.get('fair_chance', 'no_requirements_mentioned'),
            'ai.endorsements': result.get('endorsements', 'none_required'),
            'ai.route_type': result.get('route_type', 'Unknown')
        }
    
    # Apply AI results
    ai_fields = {}
    classification_data = df['id.job'].apply(apply_ai_result)
    
    for field in ['ai.match', 'ai.reason', 'ai.summary', 'ai.normalized_location', 'ai.fair_chance', 'ai.endorsements', 'ai.route_type']:
        ai_fields[field] = classification_data.apply(lambda x: x[field])
    
    # Set classification metadata
    current_date = datetime.now().date().isoformat()  # Just YYYY-MM-DD format
    current_time = datetime.now().isoformat()
    ai_fields['route.stage'] = 'classified'
    ai_fields['sys.classified_at'] = current_date  # Date only for schema validation
    ai_fields['sys.updated_at'] = current_time
    ai_fields['sys.classification_source'] = 'ai_classification'
    ai_fields['sys.model'] = 'gpt-4o-mini'
    
    return df.assign(**ai_fields)

# ==============================================================================
# STAGE 5: ROUTING AND STATUS TRANSFORMS
# ==============================================================================

def transform_routing(df: pd.DataFrame, route_filter: str = 'both') -> pd.DataFrame:
    """
    Apply routing rules and set final status - fills route.* fields
    
    Args:
        df: DataFrame with classification complete
        route_filter: 'both', 'local', or 'otr'
        
    Returns:
        DataFrame with routing decisions applied
    """
    
    # Handle empty DataFrame
    if len(df) == 0:
        return df
        
    def determine_final_status(row: pd.Series) -> str:
        """Determine why a job was included or excluded"""
        
        # Check for processing errors
        if row.get('ai.match') == 'error':
            return f"processing_error: {row.get('ai.reason', 'Unknown error')}"
        
        # Check business rule filters
        if row.get('rules.is_owner_op', False):
            return 'filtered: Owner-operator job'
        
        if row.get('rules.is_school_bus', False):
            return 'filtered: School bus driver job'
        
        if row.get('rules.is_spam_source', False):
            return 'filtered: Spam source'
        
        # Check AI classification
        if row.get('ai.match') == 'bad':
            reason = row.get('ai.reason', 'Bad match')
            return f"AI classified as bad: {reason}"
        
        # Check route filter
        if route_filter != 'both':
            job_route = row.get('ai.route_type', '').lower()
            if route_filter == 'local' and job_route != 'local':
                return f'filtered: Route type {job_route} (local only requested)'
            elif route_filter == 'otr' and job_route not in ['otr', 'regional']:
                return f'filtered: Route type {job_route} (OTR only requested)'
        
        # Check for valid application URLs (QC filter)
        source_url = str(row.get('source.url', ''))
        has_valid_url = source_url and len(source_url) > 10
        if not has_valid_url:
            return 'filtered: No valid application URL'
        
        # If we get here, job passes all filters - now check AI classification to determine final status
        ai_match = row.get('ai.match', '').lower()
        if ai_match in ['good', 'so-so']:
            return f'included: {ai_match} match'
        elif ai_match == 'bad':
            # This should have been caught above, but handle it here as fallback
            return f"AI classified as bad: {row.get('ai.reason', 'Bad match')}"
        else:
            # No AI classification yet or unknown status - keep as passed filters
            return 'passed_all_filters'
    
    # Apply routing logic
    routing_fields = {}
    
    # Determine final status for each job
    routing_fields['route.final_status'] = df.apply(determine_final_status, axis=1)
    
    # Set boolean flags
    routing_fields['route.filtered'] = (
        routing_fields['route.final_status'].str.startswith('filtered:') | 
        routing_fields['route.final_status'].str.startswith('AI classified as bad') |
        routing_fields['route.final_status'].str.startswith('processing_error:')
    )
    
    # Ready for export: ALL jobs that have been fully processed and classified
    # Quality filtering happens at export time, not routing time
    routing_fields['route.ready_for_export'] = (
        # Jobs with 'included' status (good/so-so matches)
        routing_fields['route.final_status'].str.startswith('included:') |
        # OR jobs that passed all filters but no AI classification yet
        (routing_fields['route.final_status'] == 'passed_all_filters') |
        # OR jobs classified as bad but still fully processed (for complete DataFrame)
        (routing_fields['route.final_status'].str.startswith('AI classified as bad'))
    )
    
    # Update stage and timestamp
    routing_fields['route.stage'] = 'routed'
    routing_fields['sys.updated_at'] = datetime.now().isoformat()
    
    return df.assign(**routing_fields)

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def apply_market_assignment(df: pd.DataFrame, market: str, is_custom_location: bool = False) -> pd.DataFrame:
    """Apply market assignment to all jobs.

    Policy:
    - For standard markets, meta.market must be the plain market name (no ", ST").
    - For custom locations, clone the exact custom location string into meta.market
      so deduplication still works.
    """
    
    # VALIDATION: Non-custom locations should NOT have ", ST" format
    if not is_custom_location and isinstance(market, str) and ',' in market:
        raise ValueError(f"❌ NON-CUSTOM LOCATION ERROR: Received '{market}' with ', ST' format. "
                        f"Standard markets should be in Airtable format (e.g., 'Dallas', 'Phoenix'). "
                        f"Only custom locations should have ', ST' format. "
                        f"Check upstream code - something is passing location format instead of market format.")
    
    # Enforce market formatting
    market_value = market if is_custom_location else market.split(',')[0] if isinstance(market, str) else market

    return df.assign(**{
        'meta.market': market_value,
        'sys.updated_at': datetime.now().isoformat()
    })

def apply_tracked_urls(df: pd.DataFrame, url_mapping: Dict[str, str]) -> pd.DataFrame:
    """Apply tracked URL mapping"""
    tracked_urls = df['id.job'].map(url_mapping).fillna('')
    return df.assign(**{
        'meta.tracked_url': tracked_urls,
        'sys.updated_at': datetime.now().isoformat()
    })

def merge_dataframes(fresh_df: pd.DataFrame, memory_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge fresh and memory DataFrames.
    - Keep fresh rows as the base record for each job_id
    - Reuse memory fields (AI, metadata) to fill gaps on fresh rows
    - Preserve "freshness" for source fields while leveraging prior classification
    
    Args:
        fresh_df: Fresh scraped data (preferred for source.*)
        memory_df: Data from memory database (preferred for ai.* when available)
    
    Returns:
        DataFrame with fresh rows enriched by memory where applicable
    """
    if len(fresh_df) == 0:
        return memory_df
    if len(memory_df) == 0:
        return fresh_df

    # Index by job_id for quick lookups
    fresh = fresh_df.copy()
    mem = memory_df.copy()
    if 'id.job' not in fresh.columns:
        return fresh_df
    if 'id.job' not in mem.columns:
        return fresh_df

    fresh.set_index('id.job', inplace=True, drop=False)
    mem.set_index('id.job', inplace=True, drop=False)

    # Determine overlapping job_ids
    overlap_ids = fresh.index.intersection(mem.index)

    # Columns to pull from memory when missing on fresh
    prefer_memory_cols = [
        # AI outputs
        'ai.match', 'ai.reason', 'ai.summary', 'ai.fair_chance', 'ai.endorsements', 'ai.route_type',
        # Routing/meta helpful fields
        'meta.tracked_url', 'sys.classified_at', 'sys.classification_source'
    ]

    # Helper to decide if a value is "missing" on fresh
    def _is_missing(series):
        return series.isna() | (series.astype(str) == '')

    reused_ai_count = 0  # total field-level fills
    reused_ids = set()   # unique job_ids with any AI field reused
    for col in prefer_memory_cols:
        if col in fresh.columns and col in mem.columns:
            # Build a map of memory values per job_id (first occurrence)
            mem_vals_map = mem[col].groupby(level=0).first()
            # Candidate values for each fresh row based on its job_id (index)
            candidate_vals = fresh.index.map(lambda jid: mem_vals_map.get(jid))
            candidate_vals = pd.Series(candidate_vals, index=fresh.index)
            # Determine which fresh rows are missing and have a memory value
            missing_mask = _is_missing(fresh[col])
            have_mem_mask = ~_is_missing(candidate_vals)
            fill_mask = missing_mask & have_mem_mask
            if fill_mask.any():
                fresh.loc[fill_mask, col] = candidate_vals.loc[fill_mask]
                if col.startswith('ai.'):
                    reused_ai_count += int(fill_mask.sum())
                    reused_ids.update(fresh.loc[fill_mask, 'id.job'].tolist())

    # If we reused any AI fields, mark classification source accordingly where not set
    if 'sys.classification_source' in fresh.columns and len(overlap_ids) > 0:
        cls_src_missing = _is_missing(fresh.loc[overlap_ids, 'sys.classification_source'])
        if cls_src_missing.any():
            fresh.loc[overlap_ids[cls_src_missing], 'sys.classification_source'] = 'supabase_memory'

    # If AI fields were reused, stamp classified_at/updated_at to now so memory recognizes recency
    if len(reused_ids) > 0:
        now_iso = datetime.now().isoformat()
        if 'sys.classified_at' in fresh.columns:
            fresh.loc[list(reused_ids), 'sys.classified_at'] = now_iso
        if 'sys.updated_at' in fresh.columns:
            fresh.loc[list(reused_ids), 'sys.updated_at'] = now_iso

    # Combine with memory-only rows (jobs present only in memory_df)
    memory_only_ids = mem.index.difference(fresh.index)
    if len(memory_only_ids) > 0:
        combined = pd.concat([fresh, mem.loc[memory_only_ids]], ignore_index=True)
    else:
        combined = fresh

    # Sort by updated_at for stability
    combined = combined.sort_values('sys.updated_at').reset_index(drop=True)

    # Debug: clearer reuse stats
    if reused_ai_count > 0:
        print(f"🔁 Reused AI fields from memory: {reused_ai_count} fields across {len(reused_ids)} jobs")

    return combined

def create_view(df: pd.DataFrame, filter_condition: str) -> pd.DataFrame:
    """Create a filtered view of the canonical DataFrame"""
    return df.query(filter_condition) if filter_condition else df

# Views for common filters
def view_ready_for_ai(df: pd.DataFrame) -> pd.DataFrame:
    """Jobs ready for AI classification"""
    if len(df) == 0:
        return df
    
    # Use boolean indexing instead of query for dot-notation columns
    ready_mask = (
        (df.get('route.ready_for_ai', False) == True) &
        (df['ai.match'].isna() | (df['ai.match'] == ''))
    )
    return df[ready_mask]

def view_exportable(df: pd.DataFrame) -> pd.DataFrame:
    """Jobs ready for PDF/CSV export"""
    if len(df) == 0:
        return df
        
    return df[df.get('route.ready_for_export', False) == True]

def view_fresh_quality(df: pd.DataFrame) -> pd.DataFrame:
    """Fresh jobs that passed all filters (included jobs) - for Supabase upload"""
    if len(df) == 0:
        return df
        
    # Include jobs that either passed all filters OR have any "included" status
    fresh_mask = (
        (df.get('sys.is_fresh_job', False) == True) &
        ((df.get('route.final_status', '') == 'passed_all_filters') |
         (df.get('route.final_status', '').str.startswith('included')))
    )
    return df[fresh_mask]

# Field standardization functions REMOVED - Each output format now handles 
# its own canonical field mapping at the output layer for easier debugging

if __name__ == "__main__":
    # Test transform functions
    print("🔧 Canonical Transforms Test")
    print("=" * 40)
    
    # Test with empty data
    from jobs_schema import build_empty_df
    
    test_df = build_empty_df()
    print(f"✅ Empty DataFrame: {len(test_df.columns)} columns")
    
    # Test normalization
    test_df = transform_normalize(test_df)
    print(f"✅ Normalization transform completed")
    
    # Test business rules
    test_df = transform_business_rules(test_df)
    print(f"✅ Business rules transform completed")
    
    print("\n🎉 Transform functions ready!")
