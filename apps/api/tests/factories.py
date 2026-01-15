"""
Test data factories for creating deterministic test data.
Provides consistent, realistic test data for all test scenarios.
"""
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, Session, AuditLog
from app.models.resume import Resume, ResumeScorecard, ResumeShareLink
from app.models.preferences import UserPreferences
from app.models.job import JobSource, JobPosting
from app.models.match import JobMatch
from app.models.apply import ApplyKit, JobActivity, ActivityStatus
from app.models.notification import NotificationSettings, NotificationLog, NotificationType
from app.models.ai_resume import AIResumeVersion, ResumeOptimizationLog
from app.models.ai_interview import InterviewKit, InterviewQuestion, STARExample, CompanyInsight
from app.models.ai_skills import SkillGapAnalysis, SkillGap, LearningResource, SkillProgressTracking
from app.services.auth import get_password_hash


class TestDataFactory:
    """Factory for creating consistent test data."""
    
    def __init__(self):
        self.counter = 0
        self.base_time = datetime(2025, 1, 11, 12, 0, 0)
    
    def get_unique_id(self) -> str:
        """Get a unique ID for test data."""
        self.counter += 1
        return str(uuid.UUID(int=self.counter))
    
    def get_unique_email(self, prefix: str = "test") -> str:
        """Get a unique email address."""
        self.counter += 1
        return f"{prefix}{self.counter}@example.com"
    
    def get_time_offset(self, hours: int = 0) -> datetime:
        """Get a time offset from base time."""
        return self.base_time + timedelta(hours=hours)


