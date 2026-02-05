import re
import json
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional


class PrivacyPolicyScanner:
    """Scan extension for data collection indicators and privacy policy presence."""

    POLICY_FILENAMES = [
        "privacy_policy.md",
        "privacy_policy.txt",
        "privacy_policy.html",
        "privacy-policy.md",
        "privacy-policy.txt",
        "privacy-policy.html",
        "PRIVACY_POLICY.md",
        "PRIVACY_POLICY.txt",
        "PRIVACY_POLICY.html",
        "PRIVACY-POLICY.md",
        "PRIVACY-POLICY.txt",
        "PRIVACY-POLICY.html",
    ]

    ANALYTICS_DOMAINS = [
        "google-analytics.com",
        "googletagmanager.com",
        "mixpanel.com",
        "segment.com",
        "amplitude.com",
        "sentry.io",
        "datadog",
    ]

    def __init__(self, extension_path: str):
        self.extension_path = Path(extension_path)

    def scan(self) -> Dict:
        data_indicators = self._scan_data_indicators()
        policy_file = self._find_policy_file()
        policy_url = self._find_policy_url(policy_file)
        url_reachable = self._check_url_reachable(policy_url) if policy_url else False

        warnings = []
        if data_indicators and not policy_file and not policy_url:
            warnings.append("Data collection indicators found but no privacy policy detected")
        if policy_url and not url_reachable:
            warnings.append("Privacy policy URL appears unreachable")

        return {
            "data_indicators": data_indicators,
            "policy_file": policy_file,
            "policy_url": policy_url,
            "policy_url_reachable": url_reachable,
            "warnings": warnings,
        }

    def _scan_data_indicators(self) -> List[str]:
        indicators = []
        patterns = {
            "network_fetch": r"\bfetch\s*\(",
            "xhr": r"\bXMLHttpRequest\b",
            "send_beacon": r"\bnavigator\.sendBeacon\b",
            "websocket": r"\bWebSocket\b",
            "cookies_api": r"\bchrome\.cookies\b|\bdocument\.cookie\b",
            "storage": r"\bchrome\.storage\b|\blocalStorage\b|\bsessionStorage\b",
        }

        for file_path in self.extension_path.rglob("*.js"):
            content = self._safe_read(file_path)
            if not content:
                continue

            for name, regex in patterns.items():
                if re.search(regex, content):
                    indicators.append(f"{name}: {file_path.relative_to(self.extension_path)}")

            for domain in self.ANALYTICS_DOMAINS:
                if domain in content:
                    indicators.append(f"analytics: {domain} in {file_path.relative_to(self.extension_path)}")

        return sorted(set(indicators))

    def _find_policy_file(self) -> Optional[str]:
        for filename in self.POLICY_FILENAMES:
            candidate = self.extension_path / filename
            if candidate.exists():
                return str(candidate.relative_to(self.extension_path))
        return None

    def _find_policy_url(self, policy_file: Optional[str]) -> Optional[str]:
        urls = []

        # Look in README and manifest for URLs mentioning privacy
        readme = self.extension_path / "README.md"
        if readme.exists():
            urls.extend(self._extract_urls(self._safe_read(readme)))

        manifest_path = self.extension_path / "manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(self._safe_read(manifest_path) or "{}")
                for key in ["homepage_url", "privacy_policy_url", "developer", "author"]:
                    value = manifest.get(key)
                    if isinstance(value, str):
                        urls.extend(self._extract_urls(value))
            except json.JSONDecodeError:
                pass

        if policy_file:
            policy_path = self.extension_path / policy_file
            urls.extend(self._extract_urls(self._safe_read(policy_path)))

        # Prefer URLs containing "privacy"
        for url in urls:
            if "privacy" in url.lower():
                return url
        return urls[0] if urls else None

    def _check_url_reachable(self, url: str) -> bool:
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return 200 <= resp.status < 400
        except Exception:
            try:
                with urllib.request.urlopen(url, timeout=5) as resp:
                    return 200 <= resp.status < 400
            except Exception:
                return False

    @staticmethod
    def _extract_urls(text: str) -> List[str]:
        if not text:
            return []
        return re.findall(r"https?://[^\s)\]]+", text)

    @staticmethod
    def _safe_read(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""
