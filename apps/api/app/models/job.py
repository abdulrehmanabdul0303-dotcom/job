"""
Job-related database models.
Includes JobSource and JobPosting.
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class JobSource(Base):
    """Job source configuration (RSS feeds, APIs, company pages)."""
    
    __tablename__ = "job_sources"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # rss, api, html
    url = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    fetch_frequency_hours = Column(Integer, default=24, nullable=False)
    
    # Metadata
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
    last_fetch_status = Column(String(50), nullable=True)  # success, failed
    last_fetch_error = Column(Text, nullable=True)
    jobs_fetched_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<JobSource {self.name} ({self.source_type})>"


class JobPosting(Base):
    """Job posting fetched from external sources."""
    
    __tablename__ = "job_postings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), nullable=False, index=True)
    
    # Job details
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    
    # Salary (optional)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String(10), nullable=True)
    
    # Work type
    work_type = Column(String(50), nullable=True)  # remote, full-time, part-time, hybrid, contract
    
    # URLs
    application_url = Column(String(500), nullable=False)
    url_hash = Column(String(64), nullable=False, unique=True, index=True)  # For deduplication
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    posted_date = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    raw_data = Column(Text, nullable=True)  # JSON string of original data
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<JobPosting {self.title} at {self.company}>"
