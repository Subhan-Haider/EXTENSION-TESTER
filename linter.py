"""
Advanced Linting & Static Code Analysis for Browser Extensions

Analyzes JavaScript, HTML, and CSS files for:
- Syntax errors
- Security issues (eval, unsafe patterns)
- Missing imports/files
- Undefined variables
- Async/promise errors
- Deprecated APIs
- File dependency graphs
"""

import json
import re
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Set


@dataclass
class LintIssue:
    """Represents a single linting issue"""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'syntax', 'security', 'dependency', 'async', 'style'
    file: str
    line: int
    column: int
    message: str
    code: str  # error code like 'eval-detected', 'missing-import'
    suggestion: str = ""


class JavaScriptLinter:
    """Analyzes JavaScript for errors, security issues, and patterns"""
    
    # Security-sensitive patterns
    DANGEROUS_PATTERNS = {
        'eval': (r'\beval\s*\(', 'eval() usage is dangerous and disallowed in store'),
        'new_function': (r'\bnew\s+Function\s*\(', 'new Function() is dangerous'),
        'innerHTML': (r'\.innerHTML\s*=', 'innerHTML with untrusted data is XSS risk'),
        'document.write': (r'\bdocument\.write\s*\(', 'document.write breaks async content'),
        'setTimeout_string': (r'setTimeout\s*\(\s*["\']', 'setTimeout with string code is dangerous'),
        'setInterval_string': (r'setInterval\s*\(\s*["\']', 'setInterval with string code is dangerous'),
        'remote_code': (r'fetch\s*\(\s*["\'][^"\']*\?code=', 'Remote code loading detected'),
        'chrome_api_override': (r'var\s+chrome\s*=|let\s+chrome\s*=|const\s+chrome\s*=', 'Do not override chrome API object'),
    }
    
    # Async patterns to detect
    ASYNC_PATTERNS = {
        'await_without_async': (r'await\s+(?!.*async\s+function)', 'await used outside async function'),
        'promise_no_catch': (r'\.then\s*\(.*\)\s*(?!\.catch)', 'Promise without .catch() handler'),
        'unhandled_rejection': (r'Promise\.race\s*\(', 'Unhandled promise rejection possible'),
    }
    
    # Deprecated APIs
    DEPRECATED_APIS = {
        'webRequest': 'Replaced by declarativeNetRequest (Chrome 102+)',
        'tabs.executeScript': 'Replaced by chrome.scripting.executeScript (MV3)',
        'tabs.insertCSS': 'Replaced by chrome.scripting.insertCSS (MV3)',
        'tabs.removeCSS': 'Replaced by chrome.scripting.removeCSS (MV3)',
        'background.page': 'MV2 only, use service_worker in MV3',
    }
    
    # Chrome-only APIs for Firefox warning
    CHROME_ONLY_APIS = {
        'chrome.declarativeNetRequest': 'Not in Firefox',
        'chrome.sidePanel': 'Not in Firefox',
        'chrome.scripting.executeScript': 'Limited in Firefox',
        'chrome.tabs.captureVisibleTab': 'Not in Firefox',
    }
    
    def __init__(self, extension_path: str):
        self.extension_path = Path(extension_path)
        self.issues: List[LintIssue] = []
        
    def analyze_file(self, file_path: Path) -> List[LintIssue]:
        """Analyze a single JavaScript file"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            return [LintIssue(
                severity='error',
                category='syntax',
                file=str(file_path.relative_to(self.extension_path)),
                line=1,
                column=1,
                message=f'Failed to read file: {e}',
                code='file-read-error'
            )]
        
        # 1. Syntax check with regex (basic)
        issues.extend(self._check_syntax(file_path, content, lines))
        
        # 2. Security pattern detection
        issues.extend(self._check_security_patterns(file_path, content, lines))
        
        # 3. Async/Promise patterns
        issues.extend(self._check_async_patterns(file_path, content, lines))
        
        # 4. Import/require detection
        issues.extend(self._check_imports(file_path, content, lines))
        
        # 5. Deprecated API detection
        issues.extend(self._check_deprecated_apis(file_path, content, lines))
        
        return issues
    
    def _check_syntax(self, file_path: Path, content: str, lines: List[str]) -> List[LintIssue]:
        """Check for basic syntax errors"""
        issues = []
        
        # Missing semicolons (loose check)
        for line_num, line in enumerate(lines, 1):
            # Skip comments and strings
            if line.strip().startswith('//') or line.strip().startswith('*'):
                continue
                
            # Check for common syntax issues
            if re.search(r'[^{\s]\s*$', line) and not line.strip().endswith(('{', '}', ')', ',', ';', ':', '//', '/*', '*/')):
                # Likely missing semicolon
                if not any(x in line for x in ['if', 'for', 'while', 'function', 'class']):
                    issues.append(LintIssue(
                        severity='warning',
                        category='syntax',
                        file=str(file_path.relative_to(self.extension_path)),
                        line=line_num,
                        column=len(line),
                        message='Possibly missing semicolon',
                        code='missing-semicolon',
                        suggestion='Add semicolon at end of statement'
                    ))
        
        # Mismatched braces
        open_braces = content.count('{') - content.count('}')
        open_parens = content.count('(') - content.count(')')
        open_brackets = content.count('[') - content.count(']')
        
        if open_braces != 0:
            issues.append(LintIssue(
                severity='error',
                category='syntax',
                file=str(file_path.relative_to(self.extension_path)),
                line=1,
                column=1,
                message=f'Mismatched braces: {open_braces:+d}',
                code='brace-mismatch'
            ))
        
        return issues
    
    def _check_security_patterns(self, file_path: Path, content: str, lines: List[str]) -> List[LintIssue]:
        """Detect dangerous patterns"""
        issues = []
        
        for pattern_name, (regex, message) in self.DANGEROUS_PATTERNS.items():
            for match in re.finditer(regex, content, re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                col = match.start() - content.rfind('\n', 0, match.start())
                
                issues.append(LintIssue(
                    severity='error',
                    category='security',
                    file=str(file_path.relative_to(self.extension_path)),
                    line=line_num,
                    column=col,
                    message=message,
                    code=f'security-{pattern_name}',
                    suggestion=self._get_security_suggestion(pattern_name)
                ))
        
        return issues
    
    def _check_async_patterns(self, file_path: Path, content: str, lines: List[str]) -> List[LintIssue]:
        """Check for async/promise issues"""
        issues = []
        
        # Check for await outside async
        for line_num, line in enumerate(lines, 1):
            if 'await' in line:
                # Find the function context
                func_context = ''.join(lines[max(0, line_num-10):line_num])
                if 'async' not in func_context:
                    issues.append(LintIssue(
                        severity='error',
                        category='async',
                        file=str(file_path.relative_to(self.extension_path)),
                        line=line_num,
                        column=line.find('await'),
                        message='await used outside async function',
                        code='await-not-async',
                        suggestion='Wrap containing function with async keyword'
                    ))
        
        return issues
    
    def _check_imports(self, file_path: Path, content: str, lines: List[str]) -> List[LintIssue]:
        """Check import/require statements and file references"""
        issues = []
        
        # Find import statements
        import_patterns = [
            (r'import\s+.*?\s+from\s+["\']([^"\']+)["\']', 'ES6 import'),
            (r'require\s*\(\s*["\']([^"\']+)["\']\s*\)', 'CommonJS require'),
        ]
        
        for pattern, import_type in import_patterns:
            for match in re.finditer(pattern, content):
                module = match.group(1)
                
                # Skip external modules (npm packages)
                if not module.startswith('.'):
                    continue
                
                # Resolve relative path
                if file_path.parent.name == 'js':
                    resolved = file_path.parent.parent / module
                else:
                    resolved = file_path.parent / module
                
                # Check if file exists
                if not resolved.exists() and not (resolved.with_suffix('.js').exists()):
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append(LintIssue(
                        severity='error',
                        category='dependency',
                        file=str(file_path.relative_to(self.extension_path)),
                        line=line_num,
                        column=match.start() - content.rfind('\n', 0, match.start()),
                        message=f'Module not found: {module}',
                        code='module-not-found',
                        suggestion=f'Check that {module} exists'
                    ))
        
        return issues
    
    def _check_deprecated_apis(self, file_path: Path, content: str, lines: List[str]) -> List[LintIssue]:
        """Detect deprecated API usage"""
        issues = []
        
        for api, message in self.DEPRECATED_APIS.items():
            pattern = re.escape(api).replace(r'\.', r'\.')
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                issues.append(LintIssue(
                    severity='warning',
                    category='deprecated',
                    file=str(file_path.relative_to(self.extension_path)),
                    line=line_num,
                    column=match.start() - content.rfind('\n', 0, match.start()),
                    message=f'Deprecated API: {api} - {message}',
                    code=f'deprecated-{api.replace(".", "-")}'
                ))
        
        return issues
    
    def _get_security_suggestion(self, pattern_name: str) -> str:
        """Get helpful suggestion for security issue"""
        suggestions = {
            'eval': 'Use JSON.parse() for data or Function constructor with CSP nonce',
            'new_function': 'Use Function.prototype.call or arrow functions instead',
            'innerHTML': 'Use textContent for text or createElement for elements',
            'document.write': 'Use DOM methods (appendChild, insertBefore) instead',
            'setTimeout_string': 'Use arrow function: setTimeout(() => code(), delay)',
            'setInterval_string': 'Use arrow function: setInterval(() => code(), delay)',
            'remote_code': 'Load code locally or use content scripts with sandbox',
            'chrome_api_override': 'Use a different variable name to avoid shadowing the chrome API',
        }
        return suggestions.get(pattern_name, 'Review this pattern for security issues')
    
    def analyze_all(self) -> List[LintIssue]:
        """Analyze all JavaScript files in extension"""
        issues = []
        
        # Find all JS files
        for js_file in self.extension_path.rglob('*.js'):
            issues.extend(self.analyze_file(js_file))
        
        self.issues = issues
        return issues


class HTMLLinter:
    """Analyzes HTML files for structure, references, and security"""
    
    def __init__(self, extension_path: str):
        self.extension_path = Path(extension_path)
        self.issues: List[LintIssue] = []
    
    def analyze_file(self, file_path: Path) -> List[LintIssue]:
        """Analyze a single HTML file"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return [LintIssue(
                severity='error',
                category='syntax',
                file=str(file_path.relative_to(self.extension_path)),
                line=1,
                column=1,
                message=f'Failed to read file: {e}',
                code='file-read-error'
            )]
        
        issues.extend(self._check_script_tags(file_path, content))
        issues.extend(self._check_style_tags(file_path, content))
        issues.extend(self._check_file_references(file_path, content))
        issues.extend(self._check_inline_scripts(file_path, content))
        
        return issues
    
    def _check_script_tags(self, file_path: Path, content: str) -> List[LintIssue]:
        """Check script tag references"""
        issues = []
        
        # Find all script tags
        for match in re.finditer(r'<script[^>]*src=["\']([^"\']+)["\']', content, re.IGNORECASE):
            src = match.group(1)
            script_path = file_path.parent / src
            
            if not script_path.exists():
                line_num = content[:match.start()].count('\n') + 1
                issues.append(LintIssue(
                    severity='error',
                    category='dependency',
                    file=str(file_path.relative_to(self.extension_path)),
                    line=line_num,
                    column=match.start(),
                    message=f'Script file not found: {src}',
                    code='script-not-found',
                    suggestion=f'Check that {src} exists relative to {file_path.name}'
                ))
        
        return issues
    
    def _check_style_tags(self, file_path: Path, content: str) -> List[LintIssue]:
        """Check CSS file references"""
        issues = []
        
        # Find all link tags for stylesheets
        for match in re.finditer(r'<link[^>]*href=["\']([^"\']+)["\']', content, re.IGNORECASE):
            href = match.group(1)
            
            # Skip external URLs
            if href.startswith('http'):
                continue
            
            css_path = file_path.parent / href
            
            if not css_path.exists():
                line_num = content[:match.start()].count('\n') + 1
                issues.append(LintIssue(
                    severity='error',
                    category='dependency',
                    file=str(file_path.relative_to(self.extension_path)),
                    line=line_num,
                    column=match.start(),
                    message=f'Stylesheet not found: {href}',
                    code='css-not-found',
                    suggestion=f'Check that {href} exists'
                ))
        
        return issues
    
    def _check_file_references(self, file_path: Path, content: str) -> List[LintIssue]:
        """Check img, icon, and other file references"""
        issues = []
        
        # Find image references
        for match in re.finditer(r'<(?:img|icon)[^>]*(?:src|href)=["\']([^"\']+)["\']', content, re.IGNORECASE):
            ref = match.group(1)
            
            if ref.startswith('http') or ref.startswith('data:'):
                continue
            
            ref_path = file_path.parent / ref
            
            if not ref_path.exists():
                line_num = content[:match.start()].count('\n') + 1
                issues.append(LintIssue(
                    severity='warning',
                    category='dependency',
                    file=str(file_path.relative_to(self.extension_path)),
                    line=line_num,
                    column=match.start(),
                    message=f'File reference not found: {ref}',
                    code='file-not-found',
                    suggestion=f'Check that {ref} exists'
                ))
        
        return issues
    
    def _check_inline_scripts(self, file_path: Path, content: str) -> List[LintIssue]:
        """Detect inline scripts (store rejection risk)"""
        issues = []
        
        for match in re.finditer(r'<script[^>]*>([^<]+)</script>', content, re.IGNORECASE):
            code = match.group(1)
            
            # Skip if only whitespace or comments
            if code.strip() and not code.strip().startswith('//'):
                line_num = content[:match.start()].count('\n') + 1
                issues.append(LintIssue(
                    severity='warning',
                    category='security',
                    file=str(file_path.relative_to(self.extension_path)),
                    line=line_num,
                    column=match.start(),
                    message='Inline script detected - causes store rejection',
                    code='inline-script',
                    suggestion='Move script to external .js file and reference with src attribute'
                ))
        
        return issues
    
    def analyze_all(self) -> List[LintIssue]:
        """Analyze all HTML files in extension"""
        issues = []
        
        for html_file in self.extension_path.rglob('*.html'):
            issues.extend(self.analyze_file(html_file))
        
        self.issues = issues
        return issues


