"""
Tests for browser testing module
"""
import pytest
from pathlib import Path
from exttester.browser_tester import (
    BrowserManager, 
    ExtensionBrowserTester, 
    BrowserTestResult
)


class TestBrowserManager:
    """Test browser management"""
    
    def test_browser_manager_creation(self):
        """Test manager can be created"""
        manager = BrowserManager()
        assert manager is not None
        assert hasattr(manager, 'browsers')
    
    def test_browser_configs_exist(self):
        """Test browser configurations are defined"""
        assert 'chrome' in BrowserManager.BROWSER_CONFIGS
        assert 'firefox' in BrowserManager.BROWSER_CONFIGS
        assert 'edge' in BrowserManager.BROWSER_CONFIGS
    
    def test_get_browser_path(self):
        """Test getting browser path"""
        manager = BrowserManager()
        
        # Should return a path (may not exist on all systems)
        chrome_path = manager.get_browser_path('chrome')
        assert isinstance(chrome_path, str)
        assert len(chrome_path) > 0
    
    @pytest.mark.slow
    def test_browser_detection(self):
        """Test browser detection"""
        manager = BrowserManager()
        
        # At least one browser should be available on most systems
        chrome_available = manager.is_installed('chrome')
        edge_available = manager.is_installed('edge')
        firefox_available = manager.is_installed('firefox')
        
        # On Windows, at least Edge should be available
        # On CI, we ensure Chrome is available
        assert chrome_available or edge_available or firefox_available


class TestBrowserTestResult:
    """Test result data structure"""
    
    def test_result_creation(self):
        """Test creating test result"""
        result = BrowserTestResult(
            browser='chrome',
            test_type='load',
            success=True,
            message='Test passed'
        )
        
        assert result.browser == 'chrome'
        assert result.test_type == 'load'
        assert result.success is True
        assert result.message == 'Test passed'
    
    def test_result_defaults(self):
        """Test default values are set"""
        result = BrowserTestResult(
            browser='firefox',
            test_type='popup',
            success=False,
            message='Failed'
        )
        
        assert result.console_errors == []
        assert result.console_warnings == []
        assert result.duration == 0.0
        assert result.details == {}
    
    def test_result_with_errors(self):
        """Test result with console errors"""
        result = BrowserTestResult(
            browser='chrome',
            test_type='load',
            success=False,
            message='Extension failed to load',
            console_errors=['Error 1', 'Error 2']
        )
        
        assert len(result.console_errors) == 2
        assert 'Error 1' in result.console_errors


