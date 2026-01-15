"""
User preferences database model.
Stores job search preferences for matching engine.
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class UserPreferences(Base):
    """User job search preferences."""
    
    __tablename__ = "user_preferences"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, unique=True, index=True)
    
    # Job search criteria - COMPATIBILITY: Support both old and new fields
    desired_role = Column(String(255), nullable=True)
    desired_roles = Column(Text, nullable=True)  # JSON array as TEXT
    desired_locations = Column(Text, nullable=True)  # JSON array as TEXT
    desired_seniority = Column(Text, nullable=True)  # JSON array as TEXT
    desired_industries = Column(Text, nullable=True)  # JSON array as TEXT
    desired_company_size = Column(Text, nullable=True)  # JSON array as TEXT
    
    preferred_countries = Column(Text, nullable=True)  # JSON array as TEXT for SQLite
    min_salary = Column(Integer, nullable=True)
    max_salary = Column(Integer, nullable=True)
    work_type = Column(String(50), nullable=True)  # remote, full-time, part-time, hybrid, contract
    
    # Additional preferences from tests
    remote_preference = Column(String(50), nullable=True)
    willing_to_relocate = Column(Boolean, nullable=True)
    job_types = Column(Text, nullable=True)  # JSON array as TEXT
    benefits_important = Column(Text, nullable=True)  # JSON array as TEXT
    skills_to_develop = Column(Text, nullable=True)  # JSON array as TEXT
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<UserPreferences for user {self.user_id}>"
