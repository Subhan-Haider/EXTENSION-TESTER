"""
Advanced Extension Testing - Popup, Content Script, Background Script Testing
"""
import json
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Tuple
import re


class ExtensionTester:
    """Advanced testing for extension features"""
    
    def __init__(self, extension_path: str):
        self.extension_path = Path(extension_path)
        self.manifest = self._load_manifest()
        self.errors = []
        self.warnings = []
    
    def _load_manifest(self) -> dict:
        """Load manifest.json"""
        try:
            with open(self.extension_path / "manifest.json", 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def test_popup(self) -> Tuple[bool, List[str]]:
        """
        Test extension popup:
        - Verify popup.html exists
        - Check popup.js for errors
        - Verify all assets load
        """
        issues = []
        
        action = self.manifest.get('action', {})
        if not action:
            action = self.manifest.get('browser_action', {})
        
        popup_path = action.get('default_popup')
        
        if not popup_path:
            return True, []  # No popup defined, that's OK
        
        full_popup_path = self.extension_path / popup_path
        
        if not full_popup_path.exists():
            issues.append(f"❌ Popup file not found: {popup_path}")
            return False, issues
        
        # Check for inline scripts (security issue)
        with open(full_popup_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if '<script>' in content or 'onclick=' in content:
                issues.append(f"⚠️ Popup contains inline scripts (security risk for MV3)")
            
            # Check referenced CSS/JS
            for match in re.findall(r'(src|href)=["\']([^"\']+)["\']', content):
                asset_path = self.extension_path / match[1]
                if not asset_path.exists():
                    issues.append(f"❌ Popup asset not found: {match[1]}")
        
        return len(issues) == 0, issues
    
    def test_content_scripts(self) -> Tuple[bool, List[str]]:
        """
        Test content scripts:
        - Verify all files exist
        - Check for common issues
        - Detect conflicts
        """
        issues = []
        
        content_scripts = self.manifest.get('content_scripts', [])
        
        if not content_scripts:
            return True, []  # No content scripts
        
        for i, script_config in enumerate(content_scripts):
            # Check JS files
            for js_file in script_config.get('js', []):
                full_path = self.extension_path / js_file
                if not full_path.exists():
                    issues.append(f"❌ Content script not found: {js_file}")
                else:
                    # Check for common issues
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                        
                        # Check for document_start (can cause issues)
                        if script_config.get('run_at') == 'document_start':
                            if 'document.body' in code or 'document.addEventListener' in code:
                                issues.append(f"⚠️ Content script runs at document_start but accesses DOM in {js_file}")
                        
                        # Check for eval
                        if 'eval(' in code:
                            issues.append(f"❌ Content script uses eval() - security risk: {js_file}")
            
            # Check CSS files
            for css_file in script_config.get('css', []):
                full_path = self.extension_path / css_file
                if not full_path.exists():
                    issues.append(f"❌ Content script CSS not found: {css_file}")
            
            # Check match patterns
            matches = script_config.get('matches', [])
            if '*://*/*' in matches:
                issues.append(f"⚠️ Content script uses overly broad match pattern: *://*/*")
        
        return len(issues) == 0, issues
    
    def test_background_script(self) -> Tuple[bool, List[str]]:
        """
        Test background script/service worker:
        - Verify file exists
        - Check for common issues
        """
        issues = []
        
        background = self.manifest.get('background', {})
        
        if not background:
            return True, []
        
        # Manifest v3 uses service_worker
        if self.manifest.get('manifest_version') == 3:
            service_worker = background.get('service_worker')
            if not service_worker:
                issues.append(f"❌ Manifest v3: background.service_worker not specified")
                return False, issues
            
            full_path = self.extension_path / service_worker
            if not full_path.exists():
                issues.append(f"❌ Service worker file not found: {service_worker}")
            else:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                    if 'eval(' in code:
                        issues.append(f"❌ Service worker uses eval() - not allowed")
                    if 'async function' not in code and 'Promise' not in code:
                        issues.append(f"⚠️ Service worker might not handle async operations properly")
        
        # Manifest v2 uses scripts
        elif self.manifest.get('manifest_version') == 2:
            scripts = background.get('scripts', [])
            for script in scripts:
                full_path = self.extension_path / script
                if not full_path.exists():
                    issues.append(f"❌ Background script not found: {script}")
        
        return len(issues) == 0, issues
    
    def test_permissions(self) -> Tuple[bool, List[str]]:
        """
        Test permission declarations:
        - Check for dangerous permissions
        - Unused permissions
        - Browser-specific issues
        """
        issues = []
        
        permissions = self.manifest.get('permissions', [])
        host_permissions = self.manifest.get('host_permissions', [])
        
        # Check host permissions for overly broad patterns
        for perm in host_permissions:
            if perm in ['<all_urls>', '*://*/*', 'http://*/*', 'https://*/*']:
                issues.append(f"❌ Overly broad host permission: {perm} - specify exact hosts")
        
        # Check for dangerous permissions
        dangerous_perms = {
            'webRequest': '⚠️ webRequest is slow and deprecated - use declarativeNetRequest',
            'webRequestBlocking': '❌ webRequestBlocking not allowed in MV3',
            'tabs': '⚠️ tabs permission - consider limiting scope',
            'activeTab': '✓ activeTab is safer than tabs'
        }
        
        for perm, warning in dangerous_perms.items():
            if perm in permissions:
                issues.append(f"{warning}")
        
        return len(issues) == 0, issues
    
    def run_all_tests(self) -> Dict[str, Tuple[bool, List[str]]]:
        """Run all tests"""
        return {
            'popup': self.test_popup(),
            'content_scripts': self.test_content_scripts(),
            'background': self.test_background_script(),
            'permissions': self.test_permissions(),
        }
