"""
Job-related Pydantic schemas.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import html


# Job Source Schemas
class JobSourceBase(BaseModel):
    """Base schema for job source."""
    name: str = Field(..., max_length=255, description="Source name")
    source_type: str = Field(..., description="Source type: rss, api, html")
    url: str = Field(..., max_length=500, description="Source URL")
    is_active: bool = Field(True, description="Whether source is active")
    fetch_frequency_hours: int = Field(24, ge=1, le=168, description="Fetch frequency in hours (1-168)")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate and sanitize name field to prevent XSS."""
        if v:
            # HTML escape to prevent XSS attacks
            return html.escape(v)
        return v
    
    @field_validator('source_type')
    @classmethod
    def validate_source_type(cls, v):
        """Validate source type."""
        allowed = ['rss', 'api', 'html']
        if v not in allowed:
            raise ValueError(f"source_type must be one of: {', '.join(allowed)}")
        return v


class JobSourceCreate(JobSourceBase):
    """Schema for creating job source."""
    pass


class JobSourceUpdate(BaseModel):
    """Schema for updating job source."""
    name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    fetch_frequency_hours: Optional[int] = Field(None, ge=1, le=168)


class JobSourceResponse(JobSourceBase):
    """Schema for job source response."""
    id: str
    last_fetched_at: Optional[datetime] = None
    last_fetch_status: Optional[str] = None
    last_fetch_error: Optional[str] = None
    jobs_fetched_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Job Posting Schemas
class JobPostingBase(BaseModel):
    """Base schema for job posting."""
    title: str = Field(..., max_length=255)
    company: str = Field(..., max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    salary_currency: Optional[str] = Field(None, max_length=10)
    work_type: Optional[str] = None
    application_url: str = Field(..., max_length=500)
    posted_date: Optional[datetime] = None


class JobPostingResponse(JobPostingBase):
    """Schema for job posting response."""
    id: str
    source_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class JobPostingListResponse(BaseModel):
    """Schema for paginated job listing."""
    jobs: List[JobPostingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobFilters(BaseModel):
    """Schema for job filtering."""
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    work_type: Optional[str] = None
    min_salary: Optional[int] = None
    source_id: Optional[str] = None
    is_active: Optional[bool] = True
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class FetchJobsResponse(BaseModel):
    """Response after fetching jobs from a source."""
    source_id: str
    source_name: str
    jobs_fetched: int
    jobs_new: int
    jobs_updated: int
    status: str
    message: str
