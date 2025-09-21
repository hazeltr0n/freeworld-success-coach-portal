# FreeWorld Success Coach Portal - Playwright Testing Suite

Comprehensive automated testing suite for pre-production validation and quality assurance.

## 🎯 Overview

This testing suite provides one-click automation to validate all critical functionality before deploying new features to production. It tests both search paths (Memory Only and Indeed Fresh), both classifiers (CDL Traditional and Career Pathways), Supabase integration, link tracking, and scheduled search functionality.

## 🏗️ Test Architecture

### Test Suites

1. **Search Paths (`test_search_paths.py`)**
   - Memory Only search with CDL Traditional classifier
   - Memory Only search with Career Pathways classifier
   - Indeed Fresh Only search with CDL Traditional classifier
   - Indeed Fresh Only search with Career Pathways classifier
   - Multiple search terms handling
   - Filter combinations testing

2. **Classification Accuracy (`test_classification_accuracy.py`)**
   - CDL Traditional classifier accuracy validation
   - Career Pathways classifier accuracy validation
   - Classification consistency across searches
   - Forced fresh classification testing
   - Supabase data integrity verification

3. **Scheduled Search (`test_scheduled_search.py`)**
   - Batch job creation and submission
   - CDL Traditional batch processing
   - Career Pathways batch processing
   - Batch status monitoring
   - Multi-location batch searches
   - Webhook processing validation

4. **Link Tracking (`test_link_tracking.py`)**
   - Agent portal link generation
   - Bulk portal link regeneration
   - Job tracking links in search results
   - Click analytics system functionality
   - PDF generation with tracking links
   - Short.io API integration testing

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install playwright pytest python-dotenv

# Install Playwright browsers
playwright install
```

### Environment Setup

Ensure your `.streamlit/secrets.toml` or `.env` file contains:

```toml
OPENAI_API_KEY = "sk-..."
OUTSCRAPER_API_KEY = "..."
SUPABASE_URL = "https://..."
SUPABASE_ANON_KEY = "..."
SHORT_IO_API_KEY = "..."
SHORT_DOMAIN = "freeworldjobs.short.gy"
```

### Run All Tests

```bash
# Navigate to test directory
cd tests/playwright

# Run complete test suite
python run_tests.py

# Run specific test suites
python run_tests.py --suites search_paths classification

# Run with verbose output
python run_tests.py --verbose

# Skip environment checks (if already validated)
python run_tests.py --skip-env-check

# Skip server startup (if already running)
python run_tests.py --skip-server-start
```

### Individual Test Execution

```bash
# Run specific test file
pytest test_search_paths.py -v

# Run specific test method
pytest test_search_paths.py::TestSearchPaths::test_memory_only_cdl_traditional -v

