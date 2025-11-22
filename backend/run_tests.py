# backend/run_tests.py
"""
Cross-platform test runner script.
Usage: python run_tests.py
"""
import subprocess
import sys
import os
from pathlib import Path


def main():
    print("🧪 Running Real-Time Chat AI Test Suite")
    print("=" * 50)
    print()
    
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Check if pytest is installed
    try:
        import pytest
    except ImportError:
        print("📦 Installing test dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-q",
            "pytest", "pytest-asyncio", "pytest-cov", "httpx", "pytest-mock", "faker"
        ])
    
    print("🚀 Running tests...")
    print()
    
    # Run pytest
    exit_code = pytest.main([
        "tests/",
        "-v",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=40",
        "-W", "ignore::DeprecationWarning"
    ])
    
    print()
    if exit_code == 0:
        print("✅ All tests passed!")
        print()
        print("📊 Coverage report generated: htmlcov/index.html")
        print("   Open in browser to view detailed coverage")
    else:
        print("❌ Some tests failed. Check output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()