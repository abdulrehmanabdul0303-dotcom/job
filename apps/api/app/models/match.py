"""
Job matching database models.
Includes JobMatch for storing match scores and explanations.
"""
from sqlalchemy import Column, String, DateTime, Float, Text
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class JobMatch(Base):
    """Job match score and explanation for a user."""
    
    __tablename__ = "job_matches"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    job_id = Column(String(36), nullable=False, index=True)
    resume_id = Column(String(36), nullable=False, index=True)
    
    # Match score (0-100)
    match_score = Column(Float, nullable=False)
    
    # Score breakdown (JSON)
    score_breakdown = Column(Text, nullable=True)  # JSON: {tf_idf, skill_overlap, location_bonus, etc}
    
    # Explanation (JSON)
    why_json = Column(Text, nullable=True)  # JSON: {reasons: [...], strengths: [...]}
    
    # Missing skills (JSON array)
    missing_skills_json = Column(Text, nullable=True)  # JSON: ["skill1", "skill2", ...]
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<JobMatch user={self.user_id} job={self.job_id} score={self.match_score}>"
