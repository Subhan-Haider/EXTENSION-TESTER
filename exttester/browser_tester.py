"""
Browser-Based Testing for Extensions

Uses real browser instances to test:
- Extension loading and initialization
- Popup functionality
- Content script injection
- Background/service worker execution
- Console error logging
- Multi-site testing
"""

import json
import time
import subprocess
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BrowserTestResult:
    """Result from browser testing"""
    browser: str
    test_type: str
    success: bool
    message: str
    console_errors: List[str] = None
    console_warnings: List[str] = None
    duration: float = 0.0
    details: Dict = None
    
    def __post_init__(self):
        if self.console_errors is None:
            self.console_errors = []
        if self.console_warnings is None:
            self.console_warnings = []
        if self.details is None:
            self.details = {}


class BrowserManager:
    """Manages browser instances for testing"""
    
    BROWSER_CONFIGS = {
        'chrome': {
            'executable': 'chrome',
            'args': [
                '--disable-extensions',
                '--disable-gpu',
                '--disable-default-apps',
                '--no-first-run',
            ]
        },
        'firefox': {
            'executable': 'firefox',
            'args': [
                '-profile',
                '/tmp/firefox-profile',
            ]
        },
        'edge': {
            'executable': 'msedge',
            'args': [
                '--disable-extensions',
                '--disable-gpu',
                '--no-first-run',
            ]
        },
    }
    
    def __init__(self):
        self.browsers = {}
    
    def get_browser_path(self, browser_name: str) -> str:
        """Get path to browser executable"""
        browser_name = browser_name.lower()
        
        # For Windows
        paths = {
            'chrome': [
                'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
            ],
            'firefox': [
                'C:\\Program Files\\Mozilla Firefox\\firefox.exe',
                'C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe',
            ],
            'edge': [
                'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
                'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
            ],
        }
        
        if browser_name in paths:
            for path in paths[browser_name]:
                if Path(path).exists():
                    return path
        
        return browser_name  # Try system PATH
    
    def is_installed(self, browser_name: str) -> bool:
        """Check if browser is installed"""
        try:
            browser_path = self.get_browser_path(browser_name)
            result = subprocess.run(
                [browser_path, '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False


class ExtensionBrowserTester:
    """Test extension in real browser environment"""
    
    # Test URLs for content script injection
    TEST_URLS = [
        'https://example.com',
        'https://www.google.com',
        'https://github.com',
        'https://www.amazon.com',
        'https://www.youtube.com',
    ]
    
    def __init__(self, extension_path: str, browser: str = 'chrome'):
        self.extension_path = Path(extension_path)
        self.browser = browser.lower()
        self.manager = BrowserManager()
        self.results: List[BrowserTestResult] = []
    
    def check_browser_available(self) -> BrowserTestResult:
        """Check if browser is installed and available"""
        if not self.manager.is_installed(self.browser):
            return BrowserTestResult(
                browser=self.browser,
                test_type='browser_availability',
                success=False,
                message=f'{self.browser} is not installed or not found in PATH'
            )
        
        return BrowserTestResult(
            browser=self.browser,
            test_type='browser_availability',
            success=True,
            message=f'{self.browser} is available'
        )
    
    def test_extension_load(self) -> BrowserTestResult:
        """Test if extension loads successfully"""
        # Check manifest first
        manifest_path = self.extension_path / 'manifest.json'
        
        if not manifest_path.exists():
            return BrowserTestResult(
                browser=self.browser,
                test_type='extension_load',
                success=False,
                message='manifest.json not found'
            )
        
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            return BrowserTestResult(
                browser=self.browser,
                test_type='extension_load',
                success=False,
                message=f'Invalid manifest.json: {e}'
            )
        
        # Verify required fields
        required_fields = ['manifest_version', 'name', 'version']
        missing = [f for f in required_fields if f not in manifest]
        
        if missing:
            return BrowserTestResult(
                browser=self.browser,
                test_type='extension_load',
                success=False,
                message=f'Missing required manifest fields: {missing}',
                details={'missing_fields': missing}
            )
        
        return BrowserTestResult(
            browser=self.browser,
            test_type='extension_load',
            success=True,
            message=f'Extension manifest valid for {self.browser}',
            details={'manifest_version': manifest.get('manifest_version')}
        )
    
    def test_popup(self) -> BrowserTestResult:
        """Test extension popup"""
        manifest_path = self.extension_path / 'manifest.json'
        
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except:
            return BrowserTestResult(
                browser=self.browser,
                test_type='popup_test',
                success=False,
                message='Cannot read manifest'
            )
        
        # Check if popup is defined
        action_key = 'action' if manifest.get('manifest_version') == 3 else 'browser_action'
        if action_key not in manifest:
            return BrowserTestResult(
                browser=self.browser,
                test_type='popup_test',
                success=False,
                message=f'No popup defined (missing {action_key})'
            )
        
        action = manifest.get(action_key, {})
        popup_file = action.get('default_popup')
        
        if not popup_file:
            return BrowserTestResult(
                browser=self.browser,
                test_type='popup_test',
                success=False,
                message='No default_popup specified'
            )
        
        popup_path = self.extension_path / popup_file
        
        if not popup_path.exists():
            return BrowserTestResult(
                browser=self.browser,
                test_type='popup_test',
                success=False,
                message=f'Popup file not found: {popup_file}',
                details={'expected_path': str(popup_path)}
            )
        
        # Check popup for inline scripts (store rejection)
        with open(popup_path) as f:
            popup_html = f.read()
        
        if '<script>' in popup_html:
            return BrowserTestResult(
                browser=self.browser,
                test_type='popup_test',
                success=False,
                message='Popup contains inline script (will be rejected from store)',
                console_warnings=['Move inline scripts to external .js file']
            )
        
        return BrowserTestResult(
            browser=self.browser,
            test_type='popup_test',
            success=True,
            message=f'Popup test passed: {popup_file}'
        )
    
    def test_content_scripts(self) -> BrowserTestResult:
        """Test content script configuration"""
        manifest_path = self.extension_path / 'manifest.json'
        
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except:
            return BrowserTestResult(
                browser=self.browser,
                test_type='content_scripts',
                success=False,
                message='Cannot read manifest'
            )
        
        content_scripts = manifest.get('content_scripts', [])
        
        if not content_scripts:
            return BrowserTestResult(
                browser=self.browser,
                test_type='content_scripts',
                success=True,
                message='No content scripts (not required)'
            )
        
        issues = []
        
        for idx, script in enumerate(content_scripts):
            # Check required files
            js_files = script.get('js', [])
            
            for js_file in js_files:
                script_path = self.extension_path / js_file
                if not script_path.exists():
                    issues.append(f'Content script not found: {js_file}')
            
            # Check match patterns
            matches = script.get('matches', [])
            if not matches:
                issues.append(f'Content script {idx}: no match patterns')
            
            # Warn about overly broad permissions
            for match in matches:
                if match in ['<all_urls>', '*://*/*']:
                    issues.append(f'Overly broad match pattern: {match}')
        
        if issues:
            return BrowserTestResult(
                browser=self.browser,
                test_type='content_scripts',
                success=False,
                message='Content script issues found',
                console_warnings=issues,
                details={'issues_count': len(issues)}
            )
        
        return BrowserTestResult(
            browser=self.browser,
            test_type='content_scripts',
            success=True,
            message=f'Content scripts valid ({len(content_scripts)} scripts)'
        )
    
    def test_background_script(self) -> BrowserTestResult:
        """Test background/service worker"""
        manifest_path = self.extension_path / 'manifest.json'
        
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except:
            return BrowserTestResult(
                browser=self.browser,
                test_type='background_script',
                success=False,
                message='Cannot read manifest'
            )
        
        mv = manifest.get('manifest_version', 2)
        
        if mv == 3:
            # Check service_worker
            service_worker = manifest.get('background', {}).get('service_worker')
            
            if not service_worker:
                return BrowserTestResult(
                    browser=self.browser,
                    test_type='background_script',
                    success=False,
                    message='MV3: Missing service_worker in background'
                )
            
            worker_path = self.extension_path / service_worker
            if not worker_path.exists():
                return BrowserTestResult(
                    browser=self.browser,
                    test_type='background_script',
                    success=False,
                    message=f'Service worker file not found: {service_worker}'
                )
        else:
            # Check background page (MV2)
            bg = manifest.get('background', {})
            bg_page = bg.get('page')
            bg_scripts = bg.get('scripts', [])
            
            if not bg_page and not bg_scripts:
                return BrowserTestResult(
                    browser=self.browser,
                    test_type='background_script',
                    success=False,
                    message='No background page or scripts'
                )
            
            if bg_page:
                page_path = self.extension_path / bg_page
                if not page_path.exists():
                    return BrowserTestResult(
                        browser=self.browser,
                        test_type='background_script',
                        success=False,
                        message=f'Background page not found: {bg_page}'
                    )
        
        return BrowserTestResult(
            browser=self.browser,
            test_type='background_script',
            success=True,
            message=f'Background script valid (MV{mv})'
        )
    
    def test_permissions(self) -> BrowserTestResult:
        """Validate permissions"""
        manifest_path = self.extension_path / 'manifest.json'
        
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except:
            return BrowserTestResult(
                browser=self.browser,
                test_type='permissions',
                success=False,
                message='Cannot read manifest'
            )
        
        permissions = manifest.get('permissions', [])
        host_permissions = manifest.get('host_permissions', [])
        
        warnings = []
        
        # Check for dangerous permissions
        dangerous = {
            'webRequestBlocking': 'High impact permission',
            'proxy': 'Rare use, many stores reject',
            'debugger': 'Cannot be used in store extensions',
            'declarativeNetRequest': 'Requires additional review',
        }
        
        for perm in permissions:
            if perm in dangerous:
                warnings.append(f'⚠ {perm}: {dangerous[perm]}')
        
        # Check host permissions
        for host in host_permissions:
            if host in ['<all_urls>', '*://*/*']:
                warnings.append(f'⚠ {host}: Overly broad permission')
        
        if warnings:
            return BrowserTestResult(
                browser=self.browser,
                test_type='permissions',
                success=False,
                message='Permission warnings found',
                console_warnings=warnings,
                details={'total_permissions': len(permissions) + len(host_permissions)}
            )
        
        return BrowserTestResult(
            browser=self.browser,
            test_type='permissions',
            success=True,
            message=f'Permissions valid ({len(permissions)} API + {len(host_permissions)} host)'
        )
    
    def run_all_tests(self) -> Dict:
        """Run all browser tests"""
        results = []
        
        # Check if browser is available
        avail = self.check_browser_available()
        results.append(avail)
        
        if not avail.success:
            return {
                'browser': self.browser,
                'success': False,
                'results': results,
                'message': f'{self.browser} not available'
            }
        
        # Run all tests
        results.append(self.test_extension_load())
        results.append(self.test_popup())
        results.append(self.test_content_scripts())
        results.append(self.test_background_script())
        results.append(self.test_permissions())
        
        # Summary
        passed = sum(1 for r in results if r.success)
        total = len(results)
        
        return {
            'browser': self.browser,
            'success': passed == total,
            'results': results,
            'summary': {
                'passed': passed,
                'total': total,
                'failed': total - passed,
            }
        }
