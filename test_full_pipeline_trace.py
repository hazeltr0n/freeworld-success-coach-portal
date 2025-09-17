#!/usr/bin/env python3
"""
Full pipeline test to trace where descriptions get lost during CSV processing
"""

import pandas as pd
import sys
from pathlib import Path
import os

# Add current directory to path
sys.path.append('.')

# Set dummy environment variables to avoid pipeline initialization errors
os.environ['OUTSCRAPER_API_KEY'] = 'dummy'
os.environ['OPENAI_API_KEY'] = 'dummy'

def test_full_pipeline():
    """Test the full CSV processing pipeline to find where descriptions are lost"""
    
    print("🔍 FULL PIPELINE TRACE - CSV DESCRIPTION MAPPING")
    print("=" * 70)
    
    # Step 1: Load CSV and create raw rows (same as classify_csv.py)
    csv_path = Path("Outscraper-20250905004557xs8b_dallas_-_indeed.csv")
    if not csv_path.exists():
        print(f"❌ CSV not found: {csv_path}")
        return
    
    df_src = pd.read_csv(csv_path).head(2)  # Just 2 rows for detailed testing
    print(f"✅ Loaded {len(df_src)} rows from CSV")
    
    # Map to raw Outscraper-like dicts (same logic as classify_csv.py)
    cols_map = {c.lower(): c for c in df_src.columns}
    
    def _first(row, cols_map, names, default=""):
        for n in names:
            k = cols_map.get(n.lower())
            if k is not None:
                v = row.get(k)
                if pd.notna(v) and str(v).strip():
                    return str(v).strip()
        return default
    
    raw_rows = []
    for i, (_, row) in enumerate(df_src.iterrows()):
        title = _first(row, cols_map, ["title", "job_title", "job"], "")
        company = _first(row, cols_map, ["company", "company_name", "employer"], "")
        location_raw = _first(row, cols_map, ["formattedLocation", "location", "city", "job_location"], "")
        apply_url = _first(row, cols_map, ["viewJobLink", "apply_url", "applyUrl", "url", "link"], "")
        description = _first(row, cols_map, ["snippet", "description", "job_description", "jobDescription", "details"], "")
        
        print(f"\n🔍 RAW ROW {i+1} EXTRACTED:")
        print(f"   title: '{title}' (len={len(title)})")
        print(f"   company: '{company}' (len={len(company)})")
        print(f"   description: (len={len(description)})")
        print(f"   description preview: '{str(description)[:100]}...'")
        
        raw_rows.append({
            "title": title,
            "company": company,
            "formattedLocation": location_raw,
            "viewJobLink": apply_url,
            "snippet": description,  # Use 'snippet' key to match canonical transform expectations
        })
    
    print(f"✅ Created {len(raw_rows)} raw rows")
    
    # Step 2: Canonical transform (ingestion stage)
    print(f"\n📥 STEP 2: CANONICAL TRANSFORM (INGESTION)")
    print("=" * 50)
    
    from canonical_transforms import transform_ingest_outscraper
    
    run_id = "test_full_trace"
    df_canonical = transform_ingest_outscraper(raw_rows, run_id, '')
    
    print(f"✅ Canonical transform: {len(df_canonical)} rows")
    
    # Check source.description_raw
    for i in range(len(df_canonical)):
        desc_raw = df_canonical.iloc[i]['source.description_raw']
        print(f"   ROW {i+1} source.description_raw: (len={len(str(desc_raw))}) '{str(desc_raw)[:100]}...'")
    
    # Step 3: Normalization stage
    print(f"\n🧹 STEP 3: NORMALIZATION")
    print("=" * 50)
    
    from canonical_transforms import transform_normalize
    
    df_norm = transform_normalize(df_canonical)
    
    print(f"✅ Normalization: {len(df_norm)} rows")
    
    # Check both source.description_raw and norm.description
    for i in range(len(df_norm)):
        desc_raw = df_norm.iloc[i].get('source.description_raw', '')
        desc_norm = df_norm.iloc[i].get('norm.description', '')
        print(f"   ROW {i+1}:")
        print(f"     source.description_raw: (len={len(str(desc_raw))}) '{str(desc_raw)[:50]}...'")
        print(f"     norm.description: (len={len(str(desc_norm))}) '{str(desc_norm)[:50]}...'")
    
    # Step 4: Business rules stage
    print(f"\n⚖️ STEP 4: BUSINESS RULES")
    print("=" * 50)
    
    from canonical_transforms import transform_business_rules
    
    df_rules = transform_business_rules(df_norm, filter_settings={})
    
    print(f"✅ Business rules: {len(df_rules)} rows")
    
    # Check descriptions still intact
    for i in range(len(df_rules)):
        desc_raw = df_rules.iloc[i].get('source.description_raw', '')
        desc_norm = df_rules.iloc[i].get('norm.description', '')
        print(f"   ROW {i+1}:")
        print(f"     source.description_raw: (len={len(str(desc_raw))})")
        print(f"     norm.description: (len={len(str(desc_norm))})")
    
    # Step 5: Deduplication stage  
    print(f"\n🔄 STEP 5: DEDUPLICATION")
    print("=" * 50)
    
    try:
        from pipeline_v3 import FreeWorldPipelineV3
        pipe = FreeWorldPipelineV3()
        df_dedup = pipe._stage4_deduplication(df_rules)
        
        print(f"✅ Deduplication: {len(df_dedup)} rows")
        
        # Check descriptions after dedup
        for i in range(len(df_dedup)):
            desc_raw = df_dedup.iloc[i].get('source.description_raw', '')
            desc_norm = df_dedup.iloc[i].get('norm.description', '')
            print(f"   ROW {i+1}:")
            print(f"     source.description_raw: (len={len(str(desc_raw))})")
            print(f"     norm.description: (len={len(str(desc_norm))})")
            
        # Step 6: AI Classification preparation
        print(f"\n🤖 STEP 6: AI CLASSIFICATION PREPARATION")
        print("=" * 50)
        
        # Test the exact logic from pipeline_v3.py line 1365+
        jobs_for_ai = []
        for _, job in df_dedup.iterrows():
            # This is the exact logic from pipeline_v3.py:1368-1373
            raw_desc = job.get('source.description_raw', '')
            clean_desc = job.get('norm.description', '')
            
            # Use cleaned description if available and not empty, otherwise fallback to raw
            final_desc = clean_desc if clean_desc and str(clean_desc).strip() else raw_desc
            
            job_data = {
                'job_id': job['id.job'],
                'job_title': job.get('source.title', ''),
                'company': job.get('source.company', ''),
                'location': job.get('source.location_raw', ''),
                'job_description': final_desc
            }
            jobs_for_ai.append(job_data)
            
            print(f"   AI PREP ROW {len(jobs_for_ai)}:")
            print(f"     raw_desc: (len={len(str(raw_desc))})")
            print(f"     clean_desc: (len={len(str(clean_desc))})")
            print(f"     final_desc: (len={len(str(final_desc))})")
            print(f"     job_description in AI payload: (len={len(str(job_data['job_description']))}) '{str(job_data['job_description'])[:100]}...'")
            
        print(f"✅ AI classification preparation: {len(jobs_for_ai)} jobs ready")
            
        # Check if any have empty descriptions
        empty_desc_count = sum(1 for job in jobs_for_ai if not str(job['job_description']).strip())
        if empty_desc_count > 0:
            print(f"❌ WARNING: {empty_desc_count} jobs have empty descriptions for AI!")
        else:
            print(f"✅ All jobs have descriptions for AI classification")
            
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {e}")
        print("Skipping deduplication and AI prep stages")
    
    print(f"\n✅ Full pipeline trace complete")
    print("=" * 70)

if __name__ == "__main__":
    test_full_pipeline()