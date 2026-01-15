"""Database models package."""
from app.models.user import User, Session, AuditLog
from app.models.resume import Resume, ResumeScorecard, ResumeShareLink
from app.models.preferences import UserPreferences
from app.models.job import JobSource, JobPosting
from app.models.match import JobMatch
from app.models.apply import ApplyKit, JobActivity, ActivityStatus
from app.models.notification import NotificationSettings, NotificationLog, NotificationType
from app.models.ai_resume import AIResumeVersion, ResumeOptimizationLog, ResumeVersionComparison
from app.models.ai_interview import InterviewKit, InterviewQuestion, STARExample, InterviewSession, CompanyInsight
from app.models.ai_skills import (
    SkillGapAnalysis, SkillGap, LearningResource, 
    SkillProgressTracking, SkillMarketData, LearningPath
)

__all__ = [
    "User", "Session", "AuditLog", 
    "Resume", "ResumeScorecard", "ResumeShareLink", 
    "UserPreferences",
    "JobSource", "JobPosting",
    "JobMatch",
    "ApplyKit", "JobActivity", "ActivityStatus",
    "NotificationSettings", "NotificationLog", "NotificationType",
    "AIResumeVersion", "ResumeOptimizationLog", "ResumeVersionComparison",
    "InterviewKit", "InterviewQuestion", "STARExample", "InterviewSession", "CompanyInsight",
    "SkillGapAnalysis", "SkillGap", "LearningResource", 
    "SkillProgressTracking", "SkillMarketData", "LearningPath"
]
