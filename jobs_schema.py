"""
Jobs Schema Definition for FreeWorld Job Scraper
Single canonical table with namespaced columns and strict validation
"""

import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, Check
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib

# ==============================================================================
# COLUMN REGISTRY - Complete field definitions with namespaces
# ==============================================================================

COLUMN_REGISTRY = {
    # === IDENTITY (stable keys) ===
    'id.job': str,                    # MD5 hash - primary key
    'id.source': str,                 # outscraper|memory|indeed|google
    'id.source_row': str,             # Original row identifier
    
    # === SOURCE (raw data - immutable once set) ===
    'source.title': str,              # Raw job title from API
    'source.company': str,            # Raw company from API
    'source.location_raw': str,       # Raw location string
    'source.description_raw': str,    # Full HTML/text description
    'source.url': str,                # Single unified URL (from any source)
    'source.salary_raw': str,         # Raw salary text
    'source.posted_date': str,        # Raw posting date
    
    # === NORMALIZED (cleaned once - deterministic) ===
    'norm.title': str,                # Cleaned job title
    'norm.company': str,              # Cleaned company name
    'norm.city': str,                 # Extracted city
    'norm.state': str,                # Extracted state
    'norm.location': str,             # Standardized "City, State"
    'norm.description': str,          # Cleaned description (HTML stripped)
    'norm.salary_display': str,       # Human readable salary
    'norm.salary_min': float,         # Parsed minimum salary
    'norm.salary_max': float,         # Parsed maximum salary
    'norm.salary_unit': str,          # hour|week|year
    'norm.salary_currency': str,      # USD|CAD etc
    
    # === RULES (deterministic business logic) ===
    'rules.is_owner_op': bool,        # Owner-operator job detection
    'rules.is_school_bus': bool,      # School bus driver detection
    'rules.has_experience_req': bool, # Experience requirement detection
    'rules.experience_years_min': float, # Minimum years required
    'rules.is_spam_source': bool,     # Spam source detection
    'rules.duplicate_r1': str,        # Round 1 dedup key (company+title+market)
    'rules.duplicate_r2': str,        # Round 2 dedup key (company+location)
    'rules.collapse_group': str,      # Final dedup group assignment
    
    # === AI OUTPUTS (from classification APIs) ===
    'ai.match': str,                  # good|so-so|bad|error
    'ai.reason': str,                 # AI classification reasoning
    'ai.summary': str,                # 4-6 sentence AI summary
    'ai.normalized_location': str,    # Translated/normalized location
    'ai.fair_chance': str,            # Background check analysis
    'ai.endorsements': str,           # CDL endorsement requirements
    'ai.route_type': str,             # Local|OTR|Regional
    'ai.raw_response': str,           # Full API response (optional)
    
    # === ROUTING (pipeline state management) ===
    'route.stage': str,               # Current pipeline stage
    'route.final_status': str,        # Why included/excluded
    'route.filtered': bool,           # Is this job filtered out?
    'route.ready_for_ai': bool,       # Ready for AI classification?
    'route.ready_for_export': bool,   # Ready for PDF/CSV export?
    'route.error': str,               # Error message if processing failed
    'route.batch_id': str,            # Batch identifier for parallel processing
    
    # === METADATA (search and organization) ===
    'meta.market': str,               # Target market (Houston, Dallas, etc.)
    'meta.query': str,                # Search query used
    'meta.search_terms': str,         # Expanded search terms
    'meta.tracked_url': str,          # Shortened URL for analytics
    'meta.airtable_id': str,          # Airtable record ID if uploaded
    
    # === SEARCH PARAMETERS (complete search context) ===
    'search.location': str,           # Search location (Houston, TX)
    'search.custom_location': str,    # Custom location if provided
    'search.route_filter': str,       # local|otr|both
    'search.mode': str,               # test|sample|medium|large|full
    'search.job_limit': int,          # Target number of jobs (25, 100, 500, etc.)
    'search.radius': int,             # Search radius in miles
    'search.exact_location': bool,    # Use exact location (radius=0)
    'search.no_experience': bool,     # Include no experience jobs
    'search.force_fresh': bool,       # Force fresh classification
    'search.memory_only': bool,       # Memory-only search
    'search.business_rules': bool,    # Apply business rules
    'search.deduplication': bool,     # Apply deduplication
    'search.experience_filter': bool, # Apply experience filtering
    'search.model': str,              # AI model used (gpt-4o-mini)
    'search.batch_size': int,         # Classification batch size
    'search.sources': str,            # outscraper|google|indeed (comma-separated)
    'search.strategy': str,           # balanced|aggressive|conservative
    'search.coach_username': str,     # Coach who initiated search
    
    # === FREE AGENT (Airtable imported data for personalization) ===
    'agent.uuid': str,                # Free Agent UUID from Airtable
    'agent.name': str,                # Free Agent First + Last Name
    'agent.first_name': str,          # Free Agent First Name only
    'agent.last_name': str,           # Free Agent Last Name only
    'agent.email': str,               # Free Agent contact email
    'agent.phone': str,               # Free Agent phone number
    'agent.city': str,                # Free Agent city
    'agent.state': str,               # Free Agent state
    'agent.coach_name': str,          # Success Coach First Name
    'agent.coach_username': str,      # Full Coach Username
    'agent.preferred_route': str,     # Local|OTR|Regional preference
    'agent.experience_years': float,  # Years of CDL experience
    'agent.endorsements_held': str,   # Current CDL endorsements
    'agent.notes': str,               # Coach notes about Free Agent
    'agent.last_contact': str,        # Last contact date
    'agent.status': str,              # Active|Inactive|Placed status
    
    # === QUALITY ASSURANCE ===
    'qa.missing_required_fields': bool, # Has missing required data?
    'qa.flags': str,                  # JSON list of validation flags
    'qa.last_validated_at': str,      # Last validation timestamp
    'qa.data_quality_score': float,   # Overall data quality (0-1)
    
    # === SYSTEM (audit trail and provenance) ===
    'sys.created_at': str,            # When record was first created
    'sys.updated_at': str,            # Last modification time
    'sys.classified_at': str,         # When AI classification occurred
    'sys.run_id': str,                # Pipeline run identifier
    'sys.version': str,               # Schema version
    'sys.classification_source': str, # ai_classification|memory|airtable
    'sys.is_fresh_job': bool,         # True if scraped this run
    'sys.model': str,                 # AI model used (gpt-4o-mini)
    'sys.prompt_sha': str,            # Hash of prompt for cache validation
    'sys.schema_sha': str,            # Hash of schema for compatibility
    'sys.coach': str,                 # Success Coach who ordered this search
}

