"""
AI Resume Versioning API endpoints.
Handles job-specific resume optimization and version management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.ai.resume_versioning import ResumeVersioningEngine
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response

class ResumeVersionRequest(BaseModel):
    """Request model for resume version generation."""
    optimization_focus: Optional[List[str]] = Field(
        default=["keywords", "ats_score", "relevance"],
        description="Areas to focus optimization on"
    )
    regenerate: bool = Field(
        default=False,
        description="Whether to regenerate if version already exists"
    )

class ResumeVersionResponse(BaseModel):
    """Response model for resume version."""
    id: str
    job_id: str
    base_resume_id: str
    optimized_content: dict
    changes_explanation: str
    ats_score: float
    match_score: float
    keyword_density: dict
    formats: dict
    version_number: int
    created_at: str
    updated_at: Optional[str]

class VersionComparisonResponse(BaseModel):
    """Response model for version comparison."""
    version_a: dict
    version_b: dict
    comparison: dict

# Initialize the resume versioning engine
resume_engine = ResumeVersioningEngine()


@router.post("/resume/version/{job_id}", response_model=ResumeVersionResponse)
async def generate_resume_version(
    job_id: str,
    request: ResumeVersionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a job-specific resume version.
    
    This endpoint creates an optimized resume version tailored for a specific job posting.
    The AI system analyzes the job requirements and optimizes the user's resume for:
    - ATS compatibility
    - Keyword density
    - Content relevance
    - Formatting improvements
    """
    try:
        logger.info(f"Generating resume version for user {current_user.id}, job {job_id}")
        
        # Get user's primary resume
        from sqlalchemy import select
        from app.models.resume import Resume
        
        result = await db.execute(
            select(Resume).where(
                Resume.user_id == current_user.id,
                Resume.is_parsed == True
            ).order_by(Resume.uploaded_at.desc())
        )
        base_resume = result.scalar_one_or_none()
        
        if not base_resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No parsed resume found. Please upload and parse a resume first."
            )
        
        # Generate the version
        version_data = await resume_engine.generate_version(
            db=db,
            user_id=current_user.id,
            job_id=job_id,
            base_resume_id=base_resume.id,
            optimization_focus=request.optimization_focus,
            regenerate=request.regenerate
        )
        
        logger.info(f"Resume version generated successfully: {version_data['id']}")
        return ResumeVersionResponse(**version_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is (they have proper status codes)
        raise
    except ValueError as e:
        logger.error(f"ValueError in resume version generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating resume version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate resume version. Please try again."
        )


@router.get("/resume/version/{job_id}", response_model=Optional[ResumeVersionResponse])
async def get_resume_version(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get existing resume version for a specific job.
    
    Returns the most recent resume version created for the specified job,
    or null if no version exists.
    """
    try:
        logger.info(f"Retrieving resume version for user {current_user.id}, job {job_id}")
        
        version_data = await resume_engine.get_version(
            db=db,
            user_id=current_user.id,
            job_id=job_id
        )
        
        if version_data:
            return ResumeVersionResponse(**version_data)
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error retrieving resume version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resume version."
        )


@router.get("/resume/versions", response_model=List[ResumeVersionResponse])
async def list_resume_versions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all resume versions for the current user.
    
    Returns a list of all resume versions created by the user,
    ordered by creation date (most recent first).
    """
    try:
        logger.info(f"Listing resume versions for user {current_user.id}")
        
        from sqlalchemy import select
        from app.models.ai_resume import AIResumeVersion
        
        result = await db.execute(
            select(AIResumeVersion)
            .where(
                AIResumeVersion.user_id == current_user.id,
                AIResumeVersion.is_active == True
            )
            .order_by(AIResumeVersion.created_at.desc())
        )
        versions = result.scalars().all()
        
        version_list = []
        for version in versions:
            version_data = await resume_engine._format_version_response(version)
            version_list.append(ResumeVersionResponse(**version_data))
        
        logger.info(f"Found {len(version_list)} resume versions")
        return version_list
        
    except Exception as e:
        logger.error(f"Error listing resume versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resume versions."
        )


@router.get("/resume/compare/{version_a_id}/{version_b_id}", response_model=VersionComparisonResponse)
async def compare_resume_versions(
    version_a_id: str,
    version_b_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Compare two resume versions.
    
    Provides a detailed comparison between two resume versions, including:
    - Content differences
    - Score comparisons (ATS, match scores)
    - Similarity analysis
    """
    try:
        logger.info(f"Comparing resume versions {version_a_id} vs {version_b_id}")
        
        comparison_data = await resume_engine.compare_versions(
            db=db,
            user_id=current_user.id,
            version_a_id=version_a_id,
            version_b_id=version_b_id
        )
        
        return VersionComparisonResponse(**comparison_data)
        
    except ValueError as e:
        logger.error(f"ValueError in version comparison: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error comparing resume versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare resume versions."
        )


@router.delete("/resume/version/{version_id}")
async def delete_resume_version(
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a resume version.
    
    Soft deletes a resume version by marking it as inactive.
    The version data is retained for audit purposes.
    """
    try:
        logger.info(f"Deleting resume version {version_id} for user {current_user.id}")
        
        from sqlalchemy import select, update
        from app.models.ai_resume import AIResumeVersion
        
        # Check if version exists and belongs to user
        result = await db.execute(
            select(AIResumeVersion).where(
                AIResumeVersion.id == version_id,
                AIResumeVersion.user_id == current_user.id
            )
        )
        version = result.scalar_one_or_none()
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume version not found."
            )
        
        # Soft delete by marking as inactive
        await db.execute(
            update(AIResumeVersion)
            .where(AIResumeVersion.id == version_id)
            .values(is_active=False)
        )
        
        await db.commit()
        
        logger.info(f"Resume version {version_id} deleted successfully")
        return {"message": "Resume version deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resume version: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resume version."
        )


@router.get("/resume/analytics/{job_id}")
async def get_resume_analytics(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get analytics for resume versions for a specific job.
    
    Provides insights into resume optimization performance including:
    - Score improvements over time
    - Optimization effectiveness
    - Processing statistics
    """
    try:
        logger.info(f"Getting resume analytics for user {current_user.id}, job {job_id}")
        
        from sqlalchemy import select, func
        from app.models.ai_resume import AIResumeVersion, ResumeOptimizationLog
        
        # Get all versions for this job
        versions_result = await db.execute(
            select(AIResumeVersion)
            .where(
                AIResumeVersion.user_id == current_user.id,
                AIResumeVersion.job_id == job_id
            )
            .order_by(AIResumeVersion.created_at.asc())
        )
        versions = versions_result.scalars().all()
        
        if not versions:
            return {
                "job_id": job_id,
                "total_versions": 0,
                "score_progression": [],
                "optimization_stats": {}
            }
        
        # Get optimization logs
        logs_result = await db.execute(
            select(ResumeOptimizationLog)
            .where(ResumeOptimizationLog.user_id == current_user.id)
            .order_by(ResumeOptimizationLog.created_at.desc())
        )
        logs = logs_result.scalars().all()
        
        # Calculate analytics
        score_progression = [
            {
                "version_id": v.id,
                "ats_score": v.ats_score,
                "match_score": v.match_score,
                "created_at": v.created_at.isoformat()
            }
            for v in versions
        ]
        
        optimization_stats = {
            "total_optimizations": len(logs),
            "success_rate": (sum(1 for log in logs if log.success) / len(logs) * 100) if logs else 0,
            "avg_processing_time_ms": sum(log.processing_time_ms or 0 for log in logs) / len(logs) if logs else 0,
            "best_ats_score": max(v.ats_score for v in versions),
            "best_match_score": max(v.match_score for v in versions)
        }
        
        return {
            "job_id": job_id,
            "total_versions": len(versions),
            "score_progression": score_progression,
            "optimization_stats": optimization_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting resume analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resume analytics."
        )