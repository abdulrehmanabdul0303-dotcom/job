"""
Application and tracking database models.
Includes ApplyKit and JobActivity for application management.
"""
from sqlalchemy import Column, String, DateTime, Text, Enum as SQLEnum, Integer, Boolean
import sqlalchemy as sa
from sqlalchemy.sql import func
import uuid
from enum import Enum
from app.core.database import Base


class ActivityStatus(str, Enum):
    """Job activity status enum."""
    INTERESTED = "interested"
    APPLIED = "applied"
    REJECTED = "rejected"
    INTERVIEW = "interview"
    OFFER = "offer"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class ApplyKit(Base):
    """Application kit with cover letter and tailored content."""
    
    __tablename__ = "apply_kits"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    job_id = Column(String(36), nullable=False, index=True)
    
    # Application content
    cover_letter = Column(Text, nullable=True)
    tailored_bullets_json = Column(Text, nullable=True)  # JSON array of tailored resume bullets
    qa_json = Column(Text, nullable=True)  # JSON: {question: answer} for common interview questions
    
    # Version tracking (Task 2.1)
    version = Column(sa.Integer, nullable=False, default=1, index=True)
    is_active = Column(sa.Boolean, nullable=False, default=True, index=True)
    parent_version_id = Column(String(36), nullable=True)  # Reference to previous version
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ApplyKit user={self.user_id} job={self.job_id} v{self.version}>"


class JobActivity(Base):
    """Job application activity tracking."""
    
    __tablename__ = "job_activities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    job_id = Column(String(36), nullable=False, index=True)
    
    # Status tracking
    status = Column(
        SQLEnum(ActivityStatus),
        nullable=False,
        default=ActivityStatus.INTERESTED,
        index=True
    )
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<JobActivity user={self.user_id} job={self.job_id} status={self.status}>"
