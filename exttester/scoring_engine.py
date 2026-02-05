"""
Comprehensive Scoring Engine for Browser Extensions
Calculates weighted scores across multiple categories
"""
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class ScoreWeights:
    """Category weights for final score calculation"""
    security: float = 0.30
    performance: float = 0.20
    store_compliance: float = 0.20
    code_quality: float = 0.15
    privacy: float = 0.15


class ScoringEngine:
    """
    Calculates comprehensive quality scores for browser extensions.
    
    Final Score = Weighted sum of:
    - Security (30%)
    - Performance (20%)
    - Store Compliance (20%)
    - Code Quality (15%)
    - Privacy (15%)
    """
    
    def __init__(self, weights: ScoreWeights = None):
        self.weights = weights or ScoreWeights()
    
    def calculate_final_score(self, extension_data: Dict) -> Dict:
        """
        Calculate comprehensive score from all test results.
        
        Returns:
            Dict with scores, breakdown, and grade
        """
        security_score = self._calculate_security_score(extension_data)
        performance_score = self._calculate_performance_score(extension_data)
        compliance_score = self._calculate_compliance_score(extension_data)
        code_quality_score = self._calculate_code_quality_score(extension_data)
        privacy_score = self._calculate_privacy_score(extension_data)
        
        # Weighted final score
        final_score = (
            security_score * self.weights.security +
            performance_score * self.weights.performance +
            compliance_score * self.weights.store_compliance +
            code_quality_score * self.weights.code_quality +
            privacy_score * self.weights.privacy
        )
        
        return {
            'final_score': round(final_score, 2),
            'grade': self._score_to_grade(final_score),
            'breakdown': {
                'security': {
                    'score': security_score,
                    'weight': self.weights.security,
                    'weighted': round(security_score * self.weights.security, 2)
                },
                'performance': {
                    'score': performance_score,
                    'weight': self.weights.performance,
                    'weighted': round(performance_score * self.weights.performance, 2)
                },
                'store_compliance': {
                    'score': compliance_score,
                    'weight': self.weights.store_compliance,
                    'weighted': round(compliance_score * self.weights.store_compliance, 2)
                },
                'code_quality': {
                    'score': code_quality_score,
                    'weight': self.weights.code_quality,
                    'weighted': round(code_quality_score * self.weights.code_quality, 2)
                },
                'privacy': {
                    'score': privacy_score,
                    'weight': self.weights.privacy,
                    'weighted': round(privacy_score * self.weights.privacy, 2)
                }
            },
            'recommendations': self._generate_recommendations(extension_data)
        }
    
    def _calculate_security_score(self, data: Dict) -> float:
        """Calculate security score (0-100)"""
        security = data.get('security', {})
        base_score = security.get('score', 100)
        
        # Deductions
        findings = security.get('findings', [])
        permission_findings = security.get('permission_findings', [])
        
        # Critical findings
        critical_deductions = sum(15 for f in findings if 'eval' in f.lower() or 'unsafe-eval' in f.lower())
        high_deductions = sum(10 for f in findings if 'unsafe-inline' in f.lower() or 'remote' in f.lower())
        medium_deductions = sum(5 for f in permission_findings if 'High' in f or 'Critical' in f)
        
        score = base_score - critical_deductions - high_deductions - medium_deductions
        return max(0, min(100, score))
    
    def _calculate_performance_score(self, data: Dict) -> float:
        """Calculate performance score based on size and file count"""
        perf = data.get('performance', {})
        score = 100
        
        # Size penalties
        total_size = perf.get('total_size_mb', 0)
        if total_size > 10:
            score -= 30
        elif total_size > 5:
            score -= 15
        elif total_size > 2:
            score -= 5
        
        # File count penalties
        file_count = perf.get('file_count', 0)
        if file_count > 500:
            score -= 20
        elif file_count > 200:
            score -= 10
        
        # Largest file penalty
        largest_mb = perf.get('largest_file_mb', 0)
        if largest_mb > 5:
            score -= 15
        elif largest_mb > 2:
            score -= 8
        
        return max(0, min(100, score))
    
    def _calculate_compliance_score(self, data: Dict) -> float:
        """Calculate store compliance score"""
        score = 100
        
        # Check manifest errors
        for browser_data in data.get('browsers', {}).values():
            errors = browser_data.get('errors', [])
            for error in errors:
                if 'manifest' in error.lower():
                    score -= 10
                if 'permission' in error.lower() and 'broad' in error.lower():
                    score -= 15
                if 'icon' in error.lower() and 'missing' in error.lower():
                    score -= 5
        
        # Check for required fields
        meta = data.get('meta', {})
        if not meta.get('name'):
            score -= 20
        if not meta.get('version'):
            score -= 15
        if not meta.get('description'):
            score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_code_quality_score(self, data: Dict) -> float:
        """Calculate code quality score"""
        score = 100
        
        # Count errors and warnings across all browsers
        total_errors = 0
        total_warnings = 0
        
        for browser_data in data.get('browsers', {}).values():
            total_errors += len(browser_data.get('errors', []))
            total_warnings += len(browser_data.get('warnings', []))
        
        # Deductions
        score -= total_errors * 8
        score -= total_warnings * 3
        
        # Linting issues
        security = data.get('security', {})
        findings = security.get('findings', [])
        
        # Code smell deductions
        for finding in findings:
            if 'innerHTML' in finding:
                score -= 5
            if 'document.write' in finding:
                score -= 5
        
        return max(0, min(100, score))
    
    def _calculate_privacy_score(self, data: Dict) -> float:
        """Calculate privacy compliance score"""
        score = 100
        
        security = data.get('security', {})
        findings = security.get('findings', [])
        
        # Privacy-related deductions
        for finding in findings:
            if 'privacy policy' in finding.lower():
                score -= 20
            if 'tracking' in finding.lower():
                score -= 15
            if 'analytics' in finding.lower():
                score -= 10
            if 'cookies' in finding.lower() or 'storage' in finding.lower():
                score -= 5
        
        # Permission risk
        permission_risk = security.get('permission_risk', 'Low')
        if permission_risk == 'Critical':
            score -= 30
        elif permission_risk == 'High':
            score -= 20
        elif permission_risk == 'Medium':
            score -= 10
        
        return max(0, min(100, score))
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'A-'
        elif score >= 80:
            return 'B+'
        elif score >= 75:
            return 'B'
        elif score >= 70:
            return 'B-'
        elif score >= 65:
            return 'C+'
        elif score >= 60:
            return 'C'
        elif score >= 55:
            return 'C-'
        elif score >= 50:
            return 'D'
        else:
            return 'F'
    
    def _generate_recommendations(self, data: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        security = data.get('security', {})
        perf = data.get('performance', {})
        
        # Security recommendations
        findings = security.get('findings', [])
        for finding in findings:
            if 'eval' in finding.lower():
                recommendations.append("🔴 CRITICAL: Remove eval() usage - Chrome Web Store will reject this")
            if 'unsafe-eval' in finding.lower():
                recommendations.append("🔴 CRITICAL: Remove 'unsafe-eval' from CSP")
            if 'privacy policy' in finding.lower():
                recommendations.append("⚠️ Add a privacy policy URL (required for sensitive permissions)")
        
        # Performance recommendations
        if perf.get('total_size_mb', 0) > 5:
            recommendations.append("⚡ Reduce extension size - consider minification and removing unused assets")
        
        if perf.get('largest_file_mb', 0) > 2:
            recommendations.append(f"⚡ Largest file is {perf.get('largest_file_mb')}MB - consider splitting or compressing")
        
        # Compliance recommendations
        for browser_data in data.get('browsers', {}).values():
            errors = browser_data.get('errors', [])
            for error in errors:
                if 'icon' in error.lower() and 'missing' in error.lower():
                    recommendations.append("📦 Add all required icon sizes (16x16, 48x48, 128x128)")
                    break
        
        if not recommendations:
            recommendations.append("✅ No critical issues found - extension looks good!")
        
        return recommendations
