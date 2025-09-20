#!/usr/bin/env python3
"""
Comprehensive Test Script for Dual Classification Pipelines
Tests both CDL Traditional and Career Pathways classifiers with Indeed fresh only searches
Includes proper Supabase upload and pathway badge validation
"""

import os
import sys
import pandas as pd
from datetime import datetime
import argparse

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dual_classifier(location="Houston", max_jobs=50, test_both=True):
    """
    Test both CDL and Pathway classifiers with Indeed fresh only searches

    Args:
        location: Location to search
        max_jobs: Maximum number of jobs to process
        test_both: If True, test both classifiers; if False, test pathway only
    """

    print("=" * 80)
    print("🧪 DUAL CLASSIFIER TEST SCRIPT")
    print("=" * 80)
    print(f"📍 Location: {location}")
    print(f"📊 Max Jobs: {max_jobs}")
    print(f"🔬 Testing: {'Both CDL & Pathway Classifiers' if test_both else 'Pathway Classifier Only'}")
    print("=" * 80)

    try:
        from pipeline_v3 import FreeWorldPipelineV3

        # Initialize pipeline
        pipeline = FreeWorldPipelineV3()

        # Test configurations
        test_configs = []

        if test_both:
            test_configs.append({
                'name': 'CDL Traditional',
                'classifier_type': 'cdl',
                'search_terms': 'CDL Driver No Experience',
                'expected_fields': ['ai.match', 'ai.summary', 'ai.route_type']
            })

        test_configs.append({
            'name': 'Career Pathways',
            'classifier_type': 'pathway',
            'search_terms': 'warehouse worker dock loader forklift driver training construction apprentice',
            'expected_fields': ['ai.match', 'ai.summary', 'ai.career_pathway', 'ai.training_provided']
        })

        results = {}

        for i, config in enumerate(test_configs, 1):
            print(f"\n🔍 TEST {i}/{len(test_configs)}: {config['name']} Classifier")
            print("-" * 60)

            # Configure pipeline parameters for Indeed fresh only
            mode_info = {
                'mode': 'test',
                'limit': max_jobs,
                'source': 'indeed_fresh'
            }

            # Run pipeline with specific classifier
            print(f"🚀 Running {config['name']} pipeline...")
            pipeline_results = pipeline.run_complete_pipeline(
                location=location,
                mode_info=mode_info,
                search_terms=config['search_terms'],
                force_fresh=True,  # Indeed fresh only
                force_fresh_classification=True,  # Force fresh AI classification
                classifier_type=config['classifier_type'],
                push_to_airtable=False,  # Don't push to Airtable during testing
                generate_pdf=False,  # Don't generate PDF during testing
                generate_csv=True,   # Generate CSV for analysis
                route_filter='both',
                radius=50,
                no_experience=True
            )

            # Extract results
            df = pipeline_results.get('jobs_df', pd.DataFrame())
            metadata = pipeline_results.get('metadata', {})

            print(f"✅ Pipeline completed: {len(df)} jobs processed")

            # Analyze results
            analysis = analyze_classifier_results(df, config)
            results[config['name']] = {
                'config': config,
                'dataframe': df,
                'metadata': metadata,
                'analysis': analysis
            }

            # Display analysis
            display_analysis(config['name'], analysis)

            # Test Supabase upload if we have jobs
            if not df.empty and df.get('ai.match', pd.Series()).notna().any():
                test_supabase_upload(df, config['classifier_type'])

            print(f"💾 Results stored for {config['name']}")

        # Compare results if testing both
        if test_both and len(results) == 2:
            print(f"\n📊 COMPARATIVE ANALYSIS")
            print("-" * 60)
            compare_classifier_results(results)

        # Test pathway badges
        if 'Career Pathways' in results:
            test_pathway_badges(results['Career Pathways']['dataframe'])

        print(f"\n✅ DUAL CLASSIFIER TEST COMPLETED")
        print("=" * 80)

        return results

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return {}

