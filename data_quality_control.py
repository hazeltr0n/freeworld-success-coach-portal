#!/usr/bin/env python3
"""
Data Quality Control for FreeWorld Job Pipeline

Validates job data before Supabase upload to ensure data integrity
and prevent bad/incomplete records from entering the database.
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class JobDataQC:
    """Quality control validator for job data before database upload"""
    
    def __init__(self):
        # Define required fields that must be present and non-empty
        self.required_fields = {
            'core_fields': {
                'id.job': 'Unique job identifier',
                'source.title': 'Job title',
                'source.company': 'Company name',
                'source.url': 'Application URL',
                'meta.market': 'Target market'
            },
            'classification_fields': {
                'ai.match': 'AI match quality (good/so-so/bad)',
                'ai.summary': 'AI job summary',
                'ai.route_type': 'Route type (Local/Regional/OTR)'
            },
            'routing_fields': {
                'route.final_status': 'Final routing decision'
            }
        }
        
        # Optional but recommended fields
        self.recommended_fields = {
            'source.description_raw': 'Job description text',
            'source.location_raw': 'Job location',
            'ai.fair_chance': 'Fair chance assessment',
            'meta.tracked_url': 'Tracking URL for analytics'
        }
        
        # Field validation rules
        self.validation_rules = {
            'ai.match': ['good', 'so-so', 'bad', 'error'],
            'ai.route_type': ['Local', 'Regional', 'OTR', 'unknown'],
            'ai.fair_chance': ['yes', 'no', 'unknown']
        }
        
        # Minimum field lengths
        self.min_lengths = {
            'source.title': 5,
            'source.company': 2,
            'ai.summary': 10,
            'source.description_raw': 20
        }
        
    def validate_job_batch(self, df: pd.DataFrame, strict_mode: bool = False) -> Tuple[pd.DataFrame, Dict]:
        """
        Validate a batch of jobs and return clean data with quality report
        
        Args:
            df: DataFrame with job data
            strict_mode: DEPRECATED - QC is now report-only and never blocks jobs
            
        Returns:
            Tuple of (original_dataframe, quality_report)
        """
        if df.empty:
            return df, {'total_jobs': 0, 'valid_jobs': 0, 'rejected_jobs': 0, 'warnings': []}
        
        print(f"🔍 QC: Starting validation of {len(df)} jobs (REPORT-ONLY mode)...")
        
        validation_results = []
        quality_report = {
            'total_jobs': len(df),
            'valid_jobs': 0,
            'rejected_jobs': 0,
            'warnings': [],
            'field_completeness': {},
            'validation_details': []
        }
        
        for idx, job in df.iterrows():
            job_validation = self._validate_single_job(job, idx)
            validation_results.append(job_validation)
            
            if job_validation['is_valid']:
                quality_report['valid_jobs'] += 1
            else:
                quality_report['rejected_jobs'] += 1
                
        # Generate field completeness report
        for field_group, fields in self.required_fields.items():
            for field, description in fields.items():
                if field in df.columns:
                    non_empty_count = df[field].notna().sum()
                    completeness = non_empty_count / len(df) * 100
                    quality_report['field_completeness'][field] = {
                        'completeness_percent': round(completeness, 1),
                        'non_empty_count': int(non_empty_count),
                        'description': description
                    }
        
        # QC IS NOW REPORT-ONLY - Always return the original DataFrame unchanged
        df_clean = df.copy()
            
        # Add validation warnings to report
        all_warnings = []
        for result in validation_results:
            all_warnings.extend(result['warnings'])
        
        # Consolidate similar warnings
        warning_counts = {}
        for warning in all_warnings:
            warning_counts[warning] = warning_counts.get(warning, 0) + 1
            
        quality_report['warnings'] = [
            f"{warning} (affects {count} jobs)" for warning, count in warning_counts.items()
        ]
        
        print(f"✅ QC: Validation complete - {quality_report['valid_jobs']}/{quality_report['total_jobs']} jobs would pass strict validation")
        if quality_report['warnings']:
            print(f"⚠️  QC: {len(quality_report['warnings'])} types of validation warnings found")
        print(f"📝 QC: REPORT-ONLY mode - All {len(df)} jobs will be uploaded regardless of validation status")
            
        return df_clean, quality_report
        
    def _validate_single_job(self, job: pd.Series, idx: int) -> Dict:
        """Validate a single job record"""
        result = {
            'job_index': idx,
            'job_id': job.get('id.job', 'unknown'),
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check required fields
        for field_group, fields in self.required_fields.items():
            for field, description in fields.items():
                if not self._is_field_valid(job, field):
                    error_msg = f"Missing or empty required field: {field} ({description})"
                    result['errors'].append(error_msg)
                    result['is_valid'] = False
                    
        # Check field value constraints
        for field, valid_values in self.validation_rules.items():
            if field in job and pd.notna(job[field]):
                if str(job[field]).lower() not in [v.lower() for v in valid_values]:
                    warning_msg = f"Invalid value for {field}: '{job[field]}' (expected: {valid_values})"
                    result['warnings'].append(warning_msg)
                    
        # Check minimum field lengths
        for field, min_length in self.min_lengths.items():
            if field in job and pd.notna(job[field]):
                field_length = len(str(job[field]).strip())
                if field_length < min_length:
                    warning_msg = f"Field {field} too short: {field_length} chars (minimum: {min_length})"
                    result['warnings'].append(warning_msg)
                    
        # Check for suspicious patterns
        if self._detect_suspicious_data(job):
            result['warnings'].append("Suspicious data pattern detected")
            
        return result
        
    def _is_field_valid(self, job: pd.Series, field: str) -> bool:
        """Check if a field has valid (non-empty) data"""
        if field not in job:
            return False
            
        value = job[field]
        if pd.isna(value):
            return False
            
        str_value = str(value).strip()
        if str_value == '' or str_value.lower() in ['none', 'null', 'nan']:
            return False
            
        return True
        
    def _detect_suspicious_data(self, job: pd.Series) -> bool:
        """Detect suspicious data patterns that might indicate bad data"""
        suspicious_patterns = []
        
        # Check for placeholder text
        text_fields = ['source.title', 'source.company', 'ai.summary', 'source.description_raw']
        placeholder_terms = ['test', 'placeholder', 'lorem ipsum', 'sample', 'example']
        
        for field in text_fields:
            if field in job and pd.notna(job[field]):
                text = str(job[field]).lower()
                for term in placeholder_terms:
                    if term in text:
                        suspicious_patterns.append(f"Placeholder text '{term}' in {field}")
                        
        # Check for obviously malformed URLs
        if 'source.url' in job and pd.notna(job['source.url']):
            url = str(job['source.url'])
            if not (url.startswith('http://') or url.startswith('https://')):
                suspicious_patterns.append("Malformed URL format")
                
        # Check for duplicate title/company combinations (might indicate scraping issues)
        title = str(job.get('source.title', '')).strip().lower()
        company = str(job.get('source.company', '')).strip().lower()
        if title and company and title == company:
            suspicious_patterns.append("Title identical to company name")
            
        return len(suspicious_patterns) > 0
        
    def generate_quality_report(self, quality_data: Dict) -> str:
        """Generate a human-readable quality report"""
        report = []
        report.append("📊 DATA QUALITY CONTROL REPORT")
        report.append("=" * 50)
        
        # Summary
        total = quality_data['total_jobs']
        valid = quality_data['valid_jobs']
        rejected = quality_data['rejected_jobs']
        
        report.append(f"Total Jobs Processed: {total}")
        report.append(f"✅ Valid Jobs: {valid} ({valid/total*100:.1f}%)")
        if rejected > 0:
            report.append(f"❌ Rejected Jobs: {rejected} ({rejected/total*100:.1f}%)")
        
        # Field completeness
        if quality_data['field_completeness']:
            report.append("\n📋 FIELD COMPLETENESS:")
            for field, stats in quality_data['field_completeness'].items():
                completeness = stats['completeness_percent']
                count = stats['non_empty_count']
                desc = stats['description']
                
                status = "✅" if completeness >= 95 else "⚠️" if completeness >= 80 else "❌"
                report.append(f"   {status} {field}: {completeness}% ({count}/{total}) - {desc}")
        
        # Warnings
        if quality_data['warnings']:
            report.append(f"\n⚠️  VALIDATION WARNINGS:")
            for warning in quality_data['warnings'][:10]:  # Limit to top 10
                report.append(f"   • {warning}")
            if len(quality_data['warnings']) > 10:
                report.append(f"   ... and {len(quality_data['warnings']) - 10} more warnings")
                
        return "\n".join(report)

# Convenience function for pipeline integration
def validate_jobs_for_upload(df: pd.DataFrame, strict_mode: bool = False) -> Tuple[pd.DataFrame, str]:
    """
    Convenience function to validate jobs before Supabase upload
    
    Args:
        df: DataFrame with job data
        strict_mode: DEPRECATED - QC is now report-only and never blocks jobs
        
    Returns:
        Tuple of (original_dataframe, quality_report_text)
    """
    qc = JobDataQC()
    validated_df, quality_data = qc.validate_job_batch(df, strict_mode=False)  # Force non-strict mode
    report_text = qc.generate_quality_report(quality_data)
    
    return validated_df, report_text