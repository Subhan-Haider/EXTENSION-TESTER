# Advanced Features Guide

## 🆕 New Features

Your browser extension tester now has **enterprise-level testing capabilities**:

### 1. 🧪 Advanced Extension Testing
Test the actual extension components:
- **Popup Testing** - Verify popup.html loads, check for missing assets
- **Content Script Testing** - Check injection, find DOM timing issues
- **Background Script Testing** - Verify service worker/background page
- **Permission Analysis** - Flag dangerous or unused permissions

### 2. 🔍 API Compatibility Checker
Detect Chrome-only APIs that will break in Firefox/Edge:
- `chrome.scripting` ❌ Firefox
- `chrome.declarativeNetRequest` ❌ Firefox
- `chrome.sidePanel` ❌ Firefox
- `chrome.alarms` ❌ Firefox (use setInterval)
- And 15+ more...

### 3. 📊 Multi-Format Reports
Export test results in:
- **HTML** - Beautiful dashboard with styling
- **JSON** - Machine-readable format
- **CSV** - Import to Excel
- **Markdown** - GitHub-friendly format

---

## 🚀 New Commands

### Advanced Testing
```bash
python main.py advanced-test C:\path\to\extension
python main.py advanced-test C:\path\to\extension --format json
python main.py advanced-test C:\path\to\extension --format html
```

### API Compatibility Check
```bash
python main.py check-apis C:\path\to\extension
python main.py check-apis C:\path\to\extension --browser firefox
python main.py check-apis C:\path\to\extension --browser all
```

---

## 📋 What Gets Tested

### Popup Testing
- ✓ Popup file exists
- ✓ All referenced CSS/JS load
- ✓ No inline scripts (MV3 safety)
- ✓ Proper asset paths