def analyze_classifier_results(df, config):
    """Analyze classification results for quality and accuracy"""

    analysis = {
        'total_jobs': len(df),
        'classified_jobs': 0,
        'match_distribution': {},
        'pathway_distribution': {},
        'training_jobs': 0,
        'job_id_format': {'cdl_suffix': 0, 'pathway_suffix': 0},
        'required_fields_present': True,
        'missing_fields': []
    }

    if df.empty:
        return analysis

    # Count classified jobs (have ai.match)
    classified_mask = df['ai.match'].notna()
    analysis['classified_jobs'] = classified_mask.sum()

    # Match quality distribution
    if 'ai.match' in df.columns:
        analysis['match_distribution'] = df['ai.match'].value_counts().to_dict()

    # Career pathway analysis (for pathway classifier)
    if config['classifier_type'] == 'pathway':
        if 'ai.career_pathway' in df.columns:
            pathway_counts = df['ai.career_pathway'].value_counts()
            analysis['pathway_distribution'] = pathway_counts.to_dict()

        if 'ai.training_provided' in df.columns:
            analysis['training_jobs'] = df['ai.training_provided'].sum()

    # Job ID format validation
    if 'id.job' in df.columns:
        job_ids = df['id.job'].astype(str)
        analysis['job_id_format']['cdl_suffix'] = job_ids.str.endswith('_cdl').sum()
        analysis['job_id_format']['pathway_suffix'] = job_ids.str.endswith('_pathway').sum()

    # Check required fields
    for field in config['expected_fields']:
        if field not in df.columns or df[field].isna().all():
            analysis['required_fields_present'] = False
            analysis['missing_fields'].append(field)

    return analysis

def display_analysis(classifier_name, analysis):
    """Display analysis results in a readable format"""

    print(f"\n📈 {classifier_name} Analysis:")
    print(f"   Total Jobs: {analysis['total_jobs']}")
    print(f"   Classified: {analysis['classified_jobs']}")

    if analysis['match_distribution']:
        print(f"   Match Quality:")
        for match, count in analysis['match_distribution'].items():
            print(f"     {match}: {count}")

    if analysis['pathway_distribution']:
        print(f"   Career Pathways:")
        for pathway, count in analysis['pathway_distribution'].items():
            print(f"     {pathway}: {count}")
        print(f"   Training Provided: {analysis['training_jobs']}")

    # Job ID format validation
    job_id_info = analysis['job_id_format']
    print(f"   Job ID Format:")
    print(f"     CDL suffix: {job_id_info['cdl_suffix']}")
    print(f"     Pathway suffix: {job_id_info['pathway_suffix']}")

    # Field validation
    if analysis['required_fields_present']:
        print("   ✅ All required fields present")
    else:
        print(f"   ❌ Missing fields: {', '.join(analysis['missing_fields'])}")

def compare_classifier_results(results):
    """Compare results between CDL and Pathway classifiers"""

    cdl_results = results.get('CDL Traditional', {})
    pathway_results = results.get('Career Pathways', {})

    if not cdl_results or not pathway_results:
        print("   ⚠️ Cannot compare - missing results")
        return

    cdl_analysis = cdl_results['analysis']
    pathway_analysis = pathway_results['analysis']

    print(f"   CDL Jobs: {cdl_analysis['total_jobs']} | Pathway Jobs: {pathway_analysis['total_jobs']}")
    print(f"   CDL Classified: {cdl_analysis['classified_jobs']} | Pathway Classified: {pathway_analysis['classified_jobs']}")

    # Compare match distributions
    cdl_good = cdl_analysis['match_distribution'].get('good', 0)
    pathway_good = pathway_analysis['match_distribution'].get('good', 0)

    print(f"   Good Matches: CDL={cdl_good} | Pathway={pathway_good}")

    # Pathway-specific metrics
    if pathway_analysis['pathway_distribution']:
        non_pathway = pathway_analysis['pathway_distribution'].get('no_pathway', 0)
        total_pathways = pathway_analysis['total_jobs'] - non_pathway
        print(f"   Career Pathway Jobs: {total_pathways}/{pathway_analysis['total_jobs']}")

