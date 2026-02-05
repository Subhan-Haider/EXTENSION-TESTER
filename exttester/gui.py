import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QTextEdit, QFileDialog, QLabel, QProgressBar,
    QTableWidget, QTableWidgetItem, QMessageBox, QTabWidget, QScrollArea,
    QCheckBox, QGroupBox, QGridLayout, QComboBox, QFrame, QHeaderView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QColor, QFont, QPalette
import os
import html
import webbrowser
from .report_generator import generate_reports
from .performance_metrics import collect_metrics
from .security_scanner import scan_extension
from .validator import ExtensionValidator, validate_all_extensions, BrowserType
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestWorkerThread(QThread):
    """Worker thread for running extension tests without blocking GUI"""
    finished = pyqtSignal()
    update_progress = pyqtSignal(str)
    update_results = pyqtSignal(dict)
    
    def __init__(self, path: str, test_all: bool = False, browsers: list = None):
        super().__init__()
        self.path = path
        self.test_all = test_all
        self.browsers = browsers or [BrowserType.CHROME]
    
    def run(self):
        try:
            if self.test_all:
                self.update_progress.emit("Scanning extensions...")
                results = validate_all_extensions(self.path)
                self.update_results.emit(results)
            else:
                self.update_progress.emit("Testing extension...")
                results = {}
                for browser in self.browsers:
                    self.update_progress.emit(f"Testing for {browser}...")
                    validator = ExtensionValidator(browser)
                    is_valid, errors, warnings = validator.validate_extension(self.path, browser)
                    ext_name = Path(self.path).name
                    key = f"{ext_name} ({browser})"
                    results[key] = (is_valid, errors, warnings, validator.detected_browsers)
                self.update_results.emit(results)
            
            self.finished.emit()
        except Exception as e:
            self.update_progress.emit(f"Error: {str(e)}")
            self.finished.emit()


