"""
Resume-related database models.
Includes Resume, ResumeScorecard, and ResumeShareLink.
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean
from sqlalchemy.sql import func
import uuid
import json
from app.core.database import Base


class Resume(Base):
    """Resume/CV uploaded by user."""
    
    __tablename__ = "resumes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    mime_type = Column(String(100), nullable=False)
    raw_text = Column(Text, nullable=True)  # Extracted text
    parsed_data = Column(Text, nullable=True)  # JSON as TEXT for SQLite
    is_parsed = Column(Boolean, default=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    parsed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Resume {self.filename} for user {self.user_id}>"


class ResumeScorecard(Base):
    """ATS score and analysis for a resume."""
    
    __tablename__ = "resume_scorecards"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = Column(String(36), nullable=False, index=True, unique=True)
    user_id = Column(String(36), nullable=False, index=True)
    
    # Overall score
    ats_score = Column(Integer, nullable=False)  # 0-100
    
    # Score breakdown
    contact_score = Column(Integer, nullable=False)  # 0-20
    sections_score = Column(Integer, nullable=False)  # 0-20
    keywords_score = Column(Integer, nullable=False)  # 0-30
    formatting_score = Column(Integer, nullable=False)  # 0-15
    impact_score = Column(Integer, nullable=False)  # 0-15
    
    # Detailed analysis (JSON as TEXT for SQLite)
    missing_keywords = Column(Text, nullable=True)  # JSON array of missing keywords
    formatting_issues = Column(Text, nullable=True)  # JSON array of issues
    suggestions = Column(Text, nullable=True)  # JSON array of improvement suggestions
    strengths = Column(Text, nullable=True)  # JSON array of strengths
    
    # Metadata
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ResumeScorecard {self.ats_score}/100 for resume {self.resume_id}>"


class ResumeShareLink(Base):
    """Shareable public link for resume score."""
    
    __tablename__ = "resume_share_links"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    share_token = Column(String(64), nullable=False, unique=True, index=True)
    
    # Privacy settings
    is_active = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_viewed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<ResumeShareLink {self.share_token} for resume {self.resume_id}>"
