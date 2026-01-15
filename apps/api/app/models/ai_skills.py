"""
AI Skill Gap Analysis models.
Handles skill analysis, gap identification, and learning recommendations.
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean, Float
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class SkillGapAnalysis(Base):
    """AI-generated skill gap analysis for a specific job."""
    
    __tablename__ = "skill_gap_analyses"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    job_id = Column(String(36), nullable=False, index=True)
    
    # Analysis results (JSON as TEXT for SQLite)
    missing_skills = Column(Text, nullable=False)  # JSON array of SkillGap objects
    learning_recommendations = Column(Text, nullable=False)  # JSON array of LearningResource objects
    estimated_timeline = Column(Text, nullable=False)  # JSON dict of skill -> hours
    priority_score = Column(Text, nullable=False)  # JSON dict of skill -> priority score
    market_demand = Column(Text, nullable=True)  # JSON dict of skill -> market demand score
    
    # Overall metrics
    total_missing_skills = Column(Integer, nullable=False)
    critical_skills_count = Column(Integer, default=0)
    estimated_total_hours = Column(Integer, nullable=False)  # Total learning time
    overall_readiness_score = Column(Float, nullable=False)  # 0-100 job readiness score
    
    # Metadata
    analysis_version = Column(String(10), default="1.0")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<SkillGapAnalysis {self.id} for job {self.job_id}>"


class SkillGap(Base):
    """Individual skill gap with detailed analysis."""
    
    __tablename__ = "skill_gaps"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    
    # Skill details
    skill_name = Column(String(100), nullable=False, index=True)
    skill_category = Column(String(50), nullable=False)  # technical, soft, certification, etc.
    importance = Column(String(20), nullable=False)  # critical, important, nice-to-have
    
    # Gap analysis
    current_level = Column(Integer, default=0)  # 0-5 scale
    required_level = Column(Integer, nullable=False)  # 0-5 scale
    gap_score = Column(Float, nullable=False)  # Calculated gap severity (0-100)
    
    # Market insights
    market_demand_score = Column(Float, nullable=True)  # Market demand (0-100)
    salary_impact = Column(Float, nullable=True)  # Potential salary increase
    job_postings_count = Column(Integer, nullable=True)  # Number of jobs requiring this skill
    
    # Learning recommendations
    recommended_resources = Column(Text, nullable=True)  # JSON array of learning resources
    estimated_learning_hours = Column(Integer, nullable=False)
    difficulty_level = Column(String(20), default="intermediate")  # beginner, intermediate, advanced
    
    # Progress tracking
    learning_progress = Column(Float, default=0.0)  # 0-100 completion percentage
    target_completion_date = Column(DateTime(timezone=True), nullable=True)
    last_progress_update = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SkillGap {self.skill_name} ({self.importance}) for analysis {self.analysis_id}>"


class LearningResource(Base):
    """Learning resource recommendation for skill development."""
    
    __tablename__ = "learning_resources"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    skill_gap_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    
    # Resource details
    title = Column(String(200), nullable=False)
    provider = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)  # course, certification, book, tutorial, practice
    url = Column(String(500), nullable=True)
    
    # Resource metrics
    estimated_hours = Column(Integer, nullable=False)
    difficulty = Column(String(20), nullable=False)  # beginner, intermediate, advanced
    cost = Column(Float, nullable=True)  # Cost in USD, null for free
    rating = Column(Float, nullable=True)  # 0-5 rating
    
    # Relevance and priority
    relevance_score = Column(Float, nullable=False)  # How relevant to the skill gap (0-100)
    priority_rank = Column(Integer, nullable=False)  # Priority order for this skill
    
    # User interaction
    is_bookmarked = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    user_rating = Column(Float, nullable=True)  # User's rating after completion
    completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    data_source = Column(String(100), nullable=True)  # Where the recommendation came from
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<LearningResource {self.title} for skill gap {self.skill_gap_id}>"


class SkillProgressTracking(Base):
    """Track user's skill development progress over time."""
    
    __tablename__ = "skill_progress_tracking"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False, index=True)
    
    # Progress details
    current_level = Column(Float, nullable=False)  # Current skill level (0-5 scale)
    previous_level = Column(Float, nullable=True)  # Previous level for comparison
    progress_percentage = Column(Float, nullable=False)  # 0-100 completion percentage
    
    # Learning activity
    hours_invested = Column(Float, default=0.0)  # Total hours spent learning
    resources_completed = Column(Integer, default=0)  # Number of resources completed
    certifications_earned = Column(Text, nullable=True)  # JSON array of certifications
    
    # Assessment and validation
    self_assessment_score = Column(Float, nullable=True)  # User's self-assessment (0-5)
    external_validation = Column(Text, nullable=True)  # JSON with external validations
    skill_demonstration = Column(Text, nullable=True)  # JSON with project/work examples
    
    # Timeline and goals
    learning_goal = Column(Float, nullable=True)  # Target skill level
    target_date = Column(DateTime(timezone=True), nullable=True)
    milestone_dates = Column(Text, nullable=True)  # JSON array of milestone dates
    
    # Progress notes and feedback
    progress_notes = Column(Text, nullable=True)  # User's notes on learning journey
    ai_feedback = Column(Text, nullable=True)  # AI-generated feedback and suggestions
    
    # Metadata
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SkillProgressTracking {self.skill_name} for user {self.user_id}>"


