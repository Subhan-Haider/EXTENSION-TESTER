from pathlib import Path
from typing import Dict, List


def generate_pdf_report(report: Dict, out_path: str) -> str:
    """
    Generate a simple PDF report (summary + table).
    Requires reportlab.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    except Exception as e:
        raise RuntimeError(f"reportlab not installed: {e}")

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    summary = _build_summary(report)
    browsers = report.get("browsers", [])

    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Extension Test Report", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Root: {summary['root']}", styles["Normal"]))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"Total: {summary['total']} | Passed: {summary['passed']} | Failed: {summary['failed']} | Warnings: {summary['warnings']}",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 16))

    data = [["Extension"] + browsers + ["Risk", "Score", "Security"]]
    for ext_name, ext_data in report.get("extensions", {}).items():
        row = [ext_name]
        for b in browsers:
            row.append(_browser_status(ext_data, b))
        row.append(_risk_label(ext_data))
        row.append(str(_risk_score(ext_data)))
        row.append(str(_security_score(ext_data)))
        data.append(row)

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
    ]))
    elements.append(table)

    doc.build(elements)
    return str(path)


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

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "warnings": warnings,
        "root": report.get("root_folder", "unknown"),
    }


def _warning_count(data: Dict) -> int:
    total = 0
    for b in data.get("browsers", {}).values():
        total += len(b.get("warnings", []) or [])
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


def _risk_label(data: Dict) -> str:
    score = _risk_score(data)
    if score >= 85:
        return "Low"
    if score >= 60:
        return "Medium"
    return "High"


def _security_score(data: Dict) -> int:
    security = data.get("security", {})
    score = security.get("score")
    if isinstance(score, int):
        return max(0, min(100, score))
    return 100
