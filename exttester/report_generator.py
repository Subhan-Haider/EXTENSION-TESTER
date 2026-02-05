import csv
import json
import shutil
from pathlib import Path
from typing import Dict, List

from .screenshotter import capture_static_screenshots
from .report_pdf import generate_pdf_report


def generate_reports(report: Dict, out_dir: str) -> Dict[str, str]:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    _inject_static_screenshots(report, out_path)
    _normalize_screenshots(report, out_path)

    json_path = out_path / "report.json"
    csv_path = out_path / "report.csv"
    html_path = out_path / "report.html"
    pdf_path = out_path / "report.pdf"

    _write_json(report, json_path)
    _write_csv(report, csv_path)
    _write_html(report, html_path)
    try:
        generate_pdf_report(report, str(pdf_path))
    except Exception:
        pdf_path = None

    return {
        "json": str(json_path),
        "csv": str(csv_path),
        "html": str(html_path),
        "pdf": str(pdf_path) if pdf_path else "",
    }


def _write_json(report: Dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=_json_fallback)


def _json_fallback(value):
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, Path):
        return str(value)
    return str(value)


def _write_csv(report: Dict, path: Path) -> None:
    browsers = report.get("browsers", [])
    rows = []
    for ext_name, data in report.get("extensions", {}).items():
        row = {
            "extension": ext_name,
            "risk_score": _risk_score(data),
            "security_score": _security_score(data),
            "status": _status_label(data),
            "errors": _error_count(data),
            "warnings": _warning_count(data),
        }
        for browser in browsers:
            row[browser] = _browser_status(data, browser)
        rows.append(row)

    fieldnames = ["extension"] + browsers + ["risk_score", "security_score", "errors", "warnings", "status"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_html(report: Dict, path: Path) -> None:
    browsers = report.get("browsers", [])
    summary = _build_summary(report)
    table_rows = _build_table_rows(report, browsers)
    detail_sections = _build_detail_sections(report, browsers)

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Extension Test Report</title>
  <style>
    :root {{
      --bg: #0F1115;
      --panel: #161922;
      --panel-2: #1D2230;
      --text: #E8EAF0;
      --muted: #A8B0C2;
      --accent: #7CC4FF;
      --ok: #39D98A;
      --warn: #FFD166;
      --fail: #EF476F;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Arial, sans-serif;
      background: radial-gradient(1200px 600px at 10% -10%, #1E2A4A, transparent),
                  radial-gradient(1000px 600px at 110% 10%, #2B1D4A, transparent),
                  var(--bg);
      color: var(--text);
    }}
    .container {{
      max-width: 1200px;
      margin: 24px auto 60px;
      padding: 0 20px;
    }}
    .header {{
      background: linear-gradient(135deg, #1A2236, #141824);
      border: 1px solid #2A3145;
      border-radius: 16px;
      padding: 20px;
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 12px;
    }}
    .title {{
      font-size: 26px;
      font-weight: 700;
      margin: 0 0 6px;
    }}
    .subtitle {{
      color: var(--muted);
      margin: 0;
    }}
    .badge {{
      padding: 8px 12px;
      border-radius: 999px;
      font-weight: 700;
      align-self: start;
    }}
    .badge.ok {{ background: rgba(57,217,138,0.15); color: var(--ok); border: 1px solid rgba(57,217,138,0.35); }}
    .badge.warn {{ background: rgba(255,209,102,0.15); color: var(--warn); border: 1px solid rgba(255,209,102,0.35); }}
    .badge.fail {{ background: rgba(239,71,111,0.15); color: var(--fail); border: 1px solid rgba(239,71,111,0.35); }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-top: 16px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid #2A3145;
      border-radius: 14px;
      padding: 14px;
    }}
    .card h4 {{
      margin: 0 0 4px;
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .card p {{
      margin: 0;
      font-size: 20px;
      font-weight: 700;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
      background: var(--panel);
      border: 1px solid #2A3145;
      border-radius: 12px;
      overflow: hidden;
    }}
    th, td {{
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid #2A3145;
    }}
    th {{
      background: var(--panel-2);
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    tr:hover td {{ background: #1B2130; }}
    .pill {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 999px;
      font-weight: 700;
      font-size: 12px;
    }}
    .pill.ok {{ background: rgba(57,217,138,0.15); color: var(--ok); }}
    .pill.warn {{ background: rgba(255,209,102,0.15); color: var(--warn); }}
    .pill.fail {{ background: rgba(239,71,111,0.15); color: var(--fail); }}
    .section {{
      margin-top: 30px;
      background: var(--panel);
      border: 1px solid #2A3145;
      border-radius: 14px;
      padding: 16px;
    }}
    .section h3 {{
      margin: 0 0 12px;
      font-size: 18px;
    }}
    .muted {{ color: var(--muted); }}
    .details-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0,1fr));
      gap: 12px;
    }}
    .tag {{
      display: inline-block;
      padding: 2px 6px;
      border: 1px solid #2A3145;
      border-radius: 6px;
      font-size: 12px;
      color: var(--muted);
      margin-right: 6px;
    }}
    .meter {{
      height: 10px;
      background: #1D2230;
      border: 1px solid #2A3145;
      border-radius: 999px;
      overflow: hidden;
      margin-top: 6px;
    }}
    .meter > span {{
      display: block;
      height: 100%;
      background: linear-gradient(90deg, #39D98A, #7CC4FF);
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    @media (max-width: 900px) {{
      .grid {{ grid-template-columns: repeat(2, 1fr); }}
      .details-grid {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 600px) {{
      .grid {{ grid-template-columns: 1fr; }}
      table, thead, tbody, th, td, tr {{ display: block; }}
      th {{ position: sticky; top: 0; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1 class="title">Extension Test Report</h1>
        <p class="subtitle">Automated QA + security + compatibility report</p>
        <p class="subtitle muted">Root: {summary['root']}</p>
      </div>
      <div class="badge {summary['badge_class']}">{summary['badge']}</div>
    </div>

    <div class="grid">
      <div class="card"><h4>Total Extensions</h4><p>{summary['total']}</p></div>
      <div class="card"><h4>Passed</h4><p>{summary['passed']}</p></div>
      <div class="card"><h4>Failed</h4><p>{summary['failed']}</p></div>
      <div class="card"><h4>Total Warnings</h4><p>{summary['warnings']}</p></div>
    </div>

    <div class="section">
      <h3>Extension Summary</h3>
      <table>
        <thead>
          <tr>
            <th>Extension</th>
            {''.join(f'<th>{b}</th>' for b in browsers)}
            <th>Risk</th>
            <th>Score</th>
            <th>Security</th>
          </tr>
        </thead>
        <tbody>
          {table_rows}
        </tbody>
      </table>
    </div>

    <div class="section">
      <h3>Per Extension Details</h3>
      {detail_sections}
    </div>
  </div>
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def _build_summary(report: Dict) -> Dict:
    total = len(report.get("extensions", {}))
    passed = 0
    failed = 0
    warnings = 0
    for data in report.get("extensions", {}).values():
        status = _status_label(data)
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        warnings += _warning_count(data)

    badge = "Healthy"
    badge_class = "ok"
    if failed > 0:
        badge = "Critical"
        badge_class = "fail"
    elif warnings > 0:
        badge = "Warning"
        badge_class = "warn"

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "warnings": warnings,
        "badge": badge,
        "badge_class": badge_class,
        "root": report.get("root_folder", "unknown"),
    }


def _build_table_rows(report: Dict, browsers: List[str]) -> str:
    rows = []
    for ext_name, data in report.get("extensions", {}).items():
        risk = _risk_label(data)
        score = _risk_score(data)
        sec_score = _security_score(data)
        cells = [f'<td><a href="#ext-{_slug(ext_name)}">{ext_name}</a></td>']
        for browser in browsers:
            status = _browser_status(data, browser)
            cls = "ok" if status == "PASS" else "fail"
            cells.append(f'<td><span class="pill {cls}">{status}</span></td>')
        cells.append(f'<td>{risk}</td>')
        cells.append(f'<td>{score}</td>')
        cells.append(f'<td>{sec_score}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return "\n".join(rows)


def _build_detail_sections(report: Dict, browsers: List[str]) -> str:
    sections = []
    for ext_name, data in report.get("extensions", {}).items():
        meta = data.get("meta", {})
        performance = data.get("performance", {})
        security = data.get("security", {})
        runtime = data.get("runtime", {})
        issues = _collect_issues(data, browsers)
        sections.append(f"""
        <div id="ext-{_slug(ext_name)}" class="section">
          <h3>{ext_name}</h3>
          <div class="details-grid">
            <div>
              <div class="tag">Version: {meta.get('version', 'unknown')}</div>
              <div class="tag">Manifest: {meta.get('manifest_version', 'unknown')}</div>
              <div class="tag">Size: {performance.get('total_size_mb', 0)} MB</div>
              <div class="tag">Files: {performance.get('file_count', 0)}</div>
            </div>
            <div>
              <div class="tag">Health Score: {_risk_score(data)}</div>
              <div class="tag">Risk: {_risk_label(data)}</div>
              <div class="tag">Security Score: {_security_score(data)}</div>
              <div class="meter"><span style="width:{_risk_score(data)}%"></span></div>
            </div>
          </div>
          <h4>Test Results</h4>
          <ul>
            {issues['results']}
          </ul>
          <h4>Error Logs</h4>
          <pre>{issues['errors'] or 'No errors captured.'}</pre>
          <h4>Warnings</h4>
          <pre>{issues['warnings'] or 'No warnings.'}</pre>
          <h4>Security Findings</h4>
          <pre>{issues['security'] or 'No high-risk security findings detected.'}</pre>
          <h4>Compatibility</h4>
          <pre>{issues['compatibility'] or 'No compatibility issues detected.'}</pre>
          <h4>Performance Metrics</h4>
          <pre>Size: {performance.get('total_size_mb', 0)} MB
JS: {performance.get('js_size_mb', 0)} MB
CSS: {performance.get('css_size_mb', 0)} MB
Images: {performance.get('image_size_mb', 0)} MB
Largest File: {performance.get('largest_file', 'unknown')} ({performance.get('largest_file_mb', 0)} MB)</pre>
          <h4>Runtime Results</h4>
          <pre>{_format_runtime(runtime)}</pre>
          <h4>Screenshots</h4>
          {issues['screenshots']}
        </div>
        """)
    return "\n".join(sections)


def _collect_issues(data: Dict, browsers: List[str]) -> Dict[str, str]:
    results = []
    errors_all = []
    warnings_all = []
    security_all = []
    compatibility_all = []

    for browser in browsers:
        b = data.get("browsers", {}).get(browser, {})
        status = "PASS" if b.get("valid") else "FAIL"
        results.append(f"<li>{browser}: <strong>{status}</strong></li>")

        errors = b.get("errors", []) or []
        warnings = b.get("warnings", []) or []
        compatible = set(b.get("compatible", []) or [])

        for e in errors:
            errors_all.append(f"[{browser}] {e}")
            if _is_security_related(e):
                security_all.append(f"[{browser}] {e}")
        for w in warnings:
            warnings_all.append(f"[{browser}] {w}")
            if _is_security_related(w):
                security_all.append(f"[{browser}] {w}")

        if compatible and browser not in compatible:
            compatibility_all.append(f"[{browser}] Not listed as compatible")

    security = data.get("security", {})
    for f in security.get("findings", []) or []:
        security_all.append(f"[SECURITY] {f}")
    for f in security.get("permission_findings", []) or []:
        security_all.append(f"[PERMISSION] {f}")

    screenshots = data.get("screenshots", []) or []
    if screenshots:
        imgs = []
        for s in screenshots:
            imgs.append(f'<img src="{s}" alt="screenshot" style="max-width:100%; border-radius:8px; margin-top:8px;"/>')
        screenshots_html = "\n".join(imgs)
    else:
        screenshots_html = "<pre>Not captured in this run.</pre>"

    return {
        "results": "\n".join(results),
        "errors": "\n".join(errors_all),
        "warnings": "\n".join(warnings_all),
        "security": "\n".join(security_all),
        "compatibility": "\n".join(compatibility_all),
        "screenshots": screenshots_html,
    }


def _warning_count(data: Dict) -> int:
    total = 0
    for b in data.get("browsers", {}).values():
        total += len(b.get("warnings", []) or [])
    return total


def _error_count(data: Dict) -> int:
    total = 0
    for b in data.get("browsers", {}).values():
        total += len(b.get("errors", []) or [])
    return total


def _status_label(data: Dict) -> str:
    for b in data.get("browsers", {}).values():
        if not b.get("valid"):
            return "FAIL"
    return "PASS"


def _browser_status(data: Dict, browser: str) -> str:
    b = data.get("browsers", {}).get(browser, {})
    return "PASS" if b.get("valid") else "FAIL"


def _risk_score(data: Dict) -> int:
    errors = 0
    warnings = 0
    for b in data.get("browsers", {}).values():
        errors += len(b.get("errors", []) or [])
        warnings += len(b.get("warnings", []) or [])
    score = 100 - (errors * 10 + warnings * 3)
    return max(0, min(100, score))


def _security_score(data: Dict) -> int:
    security = data.get("security", {})
    score = security.get("score")
    if isinstance(score, int):
        return max(0, min(100, score))
    return 100


def _risk_label(data: Dict) -> str:
    score = _risk_score(data)
    if score >= 85:
        return "Low"
    if score >= 60:
        return "Medium"
    return "High"


def _is_security_related(text: str) -> bool:
    keywords = [
        "unsafe", "csp", "permission", "host_permissions",
        "externally_connectable", "eval", "security", "risk"
    ]
    t = text.lower()
    return any(k in t for k in keywords)


def _slug(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")


def _format_runtime(runtime: Dict) -> str:
    if not runtime:
        return "Not measured in this run."
    if runtime.get("error"):
        return f"Runtime test error: {runtime.get('error')}"
    lines = []
    for browser, data in runtime.items():
        if isinstance(data, dict) and data.get("skipped"):
            lines.append(f"{browser}: {data.get('skipped')}")
            continue
        errors = data.get("console_errors", []) if isinstance(data, dict) else []
        timings = data.get("timings", []) if isinstance(data, dict) else []
        lines.append(f"{browser}:")
        if timings:
            for t in timings:
                lines.append(f"  {t.get('url')}: {t.get('load_ms')} ms")
        if errors:
            lines.append("  Console Errors:")
            for e in errors:
                lines.append(f"    - {e}")
        if not timings and not errors:
            lines.append("  No runtime data")
    return "\n".join(lines)


def _inject_static_screenshots(report: Dict, out_path: Path) -> None:
    for ext_name, data in report.get("extensions", {}).items():
        if data.get("screenshots"):
            continue
        ext_path = data.get("path")
        if not ext_path:
            continue
        result = capture_static_screenshots(ext_path, str(out_path), ext_name)
        shots = result.get("screenshots") or []
        if shots:
            data["screenshots"] = shots


def _normalize_screenshots(report: Dict, out_path: Path) -> None:
    for ext_name, data in report.get("extensions", {}).items():
        shots = data.get("screenshots", []) or []
        if not shots:
            continue
        normalized = []
        for s in shots:
            p = Path(s)
            if not p.is_absolute():
                normalized.append(s.replace("\\", "/"))
                continue
            if not p.exists():
                continue
            dest_dir = out_path / "screenshots" / _slug(ext_name)
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / p.name
            if p.resolve() != dest.resolve():
                shutil.copy2(p, dest)
            rel = str(Path("screenshots") / _slug(ext_name) / dest.name).replace("\\", "/")
            normalized.append(rel)
        data["screenshots"] = normalized


class ReportGenerator:
    """
    Legacy report generator for advanced_test.
    Produces HTML/JSON/CSV/Markdown from component test_details.
    """

    def __init__(self, test_details: Dict, extension_path: str):
        self.test_details = test_details
        self.extension_path = Path(extension_path)
        self.out_dir = self.extension_path / "reports"
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def generate_json_report(self) -> str:
        path = self.out_dir / "advanced_report.json"
        payload = {
            "extension": self.extension_path.name,
            "path": str(self.extension_path),
            "tests": self.test_details,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return str(path)

    def generate_csv_report(self) -> str:
        path = self.out_dir / "advanced_report.csv"
        rows = []
        for name, data in self.test_details.items():
            rows.append({
                "test": name,
                "status": data.get("status", "UNKNOWN"),
                "errors": len(data.get("errors", []) or []),
                "warnings": len(data.get("warnings", []) or []),
                "message": data.get("message", ""),
            })
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["test", "status", "errors", "warnings", "message"]
            )
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        return str(path)

    def generate_markdown_report(self) -> str:
        path = self.out_dir / "advanced_report.md"
        lines = [
            f"# Advanced Report: {self.extension_path.name}",
            "",
            "| Test | Status | Errors | Warnings |",
            "|---|---|---:|---:|",
        ]
        for name, data in self.test_details.items():
            errors = len(data.get("errors", []) or [])
            warnings = len(data.get("warnings", []) or [])
            status = data.get("status", "UNKNOWN")
            lines.append(f"| {name} | {status} | {errors} | {warnings} |")
        lines.append("")
        for name, data in self.test_details.items():
            lines.append(f"## {name}")
            lines.append(f"Status: **{data.get('status', 'UNKNOWN')}**")
            if data.get("message"):
                lines.append(f"Message: {data.get('message')}")
            if data.get("errors"):
                lines.append("Errors:")
                for e in data["errors"]:
                    lines.append(f"- {e}")
            if data.get("warnings"):
                lines.append("Warnings:")
                for w in data["warnings"]:
                    lines.append(f"- {w}")
            lines.append("")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return str(path)

    def generate_html_report(self) -> str:
        path = self.out_dir / "advanced_report.html"
        rows = []
        for name, data in self.test_details.items():
            status = data.get("status", "UNKNOWN")
            badge = "ok" if status == "PASS" else "fail"
            rows.append(
                f"<tr><td>{name}</td><td><span class='pill {badge}'>{status}</span></td>"
                f"<td>{len(data.get('errors', []) or [])}</td>"
                f"<td>{len(data.get('warnings', []) or [])}</td></tr>"
            )
        details = []
        for name, data in self.test_details.items():
            errors = "<br/>".join(data.get("errors", []) or []) or "None"
            warnings = "<br/>".join(data.get("warnings", []) or []) or "None"
            details.append(
                f"<h3>{name}</h3>"
                f"<p>Status: <strong>{data.get('status', 'UNKNOWN')}</strong></p>"
                f"<p>{data.get('message', '')}</p>"
                f"<h4>Errors</h4><div class='box'>{errors}</div>"
                f"<h4>Warnings</h4><div class='box'>{warnings}</div>"
            )
        html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Advanced Report</title>
  <style>
    body {{ font-family: "Segoe UI", Arial, sans-serif; background:#0F1115; color:#E8EAF0; padding:20px; }}
    .card {{ background:#161922; border:1px solid #2A3145; border-radius:12px; padding:16px; margin-bottom:16px; }}
    table {{ width:100%; border-collapse:collapse; }}
    th, td {{ padding:8px 10px; border-bottom:1px solid #2A3145; text-align:left; }}
    th {{ color:#A8B0C2; text-transform:uppercase; font-size:12px; }}
    .pill {{ padding:3px 8px; border-radius:999px; font-weight:700; font-size:12px; }}
    .pill.ok {{ background:rgba(57,217,138,0.15); color:#39D98A; }}
    .pill.fail {{ background:rgba(239,71,111,0.15); color:#EF476F; }}
    .box {{ background:#1D2230; border:1px solid #2A3145; border-radius:8px; padding:10px; }}
  </style>
</head>
<body>
  <div class="card">
    <h2>Advanced Report: {self.extension_path.name}</h2>
    <table>
      <thead>
        <tr><th>Test</th><th>Status</th><th>Errors</th><th>Warnings</th></tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>
  <div class="card">
    {''.join(details)}
  </div>
</body>
</html>
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return str(path)