### Content Scripts
- ✓ All files exist
- ✓ No eval() usage
- ✓ Correct run_at timing
- ✓ Safe match patterns (not *://*/* )
- ✓ DOM access matches run timing

### Background/Service Worker
- ✓ Service worker exists (MV3)
- ✓ No eval() usage
- ✓ Proper async handling
- ✓ MV3 compliance

### Permissions
- ✓ No overly broad patterns
- ✓ No deprecated permissions
- ✓ Browser-specific warnings
- ✓ Required vs optional check

### API Compatibility
- ✗ Chrome-only APIs detected
- ✗ Deprecated APIs flagged
- ✓ Fixes suggested

---

## 📊 Report Types

### HTML Report
Professional-looking report with:
- Color-coded status
- Summary statistics
- Detailed issue breakdown
- Browser compatibility matrix
- Clickable navigation

**Open in browser** - `test_report.html`

### JSON Report
Machine-readable format:
```json
{
  "metadata": {
    "timestamp": "2026-02-05 10:30:00",
    "extension": "my-extension"
  },
  "summary": {
    "total_tests": 5,
    "passed": 4,
    "failed": 1
  },
  "results": { ... }
}
```

### CSV Report
Import to Excel/Sheets:
```
Test,Status,Errors,Warnings,Details
popup,PASS,0,1,No issues
content_scripts,FAIL,2,1,Missing files
```

### Markdown Report
GitHub-friendly:
```markdown
# Extension Test Report
**Generated:** 2026-02-05

## Summary
| Metric | Value |
|--------|-------|
| Tests  | 5     |
```

---

## 🔎 Example Outputs

### API Compatibility Issue
```
❌ chrome.scripting used in background.js
   └─ Issue: Scripting API - not in Firefox. Use content scripts instead.

❌ chrome.declarativeNetRequest used in background.js
   └─ Solution: Use declarativeNetRequest (Chrome 88+, Edge 88+)
```

### Popup Issue
```
❌ Popup asset not found: assets/icon.png
   └─ Location: popup.html references missing file
```

### Content Script Issue
```
⚠️ Content script runs at document_start but accesses DOM in content.js
   └─ Risk: DOM not ready yet. Use document_end or add ready check.
```

### Permission Issue
```
❌ Overly broad host permission: <all_urls>
   └─ Specify exact hosts instead, e.g., "https://example.com/*"

⚠️ webRequest permission is deprecated
   └─ Use: declarativeNetRequest (Chrome 88+, Edge 88+)
```

---

## 💡 Usage Examples

### Example 1: Basic Advanced Test
```bash
python main.py advanced-test ./my-extension
```

Output:
```
========================================================================
Advanced Testing: my-extension
========================================================================

📋 Extension Component Tests:
  POPUP: ✓ PASS
  CONTENT_SCRIPTS: ✗ FAIL
    ❌ Content script not found: scripts/inject.js
  BACKGROUND: ✓ PASS
  PERMISSIONS: ⚠ WARN
    ⚠️ Overly broad host permission

🔍 API Compatibility Check:
  ❌ chrome.scripting used in background.js
     └─ Issue: Not in Firefox

📄 Generating HTML Report...
  ✓ Report saved to: ./my-extension/test_report.html
```

### Example 2: Firefox Compatibility Check
```bash
python main.py check-apis ./my-extension --browser firefox
```

Output:
```
========================================================================
API Compatibility Check: my-extension
Browsers: Firefox
========================================================================

FIREFOX:
  ❌ chrome.scripting used in background.js
  ❌ chrome.declarativeNetRequest used in background.js
  ⚠️ webRequest permission is deprecated
```

### Example 3: JSON Report for CI/CD
```bash
python main.py advanced-test ./my-extension --format json
```

Creates `test_report.json` for:
- Parsing in CI pipelines
- Automated error detection
- Database storage
- Dashboard integration

### Example 4: Markdown Report for GitHub
```bash
python main.py advanced-test ./my-extension --format markdown
```

Creates `test_report.md` for:
- Commit comments
- Pull request reviews
- Release notes
- Documentation

---

## 🎯 Best Practices

### Before Publishing
1. Run basic validation:
   ```bash
   python main.py test ./my-extension --browser all
   ```

2. Run advanced tests:
   ```bash
   python main.py advanced-test ./my-extension --format html
   ```

3. Check API compatibility:
   ```bash
   python main.py check-apis ./my-extension
   ```

4. Review HTML report in browser

5. Fix all errors, address warnings

### For Teams
1. Save JSON report in Git:
   ```bash
   python main.py advanced-test ./my-extension --format json
   ```

2. Parse results in CI pipeline:
   ```python
   import json
   with open('test_report.json') as f:
       results = json.load(f)
       if results['summary']['failed'] > 0:
           exit(1)  # Fail build
   ```

3. Display in dashboard
4. Track improvements over time

### For Documentation
1. Generate Markdown report:
   ```bash
   python main.py advanced-test ./my-extension --format markdown
   ```

2. Include in README.md
3. Share with team
4. Reference in release notes

---

## 🐛 Debugging

### Check specific component
```bash
python main.py advanced-test ./my-extension --format json | grep "popup"
```

### Firefox-only issues
```bash
python main.py check-apis ./my-extension --browser firefox
```

### Compare browsers
```bash
for browser in chrome firefox edge; do
  python main.py check-apis ./my-extension --browser $browser > report_$browser.txt
done
```

---

## 📈 Integration Examples

### GitHub Actions
```yaml
- name: Test Extension
  run: |
    python main.py advanced-test ./extension --format json
    python -c "
      import json
      with open('test_report.json') as f:
        if json.load(f)['summary']['failed'] > 0:
          exit(1)
    "
```

### Pre-commit Hook
```bash
#!/bin/bash
python main.py test . --browser all || exit 1
python main.py advanced-test . || exit 1
```

### Release Checklist
```bash
#!/bin/bash
echo "Running comprehensive tests..."
python main.py test . --browser all
python main.py advanced-test . --format html
python main.py check-apis .
echo "✓ Ready to release!"
```

---

## 🎁 What's Next?

These features make your tool **enterprise-grade**:

✅ Comprehensive testing  
✅ Multi-format reporting  
✅ API compatibility detection  
✅ CI/CD ready  
✅ Team-friendly  

**You now have everything you need to catch extension bugs before users do!** 🚀
