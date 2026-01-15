"""
Resume API endpoints - upload, parse, score, and share resumes.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from pathlib import Path
from slowapi import Limiter
from slowapi.util import get_remote_address
import os

from app.core.database import get_db
from app.services.auth import get_current_user_from_cookie
from app.services.resume import ResumeService
from app.models.user import User
from app.schemas.resume import (
    ResumeUploadResponse,
    ResumeDetail,
    ResumeListItem,
    ScorecardDetail,
    ShareLinkCreate,
    ShareLinkResponse,
    PublicScorecardView,
    ATSScoreBreakdown,
    ParsedResumeUpload
)
from app.core.config import settings, limit_if_enabled


def is_test_env() -> bool:
    """Check if running in test environment to disable rate limiting."""
    env = os.getenv("ENV", "development").lower()
    return env in {"test", "pytest", "testing"}


# Conditional rate limiting based on environment
def conditional_rate_limit(limit_str: str):
    """Apply rate limiting only in non-test environments."""
    def decorator(func):
        if is_test_env():
            return func
        else:
            return limiter.limit(limit_str)(func)
    return decorator


# SECURITY P0: Rate limiter for upload endpoints
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Get current user from cookie-based auth."""
    return await get_current_user_from_cookie(request, db)


@router.post("/upload-parsed", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
@limit_if_enabled(f"{settings.RATE_LIMIT_UPLOAD_PER_MINUTE}/minute")
async def upload_parsed_resume(
    request: Request,
    request_data: ParsedResumeUpload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload pre-parsed resume data (for testing and API integration).
    Creates a resume record with parsed data directly.
    """
    # Create resume record with parsed data
    resume = await ResumeService.create_parsed_resume(
        db=db,
        user_id=str(current_user.id),
        filename=request_data.filename,
        parsed_content=request_data.parsed_data,
        skills=request_data.skills or [],
        experience_years=request_data.experience_years or 0
    )
    
    # Calculate ATS score
    try:
        await ResumeService.calculate_ats_score(db, resume)
    except Exception as score_error:
        # Log scoring error but don't fail the upload
        import logging
        logging.warning(f"ATS scoring failed for resume {resume.id}: {score_error}")
    
    return ResumeUploadResponse(
        id=resume.id,
        filename=resume.filename,
        file_size=len(request_data.parsed_data.encode('utf-8')),
        uploaded_at=resume.uploaded_at,
        is_parsed=True,
        message="Resume data uploaded and processed successfully!"
    )


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
@limit_if_enabled(f"{settings.RATE_LIMIT_UPLOAD_PER_MINUTE}/minute")
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and parse resume (PDF/DOCX only, max 5MB).
    Automatically triggers parsing and ATS scoring.
    """
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_CV_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_CV_EXTENSIONS)}"
        )
    
    # Validate content type
    allowed_mimes = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword"
    ]
    if file.content_type not in allowed_mimes:
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Upload PDF or DOCX only."
        )
    
    # Save file
    file_path, file_size = await ResumeService.save_uploaded_file(file, str(current_user.id))
    
    # Create resume record
    resume = await ResumeService.create_resume(
        db=db,
        user_id=str(current_user.id),
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type
    )
    
    # Parse resume (synchronous for now, can be async background job later)
    try:
        resume = await ResumeService.parse_resume(db, resume)
        
        # Calculate ATS score
        try:
            await ResumeService.calculate_ats_score(db, resume)
        except Exception as score_error:
            # Log scoring error but don't fail the upload
            import logging
            logging.warning(f"ATS scoring failed for resume {resume.id}: {score_error}")
    except Exception as e:
        # If parsing fails, still return the resume record
        import logging
        logging.warning(f"Resume parsing failed for {resume.id}: {e}")
    
    return ResumeUploadResponse(
        id=resume.id,
        filename=resume.filename,
        file_size=resume.file_size,
        uploaded_at=resume.uploaded_at,
        is_parsed=resume.is_parsed,
        message="Resume uploaded and parsed successfully!" if resume.is_parsed else "Resume uploaded. Parsing in progress..."
    )


@router.get("/list", response_model=List[ResumeListItem])
async def list_resumes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of all user's resumes with ATS scores."""
    resumes = await ResumeService.get_user_resumes(db, str(current_user.id))
    
    result = []
    for resume in resumes:
        # Get scorecard if exists
        scorecard = await ResumeService.get_scorecard(db, resume.id, str(current_user.id))
        
        result.append(ResumeListItem(
            id=resume.id,
            filename=resume.filename,
            file_size=resume.file_size,
            is_parsed=resume.is_parsed,
            uploaded_at=resume.uploaded_at,
            ats_score=scorecard.ats_score if scorecard else None
        ))
    
    return result


