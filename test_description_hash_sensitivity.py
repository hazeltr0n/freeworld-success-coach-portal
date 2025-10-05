#!/usr/bin/env python3
"""
Test how different descriptions need to be to get different hashes
"""
import json
import hashlib
import re
from html import unescape

def strip_html(text):
    """Strip HTML tags"""
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    text = unescape(text)
    return text.strip()

def generate_content_hash(description: str) -> str:
    """Generate hash from description content"""
    # Strip HTML
    desc_clean = strip_html(description).lower()[:500]

    # Remove common filler words
    for word in ['driver', 'cdl', 'class', 'truck', 'a', 'b', 'the', 'and', 'or', 'our', 'we', 'you', 'your']:
        desc_clean = desc_clean.replace(f' {word} ', ' ')

    # Normalize whitespace
    desc_clean = ' '.join(desc_clean.split())

    return hashlib.md5(desc_clean.encode()).hexdigest()[:12]

# Load DriverPulse data
with open('driver_pulse_full_jobs_20251004_014039.json', 'r') as f:
    jobs = json.load(f)

print("🔍 Testing Description Hash Sensitivity")
print("=" * 80)
print()

# Group by company
from collections import defaultdict
company_jobs = defaultdict(list)

for job in jobs:
    company = job.get('company_name', '')
    if company:
        company_jobs[company].append(job)

# Test Zimmerman (16 jobs - should some be dupes?)
print("🏢 Zimmerman Transfer, Inc. (16 jobs)")
print("-" * 80)

zim_jobs = company_jobs['Zimmerman Transfer, Inc.']
print(f"Total jobs: {len(zim_jobs)}")
print()

# Generate hashes and group
hash_groups = defaultdict(list)
for job in zim_jobs:
    desc = job.get('job_description', '')
    hash_val = generate_content_hash(desc)
    hash_groups[hash_val].append(job)

print(f"Unique hashes: {len(hash_groups)}")
print()

# Show groups
for i, (hash_val, jobs_in_group) in enumerate(hash_groups.items(), 1):
    print(f"Hash Group {i}: {hash_val} ({len(jobs_in_group)} jobs)")
    for job in jobs_in_group:
        title = job.get('job_title', '')
        salary = f"${job.get('job_min_pay', '')}-${job.get('job_max_pay', '')} {job.get('job_min_max_pay_unit', '')}"
        print(f"  - {title}")
        print(f"    Salary: {salary}")
    print()

print()
print("=" * 80)
print("🔬 Detailed Comparison: First 2 Jobs")
print("=" * 80)
print()

job1 = zim_jobs[0]
job2 = zim_jobs[1]

print(f"Job 1: {job1['job_title']}")
print(f"Hash:  {generate_content_hash(job1['job_description'])}")
print(f"First 300 chars of cleaned description:")
desc1_clean = strip_html(job1['job_description']).lower()[:300]
print(desc1_clean)
print()

print(f"Job 2: {job2['job_title']}")
print(f"Hash:  {generate_content_hash(job2['job_description'])}")
print(f"First 300 chars of cleaned description:")
desc2_clean = strip_html(job2['job_description']).lower()[:300]
print(desc2_clean)
print()

# Calculate exact difference
if generate_content_hash(job1['job_description']) == generate_content_hash(job2['job_description']):
    print("✅ SAME HASH - Would be deduplicated")
else:
    print("❌ DIFFERENT HASH - Would be kept as separate jobs")
    print()
    print("Character-by-character diff:")
    from difflib import SequenceMatcher
    ratio = SequenceMatcher(None, desc1_clean, desc2_clean).ratio()
    print(f"Similarity: {ratio*100:.1f}%")

print()
print("=" * 80)
print("📊 Summary for All Companies")
print("=" * 80)

for company, jobs_list in sorted(company_jobs.items()):
    if len(jobs_list) > 1:
        hash_groups_company = defaultdict(list)
        for job in jobs_list:
            desc = job.get('job_description', '')
            hash_val = generate_content_hash(desc)
            hash_groups_company[hash_val].append(job)

        reduction = len(jobs_list) - len(hash_groups_company)
        if reduction > 0:
            print(f"{company}: {len(jobs_list)} jobs → {len(hash_groups_company)} unique ({reduction} deduplicated)")
