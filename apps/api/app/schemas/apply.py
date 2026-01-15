"""
Application and tracking Pydantic schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ActivityStatusEnum(str, Enum):
    """Activity status enum for schemas."""
    INTERESTED = "interested"
    APPLIED = "applied"
    REJECTED = "rejected"
    INTERVIEW = "interview"
    OFFER = "offer"
    ACCEPTED = "accepted"
    DECLINED = "declined"


# Apply Kit Schemas
class ApplyKitBase(BaseModel):
    """Base schema for apply kit."""
    cover_letter: Optional[str] = Field(None, description="Generated cover letter")
    tailored_bullets_json: Optional[List[str]] = Field(None, description="Tailored resume bullets")
    qa_json: Optional[Dict[str, str]] = Field(None, description="Q&A for interview prep")


class ApplyKitCreate(ApplyKitBase):
    """Schema for creating apply kit."""
    pass


class ApplyKitUpdate(BaseModel):
    """Schema for updating apply kit."""
    cover_letter: Optional[str] = None
    tailored_bullets_json: Optional[List[str]] = None
    qa_json: Optional[Dict[str, str]] = None


class ApplyKitResponse(ApplyKitBase):
    """Schema for apply kit response."""
    id: str
    user_id: str
    job_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GenerateApplyKitRequest(BaseModel):
    """Request to generate apply kit."""
    resume_id: Optional[str] = Field(None, description="Specific resume to use")


class GenerateApplyKitResponse(BaseModel):
    """Response after generating apply kit."""
    apply_kit_id: str
    job_id: str
    cover_letter: Optional[str] = None
    tailored_bullets: Optional[List[str]] = None
    qa: Optional[Dict[str, str]] = None
    message: str


# Job Activity Schemas
class JobActivityBase(BaseModel):
    """Base schema for job activity."""
    status: ActivityStatusEnum = Field(..., description="Activity status")
    notes: Optional[str] = Field(None, description="Additional notes")


class JobActivityCreate(JobActivityBase):
    """Schema for creating job activity."""
    pass


class JobActivityUpdate(BaseModel):
    """Schema for updating job activity."""
    status: Optional[ActivityStatusEnum] = None
    notes: Optional[str] = None


class JobActivityResponse(JobActivityBase):
    """Schema for job activity response."""
    id: str
    user_id: str
    job_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class JobActivityListResponse(BaseModel):
    """Response for paginated activity listing."""
    activities: List[JobActivityResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SetActivityStatusRequest(BaseModel):
    """Request to set activity status."""
    status: ActivityStatusEnum = Field(..., description="New status")
    notes: Optional[str] = Field(None, description="Optional notes")


class SetActivityStatusResponse(BaseModel):
    """Response after setting activity status."""
    activity_id: str
    job_id: str
    status: ActivityStatusEnum
    message: str


# Combined Job Detail Response
class JobDetailWithApplyKit(BaseModel):
    """Job detail with apply kit and activity."""
    job_id: str
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    work_type: Optional[str] = None
    application_url: str
    
    # Apply kit
    apply_kit: Optional[ApplyKitResponse] = None
    
    # Activity
    activity: Optional[JobActivityResponse] = None
    
    class Config:
        from_attributes = True
