# Usage Examples

## Example 1: Testing the Sample Extension

```bash
# Launch GUI
python main.py gui
```

**Steps:**
1. Click "Test Single Extension"
2. Navigate to `sample-extension` folder
3. Select it and click OK
4. Leave all browsers checked (Chrome, Firefox, Edge, Opera)
5. Click "Test Single Extension" button
6. View results

**Expected Result:**
- ✓ Status: VALID
- 0 Errors
- 0 Warnings (or minimal browser-specific warnings)
- Compatible with: Chrome, Edge, Opera

---

## Example 2: Testing Multiple Extensions

```bash
# Create a folder with your extensions
# extensions/
#   ├── extension-1/
#   │   └── manifest.json
#   ├── extension-2/
#   │   └── manifest.json
#   └── extension-3/
#       └── manifest.json

# Launch GUI
python main.py gui

# Click "Test All Extensions in Folder"
# Select the extensions folder
```

---

## Example 3: CLI Testing for Chrome Only

```bash
python main.py test "C:\Users\setup\OneDrive\Pictures\extenion tester\sample-extension" --browser chrome
```

**Output:**
```
======================================================================
Testing Extension: sample-extension
Browsers: Chrome
======================================================================

[*] Testing for Chrome:
[OK] Status: VALID
     Compatible with: Chrome, Edge, Opera

     No issues found!

======================================================================
```

---

## Example 4: Batch Testing Firefox Compatibility

```bash
python main.py test-all "C:\path\to\extensions" --browser firefox
```

**Sample Output:**
```
======================================================================
Testing All Extensions in: C:\path\to\extensions
Browsers: Firefox
======================================================================

Total Extensions: 3
Valid Extensions: 2
Total Errors: 1
Total Warnings: 2

──────────────────────────────────────────────────────────────────────

[OK] extension-1
      No issues found

[FAIL] extension-2
      ✗ Missing 'browser_specific_settings' for Firefox compatibility
      ⚠ Manifest v2 is deprecated - migrate to Manifest v3

[OK] extension-3
      No issues found

======================================================================
```

---

## Example 5: Testing Invalid Extension

Create a folder with a broken manifest.json:

```bash
# Create folder
mkdir my-broken-extension
cd my-broken-extension

# Create invalid manifest.json
echo { invalid json > manifest.json

# Test it
python main.py test .
```

**Output:**
```
======================================================================
Testing Extension: my-broken-extension
Browsers: Chrome, Firefox, Edge, Opera
======================================================================

[*] Testing for Chrome:
[FAIL] Status: INVALID
       ✗ Invalid JSON in manifest.json: Expecting value: line 1 column 1 (char 0)

[*] Testing for Firefox:
[FAIL] Status: INVALID
       ✗ Invalid JSON in manifest.json: Expecting value: line 1 column 1 (char 0)

...
```

---

## Example 6: GUI Workflow for Publishing

1. **Run the tester:**
   ```bash
   python main.py gui
   ```

2. **Test your extension:**
   - Select "Test Single Extension"
   - Choose your extension folder
   - Select all browsers
   - Click test button

3. **Review results:**
   - Look at Summary tab for overview
   - Check Detailed Results for any issues
   - Read Full Report for detailed explanations

4. **Fix errors:**
   - Open Full Report tab
   - Note each error and fix in your manifest.json
   - Re-run tests until all errors cleared

5. **Check compatibility:**
   - Compatible Browsers column shows supported browsers
   - Warnings in report help with best practices

6. **Publish:**
   - Once all errors are gone, extension is ready
   - Submit to Chrome Web Store, Firefox Add-ons, etc.

---

## Example 7: Detecting Browser Compatibility

Test an extension built for multiple browsers:

```bash
python main.py test my-webextension
```

**Output example:**
```
[*] Testing for Chrome:
[OK] Status: VALID
     Compatible with: Chrome, Edge, Opera

[*] Testing for Firefox:
[OK] Status: VALID
     Compatible with: Firefox
     ⚠ Firefox has limited Manifest v3 support - test thoroughly

[*] Testing for Edge:
[OK] Status: VALID
     Compatible with: Chrome, Edge, Opera

[*] Testing for Opera:
[OK] Status: VALID
     Compatible with: Chrome, Edge, Opera
```

---

## Example 8: Security Check Example

Extension with overly broad permissions:

```bash
python main.py test insecure-extension
```

**Output:**
```
[*] Testing for Chrome:
[FAIL] Status: INVALID
       ✗ '<all_urls>' in host_permissions is too broad - specify specific hosts
       ✗ Extension has many permissions (15) - consider reducing for security
       ⚠ 'unsafe-inline' in CSP can be a security risk - consider using nonces
```

---

## Example 9: Batch Report Generation

Generate a report for your extension portfolio:

```bash
# Save output to file
python main.py test-all "C:\my-extensions" >> report.txt

# View in text editor
notepad report.txt
```

---

## Example 10: Automated Testing Script

Create `test_extensions.bat`:

```batch
@echo off
echo Testing all browser extensions...
python main.py test-all "C:\my-extensions" --browser all
pause
```

Run it before publishing:
```bash
test_extensions.bat
```

---

## Tips for Different Scenarios

### For Development Teams
```bash
# Regular testing before commits
python main.py test . --browser chrome

# Full validation before release
python main.py test . --browser all
```

### For CI/CD Pipeline
```bash
# Exit with error code if validation fails
python main.py test . --browser all || exit 1
```

### For Quality Assurance
```bash
# Generate detailed report
python main.py test-all . > qa_report.txt
# Review report.txt in detail
```

### For Multi-Platform Releases
```bash
# Test Chrome version
python main.py test . --browser chrome

# Test Firefox version  
python main.py test . --browser firefox

# Test Edge version
python main.py test . --browser edge
```

---

## Summary of Commands

| Command | Use Case |
|---------|----------|
| `python main.py gui` | Interactive testing with GUI |
| `python main.py test path` | Test single extension |
| `python main.py test path --browser firefox` | Test for Firefox |
| `python main.py test-all path` | Test all extensions in folder |
| `python main.py test-all path --browser edge` | Test all for Edge |

---

Enjoy testing! Happy extension development! 🚀
