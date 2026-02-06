"""
Automation Runner (Puppeteer-style)
Loads an extension and executes test scenarios.
"""
from pathlib import Path
from typing import List, Callable
import logging
from .playwright_engine import PlaywrightBrowserEngine

logger = logging.getLogger(__name__)

class ExtensionTestRunner:
    """
    Orchestrates real-world testing of an extension by loading it 
    into a browser and running scripts against it.
    """
    
    def __init__(self, extension_path: str, browser: str = 'chromium'):
        self.extension_path = Path(extension_path)
        self.browser = browser
        self.engine = PlaywrightBrowserEngine(self.extension_path)
        self.scenarios: List[Callable] = []

    def add_scenario(self, scenario_func: Callable):
        """Add a test script to the runner queue"""
        self.scenarios.append(scenario_func)

    def run(self, headless: bool = False):
        """
        1. Launches browser
        2. Loads extension automatically
        3. Executes all scenarios
        4. Captures results
        """
        logger.info(f"🚀 Starting Puppeteer-style runner for {self.extension_path.name}")
        
        # Load the extension (using our persistent context engine)
        # Instead of just loading, we'll keep the session open to run scenarios
        from playwright.sync_api import sync_playwright
        import tempfile
        import shutil
        
        user_data_dir = tempfile.mkdtemp(prefix="runner_profile_")
        results = []

        try:
            with sync_playwright() as p:
                launch_args = [
                    f"--disable-extensions-except={self.extension_path.absolute()}",
                    f"--load-extension={self.extension_path.absolute()}",
                ]
                
                # Step 1: Launch Browser
                context = p.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    headless=headless,
                    args=launch_args
                )
                
                page = context.new_page()
                page.goto("https://www.wikipedia.org")
                
                # Step 2: Verify Extension is Active
                # Fallback: Instead of searching chrome://extensions (which can fail in headless),
                # we check if the extension API is present on a real webpage.
                is_active = page.evaluate("() => typeof chrome !== 'undefined' && typeof chrome.runtime !== 'undefined'")
                
                # Try to get ID via internal API if possible
                ext_id = None
                if is_active:
                    try:
                        ext_id = page.evaluate("() => chrome.runtime.id")
                    except:
                        ext_id = "Detected (ID Hidden)"
                
                # Step 3: Run Scenarios
                for scenario in self.scenarios:
                    logger.info(f"⚡ Running scenario: {scenario.__name__}")
                    scenario_results = scenario(page, context, ext_id)
                    results.extend(scenario_results)
                
                context.close()
                
        finally:
            shutil.rmtree(user_data_dir, ignore_errors=True)
            
        return results

if __name__ == "__main__":
    # Test the runner standalone
    logging.basicConfig(level=logging.INFO)
    runner = ExtensionTestRunner("./sample-extension")
    
    # Import the scenario
    from tests.scenarios.smoke_test import test_extension_full_workflow
    runner.add_scenario(test_extension_full_workflow)
    
    output = runner.run(headless=True)
    for line in output:
        print(line)
