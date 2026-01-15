"""
Tests for job matching service.
"""
import pytest
from app.services.matcher import MatchingService


class TestSkillExtraction:
    """Test skill extraction from text."""
    
    def test_extract_tech_skills(self):
        """Test extracting tech skills from text."""
        text = "I have experience with Python, JavaScript, and React"
        tech_skills, soft_skills = MatchingService.extract_skills_from_text(text)
        
        assert "python" in tech_skills
        assert "javascript" in tech_skills
        assert "react" in tech_skills
    
    def test_extract_soft_skills(self):
        """Test extracting soft skills from text."""
        text = "Strong communication and leadership skills with excellent teamwork"
        tech_skills, soft_skills = MatchingService.extract_skills_from_text(text)
        
        assert "communication" in soft_skills
        assert "leadership" in soft_skills
        assert "teamwork" in soft_skills
    
    def test_extract_mixed_skills(self):
        """Test extracting both tech and soft skills."""
        text = "Python developer with strong communication and Docker experience"
        tech_skills, soft_skills = MatchingService.extract_skills_from_text(text)
        
        assert "python" in tech_skills
        assert "docker" in tech_skills
        assert "communication" in soft_skills
    
    def test_extract_no_skills(self):
        """Test extraction with no matching skills."""
        text = "Some random text without any skills"
        tech_skills, soft_skills = MatchingService.extract_skills_from_text(text)
        
        assert len(tech_skills) == 0
        assert len(soft_skills) == 0


class TestTFIDFSimilarity:
    """Test TF-IDF similarity computation."""
    
    def test_identical_texts(self):
        """Test similarity of identical texts."""
        text = "Python developer with FastAPI experience"
        similarity = MatchingService.compute_tf_idf_similarity(text, text)
        
        # Use approximate comparison for floating point
        assert abs(similarity - 1.0) < 0.0001
    
    def test_similar_texts(self):
        """Test similarity of similar texts."""
        resume = "Python developer with FastAPI and PostgreSQL experience"
        job = "Looking for Python developer with FastAPI skills"
        similarity = MatchingService.compute_tf_idf_similarity(resume, job)
        
        # Similar texts should have positive similarity
        assert 0.3 < similarity < 1.0
    
    def test_dissimilar_texts(self):
        """Test similarity of dissimilar texts."""
        resume = "Accountant with Excel and QuickBooks"
        job = "Python developer with FastAPI experience"
        similarity = MatchingService.compute_tf_idf_similarity(resume, job)
        
        assert 0 <= similarity < 0.5
    
    def test_empty_text(self):
        """Test similarity with empty text."""
        similarity = MatchingService.compute_tf_idf_similarity("", "Some text")
        assert similarity == 0.0
    
    def test_none_text(self):
        """Test similarity with None text."""
        similarity = MatchingService.compute_tf_idf_similarity(None, "Some text")
        assert similarity == 0.0


class TestSkillOverlap:
    """Test skill overlap computation."""
    
    def test_perfect_overlap(self):
        """Test perfect skill overlap."""
        resume_skills = ["python", "javascript", "react"]
        job_skills = ["python", "javascript", "react"]
        
        overlap, missing = MatchingService.compute_skill_overlap(resume_skills, job_skills)
        
        assert overlap == 1.0
        assert len(missing) == 0
    
    def test_partial_overlap(self):
        """Test partial skill overlap."""
        resume_skills = ["python", "javascript"]
        job_skills = ["python", "javascript", "react", "typescript"]
        
        overlap, missing = MatchingService.compute_skill_overlap(resume_skills, job_skills)
        
        assert 0.4 < overlap < 0.6
        assert "react" in missing
        assert "typescript" in missing
    
    def test_no_overlap(self):
        """Test no skill overlap."""
        resume_skills = ["python", "javascript"]
        job_skills = ["java", "c++", "rust"]
        
        overlap, missing = MatchingService.compute_skill_overlap(resume_skills, job_skills)
        
        assert overlap == 0.0
        assert len(missing) == 3
    
    def test_empty_job_skills(self):
        """Test with empty job skills."""
        resume_skills = ["python", "javascript"]
        job_skills = []
        
        overlap, missing = MatchingService.compute_skill_overlap(resume_skills, job_skills)
        
        assert overlap == 1.0
        assert len(missing) == 0
    
    def test_case_insensitive(self):
        """Test case-insensitive skill matching."""
        resume_skills = ["Python", "JavaScript"]
        job_skills = ["python", "javascript"]
        
        overlap, missing = MatchingService.compute_skill_overlap(resume_skills, job_skills)
        
        assert overlap == 1.0


