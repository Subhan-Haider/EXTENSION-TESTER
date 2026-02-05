"""
End-to-End Integration Tests
Tests the entire pipeline with real browser automation
"""
import unittest
import tempfile
import shutil
import json
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from exttester.pipeline import TestingPipeline
from exttester.playwright_engine import PlaywrightBrowserEngine


class TestRealBrowserAutomation(unittest.TestCase):
    """Test real browser automation with Playwright"""
    
    @classmethod
    def setUpClass(cls):
        """Create a test extension"""
        cls.test_dir = tempfile.mkdtemp()
        cls.extension_path = Path(cls.test_dir) / "test-extension"
        cls.extension_path.mkdir()
        
        # Create manifest.json
        manifest = {
            "manifest_version": 3,
            "name": "Test Extension",
            "version": "1.0.0",
            "description": "Test extension for automated testing",
            "action": {
                "default_popup": "popup.html",
                "default_icon": {
                    "16": "icon16.png",
                    "48": "icon48.png",
                    "128": "icon128.png"
                }
            },
            "permissions": ["storage", "tabs"],
            "background": {
                "service_worker": "background.js"
            }
        }
        
        with open(cls.extension_path / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
        
        # Create popup.html
        popup_html = """<!DOCTYPE html>
<html>
<head>
    <title>Test Popup</title>
    <style>
        body { width: 300px; padding: 10px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Test Extension</h1>
    <button id="testBtn">Click Me</button>
    <script src="popup.js"></script>
</body>
</html>"""
        
        with open(cls.extension_path / "popup.html", "w") as f:
            f.write(popup_html)
        
        # Create popup.js
        popup_js = """
document.getElementById('testBtn').addEventListener('click', function() {
    console.log('Button clicked!');
    chrome.storage.local.set({clicked: true});
});
"""
        
        with open(cls.extension_path / "popup.js", "w") as f:
            f.write(popup_js)
        
        # Create background.js
        background_js = """
console.log('Background service worker started');

chrome.runtime.onInstalled.addListener(() => {
    console.log('Extension installed');
});
"""
        
        with open(cls.extension_path / "background.js", "w") as f:
            f.write(background_js)
        
        # Create dummy icons
        for size in [16, 48, 128]:
            icon_path = cls.extension_path / f"icon{size}.png"
            # Create minimal PNG (1x1 transparent pixel)
            icon_path.write_bytes(
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
                b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
                b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            )
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test directory"""
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
    
    def test_playwright_engine_exists(self):
        """Test that Playwright engine can be instantiated"""
        try:
            engine = PlaywrightBrowserEngine(str(self.extension_path))
            self.assertIsNotNone(engine)
        except ImportError:
            self.skipTest("Playwright not installed")
    
    def test_extension_load_chromium(self):
        """Test loading extension in Chromium"""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("Playwright not installed")
        
        engine = PlaywrightBrowserEngine(str(self.extension_path))
        result = engine.test_extension_load(browser='chromium', headless=True)
        
        # Should succeed or have specific error
        self.assertIn('success', result)
        self.assertIn('console_logs', result)
        self.assertIn('errors', result)
    
    def test_popup_testing(self):
        """Test popup functionality"""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("Playwright not installed")
        
        engine = PlaywrightBrowserEngine(str(self.extension_path))
        result = engine.test_popup(browser='chromium')
        
        # Should complete without crashing
        self.assertIn('success', result)
        self.assertIsInstance(result.get('errors', []), list)
    
    def test_full_pipeline(self):
        """Test complete testing pipeline"""
        pipeline = TestingPipeline(str(self.extension_path), browsers=['chrome'])
        results = pipeline.run()
        
        # Verify structure
        self.assertIn('extension', results)
        self.assertIn('stages', results)
        self.assertIn('summary', results)
        
        # Verify stages ran
        self.assertGreater(len(results['stages']), 0)
        
        # Verify summary
        summary = results['summary']
        self.assertIn('total_stages', summary)
        self.assertIn('success', summary)


class TestScoringEngine(unittest.TestCase):
    """Test the scoring engine"""
    
    def test_scoring_calculation(self):
        """Test that scoring engine calculates correctly"""
        from exttester.scoring_engine import ScoringEngine
        
        # Mock extension data
        test_data = {
            'security': {
                'score': 85,
                'findings': ['test finding'],
                'permission_findings': []
            },
            'performance': {
                'total_size_mb': 1.5,
                'file_count': 50,
                'largest_file_mb': 0.5
            },
            'meta': {
                'name': 'Test Extension',
                'version': '1.0.0',
                'description': 'Test'
            },
            'browsers': {
                'chrome': {
                    'valid': True,
                    'errors': [],
                    'warnings': []
                }
            }
        }
        
        engine = ScoringEngine()
        score_results = engine.calculate_final_score(test_data)
        
        # Verify structure
        self.assertIn('final_score', score_results)
        self.assertIn('grade', score_results)
        self.assertIn('breakdown', score_results)
        self.assertIn('recommendations', score_results)
        
        # Verify score is valid
        self.assertGreaterEqual(score_results['final_score'], 0)
        self.assertLessEqual(score_results['final_score'], 100)
        
        # Verify grade is valid
        valid_grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
        self.assertIn(score_results['grade'], valid_grades)


class TestVulnerabilityScanner(unittest.TestCase):
    """Test vulnerability scanner"""
    
    @classmethod
    def setUpClass(cls):
        """Create test package.json"""
        cls.test_dir = tempfile.mkdtemp()
        cls.extension_path = Path(cls.test_dir)
        
        # Create package.json with vulnerable dependency
        package_json = {
            "name": "test-extension",
            "version": "1.0.0",
            "dependencies": {
                "lodash": "4.17.0",  # Vulnerable version
                "axios": "0.21.0"     # Vulnerable version
            }
        }
        
        with open(cls.extension_path / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
    
    def test_vulnerability_detection(self):
        """Test that vulnerable packages are detected"""
        from exttester.vulnerability_scanner import scan_for_vulnerabilities
        
        results = scan_for_vulnerabilities(str(self.extension_path))
        
        # Verify structure
        self.assertIn('vulnerabilities', results)
        self.assertIn('total_count', results)
        self.assertIn('severity_counts', results)
        
        # Should detect vulnerabilities
        self.assertGreater(results['total_count'], 0)
        
        # Should have recommendations
        self.assertIn('recommendations', results)
        self.assertGreater(len(results['recommendations']), 0)


class TestSecurityScanner(unittest.TestCase):
    """Test security scanner"""
    
    def test_permission_risk_detection(self):
        """Test that risky permissions are flagged"""
        from exttester.security_scanner import scan_extension
        
        # Create temp extension with risky permissions
        test_dir = tempfile.mkdtemp()
        extension_path = Path(test_dir)
        
        manifest = {
            "manifest_version": 3,
            "name": "Risky Extension",
            "version": "1.0.0",
            "permissions": ["webRequestBlocking", "debugger", "cookies"],
            "host_permissions": ["<all_urls>"]
        }
        
        with open(extension_path / "manifest.json", "w") as f:
            json.dump(manifest, f)
        
        results = scan_extension(str(extension_path))
        
        # Clean up
        shutil.rmtree(test_dir)
        
        # Verify structure
        self.assertIn('findings', results)
        self.assertIn('permission_risk', results)
        self.assertIn('score', results)
        
        # Should detect high risk
        self.assertIn(results['permission_risk'], ['High', 'Critical'])
        
        # Score should be lower due to risks
        self.assertLess(results['score'], 100)


def run_automated_tests():
    """Run all automated tests"""
    print("=" * 70)
    print("RUNNING AUTOMATED REAL BROWSER TESTS")
    print("=" * 70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRealBrowserAutomation))
    suite.addTests(loader.loadTestsFromTestCase(TestScoringEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestVulnerabilityScanner))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityScanner))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print()
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_automated_tests()
    sys.exit(0 if success else 1)
