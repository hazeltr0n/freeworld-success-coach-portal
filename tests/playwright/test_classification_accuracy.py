"""
Classification Accuracy Testing - Redirects to Master Efficient Test
For maximum efficiency, all classification accuracy testing is now handled by test_master_efficient.py
This provides complete QA coverage while reusing DataFrames for optimal performance.
"""

import pytest
from playwright.sync_api import Page
from conftest import DataCollector

class TestClassificationAccuracy:
    """Classification accuracy tests - now uses master efficient approach for maximum speed"""

    def test_classification_accuracy_comprehensive(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """Complete classification accuracy testing using master efficient approach"""
        print("🧠 CLASSIFICATION ACCURACY TESTING")
        print("⚡ Using Master Efficient Test for complete classification validation")
        print("🎯 This approach tests CDL, Pathways, Consistency, and Supabase in one efficient run")

        # Import and run the master efficient test which includes all classification testing
        from test_master_efficient import TestMasterEfficient
        master_tester = TestMasterEfficient()

        # Run the master test which includes comprehensive classification validation
        master_tester.test_master_comprehensive_validation(authenticated_admin_page, test_data_collector)

        print("✅ Classification accuracy testing completed as part of master efficient validation")

    def test_classification_cherry_pick(self, authenticated_admin_page: Page, test_data_collector: DataCollector):
        """Cherry-pick classification testing only (requires master test data)"""
        print("🍒 CHERRY-PICK: Classification Testing Only")

        from test_master_efficient import TestMasterEfficient
        master_tester = TestMasterEfficient()

        # Run cherry-pick classification test
        master_tester.test_cherry_pick_classification_only(authenticated_admin_page, test_data_collector)

        print("✅ Cherry-pick classification testing completed")

