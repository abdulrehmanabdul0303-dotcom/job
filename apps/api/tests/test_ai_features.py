"""
Comprehensive AI Features Tests for Phase 1 QA.
Tests AI-powered resume versioning, interview preparation, and skill gap analysis.
Uses mocks for deterministic testing without external AI dependencies.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, MagicMock, AsyncMock
from app.core.config import settings
from app.models.user import User
from app.models.resume import Resume
from app.models.job import JobPosting
from app.services.ai.resume_versioning import ResumeVersioningEngine
from app.services.ai.interview_prep import InterviewPreparationEngine
from app.services.ai.skill_analyzer import SkillAnalyzerEngine
from uuid import uuid4
import json


# ============================================================
# Test Fixtures
# ============================================================

@pytest.fixture
def mock_resume_data():
    """Sample parsed resume data for testing."""
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "title": "Software Engineer",
        "summary": "Experienced software engineer with 5 years of experience in Python and JavaScript.",
        "skills": ["Python", "JavaScript", "React", "Node.js", "SQL", "AWS"],
        "experience": [
            {
                "company": "Tech Corp",
                "position": "Senior Developer",
                "duration": "2020-2023",
                "description": "Led development of microservices architecture using Python and FastAPI."
            },
            {
                "company": "StartupXYZ",
                "position": "Software Engineer",
                "duration": "2018-2020",
                "description": "Built React frontend applications and Node.js backend services."
            }
        ],
        "education": [
            {
                "institution": "State University",
                "degree": "BS Computer Science",
                "year": "2018"
            }
        ],
        "projects": [
            {
                "name": "E-commerce Platform",
                "description": "Built scalable e-commerce platform",
                "technologies": ["Python", "React", "PostgreSQL"]
            }
        ]
    }


@pytest.fixture
def mock_job_requirements():
    """Sample job requirements for testing."""
    return {
        "title": "Senior Software Engineer",
        "company": "TechCorp Inc",
        "description": "We are looking for a senior software engineer with experience in Python, AWS, and microservices.",
        "requirements": "Required: Python, AWS, Docker, Kubernetes. Nice to have: Machine Learning, Go.",
        "skills": ["python", "aws", "docker", "kubernetes"],
        "keywords": ["python", "aws", "docker", "kubernetes", "microservices", "senior"]
    }


# ============================================================
# Resume Versioning Engine Tests
# ============================================================

@pytest.mark.asyncio
class TestResumeVersioningEngine:
    """Test AI Resume Versioning Engine."""
    
    async def test_engine_initialization(self):
        """Test engine initializes correctly."""
        engine = ResumeVersioningEngine()
        assert engine is not None
        assert hasattr(engine, 'optimization_strategies')
        assert 'keywords' in engine.optimization_strategies
        assert 'ats_score' in engine.optimization_strategies
    
    async def test_parse_resume_content_valid_json(self, mock_resume_data):
        """Test parsing valid JSON resume content."""
        engine = ResumeVersioningEngine()
        json_data = json.dumps(mock_resume_data)
        result = engine._parse_resume_content(json_data)
        assert result == mock_resume_data
        assert result["name"] == "John Doe"
    
    async def test_parse_resume_content_empty(self):
        """Test parsing empty resume content."""
        engine = ResumeVersioningEngine()
        result = engine._parse_resume_content("")
        assert result == {}
    
    async def test_parse_resume_content_invalid_json(self):
        """Test parsing invalid JSON returns empty dict."""
        engine = ResumeVersioningEngine()
        result = engine._parse_resume_content("not valid json")
        assert result == {}
    
    async def test_calculate_ats_score(self, mock_resume_data, mock_job_requirements):
        """Test ATS score calculation."""
        engine = ResumeVersioningEngine()
        score = engine._calculate_ats_score(mock_resume_data, mock_job_requirements)
        assert isinstance(score, float)
        assert 0 <= score <= 100
        # Should have good score with matching skills
        assert score >= 40  # Has required sections and some skill matches
    
    async def test_calculate_match_score(self, mock_resume_data, mock_job_requirements):
        """Test job match score calculation."""
        engine = ResumeVersioningEngine()
        score = engine._calculate_match_score(mock_resume_data, mock_job_requirements)
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    async def test_analyze_keywords(self, mock_resume_data, mock_job_requirements):
        """Test keyword analysis."""
        engine = ResumeVersioningEngine()
        analysis = engine._analyze_keywords(mock_resume_data, mock_job_requirements)
        assert "total_keywords" in analysis
        assert "matched_keywords" in analysis
        assert "missing_keywords" in analysis
        assert "density_score" in analysis
        assert isinstance(analysis["density_score"], float)
    
    async def test_generate_explanation(self, mock_resume_data, mock_job_requirements):
        """Test explanation generation."""
        engine = ResumeVersioningEngine()
        # Create slightly modified version
        optimized = mock_resume_data.copy()
        optimized["skills"] = mock_resume_data["skills"] + ["Docker", "Kubernetes"]
        
        explanation = engine._generate_explanation(mock_resume_data, optimized, mock_job_requirements)
        assert isinstance(explanation, str)
        assert len(explanation) > 0
    
    async def test_calculate_differences(self, mock_resume_data):
        """Test version difference calculation."""
        engine = ResumeVersioningEngine()
        content_a = mock_resume_data.copy()
        content_b = mock_resume_data.copy()
        content_b["skills"] = content_a["skills"] + ["Go", "Rust"]
        
        differences = engine._calculate_differences(content_a, content_b)
        assert "skills_added" in differences
        assert "skills_removed" in differences
        assert "sections_changed" in differences
        assert "go" in [s.lower() for s in differences["skills_added"]]
    
    async def test_calculate_similarity(self, mock_resume_data):
        """Test similarity calculation."""
        engine = ResumeVersioningEngine()
        content_a = mock_resume_data.copy()
        content_b = mock_resume_data.copy()
        
        # Identical content should have high similarity
        similarity = engine._calculate_similarity(content_a, content_b)
        assert similarity == 100.0
        
        # Modified content should have lower similarity
        content_b["summary"] = "Different summary"
        similarity = engine._calculate_similarity(content_a, content_b)
        assert similarity < 100.0


# ============================================================
# Interview Preparation Engine Tests
# ============================================================

@pytest.mark.asyncio
class TestInterviewPreparationEngine:
    """Test AI Interview Preparation Engine."""
    
    async def test_engine_initialization(self):
        """Test engine initializes correctly."""
        engine = InterviewPreparationEngine()
        assert engine is not None
        assert hasattr(engine, 'question_templates')
        assert 'technical' in engine.question_templates
        assert 'behavioral' in engine.question_templates
        assert 'company_specific' in engine.question_templates
    
    async def test_star_competencies_defined(self):
        """Test STAR competencies are defined."""
        engine = InterviewPreparationEngine()
        assert hasattr(engine, 'star_competencies')
        assert len(engine.star_competencies) > 0
        assert "Leadership" in engine.star_competencies
        assert "Problem Solving" in engine.star_competencies
    
    async def test_extract_skills_from_text(self):
        """Test skill extraction from job text."""
        engine = InterviewPreparationEngine()
        text = "We need someone with Python, JavaScript, and AWS experience. Docker is a plus."
        skills = engine._extract_skills(text)
        assert isinstance(skills, list)
        assert "python" in skills
        assert "javascript" in skills
        assert "aws" in skills
    
    async def test_extract_seniority_senior(self):
        """Test seniority extraction for senior roles."""
        engine = InterviewPreparationEngine()
        assert engine._extract_seniority("Senior Software Engineer") == "senior"
        assert engine._extract_seniority("Lead Developer") == "senior"
        assert engine._extract_seniority("Principal Engineer") == "senior"
    
    async def test_extract_seniority_junior(self):
        """Test seniority extraction for junior roles."""
        engine = InterviewPreparationEngine()
        assert engine._extract_seniority("Junior Developer") == "junior"
        assert engine._extract_seniority("Entry Level Engineer") == "junior"
        assert engine._extract_seniority("Associate Software Engineer") == "junior"
    
    async def test_extract_seniority_mid(self):
        """Test seniority extraction for mid-level roles."""
        engine = InterviewPreparationEngine()
        assert engine._extract_seniority("Software Engineer") == "mid"
        assert engine._extract_seniority("Developer") == "mid"
    
    async def test_extract_industry(self):
        """Test industry extraction from company name."""
        engine = InterviewPreparationEngine()
        assert engine._extract_industry("TechCorp Software") == "technology"
        assert engine._extract_industry("First National Bank") == "finance"
        assert engine._extract_industry("HealthCare Plus") == "healthcare"
        assert engine._extract_industry("Random Company") == "general"
    
    async def test_generate_answer_approach_technical(self):
        """Test answer approach generation for technical questions."""
        engine = InterviewPreparationEngine()
        approach = engine._generate_answer_approach("technical", "Explain Python decorators")
        assert isinstance(approach, str)
        assert len(approach) > 0
    
    async def test_generate_answer_approach_behavioral(self):
        """Test answer approach generation for behavioral questions."""
        engine = InterviewPreparationEngine()
        approach = engine._generate_answer_approach("behavioral", "Tell me about a challenge")
        assert isinstance(approach, str)
        assert "STAR" in approach
    
    async def test_generate_key_points_technical(self):
        """Test key points generation for technical questions."""
        engine = InterviewPreparationEngine()
        points = engine._generate_key_points("technical", "Python", ["python", "django"])
        assert isinstance(points, list)
        assert len(points) > 0
    
    async def test_generate_key_points_behavioral(self):
        """Test key points generation for behavioral questions."""
        engine = InterviewPreparationEngine()
        points = engine._generate_key_points("behavioral", "leadership", [])
        assert isinstance(points, list)
        assert any("Situation" in p for p in points)
        assert any("Result" in p for p in points)
    
    async def test_generate_follow_ups(self):
        """Test follow-up question generation."""
        engine = InterviewPreparationEngine()
        follow_ups = engine._generate_follow_ups("technical", "Explain microservices")
        assert isinstance(follow_ups, list)
        assert len(follow_ups) > 0
    
    async def test_generate_preparation_checklist(self, mock_job_requirements):
        """Test preparation checklist generation."""
        engine = InterviewPreparationEngine()
        checklist = engine._generate_preparation_checklist(mock_job_requirements, "intermediate")
        assert isinstance(checklist, list)
        assert len(checklist) > 0
        assert any("resume" in item.lower() for item in checklist)
    
    async def test_calculate_prep_time(self):
        """Test preparation time calculation."""
        engine = InterviewPreparationEngine()
        # Test with different question counts and difficulty levels
        time_basic = engine._calculate_prep_time(5, "beginner")
        time_advanced = engine._calculate_prep_time(10, "advanced")
        assert time_basic > 0
        assert time_advanced > time_basic


# ============================================================
# Skill Analyzer Engine Tests
# ============================================================

@pytest.mark.asyncio
class TestSkillAnalyzerEngine:
    """Test AI Skill Gap Analysis Engine."""
    
    async def test_engine_initialization(self):
        """Test engine initializes correctly."""
        engine = SkillAnalyzerEngine()
        assert engine is not None
        assert hasattr(engine, 'skill_categories')
        assert hasattr(engine, 'skill_database')
    
    async def test_skill_categories_defined(self):
        """Test skill categories are properly defined."""
        engine = SkillAnalyzerEngine()
        assert "technical" in engine.skill_categories
        assert "soft" in engine.skill_categories
        assert "certification" in engine.skill_categories
        assert "domain" in engine.skill_categories
    
    async def test_skill_database_populated(self):
        """Test skill database has entries."""
        engine = SkillAnalyzerEngine()
        assert len(engine.skill_database) > 0
        assert "python" in engine.skill_database
        assert "javascript" in engine.skill_database
        assert "aws" in engine.skill_database
    
    async def test_skill_database_structure(self):
        """Test skill database entry structure."""
        engine = SkillAnalyzerEngine()
        python_skill = engine.skill_database["python"]
        assert "category" in python_skill
        assert "difficulty" in python_skill
        assert "market_demand" in python_skill
        assert "avg_salary_impact" in python_skill
    
    async def test_extract_user_skills(self, mock_resume_data):
        """Test user skill extraction from resume."""
        engine = SkillAnalyzerEngine()
        skills = engine._extract_user_skills(mock_resume_data)
        assert isinstance(skills, list)
        assert len(skills) > 0
        skill_names = [s["name"] for s in skills]
        assert "python" in skill_names
    
    async def test_calculate_learning_timeline(self):
        """Test learning timeline calculation."""
        engine = SkillAnalyzerEngine()
        skill_gaps = [
            {"skill_name": "kubernetes", "importance": "critical", "estimated_learning_hours": 60},
            {"skill_name": "docker", "importance": "important", "estimated_learning_hours": 40},
            {"skill_name": "go", "importance": "nice-to-have", "estimated_learning_hours": 80}
        ]
        timeline = engine._calculate_learning_timeline(skill_gaps)
        assert isinstance(timeline, dict)
        assert "kubernetes" in timeline
        assert "docker" in timeline
    
    async def test_calculate_priority_scores(self, mock_job_requirements):
        """Test priority score calculation."""
        engine = SkillAnalyzerEngine()
        skill_gaps = [
            {"skill_name": "kubernetes", "importance": "critical", "market_demand_score": 85, "gap_score": 100},
            {"skill_name": "docker", "importance": "important", "market_demand_score": 89, "gap_score": 50}
        ]
        scores = engine._calculate_priority_scores(skill_gaps, mock_job_requirements)
        assert isinstance(scores, dict)
        assert "kubernetes" in scores
        assert "docker" in scores
        # Critical skill should have higher priority
        assert scores["kubernetes"] > scores["docker"]
    
    async def test_get_learning_resources_for_skill(self):
        """Test learning resource retrieval."""
        engine = SkillAnalyzerEngine()
        resources = engine._get_learning_resources_for_skill("python", "intermediate")
        assert isinstance(resources, list)
        assert len(resources) > 0
        assert all("title" in r for r in resources)
        assert all("provider" in r for r in resources)
    
    async def test_generate_progress_feedback(self):
        """Test progress feedback generation."""
        engine = SkillAnalyzerEngine()
        # Create mock progress record
        progress_record = MagicMock()
        progress_record.current_level = 3.0
        progress_record.previous_level = 2.0
        progress_record.progress_percentage = 60.0
        progress_record.hours_invested = 20
        
        progress_data = {"current_level": 3.5, "hours_invested": 25}
        
        feedback = engine._generate_progress_feedback(progress_record, progress_data)
        assert isinstance(feedback, dict)


# ============================================================
# Integration Tests with Mocked Database
# ============================================================

@pytest.mark.asyncio
class TestAIFeaturesIntegration:
    """Integration tests for AI features with mocked dependencies."""
    
    async def test_resume_versioning_workflow(self, mock_resume_data, mock_job_requirements):
        """Test complete resume versioning workflow."""
        engine = ResumeVersioningEngine()
        
        # Test optimization pipeline
        optimized = await engine._optimize_keywords(mock_resume_data.copy(), mock_job_requirements)
        assert "skills" in optimized
        
        optimized = await engine._optimize_ats_score(optimized, mock_job_requirements)
        optimized = await engine._optimize_relevance(optimized, mock_job_requirements)
        optimized = await engine._optimize_formatting(optimized, mock_job_requirements)
        
        # Calculate final scores
        ats_score = engine._calculate_ats_score(optimized, mock_job_requirements)
        match_score = engine._calculate_match_score(optimized, mock_job_requirements)
        
        assert ats_score >= 0
        assert match_score >= 0
    
    async def test_interview_prep_question_generation(self, mock_resume_data, mock_job_requirements):
        """Test interview question generation workflow."""
        engine = InterviewPreparationEngine()
        
        # Generate technical questions
        tech_questions = await engine._generate_technical_questions(
            mock_resume_data, mock_job_requirements, "intermediate"
        )
        assert len(tech_questions) > 0
        assert all("text" in q for q in tech_questions)
        assert all("category" in q for q in tech_questions)
        
        # Generate behavioral questions
        behavioral_questions = await engine._generate_behavioral_questions(
            mock_resume_data, mock_job_requirements, "intermediate"
        )
        assert len(behavioral_questions) > 0
        
        # Generate company questions
        company_questions = await engine._generate_company_questions(
            mock_job_requirements, "intermediate"
        )
        assert len(company_questions) > 0
    
    async def test_interview_prep_talking_points(self, mock_resume_data, mock_job_requirements):
        """Test talking points generation."""
        engine = InterviewPreparationEngine()
        talking_points = await engine._generate_talking_points(mock_resume_data, mock_job_requirements)
        assert isinstance(talking_points, list)
        assert len(talking_points) > 0
    
    async def test_interview_prep_star_examples(self, mock_resume_data, mock_job_requirements):
        """Test STAR example generation."""
        engine = InterviewPreparationEngine()
        star_examples = await engine._generate_star_examples(mock_resume_data, mock_job_requirements)
        assert isinstance(star_examples, list)
        if len(star_examples) > 0:
            example = star_examples[0]
            assert "competency" in example
            assert "situation" in example
            assert "task" in example
            assert "action" in example
            assert "result" in example
    
    async def test_skill_gap_identification(self, mock_resume_data, mock_job_requirements):
        """Test skill gap identification."""
        engine = SkillAnalyzerEngine()
        
        user_skills = engine._extract_user_skills(mock_resume_data)
        
        # Create mock required skills
        required_skills = [
            {"name": "kubernetes", "required_level": 3, "importance": "critical", "category": "technical", "market_demand": 85, "salary_impact": 18000},
            {"name": "docker", "required_level": 3, "importance": "important", "category": "technical", "market_demand": 89, "salary_impact": 12000},
            {"name": "python", "required_level": 4, "importance": "critical", "category": "technical", "market_demand": 95, "salary_impact": 15000}
        ]
        
        skill_gaps = await engine._identify_skill_gaps(user_skills, required_skills)
        assert isinstance(skill_gaps, list)
        # Should identify kubernetes as a gap (not in user skills)
        gap_names = [g["skill_name"] for g in skill_gaps]
        assert "kubernetes" in gap_names
    
    async def test_learning_recommendations(self):
        """Test learning recommendation generation."""
        engine = SkillAnalyzerEngine()
        
        skill_gaps = [
            {"skill_name": "kubernetes", "difficulty_level": "advanced"},
            {"skill_name": "docker", "difficulty_level": "intermediate"}
        ]
        
        recommendations = await engine._generate_learning_recommendations(skill_gaps)
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all("skill_name" in r for r in recommendations)
        assert all("title" in r for r in recommendations)


# ============================================================
# Edge Cases and Error Handling Tests
# ============================================================

@pytest.mark.asyncio
class TestAIFeaturesEdgeCases:
    """Test edge cases and error handling."""
    
    async def test_empty_resume_data(self):
        """Test handling of empty resume data."""
        engine = ResumeVersioningEngine()
        result = engine._parse_resume_content(None)
        assert result == {}
    
    async def test_empty_skills_list(self):
        """Test handling of empty skills list."""
        engine = SkillAnalyzerEngine()
        resume_data = {"name": "Test User", "skills": []}
        skills = engine._extract_user_skills(resume_data)
        assert isinstance(skills, list)
    
    async def test_missing_experience_section(self):
        """Test handling of missing experience section."""
        engine = SkillAnalyzerEngine()
        resume_data = {"name": "Test User", "skills": ["Python"]}
        skills = engine._extract_user_skills(resume_data)
        assert isinstance(skills, list)
    
    async def test_ats_score_with_minimal_data(self):
        """Test ATS score calculation with minimal data."""
        engine = ResumeVersioningEngine()
        minimal_content = {"name": "Test"}
        job_requirements = {"skills": [], "keywords": []}
        score = engine._calculate_ats_score(minimal_content, job_requirements)
        assert isinstance(score, float)
        assert score >= 0
    
    async def test_match_score_with_no_skills(self):
        """Test match score with no skills."""
        engine = ResumeVersioningEngine()
        content = {"name": "Test", "skills": []}
        job_requirements = {"skills": ["python"], "title": "Developer"}
        score = engine._calculate_match_score(content, job_requirements)
        assert isinstance(score, float)
        assert score >= 0
    
    async def test_keyword_analysis_empty_keywords(self):
        """Test keyword analysis with empty keywords."""
        engine = ResumeVersioningEngine()
        content = {"name": "Test"}
        job_requirements = {"keywords": []}
        analysis = engine._analyze_keywords(content, job_requirements)
        assert analysis["total_keywords"] == 0
        assert analysis["density_score"] == 0.0
    
    async def test_similarity_with_empty_content(self):
        """Test similarity calculation with empty content."""
        engine = ResumeVersioningEngine()
        similarity = engine._calculate_similarity({}, {})
        assert similarity == 0.0 or similarity == 100.0  # Either no fields or all match
    
    async def test_prep_time_zero_questions(self):
        """Test prep time with zero questions."""
        engine = InterviewPreparationEngine()
        time = engine._calculate_prep_time(0, "beginner")
        assert time >= 0
