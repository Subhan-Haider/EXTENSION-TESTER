import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
import re

# Setup logging
logger = logging.getLogger(__name__)


class BrowserType:
    """Browser type enumeration and detection"""
    CHROME = "Chrome"
    FIREFOX = "Firefox"
    EDGE = "Edge"
    OPERA = "Opera"
    SAFARI = "Safari"
    UNKNOWN = "Unknown"
    
    ALL = [CHROME, FIREFOX, EDGE, OPERA, SAFARI]


class ExtensionValidator:
    """Validates browser extensions for common issues and errors."""
    
    # Manifest v2 & v3 required fields
    MANIFEST_REQUIRED_FIELDS = {
        "manifest_version": [2, 3],
        "name": str,
        "version": str,
    }
    
    # Valid manifest v3 fields
    MANIFEST_V3_FIELDS = {
        "manifest_version", "name", "version", "description",
        "icons", "default_locale", "permissions", "host_permissions",
        "content_scripts", "background", "action", "page_action",
        "browser_action", "web_accessible_resources", "host_permissions",
        "commands", "options_page", "options_ui", "homepage_url",
        "author", "short_name", "offline_enabled", "minimum_chrome_version"
    }
    
    MANIFEST_V2_FIELDS = MANIFEST_V3_FIELDS | {
        "content_security_policy", "externally_connectable", "incognito",
        "key", "oauth2", "platforms", "export", "requirements", "update_url"
    }
    
    # Firefox WebExtension specific fields
    FIREFOX_SPECIFIC_FIELDS = {
        "browser_specific_settings", "applications", "default_locale"
    }
    
    # Chrome specific fields
    CHROME_SPECIFIC_FIELDS = {
        "minimum_chrome_version", "key", "update_url"
    }
    
    def __init__(self, browser_type: str = BrowserType.CHROME):
        self.errors = []
        self.warnings = []
        self.browser_type = browser_type
        self.detected_browsers = set()
    
    def detect_browser_compatibility(self, manifest: dict) -> List[str]:
        """Detect which browsers this extension is compatible with"""
        compatible_browsers = []
        
        manifest_version = manifest.get("manifest_version")
        
        # All modern manifest versions work with Chrome
        if manifest_version in [2, 3]:
            compatible_browsers.append(BrowserType.CHROME)
        
        # Firefox (Manifest v2 only, v3 support limited)
        if manifest_version == 2:
            compatible_browsers.append(BrowserType.FIREFOX)
            # Check for Firefox-specific settings
            if "browser_specific_settings" in manifest:
                compatible_browsers.append(BrowserType.FIREFOX)
            if "applications" in manifest:
                compatible_browsers.append(BrowserType.FIREFOX)
        elif manifest_version == 3:
            # Firefox has limited MV3 support
            if "browser_specific_settings" in manifest:
                compatible_browsers.append(BrowserType.FIREFOX)
                self.warnings.append("Firefox has limited Manifest v3 support")
        
        # Edge (Chrome-based, supports MV3)
        if manifest_version in [2, 3]:
            compatible_browsers.append(BrowserType.EDGE)
        
        # Opera (Chrome-based)
        if manifest_version in [2, 3]:
            compatible_browsers.append(BrowserType.OPERA)
        
        # Safari (WebKit-based)
        if "safari" in str(manifest).lower() or manifest_version == 3:
            compatible_browsers.append(BrowserType.SAFARI)
        
        self.detected_browsers = set(compatible_browsers)
        return list(set(compatible_browsers))  # Remove duplicates
    
    def validate_extension(self, extension_path: str, browser_type: Optional[str] = None) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a single extension.
        
        Args:
            extension_path: Path to extension directory
            browser_type: Specific browser to validate for (optional)
        
        Returns:
            Tuple of (is_valid, errors_list, warnings_list)
        """
        self.errors = []
        self.warnings = []
        
        if browser_type:
            self.browser_type = browser_type
        
        ext_path = Path(extension_path)
        
        if not ext_path.is_dir():
            self.errors.append(f"Extension path is not a directory: {extension_path}")
            return False, self.errors, self.warnings
        
        # Check for manifest.json
        manifest_path = ext_path / "manifest.json"
        if not manifest_path.exists():
            self.errors.append("manifest.json not found in extension root")
            return False, self.errors, self.warnings
        
        # Validate manifest
        manifest_data = self._validate_manifest(manifest_path)
        if manifest_data is None:
            return False, self.errors, self.warnings
        
        manifest_version = manifest_data.get("manifest_version")
        
        # Detect compatible browsers
        compatible_browsers = self.detect_browser_compatibility(manifest_data)
        
        # Validate manifest structure
        self._validate_manifest_structure(manifest_data, manifest_version)
        
        # Validate required files based on manifest content
        self._validate_required_files(ext_path, manifest_data)
        
        # Validate permissions
        self._validate_permissions(manifest_data, manifest_version)
        
        # Check for icon files
        self._validate_icons(ext_path, manifest_data)
        
        # Browser-specific validation
        self._validate_browser_specifics(manifest_data, self.browser_type)
        
        # Additional checks based on version
        if manifest_version == 3:
            self._validate_manifest_v3_requirements(ext_path, manifest_data)
        elif manifest_version == 2:
            self._validate_manifest_v2_requirements(manifest_data)
        
        # Performance and security checks
        self._validate_performance(ext_path, manifest_data)
        self._validate_security(manifest_data)
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _validate_manifest(self, manifest_path: Path) -> Optional[dict]:
        """Load and parse manifest.json"""
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            return manifest
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in manifest.json: {str(e)}")
            return None
        except Exception as e:
            self.errors.append(f"Error reading manifest.json: {str(e)}")
            return None
    
    def _validate_manifest_structure(self, manifest: dict, manifest_version: int):
        """Check manifest has required fields"""
        # Check manifest_version
        if "manifest_version" not in manifest:
            self.errors.append("Missing 'manifest_version' in manifest.json")
        elif manifest["manifest_version"] not in [2, 3]:
            self.errors.append(f"Invalid manifest_version: {manifest['manifest_version']} (must be 2 or 3)")
        
        # Check required fields
        for field, field_type in self.MANIFEST_REQUIRED_FIELDS.items():
            if field == "manifest_version":
                continue
            
            if field not in manifest:
                self.errors.append(f"Missing required field '{field}' in manifest.json")
            elif not isinstance(manifest[field], field_type):
                self.errors.append(f"Field '{field}' has wrong type. Expected {field_type.__name__}")

        if "description" not in manifest:
            self.warnings.append("Missing optional field 'description' in manifest.json")
        elif not isinstance(manifest.get("description"), str):
            self.errors.append("Field 'description' has wrong type. Expected string")
        
        # Check for deprecated fields
        if manifest_version == 3 and "page_action" in manifest:
            self.warnings.append("'page_action' is deprecated in Manifest v3, use 'action' instead")
        
        if manifest_version == 3 and "browser_action" in manifest:
            self.warnings.append("'browser_action' is deprecated in Manifest v3, use 'action' instead")
    
    def _validate_required_files(self, ext_path: Path, manifest: dict):
        """Check for required files referenced in manifest"""
        # Check icons
        if "icons" in manifest and isinstance(manifest["icons"], dict):
            for size, icon_path in manifest["icons"].items():
                full_path = ext_path / icon_path
                if not full_path.exists():
                    self.errors.append(f"Icon file not found: {icon_path}")
        
        # Check content scripts
        if "content_scripts" in manifest:
            if isinstance(manifest["content_scripts"], list):
                for i, script in enumerate(manifest["content_scripts"]):
                    if "js" in script and isinstance(script["js"], list):
                        for js_file in script["js"]:
                            if not (ext_path / js_file).exists():
                                self.errors.append(f"Content script not found: {js_file}")
                    if "css" in script and isinstance(script["css"], list):
                        for css_file in script["css"]:
                            if not (ext_path / css_file).exists():
                                self.errors.append(f"Content stylesheet not found: {css_file}")
        
        # Check background script/service worker
        if "background" in manifest:
            bg = manifest["background"]
            if isinstance(bg, dict):
                if "service_worker" in bg:
                    if not (ext_path / bg["service_worker"]).exists():
                        self.errors.append(f"Service worker not found: {bg['service_worker']}")
                elif "scripts" in bg:
                    for script in bg["scripts"]:
                        if not (ext_path / script).exists():
                            self.errors.append(f"Background script not found: {script}")
    
    def _validate_permissions(self, manifest: dict, manifest_version: int):
        """Validate permission declarations"""
        if "permissions" in manifest:
            perms = manifest["permissions"]
            if not isinstance(perms, list):
                self.errors.append("'permissions' must be an array")
            else:
                for perm in perms:
                    if not isinstance(perm, str):
                        self.errors.append(f"Invalid permission: {perm} (must be string)")
        
        if manifest_version == 3 and "host_permissions" in manifest:
            host_perms = manifest["host_permissions"]
            if not isinstance(host_perms, list):
                self.errors.append("'host_permissions' must be an array")
    
    def _validate_icons(self, ext_path: Path, manifest: dict):
        """Validate icon specifications"""
        if "icons" not in manifest:
            self.warnings.append("No icons specified in manifest.json")
        else:
            icons = manifest["icons"]
            if not isinstance(icons, dict):
                self.errors.append("'icons' must be an object with size keys")
            elif len(icons) == 0:
                self.warnings.append("'icons' object is empty")
    
    def _validate_manifest_v3_requirements(self, ext_path: Path, manifest: dict):
        """Additional validation for Manifest v3"""
        # Check for action (page_action/browser_action deprecated)
        if "action" not in manifest:
            if "page_action" not in manifest and "browser_action" not in manifest:
                self.warnings.append("No 'action' field specified (recommended for Manifest v3)")
        
        # Check for service_worker if background specified
        if "background" in manifest:
            bg = manifest["background"]
            if isinstance(bg, dict) and "scripts" in bg:
                self.errors.append("'background.scripts' not supported in Manifest v3, use 'background.service_worker'")
    
    def _validate_manifest_v2_requirements(self, manifest: dict):
        """Additional validation for Manifest v2"""
        # Check for Content Security Policy
        if "content_security_policy" not in manifest:
            self.warnings.append("No 'content_security_policy' specified (recommended for security)")
    
    def _validate_browser_specifics(self, manifest: dict, browser_type: str):
        """Validate browser-specific requirements"""
        if browser_type == BrowserType.FIREFOX:
            self._validate_firefox_requirements(manifest)
        elif browser_type == BrowserType.CHROME:
            self._validate_chrome_requirements(manifest)
        elif browser_type == BrowserType.EDGE:
            self._validate_edge_requirements(manifest)
        elif browser_type == BrowserType.OPERA:
            self._validate_opera_requirements(manifest)
    
    def _validate_firefox_requirements(self, manifest: dict):
        """Validate Firefox WebExtension requirements"""
        manifest_version = manifest.get("manifest_version")
        
        if manifest_version == 3:
            self.warnings.append("Firefox has limited Manifest v3 support - test thoroughly")
        
        # Firefox-specific permissions
        firefox_permissions = {
            "tabs", "webRequest", "webRequestBlocking", "scripting",
            "activeTab", "contextMenus", "storage", "unlimitedStorage"
        }
        
        # Check for Firefox-specific settings
        if "browser_specific_settings" not in manifest and manifest_version == 2:
            self.warnings.append("Missing 'browser_specific_settings' for Firefox (optional but recommended)")
    
    def _validate_chrome_requirements(self, manifest: dict):
        """Validate Chrome-specific requirements"""
        manifest_version = manifest.get("manifest_version")
        
        if manifest_version == 2:
            self.warnings.append("Manifest v2 is deprecated - migrate to Manifest v3")
        
        # Chrome-specific validation
        if manifest_version == 3:
            # In MV3, service_worker is required if background scripts are needed
            if "background" in manifest:
                bg = manifest["background"]
                if isinstance(bg, dict) and "service_worker" not in bg and "scripts" not in bg:
                    self.warnings.append("Empty 'background' object - consider adding service_worker or scripts")
    
    def _validate_edge_requirements(self, manifest: dict):
        """Validate Edge-specific requirements"""
        # Edge follows Chrome standards but may have additional settings
        manifest_version = manifest.get("manifest_version")
        
        if manifest_version == 2:
            self.warnings.append("Manifest v2 is deprecated - migrate to Manifest v3")
        
        # Edge-specific fields
        if "browser_specific_settings" in manifest:
            self.warnings.append("'browser_specific_settings' is typically for Firefox, not Edge")
    
    def _validate_opera_requirements(self, manifest: dict):
        """Validate Opera-specific requirements"""
        # Opera is Chrome-based, follows similar standards
        manifest_version = manifest.get("manifest_version")
        
        if manifest_version == 2:
            self.warnings.append("Manifest v2 is deprecated - migrate to Manifest v3")
    
    def _validate_performance(self, ext_path: Path, manifest: dict):
        """Validate performance-related issues"""
        # Check for large bundle size
        total_size = sum(f.stat().st_size for f in ext_path.rglob('*') if f.is_file()) / (1024 * 1024)  # Size in MB
        
        if total_size > 50:
            self.warnings.append(f"Extension size is large ({total_size:.1f} MB) - may slow down browser loading")
        
        # Check for excessive permissions
        permissions = manifest.get("permissions", [])
        if len(permissions) > 10:
            self.warnings.append(f"Extension has many permissions ({len(permissions)}) - consider reducing for security")
        
        # Check for wildcard host permissions
        host_permissions = manifest.get("host_permissions", [])
        if "<all_urls>" in host_permissions:
            self.errors.append("'<all_urls>' in host_permissions is too broad - specify specific hosts")
        
        for perm in host_permissions:
            if perm == "*://*/*":
                self.errors.append("'*://*/*' host permission is too broad - specify specific hosts")
    
    def _validate_security(self, manifest: dict):
        """Validate security-related issues"""
        # Check for eval() in content security policy
        csp = manifest.get("content_security_policy", "")
        if isinstance(csp, dict):
            csp = str(csp)
        
        if "unsafe-eval" in csp:
            self.errors.append("'unsafe-eval' found in CSP - this is a security risk")
        
        if "unsafe-inline" in csp:
            self.warnings.append("'unsafe-inline' in CSP can be a security risk - consider using nonces")
        
        # Check for externally_connectable
        if "externally_connectable" in manifest:
            ext_conn = manifest["externally_connectable"]
            if isinstance(ext_conn, dict) and "matches" in ext_conn:
                matches = ext_conn["matches"]
                if "*://*/*" in matches or "<all_urls>" in matches:
                    self.errors.append("'externally_connectable' with <all_urls> is a security risk")


def validate_all_extensions(directory: str) -> Dict[str, Tuple[bool, List, List]]:
    """
    Scan a directory and validate all extensions found.
    
    Returns:
        Dictionary mapping extension paths to (is_valid, errors, warnings)
    """
    results = {}
    dir_path = Path(directory)
    
    if not dir_path.is_dir():
        logger.error(f"Directory not found: {directory}")
        return results
    
    # Look for subdirectories with manifest.json
    validator = ExtensionValidator()
    
    for item in dir_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            if (item / "manifest.json").exists():
                is_valid, errors, warnings = validator.validate_extension(str(item))
                results[item.name] = (is_valid, errors, warnings)
    
    if not results:
        logger.warning(f"No extensions with manifest.json found in {directory}")
    
    return results