# Run with detailed output
pytest test_classification_accuracy.py -v -s
```

## 📊 Test Configuration

### Default Test Parameters

```python
TEST_CONFIG = {
    "base_url": "http://localhost:8501",
    "timeout": 30000,
    "admin_username": "admin",
    "admin_password": "freeworld2024",
    "test_locations": ["Houston, TX", "Dallas, TX", "Austin, TX"],
    "test_search_terms": ["CDL driver", "truck driver", "warehouse, forklift"],
    "classifiers": ["CDL Traditional", "Career Pathways"],
    "search_modes": ["memory_only", "indeed_fresh"],
    "pathway_options": [
        "cdl_pathway", "dock_to_driver", "internal_cdl_training",
        "warehouse_to_driver", "logistics_progression", "general_warehouse"
    ]
}
```

### Customizing Test Parameters

Edit `conftest.py` to modify:
- Test locations and search terms
- Timeout values
- Authentication credentials
- Classifier options and pathway preferences

## 🧪 Test Coverage

### Search Functionality
- ✅ Memory Only searches (both classifiers)
- ✅ Indeed Fresh Only searches (both classifiers)
- ✅ Multiple search terms (comma-separated)
- ✅ Filter combinations (route, quality, experience)
- ✅ Search parameter validation
- ✅ Search completion and result extraction

### Classification System
- ✅ CDL Traditional classifier accuracy
- ✅ Career Pathways classifier accuracy
- ✅ Classification consistency testing
- ✅ Forced fresh classification
- ✅ AI match quality validation
- ✅ Route type classification
- ✅ Career pathway categorization

### Database Integration
- ✅ Supabase job uploads
- ✅ Classification data integrity
- ✅ Click event tracking
- ✅ Database schema validation
- ✅ Recent data verification

### Link Management
- ✅ Portal link generation for agents
- ✅ Bulk link regeneration
- ✅ Job tracking link creation
- ✅ Short.io API integration
- ✅ Analytics dashboard functionality
- ✅ PDF tracking link inclusion

### Batch Processing
- ✅ Scheduled search submission
- ✅ Batch status monitoring
- ✅ Multi-location batch searches
- ✅ Webhook processing verification
- ✅ Async job management

## 📈 Test Results and Reporting

### Automated Reports

The test runner generates comprehensive reports:

```
reports/
├── test_report_YYYYMMDD_HHMMSS.json    # Detailed JSON report
├── search_paths_results.xml            # JUnit XML for CI/CD
├── classification_results.xml          # Individual suite results
├── scheduled_search_results.xml
└── link_tracking_results.xml
```

### Report Contents

- Test execution summary
- Individual test results
- Performance metrics (jobs found, duration)
- Supabase upload verification
- Link generation statistics
- Error details and stack traces

### Sample Report Output

```
📊 TEST SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Run Time: 2025-09-21 16:30:00
⏱️  Total Duration: 847.3 seconds
📦 Test Suites: 4
✅ Passed: 4
❌ Failed: 0
💥 Errors: 0
⏰ Timeouts: 0
📈 Success Rate: 100.0%
```

## 🔧 Test Customization

### Adding New Tests

1. Create test file in the appropriate suite
2. Follow naming convention: `test_*.py`
3. Use fixtures from `conftest.py`
4. Add to `TEST_SUITES` in `run_tests.py`

### Custom Assertions

```python
def test_custom_functionality(authenticated_admin_page: Page, test_data_collector: TestDataCollector):
    start_time = time.time()
    test_name = "custom_test"

    try:
        # Your test logic here

        test_data_collector.add_result(
            test_name, "passed", time.time() - start_time,
            jobs_found=10, supabase_records=10, links_generated=5
        )

    except Exception as e:
        test_data_collector.add_result(
            test_name, "failed", time.time() - start_time,
            errors=[str(e)]
        )
        raise
```

## 🚨 Troubleshooting

### Common Issues

**Streamlit Server Not Starting**
```bash
# Check if port 8501 is in use
lsof -i :8501

# Start manually
streamlit run app.py --server.port=8501
```

**Authentication Failures**
- Verify admin credentials in `TEST_CONFIG`
- Check if user permissions allow testing features
- Ensure test user exists in system

**Environment Variables Missing**
```bash
# Check environment
python -c "import os; print([k for k in os.environ if 'OPENAI' in k or 'SUPABASE' in k])"

# Load from secrets
export $(cat .streamlit/secrets.toml | grep = | xargs)
```

**Test Timeouts**
- Increase timeout values in `conftest.py`
- Use `--skip-server-start` if server is slow
- Run individual suites instead of all tests

### Debug Mode

```bash
# Run with maximum debugging
pytest test_search_paths.py -v -s --tb=long --capture=no

# Show browser window (for visual debugging)
pytest test_search_paths.py --headed

# Slow down interactions
pytest test_search_paths.py --slowmo=1000
```

## 🎯 Best Practices

### Before Running Tests

1. **Environment Validation**: Ensure all APIs are functional
2. **Data Cleanup**: Clear any test data from previous runs
3. **Server Status**: Verify Streamlit app is working manually
4. **Resource Availability**: Ensure sufficient API quotas

### During Development

1. **Incremental Testing**: Run individual tests during development
2. **Mock Data**: Use test data that won't interfere with production
3. **Error Handling**: Implement proper cleanup in test failures
4. **Performance**: Monitor test execution times

### For CI/CD Integration

```yaml
# Example GitHub Actions workflow
name: FreeWorld Portal Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: playwright install
      - run: cd tests/playwright && python run_tests.py --skip-server-start
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
```

## 📞 Support

For issues with the testing suite:

1. Check the troubleshooting section above
2. Review test logs in `reports/` directory
3. Run individual tests to isolate issues
4. Verify environment configuration

The testing suite is designed to be comprehensive yet maintainable, providing confidence in system functionality before production deployments.