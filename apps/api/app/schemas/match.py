"""
Job match Pydantic schemas.
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class MatchScoreBreakdown(BaseModel):
    """Score breakdown components."""
    tf_idf: float = Field(..., ge=0, le=100, description="TF-IDF similarity score (0-100)")
    skill_overlap: float = Field(..., ge=0, le=100, description="Skill overlap percentage (0-100)")
    location_bonus: float = Field(..., ge=0, le=20, description="Location bonus (0-20)")


class MatchExplanation(BaseModel):
    """Match explanation with reasons and strengths."""
    reasons: List[str] = Field(default_factory=list, description="Reasons for the match")
    strengths: List[str] = Field(default_factory=list, description="Strengths of the match")


class JobMatchResponse(BaseModel):
    """Response schema for job match."""
    id: str
    user_id: str
    job_id: str
    resume_id: str
    match_score: float = Field(..., ge=0, le=100, description="Overall match score (0-100)")
    score_breakdown: Optional[Dict[str, float]] = None
    why: Optional[Dict[str, Any]] = None
    missing_skills: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
    
    @model_validator(mode='before')
    @classmethod
    def map_json_fields(cls, data):
        """Map model JSON fields to schema fields and parse JSON strings."""
        if hasattr(data, '__dict__'):
            # SQLAlchemy model object
            result = {
                'id': data.id,
                'user_id': data.user_id,
                'job_id': data.job_id,
                'resume_id': data.resume_id,
                'match_score': data.match_score,
                'created_at': data.created_at,
                'updated_at': data.updated_at,
            }
            # Parse JSON fields
            if hasattr(data, 'score_breakdown') and data.score_breakdown:
                try:
                    result['score_breakdown'] = json.loads(data.score_breakdown) if isinstance(data.score_breakdown, str) else data.score_breakdown
                except (json.JSONDecodeError, TypeError):
                    result['score_breakdown'] = None
            
            if hasattr(data, 'why_json') and data.why_json:
                try:
                    result['why'] = json.loads(data.why_json) if isinstance(data.why_json, str) else data.why_json
                except (json.JSONDecodeError, TypeError):
                    result['why'] = None
            
            if hasattr(data, 'missing_skills_json') and data.missing_skills_json:
                try:
                    result['missing_skills'] = json.loads(data.missing_skills_json) if isinstance(data.missing_skills_json, str) else data.missing_skills_json
                except (json.JSONDecodeError, TypeError):
                    result['missing_skills'] = None
            
            return result
        return data


class JobMatchListResponse(BaseModel):
    """Response for paginated match listing."""
    matches: List[JobMatchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RecomputeMatchesRequest(BaseModel):
    """Request to recompute matches."""
    resume_id: Optional[str] = Field(None, description="Specific resume to match against all jobs")
    min_score: float = Field(0, ge=0, le=100, description="Minimum score threshold to store")


class RecomputeMatchesResponse(BaseModel):
    """Response after recomputing matches."""
    matches_computed: int
    matches_stored: int
    min_score: float
    message: str


class NoMatchesSuggestion(BaseModel):
    """Suggestion when no matches are found."""
    type: str = Field(..., description="Type of suggestion: 'profile', 'preferences', 'resume'")
    title: str = Field(..., description="Short title for the suggestion")
    description: str = Field(..., description="Detailed description of what to do")
    action_url: Optional[str] = Field(None, description="API endpoint or frontend route to take action")


class MatchSuggestionsResponse(BaseModel):
    """Response with suggestions when no/few matches found."""
    has_matches: bool
    match_count: int
    suggestions: List[NoMatchesSuggestion] = Field(default_factory=list)
    message: str
