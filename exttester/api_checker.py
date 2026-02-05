"""
API Compatibility Checker - Detect Chrome-only APIs and incompatibilities
"""
import re
from pathlib import Path
from typing import Dict, List, Tuple


class APICompatibilityChecker:
    """Check for API compatibility issues across browsers"""
    
    # APIs that are Chrome/Chromium only
    CHROME_ONLY_APIS = {
        'chrome.scripting': 'Scripting API - not in Firefox. Use content scripts instead.',
        'chrome.declarativeNetRequest': 'DNR API - not in Firefox. Use webRequest or use tabs API.',
        'chrome.sidePanel': 'Side panel - not in Firefox. No equivalent.',
        'chrome.sidePanel.setPanelBehavior': 'Side panel - Firefox alternative: sidebar',
        'chrome.readingList': 'Reading List API - Chrome only.',
        'chrome.tabGroups': 'Tab Groups - Chrome only.',
        'chrome.sessions': 'Sessions API - Chrome only.',
        'chrome.management.getPermissionWarningsById': 'Chrome only.',
        'chrome.autofill': 'Autofill API - Chrome only.',
    }
    
    # Firefox-only APIs
    FIREFOX_ONLY_APIS = {
        'browser.windows': 'Windows API - limited in Chrome. Use chrome.windows instead.',
        'browser.menus': 'Menus API - Chrome uses contextMenus instead.',
    }
    
    # APIs that work differently
    API_DIFFERENCES = {
        'chrome.storage.local': {
            'chrome': 'Fully supported',
            'firefox': 'Fully supported',
            'edge': 'Fully supported',
            'opera': 'Fully supported'
        },
        'chrome.alarms': {
            'chrome': 'Fully supported',
            'firefox': 'Not supported - use setInterval',
            'edge': 'Fully supported',
            'opera': 'Fully supported'
        },
        'chrome.offscreen': {
            'chrome': 'MV3 - Fully supported',
            'firefox': 'Not supported',
            'edge': 'MV3 - Fully supported',
            'opera': 'MV3 - Fully supported'
        },
    }
    
    # Suggested replacements
    REPLACEMENTS = {
        'chrome.scripting.executeScript': 'Use content scripts with event listeners',
        'chrome.declarativeNetRequest': 'Use webRequest or service worker message handling',
        'chrome.alarms': 'Use setTimeout / setInterval in service worker',
        'chrome.management': 'Not available - remove or make optional',
        'chrome.system': 'Not available in all browsers - check availability',
    }
    
    def __init__(self, extension_path: str):
        self.extension_path = Path(extension_path)
        self.issues = []
    
    def _read_file(self, filepath: Path) -> str:
        """Safely read file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except:
            return ""
    
    def check_api_usage(self, target_browser: str = 'firefox') -> List[str]:
        """Check for API incompatibilities"""
        issues = []
        
        # Find all JS files
        js_files = list(self.extension_path.rglob('*.js'))
        
        for js_file in js_files:
            content = self._read_file(js_file)
            
            # Check Chrome-only APIs
            for api, issue in self.CHROME_ONLY_APIS.items():
                if api in content:
                    # Check if it's just a comment
                    if not re.search(f'//.*{re.escape(api)}', content):
                        relative_path = js_file.relative_to(self.extension_path)
                        issues.append(f"❌ {api} used in {relative_path}")
                        issues.append(f"   └─ Issue: {issue}")
            
            # Check for deprecated webRequest (MV3)
            if 'chrome.webRequest' in content:
                manifest_path = self.extension_path / 'manifest.json'
                manifest_content = self._read_file(manifest_path)
                if '"manifest_version": 3' in manifest_content:
                    relative_path = js_file.relative_to(self.extension_path)
                    issues.append(f"❌ chrome.webRequest in MV3 {relative_path}")
                    issues.append(f"   └─ Solution: Use declarativeNetRequest instead")
            
            # Check for eval usage
            if re.search(r'\beval\s*\(', content):
                relative_path = js_file.relative_to(self.extension_path)
                issues.append(f"❌ eval() used in {relative_path}")
                issues.append(f"   └─ Issue: Not allowed in most browsers. Use Function() or dynamic imports.")
            
            # Check for unsafe DOM manipulation patterns
            if 'innerHTML' in content and 'setAttribute' not in content:
                if any(x in content for x in ['user_data', 'api_response', 'fetch']):
                    relative_path = js_file.relative_to(self.extension_path)
                    issues.append(f"⚠️ innerHTML with dynamic content in {relative_path}")
                    issues.append(f"   └─ Risk: XSS vulnerability. Use textContent or DOM methods.")
            
            # Check for unescaped regex in content scripts
            if 'match' in str(js_file) and '.match(' in content:
                if not 'RegExp' in content:
                    relative_path = js_file.relative_to(self.extension_path)
                    issues.append(f"⚠️ String.match() in {relative_path}")
                    issues.append(f"   └─ Tip: Use regex flags consistently")
        
        return issues
    
    def check_manifest_apis(self) -> List[str]:
        """Check manifest for API-related issues"""
        issues = []
        
        manifest_path = self.extension_path / 'manifest.json'
        if not manifest_path.exists():
            return issues
        
        content = self._read_file(manifest_path)
        
        # Check for deprecated permissions
        if '"webRequest"' in content:
            issues.append(f"⚠️ webRequest permission is deprecated")
            issues.append(f"   └─ Use: declarativeNetRequest (Chrome 88+, Edge 88+)")
        
        if '"webRequestBlocking"' in content:
            issues.append(f"❌ webRequestBlocking not allowed in MV3")
            issues.append(f"   └─ Use: declarativeNetRequest")
        
        if '"pageCapture"' in content:
            issues.append(f"⚠️ pageCapture is Chrome-specific")
            issues.append(f"   └─ Firefox: Not supported")
        
        return issues
    
    def generate_compatibility_report(self, target_browsers: list) -> Dict[str, list]:
        """Generate API compatibility report for multiple browsers"""
        report = {}
        
        for browser in target_browsers:
            issues = self.check_api_usage(browser)
            report[browser] = issues
        
        # Add manifest checks (applies to all)
        manifest_issues = self.check_manifest_apis()
        for browser in target_browsers:
            if browser not in report:
                report[browser] = []
            report[browser].extend(manifest_issues)
        
        return report
    
    def get_suggestions(self, api_name: str) -> str:
        """Get fix suggestions for an API"""
        if api_name in self.REPLACEMENTS:
            return f"Suggestion: {self.REPLACEMENTS[api_name]}"
        return "Check browser documentation for alternatives"