# ==============================================================================
# ENUM DEFINITIONS - Valid values for categorical fields
# ==============================================================================

ENUMS = {
    'id.source': ['memory', 'indeed', 'google'],
    'ai.match': ['good', 'so-so', 'bad', 'error'],
    'ai.fair_chance': ['fair_chance_employer', 'background_check_required', 
                      'clean_record_required', 'no_requirements_mentioned'],
    'ai.endorsements': ['none_required', 'hazmat', 'passenger', 'school_bus', 
                       'tanker', 'double_triple', 'x - hazmat/tanker combo', 'multiple'],
    'ai.route_type': ['Local', 'OTR', 'Regional', 'Unknown'],
    'route.stage': ['ingested', 'normalized', 'business_rules_applied', 'deduped', 'classified', 'routed', 'exported'],
    'norm.salary_unit': ['hour', 'week', 'month', 'year'],
    'norm.salary_currency': ['USD', 'CAD'],
    'sys.classification_source': ['ai_classification', 'supabase_memory', 'airtable_memory']
}

# ==============================================================================
# SUPABASE FIELD MAPPING - Only paid data and PDF requirements
# ==============================================================================

SUPABASE_FIELDS = {
    # Core identity
    'job_id': 'id.job',
    
    # Outscraper paid data ($0.001/job)
    'job_title': 'source.title',
    'company': 'source.company', 
    'location': 'source.location_raw',
    'job_description': 'source.description_raw',
    'apply_url': 'source.url',              # Single unified URL field
    'salary': 'source.salary_raw',
    
    # OpenAI paid data ($0.0003/job)
    'match_level': 'ai.match',
    'match_reason': 'ai.reason',
    'summary': 'ai.summary',
    'normalized_location': 'ai.normalized_location',
    'fair_chance': 'ai.fair_chance',
    'endorsements': 'ai.endorsements',
    'route_type': 'ai.route_type',
    
    # PDF and organization requirements
    'market': 'meta.market',
    'tracked_url': 'meta.tracked_url',
    'success_coach': 'sys.coach',
    
    # Recall context fields (added for complete data banking)
    'search_query': 'meta.query',           # Search terms used
    'source': 'id.source',                  # Data provenance
    'filter_reason': 'route.final_status',  # Why filtered out
    
    # Memory system requirements
    'classified_at': 'sys.classified_at',
    'classification_source': 'sys.classification_source',
    'created_at': 'sys.created_at',
    'updated_at': 'sys.updated_at',
    
    # Free Agent personalization (from canonical DataFrame)
    'agent_uuid': 'agent.uuid',
    'agent_name': 'agent.name',
    'agent_first_name': 'agent.first_name',
    'agent_email': 'agent.email',
    'coach_name': 'agent.coach_name',
    'coach_username': 'agent.coach_username',
    
    # Deduplication keys for database-level deduplication
    'rules_duplicate_r1': 'rules.duplicate_r1',
    'rules_duplicate_r2': 'rules.duplicate_r2',
    'clean_apply_url': 'clean_apply_url',
    'job_id_hash': 'sys.hash',
}