class UserFactory:
    """Factory for creating user-related test data."""
    
    def __init__(self, factory: TestDataFactory):
        self.factory = factory
    
    def create_user(
        self,
        email: Optional[str] = None,
        password: str = "TestPass123!",
        full_name: Optional[str] = None,
        is_active: bool = True,
        **kwargs
    ) -> User:
        """Create a test user."""
        if not email:
            email = self.factory.get_unique_email("user")
        
        if not full_name:
            full_name = f"Test User {self.factory.counter}"
        
        return User(
            id=self.factory.get_unique_id(),
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            is_active=is_active,
            created_at=self.factory.get_time_offset(),
            **kwargs
        )
    
    def create_session(
        self,
        user_id: str,
        refresh_token: str = "test_refresh_token",
        expires_at: Optional[datetime] = None,
        **kwargs
    ) -> Session:
        """Create a test session."""
        if not expires_at:
            expires_at = self.factory.get_time_offset(hours=24 * 7)  # 7 days
        
        return Session(
            id=self.factory.get_unique_id(),
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            created_at=self.factory.get_time_offset(),
            **kwargs
        )
    
    def create_audit_log(
        self,
        user_id: str,
        action: str = "test_action",
        resource_type: str = "test_resource",
        **kwargs
    ) -> AuditLog:
        """Create a test audit log entry."""
        return AuditLog(
            id=self.factory.get_unique_id(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            ip_address="127.0.0.1",
            user_agent="Test User Agent",
            created_at=self.factory.get_time_offset(),
            **kwargs
        )


class ResumeFactory:
    """Factory for creating resume-related test data."""
    
    def __init__(self, factory: TestDataFactory):
        self.factory = factory
    
    def create_resume(
        self,
        user_id: str,
        filename: str = "test_resume.pdf",
        parsed_data: Optional[Dict] = None,
        **kwargs
    ) -> Resume:
        """Create a test resume."""
        if not parsed_data:
            parsed_data = self.get_sample_resume_data()
        
        return Resume(
            id=self.factory.get_unique_id(),
            user_id=user_id,
            filename=filename,
            file_path=f"/uploads/{filename}",
            file_size=2048,
            mime_type="application/pdf",
            parsed_data=json.dumps(parsed_data),
            is_parsed=True,
            uploaded_at=self.factory.get_time_offset(),
            **kwargs
        )
    
    def get_sample_resume_data(self) -> Dict[str, Any]:
        """Get sample resume data."""
        return {
            "name": f"Test User {self.factory.counter}",
            "email": self.factory.get_unique_email("resume"),
            "phone": "+1-555-0123",
            "title": "Software Developer",
            "summary": "Experienced software developer with expertise in Python, JavaScript, and React. Strong problem-solving skills and team collaboration experience.",
            "skills": [
                "Python", "JavaScript", "React", "Node.js", "SQL", "Git",
                "FastAPI", "PostgreSQL", "Docker", "AWS", "REST APIs"
            ],
            "experience": [
                {
                    "company": "Tech Solutions Inc",
                    "position": "Senior Software Developer",
                    "duration": "2022-2024",
                    "description": "Led development of web applications using React and Python. Managed team of 3 developers. Implemented CI/CD pipelines and improved system performance by 40%.",
                    "achievements": [
                        "Reduced application load time by 40%",
                        "Led team of 3 developers",
                        "Implemented automated testing pipeline"
                    ]
                },
                {
                    "company": "StartupCorp",
                    "position": "Full Stack Developer",
                    "duration": "2020-2022",
                    "description": "Developed full stack applications using JavaScript, Node.js, and PostgreSQL. Collaborated with design team to implement user-friendly interfaces.",
                    "achievements": [
                        "Built 5 production applications",
                        "Improved user engagement by 25%",
                        "Mentored 2 junior developers"
                    ]
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Computer Science",
                    "school": "Tech University",
                    "year": "2020",
                    "gpa": "3.8"
                }
            ],
            "projects": [
                {
                    "name": "Job Portal Application",
                    "description": "Full stack job portal with React frontend and Python backend",
                    "technologies": ["React", "Python", "FastAPI", "PostgreSQL"],
                    "url": "https://github.com/testuser/job-portal"
                }
            ],
            "certifications": [
                {
                    "name": "AWS Certified Developer",
                    "issuer": "Amazon Web Services",
                    "date": "2023"
                }
            ]
        }
    
    def create_scorecard(
        self,
        resume_id: str,
        overall_score: float = 85.0,
        **kwargs
    ) -> ResumeScorecard:
        """Create a test resume scorecard."""
        return ResumeScorecard(
            id=self.factory.get_unique_id(),
            resume_id=resume_id,
            overall_score=overall_score,
            ats_score=80.0,
            content_score=90.0,
            format_score=85.0,
            keyword_score=88.0,
            suggestions=json.dumps([
                "Add more quantifiable achievements",
                "Include relevant keywords for target roles",
                "Improve formatting consistency"
            ]),
            created_at=self.factory.get_time_offset(),
            **kwargs
        )
    
    def create_share_link(
        self,
        resume_id: str,
        expires_at: Optional[datetime] = None,
        **kwargs
    ) -> ResumeShareLink:
        """Create a test resume share link."""
        if not expires_at:
            expires_at = self.factory.get_time_offset(hours=24 * 30)  # 30 days
        
        return ResumeShareLink(
            id=self.factory.get_unique_id(),
            resume_id=resume_id,
            share_token=f"share_token_{self.factory.counter}",
            expires_at=expires_at,
            created_at=self.factory.get_time_offset(),
            **kwargs
        )


class JobFactory:
    """Factory for creating job-related test data."""
    
    def __init__(self, factory: TestDataFactory):
        self.factory = factory
    
    def create_job_source(
        self,
        name: str = "Test Job Board",
        url: str = "https://testjobs.com",
        source_type: str = "rss",
        **kwargs
    ) -> JobSource:
        """Create a test job source."""
        return JobSource(
            id=self.factory.get_unique_id(),
            name=name,
            url=url,
            source_type=source_type,
            is_active=True,
            last_fetched=self.factory.get_time_offset(),
            created_at=self.factory.get_time_offset(),
            **kwargs
        )
    
    def create_job_posting(
        self,
        title: str = "Software Developer",
        company: str = "Tech Corp",
        **kwargs
    ) -> JobPosting:
        """Create a test job posting."""
        return JobPosting(
            id=self.factory.get_unique_id(),
            title=title,
            company=company,
            location="San Francisco, CA",
            job_type="full-time",
            description=f"We are looking for a {title} to join our team. You will work on exciting projects using modern technologies.",
            requirements="Required: Python, JavaScript, React. Preferred: AWS, Docker, Kubernetes. 3+ years experience required.",
            salary_min=80000,
            salary_max=120000,
            is_remote=True,
            source="test_source",
            external_id=f"job_{self.factory.counter}",
            posted_at=self.factory.get_time_offset(),
            created_at=self.factory.get_time_offset(),
            **kwargs
        )
    
    def create_job_match(
        self,
        user_id: str,
        job_id: str,
        match_score: float = 85.0,
        **kwargs
    ) -> JobMatch:
        """Create a test job match."""
        return JobMatch(
            id=self.factory.get_unique_id(),
            user_id=user_id,
            job_id=job_id,
            match_score=match_score,
            skill_match_score=80.0,
            location_match_score=90.0,
            salary_match_score=85.0,
            experience_match_score=88.0,
            matching_keywords=json.dumps(["python", "javascript", "react"]),
            missing_keywords=json.dumps(["aws", "docker"]),
            created_at=self.factory.get_time_offset(),
            **kwargs
        )


class AIFactory:
    """Factory for creating AI-related test data."""
    
    def __init__(self, factory: TestDataFactory):
        self.factory = factory
    
    def create_ai_resume_version(
        self,
        user_id: str,
        job_id: str,
        base_resume_id: str,
        **kwargs
    ) -> AIResumeVersion:
        """Create a test AI resume version."""
        optimized_content = {
            "name": "Test User",
            "title": "Senior Software Developer",
            "summary": "Experienced senior software developer with expertise in Python, JavaScript, React, and AWS. Proven track record of delivering high-quality solutions.",
            "skills": ["Python", "JavaScript", "React", "AWS", "Docker", "Kubernetes"],
            "experience": [
                {
                    "company": "Tech Solutions Inc",
                    "position": "Senior Software Developer",
                    "description": "Led development of scalable web applications using React and Python. Implemented AWS infrastructure and Docker containerization."
                }
            ]
        }
        
        return AIResumeVersion(
            id=self.factory.get_unique_id(),
            user_id=user_id,
            job_id=job_id,
            base_resume_id=base_resume_id,
            optimized_content=json.dumps(optimized_content),
            changes_explanation="Enhanced summary with job-relevant keywords. Added AWS and Docker skills. Improved experience descriptions with quantifiable achievements.",
            ats_score=92.0,
            match_score=88.0,
            keyword_density=json.dumps({
                "total_keywords": 15,
                "matched_keywords": ["python", "javascript", "react", "aws"],
                "density_score": 85.0
            }),
            version_number=1,
            created_at=self.factory.get_time_offset(),
            **kwargs
        )
    
    def create_interview_kit(
        self,
        user_id: str,
        job_id: str,
        difficulty_level: str = "intermediate",
        **kwargs
    ) -> InterviewKit:
        """Create a test interview kit."""
        questions = [
            {
                "id": self.factory.get_unique_id(),
                "text": "Tell me about your experience with Python and web development.",
                "category": "technical",
                "difficulty": difficulty_level
            },
            {
                "id": self.factory.get_unique_id(),
                "text": "Describe a time when you had to solve a challenging technical problem.",
                "category": "behavioral",
                "difficulty": difficulty_level
            }
        ]
        
        talking_points = [
            "Highlight your experience with Python and React",
            "Discuss your problem-solving approach",
            "Mention your team collaboration skills"
        ]
        
        return InterviewKit(
            id=self.factory.get_unique_id(),
            user_id=user_id,
            job_id=job_id,
            questions=json.dumps(questions),
            talking_points=json.dumps(talking_points),
            company_insights=json.dumps({"culture": "Fast-paced, innovative"}),
            star_examples=json.dumps([]),
            preparation_checklist=json.dumps([
                "Review your resume",
                "Research the company",
                "Prepare STAR examples"
            ]),
            difficulty_level=difficulty_level,
            estimated_prep_time=120,
            created_at=self.factory.get_time_offset(),
            **kwargs
        )
    
    def create_skill_gap_analysis(
        self,
        user_id: str,
        job_id: str,
        **kwargs
    ) -> SkillGapAnalysis:
        """Create a test skill gap analysis."""
        missing_skills = [
            {
                "skill_name": "aws",
                "importance": "critical",
                "gap_score": 100.0,
                "estimated_learning_hours": 40
            },
            {
                "skill_name": "docker",
                "importance": "important",
                "gap_score": 80.0,
                "estimated_learning_hours": 20
            }
        ]
        
        learning_recommendations = [
            {
                "skill_name": "aws",
                "title": "AWS Certified Developer Course",
                "provider": "AWS",
                "type": "certification",
                "hours": 40,
                "relevance": 95
            }
        ]
        
        return SkillGapAnalysis(
            id=self.factory.get_unique_id(),
            user_id=user_id,
            job_id=job_id,
            missing_skills=json.dumps(missing_skills),
            learning_recommendations=json.dumps(learning_recommendations),
            estimated_timeline=json.dumps({"aws": {"hours": 40, "weeks": 4}}),
            priority_score=json.dumps({"aws": 95.0, "docker": 75.0}),
            market_demand=json.dumps({"aws": {"demand_score": 93}}),
            total_missing_skills=2,
            critical_skills_count=1,
            estimated_total_hours=60,
            overall_readiness_score=75.0,
            created_at=self.factory.get_time_offset(),
            **kwargs
        )


class NotificationFactory:
    """Factory for creating notification-related test data."""
    
    def __init__(self, factory: TestDataFactory):
        self.factory = factory
    
    def create_notification_settings(
        self,
        user_id: str,
        **kwargs
    ) -> NotificationSettings:
        """Create test notification settings."""
        return NotificationSettings(
            id=self.factory.get_unique_id(),
            user_id=user_id,
            email_notifications=True,
            job_alerts=True,
            application_updates=True,
            weekly_digest=True,
            marketing_emails=False,
            created_at=self.factory.get_time_offset(),
            **kwargs
        )
    
    def create_notification_log(
        self,
        user_id: str,
        notification_type: NotificationType = NotificationType.HIGH_MATCH_ALERT,
        **kwargs
    ) -> NotificationLog:
        """Create test notification log."""
        return NotificationLog(
            id=self.factory.get_unique_id(),
            user_id=user_id,
            notification_type=notification_type,
            title="Test Notification",
            message="This is a test notification message",
            is_read=False,
            created_at=self.factory.get_time_offset(),
            **kwargs
        )


class TestDataBuilder:
    """Builder for creating complete test scenarios."""
    
    def __init__(self):
        self.factory = TestDataFactory()
        self.user_factory = UserFactory(self.factory)
        self.resume_factory = ResumeFactory(self.factory)
        self.job_factory = JobFactory(self.factory)
        self.ai_factory = AIFactory(self.factory)
        self.notification_factory = NotificationFactory(self.factory)
    
    async def create_complete_user_scenario(
        self,
        db: AsyncSession,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a complete user scenario with all related data."""
        # Create user
        user = self.user_factory.create_user(email=email)
        db.add(user)
        await db.flush()
        
        # Create resume
        resume = self.resume_factory.create_resume(user.id)
        db.add(resume)
        await db.flush()
        
        # Create scorecard
        scorecard = self.resume_factory.create_scorecard(resume.id)
        db.add(scorecard)
        
        # Create job posting
        job = self.job_factory.create_job_posting()
        db.add(job)
        await db.flush()
        
        # Create job match
        match = self.job_factory.create_job_match(user.id, job.id)
        db.add(match)
        
        # Create AI features
        ai_resume = self.ai_factory.create_ai_resume_version(user.id, job.id, resume.id)
        db.add(ai_resume)
        
        interview_kit = self.ai_factory.create_interview_kit(user.id, job.id)
        db.add(interview_kit)
        
        skill_analysis = self.ai_factory.create_skill_gap_analysis(user.id, job.id)
        db.add(skill_analysis)
        
        # Create notifications
        notification_settings = self.notification_factory.create_notification_settings(user.id)
        db.add(notification_settings)
        
        await db.commit()
        
        return {
            "user": user,
            "resume": resume,
            "scorecard": scorecard,
            "job": job,
            "match": match,
            "ai_resume": ai_resume,
            "interview_kit": interview_kit,
            "skill_analysis": skill_analysis,
            "notification_settings": notification_settings
        }
    
    async def create_multiple_users_scenario(
        self,
        db: AsyncSession,
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """Create multiple users with complete data."""
        scenarios = []
        
        for i in range(count):
            scenario = await self.create_complete_user_scenario(
                db, 
                email=f"testuser{i+1}@example.com"
            )
            scenarios.append(scenario)
        
        return scenarios
    
    def create_performance_test_data(self) -> Dict[str, List[Any]]:
        """Create large dataset for performance testing."""
        users = [self.user_factory.create_user() for _ in range(100)]
        jobs = [self.job_factory.create_job_posting() for _ in range(50)]
        
        return {
            "users": users,
            "jobs": jobs
        }


# Global factory instance for easy access
test_data_builder = TestDataBuilder()