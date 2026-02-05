#!/usr/bin/env python3
"""
Automated Test Runner
Runs all tests and generates a comprehensive report
"""
import subprocess
import sys
import time
from pathlib import Path


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"▶ {description}...")
    start = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        duration = time.time() - start
        
        if result.returncode == 0:
            print(f"  ✅ PASSED ({duration:.2f}s)")
            return True
        else:
            print(f"  ❌ FAILED ({duration:.2f}s)")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ⏱️ TIMEOUT (>60s)")
        return False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False


def main():
    """Run all automated tests"""
    print_header("AUTOMATED TEST SUITE")
    
    results = {}
    
    # 1. Unit Tests
    print_header("1. UNIT TESTS")
    results['unit_validator'] = run_command(
        "python -m unittest tests.test_validator",
        "Testing Validator Module"
    )
    results['unit_scanner'] = run_command(
        "python -m unittest tests.test_scanner",
        "Testing Security Scanner Module"
    )
    
    # 2. Integration Tests
    print_header("2. INTEGRATION TESTS (Real Browser)")
    results['integration'] = run_command(
        "python tests/test_integration.py",
        "End-to-End Pipeline Tests"
    )
    
    # 3. CLI Tests
    print_header("3. CLI FUNCTIONALITY")
    results['cli_help'] = run_command(
        "python main.py --help",
        "CLI Help Command"
    )
    results['cli_version'] = run_command(
        "python main.py --version",
        "CLI Version Command"
    )
    
    # 4. Module Import Tests
    print_header("4. MODULE IMPORTS")
    results['import_pipeline'] = run_command(
        "python -c \"from exttester.pipeline import TestingPipeline; print('OK')\"",
        "Import Pipeline Module"
    )
    results['import_scoring'] = run_command(
        "python -c \"from exttester.scoring_engine import ScoringEngine; print('OK')\"",
        "Import Scoring Engine"
    )
    results['import_vuln'] = run_command(
        "python -c \"from exttester.vulnerability_scanner import VulnerabilityScanner; print('OK')\"",
        "Import Vulnerability Scanner"
    )
    
    # 5. Playwright Check
    print_header("5. PLAYWRIGHT AVAILABILITY")
    results['playwright'] = run_command(
        "python -c \"from playwright.sync_api import sync_playwright; print('Playwright installed')\"",
        "Check Playwright Installation"
    )
    
    # Generate Summary
    print_header("TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"Total Tests:  {total}")
    print(f"✅ Passed:    {passed}")
    print(f"❌ Failed:    {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    print("\nDetailed Results:")
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}  {test_name}")
    
    print("\n" + "=" * 70)
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! System is working correctly.")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