# ==============================================================================
# PANDERA SCHEMA - Data validation and type enforcement
# ==============================================================================

def create_validation_schema():
    """Create Pandera schema for DataFrame validation"""
    
    schema_dict = {}
    
    # Add all columns with appropriate validations
    for col, dtype in COLUMN_REGISTRY.items():
        checks = []
        nullable = True  # Most fields can be null during processing
        
        # Special validations for specific fields
        if col in ENUMS:
            checks.append(Check.isin(ENUMS[col] + [None, '']))
            
        if col == 'id.job':
            checks.append(Check.str_matches(r'^[a-f0-9]{32}$'))  # MD5 format
            nullable = False
            
        if col.endswith('_at'):
            # Datetime-like fields: allow empty/None OR ISO date/time strings that start with YYYY-MM-DD
            # Use vectorized check to handle nulls and empty strings gracefully
            checks.append(
                Check(
                    lambda s: s.isna() | (s.astype(str).str.len() == 0) | s.astype(str).str.match(r'^\d{4}-\d{2}-\d{2}'),
                    element_wise=False
                )
            )
            
        if col.startswith('qa.') and col.endswith('_score'):
            checks.append(Check.in_range(0, 1))
            
        schema_dict[col] = Column(dtype, checks=checks, nullable=nullable)
    
    return pa.DataFrameSchema(schema_dict, coerce=True, strict=False)

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def build_empty_df() -> pd.DataFrame:
    """Create empty DataFrame with correct schema"""
    df = pd.DataFrame(columns=list(COLUMN_REGISTRY.keys()))
    
    # Set correct dtypes
    for col, dtype in COLUMN_REGISTRY.items():
        if dtype == bool:
            df[col] = df[col].astype('boolean')  # Nullable boolean
        elif dtype == float:
            df[col] = df[col].astype('float64')
        elif dtype == int:
            df[col] = df[col].astype('Int64')    # Nullable int
        else:
            df[col] = df[col].astype('string')   # Nullable string
    
    return df