class SkillMarketData(Base):
    """Market data and trends for skills."""
    
    __tablename__ = "skill_market_data"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    skill_name = Column(String(100), nullable=False, unique=True, index=True)
    skill_category = Column(String(50), nullable=False)
    
    # Market demand metrics
    demand_score = Column(Float, nullable=False)  # Overall market demand (0-100)
    job_postings_count = Column(Integer, default=0)  # Number of job postings requiring this skill
    growth_rate = Column(Float, nullable=True)  # Year-over-year growth rate (%)
    
    # Salary impact
    average_salary_impact = Column(Float, nullable=True)  # Average salary increase ($)
    salary_percentile_50 = Column(Float, nullable=True)  # Median salary for this skill
    salary_percentile_90 = Column(Float, nullable=True)  # 90th percentile salary
    
    # Geographic data
    top_locations = Column(Text, nullable=True)  # JSON array of top locations for this skill
    remote_friendly = Column(Boolean, default=False)  # Whether skill is remote-friendly
    
    # Industry data
    top_industries = Column(Text, nullable=True)  # JSON array of industries using this skill
    emerging_trend = Column(Boolean, default=False)  # Whether this is an emerging skill
    
    # Learning data
    average_learning_time = Column(Integer, nullable=True)  # Average time to learn (hours)
    difficulty_rating = Column(Float, nullable=True)  # Community difficulty rating (1-5)
    prerequisite_skills = Column(Text, nullable=True)  # JSON array of prerequisite skills
    
    # Data freshness
    data_sources = Column(Text, nullable=True)  # JSON array of data sources
    confidence_score = Column(Float, nullable=False)  # Confidence in data accuracy (0-100)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SkillMarketData {self.skill_name} (demand: {self.demand_score})>"


class LearningPath(Base):
    """Structured learning path for skill development."""
    
    __tablename__ = "learning_paths"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    analysis_id = Column(String(36), nullable=False, index=True)
    
    # Path details
    path_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    target_role = Column(String(100), nullable=True)  # Target job role
    
    # Path structure (JSON as TEXT for SQLite)
    learning_steps = Column(Text, nullable=False)  # JSON array of ordered learning steps
    milestones = Column(Text, nullable=False)  # JSON array of milestone checkpoints
    skill_progression = Column(Text, nullable=False)  # JSON dict of skill -> target levels
    
    # Timeline and effort
    estimated_total_hours = Column(Integer, nullable=False)
    estimated_weeks = Column(Integer, nullable=False)
    difficulty_level = Column(String(20), nullable=False)  # beginner, intermediate, advanced
    
    # Progress tracking
    current_step = Column(Integer, default=0)  # Current step index
    completion_percentage = Column(Float, default=0.0)  # Overall completion (0-100)
    hours_completed = Column(Float, default=0.0)  # Hours completed so far
    
    # Path optimization
    priority_order = Column(Text, nullable=False)  # JSON array of skill priority order
    market_alignment_score = Column(Float, nullable=False)  # How well aligned with market demand
    personalization_score = Column(Float, nullable=False)  # How personalized to user's background
    
    # Status and metadata
    is_active = Column(Boolean, default=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    target_completion_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<LearningPath {self.path_name} for user {self.user_id}>"