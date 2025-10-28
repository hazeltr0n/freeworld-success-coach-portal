#!/usr/bin/env python3
"""Test the delete+insert deduplication behavior"""

import os
import sys
import time
from supabase import create_client

# Get Supabase credentials
try:
    import streamlit as st
    SUPABASE_URL = st.secrets.get('SUPABASE_URL')
    SUPABASE_ANON_KEY = st.secrets.get('SUPABASE_ANON_KEY')
except:
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

print('🧪 Testing DELETE + INSERT deduplication...')
print('=' * 80)

# Test job with unique R3 hash
test_job = {
    'job_id': 'test_delete_insert_123',
    'job_title': 'Test CDL Driver V1',
    'company': 'Test Company',
    'location': 'Test City, TX',
    'zip_code': '75001',
    'job_description': 'Original description',
    'apply_url': 'https://test.com/v1',
    'salary': '50k-60k',
    'match_level': 'good',
    'match_reason': 'Test reason',
    'summary': 'Original summary',
    'fair_chance': 'yes',
    'endorsements': 'none',
    'route_type': 'Local',
    'career_pathway': 'cdl_pathway',
    'training_provided': True,
    'market': 'Dallas',
    'tracked_url': 'https://short.io/test1',
    'indeed_job_url': '',
    'search_query': 'CDL driver',
    'source': 'outscraper',
    'filter_reason': '',
    'classification_source': 'ai_classification',
    'rules_duplicate_r1': 'test_r1_unique',
    'rules_duplicate_r2': 'test_r2_unique',
    'rules_duplicate_r3': 'TestCompany|Dallas|Local|good|testcdldriverv1',
    'clean_apply_url': 'https://test.com/v1',
    'job_id_hash': 'test_hash_v1'
}

# First insert
print('📝 First insert (V1)...')
result1 = client.rpc('batch_insert_jobs_with_dedup', {'p_jobs_data': [test_job]}).execute()
print(f'   Result: {result1.data} jobs inserted')

# Get created job
job1 = client.table('jobs').select('job_id, job_title, job_description, salary, created_at').eq('job_id', 'test_delete_insert_123').execute()
if job1.data:
    print(f'   Job ID: {job1.data[0]["job_id"]}')
    print(f'   Title: {job1.data[0]["job_title"]}')
    print(f'   Description: {job1.data[0]["job_description"]}')
    print(f'   Salary: {job1.data[0]["salary"]}')
    print(f'   Created: {job1.data[0]["created_at"]}')
    old_created = job1.data[0]['created_at']

time.sleep(2)

# Second insert - UPDATED JOB (same R3 hash)
print('\n🔄 Second insert (V2 - same R3, updated content)...')
test_job['job_title'] = 'Test CDL Driver V2 - UPDATED'
test_job['job_description'] = 'NEW UPDATED description'
test_job['salary'] = '60k-70k'
test_job['apply_url'] = 'https://test.com/v2'

result2 = client.rpc('batch_insert_jobs_with_dedup', {'p_jobs_data': [test_job]}).execute()
print(f'   Result: {result2.data} jobs inserted')

# Check if old was deleted and new created
job2 = client.table('jobs').select('job_id, job_title, job_description, salary, created_at').eq('job_id', 'test_delete_insert_123').execute()
if job2.data:
    print(f'   Job ID: {job2.data[0]["job_id"]}')
    print(f'   Title: {job2.data[0]["job_title"]}')
    print(f'   Description: {job2.data[0]["job_description"]}')
    print(f'   Salary: {job2.data[0]["salary"]}')
    print(f'   Created: {job2.data[0]["created_at"]}')

    new_created = job2.data[0]['created_at']

    if new_created > old_created:
        print('\n✅ SUCCESS: New created_at timestamp is newer (delete+insert worked!)')
    else:
        print('\n❌ FAILED: created_at was not refreshed')

    if 'UPDATED' in job2.data[0]['job_title']:
        print('✅ SUCCESS: Job content was updated')
    else:
        print('❌ FAILED: Job content was not updated')

# Cleanup
print('\n🧹 Cleaning up test job...')
client.table('jobs').delete().eq('job_id', 'test_delete_insert_123').execute()
print('✅ Test complete')
