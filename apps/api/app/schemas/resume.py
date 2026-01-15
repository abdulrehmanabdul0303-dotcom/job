"""
Resume-related Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class ResumeUploadResponse(BaseModel):
    """Response after successful resume upload."""
    id: UUID
    filename: str
    file_size: int
    uploaded_at: datetime
    is_parsed: bool
    message: str = "Resume uploaded successfully. Parsing in progress..."


class ParsedResumeUpload(BaseModel):
    """Request model for uploading pre-parsed resume data."""
    filename: str
    parsed_data: str
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None


class ParsedProfile(BaseModel):
    """Structured profile data extracted from resume."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)


class ResumeDetail(BaseModel):
    """Detailed resume information."""
    id: UUID
    filename: str
    file_size: int
    mime_type: str
    is_parsed: bool
    uploaded_at: datetime
    parsed_at: Optional[datetime] = None
    parsed_data: Optional[ParsedProfile] = None


class ATSScoreBreakdown(BaseModel):
    """Detailed ATS score breakdown."""
    contact_score: int = Field(..., ge=0, le=20, description="Contact info completeness (0-20)")
    sections_score: int = Field(..., ge=0, le=20, description="Required sections present (0-20)")
    keywords_score: int = Field(..., ge=0, le=30, description="Industry keywords found (0-30)")
    formatting_score: int = Field(..., ge=0, le=15, description="ATS-friendly formatting (0-15)")
    impact_score: int = Field(..., ge=0, le=15, description="Impact statements quality (0-15)")


class ScorecardDetail(BaseModel):
    """Complete ATS scorecard with analysis."""
    id: UUID
    resume_id: UUID
    ats_score: int = Field(..., ge=0, le=100, description="Overall ATS score (0-100)")
    breakdown: ATSScoreBreakdown
    missing_keywords: List[str] = Field(default_factory=list)
    formatting_issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    calculated_at: datetime


class ShareLinkCreate(BaseModel):
    """Request to create shareable link."""
    resume_id: UUID


class ShareLinkResponse(BaseModel):
    """Response with shareable link details."""
    share_token: str
    share_url: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None


class PublicScorecardView(BaseModel):
    """Public view of scorecard (privacy-safe, no personal info)."""
    ats_score: int
    breakdown: ATSScoreBreakdown
    missing_keywords: List[str]
    formatting_issues: List[str]
    suggestions: List[str]
    strengths: List[str]
    calculated_at: datetime
    # NO personal info: no name, email, phone, raw CV content


class ResumeListItem(BaseModel):
    """Resume item for list view."""
    id: UUID
    filename: str
    file_size: int
    is_parsed: bool
    uploaded_at: datetime
    ats_score: Optional[int] = None
