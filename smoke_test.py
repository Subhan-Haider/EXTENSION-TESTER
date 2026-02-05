#!/usr/bin/env python3
"""
Quick Automated Smoke Tests
Tests core functionality without requiring Playwright
"""
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from exttester.validator import ExtensionValidator
from exttester.security_scanner import scan_extension
from exttester.scoring_engine import ScoringEngine
from exttester.vulnerability_scanner import VulnerabilityScanner


def create_test_extension():
    """Create a minimal test extension"""
    test_dir = tempfile.mkdtemp()
    ext_path = Path(test_dir) / "test-ext"
    ext_path.mkdir()
    
    # Create manifest
    manifest = {
        "manifest_version": 3,
        "name": "Smoke Test Extension",
        "version": "1.0.0",
        "description": "Test extension for automated testing",
        "permissions": ["storage"]
    }
    
    with open(ext_path / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    return test_dir, ext_path


def test_validator():
    """Test validator module"""
    print("▶ Testing Validator...")
    test_dir, ext_path = create_test_extension()
    
    try:
        validator = ExtensionValidator('chrome')
        is_valid, errors, warnings = validator.validate_extension(str(ext_path), 'chrome')
        
        assert isinstance(is_valid, bool), "Validator should return boolean"
        assert isinstance(errors, list), "Errors should be a list"
        assert isinstance(warnings, list), "Warnings should be a list"
        
        print("  ✅ Validator works correctly")
        return True
    except Exception as e:
        print(f"  ❌ Validator failed: {e}")
        return False
    finally:
        shutil.rmtree(test_dir)


def test_security_scanner():
    """Test security scanner"""
    print("▶ Testing Security Scanner...")
    test_dir, ext_path = create_test_extension()
    
    try:
        result = scan_extension(str(ext_path))
        
        assert 'findings' in result, "Should have findings"
        assert 'score' in result, "Should have score"
        assert 'permission_risk' in result, "Should have permission risk"
        assert isinstance(result['score'], int), "Score should be integer"
        assert 0 <= result['score'] <= 100, "Score should be 0-100"
        
        print(f"  ✅ Security Scanner works (Score: {result['score']})")
        return True
    except Exception as e:
        print(f"  ❌ Security Scanner failed: {e}")
        return False
    finally:
        shutil.rmtree(test_dir)


def test_scoring_engine():
    """Test scoring engine"""
    print("▶ Testing Scoring Engine...")
    
    try:
        # Mock data
        test_data = {
            'security': {'score': 85, 'findings': [], 'permission_findings': []},
            'performance': {'total_size_mb': 1.0, 'file_count': 10, 'largest_file_mb': 0.5},
            'meta': {'name': 'Test', 'version': '1.0.0', 'description': 'Test'},
            'browsers': {'chrome': {'valid': True, 'errors': [], 'warnings': []}}
        }
        
        engine = ScoringEngine()
        result = engine.calculate_final_score(test_data)
        
        assert 'final_score' in result, "Should have final score"
        assert 'grade' in result, "Should have grade"
        assert 'breakdown' in result, "Should have breakdown"
        assert 'recommendations' in result, "Should have recommendations"
        
        print(f"  ✅ Scoring Engine works (Score: {result['final_score']}, Grade: {result['grade']})")
        return True
    except Exception as e:
        print(f"  ❌ Scoring Engine failed: {e}")
        return False


def test_vulnerability_scanner():
    """Test vulnerability scanner"""
    print("▶ Testing Vulnerability Scanner...")
    test_dir, ext_path = create_test_extension()
    
    try:
        # Create package.json with vulnerable dependency
        package_json = {
            "name": "test",
            "dependencies": {
                "lodash": "4.17.0"  # Known vulnerable version
            }
        }
        
        with open(ext_path / "package.json", "w") as f:
            json.dump(package_json, f)
        
        scanner = VulnerabilityScanner()
        result = scanner.scan_extension(str(ext_path))
        
        assert 'vulnerabilities' in result, "Should have vulnerabilities"
        assert 'total_count' in result, "Should have total count"
        assert 'severity_counts' in result, "Should have severity counts"
        
        # Should detect the vulnerable lodash
        assert result['total_count'] > 0, "Should detect vulnerable lodash"
        
        print(f"  ✅ Vulnerability Scanner works (Found: {result['total_count']} CVEs)")
        return True
    except Exception as e:
        print(f"  ❌ Vulnerability Scanner failed: {e}")
        return False
    finally:
        shutil.rmtree(test_dir)


def test_playwright_available():
    """Check if Playwright is available"""
    print("▶ Checking Playwright...")
    
    try:
        from playwright.sync_api import sync_playwright
        print("  ✅ Playwright is installed and available")
        return True
    except ImportError:
        print("  ⚠️  Playwright not installed (optional for basic tests)")
        return False


def main():
    """Run all smoke tests"""
    print("=" * 70)
    print("  AUTOMATED SMOKE TESTS")
    print("=" * 70)
    print()
    
    tests = [
        ("Validator", test_validator),
        ("Security Scanner", test_security_scanner),
        ("Scoring Engine", test_scoring_engine),
        ("Vulnerability Scanner", test_vulnerability_scanner),
        ("Playwright Check", test_playwright_available),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"  ❌ {name} crashed: {e}")
            results[name] = False
        print()
    
    # Summary
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"\nTotal Tests:  {total}")
    print(f"✅ Passed:    {passed}")
    print(f"❌ Failed:    {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%\n")
    
    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status}  {test_name}")
    
    print("\n" + "=" * 70)
    
    if failed == 0:
        print("🎉 ALL CORE TESTS PASSED!")
        print("The extension testing tool is working correctly.")
    else:
        print(f"⚠️  {failed} test(s) failed.")
    
    print("=" * 70)
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