def ensure_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure DataFrame has all required columns with correct types"""
    
    # Add missing columns with defaults
    for col, dtype in COLUMN_REGISTRY.items():
        if col not in df.columns:
            if dtype == bool:
                df[col] = False
            elif dtype in [int, float]:
                df[col] = None
            else:
                df[col] = ''
    
    # Ensure column order matches registry
    df = df.reindex(columns=list(COLUMN_REGISTRY.keys()), fill_value=None)
    
    # Apply correct dtypes
    for col, dtype in COLUMN_REGISTRY.items():
        try:
            if dtype == bool:
                df[col] = df[col].astype('boolean')
            elif dtype == float:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('float64')
            elif dtype == int:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            else:
                df[col] = df[col].astype('string')
        except Exception as e:
            print(f"⚠️ Type conversion failed for {col}: {e}")
    
    return df

def generate_job_id(company: str, location: str, title: str) -> str:
    """Generate consistent MD5 job ID"""
    content = f"{company.lower().strip()}|{location.lower().strip()}|{title.lower().strip()}"
    return hashlib.md5(content.encode()).hexdigest()

def validate_dataframe(df: pd.DataFrame, raise_errors: bool = False) -> Dict[str, Any]:
    """Validate DataFrame against schema"""
    
    try:
        schema = create_validation_schema()
        schema.validate(df, lazy=True)
        
        return {
            'valid': True,
            'errors': [],
            'warnings': [],
            'row_count': len(df)
        }
        
    except pa.errors.SchemaErrors as e:
        errors = []
        warnings = []
        
        for error in e.failure_cases.itertuples():
            if 'nullable' in str(error.check):
                warnings.append(f"Row {error.index}: {error.column} has null values")
            else:
                errors.append(f"Row {error.index}: {error.column} - {error.check}")
        
        if raise_errors and errors:
            raise e
            
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'row_count': len(df)
        }

def prepare_for_supabase(df: pd.DataFrame) -> pd.DataFrame:
    """Convert canonical DataFrame to Supabase format"""
    
    # Select only fields that go to Supabase
    supabase_df = pd.DataFrame()
    
    for supabase_col, canonical_col in SUPABASE_FIELDS.items():
        if canonical_col in df.columns:
            supabase_df[supabase_col] = df[canonical_col]
    
    # URL field is now directly mapped from source.url - no special handling needed
    
    # Clean for Supabase storage
    for col in supabase_df.columns:
        # Handle null values
        supabase_df[col] = supabase_df[col].fillna('')
        
        # Truncate long text fields
        if col == 'job_description':
            supabase_df[col] = supabase_df[col].astype(str).str[:5000]
        elif col in ['match_reason', 'summary']:
            supabase_df[col] = supabase_df[col].astype(str).str[:1000]
    
    return supabase_df


def sanctify_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize canonical DF for export: types, ids, enums, flags, and URLs."""
    import os
    if df is None or len(df) == 0:
        return df

    df = ensure_schema(df)

    # Normalize string columns
    for col in df.columns:
        try:
            if pd.api.types.is_string_dtype(df[col]):
                s = df[col].astype('string').fillna('').str.replace('\u00a0', ' ', regex=False).str.strip()
                s = s.replace({'None': '', 'null': '', 'NULL': '', 'NaN': '', 'nan': ''})
                df[col] = s
        except Exception:
            pass

    # Fill id.job if missing using normalized or source fields
    try:
        miss = df['id.job'].isna() | (df['id.job'].astype(str) == '')
        if miss.any():
            title = df.get('norm.title', df.get('source.title', pd.Series([''] * len(df)))).astype(str)
            company = df.get('norm.company', df.get('source.company', pd.Series([''] * len(df)))).astype(str)
            location = df.get('norm.location', df.get('source.location_raw', pd.Series([''] * len(df)))).astype(str)
            gen = [generate_job_id(company.iloc[i] if i < len(company) else '',
                                   location.iloc[i] if i < len(location) else '',
                                   title.iloc[i] if i < len(title) else '')
                   for i in range(len(df))]
            df.loc[miss, 'id.job'] = pd.Series(gen, index=df.index)[miss]
    except Exception:
        pass

    # Normalize enums
    try:
        if 'ai.match' in df.columns:
            allowed = set(ENUMS['ai.match'])
            s = df['ai.match'].astype('string')
            df['ai.match'] = s.where(s.isin(allowed), other='error')
    except Exception:
        pass
    try:
        if 'ai.route_type' in df.columns:
            allowed = set(ENUMS['ai.route_type'])
            s = df['ai.route_type'].astype('string')
            df['ai.route_type'] = s.where(s.isin(allowed), other='Unknown')
    except Exception:
        pass

    # Route flags and stage
    try:
        if 'ai.match' in df.columns:
            quality = df['ai.match'].isin(['good', 'so-so'])
            if 'route.ready_for_export' in df.columns:
                df['route.ready_for_export'] = df['route.ready_for_export'].fillna(False)
                df.loc[quality, 'route.ready_for_export'] = True
            if 'route.final_status' in df.columns:
                fs = df['route.final_status'].astype('string')
                empty = fs.isna() | (fs == '')
                df.loc[quality & empty, 'route.final_status'] = 'included: quality'
            if 'route.stage' in df.columns:
                stg = df['route.stage'].astype('string')
                empty = stg.isna() | (stg == '')
                df.loc[quality & empty, 'route.stage'] = 'exported'
    except Exception:
        pass

    # Tracked URL fallback
    try:
        if 'meta.tracked_url' in df.columns:
            empty = df['meta.tracked_url'].isna() | (df['meta.tracked_url'] == '')
            indeed = df.get('source.indeed_url', pd.Series([''] * len(df))).fillna('')
            google = df.get('source.google_url', pd.Series([''] * len(df))).fillna('')
            apply = df.get('source.apply_url', pd.Series([''] * len(df))).fillna('')
            chain = indeed
            chain = chain.mask(chain == '', google)
            chain = chain.mask(chain == '', apply)
            df.loc[empty, 'meta.tracked_url'] = chain[empty]
    except Exception:
        pass

    # System metadata
    try:
        if 'sys.version' in df.columns:
            sv = df['sys.version'].astype('string')
            df.loc[sv.isna() | (sv == ''), 'sys.version'] = SCHEMA_VERSION
    except Exception:
        pass
    try:
        if 'sys.schema_sha' in df.columns:
            sh = df['sys.schema_sha'].astype('string')
            df.loc[sh.isna() | (sh == ''), 'sys.schema_sha'] = SCHEMA_HASH
    except Exception:
        pass
    try:
        coach_env = os.getenv('FREEWORLD_COACH_USERNAME', '')
        if coach_env and 'sys.coach' in df.columns:
            sc = df['sys.coach'].astype('string')
            df.loc[sc.isna() | (sc == ''), 'sys.coach'] = coach_env
    except Exception:
        pass

    return df

