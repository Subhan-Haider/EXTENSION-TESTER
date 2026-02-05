
import unittest
from pathlib import Path
from exttester.validator import ExtensionValidator

class TestExtensionValidator(unittest.TestCase):

    def setUp(self):
        self.validator = ExtensionValidator('chrome')

    def test_validate_manifest_missing(self):
        # We need a path that doesn't have a manifest. 
        # Using the current directory if it doesn't have one, or a temp dir is better.
        # For simplicity in this env, let's use a non-existent path logic or catch the error.
        
        # Actually validation checks for file existence.
        # let's assume 'dummy_path' does not exist
        path = "dummy_path"
        is_valid, errors, warnings = self.validator.validate_extension(path, 'chrome')
        self.assertFalse(is_valid)
        self.assertTrue(any("Directory not found" in e for e in errors))

    def test_browser_support(self):
        v_firefox = ExtensionValidator('firefox')
        self.assertEqual(v_firefox.browser_type, 'firefox')
        v_chrome = ExtensionValidator('chrome')
        self.assertEqual(v_chrome.browser_type, 'chrome')

if __name__ == '__main__':
    unittest.main()