@router.get("/{resume_id}", response_model=ResumeDetail)
async def get_resume(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed resume information including parsed data."""
    resume = await ResumeService.get_resume_by_id(db, str(resume_id), str(current_user.id))
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Parse JSON string to dict if needed
    parsed_data = None
    if resume.parsed_data:
        if isinstance(resume.parsed_data, str):
            import json
            parsed_data = json.loads(resume.parsed_data)
        else:
            parsed_data = resume.parsed_data
    
    return ResumeDetail(
        id=resume.id,
        filename=resume.filename,
        file_size=resume.file_size,
        mime_type=resume.mime_type,
        is_parsed=resume.is_parsed,
        uploaded_at=resume.uploaded_at,
        parsed_at=resume.parsed_at,
        parsed_data=parsed_data
    )


@router.get("/{resume_id}/scorecard", response_model=ScorecardDetail)
async def get_scorecard(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ATS scorecard for resume."""
    import json as json_module
    scorecard = await ResumeService.get_scorecard(db, str(resume_id), str(current_user.id))
    
    if not scorecard:
        raise HTTPException(status_code=404, detail="Scorecard not found. Resume may not be parsed yet.")
    
    # Parse JSON strings to lists
    missing_keywords = scorecard.missing_keywords
    if isinstance(missing_keywords, str):
        missing_keywords = json_module.loads(missing_keywords)
    
    formatting_issues = scorecard.formatting_issues
    if isinstance(formatting_issues, str):
        formatting_issues = json_module.loads(formatting_issues)
    
    suggestions = scorecard.suggestions
    if isinstance(suggestions, str):
        suggestions = json_module.loads(suggestions)
    
    strengths = scorecard.strengths
    if isinstance(strengths, str):
        strengths = json_module.loads(strengths)
    
    return ScorecardDetail(
        id=scorecard.id,
        resume_id=scorecard.resume_id,
        ats_score=scorecard.ats_score,
        breakdown=ATSScoreBreakdown(
            contact_score=scorecard.contact_score,
            sections_score=scorecard.sections_score,
            keywords_score=scorecard.keywords_score,
            formatting_score=scorecard.formatting_score,
            impact_score=scorecard.impact_score
        ),
        missing_keywords=missing_keywords or [],
        formatting_issues=formatting_issues or [],
        suggestions=suggestions or [],
        strengths=strengths or [],
        calculated_at=scorecard.calculated_at
    )


@router.post("/{resume_id}/recalculate", response_model=ScorecardDetail)
async def recalculate_score(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recalculate ATS score for resume (useful after editing profile)."""
    import json as json_module
    resume = await ResumeService.get_resume_by_id(db, str(resume_id), str(current_user.id))
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if not resume.is_parsed:
        raise HTTPException(status_code=400, detail="Resume must be parsed first")
    
    # Recalculate score
    scorecard = await ResumeService.calculate_ats_score(db, resume)
    
    # Parse JSON strings to lists
    missing_keywords = scorecard.missing_keywords
    if isinstance(missing_keywords, str):
        missing_keywords = json_module.loads(missing_keywords)
    
    formatting_issues = scorecard.formatting_issues
    if isinstance(formatting_issues, str):
        formatting_issues = json_module.loads(formatting_issues)
    
    suggestions = scorecard.suggestions
    if isinstance(suggestions, str):
        suggestions = json_module.loads(suggestions)
    
    strengths = scorecard.strengths
    if isinstance(strengths, str):
        strengths = json_module.loads(strengths)
    
    return ScorecardDetail(
        id=scorecard.id,
        resume_id=scorecard.resume_id,
        ats_score=scorecard.ats_score,
        breakdown=ATSScoreBreakdown(
            contact_score=scorecard.contact_score,
            sections_score=scorecard.sections_score,
            keywords_score=scorecard.keywords_score,
            formatting_score=scorecard.formatting_score,
            impact_score=scorecard.impact_score
        ),
        missing_keywords=missing_keywords or [],
        formatting_issues=formatting_issues or [],
        suggestions=suggestions or [],
        strengths=strengths or [],
        calculated_at=scorecard.calculated_at
    )


@router.post("/{resume_id}/share", response_model=ShareLinkResponse)
async def create_share_link(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create shareable public link for resume scorecard (privacy-safe)."""
    # Verify resume exists and belongs to user
    resume = await ResumeService.get_resume_by_id(db, str(resume_id), str(current_user.id))
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Verify scorecard exists
    scorecard = await ResumeService.get_scorecard(db, str(resume_id), str(current_user.id))
    if not scorecard:
        raise HTTPException(status_code=400, detail="No scorecard available. Upload and parse resume first.")
    
    # Create share link
    share_link = await ResumeService.create_share_link(db, str(resume_id), str(current_user.id))
    
    # Build share URL
    share_url = f"/resume-score/result/{share_link.share_token}"
    
    return ShareLinkResponse(
        share_token=share_link.share_token,
        share_url=share_url,
        is_active=share_link.is_active,
        created_at=share_link.created_at,
        expires_at=share_link.expires_at
    )


@router.get("/public/{share_token}", response_model=PublicScorecardView)
async def get_public_scorecard(
    share_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get public scorecard by share token.
    NO AUTHENTICATION REQUIRED - Public endpoint.
    Returns privacy-safe data only (no personal info, no raw CV content).
    """
    scorecard_data = await ResumeService.get_public_scorecard(db, share_token)
    
    if not scorecard_data:
        raise HTTPException(
            status_code=404,
            detail="Scorecard not found or link has expired"
        )
    
    return PublicScorecardView(
        ats_score=scorecard_data['ats_score'],
        breakdown=ATSScoreBreakdown(
            contact_score=scorecard_data['contact_score'],
            sections_score=scorecard_data['sections_score'],
            keywords_score=scorecard_data['keywords_score'],
            formatting_score=scorecard_data['formatting_score'],
            impact_score=scorecard_data['impact_score']
        ),
        missing_keywords=scorecard_data['missing_keywords'],
        formatting_issues=scorecard_data['formatting_issues'],
        suggestions=scorecard_data['suggestions'],
        strengths=scorecard_data['strengths'],
        calculated_at=scorecard_data['calculated_at']
    )


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete resume and all associated data."""
    success = await ResumeService.delete_resume(db, str(resume_id), str(current_user.id))
    
    if not success:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return None
