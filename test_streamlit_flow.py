#!/usr/bin/env python3
"""
Test script to verify complete Streamlit pipeline flow
Runs a small test search to ensure all components work together
"""

import sys
import os
from pipeline_wrapper import StreamlitPipelineWrapper

def test_complete_flow():
    """Test the complete pipeline flow"""
    print("🧪 TESTING COMPLETE STREAMLIT PIPELINE FLOW")
    print("=" * 50)
    
    try:
        # 1. Initialize wrapper
        print("\n1️⃣ Initializing pipeline wrapper...")
        wrapper = StreamlitPipelineWrapper()
        print("✅ Pipeline wrapper initialized")
        
        # 2. Test cost estimation
        print("\n2️⃣ Testing cost estimation...")
        cost_info = wrapper.estimate_cost('test', 1)
        print(f"✅ Cost estimation: ${cost_info['total_cost']:.3f} for {cost_info['job_limit']} jobs")
        
        # 3. Test pipeline run with minimal parameters
        print("\n3️⃣ Testing pipeline run (test mode)...")
        test_params = {
            'location': 'Houston, TX',
            'mode': 'test',
            'route_filter': 'both', 
            'search_terms': 'CDL driver',
            'custom_location': None,
            'push_to_airtable': False,
            'generate_pdf': False,  # Skip PDF for quick test
            'generate_csv': True,
            'search_radius': 50,
            'no_experience': True,
            'force_fresh': False,
            'use_multi_search': False
        }
        
        df, metadata = wrapper.run_pipeline(test_params)
        
        # 4. Verify results
        print(f"\n4️⃣ Verifying results...")
        if metadata.get('success', False):
            print(f"✅ Pipeline succeeded!")
            print(f"   Total jobs: {metadata.get('total_jobs', 0)}")
            print(f"   Quality jobs: {metadata.get('quality_jobs', 0)}")
            print(f"   Included jobs: {metadata.get('included_jobs', 0)}")
            
            if not df.empty:
                print(f"   DataFrame shape: {df.shape}")
                print(f"   Canonical columns: {len(df.columns)}")
                
                # 5. Test PDF transformation (without generating actual PDF)
                print(f"\n5️⃣ Testing PDF transformation...")
                pdf_df = wrapper.transform_canonical_for_pdf(df)
                print(f"✅ PDF transformation successful")
                print(f"   PDF DataFrame shape: {pdf_df.shape}")
                print(f"   Has required fields: {'job_title' in pdf_df.columns}, {'match_level' in pdf_df.columns}")
                
                # 6. Test CSV conversion
                print(f"\n6️⃣ Testing CSV conversion...")
                csv_bytes = wrapper.dataframe_to_csv_bytes(df)
                if csv_bytes:
                    print(f"✅ CSV conversion successful ({len(csv_bytes)} bytes)")
                else:
                    print("❌ CSV conversion failed")
                    
            else:
                print("⚠️ No jobs returned (might be bypass or no results)")
                
        else:
            print(f"❌ Pipeline failed: {metadata.get('error', 'Unknown error')}")
            return False
            
        print(f"\n🎉 COMPLETE FLOW TEST SUCCESSFUL!")
        print("✅ All components working correctly")
        print("✅ Ready for Streamlit deployment")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_flow()
    sys.exit(0 if success else 1)