class TestExtensionBrowserTester:
    """Test extension browser testing"""
    
    def test_tester_creation(self, sample_extension):
        """Test creating browser tester"""
        tester = ExtensionBrowserTester(str(sample_extension), browser='chrome')
        
        assert tester is not None
        assert tester.extension_path == sample_extension
        assert tester.browser == 'chrome'
    
    def test_check_browser_available(self, sample_extension):
        """Test browser availability check"""
        tester = ExtensionBrowserTester(str(sample_extension), browser='chrome')
        result = tester.check_browser_available()
        
        assert isinstance(result, BrowserTestResult)
        assert result.test_type == 'browser_availability'
    
    def test_extension_load_valid_manifest(self, sample_extension):
        """Test loading extension with valid manifest"""
        tester = ExtensionBrowserTester(str(sample_extension), browser='chrome')
        result = tester.test_extension_load()
        
        assert isinstance(result, BrowserTestResult)
        assert result.test_type in ['extension_load', 'extension_load_runtime']
    
    def test_extension_load_missing_manifest(self, temp_dir):
        """Test loading extension without manifest"""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        tester = ExtensionBrowserTester(str(empty_dir), browser='chrome')
        result = tester.test_extension_load()
        
        assert result.success is False
        assert 'manifest.json not found' in result.message
    
    def test_extension_load_invalid_json(self, temp_dir):
        """Test loading extension with invalid JSON"""
        bad_ext = temp_dir / "bad-extension"
        bad_ext.mkdir()
        
        # Create invalid JSON
        with open(bad_ext / "manifest.json", "w") as f:
            f.write("{ invalid json }")
        
        tester = ExtensionBrowserTester(str(bad_ext), browser='chrome')
        result = tester.test_extension_load()
        
        assert result.success is False
        assert 'Invalid manifest.json' in result.message
    
    def test_extension_load_missing_required_fields(self, temp_dir):
        """Test loading extension with missing required fields"""
        import json
        
        bad_ext = temp_dir / "incomplete-extension"
        bad_ext.mkdir()
        
        # Create manifest missing required fields
        manifest = {"name": "Test"}  # Missing version and manifest_version
        with open(bad_ext / "manifest.json", "w") as f:
            json.dump(manifest, f)
        
        tester = ExtensionBrowserTester(str(bad_ext), browser='chrome')
        result = tester.test_extension_load()
        
        assert result.success is False
        assert 'Missing required manifest fields' in result.message
    
    def test_popup_test_no_popup(self, temp_dir):
        """Test popup test when no popup is defined"""
        import json
        
        ext = temp_dir / "no-popup"
        ext.mkdir()
        
        manifest = {
            "manifest_version": 3,
            "name": "No Popup",
            "version": "1.0.0"
        }
        with open(ext / "manifest.json", "w") as f:
            json.dump(manifest, f)
        
        tester = ExtensionBrowserTester(str(ext), browser='chrome')
        result = tester.test_popup()
        
        assert result.success is False
        assert 'No popup defined' in result.message or 'missing action' in result.message
    
    def test_popup_test_missing_file(self, temp_dir):
        """Test popup test when popup file is missing"""
        import json
        
        ext = temp_dir / "missing-popup"
        ext.mkdir()
        
        manifest = {
            "manifest_version": 3,
            "name": "Missing Popup",
            "version": "1.0.0",
            "action": {
                "default_popup": "popup.html"
            }
        }
        with open(ext / "manifest.json", "w") as f:
            json.dump(manifest, f)
        
        tester = ExtensionBrowserTester(str(ext), browser='chrome')
        result = tester.test_popup()
        
        assert result.success is False
        assert 'not found' in result.message
    
    def test_content_scripts_none(self, temp_dir):
        """Test content scripts when none are defined"""
        import json
        
        ext = temp_dir / "no-content"
        ext.mkdir()
        
        manifest = {
            "manifest_version": 3,
            "name": "No Content Scripts",
            "version": "1.0.0"
        }
        with open(ext / "manifest.json", "w") as f:
            json.dump(manifest, f)
        
        tester = ExtensionBrowserTester(str(ext), browser='chrome')
        result = tester.test_content_scripts()
        
        assert result.success is True
        assert 'not required' in result.message
    
    def test_permissions_validation(self, sample_extension):
        """Test permissions validation"""
        tester = ExtensionBrowserTester(str(sample_extension), browser='chrome')
        result = tester.test_permissions()
        
        assert isinstance(result, BrowserTestResult)
        assert result.test_type == 'permissions'
    
    def test_dangerous_permissions_detected(self, risky_extension):
        """Test that dangerous permissions are flagged"""
        tester = ExtensionBrowserTester(str(risky_extension), browser='chrome')
        result = tester.test_permissions()
        
        # Should detect risky permissions
        assert result.success is False or len(result.console_warnings) > 0
    
    @pytest.mark.unit
    def test_test_urls_defined(self):
        """Test that test URLs are defined"""
        assert len(ExtensionBrowserTester.TEST_URLS) > 0
        assert all(url.startswith('http') for url in ExtensionBrowserTester.TEST_URLS)
    
    def test_run_all_tests(self, sample_extension):
        """Test running all tests"""
        tester = ExtensionBrowserTester(str(sample_extension), browser='chrome')
        results = tester.run_all_tests()
        
        assert 'browser' in results
        assert 'success' in results
        assert 'results' in results
        assert 'summary' in results
        
        summary = results['summary']
        assert 'passed' in summary
        assert 'total' in summary
        assert 'failed' in summary
