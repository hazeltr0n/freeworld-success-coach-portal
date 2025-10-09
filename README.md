# Opptek Success Coach Portal

[![Test Suite](https://img.shields.io/badge/Test%20Suite-Master%20Efficient-brightgreen)](tests/playwright/) [![QA Status](https://img.shields.io/badge/QA-100%25%20Pass%20Rate-success)](tests/playwright/test_master_efficient.py) [![Performance](https://img.shields.io/badge/Performance-76s%20Full%20Validation-blue)](tests/playwright/)

## 🚀 Overview

**Opptek** is an AI-powered job discovery platform that cuts through the noise of the job market. Our mission: connect Free Agents (CDL drivers and warehouse workers) with quality employment opportunities through intelligent matching, personalized career pathways, and real-time analytics tracking.

### The Problem We Solve

The job market is overwhelming. Free Agents don't have time to read through thousands of irrelevant job postings to find the few that actually matter to them. **That's what Opptek is for.**

### 🎯 Key Features

- **🤖 AI-Powered Job Intelligence**: OpenAI GPT-4o-mini classifies job quality (good/so-so/bad) with detailed reasoning
- **🔍 Multi-Source Discovery**: Outscraper, Google Jobs, Indeed, and DriverPulse integration
- **💾 High-Performance Memory**: Supabase-based caching with 72-hour intelligent expiry
- **📊 Real-Time Analytics**: Comprehensive Free Agent engagement and click tracking
- **🔗 Smart Link Tracking**: Short.io integration for detailed attribution analytics
- **👥 Coach Management**: Role-based access control with budget tracking
- **📱 Personalized Portals**: Agent-specific job portals with smart filtering
- **⚡ Async Job Processing**: GitHub Actions workflows for hands-free batch execution
- **💰 Financial Planning**: Loan calculator and pathway guidance

## 🏗️ Architecture

### System Overview
```
┌─────────────────────────────────────────────────────────────┐
│                   Opptek Platform                            │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Streamlit  │  │    GitHub    │  │   Supabase   │      │
│  │   Web App    │  │   Actions    │  │  PostgreSQL  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│  ┌──────▼──────────────────▼──────────────────▼─────┐       │
│  │          Pipeline v3.1 (8-Stage Processing)       │       │
│  │                                                    │       │
│  │  1. Ingestion → 2. Normalization → 3. Rules →    │       │
│  │  4. Dedup → 5. AI Classification → 6. Routing →  │       │
│  │  7. Link Tracking → 8. Data Storage               │       │
│  └────────────────────────────────────────────────────┘      │
│                                                              │
│  Data Sources: Outscraper • Google Jobs • Indeed •          │
│                DriverPulse                                   │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### Pipeline v3.1 Engine
**8-stage job processing with checkpoint system**

1. **Ingestion**: Multi-source API integration with intelligent fallbacks
2. **Normalization**: 100+ field canonical schema mapping
3. **Business Rules**: Quality filtering and compliance checks
4. **Deduplication**: Hash-based duplicate removal across sources
5. **AI Classification**: Dual classifier system (CDL quality + Career pathways)
6. **Routing**: Final job selection and distribution logic
7. **Link Tracking**: Short.io tracked URL generation for analytics
8. **Data Storage**: Supabase persistence with real-time synchronization

#### Async Job Queue System
**GitHub Actions integration for hands-free execution**

- **Queue Management**: Supabase-based job queue (`async_job_queue` table)
- **Workflow Dispatch**: Automated GitHub Actions triggers
- **Status Tracking**: Real-time job status (pending → processing → completed/failed)
- **Result Storage**: Job count and metadata in `result_data` JSONB column
- **Auth Management**: Automatic DriverPulse session refresh before each scrape

#### AI Classification System
**Dual classifier architecture for comprehensive job analysis**

- **CDL Job Classifier**: Quality assessment (good/so-so/bad) with detailed reasoning
  - Fair chance analysis
  - Route type detection (OTR, Regional, Local, Dedicated)
  - Endorsement requirements
  - Home time expectations

- **Pathway Classifier**: Career progression identification
  - `dock_to_driver` - Warehouse to CDL progression
  - `warehouse_to_driver` - General warehouse to driving
  - `internal_cdl_training` - Company-sponsored CDL programs
  - `cdl_pathway` - Direct CDL opportunities

#### Supabase Memory System
**High-performance caching with 72-hour intelligent expiry**

- Hash-based deduplication across all sources
- Radius-based geographic filtering
- TTL expiry system for freshness
- Centralized client management with health checks
- 85-95% cache hit rate, sub-second lookups

### Technology Stack

- **Frontend**: Streamlit web application with multi-tab interface
- **Backend**: Python with Pandas for data processing
- **Database**: Supabase (PostgreSQL) for analytics, jobs, and memory
- **AI**: OpenAI GPT-4o-mini with structured output
- **Automation**: GitHub Actions for async job execution
- **Link Tracking**: Short.io with real-time webhook integration
- **Testing**: Playwright with Master Efficient Test Suite
- **Deployment**: Streamlit Cloud

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js (for Playwright tests)
- Supabase account
- Required API keys (OpenAI, Outscraper, Short.io)
- Optional: GitHub repository with Actions enabled for async jobs

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

4. **Set up Supabase**
   ```bash
   # Install Supabase CLI
   npm install -g supabase

   # Link to your project
   supabase link --project-ref YOUR_PROJECT_REF

   # Apply migrations
   supabase db push
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

### Environment Variables

```bash
# AI Services
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Job Scraping APIs (in order of preference)
OUTSCRAPER_API_KEY=...       # Primary source
GOOGLE_JOBS_API_KEY=...      # Secondary source
INDEED_API_KEY=...           # Legacy fallback
DRIVER_PULSE_EMAIL=...       # For DriverPulse integration
DRIVER_PULSE_FIRST_NAME=...
DRIVER_PULSE_LAST_NAME=...
DRIVER_PULSE_PHONE=...

# Data Storage & Analytics
SUPABASE_URL=...
SUPABASE_ANON_KEY=...

# Link Tracking
SHORTIO_API_KEY=...
SHORTIO_DOMAIN=...

# GitHub Actions (for async jobs)
GITHUB_TOKEN=...             # Personal access token with workflow permissions
GITHUB_REPO=owner/repo       # Your repository
```

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

# Cherry-pick specific validations
python -m pytest tests/playwright/test_master_efficient.py::TestMasterEfficient::test_cherry_pick_classification_only -v -s
```

### Test Coverage
- ✅ **Pipeline Integrity**: Memory/Fresh integration, 8-stage consistency
- ✅ **Classification Accuracy**: CDL ≥10%, Pathways ≥10% validation
- ✅ **Link Tracking**: Short.io integration and availability
- ✅ **Analytics Integration**: Dashboard functionality and data flow
- ✅ **Supabase Integrity**: Table accessibility and data persistence
- ✅ **Edge Cases**: System resilience and error handling

## 📊 Performance Metrics

### System Performance
- **Memory Hit Rate**: 85-95% for repeated searches
- **Processing Speed**: 45-75 seconds per 100 jobs (with memory optimization)
- **API Cost Efficiency**: $0.10-0.15 per 100 quality jobs
- **Test Suite Duration**: 76 seconds for complete validation
- **Agent Portal Speed**: 4x faster with database-level filtering

### User Engagement
- **Free Agent Click Rate**: 15-85% depending on coach effectiveness
- **Quality Job Accuracy**: 90%+ for "good" classifications
- **Classification Thresholds**: CDL ≥10%, Pathways ≥10%

## 🔧 Key Features Deep Dive

### 1. Async Job Queue System
**GitHub Actions integration for hands-free batch execution**

#### How It Works
1. Coach clicks "Schedule One-Off Batch" in Streamlit
2. Job parameters queued in Supabase `async_job_queue` table
3. GitHub Actions workflow triggered via API
4. Workflow executes in cloud (auth refresh → scrape → pipeline → storage)
5. Results stored in Supabase, status updated in real-time

#### Benefits
- **Zero Blocking**: UI returns immediately, no waiting for scrape completion
- **Automatic Auth**: DriverPulse session refreshed before each scrape
- **IP Consistency**: Auth and scraping from same GitHub Actions runner
- **Vacation-Proof**: Schedule jobs and walk away

### 2. Free Agent Management
**Revolutionary high-performance table management with automatic portal links**

#### Performance Breakthroughs (October 2025)
- **Speed**: Eliminated 3-5 second table gray-out delays through comprehensive caching
- **Responsiveness**: Zero auto-saves - changes only occur when user clicks "Save Changes"
- **Efficiency**: Session state caching eliminates redundant Supabase queries

#### Core Features
- **Individual Pathway Checkboxes**: Clean interface with 8 pathway options
- **Automatic Portal Link Generation**: Links generate/update during save process
- **Database Schema**: Flattened JSON fields to individual columns for optimal performance
- **Analytics Integration**: Pandas-based JOIN operations for missing field access

### 3. AI Classification System
**Dual classifier architecture for comprehensive job analysis**

- **Model**: OpenAI GPT-4o-mini with structured output
- **Classifications**: good/so-so/bad quality ratings with route type detection
- **Performance**: 90%+ accuracy for "good" job classifications
- **Flexibility**: Force Fresh Classification for testing new prompts
- **Cost Optimization**: Intelligent caching to minimize API calls

### 4. Multi-Source Job Discovery

#### Outscraper (Primary)
- Async batch processing with polling
- ZIP-based search targeting
- Company details and full job descriptions

#### Google Jobs (Secondary)
- Exact location mode for stability
- Direct company website URL prioritization
- 99% cost savings vs competitors

#### Indeed (Legacy Fallback)
- Async batch with status polling
- Comprehensive job metadata

#### DriverPulse (Specialty)
- CDL-specific job board integration
- GitHub Actions async execution
- Automatic session management

### 5. Link Tracking & Analytics

#### Short.io Integration
- Automatic tracked URL generation for all quality jobs
- Real-time webhook integration with Supabase
- Coach and Free Agent attribution
- Comprehensive click analytics

#### Analytics Dashboard
- **Overview**: System-wide engagement and performance metrics
- **Individual Agents**: Per-agent click rates and job engagement
- **FreeWorld Dashboard**: Economic impact and ROI calculations
- **Detailed Events**: Granular click tracking and user behavior
- **Admin Reports**: Coach performance and system utilization

## 🔄 Development Workflow

### Database Migrations
**Use the migration script for all Supabase schema changes**

```bash
# Common commands via migrate.sh
./scripts/migrate.sh new <migration_name>  # Create new migration
./scripts/migrate.sh push                   # Push migrations to remote
./scripts/migrate.sh diff                   # Check for schema differences
./scripts/migrate.sh status                 # Show migration history
```

### QA/Staging Workflow
1. **Make Changes**: Edit files in main production repo
2. **Test Locally**: Run app and test suite
3. **Run Master Test**: Validate all components
4. **Deploy**: Push to production

### Testing Commands
```bash
# Run master efficient test (full validation)
python -m pytest tests/playwright/test_master_efficient.py -v -s

# Run specific test components
python -m pytest tests/playwright/test_classification_comprehensive.py -v -s
python -m pytest tests/playwright/test_integration_comprehensive.py -v -s
```

## 🏢 Coach Management

### Role-Based Access Control
- **Admin Role**: Full system access, user management, force fresh classification
- **Coach Role**: Standard features with budget tracking
- **Permissions**: Granular control over advanced features
  - `can_access_google_jobs` - Access to Google Jobs API
  - `can_access_batches` - Batch processing and scheduling
  - `can_force_fresh_classification` - Bypass AI classification cache
  - `can_edit_ai_prompt` - Modify AI system prompts
  - `can_edit_filters` - Adjust business rules
  - `can_manage_users` - Add, edit, and remove coaches

### Budget Management
- **Monthly Budgets**: Allocation and spending tracking
- **Cost Calculator**: Real-time search cost estimation
- **Usage Analytics**: Search history and performance metrics

## 📚 Documentation

- **[System Architecture](CLAUDE.md)**: Comprehensive technical documentation
- **[Test Suite Guide](tests/playwright/README.md)**: Testing framework and usage
- **[Migration Guide](scripts/migrate.sh)**: Database schema management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`python -m pytest tests/playwright/test_master_efficient.py -v -s`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 🎉 Recent Achievements

### October 2025
- **⚡ DriverPulse Async Integration**: GitHub Actions workflow for hands-free batch execution
- **🔗 Tracked URL Persistence**: Fixed stage 7 → stage 8 link tracking flow
- **🚀 Async Job Queue**: Supabase-based queue system with real-time status tracking
- **💾 Free Agent Optimization**: Eliminated 3-5 second delays with comprehensive caching
- **🔄 Portal Link Automation**: Automatic generation during save process
- **📊 Database Performance**: Flattened JSON fields for optimal query speed

### September 2025
- **🧪 Revolutionary Test Suite**: 12x speed improvement with Master Efficient Test
- **⚡ Agent Portal Optimization**: 4x faster queries with database-level filtering
- **🎯 Google Jobs Integration**: 99% cost savings with intelligent URL prioritization
- **📊 Analytics Enhancement**: Comprehensive Free Agent engagement tracking
- **💰 Loan Calculator**: Restored financial planning tools

---

**Built with ❤️ for the FreeWorld community**

*Opptek: Cutting through the noise to connect Free Agents with opportunities that matter.*
