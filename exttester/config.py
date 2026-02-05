from pathlib import Path

APP_NAME = "ExtensionTester"
ROOT_DIR = Path(__file__).resolve().parent
REPORTS_DIR = ROOT_DIR.parent / "reports"
DEFAULT_TEST_URLS = ["https://www.google.com", "https://www.github.com"]