class TestLocationBonus:
    """Test location/remote preference bonus."""
    
    def test_remote_preference_match(self):
        """Test remote preference match bonus."""
        bonus = MatchingService.compute_location_bonus(
            user_location=None,
            user_remote_preference="remote",
            job_location=None,
            job_work_type="remote",
        )
        
        assert bonus == 0.15
    
    def test_hybrid_preference_match(self):
        """Test hybrid preference match bonus."""
        bonus = MatchingService.compute_location_bonus(
            user_location=None,
            user_remote_preference="hybrid",
            job_location=None,
            job_work_type="hybrid",
        )
        
        assert bonus == 0.10
    
    def test_location_match(self):
        """Test location match bonus."""
        bonus = MatchingService.compute_location_bonus(
            user_location="San Francisco",
            user_remote_preference=None,
            job_location="San Francisco, CA",
            job_work_type="full-time",
        )
        
        assert bonus == 0.05
    
    def test_no_match(self):
        """Test no location/remote match."""
        bonus = MatchingService.compute_location_bonus(
            user_location="New York",
            user_remote_preference="full-time",
            job_location="San Francisco",
            job_work_type="remote",
        )
        
        assert bonus == 0.0
    
    def test_max_bonus(self):
        """Test maximum bonus (remote + location)."""
        bonus = MatchingService.compute_location_bonus(
            user_location="San Francisco",
            user_remote_preference="remote",
            job_location="San Francisco",
            job_work_type="remote",
        )
        
        assert bonus == 0.20


class TestMatchScore:
    """Test overall match score computation."""
    
    def test_perfect_match(self):
        """Test perfect match scenario."""
        result = MatchingService.compute_match_score(
            resume_text="Python developer with FastAPI and PostgreSQL",
            job_description="Python developer with FastAPI and PostgreSQL",
            resume_skills=["python", "fastapi", "postgresql"],
            job_skills=["python", "fastapi", "postgresql"],
            user_location="San Francisco",
            user_remote_preference="remote",
            job_location="San Francisco",
            job_work_type="remote",
        )
        
        assert result['match_score'] > 90
        assert len(result['why']['strengths']) > 0
        assert len(result['missing_skills']) == 0
    
    def test_poor_match(self):
        """Test poor match scenario."""
        result = MatchingService.compute_match_score(
            resume_text="Accountant with Excel skills",
            job_description="Python developer with FastAPI experience",
            resume_skills=["excel"],
            job_skills=["python", "fastapi"],
            user_location="New York",
            user_remote_preference=None,
            job_location="San Francisco",
            job_work_type="full-time",
        )
        
        assert result['match_score'] < 50
        assert len(result['why']['reasons']) > 0
        assert len(result['missing_skills']) > 0
    
    def test_score_breakdown_weights(self):
        """Test that score breakdown follows correct weights."""
        result = MatchingService.compute_match_score(
            resume_text="Python developer",
            job_description="Python developer",
            resume_skills=["python"],
            job_skills=["python"],
            user_location=None,
            user_remote_preference=None,
            job_location=None,
            job_work_type=None,
        )
        
        breakdown = result['score_breakdown']
        assert 'tf_idf' in breakdown
        assert 'skill_overlap' in breakdown
        assert 'location_bonus' in breakdown
    
    def test_score_range(self):
        """Test that score is always in 0-100 range."""
        result = MatchingService.compute_match_score(
            resume_text="Some text",
            job_description="Some other text",
            resume_skills=["skill1"],
            job_skills=["skill2"],
            user_location=None,
            user_remote_preference=None,
            job_location=None,
            job_work_type=None,
        )
        
        assert 0 <= result['match_score'] <= 100
    
    def test_explanation_structure(self):
        """Test that explanation has correct structure."""
        result = MatchingService.compute_match_score(
            resume_text="Python developer",
            job_description="Python developer",
            resume_skills=["python"],
            job_skills=["python"],
            user_location=None,
            user_remote_preference=None,
            job_location=None,
            job_work_type=None,
        )
        
        why = result['why']
        assert 'reasons' in why
        assert 'strengths' in why
        assert isinstance(why['reasons'], list)
        assert isinstance(why['strengths'], list)
