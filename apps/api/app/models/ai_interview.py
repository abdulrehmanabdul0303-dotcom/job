"""
AI Interview Preparation models.
Handles interview questions, coaching, and preparation kits.
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean, Float
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class InterviewKit(Base):
    """AI-generated interview preparation kit."""
    
    __tablename__ = "interview_kits"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    job_id = Column(String(36), nullable=False, index=True)
    
    # Kit content (JSON as TEXT for SQLite)
    questions = Column(Text, nullable=False)  # JSON array of interview questions
    talking_points = Column(Text, nullable=False)  # JSON array of personalized talking points
    company_insights = Column(Text, nullable=True)  # JSON with company research
    star_examples = Column(Text, nullable=True)  # JSON array of STAR method examples
    preparation_checklist = Column(Text, nullable=True)  # JSON array of preparation items
    
    # Metadata
    difficulty_level = Column(String(20), default="intermediate")  # beginner, intermediate, advanced
    estimated_prep_time = Column(Integer, nullable=True)  # minutes
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<InterviewKit {self.id} for job {self.job_id}>"


class InterviewQuestion(Base):
    """Individual interview question with metadata."""
    
    __tablename__ = "interview_questions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kit_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    
    # Question details
    question_text = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # technical, behavioral, company_specific
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    
    # AI-generated content
    suggested_answer = Column(Text, nullable=True)  # AI-suggested answer approach
    key_points = Column(Text, nullable=True)  # JSON array of key points to cover
    follow_up_questions = Column(Text, nullable=True)  # JSON array of potential follow-ups
    
    # User interaction
    user_answer = Column(Text, nullable=True)  # User's practice answer
    ai_feedback = Column(Text, nullable=True)  # AI feedback on user's answer
    feedback_score = Column(Float, nullable=True)  # Score for user's answer (0-100)
    
    # Metadata
    order_index = Column(Integer, default=0)  # Order in the kit
    is_practiced = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<InterviewQuestion {self.category} for kit {self.kit_id}>"


class STARExample(Base):
    """STAR method examples generated from user's experience."""
    
    __tablename__ = "star_examples"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kit_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    
    # STAR components
    situation = Column(Text, nullable=False)  # Situation description
    task = Column(Text, nullable=False)  # Task that needed to be accomplished
    action = Column(Text, nullable=False)  # Action taken
    result = Column(Text, nullable=False)  # Result achieved
    
    # Metadata
    competency = Column(String(100), nullable=False)  # Leadership, Problem Solving, etc.
    source_experience = Column(Text, nullable=True)  # JSON with source experience data
    relevance_score = Column(Float, nullable=False)  # Relevance to job (0-100)
    
    # Usage tracking
    times_used = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<STARExample {self.competency} for kit {self.kit_id}>"


class InterviewSession(Base):
    """Interview practice session tracking."""
    
    __tablename__ = "interview_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kit_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    
    # Session details
    session_type = Column(String(50), nullable=False)  # practice, mock_interview, review
    duration_minutes = Column(Integer, nullable=True)
    questions_attempted = Column(Integer, default=0)
    questions_completed = Column(Integer, default=0)
    
    # Performance metrics
    overall_score = Column(Float, nullable=True)  # Average score across questions
    confidence_level = Column(Integer, nullable=True)  # User-reported confidence (1-10)
    
    # Session data (JSON as TEXT for SQLite)
    session_data = Column(Text, nullable=True)  # JSON with detailed session information
    feedback_summary = Column(Text, nullable=True)  # AI-generated session feedback
    
    # Status
    status = Column(String(20), default="in_progress")  # in_progress, completed, abandoned
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<InterviewSession {self.session_type} for kit {self.kit_id}>"


class CompanyInsight(Base):
    """Company research and culture insights."""
    
    __tablename__ = "company_insights"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String(200), nullable=False, index=True)
    
    # Company information (JSON as TEXT for SQLite)
    culture_info = Column(Text, nullable=True)  # JSON with culture insights
    values = Column(Text, nullable=True)  # JSON array of company values
    interview_process = Column(Text, nullable=True)  # JSON with interview process info
    recent_news = Column(Text, nullable=True)  # JSON array of recent company news
    
    # AI-generated insights
    key_talking_points = Column(Text, nullable=True)  # JSON array of talking points
    questions_to_ask = Column(Text, nullable=True)  # JSON array of questions to ask interviewer
    red_flags = Column(Text, nullable=True)  # JSON array of potential concerns
    
    # Metadata
    data_sources = Column(Text, nullable=True)  # JSON array of data sources used
    confidence_score = Column(Float, nullable=True)  # Confidence in data accuracy (0-100)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<CompanyInsight for {self.company_name}>"