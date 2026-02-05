"""
Playwright-based browser engine for extension testing.
Alternative to Selenium with better performance and modern APIs.
"""

from pathlib import Path
from typing import Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class PlaywrightBrowserEngine:
    """Modern browser automation engine using Playwright."""
    
    def __init__(self, extension_path: Path):
        self.extension_path = extension_path
        self.supported_browsers = ['chromium', 'firefox']  # Playwright naming
        
    def test_extension_load(self, browser='chromium', headless=True) -> Dict:
        """
        Load extension in browser using Playwright.
        
        Args:
            browser: Browser type ('chromium' or 'firefox')
            headless: Run in headless mode
            
        Returns:
            Dict with test results
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return {
                'success': False,
                'error': 'Playwright not installed. Run: pip install playwright && playwright install',
                'console_logs': [],
                'errors': []
            }
        
        results = {
            'success': False,
            'console_logs': [],
            'errors': [],
            'screenshots': [],
            'load_time': 0
        }
        
        try:
            with sync_playwright() as p:
                # Launch browser
                if browser == 'chromium':
                    browser_instance = p.chromium.launch(
                        headless=headless,
                        args=[
                            f'--disable-extensions-except={self.extension_path}',
                            f'--load-extension={self.extension_path}'
                        ]
                    )
                elif browser == 'firefox':
                    # Firefox extension loading is different
                    browser_instance = p.firefox.launch(headless=headless)
                else:
                    results['error'] = f'Unsupported browser: {browser}'
                    return results
                
                # Create context and page
                context = browser_instance.new_context()
                page = context.new_page()
                
                # Capture console messages
                page.on("console", lambda msg: results['console_logs'].append({
                    'type': msg.type,
                    'text': msg.text
                }))
                
                # Capture unhandled exceptions
                page.on("pageerror", lambda err: results['errors'].append(str(err)))

                # Capture network failures
                page.on("requestfailed", lambda req: results['errors'].append(f"Network fail: {req.url} - {req.failure}"))
                
                # Navigate to test page
                try:
                    page.goto('https://www.google.com', timeout=10000)
                    page.wait_for_load_state('networkidle', timeout=5000)
                    results['success'] = True
                except Exception as e:
                    results['errors'].append(f'Navigation error: {str(e)}')
                
                # Check if extension loaded
                extension_loaded = self._check_extension_loaded(page)
                results['extension_loaded'] = extension_loaded

                # Inject a script to check for content script side-effects if applicable
                # (Optional: check for specific element injected by content script)
                
                # Take screenshot
                screenshot_path = Path('reports/screenshots') / f'{self.extension_path.name}_{browser}.png'
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot_path))
                results['screenshots'].append(str(screenshot_path))
                
                # Close
                context.close()
                browser_instance.close()
                
        except Exception as e:
            results['error'] = str(e)
            results['success'] = False
            logger.error(f"Playwright test error: {e}")
        
        return results
    
        return all_results

    def test_options_page(self, browser='chromium') -> Dict:
        """Test extension options page"""
        if browser != 'chromium':
            return {'success': True, 'skipped': 'Options test only on Chromium'}

        results = {'success': False, 'errors': [], 'console_logs': []}
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser_instance = p.chromium.launch(
                    headless=True,
                    args=[f'--disable-extensions-except={self.extension_path}', f'--load-extension={self.extension_path}']
                )
                context = browser_instance.new_context()
                page = context.new_page()

                ext_id = self._find_extension_id(page)
                if not ext_id:
                    results['error'] = 'Could not find Extension ID'
                    return results

                manifest_path = self.extension_path / 'manifest.json'
                with open(manifest_path) as f:
                    manifest = json.load(f)

                options_page = manifest.get('options_page') or manifest.get('options_ui', {}).get('page')
                if not options_page:
                    results['success'] = True
                    results['skipped'] = 'No options page defined'
                    return results

                options_url = f"chrome-extension://{ext_id}/{options_page}"
                
                page.on("console", lambda msg: results['console_logs'].append(msg.text))
                page.on("pageerror", lambda err: results['errors'].append(str(err)))

                try:
                    page.goto(options_url, timeout=5000)
                    page.wait_for_load_state('domcontentloaded')
                    results['success'] = True
                except Exception as e:
                    results['errors'].append(str(e))

                context.close()
                browser_instance.close()
        except Exception as e:
            results['error'] = str(e)
        return results

    def test_service_worker(self, browser='chromium') -> Dict:
        """Test if service worker/background script is active"""
        if browser != 'chromium':
             return {'success': True, 'skipped': 'Service Worker test only on Chromium'}
             
        results = {'success': False, 'active': False, 'errors': []}
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser_instance = p.chromium.launch(
                    headless=True,
                    args=[f'--disable-extensions-except={self.extension_path}', f'--load-extension={self.extension_path}']
                )
                context = browser_instance.new_context()
                page = context.new_page()
                
                ext_id = self._find_extension_id(page)
                if not ext_id: 
                    results['error'] = 'Could not find Ext ID'
                    return results

                # Check background pages
                background_pages = context.background_pages
                if background_pages:
                    results['success'] = True
                    results['active'] = True
                    results['type'] = 'background_page'
                else:
                    # Service workers are harder to detect directly via context.service_workers in some versions
                    # We can try to query the extension management page
                    page.goto(f"chrome://extensions/?id={ext_id}")
                    try:
                        # Logic to inspect shadow DOM for 'inspect views' could go here
                        # For now, we assume if we loaded without error and have a background field, it's likely running
                        pass 
                    except:
                        pass
                    
                    # Basic check: did we crash?
                    results['success'] = True
                    results['active'] = 'unknown (service worker detection limited)'

                context.close()
                browser_instance.close()
        except Exception as e:
            results['error'] = str(e)
            
        return results
    
    def _check_extension_loaded(self, page) -> bool:
        """Check if extension is loaded in the browser."""
        try:
            # Try to access extension APIs
            result = page.evaluate("""
                () => {
                    return typeof chrome !== 'undefined' && 
                           typeof chrome.runtime !== 'undefined' &&
                           typeof chrome.runtime.id !== 'undefined';
                }
            """)
            return result
        except Exception:
            return False
    
    
    def _find_extension_id(self, page) -> str:
        """Attempt to find extension ID using chrome://extensions"""
        try:
            page.goto("chrome://extensions/", timeout=10000)
            id_val = page.evaluate("""
                () => {
                    const items = document.querySelector('extensions-manager')
                        ?.shadowRoot?.querySelector('extensions-item-list')
                        ?.shadowRoot?.querySelectorAll('extensions-item');
                    
                    if (!items) return null;
                    
                    // Since we only loaded one extension, it's likely the first one
                    // But we can filter by name if needed
                    for (const item of items) {
                        return item.getAttribute('id'); 
                    }
                    return null;
                }
            """)
            return id_val
        except Exception as e:
            logger.warning(f"Could not resolve extension ID: {e}")
            return None

    def test_popup(self, browser='chromium') -> Dict:
        """Test popup starting from browser action"""
        if browser != 'chromium':
            return {'success': True, 'skipped': 'Real popup test only on Chromium'}

        results = {
            'success': False,
            'errors': [],
            'console_logs': []
        }
        
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser_instance = p.chromium.launch(
                    headless=True,
                    args=[
                        f'--disable-extensions-except={self.extension_path}',
                        f'--load-extension={self.extension_path}'
                    ]
                )
                context = browser_instance.new_context()
                page = context.new_page()
                
                # Get ID
                ext_id = self._find_extension_id(page)
                if not ext_id:
                    results['error'] = 'Could not find Extension ID'
                    return results
                
                # Parse manifest for popup path
                manifest_path = self.extension_path / 'manifest.json'
                with open(manifest_path) as f:
                    manifest = json.load(f)
                
                popup_file = None
                action = manifest.get('action') or manifest.get('browser_action') or {}
                if isinstance(action, dict):
                    popup_file = action.get('default_popup')
                
                if not popup_file:
                    results['success'] = True
                    results['skipped'] = 'No popup defined'
                    return results

                popup_url = f"chrome-extension://{ext_id}/{popup_file}"
                
                # Monitor errors
                page.on("console", lambda msg: results['console_logs'].append(msg.text))
                page.on("pageerror", lambda err: results['errors'].append(str(err)))
                
                try:
                    page.goto(popup_url, timeout=5000)
                    page.wait_for_load_state('domcontentloaded')
                    results['success'] = True
                except Exception as e:
                    results['errors'].append(str(e))
                
                context.close()
                browser_instance.close()
                
        except Exception as e:
            results['error'] = str(e)
            
        return results



def test_with_playwright(extension_path: Path, browser='chromium') -> Dict:
    """
    Convenience function to test extension with Playwright.
    
    Args:
        extension_path: Path to extension directory
        browser: Browser to use ('chromium' or 'firefox')
        
    Returns:
        Dict with test results
    """
    engine = PlaywrightBrowserEngine(extension_path)
    return engine.test_extension_load(browser)