def test_supabase_upload(df, classifier_type):
    """Test Supabase upload functionality"""

    print(f"\n🗄️ Testing Supabase Upload for {classifier_type} classifier...")

    try:
        from supabase_utils import get_client

        client = get_client()
        if not client:
            print("   ⚠️ Supabase client not available")
            return

        # Filter to only quality jobs for upload test
        quality_jobs = df[df['ai.match'].isin(['good', 'so-so'])].copy()

        if quality_jobs.empty:
            print("   ⚠️ No quality jobs to test upload")
            return

        # Test with first job
        test_job = quality_jobs.iloc[0].to_dict()

        # Prepare job data for Supabase
        supabase_job = {
            'job_id': test_job.get('id.job', 'test_id'),
            'job_title': test_job.get('source.title', 'Test Job'),
            'company': test_job.get('source.company', 'Test Company'),
            'location': test_job.get('source.location', 'Test Location'),
            'match_level': test_job.get('ai.match', 'good'),
            'summary': test_job.get('ai.summary', 'Test summary'),
            'route_type': test_job.get('ai.route_type', 'Local'),
            'fair_chance': test_job.get('ai.fair_chance', False),
            'apply_url': test_job.get('source.url', 'https://example.com'),
            'tracked_url': test_job.get('meta.tracked_url', ''),
            'scraped_at': datetime.now().isoformat(),
            'classifier_type': classifier_type
        }

        # Add pathway fields if present
        if classifier_type == 'pathway':
            supabase_job.update({
                'career_pathway': test_job.get('ai.career_pathway', ''),
                'training_provided': test_job.get('ai.training_provided', False)
            })

        # Test insert (use upsert to avoid conflicts)
        result = client.table('jobs').upsert(supabase_job).execute()

        if result.data:
            print(f"   ✅ Supabase upload successful (job_id: {supabase_job['job_id'][:12]}...)")

            # Test pathway fields if applicable
            if classifier_type == 'pathway':
                uploaded_job = result.data[0]
                if 'career_pathway' in uploaded_job:
                    print(f"   ✅ Career pathway field uploaded: {uploaded_job.get('career_pathway', 'None')}")
                if 'training_provided' in uploaded_job:
                    print(f"   ✅ Training provided field uploaded: {uploaded_job.get('training_provided', False)}")
        else:
            print("   ❌ Supabase upload failed - no data returned")

    except Exception as e:
        print(f"   ❌ Supabase upload failed: {e}")

def test_pathway_badges(df):
    """Test pathway badge generation"""

    print(f"\n🏷️ Testing Pathway Badges...")

    if df.empty:
        print("   ⚠️ No jobs to test badges")
        return

    try:
        from pdf.html_pdf_generator import jobs_dataframe_to_dicts

        # Convert DataFrame to job dicts for badge testing
        jobs = jobs_dataframe_to_dicts(df, candidate_id="test_candidate")

        badge_counts = {
            'match_badges': 0,
            'pathway_badges': 0,
            'training_badges': 0
        }

        badge_types = set()

        for job in jobs:
            if job.get('match_badge'):
                badge_counts['match_badges'] += 1

            if job.get('career_pathway_badge'):
                badge_counts['pathway_badges'] += 1
                badge_types.add(job['career_pathway_badge'])

        print(f"   Match Badges: {badge_counts['match_badges']}")
        print(f"   Pathway Badges: {badge_counts['pathway_badges']}")

        if badge_types:
            print(f"   Badge Types Found: {', '.join(sorted(badge_types))}")
        else:
            print("   ⚠️ No pathway badges generated")

    except Exception as e:
        print(f"   ❌ Badge testing failed: {e}")

def main():
    """Main function with command line argument parsing"""

    parser = argparse.ArgumentParser(description='Test dual classification pipelines')
    parser.add_argument('--location', default='Houston', help='Search location')
    parser.add_argument('--max-jobs', type=int, default=50, help='Maximum jobs to process')
    parser.add_argument('--pathway-only', action='store_true', help='Test pathway classifier only')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        print("🔧 Verbose mode enabled")

    # Run the test
    results = test_dual_classifier(
        location=args.location,
        max_jobs=args.max_jobs,
        test_both=not args.pathway_only
    )

    if results:
        print(f"\n📁 Test results available in memory")
        for name, result in results.items():
            job_count = len(result['dataframe'])
            print(f"   {name}: {job_count} jobs")

    return results

if __name__ == "__main__":
    main()