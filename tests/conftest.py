"""
Shared pytest fixtures for Extension Tester tests
"""
import pytest
import tempfile
import shutil
import json
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    if Path(tmp).exists():
        shutil.rmtree(tmp)


@pytest.fixture
def sample_manifest_v3():
    """Sample Manifest V3 configuration"""
    return {
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


@pytest.fixture
def sample_manifest_v2():
    """Sample Manifest V2 configuration"""
    return {
        "manifest_version": 2,
        "name": "Test Extension V2",
        "version": "1.0.0",
        "description": "Test extension MV2",
        "browser_action": {
            "default_popup": "popup.html",
            "default_icon": {
                "16": "icon16.png",
                "48": "icon48.png"
            }
        },
        "permissions": ["storage", "tabs"],
        "background": {
            "scripts": ["background.js"]
        }
    }


@pytest.fixture
def sample_extension(temp_dir, sample_manifest_v3):
    """Create a complete sample extension for testing"""
    extension_path = temp_dir / "test-extension"
    extension_path.mkdir()
    
    # Create manifest.json
    with open(extension_path / "manifest.json", "w") as f:
        json.dump(sample_manifest_v3, f, indent=2)
    
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
    
    with open(extension_path / "popup.html", "w") as f:
        f.write(popup_html)
    
    # Create popup.js
    popup_js = """
document.getElementById('testBtn').addEventListener('click', function() {
    console.log('Button clicked!');
    chrome.storage.local.set({clicked: true});
});
"""
    
    with open(extension_path / "popup.js", "w") as f:
        f.write(popup_js)
    
    # Create background.js
    background_js = """
console.log('Background service worker started');

chrome.runtime.onInstalled.addListener(() => {
    console.log('Extension installed');
});
"""
    
    with open(extension_path / "background.js", "w") as f:
        f.write(background_js)
    
    # Create dummy icons
    for size in [16, 48, 128]:
        icon_path = extension_path / f"icon{size}.png"
        # Create minimal PNG (1x1 transparent pixel)
        icon_path.write_bytes(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
            b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
    
    return extension_path


@pytest.fixture
def risky_extension(temp_dir):
    """Create an extension with security risks for testing"""
    extension_path = temp_dir / "risky-extension"
    extension_path.mkdir()
    
    manifest = {
        "manifest_version": 3,
        "name": "Risky Extension",
        "version": "1.0.0",
        "permissions": ["webRequestBlocking", "debugger", "cookies", "<all_urls>"],
        "host_permissions": ["<all_urls>"]
    }
    
    with open(extension_path / "manifest.json", "w") as f:
        json.dump(manifest, f)
    
    # Create risky JavaScript
    risky_js = """
// Risky patterns
eval('console.log("dangerous")');
document.write('<script>alert(1)</script>');
innerHTML = userInput;
"""
    
    with open(extension_path / "content.js", "w") as f:
        f.write(risky_js)
    
    return extension_path


@pytest.fixture
def mock_extension_data():
    """Mock extension data for scoring tests"""
    return {
        'security': {
            'score': 85,
            'findings': ['test finding'],
            'permission_findings': [],
            'permission_risk': 'Low'
        },
        'performance': {
            'total_size_mb': 1.5,
            'file_count': 50,
            'largest_file_mb': 0.5
        },
        'meta': {
            'name': 'Test Extension',
            'version': '1.0.0',
            'description': 'Test extension for scoring'
        },
        'browsers': {
            'chrome': {
                'valid': True,
                'errors': [],
                'warnings': []
            }
        },
        'linting': {
            'errors': [],
            'warnings': ['Minor warning'],
            'security_issues': []
        }
    }


@pytest.fixture(scope="session")
def playwright_available():
    """Check if Playwright is available"""
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False
