# Browser Extension Testing Platform

A comprehensive, professional-grade testing and quality assurance platform for browser extensions. Analyze, test, and validate extensions across multiple browsers before submission to app stores.

## 🎯 Overview

This platform automates the testing and validation of browser extensions, providing a **6-stage testing pipeline** that covers everything from static analysis to real browser automation. It helps developers catch bugs, security issues, and compatibility problems before submitting to Chrome Web Store, Microsoft Edge Add-ons, and Firefox Add-ons.

## ✨ Features

### 🔍 Comprehensive Analysis
- **6-Stage Testing Pipeline** - Automated orchestration from static checks to cross-browser compatibility
- **Code Linting** - JavaScript/HTML/CSS syntax and 20+ security pattern detection
- **Static Security Analysis** - Unsafe DOM manipulation, XSS vectors, eval usage detection
- **Malware Scanning** - Obfuscation detection, suspicious pattern identification with risk scoring
- **API Usage Analysis** - Detect used APIs, flag deprecated browser APIs
- **Dependency Scanning** - Identify bundled libraries and known vulnerabilities
- **Network Behavior Analysis** - Track external endpoints, detect tracking domains, flag unencrypted requests
- **Size Analysis** - Extension size breakdown by type with configurable thresholds

### 🏪 Store Compliance
- **Chrome Web Store Compliance** - Validate against Chrome requirements
- **Microsoft Edge Add-ons** - Edge store compatibility checking
- **Firefox Add-ons (AMO)** - Mozilla Add-on compatibility validation
- **Privacy Policy Scanning** - Data collection detection, policy validation, reachability checking

### 🌐 Multi-Browser Testing
- **Real Browser Automation** - Load test extensions in actual browsers
- **Cross-Browser Support** - Chrome, Firefox, Edge, and Opera
- **Per-Browser Testing** - Separate runtime and compatibility tests for each browser
- **Compatibility Matrix** - Identify browser-specific API compatibility issues

### 📊 Reporting
- **HTML Reports** - Beautiful formatted test reports
- **JSON Export** - Machine-readable detailed results
- **CSV Export** - Spreadsheet-compatible data
- **Markdown Reports** - Version-control friendly documentation
- **Multi-Format Support** - All formats generated from single test run

### 💻 User Interface
- **Command-Line Interface** - Full-featured CLI with Click framework
- **Graphical User Interface** - PyQt5 GUI for visual testing and batch operations
- **Batch Testing** - Run multiple extensions in parallel
- **Export Functionality** - Save results in preferred format

## 🚀 Quick Start

### Requirements
- **Python 3.11+**
- **Browsers**: Chrome, Firefox, Edge, or Opera (for automation testing)
- **Dependencies**: See `requirements.txt`

### Installation

1. **Clone/Download the project:**
```bash
cd "your-extension-tester-directory"
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Verify installation:**
```bash
python main.py --help
```

## 📖 Usage

### Command-Line Interface

#### Run Full 6-Stage Pipeline
```bash
python main.py pipeline ./path/to/extension [--browser chrome]
```
Runs all stages: validation, linting, store checks, browser testing, and compatibility analysis.

#### Extended Static Analysis
```bash
python main.py analyze ./path/to/extension
```
Performs comprehensive static analysis including size, dependencies, network behavior, malware patterns, and API usage.

#### Store Compliance Check
```bash
python main.py store-check ./path/to/extension
```
Checks compliance with Chrome Web Store, Edge Add-ons, and Firefox Add-ons requirements.

#### Single Extension Test
```bash
python main.py test ./path/to/extension --browser chrome
```
Tests extension load in specified browser.

#### Batch Testing
```bash
python main.py test_all ./extensions-directory
```
Tests all extensions in a directory.

#### API Compatibility Check
```bash
python main.py check_apis ./path/to/extension
```
Generates API compatibility matrix across browsers.

### Graphical User Interface

```bash
python main.py gui
```

The GUI provides:
- Visual extension loading and analysis
- Batch testing with progress tracking
- Real-time result viewing
- Report export to multiple formats

## 📊 Testing Pipeline Stages

### Stage 1: Static File Validation
- Checks manifest.json presence and validity
- Validates required fields and structure
- Detects extension type (content, popup, background)

### Stage 2: Manifest & Compliance Review
- Validates manifest version and permissions
- Checks store compliance (Chrome, Edge, Firefox)
- Scans privacy policy and data collection practices

### Stage 3: Code Analysis & Security
- Lints JavaScript/HTML/CSS for syntax errors
- Detects 20+ security vulnerabilities
- Analyzes extension size and file types
- Checks dependencies for known vulnerabilities
- Scans network behavior and tracking domains
- Scores malware risk (0-100)
- Identifies API usage and deprecated APIs

### Stage 4: Browser Load Testing
- Tests extension loading in each browser
- Validates manifest compatibility
- Checks background scripts execution
- Verifies content script injection

### Stage 5: Runtime Behavior Testing
- Tests popup functionality
- Validates content script behavior
- Checks background script activity
- Monitors for console errors

### Stage 6: Cross-Browser Compatibility
- Generates API compatibility matrix
- Identifies browser-specific issues
- Lists compatible browsers
- Flags unsupported API usage

## 📋 Manifest.json Support

The platform works with standard Chrome extension manifests:

**Manifest V2** (Legacy):
- Full support for legacy properties
- Deprecation warnings

**Manifest V3** (Current Standard):
- Full validation and testing
- Service Worker support
- Dynamic imports validation

Example structure tested:
```json
{
  "manifest_version": 3,
  "name": "My Extension",
  "version": "1.0.0",
  "permissions": ["storage", "activeTab"],
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content.js"]
  }],
  "background": {
    "service_worker": "background.js"
  }
}
```

## 🔒 Security Patterns Detected

The linter detects 20+ security issues:
- `eval()` usage and similar code execution
- XSS vulnerabilities (innerHTML, document.write)
- Unsafe DOM manipulation
- CSRF vulnerabilities
- Insecure permissions
- Missing security headers
- Vulnerable dependency versions
- Obfuscated code patterns
- Known malware signatures
- Unencrypted network requests
- Tracking domain connections

## 🌐 Supported Browsers

| Browser | Load Test | Runtime Test | API Check |
|---------|-----------|--------------|-----------|
| Chrome  | ✅        | ✅           | ✅        |
| Firefox | ✅        | ✅           | ✅        |
| Edge    | ✅        | ✅           | ✅        |
| Opera   | ✅        | ✅           | ✅        |

## 📦 Project Structure

```
extension-tester/
├── main.py                    # CLI entry point
├── validator.py              # Manifest validation
├── linter.py                 # Code linting and security analysis
├── browser_tester.py         # Browser automation
├── pipeline.py               # 6-stage orchestration
├── report_generator.py       # Multi-format reporting
├── gui.py                    # PyQt5 graphical interface
├── store_checker.py          # Store compliance checking
├── privacy_scanner.py        # Privacy policy analysis
├── size_analyzer.py          # Extension size analysis
├── dependency_checker.py     # Library vulnerability detection
├── network_analyzer.py       # Network behavior analysis
├── malware_scanner.py        # Suspicious pattern detection
├── api_usage_scanner.py      # API detection and deprecation
├── extension_tester.py       # Component testing
├── api_checker.py            # API compatibility matrix
├── security_scanner.py       # Security scoring
├── performance_metrics.py    # Performance analysis
├── bulk_runner.py            # Batch testing
├── summary.py                # Report summarization
└── README.md                 # This file
```

## 🔧 Configuration

### Environment Requirements
- Python 3.11+
- pip package manager
- One or more of: Chrome, Firefox, Edge, Opera
- 200+ MB disk space for dependencies

### Optional: WebDriver Setup
The platform auto-discovers browser drivers. For manual setup:

```bash
# Chrome/Chromium
python -m pip install chromedriver-binary

