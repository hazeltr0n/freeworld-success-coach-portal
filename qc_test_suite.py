#!/usr/bin/env python3
"""
FreeWorld Job Pipeline QC Test Suite

Comprehensive quality control testing for all classification and filtering functions.
Ensures jobs presented to free agents are compatible and we're not disqualifying good jobs.
"""

import pandas as pd
import json
from datetime import datetime
from pipeline import FreeWorldJobPipeline
from job_classifier import JobClassifier
from route_classifier import RouteClassifier

class QCTestSuite:
    def __init__(self):
        self.pipeline = FreeWorldJobPipeline()
        self.job_classifier = JobClassifier()
        self.route_classifier = RouteClassifier()
        self.results = {}
        
    def run_comprehensive_qc(self, test_data_file):
        """Run all QC tests on a dataset"""
        print("🧪 FREEWORLD JOB PIPELINE QC SUITE")
        print("=" * 60)
        print(f"Test data: {test_data_file}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Load test data
        df = pd.read_csv(test_data_file)
        print(f"📊 Loaded {len(df)} jobs for testing")
        
        # Run all QC tests
        self.test_llm_determinism(df.head(10))  # Small sample for speed
        self.test_filter_accuracy(test_data_file)
        self.test_llm_classification_accuracy(df)
        self.test_end_to_end_quality(test_data_file)
        
        # Generate QC report
        self.generate_qc_report()
        
    def test_llm_determinism(self, sample_df):
        """Test that LLM classifications are consistent across runs"""
        print("\n🔄 TESTING LLM DETERMINISM")
        print("-" * 40)
        
        # Prepare jobs for classification
        jobs = []
        for _, row in sample_df.iterrows():
            jobs.append({
                'job_id': row.get('job_id', str(hash(row['job_title']))),
                'job_title': row['job_title'],
                'company': row['company'],
                'location': row['location'],
                'job_description': row['job_description']
            })
        
        # Run twice
        results1 = self.job_classifier.classify_jobs_in_batches(jobs)
        results2 = self.job_classifier.classify_jobs_in_batches(jobs)
        
        # Compare results
        matches1 = {r['job_id']: r['match'] for r in results1}
        matches2 = {r['job_id']: r['match'] for r in results2}
        
        differences = 0
        for job_id in matches1.keys():
            if matches1[job_id] != matches2[job_id]:
                differences += 1
        
        determinism_score = (len(matches1) - differences) / len(matches1) * 100
        
        self.results['llm_determinism'] = {
            'score': determinism_score,
            'total_jobs': len(matches1),
            'differences': differences,
            'status': 'PASS' if differences == 0 else 'FAIL'
        }
        
        print(f"Determinism Score: {determinism_score:.1f}% ({len(matches1)-differences}/{len(matches1)} consistent)")
        print(f"Status: {'✅ PASS' if differences == 0 else '❌ FAIL'}")
        
    def test_filter_accuracy(self, test_data_file):
        """Test each filter for false positives and negatives"""
        print("\n🧹 TESTING FILTER ACCURACY") 
        print("-" * 40)
        
        # Run pipeline to see filtering results
        results = self.pipeline.run_full_pipeline([test_data_file], 'qc_test', 'Dallas', 'both')
        if not results:
            print("❌ Pipeline failed to process data")
            return
        pipeline_df = results['dataframe']
        
        # Analyze each filter category
        filter_results = {}
        
        # Check removal categories
        removal_categories = [
            'removed_md5_duplicate',
            'removed_r1', 
            'removed_r2',
            'removed_owner_op',
            'removed_school_bus',
            'removed_llm_bad'
        ]
        
        for category in removal_categories:
            removed_jobs = pipeline_df[pipeline_df['final_status'] == category]
            filter_results[category] = {
                'count': len(removed_jobs),
                'percentage': len(removed_jobs) / len(pipeline_df) * 100
            }
            print(f"{category}: {len(removed_jobs)} jobs ({len(removed_jobs)/len(pipeline_df)*100:.1f}%)")
        
        # Check included jobs for obvious problems
        included_jobs = pipeline_df[pipeline_df['final_status'] == 'included']
        
        # Flag potential false positives (bad jobs that got through)
        false_positive_flags = []
        for _, job in included_jobs.iterrows():
            title = str(job['job_title']).lower()
            desc = str(job['job_description']).lower()
            
            # Check for obvious red flags
            if any(keyword in title or keyword in desc for keyword in 
                   ['owner operator', 'lease purchase', '1099', 'hotshot']):
                false_positive_flags.append(f"Owner-op language: {job['company']}")
            
            if any(keyword in title or keyword in desc for keyword in
                   ['school bus', 'student transport', 'isd']):
                false_positive_flags.append(f"School bus: {job['company']}")
                
            if 'years experience' in desc or 'years of experience' in desc:
                false_positive_flags.append(f"Experience required: {job['company']}")
        
        self.results['filter_accuracy'] = {
            'removal_breakdown': filter_results,
            'included_count': len(included_jobs),
            'potential_false_positives': false_positive_flags,
            'false_positive_rate': len(false_positive_flags) / len(included_jobs) * 100 if len(included_jobs) > 0 else 0
        }
        
        print(f"\nIncluded jobs: {len(included_jobs)}")
        print(f"Potential false positives: {len(false_positive_flags)} ({len(false_positive_flags)/len(included_jobs)*100:.1f}%)")
        
        if false_positive_flags:
            print("🚨 Potential issues found:")
            for flag in false_positive_flags[:5]:  # Show first 5
                print(f"  - {flag}")
                
    def test_llm_classification_accuracy(self, df):
        """Test LLM classification accuracy on known examples"""
        print("\n🧠 TESTING LLM CLASSIFICATION ACCURACY")
        print("-" * 40)
        
        # Create test cases with known expected results
        test_cases = [
            {
                'job_title': 'CDL Driver - No Experience Required',
                'company': 'Good Company',
                'description': 'Looking for new CDL drivers. No experience required. Training provided.',
                'expected': 'good'
            },
            {
                'job_title': 'Owner Operator CDL Driver',
                'company': 'Bad Company', 
                'description': 'Must own your own truck. 5+ years experience required.',
                'expected': 'bad'
            },
            {
                'job_title': 'CDL Driver - Experience Preferred',
                'company': 'Maybe Company',
                'description': 'Experience preferred but will train the right candidate.',
                'expected': 'so-so'
            },
            {
                'job_title': 'CNA Position',
                'company': 'Healthcare Co',
                'description': 'Seeking certified nursing assistant. CNA certification required.',
                'expected': 'bad'
            }
        ]
        
        jobs_for_classification = []
        for i, case in enumerate(test_cases):
            jobs_for_classification.append({
                'job_id': f'test_case_{i}',
                'job_title': case['job_title'],
                'company': case['company'],
                'location': 'Test, TX',
                'job_description': case['description']
            })
        
        # Run classification
        results = self.job_classifier.classify_jobs_in_batches(jobs_for_classification)
        
        # Check accuracy
        correct = 0
        total = len(test_cases)
        
        for i, result in enumerate(results):
            expected = test_cases[i]['expected']
            actual = result['match']
            is_correct = expected == actual
            
            print(f"Test {i+1}: Expected '{expected}', Got '{actual}' {'✅' if is_correct else '❌'}")
            if is_correct:
                correct += 1
        
        accuracy = correct / total * 100
        
        self.results['llm_accuracy'] = {
            'score': accuracy,
            'correct': correct,
            'total': total,
            'status': 'PASS' if accuracy >= 80 else 'WARN' if accuracy >= 60 else 'FAIL'
        }
        
        print(f"\nLLM Accuracy: {accuracy:.1f}% ({correct}/{total})")
        
    def test_end_to_end_quality(self, test_data_file):
        """Test overall pipeline quality"""
        print("\n🎯 TESTING END-TO-END QUALITY")
        print("-" * 40)
        
        # Run full pipeline
        results = self.pipeline.run_full_pipeline([test_data_file], 'e2e_qc_test', 'Dallas', 'both')
        df = results['dataframe']
        
        # Calculate key metrics
        total_jobs = len(df)
        included_jobs = len(df[df['final_status'] == 'included'])
        retention_rate = included_jobs / total_jobs * 100
        
        # Quality metrics
        good_jobs = len(df[df['match'] == 'good'])
        bad_jobs = len(df[df['match'] == 'bad'])
        unknown_jobs = len(df[df['match'].isna()])
        
        self.results['end_to_end'] = {
            'total_jobs': total_jobs,
            'included_jobs': included_jobs,
            'retention_rate': retention_rate,
            'good_jobs': good_jobs,
            'bad_jobs': bad_jobs,
            'unknown_jobs': unknown_jobs,
            'unknown_rate': unknown_jobs / total_jobs * 100 if total_jobs > 0 else 0
        }
        
        print(f"Total jobs processed: {total_jobs}")
        print(f"Jobs included: {included_jobs} ({retention_rate:.1f}%)")
        print(f"Classification breakdown:")
        print(f"  ✅ Good: {good_jobs}")
        print(f"  ❌ Bad: {bad_jobs}")
        print(f"  ❓ Unknown: {unknown_jobs} ({unknown_jobs/total_jobs*100:.1f}%)")
        
    def generate_qc_report(self):
        """Generate comprehensive QC report"""
        print("\n📋 QC REPORT SUMMARY")
        print("=" * 60)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"data/qc_report_{timestamp}.json"
        
        # Overall status
        overall_status = "PASS"
        issues = []
        
        if self.results['llm_determinism']['status'] != 'PASS':
            overall_status = "FAIL"
            issues.append("LLM non-determinism detected")
            
        if self.results['filter_accuracy']['false_positive_rate'] > 10:
            overall_status = "WARN" if overall_status == "PASS" else overall_status
            issues.append("High false positive rate in filters")
            
        if self.results['llm_accuracy']['status'] == 'FAIL':
            overall_status = "FAIL"
            issues.append("LLM accuracy below threshold")
            
        if self.results['end_to_end']['unknown_rate'] > 20:
            overall_status = "WARN" if overall_status == "PASS" else overall_status
            issues.append("High unknown job rate")
        
        # Add overall assessment
        self.results['overall'] = {
            'status': overall_status,
            'issues': issues,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save detailed report
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Print summary
        print(f"Overall Status: {'✅ PASS' if overall_status == 'PASS' else '⚠️ WARN' if overall_status == 'WARN' else '❌ FAIL'}")
        if issues:
            print("Issues identified:")
            for issue in issues:
                print(f"  - {issue}")
        
        print(f"\n📄 Detailed report saved: {report_file}")
        print(f"QC completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # Run QC on test dataset
    test_suite = QCTestSuite()
    test_file = "/Users/freeworld_james/Desktop/FreeWorld_Jobs/form_search_results_20250820_204259.csv"
    test_suite.run_comprehensive_qc(test_file)