# ==============================================================================
# FIELD POLICY DEFINITIONS
# ==============================================================================

FIELD_POLICIES = {
    # Immutable fields - can only be set once
    'immutable': [col for col in COLUMN_REGISTRY.keys() if col.startswith('source.')],
    
    # Append-only fields - can be updated but not overwritten if non-empty
    'append_only': [col for col in COLUMN_REGISTRY.keys() if col.startswith('ai.')],
    
    # System fields - updated automatically
    'system_managed': [col for col in COLUMN_REGISTRY.keys() if col.startswith('sys.')],
    
    # Fillable fields - can be updated freely
    'fillable': [col for col in COLUMN_REGISTRY.keys() 
                if col.startswith(('norm.', 'rules.', 'route.', 'meta.', 'qa.'))]
}

# ==============================================================================
# SCHEMA METADATA
# ==============================================================================

SCHEMA_VERSION = "1.0.0"
SCHEMA_HASH = hashlib.md5(str(sorted(COLUMN_REGISTRY.items())).encode()).hexdigest()

def get_schema_info():
    """Get schema metadata"""
    return {
        'version': SCHEMA_VERSION,
        'hash': SCHEMA_HASH,
        'total_fields': len(COLUMN_REGISTRY),
        'namespaces': list(set(col.split('.')[0] for col in COLUMN_REGISTRY.keys())),
        'supabase_fields': len(SUPABASE_FIELDS),
        'created_at': datetime.now().isoformat()
    }


