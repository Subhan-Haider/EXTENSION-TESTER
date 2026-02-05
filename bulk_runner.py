import json
from pathlib import Path
from typing import Dict, List, Optional

from bulk_scanner import find_extensions
from performance_metrics import collect_metrics
from security_scanner import scan_extension
from validator import ExtensionValidator, BrowserType


BROWSER_MAP = {
    "chrome": BrowserType.CHROME,
    "firefox": BrowserType.FIREFOX,
    "edge": BrowserType.EDGE,
    "opera": BrowserType.OPERA,
}


def normalize_browsers(selected_browsers: List[str]) -> List[str]:
    if not selected_browsers:
        return list(BROWSER_MAP.values())

    normalized = []
    for browser in selected_browsers:
        key = browser.lower().strip()
        if key == "all":
            return list(BROWSER_MAP.values())
        if key in BROWSER_MAP:
            normalized.append(BROWSER_MAP[key])
    return normalized


def run_bulk_tests(
    root_folder: str,
    selected_browsers: List[str],
    report_path: Optional[str] = None,
    run_runtime: bool = False,
    test_urls: Optional[List[str]] = None,
    screenshot_dir: Optional[str] = None,
) -> Dict:
    extensions = find_extensions(root_folder)
    browsers = normalize_browsers(selected_browsers)

    report: Dict[str, Dict] = {
        "root_folder": str(Path(root_folder).resolve()),
        "browsers": browsers,
        "extensions": {},
    }

    total = len(extensions)
    for i, ext_path in enumerate(extensions, start=1):
        ext_name = Path(ext_path).name
        meta = _collect_extension_metadata(ext_path)
        performance = collect_metrics(ext_path)
        security = scan_extension(ext_path)
        print(f"\n[{i}/{total}] Testing {ext_name}")
        report["extensions"][ext_name] = {
            "path": ext_path,
            "meta": meta,
            "performance": performance,
            "security": security,
            "browsers": {},
        }

        for browser in browsers:
            print(f"   - {browser}")
            validator = ExtensionValidator(browser)
            is_valid, errors, warnings = validator.validate_extension(ext_path, browser)
            report["extensions"][ext_name]["browsers"][browser] = {
                "valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "compatible": sorted(list(validator.detected_browsers)),
            }

        if run_runtime:
            from runtime_tester import run_runtime_tests
            urls = test_urls or ["https://www.google.com", "https://www.github.com"]
            runtime = run_runtime_tests(
                ext_path,
                [b.lower() for b in browsers],
                urls,
                capture_screenshots=bool(screenshot_dir),
                screenshot_dir=screenshot_dir,
                extension_name=ext_name,
            )
            report["extensions"][ext_name]["runtime"] = runtime

    if report_path:
        _write_report(report, report_path)

    return report


def _write_report(report: Dict, report_path: str) -> None:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


def _collect_extension_metadata(ext_path: str) -> Dict:
    path = Path(ext_path)
    manifest_path = path / "manifest.json"
    meta = {
        "name": path.name,
        "version": "unknown",
        "manifest_version": "unknown",
        "file_count": 0,
        "size_mb": 0.0,
    }
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            meta["name"] = data.get("name", meta["name"])
            meta["version"] = data.get("version", meta["version"])
            meta["manifest_version"] = data.get("manifest_version", meta["manifest_version"])
        except Exception:
            pass

    try:
        files = [p for p in path.rglob("*") if p.is_file()]
        meta["file_count"] = len(files)
        total_size = sum(p.stat().st_size for p in files)
        meta["size_mb"] = round(total_size / (1024 * 1024), 2)
    except Exception:
        pass

    return meta
