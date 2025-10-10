#!/usr/bin/env python3
"""
Analyze CDL classifier results to identify misclassification patterns.
Focus: Jobs with experience requirements being classified as "so-so" instead of "bad"
"""

import os
import sys
import pandas as pd
import re
from supabase import create_client

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    # Try loading from secrets file
    try:
        import streamlit as st
        SUPABASE_URL = st.secrets.get('SUPABASE_URL')
        SUPABASE_ANON_KEY = st.secrets.get('SUPABASE_ANON_KEY')
    except:
        print("❌ Could not load Supabase credentials")
        sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

print("📊 Querying last 200 classified jobs from Supabase...")
print("=" * 80)

# Query last 200 jobs that have been AI-classified
result = client.table('jobs').select(
    'job_id, job_title, company, job_description, match_level, match_reason, '
    'created_at, salary, location, filter_reason'
).not_.is_('match_level', 'null').order('created_at', desc=True).limit(200).execute()

jobs = result.data
print(f"✅ Retrieved {len(jobs)} classified jobs\n")

# Convert to DataFrame for analysis
df = pd.DataFrame(jobs)

# Distribution of match levels
print("📈 Match Level Distribution:")
print(df['match_level'].value_counts())
print()

# Focus on "so-so" jobs
soso_jobs = df[df['match_level'] == 'so-so'].copy()
print(f"🔍 Analyzing {len(soso_jobs)} 'so-so' jobs for experience requirements...\n")

# Experience requirement patterns to look for
experience_patterns = [
    r'(\d+)\+?\s*years?\s*(of\s*)?(experience|exp)',
    r'minimum\s*(\d+)\s*years?',
    r'at\s*least\s*(\d+)\s*years?',
    r'(\d+)\s*years?\s*(minimum|min|required)',
    r'must\s*have\s*(\d+)\s*years?',
    r'require[sd]?\s*(\d+)\s*years?',
]

def extract_experience_requirement(text):
    """Extract experience requirement from job description"""
    if not text or pd.isna(text):
        return None, None

    text_lower = text.lower()

    for pattern in experience_patterns:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            # Extract the number
            years = None
            for group in match.groups():
                if group and group.isdigit():
                    years = int(group)
                    break
            if years:
                # Return years and the matched text snippet
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                snippet = text[start:end].strip()
                return years, snippet

    return None, None

# Analyze so-so jobs for experience requirements
soso_jobs['exp_years'], soso_jobs['exp_snippet'] = zip(*soso_jobs['job_description'].apply(extract_experience_requirement))
soso_with_exp = soso_jobs[soso_jobs['exp_years'].notna()].copy()

print(f"🚨 PROBLEM IDENTIFIED: {len(soso_with_exp)} 'so-so' jobs have explicit experience requirements")
print(f"   These should be classified as 'bad' instead!\n")

if len(soso_with_exp) > 0:
    print("=" * 80)
    print("📋 TOP 10 MISCLASSIFIED JOBS (so-so with experience requirements):")
    print("=" * 80)

    for idx, (i, job) in enumerate(soso_with_exp.head(10).iterrows(), 1):
        print(f"\n{idx}. {job['job_title']} @ {job['company']}")
        print(f"   Experience Required: {job['exp_years']} years")
        print(f"   Snippet: ...{job['exp_snippet']}...")
        print(f"   AI Reason: {job['match_reason'][:200]}...")
        print(f"   Location: {job['location']}")
        print(f"   Salary: {job['salary']}")
        print()

# Also check "bad" jobs to see if classifier is working correctly for some
print("\n" + "=" * 80)
print("✅ CHECKING: Are 'bad' jobs properly catching experience requirements?")
print("=" * 80)

bad_jobs = df[df['match_level'] == 'bad'].copy()
bad_jobs['exp_years'], bad_jobs['exp_snippet'] = zip(*bad_jobs['job_description'].apply(extract_experience_requirement))
bad_with_exp = bad_jobs[bad_jobs['exp_years'].notna()].copy()

print(f"✅ {len(bad_with_exp)} 'bad' jobs have explicit experience requirements")
print(f"   Classifier correctly identified these!\n")

if len(bad_with_exp) > 0:
    print("Sample of correctly classified 'bad' jobs:")
    for idx, (i, job) in enumerate(bad_with_exp.head(3).iterrows(), 1):
        print(f"\n{idx}. {job['job_title']} @ {job['company']}")
        print(f"   Experience Required: {job['exp_years']} years")
        print(f"   AI Reason: {job['match_reason'][:200]}...")

# Summary statistics
print("\n" + "=" * 80)
print("📊 SUMMARY STATISTICS:")
print("=" * 80)
print(f"Total classified jobs analyzed: {len(df)}")
print(f"'good' jobs: {len(df[df['match_level'] == 'good'])}")
print(f"'so-so' jobs: {len(soso_jobs)}")
print(f"'bad' jobs: {len(bad_jobs)}")
print()
print(f"So-so jobs WITH experience requirements: {len(soso_with_exp)} ({len(soso_with_exp)/len(soso_jobs)*100:.1f}% of so-so)")
print(f"Bad jobs WITH experience requirements: {len(bad_with_exp)} ({len(bad_with_exp)/len(bad_jobs)*100:.1f}% of bad)")
print()

# Experience distribution
all_jobs_with_exp = pd.concat([soso_with_exp, bad_with_exp])
if len(all_jobs_with_exp) > 0:
    print("Experience years distribution (jobs with requirements):")
    print(all_jobs_with_exp['exp_years'].value_counts().sort_index())
    print()

print("=" * 80)
print("🎯 NEXT STEPS:")
print("=" * 80)
print("1. Review the AI match_reason for misclassified so-so jobs")
print("2. Identify why the classifier is not catching experience requirements")
print("3. Update job_classifier.py prompt to be more strict about experience")
print("4. Consider adding explicit regex-based business rules as a fallback")
print()

# Export detailed results for further analysis
output_file = 'cdl_classifier_analysis.csv'
soso_with_exp.to_csv(output_file, index=False)
print(f"💾 Exported {len(soso_with_exp)} misclassified jobs to: {output_file}")
