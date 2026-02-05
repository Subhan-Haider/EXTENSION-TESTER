# Quick Start Guide

## Installation (First Time Only)

```bash
# Install Python dependencies
pip install -r requirements.txt
```

## Running the Application

### Option 1: GUI (Easiest)
```bash
python main.py gui
```
A window will open where you can:
1. Check which browsers to test (Chrome, Firefox, Edge, Opera)
2. Click "Test Single Extension" or "Test All Extensions in Folder"
3. Select your extension folder
4. View detailed results with errors and warnings

### Option 2: Command Line

**Test a single extension:**
```bash
python main.py test C:\path\to\my-extension

# For specific browser
python main.py test C:\path\to\my-extension --browser firefox
```

**Test multiple extensions:**
```bash
python main.py test-all C:\path\to\extensions\folder

# For specific browser
python main.py test-all C:\path\to\extensions\folder --browser chrome
```

**Bulk test a root folder (scan all extensions and save reports):**
```bash
python main.py bulk C:\path\to\extensions\root --browser all --report-dir reports

# Or use the standalone bulk runner
python bulk_main.py --folder C:\path\to\extensions\root --browsers chrome edge firefox --report-dir reports
```

**Runtime testing (Playwright):**
```bash
pip install playwright
playwright install

python main.py runtime-test C:\path\to\my-extension --browser chrome --url https://www.google.com
```

## What You'll Get

✓ **Summary Tab** - Overall statistics
✓ **Detailed Results Tab** - Per-extension breakdown with:
  - Extension name
  - Validation status (✓ Valid or ✗ Invalid)
  - Number of errors
  - Number of warnings
  - Compatible browsers

✓ **Full Report Tab** - Detailed findings:
  - Specific error messages
  - Warning descriptions
  - Compatible browser detection

## Common Issues

**Issue: Extension shows as invalid**
→ Check the "Full Report" tab for specific error messages and fix them

**Issue: "No extensions found"**
→ Make sure manifest.json exists in your extension folder

**Issue: GUI won't open**
→ Run `pip install PyQt5` to install the GUI library

**Issue: Firefox shows as incompatible**
→ Add "browser_specific_settings" to manifest.json for Firefox support

## Browser Detection

The tool automatically detects which browsers your extension supports based on:
- Manifest version (v2 or v3)
- Browser-specific settings
- Compatible APIs and features

## Tips

- **Manifest v3 is recommended** - Manifest v2 is deprecated
- **Test on actual browsers** - This tool validates structure, test functionality in real browsers
- **Minimize permissions** - Only request what you need
- **Avoid <all_urls>** - Use specific host patterns instead
- **Include all icon sizes** - Provides better user experience

---

Need help? Check the full README.md for detailed documentation!
