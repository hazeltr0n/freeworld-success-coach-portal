#!/usr/bin/env python3
"""
Test HTML/CSS PDF generation with real CSV data
"""

import pandas as pd
from pdf_generator import generate_pdf
from pdf.html_pdf_generator import jobs_dataframe_to_dicts, render_jobs_html
import os
from pathlib import Path

def test_csv_html_pdf():
    """Test HTML PDF generation with real Dallas jobs CSV"""
    
    # Load real CSV data
    csv_path = "/workspaces/freeworld-success-coach-portal/FreeWorld_Jobs/Dallas_TX_complete_jobs_20250831_095204.csv"
    print(f"📁 Loading CSV: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded CSV with {len(df)} jobs")
        print(f"📊 Columns: {list(df.columns)}")
        
        # Take a sample of jobs for testing (first 10)
        sample_df = df.head(10)
        print(f"🎯 Testing with {len(sample_df)} sample jobs")
        
        # Map CSV columns to our template format
        mapped_data = []
        for _, row in sample_df.iterrows():
            # Safe string conversion with null handling
            def safe_str(val, default=''):
                if pd.isna(val) or val is None:
                    return default
                return str(val)
            
            def safe_bool(val):
                if pd.isna(val) or val is None:
                    return False
                return bool(val)
            
            ai_match = safe_str(row.get('ai.match', ''), 'unknown').lower()
            match_badge = ai_match.title() + ' Match' if ai_match != 'unknown' else 'Excellent Match'
            
            mapped_data.append({
                'Title': safe_str(row.get('source.title', ''), 'CDL Driver Position'),
                'Company': safe_str(row.get('source.company', ''), 'Trucking Company'), 
                'City': safe_str(row.get('norm.city', ''), 'Dallas'),
                'State': safe_str(row.get('norm.state', ''), 'TX'),
                'Route': safe_str(row.get('ai.route_type', ''), 'OTR'),
                'MatchBadge': match_badge,
                'FairChance': safe_bool(row.get('ai.fair_chance', False)),
                'Description': safe_str(row.get('norm.description', ''), 'No description available'),
                'ApplyURL': safe_str(row.get('clean_apply_url', '') or row.get('source.apply_url', ''), 'https://example.com'),
                'ShortURL': safe_str(row.get('meta.tracked_url', ''), 'https://fw.ly/test')
            })
        
        # Convert to DataFrame for our generator
        test_df = pd.DataFrame(mapped_data)
        print(f"🔄 Mapped data to template format")
        
        # Test HTML generation
        print(f"\n🧪 Testing HTML template generation...")
        jobs = jobs_dataframe_to_dicts(test_df)
        agent_params = {
            'location': 'Dallas Test',
            'agent_name': 'Test Agent',
            'agent_uuid': 'test-123',
            'coach_username': 'testcoach'
        }
        html = render_jobs_html(jobs, agent_params)
        
        # Save HTML preview
        html_path = 'out/csv_test_preview.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ HTML preview saved: {html_path}")
        
        # Test all PDF backends
        backends = ['fpdf', 'playwright', 'weasyprint']
        results = {}
        
        for backend in backends:
            print(f"\n🧪 Testing {backend} backend...")
            output_path = f'out/csv_test_{backend}.pdf'
            
            try:
                result = generate_pdf(
                    test_df,
                    output_path,
                    market="Dallas Test",
                    backend=backend,
                    candidate_name="Test Agent Dallas",
                    candidate_id="test-csv-123",
                    coach_username="testcoach"
                )
                
                # Check file was created
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path) / 1024  # KB
                    results[backend] = {'success': True, 'size_kb': file_size}
                    print(f"✅ {backend}: Success ({file_size:.1f} KB)")
                else:
                    results[backend] = {'success': False, 'error': 'File not created'}
                    print(f"❌ {backend}: File not created")
                    
            except Exception as e:
                results[backend] = {'success': False, 'error': str(e)}
                print(f"❌ {backend}: {e}")
        
        # Print summary
        print(f"\n{'='*50}")
        print("CSV PDF GENERATION TEST RESULTS")
        print(f"{'='*50}")
        print(f"📊 Source data: {len(df)} Dallas jobs")
        print(f"🎯 Test sample: {len(sample_df)} jobs")
        print(f"📄 HTML preview: {html_path}")
        
        for backend, result in results.items():
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            print(f"{backend:12} {status}")
            if result['success']:
                print(f"             Size: {result['size_kb']:.1f} KB")
            else:
                print(f"             Error: {result['error']}")
        
        print(f"\n🎉 Test completed! Check out/ directory for generated files.")
        
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")

if __name__ == '__main__':
    # Create output directory
    Path('out').mkdir(exist_ok=True)
    test_csv_html_pdf()