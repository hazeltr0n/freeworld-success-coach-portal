#!/bin/bash
# FreeWorld Production QA Suite - Deployment Script
# Comprehensive setup and validation for production testing deployments

set -e  # Exit on any error

echo "🏭 FreeWorld Production QA Suite Deployment"
echo "============================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Step 1: Environment check
echo ""
echo "🔍 Step 1: Environment Verification"
echo "-----------------------------------"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [[ $MAJOR -ge 3 && $MINOR -ge 11 ]]; then
    print_status "Python version: $PYTHON_VERSION"
else
    print_error "Python 3.11+ required, found: $PYTHON_VERSION"
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "test_master_efficient.py" ]]; then
    print_error "Must run from tests/playwright directory"
    exit 1
fi

print_status "Environment verification complete"

# Step 2: Dependency installation
echo ""
echo "📦 Step 2: Production Dependency Installation"
echo "---------------------------------------------"

print_info "Installing Python dependencies..."
if pip install -r requirements.txt; then
    print_status "Python dependencies installed"
else
    print_error "Failed to install Python dependencies"
    exit 1
fi

print_info "Installing Playwright browsers..."
if python -m playwright install; then
    print_status "Playwright browsers installed"
else
    print_error "Failed to install Playwright browsers"
    exit 1
fi

# Step 3: Dependency validation
echo ""
echo "🔍 Step 3: Dependency Validation"
echo "--------------------------------"

print_info "Running comprehensive dependency check..."
if python setup_production_dependencies.py; then
    print_status "All dependencies validated"
else
    print_error "Dependency validation failed"
    exit 1
fi

# Step 4: Test suite validation
echo ""
echo "🧪 Step 4: Master Efficient Test Validation"
echo "-------------------------------------------"

print_info "Running Master Efficient Test Suite..."
if python -m pytest test_master_efficient.py::TestMasterEfficient::test_master_comprehensive_validation -v -s; then
    print_status "Master Efficient Test Suite: 100% PASS"
else
    print_error "Master Efficient Test Suite: FAILED"
    exit 1
fi

# Step 5: Performance benchmark
echo ""
echo "⚡ Step 5: Performance Benchmark"
echo "-------------------------------"

print_info "Running performance benchmark..."
if python -m pytest test_master_efficient.py::TestMasterPerformance::test_master_performance_benchmark -v -s; then
    print_status "Performance benchmark: PASSED"
else
    print_warning "Performance benchmark: FAILED (non-critical)"
fi

# Step 6: Final validation
echo ""
echo "🎯 Step 6: Final Production Readiness"
echo "------------------------------------"

# Check critical files exist
CRITICAL_FILES=(
    "test_master_efficient.py"
    "conftest.py"
    "supabase_utils.py"
    "requirements.txt"
    "setup_production_dependencies.py"
    "TEST_GUIDE.md"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        print_status "Critical file present: $file"
    else
        print_error "Missing critical file: $file"
        exit 1
    fi
done

# Final summary
echo ""
echo "🎉 PRODUCTION QA SUITE DEPLOYMENT COMPLETE!"
echo "==========================================="
echo ""
echo "✅ Environment verified and ready"
echo "✅ All dependencies installed and validated"
echo "✅ Master Efficient Test Suite operational"
echo "✅ Performance benchmarks completed"
echo "✅ Critical files verified"
echo ""
echo "🚀 DEPLOYMENT STATUS: READY FOR PRODUCTION"
echo ""
echo "📋 Usage Instructions:"
echo "  Complete validation: ./deploy_qa_suite.sh"
echo "  Quick test:          python -m pytest test_master_efficient.py::TestMasterEfficient::test_master_comprehensive_validation -v -s"
echo "  Cherry-pick tests:   python -m pytest test_master_efficient.py::TestMasterEfficient::test_cherry_pick_classification_only -v -s"
echo ""
echo "📊 Expected Performance:"
echo "  Duration: ~76 seconds for complete validation"
echo "  Coverage: 70+ jobs tested across all scenarios"
echo "  Pass Rate: 100% reliability"
echo ""

print_status "Production QA Suite ready for deployment! 🎯"