"""Version information for Extension Tester"""

__version__ = "1.0.0"
__version_info__ = (1, 0, 0)

# Release metadata
__title__ = "Extension Tester"
__description__ = "Professional browser extension testing platform"
__author__ = "Subhan Haider"
__license__ = "MIT"
__url__ = "https://github.com/Subhan-Haider/EXTENSION-TESTER"

# Build info
BUILD_DATE = "2026-02-05"
BUILD_STATUS = "production"
PYTHON_REQUIRES = ">=3.9"

# Feature flags
FEATURES = {
    "browser_automation": True,
    "playwright_engine": True,
    "scoring_engine": True,
    "vulnerability_scanning": True,
    "pdf_reports": True,
    "gui_interface": True,
    "ci_cd": True,
}