def validate_canonical_df(df: pd.DataFrame, context: str = "") -> Dict[str, Any]:
    """Validate that DataFrame conforms to canonical schema requirements.
    
    Args:
        df: DataFrame to validate
        context: Context description for logging (e.g., "Memory Only", "Fresh Scrape")
        
    Returns:
        Dict with validation results: {
            'valid': bool,
            'field_count': int,
            'missing_fields': List[str],
            'extra_fields': List[str], 
            'errors': List[str],
            'warnings': List[str]
        }
    """
    
    results = {
        'valid': True,
        'field_count': len(df.columns),
        'expected_count': len(COLUMN_REGISTRY),
        'missing_fields': [],
        'extra_fields': [],
        'errors': [],
        'warnings': []
    }
    
    prefix = f"[{context}] " if context else ""
    
    # Check field count
    expected_fields = set(COLUMN_REGISTRY.keys())
    actual_fields = set(df.columns)
    
    # Find missing and extra fields
    results['missing_fields'] = sorted(expected_fields - actual_fields)
    results['extra_fields'] = sorted(actual_fields - expected_fields)
    
    # Validate field count
    if results['field_count'] != results['expected_count']:
        results['valid'] = False
        results['errors'].append(f"Field count mismatch: expected {results['expected_count']}, got {results['field_count']}")
    
    # Check for missing critical fields
    if results['missing_fields']:
        results['valid'] = False
        results['errors'].append(f"Missing {len(results['missing_fields'])} fields: {results['missing_fields'][:5]}{'...' if len(results['missing_fields']) > 5 else ''}")
    
    # Check for extra fields (warning only)
    if results['extra_fields']:
        results['warnings'].append(f"Extra {len(results['extra_fields'])} fields: {results['extra_fields'][:5]}{'...' if len(results['extra_fields']) > 5 else ''}")
    
    # Check namespace completeness
    namespaces = {}
    for field in actual_fields:
        if '.' in field:
            namespace = field.split('.')[0]
            namespaces[namespace] = namespaces.get(namespace, 0) + 1
    
    expected_namespaces = {'id', 'source', 'norm', 'rules', 'ai', 'route', 'meta', 'search', 'agent', 'qa', 'sys'}
    missing_namespaces = expected_namespaces - set(namespaces.keys())
    
    if missing_namespaces:
        results['valid'] = False
        results['errors'].append(f"Missing namespaces: {sorted(missing_namespaces)}")
    
    # Log validation results
    if results['valid']:
        print(f"✅ {prefix}DataFrame validation PASSED: {results['field_count']} fields, all namespaces present")
    else:
        print(f"❌ {prefix}DataFrame validation FAILED:")
        for error in results['errors']:
            print(f"   • {error}")
    
    if results['warnings']:
        for warning in results['warnings']:
            print(f"⚠️ {prefix}{warning}")
    
    return results


if __name__ == "__main__":
    # Schema validation test
    print("🏗️ Jobs Schema Test")
    print("=" * 40)
    
    # Test empty DataFrame creation
    df = build_empty_df()
    print(f"✅ Empty DataFrame created with {len(df.columns)} columns")
    
    # Test schema validation
    validation_result = validate_dataframe(df)
    print(f"✅ Schema validation: {validation_result['valid']}")
    
    # Test schema info
    info = get_schema_info()
    print(f"✅ Schema v{info['version']} with {info['total_fields']} fields")
    print(f"   Namespaces: {', '.join(info['namespaces'])}")
    print(f"   Supabase fields: {info['supabase_fields']}")
    
    print("\n🎉 Schema definition complete!")
