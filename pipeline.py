"""
Full Testing Pipeline Orchestrator

Coordinates 6-stage testing pipeline:
1. Static file checks
2. Manifest validation
3. Lint & syntax checks
4. Browser load test
5. Runtime behavior test
6. Compatibility analysis

Aggregates results and produces comprehensive reports
"""

import json
import time
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime

logger_enabled = True


@dataclass
class PipelineStage:
    """Represents one testing stage"""
    stage_num: int
    name: str
    description: str
    success: bool
    duration: float
    errors: List[str]
    warnings: List[str]
    details: Dict


class TestingPipeline:
    """Orchestrates complete 6-stage testing"""
    
    STAGES = [
        (1, 'Static File Checks', 'Verify all required files exist'),
        (2, 'Manifest Validation', 'Deep validation of manifest.json'),
        (3, 'Lint & Syntax Check', 'JavaScript/HTML/CSS analysis'),
        (4, 'Browser Load Test', 'Load extension in real browser'),
        (5, 'Runtime Behavior Test', 'Test popup, content scripts, background'),
        (6, 'Compatibility Analysis', 'Cross-browser API compatibility'),
    ]
    
    def __init__(self, extension_path: str, browsers: List[str] = None):
        self.extension_path = Path(extension_path)
        self.browsers = browsers or ['chrome', 'firefox', 'edge']
        self.stages: List[PipelineStage] = []
        self.start_time = None
        self.end_time = None
    
    def run(self) -> Dict:
        """Execute full testing pipeline"""
        self.start_time = time.time()
        
        results = {
            'extension': self.extension_path.name,
            'path': str(self.extension_path),
            'timestamp': datetime.now().isoformat(),
            'browsers': self.browsers,
            'stages': [],
            'summary': {}
        }
        
        # Import here to avoid circular imports
        from validator import ExtensionValidator, BrowserType
        from linter import ExtensionLinter
        from browser_tester import ExtensionBrowserTester
        from api_checker import APICompatibilityChecker
        
        # Stage 1: Static File Checks
        stage1 = self._run_stage(1, 'Static File Checks', 'Verify all required files exist',
                                self._check_static_files)
        results['stages'].append(asdict(stage1))
        
        # Stage 2: Manifest Validation
        stage2 = self._run_stage(2, 'Manifest Validation', 'Deep validation of manifest.json',
                                lambda: self._validate_manifest())
        results['stages'].append(asdict(stage2))
        
        # Stage 3: Lint & Syntax Check
        stage3 = self._run_stage(3, 'Lint & Syntax Check', 'JavaScript/HTML/CSS analysis',
                                lambda: self._lint_code())
        results['stages'].append(asdict(stage3))
        
        # Stage 4: Browser Load Test (per browser)
        stage4_results = {}
        for browser in self.browsers:
            stage4 = self._run_stage(4, f'Browser Load ({browser})', f'Load extension in {browser}',
                                    lambda b=browser: self._browser_load_test(b))
            stage4_results[browser] = asdict(stage4)
        results['stages'].append({
            'stage_num': 4,
            'name': 'Browser Load Test',
            'per_browser': stage4_results
        })
        
        # Stage 5: Runtime Behavior Test (per browser)
        stage5_results = {}
        for browser in self.browsers:
            stage5 = self._run_stage(5, f'Runtime Behavior ({browser})', f'Test extension behavior in {browser}',
                                    lambda b=browser: self._runtime_behavior_test(b))
            stage5_results[browser] = asdict(stage5)
        results['stages'].append({
            'stage_num': 5,
            'name': 'Runtime Behavior Test',
            'per_browser': stage5_results
        })
        
        # Stage 6: Compatibility Analysis
        stage6 = self._run_stage(6, 'Compatibility Analysis', 'Cross-browser API compatibility',
                                lambda: self._compatibility_analysis())
        results['stages'].append(asdict(stage6))
        
        # Calculate summary
        self.end_time = time.time()
        results['summary'] = self._calculate_summary(results)
        
        return results
    
    def _run_stage(self, num: int, name: str, description: str, test_func) -> PipelineStage:
        """Run a single testing stage"""
        start = time.time()
        errors = []
        warnings = []
        details = {}
        success = True
        
        try:
            result = test_func()
            
            if isinstance(result, dict):
                errors = result.get('errors', [])
                warnings = result.get('warnings', [])
                details = result.get('details', {})
                success = result.get('success', True)
        except Exception as e:
            errors = [str(e)]
            success = False
        
        duration = time.time() - start
        
        return PipelineStage(
            stage_num=num,
            name=name,
            description=description,
            success=success,
            duration=duration,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def _check_static_files(self) -> Dict:
        """Stage 1: Check required files"""
        errors = []
        warnings = []
        
        # Must have manifest
        manifest = self.extension_path / 'manifest.json'
        if not manifest.exists():
            errors.append('manifest.json missing')
            return {'success': False, 'errors': errors, 'warnings': warnings}
        
        # Check for basic structure
        files_found = []
        for f in self.extension_path.rglob('*'):
            if f.is_file():
                files_found.append(str(f.relative_to(self.extension_path)))
        
        # Warn if no icons
        icons = [f for f in files_found if 'icon' in f.lower()]
        if not icons:
            warnings.append('No icon files found (may be required for stores)')
        
        return {
            'success': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'details': {'files_found': len(files_found), 'icons': len(icons)}
        }
    
    def _validate_manifest(self) -> Dict:
        """Stage 2: Manifest validation"""
        from validator import ExtensionValidator, BrowserType
        from store_checker import StoreComplianceChecker
        
        try:
            validator = ExtensionValidator(BrowserType.CHROME)
            is_valid, errors, warnings = validator.validate_extension(str(self.extension_path), BrowserType.CHROME)

            store_checker = StoreComplianceChecker(str(self.extension_path))
            store_report = store_checker.check_all()

            store_warnings = []
            for store_key in ["chrome", "edge", "firefox"]:
                store_warnings.extend(store_report.get(store_key, {}).get("warnings", []))
                store_errors = store_report.get(store_key, {}).get("errors", [])
                if store_errors:
                    errors.extend(store_errors)

            privacy_warnings = store_report.get("privacy", {}).get("warnings", [])
            warnings.extend(store_warnings)
            warnings.extend(privacy_warnings)

            return {
                'success': is_valid and len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'details': {
                    'valid': is_valid,
                    'store_readiness': {
                        'chrome': store_report.get("chrome", {}).get("score", 0),
                        'edge': store_report.get("edge", {}).get("score", 0),
                        'firefox': store_report.get("firefox", {}).get("score", 0),
                    },
                    'privacy': store_report.get("privacy", {}),
                }
            }
        except Exception as e:
            return {
                'success': False,
                'errors': [str(e)],
                'warnings': [],
                'details': {}
            }
    
    def _lint_code(self) -> Dict:
        """Stage 3: Lint all code"""
        from linter import ExtensionLinter
        from size_analyzer import ExtensionSizeAnalyzer
        from dependency_checker import DependencyChecker
        from network_analyzer import NetworkBehaviorAnalyzer
        from malware_scanner import MalwareScanner
        from api_usage_scanner import APIUsageScanner
        
        linter = ExtensionLinter(str(self.extension_path))
        lint_results = linter.lint_all()
        
        issues = lint_results['issues']
        errors = [f"{i.file}:{i.line} {i.code} - {i.message}" 
                 for i in issues if i.severity == 'error']
        warnings = [f"{i.file}:{i.line} {i.code} - {i.message}" 
                   for i in issues if i.severity == 'warning']
        
        size_report = ExtensionSizeAnalyzer(str(self.extension_path)).analyze()
        dep_report = DependencyChecker(str(self.extension_path)).analyze()
        network_report = NetworkBehaviorAnalyzer(str(self.extension_path)).analyze()
        malware_report = MalwareScanner(str(self.extension_path)).scan()
        api_report = APIUsageScanner(str(self.extension_path)).analyze()

        errors.extend(size_report.get('errors', []))
        warnings.extend(size_report.get('warnings', []))
        warnings.extend(dep_report.get('warnings', []))
        warnings.extend(network_report.get('warnings', []))
        warnings.extend(malware_report.get('warnings', []))
        warnings.extend(api_report.get('deprecated', []))

        return {
            'success': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'details': {
                **lint_results['summary'],
                'size': size_report,
                'dependencies': dep_report,
                'network': network_report,
                'malware': malware_report,
                'api_usage': api_report,
            }
        }
    
    def _browser_load_test(self, browser: str) -> Dict:
        """Stage 4: Browser load test"""
        from browser_tester import ExtensionBrowserTester
        
        tester = ExtensionBrowserTester(str(self.extension_path), browser)
        result = tester.test_extension_load()
        
        return {
            'success': result.success,
            'errors': [] if result.success else [result.message],
            'warnings': result.console_warnings or [],
            'details': result.details
        }
    
    def _runtime_behavior_test(self, browser: str) -> Dict:
        """Stage 5: Runtime behavior test"""
        from browser_tester import ExtensionBrowserTester
        
        tester = ExtensionBrowserTester(str(self.extension_path), browser)
        test_results = tester.run_all_tests()
        
        errors = []
        warnings = []
        
        for r in test_results['results']:
            if not r.success:
                errors.append(r.message)
            warnings.extend(r.console_warnings or [])
        
        return {
            'success': test_results['success'],
            'errors': errors,
            'warnings': warnings,
            'details': test_results['summary']
        }
    
    def _compatibility_analysis(self) -> Dict:
        """Stage 6: Cross-browser compatibility"""
        from api_checker import APICompatibilityChecker
        
        try:
            checker = APICompatibilityChecker(str(self.extension_path))
            report = checker.generate_compatibility_report(self.browsers)
            
            errors = []
            warnings = []
            
            # report is a dict with browser names as keys
            if isinstance(report, dict):
                for browser_name, issues_list in report.items():
                    if isinstance(issues_list, list):
                        warnings.extend(issues_list)
            
            return {
                'success': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'details': {'browsers_checked': len(self.browsers)}
            }
        except Exception as e:
            return {
                'success': False,
                'errors': [str(e)],
                'warnings': [],
                'details': {}
            }
    
    def _calculate_summary(self, results: Dict) -> Dict:
        """Calculate overall summary"""
        stages = results['stages']
        total_stages = len([s for s in stages if isinstance(s, dict) and 'stage_num' in s])
        passed_stages = len([s for s in stages if isinstance(s, dict) and s.get('success', False)])
        
        total_errors = 0
        total_warnings = 0
        
        for stage in stages:
            if isinstance(stage, dict):
                total_errors += len(stage.get('errors', []))
                total_warnings += len(stage.get('warnings', []))
                if 'per_browser' in stage:
                    for browser_result in stage['per_browser'].values():
                        total_errors += len(browser_result.get('errors', []))
                        total_warnings += len(browser_result.get('warnings', []))
        
        return {
            'total_stages': total_stages,
            'passed_stages': passed_stages,
            'failed_stages': total_stages - passed_stages,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'success': passed_stages == total_stages,
            'duration': self.end_time - self.start_time if self.end_time else 0,
            'timestamp': datetime.now().isoformat()
        }


class PipelineReporter:
    """Generate reports from pipeline results"""
    
    @staticmethod
    def get_summary(results: Dict) -> str:
        """Generate human-readable summary"""
        summary = results['summary']
        
        output = f"""
═══════════════════════════════════════════════════════════════
                    TESTING PIPELINE RESULTS
═══════════════════════════════════════════════════════════════

Extension: {results['extension']}
Tested: {results['timestamp']}
Browsers: {', '.join(results['browsers'])}

Pipeline Status: {'✅ PASSED' if summary['success'] else '❌ FAILED'}

Stages: {summary['passed_stages']}/{summary['total_stages']} passed
Errors: {summary['total_errors']}
Warnings: {summary['total_warnings']}
Duration: {summary['duration']:.2f}s

Stage Results:
"""
        
        for stage in results['stages']:
            if isinstance(stage, dict):
                if 'per_browser' in stage:
                    # Multi-browser stage
                    output += f"\n  {stage['stage_num']}. {stage['name']}"
                    for browser, browser_result in stage['per_browser'].items():
                        status = '✅' if browser_result.get('success', False) else '❌'
                        output += f"\n     {browser.upper()} {status}"
                elif 'stage_num' in stage:
                    # Single result stage
                    status = '✅' if stage.get('success', False) else '❌'
                    output += f"\n  {stage['stage_num']}. {stage['name']} {status}"
                    if stage.get('errors'):
                        output += f" ({len(stage['errors'])} errors)"
                    if stage.get('warnings'):
                        output += f" ({len(stage['warnings'])} warnings)"
        
        output += "\n═══════════════════════════════════════════════════════════════\n"
        return output
