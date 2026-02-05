import re
from pathlib import Path
from typing import Dict, List


class APIUsageScanner:
    """Scan for browser API usage and deprecated calls."""

    DEPRECATED_APIS = {
        "chrome.extension.getURL": "Use chrome.runtime.getURL instead",
        "chrome.extension.sendRequest": "Use chrome.runtime.sendMessage instead",
        "chrome.tabs.executeScript": "Use chrome.scripting.executeScript (MV3)",
        "chrome.tabs.insertCSS": "Use chrome.scripting.insertCSS (MV3)",
        "chrome.tabs.removeCSS": "Use chrome.scripting.removeCSS (MV3)",
    }

    API_PREFIXES = [
        "chrome.tabs",
        "chrome.cookies",
        "chrome.storage",
        "chrome.webRequest",
        "chrome.scripting",
        "chrome.runtime",
        "chrome.declarativeNetRequest",
        "browser.tabs",
        "browser.cookies",
        "browser.storage",
        "browser.runtime",
    ]

    def __init__(self, extension_path: str):
        self.extension_path = Path(extension_path)

    def analyze(self) -> Dict:
        used = set()
        deprecated = []

        for file_path in self.extension_path.rglob("*.js"):
            content = self._safe_read(file_path)
            if not content:
                continue

            for prefix in self.API_PREFIXES:
                if prefix in content:
                    used.add(prefix)

            for api, suggestion in self.DEPRECATED_APIS.items():
                if api in content:
                    deprecated.append(f"Uses deprecated API: {api} ({suggestion})")

        return {
            "used": sorted(used),
            "deprecated": sorted(set(deprecated)),
        }

    @staticmethod
    def _safe_read(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""
