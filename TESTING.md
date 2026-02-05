# Automated Testing Guide

## 🧪 Test Suite Overview

The Extension Tester includes a comprehensive automated test suite that validates all core functionality, including **real browser automation**.

### Test Types

1. **Unit Tests** - Test individual modules
2. **Integration Tests** - Test complete pipeline with real browser
3. **Smoke Tests** - Quick validation of core features
4. **CI/CD Tests** - Automated tests on every push

---

## 🚀 Quick Start

### Run All Tests (Recommended)
```bash
python smoke_test.py
```

This runs quick smoke tests that validate:
- ✅ Validator module
- ✅ Security scanner
- ✅ Scoring engine
- ✅ Vulnerability scanner
- ✅ Playwright availability

**Expected Output:**
```
======================================================================
  AUTOMATED SMOKE TESTS
======================================================================

▶ Testing Validator...
  ✅ Validator works correctly

▶ Testing Security Scanner...
  ✅ Security Scanner works (Score: 100)

▶ Testing Scoring Engine...
  ✅ Scoring Engine works (Score: 88.5, Grade: B+)

▶ Testing Vulnerability Scanner...
  ✅ Vulnerability Scanner works (Found: 1 CVEs)

▶ Checking Playwright...
  ✅ Playwright is installed and available

======================================================================
  SUMMARY
======================================================================

Total Tests:  5
✅ Passed:    5
❌ Failed:    0
Success Rate: 100.0%

🎉 ALL CORE TESTS PASSED!
```

---

## 🔬 Detailed Test Commands

### 1. Unit Tests Only
```bash
python -m unittest discover tests -v
```

Tests individual modules:
- `test_validator.py` - Extension validator
- `test_scanner.py` - Security scanner

### 2. Integration Tests (Real Browser)
```bash
python tests/test_integration.py
```

**What it tests:**
- ✅ Creates a real test extension
- ✅ Loads it in Chromium using Playwright
- ✅ Tests popup functionality
- ✅ Tests service worker
- ✅ Runs complete pipeline
- ✅ Validates scoring engine
- ✅ Tests vulnerability detection

**Requirements:**
- Playwright must be installed
- Chromium browser installed

### 3. Full Test Runner
```bash
python run_tests.py
```

Runs comprehensive test suite including:
- Unit tests
- Integration tests
- CLI functionality tests
- Module import tests
- Playwright availability check

---

## 📦 Test Setup

### Install Test Dependencies
```bash
pip install -r requirements.txt
pip install playwright pytest
python -m playwright install chromium
```

### Verify Installation
```bash
python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright ready')"
```

---

## 🤖 CI/CD Automated Testing

Every push to `main` automatically triggers:

1. **Unit Tests** - All module tests
2. **Integration Tests** - Real browser tests
3. **CLI Tests** - Command validation
4. **Linting** - Code quality checks

**View Results:**
- GitHub Actions: `https://github.com/Subhan-Haider/EXTENSION-TESTER/actions`

---

## 📊 Test Coverage

| Module | Unit Tests | Integration Tests | Coverage |
|--------|-----------|-------------------|----------|
| Validator | ✅ | ✅ | High |
| Security Scanner | ✅ | ✅ | High |
| Scoring Engine | ✅ | ✅ | High |
| Vulnerability Scanner | ✅ | ✅ | High |
| Playwright Engine | ⚠️ | ✅ | Medium |
| Pipeline | ⚠️ | ✅ | Medium |
| GUI | ❌ | ❌ | Low |

**Legend:**
- ✅ Comprehensive tests
- ⚠️ Partial coverage
- ❌ Needs tests

---

## 🐛 Troubleshooting

### Playwright Not Found
```bash
pip install playwright
python -m playwright install chromium
```

### Tests Timeout
Increase timeout in test files or run with:
```bash
python tests/test_integration.py --timeout=120
```

### Permission Errors
On Linux/Mac:
```bash
chmod +x smoke_test.py run_tests.py
```

---

## 📝 Writing New Tests

### Example Unit Test
```python
import unittest
from exttester.validator import ExtensionValidator

class TestMyFeature(unittest.TestCase):
    def test_something(self):
        validator = ExtensionValidator('chrome')
        self.assertIsNotNone(validator)

if __name__ == '__main__':
    unittest.main()
```

### Example Integration Test
```python
from exttester.pipeline import TestingPipeline

def test_full_pipeline():
    pipeline = TestingPipeline('./my-extension', browsers=['chrome'])
    results = pipeline.run()
    assert results['summary']['success'] == True
```

---

## ✅ Test Checklist

Before committing code:

- [ ] Run `python smoke_test.py` - All pass
- [ ] Run `python -m unittest discover tests` - All pass
- [ ] Run `python tests/test_integration.py` - All pass
- [ ] Check GitHub Actions - Build passes

---

## 🎯 Test Goals

**Current Coverage:** ~60%  
**Target Coverage:** 80%+

**Priority Areas:**
1. ✅ Core modules (Done)
2. ✅ Real browser automation (Done)
3. ⚠️ GUI testing (In Progress)
4. ❌ Accessibility testing (Planned)
5. ❌ Performance testing (Planned)

---

## 📚 Resources

- [unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [Playwright Python](https://playwright.dev/python/)
- [GitHub Actions](https://docs.github.com/en/actions)

---

**Last Updated:** 2026-02-05  
**Test Suite Version:** 1.0