class BrowserExtensionTester(QMainWindow):
    """Main GUI application for testing browser extensions"""
    
    def __init__(self):
        super().__init__()
        self.worker_thread = None
        self.last_test = None
        self.last_results = None
        self.last_report_paths = None
        self.selected_browsers = {
            BrowserType.CHROME: True,
            BrowserType.FIREFOX: True,
            BrowserType.EDGE: True,
            BrowserType.OPERA: True,
        }
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Browser Extension Tester")
        self.setGeometry(100, 100, 1280, 780)
        self._apply_theme()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)
        
        # Header
        header = QFrame()
        header.setObjectName("headerCard")
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(18, 14, 18, 14)
        header_layout.setSpacing(6)
        
        title = QLabel("Browser Extension Tester")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Validate Chrome, Firefox, Edge, and Opera extensions with clear diagnostics.")
        subtitle.setObjectName("subtitleLabel")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header.setLayout(header_layout)
        main_layout.addWidget(header)
        
        # Browser selection group
        browser_group = QGroupBox("Target Browsers")
        browser_group.setObjectName("groupCard")
        browser_layout = QHBoxLayout()
        browser_layout.setSpacing(12)
        
        self.browser_checkboxes = {}
        for browser in [BrowserType.CHROME, BrowserType.FIREFOX, BrowserType.EDGE, BrowserType.OPERA]:
            cb = QCheckBox(browser)
            cb.setChecked(self.selected_browsers.get(browser, True))
            cb.stateChanged.connect(lambda state, b=browser: self.update_browser_selection(b, state))
            cb.setObjectName("browserCheck")
            self.browser_checkboxes[browser] = cb
            browser_layout.addWidget(cb)
        
        browser_group.setLayout(browser_layout)
        main_layout.addWidget(browser_group)
        
        # Action bar
        action_bar = QFrame()
        action_bar.setObjectName("actionBar")
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(12, 8, 12, 8)
        action_layout.setSpacing(10)
        
        self.single_test_btn = QPushButton("Test Single Extension")
        self.single_test_btn.clicked.connect(self.test_single_extension)
        self.single_test_btn.setObjectName("primaryButton")
        action_layout.addWidget(self.single_test_btn)
        
        self.batch_test_btn = QPushButton("Test All Extensions in Folder")
        self.batch_test_btn.clicked.connect(self.test_all_extensions)
        self.batch_test_btn.setObjectName("secondaryButton")
        action_layout.addWidget(self.batch_test_btn)

        self.refresh_test_btn = QPushButton("Refresh / Test Again")
        self.refresh_test_btn.clicked.connect(self.refresh_last_test)
        self.refresh_test_btn.setObjectName("ghostButton")
        self.refresh_test_btn.setEnabled(False)
        action_layout.addWidget(self.refresh_test_btn)

        self.export_btn = QPushButton("Export Report")
        self.export_btn.clicked.connect(self.export_report)
        self.export_btn.setObjectName("secondaryButton")
        self.export_btn.setEnabled(False)
        action_layout.addWidget(self.export_btn)

        self.open_report_btn = QPushButton("Open Last Report")
        self.open_report_btn.clicked.connect(self.open_last_report)
        self.open_report_btn.setObjectName("ghostButton")
        self.open_report_btn.setEnabled(False)
        action_layout.addWidget(self.open_report_btn)
        
        action_layout.addStretch(1)
        action_bar.setLayout(action_layout)
        main_layout.addWidget(action_bar)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setObjectName("progressBar")
        main_layout.addWidget(self.progress_bar)
        
        # Tabs for results
        self.tabs = QTabWidget()
        self.tabs.setObjectName("resultTabs")
        main_layout.addWidget(self.tabs)
        
        # Summary tab
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setObjectName("summaryText")
        self.tabs.addTab(self.summary_text, "Summary")
        
        # Detailed results tab
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(
            ["Extension Name", "Status", "Errors", "Warnings", "Compatible Browsers"]
        )
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setObjectName("resultsTable")
        self.tabs.addTab(self.results_table, "Detailed Results")
        
        # Full report tab
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setObjectName("reportText")
        self.tabs.addTab(self.report_text, "Full Report")
        
        central_widget.setLayout(main_layout)

    def _apply_theme(self):
        font = QFont("Segoe UI", 10)
        self.setFont(font)

        base = self.palette()
        base.setColor(QPalette.Window, QColor(248, 248, 250))
        base.setColor(QPalette.Base, QColor(255, 255, 255))
        base.setColor(QPalette.Text, QColor(30, 30, 35))
        base.setColor(QPalette.Button, QColor(245, 245, 248))
        base.setColor(QPalette.ButtonText, QColor(20, 20, 25))
        self.setPalette(base)

        self.setStyleSheet("""
            QMainWindow { background: #F8F8FA; }
            QLabel#titleLabel { font-size: 22px; font-weight: 700; color: #1A1A1F; }
            QLabel#subtitleLabel { color: #5A5A66; font-size: 12px; }

            QFrame#headerCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFFFFF, stop:1 #F2F4F8);
                border: 1px solid #E3E5EA;
                border-radius: 12px;
            }
            QGroupBox#groupCard {
                border: 1px solid #E3E5EA;
                border-radius: 10px;
                margin-top: 8px;
                padding: 10px;
                background: #FFFFFF;
            }
            QGroupBox#groupCard::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                color: #4B4B57;
                font-weight: 600;
            }
            QFrame#actionBar {
                background: #FFFFFF;
                border: 1px solid #E3E5EA;
                border-radius: 10px;
            }
            QPushButton#primaryButton {
                background: #1E4DD8;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton#primaryButton:hover { background: #224FE0; }
            QPushButton#primaryButton:disabled { background: #9FB4F0; }

            QPushButton#secondaryButton {
                background: #FFFFFF;
                color: #1E4DD8;
                border: 1px solid #CBD3E3;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton#secondaryButton:hover { background: #F2F5FF; }

            QPushButton#ghostButton {
                background: transparent;
                color: #4B4B57;
                border: 1px dashed #C9CDD8;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton#ghostButton:hover { background: #F7F8FB; }

            QProgressBar#progressBar {
                border: 1px solid #E3E5EA;
                border-radius: 6px;
                height: 10px;
                background: #FFFFFF;
            }
            QProgressBar#progressBar::chunk {
                background: #1E4DD8;
                border-radius: 6px;
            }
            QTabWidget#resultTabs::pane {
                border: 1px solid #E3E5EA;
                border-radius: 10px;
                padding: 4px;
                background: #FFFFFF;
            }
            QTabBar::tab {
                background: #F4F6FA;
                border: 1px solid #E3E5EA;
                padding: 6px 12px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
                color: #4B4B57;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                color: #1E4DD8;
                font-weight: 600;
            }
            QTextEdit#summaryText, QTextEdit#reportText {
                border: none;
                padding: 8px;
                background: #FFFFFF;
            }
            QTableWidget#resultsTable {
                border: none;
                background: #FFFFFF;
                gridline-color: #EEF0F4;
            }
            QHeaderView::section {
                background: #F4F6FA;
                border: none;
                padding: 6px;
                color: #4B4B57;
                font-weight: 600;
            }
            QCheckBox#browserCheck {
                padding: 4px 8px;
            }
        """)
    
    def update_browser_selection(self, browser: str, state):
        """Update selected browsers"""
        self.selected_browsers[browser] = state == Qt.Checked
    
    def test_single_extension(self):
        """Browse and test a single extension folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Extension Folder",
            "",
            options=QFileDialog.ShowDirsOnly
        )
        
        if folder:
            selected_browsers = [b for b, selected in self.selected_browsers.items() if selected]
            if not selected_browsers:
                QMessageBox.warning(self, "No Browsers Selected", "Please select at least one browser to test")
                return
            self.run_test(folder, test_all=False, browsers=selected_browsers)
    
    def test_all_extensions(self):
        """Browse and test all extensions in a folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder Containing Extensions",
            "",
            options=QFileDialog.ShowDirsOnly
        )
        
        if folder:
            self.run_test(folder, test_all=True)
    
    def run_test(self, path: str, test_all: bool = False, browsers: list = None):
        """Run the test in a worker thread"""
        self.single_test_btn.setEnabled(False)
        self.batch_test_btn.setEnabled(False)
        self.refresh_test_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.open_report_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        self.last_test = {
            "path": path,
            "test_all": test_all,
            "browsers": browsers or []
        }
        self.worker_thread = TestWorkerThread(path, test_all, browsers)
        self.worker_thread.update_progress.connect(self.update_progress_text)
        self.worker_thread.update_results.connect(self.display_results)
        self.worker_thread.finished.connect(self.test_finished)
        self.worker_thread.start()
    
    def update_progress_text(self, text: str):
        """Update progress message"""
        self.summary_text.setText(text)
    
    def display_results(self, results: dict):
        """Display test results"""
        self.summary_text.clear()
        self.results_table.setRowCount(0)
        self.report_text.clear()
        
        if not results:
            self.summary_text.setText("No extensions found to test.")
            return

        self.last_results = results
        
        total_extensions = len(results)
        valid_count = sum(1 for _, data in results.items() if data[0])
        total_errors = sum(len(data[1]) for _, data in results.items())
        total_warnings = sum(len(data[2]) for _, data in results.items())
        
        # Summary
        status_line = "[OK] All tests passed!" if total_errors == 0 else "[FAIL] Issues found - see details below"
        status_color = "#16a34a" if total_errors == 0 else "#dc2626"
        summary_html = f"""
        <div style="font-size:16px;font-weight:700;margin-bottom:6px;">Extension Test Summary</div>
        <div style="color:#6b7280;margin-bottom:12px;">Overall health of your tested extensions.</div>
        <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;">
          <div style="border:1px solid #e5e7eb;border-radius:10px;padding:10px;background:#ffffff;">
            <div style="color:#6b7280;font-size:12px;">Total Extensions Tested</div>
            <div style="font-size:18px;font-weight:700;">{total_extensions}</div>
          </div>
          <div style="border:1px solid #e5e7eb;border-radius:10px;padding:10px;background:#ffffff;">
            <div style="color:#6b7280;font-size:12px;">Valid Extensions</div>
            <div style="font-size:18px;font-weight:700;">{valid_count}</div>
          </div>
          <div style="border:1px solid #e5e7eb;border-radius:10px;padding:10px;background:#ffffff;">
            <div style="color:#6b7280;font-size:12px;">Extensions with Errors</div>
            <div style="font-size:18px;font-weight:700;">{total_extensions - valid_count}</div>
          </div>
          <div style="border:1px solid #e5e7eb;border-radius:10px;padding:10px;background:#ffffff;">
            <div style="color:#6b7280;font-size:12px;">Total Warnings</div>
            <div style="font-size:18px;font-weight:700;">{total_warnings}</div>
          </div>
        </div>
        <div style="margin-top:12px;border:1px solid #e5e7eb;border-radius:10px;padding:10px;background:#ffffff;">
          <div style="color:#6b7280;font-size:12px;">Total Issues</div>
          <div style="display:flex;gap:12px;margin-top:6px;">
            <div>Errors: <strong>{total_errors}</strong></div>
            <div>Warnings: <strong>{total_warnings}</strong></div>
          </div>
          <div style="margin-top:8px;font-weight:700;color:{status_color};">Status: {status_line}</div>
        </div>
        """
        self.summary_text.setHtml(summary_html)
        
        # Detailed results table
        self.results_table.setRowCount(len(results))
        
        html_blocks = []
        html_blocks.append("""
        <div style="font-size:16px;font-weight:700;margin-bottom:6px;">Detailed Test Report</div>
        <div style="color:#6b7280;margin-bottom:12px;">Each entry shows status, compatibility, then errors/warnings.</div>
        """)
        
        row = 0
        for ext_name in sorted(results.keys()):
            data = results[ext_name]
            is_valid, errors, warnings = data[0], data[1], data[2]
            compatible_browsers = data[3] if len(data) > 3 else []
            
            status = "[OK] Valid" if is_valid else "[FAIL] Invalid"

            # Table
            self.results_table.setItem(row, 0, QTableWidgetItem(ext_name))
            status_item = QTableWidgetItem(status)
            status_item.setBackground(QColor(144, 238, 144) if is_valid else QColor(255, 99, 71))
            self.results_table.setItem(row, 1, status_item)
            self.results_table.setItem(row, 2, QTableWidgetItem(str(len(errors))))
            self.results_table.setItem(row, 3, QTableWidgetItem(str(len(warnings))))
            
            browsers_str = ", ".join(compatible_browsers) if compatible_browsers else "Unknown"
            self.results_table.setItem(row, 4, QTableWidgetItem(browsers_str))

            # Full report (HTML)
            safe_name = html.escape(ext_name)
            safe_status = html.escape(status)
            safe_compat = html.escape(", ".join(compatible_browsers)) if compatible_browsers else "Unknown"
            status_color = "#16a34a" if is_valid else "#dc2626"

            error_lines = ""
            if errors:
                error_items = "".join(
                    f"<li>{html.escape(str(e))}</li>" for e in errors
                )
                error_lines = f"""
                    <div style="margin-top:8px;">
                      <div style="font-weight:600;color:#b91c1c;">Errors ({len(errors)}):</div>
                      <ul style="margin:6px 0 0 18px;">{error_items}</ul>
                    </div>
                """

            warning_lines = ""
            if warnings:
                warning_items = "".join(
                    f"<li>{html.escape(str(w))}</li>" for w in warnings
                )
                warning_lines = f"""
                    <div style="margin-top:8px;">
                      <div style="font-weight:600;color:#b45309;">Warnings ({len(warnings)}):</div>
                      <ul style="margin:6px 0 0 18px;">{warning_items}</ul>
                    </div>
                """

            if not errors and not warnings:
                warning_lines = "<div style='margin-top:8px;color:#16a34a;font-weight:600;'>No issues found.</div>"

            html_blocks.append(f"""
            <div style="border:1px solid #e5e7eb;border-radius:10px;padding:12px;margin-bottom:12px;background:#ffffff;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div style="font-size:14px;font-weight:700;">{safe_name}</div>
                <div style="color:{status_color};font-weight:700;">{safe_status}</div>
              </div>
              <div style="color:#6b7280;margin-top:4px;">Compatible Browsers: {safe_compat}</div>
              {error_lines}
              {warning_lines}
            </div>
            """)
            
            row += 1

        self.report_text.setHtml("".join(html_blocks))
    
    def test_finished(self):
        """Called when test thread finishes"""
        self.single_test_btn.setEnabled(True)
        self.batch_test_btn.setEnabled(True)
        self.refresh_test_btn.setEnabled(self.last_test is not None)
        self.export_btn.setEnabled(self.last_results is not None)
        self.open_report_btn.setEnabled(self.last_report_paths is not None)
        self.progress_bar.setVisible(False)

    def refresh_last_test(self):
        """Re-run the most recent test without re-selecting folders"""
        if not self.last_test:
            return
        path = self.last_test["path"]
        test_all = self.last_test["test_all"]
        browsers = self.last_test["browsers"]
        if not test_all and not browsers:
            # Fallback to current UI selection if last browsers missing
            browsers = [b for b, selected in self.selected_browsers.items() if selected]
        self.run_test(path, test_all=test_all, browsers=browsers)

    def export_report(self):
        """Export last results to HTML/JSON/CSV."""
        if not self.last_results or not self.last_test:
            QMessageBox.warning(self, "No Results", "Run a test before exporting reports.")
            return
        try:
            report = self._build_report_from_results(self.last_results, self.last_test)
            out_dir = QFileDialog.getExistingDirectory(
                self,
                "Select Report Output Folder",
                str(Path("reports").resolve()),
                options=QFileDialog.ShowDirsOnly
            )
            if not out_dir:
                return
            paths = generate_reports(report, str(out_dir))
            self.last_report_paths = paths
            self.open_report_btn.setEnabled(True)
            pdf_line = f"\nPDF: {paths['pdf']}" if paths.get("pdf") else ""
            QMessageBox.information(self, "Report Exported",
                                    f"HTML: {paths['html']}\nJSON: {paths['json']}\nCSV: {paths['csv']}{pdf_line}")
            html_path = paths.get("html")
            if html_path and Path(html_path).exists():
                webbrowser.open(Path(html_path).resolve().as_uri())
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export report:\n{e}")

    def open_last_report(self):
        """Open the last generated HTML report."""
        if not self.last_report_paths:
            return
        html_path = self.last_report_paths.get("html")
        if html_path and Path(html_path).exists():
            try:
                webbrowser.open(Path(html_path).resolve().as_uri())
            except Exception as e:
                QMessageBox.critical(self, "Open Report Failed", f"Could not open report:\n{e}")

    def _build_report_from_results(self, results: dict, last_test: dict) -> dict:
        """Convert GUI results to report schema used by report_generator."""
        root = last_test.get("path", "")
        is_batch = last_test.get("test_all", False)
        report = {
            "root_folder": str(Path(root).resolve()),
            "browsers": list({k.split(" (")[-1].rstrip(")") for k in results.keys()}),
            "extensions": {}
        }
        for key, data in results.items():
            if " (" in key and key.endswith(")"):
                ext_name = key.rsplit(" (", 1)[0]
                browser = key.rsplit(" (", 1)[1].rstrip(")")
            else:
                ext_name = key
                browser = "Unknown"
            is_valid, errors, warnings = data[0], data[1], data[2]
            compatible = data[3] if len(data) > 3 else []

            ext_path = root
            if is_batch:
                ext_path = str(Path(root) / ext_name)

            ext_entry = report["extensions"].setdefault(ext_name, {
                "path": ext_path,
                "meta": {"name": ext_name},
                "performance": collect_metrics(ext_path),
                "security": scan_extension(ext_path),
                "browsers": {},
            })
            if isinstance(compatible, set):
                compatible = sorted(compatible)
            ext_entry["browsers"][browser] = {
                "valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "compatible": compatible,
            }
        report["browsers"] = sorted({b for ext in report["extensions"].values() for b in ext["browsers"].keys()})
        return report


def main():
    app = QApplication(sys.argv)
    tester = BrowserExtensionTester()
    tester.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
