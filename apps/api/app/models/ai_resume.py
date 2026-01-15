"""
AI Resume Versioning models.
Handles job-specific resume versions and optimization.
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean, Float
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class AIResumeVersion(Base):
    """AI-generated job-specific resume version."""
    
    __tablename__ = "ai_resume_versions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    job_id = Column(String(36), nullable=False, index=True)
    base_resume_id = Column(String(36), nullable=False, index=True)
    
    # Optimized content (JSON as TEXT for SQLite)
    optimized_content = Column(Text, nullable=False)  # JSON with optimized resume sections
    changes_explanation = Column(Text, nullable=False)  # Explanation of changes made
    
    # Scoring and metrics
    ats_score = Column(Float, nullable=False)  # ATS compatibility score (0-100)
    keyword_density = Column(Text, nullable=True)  # JSON with keyword analysis
    match_score = Column(Float, nullable=False)  # Job match score (0-100)
    
    # Generated formats (JSON as TEXT for SQLite)
    formats = Column(Text, nullable=True)  # JSON with URLs to different formats (PDF, DOCX, TXT)
    
    # Metadata
    version_number = Column(Integer, default=1)  # Version number for this job
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<AIResumeVersion {self.id} for job {self.job_id}>"


class ResumeOptimizationLog(Base):
    """Log of resume optimization operations."""
    
    __tablename__ = "resume_optimization_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String(36), nullable=True, index=True)  # Allow NULL for error logs
    user_id = Column(String(36), nullable=False, index=True)
    
    # Operation details
    operation_type = Column(String(50), nullable=False)  # generate, regenerate, update
    processing_time_ms = Column(Integer, nullable=True)  # Processing time in milliseconds
    
    # AI processing details (JSON as TEXT for SQLite)
    ai_parameters = Column(Text, nullable=True)  # JSON with AI processing parameters
    optimization_focus = Column(Text, nullable=True)  # JSON array of optimization areas
    
    # Results
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ResumeOptimizationLog {self.operation_type} for version {self.version_id}>"


class ResumeVersionComparison(Base):
    """Comparison between resume versions."""
    
    __tablename__ = "resume_version_comparisons"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    version_a_id = Column(String(36), nullable=False, index=True)
    version_b_id = Column(String(36), nullable=False, index=True)
    
    # Comparison results (JSON as TEXT for SQLite)
    differences = Column(Text, nullable=False)  # JSON with detailed differences
    similarity_score = Column(Float, nullable=False)  # Similarity score (0-100)
    
    # Performance comparison
    ats_score_diff = Column(Float, nullable=True)  # ATS score difference
    match_score_diff = Column(Float, nullable=True)  # Match score difference
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ResumeVersionComparison {self.version_a_id} vs {self.version_b_id}>"