# Firefox
python -m pip install geckodriver-autoinstall

# Edge
# Download from: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
```

## 📊 Output Examples

### Console Output (Pipeline)
```
========================================
  EXTENSION TESTING PIPELINE REPORT
========================================

STAGE 1: STATIC FILE VALIDATION ✓
  Status: PASSED
  manifest.json found and valid

STAGE 2: MANIFEST & COMPLIANCE ✓
  Manifest validation: PASSED
  Store Compliance:
    Chrome Web Store: 95/100
    Microsoft Edge: 92/100
    Firefox Add-ons: 88/100

STAGE 3: CODE ANALYSIS & SECURITY ✓
  Linting: PASSED (0 errors, 2 warnings)
  Size: 245 KB
  Dependencies: 3 libraries identified

[... additional stages ...]

OVERALL RESULT: ✓ READY FOR SUBMISSION
```

### Report Files
All reports are generated in the extension directory:
- `report.html` - Interactive HTML report
- `report.json` - Detailed JSON data
- `report.csv` - Spreadsheet-compatible format
- `report.md` - Markdown documentation

## 🛠️ Troubleshooting

### "Browser not found" Error
Install missing browser or WebDriver:
```bash
# For Chrome
pip install chromedriver-binary

# For Firefox
pip install geckodriver-autoinstall
```

### "Manifest validation failed"
Ensure manifest.json is in the extension root and has required fields:
- `manifest_version` (2 or 3)
- `name`
- `version`

### "Module not found" Error
Reinstall dependencies:
```bash
pip install -r requirements.txt --force-reinstall
```

### GUI Not Launching
Ensure PyQt5 is installed:
```bash
pip install PyQt5 --upgrade
```

## 📈 Future Roadmap

### Planned Features
- **UI Automation Testing** - Playwright integration for interactive testing
- **Screenshot Testing** - Visual regression detection
- **Accessibility Testing** - ARIA/keyboard navigation validation
- **Cross-Version Testing** - Multiple browser version support
- **Watch Mode** - Auto-retest on file changes
- **Version Comparison** - Diff between extension versions
- **Video Recording** - Capture test execution videos
- **Extension Lifecycle Testing** - Install/update/uninstall workflows
- **Real User Scenarios** - Browse, shop, watch video simulations
- **Plugin Architecture** - Custom test plugins
- **Cloud Testing** - Multi-platform VM testing
- **Web Dashboard** - Browser-based test management UI

## 📝 License

See LICENSE file for details.

## 🤝 Support

For issues or feature requests, please refer to the project documentation or contact the development team.

## 📚 Additional Resources

- [Chrome Extension Documentation](https://developer.chrome.com/docs/extensions/)
- [Firefox WebExtensions API](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions)
- [Edge Extension Development](https://learn.microsoft.com/en-us/microsoft-edge/extensions-chromium/)
- [Selenium Documentation](https://www.selenium.dev/documentation/)

---

**Version**: 2.3  
**Last Updated**: February 2026  
**Status**: Production Ready

