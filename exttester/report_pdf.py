from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import io

try:
    from reportlab.graphics.shapes import Drawing
except ImportError:
    Drawing = None  # Will be checked at runtime


def generate_pdf_report(report: Dict, out_path: str) -> str:
    """
    Generate a comprehensive PDF report with charts and detailed analysis.
    Requires reportlab and matplotlib.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak, Image, KeepTogether
        )
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.graphics.charts.barcharts import VerticalBarChart
    except ImportError as e:
        raise RuntimeError(f"reportlab not installed: pip install reportlab - {e}")

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    elements = []
    
    # Title page
    elements.append(Spacer(1, 2 * inch))
    elements.append(Paragraph("Browser Extension", title_style))
    elements.append(Paragraph("Testing Report", title_style))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles["Normal"]
    ))
    elements.append(PageBreak())
    
    # Executive Summary
    elements.append(Paragraph("Executive Summary", heading_style))
    elements.append(Spacer(1, 12))
    
    summary = _build_summary(report)
    summary_data = [
        ["Metric", "Value"],
        ["Total Extensions", str(summary['total'])],
        ["Passed", str(summary['passed'])],
        ["Failed", str(summary['failed'])],
        ["Total Warnings", str(summary['warnings'])],
        ["Success Rate", f"{summary.get('success_rate', 0):.1f}%"],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Add pie chart for test results
    if summary['total'] > 0:
        elements.append(Paragraph("Test Results Overview", heading_style))
        chart = _create_pie_chart(summary)
        if chart:
            elements.append(chart)
            elements.append(Spacer(1, 20))
    
    elements.append(PageBreak())
    
    # Detailed Results
    elements.append(Paragraph("Detailed Extension Results", heading_style))
    elements.append(Spacer(1, 12))
    
    browsers = report.get("browsers", [])
    extensions = report.get("extensions", {})
    
    if extensions:
        # Create detailed table
        data = [["Extension", "Status", "Errors", "Warnings", "Score"]]
        
        for ext_name, ext_data in extensions.items():
            status = "✓ Pass" if _is_passed(ext_data) else "✗ Fail"
            errors = len(ext_data.get("errors", []))
            warnings = len(ext_data.get("warnings", []))
            score = _overall_score(ext_data)
            
            data.append([
                ext_name[:30],  # Truncate long names
                status,
                str(errors),
                str(warnings),
                f"{score}/100"
            ])
        
        result_table = Table(data, colWidths=[2.5*inch, 1*inch, 0.8*inch, 0.8*inch, 1*inch])
        result_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor('#2ECC71')),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (2, 1), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        elements.append(result_table)
        elements.append(Spacer(1, 20))
    
    # Security Analysis Section
    elements.append(PageBreak())
    elements.append(Paragraph("Security Analysis", heading_style))
    elements.append(Spacer(1, 12))
    
    security_issues = _collect_security_issues(report)
    if security_issues:
        for issue_type, issues in security_issues.items():
            if issues:
                elements.append(Paragraph(f"<b>{issue_type}:</b>", styles["Normal"]))
                for issue in issues[:10]:  # Limit to top 10
                    elements.append(Paragraph(f"  • {issue}", styles["Normal"]))
                elements.append(Spacer(1, 8))
    else:
        elements.append(Paragraph("No security issues detected.", styles["Normal"]))
    
    elements.append(Spacer(1, 20))
    
    # Recommendations
    elements.append(PageBreak())
    elements.append(Paragraph("Recommendations", heading_style))
    elements.append(Spacer(1, 12))
    
    recommendations = _generate_recommendations(report)
    for i, rec in enumerate(recommendations, 1):
        elements.append(Paragraph(f"{i}. {rec}", styles["Normal"]))
        elements.append(Spacer(1, 8))
    
    # Build PDF
    doc.build(elements)
    return str(path)


def _create_pie_chart(summary: Dict):
    """Create a pie chart for test results."""
    try:
        from reportlab.graphics.shapes import Drawing as ChartDrawing
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.lib import colors
        
        drawing = ChartDrawing(400, 200)
        pie = Pie()
        pie.x = 150
        pie.y = 50
        pie.width = 100
        pie.height = 100
        
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        
        pie.data = [passed, failed] if failed > 0 else [passed, 1]
        pie.labels = [f'Passed ({passed})', f'Failed ({failed})']
        pie.slices.strokeWidth = 0.5
        pie.slices[0].fillColor = colors.HexColor('#2ECC71')
        pie.slices[1].fillColor = colors.HexColor('#E74C3C')
        
        drawing.add(pie)
        return drawing
    except Exception:
        return None


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


def _is_passed(data: Dict) -> bool:
    """Check if extension passed all tests."""
    for b in data.get("browsers", {}).values():
        if not b.get("valid"):
            return False
    return True


def _overall_score(data: Dict) -> int:
    """Calculate overall score for an extension."""
    risk = _risk_score(data)
    security = _security_score(data)
    return int((risk + security) / 2)


def _collect_security_issues(report: Dict) -> Dict[str, List[str]]:
    """Collect all security issues from the report."""
    issues = {
        "Critical": [],
        "High": [],
        "Medium": [],
        "Low": []
    }
    
    for ext_name, ext_data in report.get("extensions", {}).items():
        errors = []
        for browser_data in ext_data.get("browsers", {}).values():
            errors.extend(browser_data.get("errors", []))
        
        for error in errors:
            error_str = str(error).lower()
            if any(word in error_str for word in ['eval', 'xss', 'injection', 'unsafe']):
                issues["Critical"].append(f"{ext_name}: {error}")
            elif any(word in error_str for word in ['security', 'permission', 'csp']):
                issues["High"].append(f"{ext_name}: {error}")
            elif 'warning' in error_str:
                issues["Medium"].append(f"{ext_name}: {error}")
            else:
                issues["Low"].append(f"{ext_name}: {error}")
    
    return issues


def _generate_recommendations(report: Dict) -> List[str]:
    """Generate recommendations based on test results."""
    recommendations = []
    
    summary = _build_summary(report)
    
    if summary['failed'] > 0:
        recommendations.append(
            f"Fix {summary['failed']} failing extension(s) before deployment."
        )
    
    if summary['warnings'] > 10:
        recommendations.append(
            f"Address {summary['warnings']} warning(s) to improve code quality."
        )
    
    # Check for common security issues
    security_issues = _collect_security_issues(report)
    if security_issues['Critical']:
        recommendations.append(
            "URGENT: Critical security issues detected. Review eval() usage, "
            "XSS vulnerabilities, and unsafe code execution patterns."
        )
    
    if security_issues['High']:
        recommendations.append(
            "Review high-priority security concerns including permissions "
            "and Content Security Policy configurations."
        )
    
    # Check for Manifest v2 deprecation
    for ext_data in report.get("extensions", {}).values():
        for browser_data in ext_data.get("browsers", {}).values():
            warnings = browser_data.get("warnings", [])
            if any('manifest v2' in str(w).lower() for w in warnings):
                recommendations.append(
                    "Migrate from Manifest V2 to V3 to ensure future compatibility."
                )
                break
        if recommendations and 'Manifest V' in recommendations[-1]:
            break
    
    # Performance recommendations
    for ext_name, ext_data in report.get("extensions", {}).items():
        perf = ext_data.get("performance", {})
        size = perf.get("total_size_mb", 0)
        if size > 10:
            recommendations.append(
                f"{ext_name}: Consider reducing extension size ({size:.1f}MB). "
                "Optimize images and remove unused files."
            )
            break
    
    # Default recommendations
    if not recommendations:
        recommendations.append("All tests passed! Extension is ready for deployment.")
        recommendations.append("Consider running additional manual tests before release.")
        recommendations.append("Review browser-specific features for optimal compatibility.")
    
    return recommendations[:10]  # Limit to top 10 recommendations

