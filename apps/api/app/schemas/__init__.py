"""Pydantic schemas package."""
from app.schemas.auth import Token, UserCreate, UserLogin, UserResponse
from app.schemas.resume import (
    ResumeUploadResponse,
    ResumeListItem,
    ResumeDetail,
    ScorecardDetail,
    ShareLinkResponse,
    PublicScorecardView,
)
from app.schemas.preferences import (
    PreferencesCreate,
    PreferencesUpdate,
    PreferencesResponse,
    PreferencesUpdateConfirmation,
)

__all__ = [
    "Token",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "ResumeUploadResponse",
    "ResumeListItem",
    "ResumeDetail",
    "ScorecardDetail",
    "ShareLinkResponse",
    "PublicScorecardView",
    "PreferencesCreate",
    "PreferencesUpdate",
    "PreferencesResponse",
    "PreferencesUpdateConfirmation",
]
