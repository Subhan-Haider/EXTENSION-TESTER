import re
from pathlib import Path
from typing import Dict, List


class NetworkBehaviorAnalyzer:
    """Static scan for network endpoints and risky URLs."""

    TRACKING_DOMAINS = [
        "google-analytics.com",
        "googletagmanager.com",
        "doubleclick.net",
        "mixpanel.com",
        "segment.com",
        "amplitude.com",
    ]

    def __init__(self, extension_path: str):
        self.extension_path = Path(extension_path)

    def analyze(self) -> Dict:
        urls = []
        warnings = []

        for file_path in self.extension_path.rglob("*.js"):
            content = self._safe_read(file_path)
            if not content:
                continue

            found_urls = re.findall(r"https?://[^\s'\"]+", content)
            for url in found_urls:
                urls.append(url)
                if url.startswith("http://"):
                    warnings.append(f"Unencrypted HTTP request: {url}")
                for domain in self.TRACKING_DOMAINS:
                    if domain in url:
                        warnings.append(f"Tracking domain detected: {domain} ({url})")

        return {
            "urls": sorted(set(urls)),
            "warnings": sorted(set(warnings)),
        }

    @staticmethod
    def _safe_read(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""