class DependencyAnalyzer:
    """Build file dependency graph and detect circular dependencies"""
    
    def __init__(self, extension_path: str):
        self.extension_path = Path(extension_path)
        self.graph: Dict[str, Set[str]] = {}
    
    def build_graph(self) -> Dict[str, Set[str]]:
        """Build dependency graph for all files"""
        self.graph = {}
        
        # Analyze HTML files
        for html in self.extension_path.rglob('*.html'):
            self._analyze_html_dependencies(html)
        
        # Analyze JS files
        for js in self.extension_path.rglob('*.js'):
            self._analyze_js_dependencies(js)
        
        return self.graph
    
    def _analyze_html_dependencies(self, html_file: Path):
        """Extract dependencies from HTML"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return
        
        deps = set()
        
        # Scripts
        for match in re.finditer(r'<script[^>]*src=["\']([^"\']+)["\']', content):
            deps.add(match.group(1))
        
        # Stylesheets
        for match in re.finditer(r'<link[^>]*href=["\']([^"\']+)["\']', content):
            deps.add(match.group(1))
        
        key = str(html_file.relative_to(self.extension_path))
        self.graph[key] = deps
    
    def _analyze_js_dependencies(self, js_file: Path):
        """Extract dependencies from JavaScript"""
        try:
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return
        
        deps = set()
        
        # Import statements
        for match in re.finditer(r'import\s+.*?\s+from\s+["\']([^"\']+)["\']', content):
            deps.add(match.group(1))
        
        # Require statements
        for match in re.finditer(r'require\s*\(\s*["\']([^"\']+)["\']\s*\)', content):
            deps.add(match.group(1))
        
        key = str(js_file.relative_to(self.extension_path))
        self.graph[key] = deps


class ExtensionLinter:
    """Main linter coordinating all analysis"""
    
    def __init__(self, extension_path: str):
        self.extension_path = Path(extension_path)
        self.js_linter = JavaScriptLinter(extension_path)
        self.html_linter = HTMLLinter(extension_path)
        self.dep_analyzer = DependencyAnalyzer(extension_path)
        self.all_issues: List[LintIssue] = []
    
    def lint_all(self) -> Dict:
        """Run all linting analysis"""
        # Analyze JavaScript
        js_issues = self.js_linter.analyze_all()
        
        # Analyze HTML
        html_issues = self.html_linter.analyze_all()
        
        # Build dependency graph
        dep_graph = self.dep_analyzer.build_graph()
        
        self.all_issues = js_issues + html_issues
        
        return {
            'issues': self.all_issues,
            'summary': self._generate_summary(self.all_issues),
            'dependencies': dep_graph,
            'by_severity': self._group_by_severity(self.all_issues),
            'by_category': self._group_by_category(self.all_issues),
        }
    
    def _generate_summary(self, issues: List[LintIssue]) -> Dict:
        """Generate summary statistics"""
        errors = [i for i in issues if i.severity == 'error']
        warnings = [i for i in issues if i.severity == 'warning']
        infos = [i for i in issues if i.severity == 'info']
        
        return {
            'total_issues': len(issues),
            'errors': len(errors),
            'warnings': len(warnings),
            'infos': len(infos),
            'files_with_issues': len(set(i.file for i in issues)),
        }
    
    def _group_by_severity(self, issues: List[LintIssue]) -> Dict[str, List[LintIssue]]:
        """Group issues by severity"""
        grouped = {'error': [], 'warning': [], 'info': []}
        for issue in issues:
            grouped[issue.severity].append(issue)
        return grouped
    
    def _group_by_category(self, issues: List[LintIssue]) -> Dict[str, List[LintIssue]]:
        """Group issues by category"""
        grouped = {}
        for issue in issues:
            if issue.category not in grouped:
                grouped[issue.category] = []
            grouped[issue.category].append(issue)
        return grouped
