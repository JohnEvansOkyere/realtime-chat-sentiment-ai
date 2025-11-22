# backend/run_tests.sh
#!/bin/bash

echo "🧪 Running Real-Time Chat AI Test Suite"
echo "========================================"
echo ""

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing test dependencies..."
pip install -q pytest pytest-asyncio pytest-cov httpx pytest-mock faker

# Run tests with coverage
echo ""
echo "🚀 Running tests..."
echo ""

pytest tests/ \
    -v \
    --cov=app \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-fail-under=70 \
    -W ignore::DeprecationWarning

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
    echo ""
    echo "📊 Coverage report generated: htmlcov/index.html"
    echo "   Open with: open htmlcov/index.html (Mac) or xdg-open htmlcov/index.html (Linux)"
else
    echo ""
    echo "❌ Some tests failed. Check output above."
    exit 1
fi