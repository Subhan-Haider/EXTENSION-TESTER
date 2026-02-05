import json
import re
from pathlib import Path
from typing import Dict, List


PERMISSION_RISK = {
    "tabs": "Medium",
    "cookies": "High",
    "webRequest": "High",
    "webRequestBlocking": "Critical",
    "history": "High",
    "bookmarks": "Medium",
    "nativeMessaging": "Critical",
    "downloads": "High",
    "management": "High",
    "proxy": "Critical",
    "debugger": "Critical",
    "clipboardRead": "Medium",
    "clipboardWrite": "Medium",
}


def scan_extension(extension_path: str) -> Dict:
    """
    Static security scan.
    Returns findings, permission risks, and a risk score (0-100).
    """
    path = Path(extension_path)
    manifest = _load_manifest(path / "manifest.json")

    findings: List[str] = []
    permission_findings: List[str] = []
    permission_risk = "Low"

    permissions = manifest.get("permissions", []) or []
    host_permissions = manifest.get("host_permissions", []) or []

    # Permission risk analysis
    for perm in permissions:
        risk = PERMISSION_RISK.get(perm)
        if risk:
            permission_findings.append(f"Permission '{perm}' risk: {risk}")
            permission_risk = _max_risk(permission_risk, risk)

    for host in host_permissions:
        if host in ("<all_urls>", "*://*/*", "http://*/*", "https://*/*"):
            findings.append(f"Overly broad host permission: {host}")
            permission_risk = _max_risk(permission_risk, "High")

    # CSP warnings
    csp = manifest.get("content_security_policy", "")
    if isinstance(csp, dict):
        csp = str(csp)
    if "unsafe-eval" in csp:
        findings.append("CSP allows 'unsafe-eval'")
        permission_risk = _max_risk(permission_risk, "High")
    if "unsafe-inline" in csp:
        findings.append("CSP allows 'unsafe-inline'")
        permission_risk = _max_risk(permission_risk, "Medium")

    # Source code checks
    code_findings = _scan_source_files(path)
    findings.extend(code_findings)

    score = _risk_score(findings, permission_findings)
    return {
        "findings": findings,
        "permission_findings": permission_findings,
        "permission_risk": permission_risk,
        "score": score,
    }


def _load_manifest(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _scan_source_files(path: Path) -> List[str]:
    findings: List[str] = []
    js_like = [".js", ".mjs", ".ts"]
    html_like = [".html", ".htm"]

    for file in path.rglob("*"):
        if not file.is_file():
            continue
        suffix = file.suffix.lower()
        if suffix not in js_like and suffix not in html_like:
            continue
        try:
            content = file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if "eval(" in content:
            findings.append(f"{file.name}: uses eval()")
        if "new Function" in content:
            findings.append(f"{file.name}: uses Function() constructor")
        if "innerHTML" in content:
            findings.append(f"{file.name}: uses innerHTML (XSS risk)")
        if "document.write" in content:
            findings.append(f"{file.name}: uses document.write()")
        if re.search(r"https?://", content):
            findings.append(f"{file.name}: references remote URL")

    return findings


def _risk_score(findings: List[str], permission_findings: List[str]) -> int:
    score = 100
    score -= len(findings) * 6
    score -= len(permission_findings) * 8
    return max(0, min(100, score))


def _max_risk(current: str, new: str) -> str:
    order = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
    return new if order.get(new, 0) > order.get(current, 0) else current
