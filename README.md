# FreeWorld Success Coach Portal

[![Test Suite](https://img.shields.io/badge/Test%20Suite-Master%20Efficient-brightgreen)](tests/playwright/) [![QA Status](https://img.shields.io/badge/QA-100%25%20Pass%20Rate-success)](tests/playwright/test_master_efficient.py) [![Performance](https://img.shields.io/badge/Performance-76s%20Full%20Validation-blue)](tests/playwright/)

## 🚀 Overview

The **FreeWorld Success Coach Portal** is a comprehensive AI-powered job discovery and distribution platform designed to connect Free Agents with quality CDL driving opportunities through intelligent matching and career coach guidance.

### 🎯 Key Features

- **🤖 AI-Powered Job Classification**: OpenAI GPT-4o-mini for intelligent job quality assessment
- **🔍 Multi-Source Job Discovery**: Indeed API, Google Jobs API, and Outscraper integration
- **💾 High-Performance Memory System**: SQLite-based caching with sub-second lookups
- **📊 Real-Time Analytics**: Comprehensive Free Agent engagement tracking
- **🔗 Link Tracking**: Short.io integration for detailed click analytics
- **👥 Coach Management**: Role-based access control and budget tracking
- **📱 Agent Portals**: Personalized job portals for Free Agents
- **💰 Loan Calculator**: Financial planning tools for Free Agents

## 🏗️ Architecture

### Core Components
- **Pipeline v3**: 6-stage job processing pipeline with checkpoint system
- **Memory Database**: High-performance job caching and deduplication
- **AI Classifier**: Quality assessment with good/so-so/bad ratings
- **Analytics Dashboard**: Multi-tab interface with performance metrics
- **Agent Portal System**: Database-level filtering for 4x faster queries

### Technology Stack
- **Frontend**: Streamlit web application
- **Backend**: Python with Pandas for data processing
- **Database**: Supabase (PostgreSQL) for analytics, SQLite for memory
- **AI**: OpenAI GPT-4o-mini for job classification
- **Testing**: Playwright with revolutionary Master Efficient Test Suite
- **Deployment**: Streamlit Cloud

## 🧪 Revolutionary Test Suite

### Master Efficient Test Architecture
Our **breakthrough testing innovation** achieves **100% QA coverage in 76 seconds** (vs 15-20 minutes previously):

- **🎯 Master Test**: Single test validates entire system through DataFrame reuse
- **⚡ 12x Speed Improvement**: From "nightmare" to "beautiful" QA workflow
- **🔄 Smart Data Reuse**: One search → All validations
- **🍒 Cherry-Pick Options**: Targeted testing for specific components

```bash
# Run complete system validation (recommended)
python -m pytest tests/playwright/test_master_efficient.py::TestMasterEfficient::test_master_comprehensive_validation -v -s

# Performance benchmark
python -m pytest tests/playwright/test_master_efficient.py::TestMasterPerformance::test_master_performance_benchmark -v -s
```

### Test Coverage
- ✅ **Search Paths**: Memory/Fresh integration, pipeline consistency
- ✅ **Classification Accuracy**: CDL & Pathway performance validation
- ✅ **Link Tracking**: Short.io integration and system availability
- ✅ **Analytics Integration**: Dashboard functionality and data flow
- ✅ **Supabase Integrity**: Table accessibility and data persistence
- ✅ **Edge Cases**: System resilience and error handling

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js (for Playwright)
- Supabase account
- Required API keys (OpenAI, Indeed, Outscraper, Short.io)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/hazeltr0n/freeworld-success-coach-portal.git
   cd freeworld-success-coach-portal
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

3. **Configure environment**
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   # Edit secrets.toml with your API keys
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

### Environment Variables

```bash
# AI Services
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Job Scraping APIs
OUTSCRAPER_API_KEY=...
INDEED_API_KEY=...

# Data Storage & Analytics
AIRTABLE_API_KEY=...
SUPABASE_URL=...
SUPABASE_ANON_KEY=...

# Link Tracking
SHORTIO_API_KEY=...
SHORTIO_DOMAIN=...
```

## 📊 Performance Metrics

### System Performance
- **Memory Hit Rate**: 85-95% for repeated searches
- **Processing Speed**: 30-60 seconds per 100 jobs
- **API Cost Efficiency**: $0.10-0.15 per 100 quality jobs
- **Test Suite Duration**: 76 seconds for complete validation

### User Engagement
- **Free Agent Click Rate**: 15-85% depending on coach effectiveness
- **Quality Job Accuracy**: 90%+ for "good" classifications
- **Classification Thresholds**: CDL ≥10%, Pathways ≥10%

## 🔄 Development Workflow

### QA/Staging Workflow
1. **Make Changes**: Edit files in main production repo
2. **Copy to QA**: Transfer updated files to QA repo for testing
3. **Test in QA**: Push only to QA repo and validate in staging
4. **Production Deploy**: Only after QA approval, commit to main

### Testing Commands
```bash
# Run master efficient test (full validation)
python -m pytest tests/playwright/test_master_efficient.py -v -s

# Run specific test components
python -m pytest tests/playwright/test_classification_comprehensive.py -v -s
python -m pytest tests/playwright/test_integration_comprehensive.py -v -s

# Performance benchmark
python -m pytest tests/playwright/test_master_efficient.py::TestMasterPerformance -v -s
```

## 📈 Key Innovations

### 1. Master Efficient Test Suite
- **Revolutionary approach**: DataFrame reuse eliminates redundant API calls
- **Comprehensive coverage**: 70+ jobs tested across all scenarios
- **Reliability**: 100% pass rate with no flaky failures
- **Speed**: 12x improvement over traditional testing approaches

### 2. AI Classification System
- **Model**: OpenAI GPT-4o-mini with structured output
- **Classifications**: good/so-so/bad quality ratings with route type detection
- **Performance**: 90%+ accuracy for "good" job classifications
- **Flexibility**: Force Fresh Classification for testing new prompts

### 3. Memory Database System
- **Technology**: SQLite with optimized indexing
- **Performance**: Sub-second lookups for cached jobs
- **Features**: TTL expiry, hash-based deduplication, radius filtering
- **Efficiency**: 85-95% hit rate for repeated searches

### 4. Agent Portal System
- **Architecture**: Database-level filtering for 4x faster queries
- **Personalization**: Agent-specific filtering and job prioritization
- **Performance**: Extended 7-day lookback period for more options
- **Integration**: Seamless with Memory Only search pipeline

## 🏢 Coach Management

### Role-Based Access Control
- **Admin Role**: Full system access, user management, force fresh classification
- **Coach Role**: Restricted features with budget tracking
- **Permissions**: Granular control over advanced features

### Budget Management
- **Monthly Budgets**: Allocation and spending tracking
- **Cost Calculator**: Real-time search cost estimation
- **Usage Analytics**: Search history and performance metrics

## 📊 Analytics & Tracking

### Click Tracking Flow
1. **Short.io Link Generation**: Automated tracking URL creation
2. **Free Agent Engagement**: Click event capture
3. **Webhook Integration**: Real-time data to Supabase
4. **Analytics Dashboard**: Comprehensive reporting and insights

### Key Metrics
- **Total Engagements**: Across all Free Agents and coaches
- **Click Rates**: Performance by coach and job quality
- **Economic Impact**: ROI and cost per engagement estimates
- **Quality Distribution**: Job classification performance

## 🔧 Technical Details

### Database Schema
- **Canonical Job DataFrame**: Standardized schema across all sources
- **Supabase Analytics**: Real-time click tracking and aggregation
- **Memory Database**: High-performance SQLite caching layer

### Pipeline Stages
1. **Ingestion**: Multi-source API data collection
2. **Normalization**: Standardized data formatting
3. **Business Rules**: Quality filtering and validation
4. **Deduplication**: Hash-based duplicate removal
5. **AI Classification**: OpenAI quality assessment
6. **Routing Logic**: Final job selection and distribution

## 📚 Documentation

- **[System Architecture](CLAUDE.md)**: Comprehensive technical documentation
- **[Test Suite Guide](tests/playwright/README.md)**: Testing framework and usage
- **[API Documentation](docs/api.md)**: Endpoint reference and examples
- **[Deployment Guide](docs/deployment.md)**: Production deployment instructions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`python -m pytest tests/playwright/test_master_efficient.py -v -s`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎉 Recent Achievements

### September 22, 2025
- **🚀 Revolutionary Test Suite**: 12x speed improvement with Master Efficient Test
- **💰 Loan Calculator**: Restored financial planning tools
- **🔧 Infrastructure**: Supabase optimization and credential fixes

### September 4, 2025
- **⚡ Agent Portal Optimization**: 4x faster queries with database-level filtering
- **🎯 Google Jobs Integration**: 99% cost savings with intelligent URL prioritization
- **📊 Analytics Enhancement**: Comprehensive Free Agent engagement tracking

---

**Built with ❤️ for the FreeWorld community**

*Connecting Free Agents with quality opportunities through AI-powered matching and career coaching.*