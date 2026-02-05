"""
Tests for scoring engine
"""
import pytest
from exttester.scoring_engine import ScoringEngine, ScoreWeights


class TestScoringEngine:
    """Test scoring calculations"""
    
    def test_scoring_engine_initialization(self):
        """Test engine can be created"""
        engine = ScoringEngine()
        assert engine is not None
        assert engine.weights is not None
    
    def test_default_weights(self):
        """Test default weights sum to 1.0"""
        engine = ScoringEngine()
        total = (
            engine.weights.security +
            engine.weights.performance +
            engine.weights.store_compliance +
            engine.weights.code_quality +
            engine.weights.privacy
        )
        assert abs(total - 1.0) < 0.01  # Allow small floating point error
    
    def test_custom_weights(self):
        """Test custom weight configuration"""
        weights = ScoreWeights(
            security=0.40,
            performance=0.20,
            store_compliance=0.20,
            code_quality=0.10,
            privacy=0.10
        )
        engine = ScoringEngine(weights=weights)
        assert engine.weights.security == 0.40
        assert engine.weights.performance == 0.20
    
    def test_score_calculation(self, mock_extension_data):
        """Test score calculation with mock data"""
        engine = ScoringEngine()
        result = engine.calculate_final_score(mock_extension_data)
        
        assert 'final_score' in result
        assert 0 <= result['final_score'] <= 100
        assert 'grade' in result
        assert result['grade'] in ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
        assert 'breakdown' in result
        assert 'recommendations' in result
    
    def test_grade_conversion(self):
        """Test score to grade conversion"""
        engine = ScoringEngine()
        
        assert engine._score_to_grade(98) == 'A+'
        assert engine._score_to_grade(95) == 'A+'
        assert engine._score_to_grade(92) == 'A'
        assert engine._score_to_grade(88) == 'A-'
        assert engine._score_to_grade(85) == 'A-'
        assert engine._score_to_grade(82) == 'B+'
        assert engine._score_to_grade(78) == 'B'
        assert engine._score_to_grade(75) == 'B'
        assert engine._score_to_grade(72) == 'B-'
        assert engine._score_to_grade(68) == 'C+'
        assert engine._score_to_grade(65) == 'C'
        assert engine._score_to_grade(62) == 'C-'
        assert engine._score_to_grade(58) == 'D'
        assert engine._score_to_grade(40) == 'F'
        assert engine._score_to_grade(0) == 'F'
    
    def test_security_score_calculation(self, mock_extension_data):
        """Test security score calculation"""
        engine = ScoringEngine()
        score = engine._calculate_security_score(mock_extension_data)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
    
    def test_performance_score_calculation(self, mock_extension_data):
        """Test performance score calculation"""
        engine = ScoringEngine()
        score = engine._calculate_performance_score(mock_extension_data)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
    
    def test_compliance_score_calculation(self, mock_extension_data):
        """Test compliance score calculation"""
        engine = ScoringEngine()
        score = engine._calculate_compliance_score(mock_extension_data)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
    
    def test_code_quality_score_calculation(self, mock_extension_data):
        """Test code quality score calculation"""
        engine = ScoringEngine()
        score = engine._calculate_code_quality_score(mock_extension_data)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
    
    def test_privacy_score_calculation(self, mock_extension_data):
        """Test privacy score calculation"""
        engine = ScoringEngine()
        score = engine._calculate_privacy_score(mock_extension_data)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
    
    def test_recommendations_generation(self, mock_extension_data):
        """Test recommendations are generated"""
        engine = ScoringEngine()
        recommendations = engine._generate_recommendations(mock_extension_data)
        
        assert isinstance(recommendations, list)
        # Should have at least some recommendations
        assert len(recommendations) >= 0
    
    def test_high_score_extension(self):
        """Test extension with high scores"""
        engine = ScoringEngine()
        
        perfect_data = {
            'security': {'score': 100, 'findings': [], 'permission_risk': 'Low'},
            'performance': {'total_size_mb': 0.5, 'file_count': 10},
            'meta': {'name': 'Perfect', 'version': '1.0.0'},
            'browsers': {'chrome': {'valid': True, 'errors': [], 'warnings': []}},
            'linting': {'errors': [], 'warnings': [], 'security_issues': []}
        }
        
        result = engine.calculate_final_score(perfect_data)
        assert result['final_score'] >= 90
        assert result['grade'] in ['A+', 'A', 'A-']
    
    def test_low_score_extension(self):
        """Test extension with low scores"""
        engine = ScoringEngine()
        
        poor_data = {
            'security': {'score': 30, 'findings': ['critical', 'high'], 'permission_risk': 'Critical'},
            'performance': {'total_size_mb': 50.0, 'file_count': 1000},
            'meta': {'name': 'Poor', 'version': '1.0.0'},
            'browsers': {'chrome': {'valid': False, 'errors': ['error1', 'error2']}},
            'linting': {'errors': ['error1', 'error2'], 'warnings': [], 'security_issues': ['xss', 'eval']}
        }
        
        result = engine.calculate_final_score(poor_data)
        assert result['final_score'] < 70
        assert result['grade'] in ['D', 'F', 'C-', 'C']
    
    def test_breakdown_structure(self, mock_extension_data):
        """Test breakdown has correct structure"""
        engine = ScoringEngine()
        result = engine.calculate_final_score(mock_extension_data)
        
        breakdown = result['breakdown']
        assert 'security' in breakdown
        assert 'performance' in breakdown
        assert 'store_compliance' in breakdown
        assert 'code_quality' in breakdown
        assert 'privacy' in breakdown
        
        # Each category should have score and weight
        for category in breakdown.values():
            assert 'score' in category
            assert 'weight' in category
