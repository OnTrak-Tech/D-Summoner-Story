#!/usr/bin/env python3
"""
Test runner script for the League of Legends Year in Review backend.
Runs unit tests, integration tests, and generates coverage reports.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ {description} failed with return code {result.returncode}")
        return False
    else:
        print(f"✅ {description} completed successfully")
        return True


def main():
    parser = argparse.ArgumentParser(description="Run backend tests")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    
    args = parser.parse_args()
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    print("🚀 Starting League of Legends Year in Review Backend Tests")
    print(f"Working directory: {os.getcwd()}")
    
    # Check if virtual environment is activated
    if not os.environ.get('VIRTUAL_ENV'):
        print("⚠️  Warning: No virtual environment detected. Consider activating one.")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      "Installing dependencies"):
        return 1
    
    # Prepare pytest arguments
    pytest_args = [sys.executable, "-m", "pytest"]
    
    if args.verbose:
        pytest_args.append("-v")
    else:
        pytest_args.append("-q")
    
    if args.coverage:
        pytest_args.extend([
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])
    
    if args.fast:
        pytest_args.extend(["-m", "not slow"])
    
    # Determine which tests to run
    test_paths = []
    
    if args.unit and not args.integration:
        test_paths.append("tests/unit/")
    elif args.integration and not args.unit:
        test_paths.append("tests/integration/")
    else:
        # Run all tests by default
        test_paths.extend(["tests/unit/", "tests/integration/"])
    
    pytest_args.extend(test_paths)
    
    # Run tests
    success = run_command(pytest_args, "Running tests")
    
    if args.coverage and success:
        print("\n📊 Coverage report generated in htmlcov/index.html")
    
    # Run linting
    print("\n🔍 Running code quality checks...")
    
    # Check if flake8 is available
    try:
        subprocess.run([sys.executable, "-m", "flake8", "--version"], 
                      capture_output=True, check=True)
        
        flake8_cmd = [
            sys.executable, "-m", "flake8", 
            "src/", "tests/",
            "--max-line-length=100",
            "--ignore=E203,W503"
        ]
        run_command(flake8_cmd, "Code style check (flake8)")
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  flake8 not available, skipping code style check")
    
    # Check if mypy is available
    try:
        subprocess.run([sys.executable, "-m", "mypy", "--version"], 
                      capture_output=True, check=True)
        
        mypy_cmd = [
            sys.executable, "-m", "mypy", 
            "src/",
            "--ignore-missing-imports"
        ]
        run_command(mypy_cmd, "Type checking (mypy)")
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  mypy not available, skipping type checking")
    
    # Summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 All tests completed successfully!")
        print("\nNext steps:")
        print("1. Review any warnings or coverage gaps")
        print("2. Deploy to AWS using: cd ../infrastructure/terraform && make deploy")
        print("3. Test the deployed API endpoints")
        return 0
    else:
        print("❌ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())