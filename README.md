# FreeWorld QA Portal

Standalone quality assurance and testing portal for the FreeWorld job processing system.

## 🧪 Features

- **QC Test Suite**: Comprehensive automated testing of job classification and filtering
- **Debug Tools**: Collection of debugging utilities for troubleshooting issues
- **Manual Testing**: Interactive tools for testing individual components
- **Test Analytics**: Historical test results and performance metrics
- **Job Inspector**: Detailed analysis of individual job postings
- **Performance Tests**: System speed and latency testing

## 🚀 Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. Run the QA portal:
   ```bash
   streamlit run app.py
   ```

## 🧪 QC Test Suite

The QC Test Suite includes:

- **LLM Determinism Test**: Ensures consistent AI classifications
- **Filter Accuracy Test**: Validates business rule filtering
- **Classification Accuracy Test**: Measures job quality assessment accuracy
- **End-to-End Quality Test**: Full pipeline testing with real data
- **Route Classification Test**: Validates route type detection
- **Memory Database Test**: Tests caching and retrieval performance

### Running Tests Programmatically

```python
from qc_test_suite import QCTestSuite

# Initialize test suite
qc = QCTestSuite()

# Run comprehensive testing
qc.run_comprehensive_qc('data/test_jobs.csv')
```

## 🐛 Debug Tools

Available debugging utilities:

- `debug_agent_tracking.py` - Agent tracking and portal issues
- `debug_coach_mismatch.py` - Coach assignment problems  
- `debug_job_urls.py` - Job URL and link issues
- `debug_link_flow.py` - Click tracking and analytics
- `debug_supabase_jobs.py` - Database connectivity issues
- `debug_real_agent.py` - Real agent data validation

## 📊 Test Data

Place test CSV files in the `data/` directory with the following columns:

- `title` - Job title
- `company` - Company name
- `location` - Job location
- `description` - Full job description
- `url` - Original job URL
- `expected_match` - Expected classification (good/so-so/bad)
- `expected_route` - Expected route type (Local/Regional/OTR)

## 🔧 Configuration

### Environment Variables

```bash
# AI Services
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Database
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=...

# Testing Configuration
QA_MODE=development
TEST_DATA_PATH=data/
RESULTS_PATH=results/
```

### Streamlit Configuration

The portal includes optimized Streamlit settings:
- File watcher disabled for cloud deployment stability
- Wide layout for better data visualization
- Custom theme matching FreeWorld branding

## 📁 Directory Structure

```
freeworld-qa-portal/
├── app.py                 # Main QA portal interface
├── qc_test_suite.py      # Comprehensive test suite
├── test_*.py             # Individual test scripts
├── debug_*.py            # Debugging utilities
├── tests/                # Automated test cases
├── data/                 # Test data files
├── results/              # Test results and reports
└── .streamlit/           # Streamlit configuration
```

## 🎯 Use Cases

### For QA Engineers
- Run automated test suites before releases
- Validate AI model performance
- Debug classification issues
- Generate test reports

### For Developers
- Test individual components during development
- Debug integration issues
- Performance profiling
- Data validation

### For Product Managers  
- View test analytics and trends
- Validate business rule accuracy
- Monitor system quality metrics
- Generate compliance reports

## 🔒 Security

- All API keys should be stored in environment variables
- Test data should not contain real PII
- Results can be exported for external analysis
- Access can be restricted through authentication

## 🤝 Contributing

1. Add new tests to the appropriate test files
2. Follow existing naming conventions
3. Include documentation for new debug tools
4. Update this README for new features

## 📈 Performance

The QA portal is optimized for:
- Fast test execution with parallel processing
- Efficient memory usage for large datasets
- Responsive UI even with complex test suites
- Reliable operation in cloud environments