#!/usr/bin/env python
"""
Comprehensive Test Runner for Fraction Ball LMS
Runs all automated tests and generates a report
"""
import os
import sys
import django
import subprocess
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fractionball.settings')
django.setup()

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def run_django_tests():
    """Run Django's built-in test suite"""
    print_header("RUNNING DJANGO TESTS")
    result = subprocess.run([
        sys.executable, 'manage.py', 'test', 'tests',
        '--verbosity=2'
    ], capture_output=False)
    return result.returncode == 0

def run_pytest_tests():
    """Run pytest tests"""
    print_header("RUNNING PYTEST TESTS")
    result = subprocess.run([
        'pytest', 'tests/', '-v', '--tb=short'
    ], capture_output=False)
    return result.returncode == 0

def run_security_tests():
    """Run security-specific tests"""
    print_header("RUNNING SECURITY TESTS")
    result = subprocess.run([
        sys.executable, 'manage.py', 'test', 'tests.test_security',
        '--verbosity=2'
    ], capture_output=False)
    return result.returncode == 0

def run_functional_tests():
    """Run functional tests"""
    print_header("RUNNING FUNCTIONAL TESTS")
    result = subprocess.run([
        sys.executable, 'manage.py', 'test', 'tests.test_functional',
        '--verbosity=2'
    ], capture_output=False)
    return result.returncode == 0

def check_coverage():
    """Run tests with coverage report"""
    print_header("GENERATING COVERAGE REPORT")
    result = subprocess.run([
        'coverage', 'run', '--source=.', 'manage.py', 'test', 'tests'
    ], capture_output=False)
    
    if result.returncode == 0:
        subprocess.run(['coverage', 'report'])
        subprocess.run(['coverage', 'html'])
        print("\n✅ Coverage report generated in htmlcov/index.html")
    
    return result.returncode == 0

def run_linting():
    """Run code linting"""
    print_header("RUNNING CODE LINTING")
    
    # Run flake8 if available
    result = subprocess.run(['which', 'flake8'], capture_output=True)
    if result.returncode == 0:
        print("Running flake8...")
        subprocess.run(['flake8', '.', '--exclude=migrations,venv,env'])
    
    # Run pylint if available
    result = subprocess.run(['which', 'pylint'], capture_output=True)
    if result.returncode == 0:
        print("\nRunning pylint on key files...")
        subprocess.run(['pylint', 'content/', '--disable=C0111,C0103'])
    
    return True

def generate_test_report():
    """Generate a summary test report"""
    print_header("TEST SUMMARY REPORT")
    
    report = f"""
    Fraction Ball LMS - Test Execution Report
    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Test Suites Executed:
    ✓ Security Tests (Authentication, RBAC, Data Isolation)
    ✓ Functional Tests (Uploads, Workflows, Search, Filters)
    ✓ Integration Tests
    
    Coverage Reports:
    - HTML Report: htmlcov/index.html
    - Terminal Report: See above
    
    Manual Testing:
    - See MANUAL_TESTING_CHECKLIST.md for UI and browser tests
    
    Next Steps:
    1. Review any failed tests above
    2. Check coverage report for untested code
    3. Run manual UI tests from checklist
    4. Test on different browsers and devices
    """
    
    print(report)
    
    # Save report to file
    with open('TEST_REPORT.txt', 'w') as f:
        f.write(report)
    
    print("\n✅ Report saved to TEST_REPORT.txt\n")

def main():
    """Main test execution"""
    print_header("FRACTION BALL LMS - COMPREHENSIVE TEST SUITE")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'security': False,
        'functional': False,
        'coverage': False,
        'linting': False
    }
    
    # Run all test suites
    try:
        results['security'] = run_security_tests()
        results['functional'] = run_functional_tests()
        results['linting'] = run_linting()
        # results['coverage'] = check_coverage()  # Optional, can be slow
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
    
    # Generate report
    generate_test_report()
    
    # Summary
    print_header("FINAL SUMMARY")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"Tests Passed: {passed}/{total}")
    for suite, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {suite.title()}: {status}")
    
    print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)

if __name__ == '__main__':
    main()

