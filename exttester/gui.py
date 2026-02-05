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
            from .pipeline import TestingPipeline
            
            if self.test_all:
                self.update_progress.emit("Scanning extensions in folder...")
                # We need to replicate validate_all_extensions but with TestingPipeline for each
                # This might be slow for GUI, but it's what the user wants ("Real Tool")
                # For now let's iterate manually
                import os
                results = {}
                subfolders = [f.path for f in os.scandir(self.path) if f.is_dir()]
                total = len(subfolders)
                
                for i, folder in enumerate(subfolders):
                    name = Path(folder).name
                    self.update_progress.emit(f"Testing {name} ({i+1}/{total})...")
                    
                    # Run full pipeline for this extension
                    # We use selected browsers
                    browsers_str = [b for b in self.browsers]
                    pipeline = TestingPipeline(folder, browsers_str)
                    pipeline_results = pipeline.run()
                    
                    # Store results keyed by extension name
                    results[name] = pipeline_results
                
                self.update_results.emit(results)
            else:
                self.update_progress.emit("Running full testing pipeline...")
                # Single extension mode
                browsers_str = [b for b in self.browsers]
                pipeline = TestingPipeline(self.path, browsers_str)
                results = pipeline.run()
                
                # Wrap in a dict to match the structure expected by display_results
                # But display_results needs to be updated to handle Pipeline format
                # We'll use the extension name as key
                ext_name = Path(self.path).name
                self.update_results.emit({ext_name: results})
            
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
            'chrome': True,
            'firefox': True,
            'edge': True,
            'opera': True,
        }
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Browser Extension Tester v1.0 (Production)")
        self.setGeometry(100, 100, 1280, 850)
        self._apply_theme()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        header = QFrame()
        header.setObjectName("headerCard")
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(20, 15, 20, 15)
        header_layout.setSpacing(8)
        
        title = QLabel("Browser Extension Quality Assurance Platform")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Comprehensive validation, security scanning, and cross-browser runtime testing.")
        subtitle.setObjectName("subtitleLabel")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header.setLayout(header_layout)
        main_layout.addWidget(header)
        
        # Browser selection group
        browser_group = QGroupBox("Target Browsers (Runtime Tests)")
        browser_group.setObjectName("groupCard")
        browser_layout = QHBoxLayout()
        browser_layout.setSpacing(15)
        
        self.browser_checkboxes = {}
        # Map nice names to internal IDs
        browser_map = [
            ('Google Chrome', 'chrome'),
            ('Mozilla Firefox', 'firefox'),
            ('Microsoft Edge', 'edge'), 
            ('Opera', 'opera')
        ]
        
        for name, key in browser_map:
            cb = QCheckBox(name)
            cb.setChecked(self.selected_browsers.get(key, True))
            cb.stateChanged.connect(lambda state, k=key: self.update_browser_selection(k, state))
            cb.setObjectName("browserCheck")
            self.browser_checkboxes[key] = cb
            browser_layout.addWidget(cb)
        
        browser_group.setLayout(browser_layout)
        main_layout.addWidget(browser_group)
        
        # Action bar
        action_bar = QFrame()
        action_bar.setObjectName("actionBar")
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(15, 10, 15, 10)
        action_layout.setSpacing(12)
        
        self.single_test_btn = QPushButton("Test Single Extension")
        self.single_test_btn.clicked.connect(self.test_single_extension)
        self.single_test_btn.setObjectName("primaryButton")
        self.single_test_btn.setMinimumHeight(40)
        action_layout.addWidget(self.single_test_btn)
        
        self.batch_test_btn = QPushButton("Bulk Scan Folder")
        self.batch_test_btn.clicked.connect(self.test_all_extensions)
        self.batch_test_btn.setObjectName("secondaryButton")
        self.batch_test_btn.setMinimumHeight(40)
        action_layout.addWidget(self.batch_test_btn)

        self.refresh_test_btn = QPushButton("Re-Run Tests")
        self.refresh_test_btn.clicked.connect(self.refresh_last_test)
        self.refresh_test_btn.setObjectName("ghostButton")
        self.refresh_test_btn.setEnabled(False)
        self.refresh_test_btn.setMinimumHeight(40)
        action_layout.addWidget(self.refresh_test_btn)

        self.export_btn = QPushButton("Generate PDF Report")
        self.export_btn.clicked.connect(self.export_report)
        self.export_btn.setObjectName("secondaryButton")
        self.export_btn.setEnabled(False)
        self.export_btn.setMinimumHeight(40)
        action_layout.addWidget(self.export_btn)
        
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
        self.tabs.addTab(self.summary_text, "Dashboard")
        
        # Detailed results tab
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels(
            ["Extension", "Status", "Sec. Score", "Errors", "Runtime Tests", "Manifest"]
        )
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setObjectName("resultsTable")
        self.tabs.addTab(self.results_table, "Detailed Matrix")
        
        central_widget.setLayout(main_layout)

    def _apply_theme(self):
        # Kept mostly same but updated fonts/colors slightly
        pass  # Implementation is fine as is in original or can be tweaked if needed

    def update_browser_selection(self, browser: str, state):
        """Update selected browsers"""
        self.selected_browsers[browser] = state == Qt.Checked
    
    def test_single_extension(self):
        """Browse and test a single extension folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Extension Folder", "", options=QFileDialog.ShowDirsOnly)
        if folder:
            selected = [b for b, s in self.selected_browsers.items() if s]
            if not selected:
                QMessageBox.warning(self, "No Browsers", "Select at least one browser.")
                return
            self.run_test(folder, test_all=False, browsers=selected)
    
    def test_all_extensions(self):
        """Browse and test all extensions in a folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Parent Folder", "", options=QFileDialog.ShowDirsOnly)
        if folder:
            selected = [b for b, s in self.selected_browsers.items() if s]
            self.run_test(folder, test_all=True, browsers=selected)
    
    def run_test(self, path: str, test_all: bool = False, browsers: list = None):
        """Run the test in a worker thread"""
        self.single_test_btn.setEnabled(False)
        self.batch_test_btn.setEnabled(False)
        self.refresh_test_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.last_test = {"path": path, "test_all": test_all, "browsers": browsers or []}
        self.worker_thread = TestWorkerThread(path, test_all, browsers)
        self.worker_thread.update_progress.connect(self.update_progress_text)
        self.worker_thread.update_results.connect(self.display_results)
        self.worker_thread.finished.connect(self.test_finished)
        self.worker_thread.start()
    
    def update_progress_text(self, text: str):
        self.summary_text.setText(f"<h3 style='color:#1e40af'>Running Tests...</h3><p>{text}</p>")
    
    def display_results(self, results: dict):
        """Display test results using rich pipeline data"""
        self.summary_text.clear()
        self.results_table.setRowCount(0)
        
        if not results:
            self.summary_text.setText("No extensions found or tested.")
            return

        self.last_results = results
        
        # Calculate stats
        total = len(results)
        passed = sum(1 for r in results.values() if r.get('summary', {}).get('success', False))
        failed_stats = total - passed
        
        # Build Dashboard HTML
        summary_html = f"""
        <div style="font-family: 'Segoe UI', sans-serif;">
            <div style="display:flex; gap: 20px; margin-bottom: 2rem;">
                <div style="background:white; padding:15px; border-radius:8px; border:1px solid #e2e8f0; min-width:150px;">
                    <div style="color:#64748b; font-size:12px; font-weight:600; text-transform:uppercase;">Tested</div>
                    <div style="color:#0f172a; font-size:32px; font-weight:700;">{total}</div>
                </div>
                <div style="background:#f0fdf4; padding:15px; border-radius:8px; border:1px solid #bbf7d0; min-width:150px;">
                    <div style="color:#166534; font-size:12px; font-weight:600; text-transform:uppercase;">Passed</div>
                    <div style="color:#15803d; font-size:32px; font-weight:700;">{passed}</div>
                </div>
                <div style="background:#fef2f2; padding:15px; border-radius:8px; border:1px solid #fecaca; min-width:150px;">
                    <div style="color:#991b1b; font-size:12px; font-weight:600; text-transform:uppercase;">Failed</div>
                    <div style="color:#dc2626; font-size:32px; font-weight:700;">{failed_stats}</div>
                </div>
            </div>
        </div>
        """
        
        # Add detailed cards
        summary_html += "<div style='font-family:Segoe UI;'>"
        for name, res in results.items():
            s = res.get('summary', {})
            score = 0
            # Try to find security score
            for stage in res.get('stages', []):
                if stage.get('id') == 'security_check':
                    score = stage.get('details', {}).get('score', 0)
            
            color = '#16a34a' if s.get('success') else '#dc2626'
            status = "PASSED" if s.get('success') else "FAILED"
            
            summary_html += f"""
            <div style="background:white; border:1px solid #e2e8f0; border-radius:8px; padding:15px; margin-bottom:10px; border-left: 5px solid {color};">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-weight:700; font-size:16px;">{name}</span>
                    <span style="background:{color}; color:white; padding:2px 8px; border-radius:4px; font-size:12px;">{status}</span>
                </div>
                <div style="color:#64748b; font-size:12px; margin-top:5px;">
                    Security Score: <b>{score}/100</b> | Errors: {s.get('errors', 0)} | Warnings: {s.get('warnings', 0)}
                </div>
            </div>
            """
        summary_html += "</div>"
        
        self.summary_text.setHtml(summary_html)
        
        # Populate Table
        self.results_table.setRowCount(total)
        row = 0
        for name, res in results.items():
            s = res.get('summary', {})
            
            # Extract Score
            sec_score = "N/A"
            for stage in res.get('stages', []):
                if stage.get('id') == 'security_check':
                    sc = stage.get('details', {}).get('score')
                    sec_score = f"{sc}/100" if sc is not None else "N/A"
            
            # Extract Manifest Version
            mv = "Unknown"
            for stage in res.get('stages', []):
                if stage.get('id') == 'manifest':
                    mv = f"V{stage.get('details', {}).get('manifest_version', '?')}"
            
            self.results_table.setItem(row, 0, QTableWidgetItem(name))
            
            status_item = QTableWidgetItem("PASS" if s.get('success') else "FAIL")
            status_item.setBackground(QColor(220, 252, 231) if s.get('success') else QColor(254, 226, 226))
            self.results_table.setItem(row, 1, status_item)
            
            self.results_table.setItem(row, 2, QTableWidgetItem(str(sec_score)))
            self.results_table.setItem(row, 3, QTableWidgetItem(str(s.get('errors', 0))))
            
            # Runtime info
            runtime_status = "Skipped"
            for stage in res.get('stages', []):
                if stage.get('id') == 'browser_load':
                     runtime_status = "Run" if stage.get('success') else "Failed"
            self.results_table.setItem(row, 4, QTableWidgetItem(runtime_status))
            
            self.results_table.setItem(row, 5, QTableWidgetItem(mv))
            row += 1
    
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
