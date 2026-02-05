import json
import re
from pathlib import Path
from typing import Dict, List

from .privacy_scanner import PrivacyPolicyScanner


class StoreComplianceChecker:
    """Check extension readiness for Chrome Web Store, Edge Add-ons, Firefox AMO."""

    REQUIRED_ICON_SIZES = {
        "chrome": [16, 48, 128],
        "edge": [16, 48, 128],
        "firefox": [48, 96],
    }

    DANGEROUS_PERMISSIONS = {
        "tabs": "Sensitive permission",
        "webRequestBlocking": "High risk permission",
        "debugger": "Not allowed for public store extensions",
        "history": "Sensitive user data",
        "clipboardRead": "Sensitive user data",
    }

    def __init__(self, extension_path: str):
        self.extension_path = Path(extension_path)
        self.manifest = self._load_manifest()

    def check_all(self) -> Dict[str, Dict]:
        privacy_report = PrivacyPolicyScanner(str(self.extension_path)).scan()

        return {
            "chrome": self._check_store("chrome", privacy_report),
            "edge": self._check_store("edge", privacy_report),
            "firefox": self._check_store("firefox", privacy_report),
            "privacy": privacy_report,
        }

    def _check_store(self, store: str, privacy_report: Dict) -> Dict:
        errors = []
        warnings = []
        score = 100

        if not self.manifest:
            return {
                "score": 0,
                "errors": ["manifest.json missing or invalid"],
                "warnings": [],
            }

        # Icon checks
        missing_icons = self._check_icons(store)
        if missing_icons:
            warnings.append(f"Missing icons for {store}: {', '.join(map(str, missing_icons))}")
            score -= 10

        # Permissions checks
        perm_warnings = self._check_permissions()
        if perm_warnings:
            warnings.extend(perm_warnings)
            score -= min(20, 5 * len(perm_warnings))

        # Remote code / external script
        remote_code_warnings = self._check_remote_code()
        if remote_code_warnings:
            errors.extend(remote_code_warnings)
            score -= 20

        # Obfuscation detection
        obfuscation_warnings = self._check_obfuscated_code()
        if obfuscation_warnings:
            warnings.extend(obfuscation_warnings)
            score -= 10

        # Privacy policy alignment
        if privacy_report.get("data_indicators") and not privacy_report.get("policy_file") and not privacy_report.get("policy_url"):
            warnings.append("Data collection detected but no privacy policy found")
            score -= 15

        score = max(0, min(100, score))
        return {
            "score": score,
            "errors": errors,
            "warnings": warnings,
        }

    def _load_manifest(self) -> Dict:
        manifest_path = self.extension_path / "manifest.json"
        if not manifest_path.exists():
            return {}
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _check_icons(self, store: str) -> List[int]:
        required_sizes = self.REQUIRED_ICON_SIZES.get(store, [])
        icons = self.manifest.get("icons", {}) if self.manifest else {}
        missing = []

        for size in required_sizes:
            path = icons.get(str(size))
            if not path or not (self.extension_path / path).exists():
                missing.append(size)
        return missing

    def _check_permissions(self) -> List[str]:
        warnings = []
        permissions = self.manifest.get("permissions", []) if self.manifest else []
        host_permissions = self.manifest.get("host_permissions", []) if self.manifest else []

        for perm in permissions:
            if perm in self.DANGEROUS_PERMISSIONS:
                warnings.append(f"Permission risk: {perm} ({self.DANGEROUS_PERMISSIONS[perm]})")

        for host in host_permissions:
            if host in ["<all_urls>", "*://*/*"]:
                warnings.append("Overly broad host permission: <all_urls>")

        return warnings

    def _check_remote_code(self) -> List[str]:
        warnings = []
        patterns = [
            r"<script[^>]+src=\"https?://",
            r"<script[^>]+src='https?://",
            r"\bimportScripts\s*\(\s*['\"]https?://",
            r"\bfetch\s*\(\s*['\"]https?://[^'\"]+\.js",
        ]

        for file_path in self.extension_path.rglob("*.html"):
            content = self._safe_read(file_path)
            if not content:
                continue
            if any(re.search(p, content, re.IGNORECASE) for p in patterns):
                warnings.append(f"Remote script reference detected in {file_path.relative_to(self.extension_path)}")

        for file_path in self.extension_path.rglob("*.js"):
            content = self._safe_read(file_path)
            if not content:
                continue
            if any(re.search(p, content, re.IGNORECASE) for p in patterns):
                warnings.append(f"Remote code load detected in {file_path.relative_to(self.extension_path)}")

        return warnings

    def _check_obfuscated_code(self) -> List[str]:
        warnings = []
        base64_pattern = re.compile(r"[A-Za-z0-9+/]{120,}={0,2}")
        packed_pattern = re.compile(r"eval\s*\(\s*function\(p,a,c,k,e,d\)")
        atob_eval_pattern = re.compile(r"eval\s*\(\s*atob\(")

        for file_path in self.extension_path.rglob("*.js"):
            content = self._safe_read(file_path)
            if not content:
                continue

            if base64_pattern.search(content):
                warnings.append(f"Possible base64 obfuscation in {file_path.relative_to(self.extension_path)}")
            if packed_pattern.search(content):
                warnings.append(f"Packed/obfuscated code detected in {file_path.relative_to(self.extension_path)}")
            if atob_eval_pattern.search(content):
                warnings.append(f"eval(atob()) pattern detected in {file_path.relative_to(self.extension_path)}")

        return warnings

    @staticmethod
    def _safe_read(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""
