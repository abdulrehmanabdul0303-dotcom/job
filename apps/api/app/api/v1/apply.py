"""
Apply kit and job activity API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.services.apply_service import ApplyKitService, ActivityService
from app.services.pdf_generator import PDFGenerator  # Task 2.5
from app.schemas.apply import (
    GenerateApplyKitRequest,
    GenerateApplyKitResponse,
    ApplyKitResponse,
    ApplyKitUpdate,
    SetActivityStatusRequest,
    SetActivityStatusResponse,
    JobActivityResponse,
    JobActivityListResponse,
    ActivityStatusEnum,
)
from app.models.user import User
from app.models.apply import ActivityStatus
from app.models.job import JobPosting
from typing import Dict
import math
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Apply Kit Endpoints
@router.post("/applykit/{job_id}/generate", response_model=GenerateApplyKitResponse)
async def generate_apply_kit(
    job_id: str,
    request: GenerateApplyKitRequest,
    regenerate: bool = Query(False, description="Force regenerate even if exists"),  # Task 2.2
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate an apply kit for a job.
    
    Task 2.2: Added regenerate parameter for version management.
    
    Generates:
    - Tailored cover letter
    - Tailored resume bullets
    - Interview Q&A
    
    Args:
        job_id: Job ID
        request: Generation request with optional resume_id
        regenerate: If True, create new version even if one exists
        
    Returns:
        Generated apply kit content
    """
    try:
        result = await ApplyKitService.generate_apply_kit(
            db=db,
            user_id=current_user.id,
            job_id=job_id,
            resume_id=request.resume_id,
            regenerate=regenerate,  # Task 2.2
        )
        
        await db.commit()
        
        return GenerateApplyKitResponse(
            apply_kit_id=result['apply_kit_id'],
            job_id=job_id,
            cover_letter=result['cover_letter'],
            tailored_bullets=result['tailored_bullets'],
            qa=result['qa'],
            message=f"Apply kit {'regenerated' if regenerate else 'generated'} successfully (v{result.get('version', 1)})",
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating apply kit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating apply kit"
        )


@router.get("/applykit/{job_id}", response_model=ApplyKitResponse)
async def get_apply_kit(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get apply kit for a job.
    
    Args:
        job_id: Job ID
        
    Returns:
        Apply kit details
    """
    try:
        apply_kit = await ApplyKitService.get_apply_kit(
            db=db,
            user_id=current_user.id,
            job_id=job_id,
        )
        
        if not apply_kit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Apply kit not found"
            )
        
        return apply_kit
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching apply kit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching apply kit"
        )


@router.put("/applykit/{job_id}", response_model=ApplyKitResponse)
async def update_apply_kit(
    job_id: str,
    request: ApplyKitUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update apply kit for a job.
    
    Args:
        job_id: Job ID
        request: Update request
        
    Returns:
        Updated apply kit
    """
    try:
        apply_kit = await ApplyKitService.update_apply_kit(
            db=db,
            user_id=current_user.id,
            job_id=job_id,
            cover_letter=request.cover_letter,
            tailored_bullets=request.tailored_bullets_json,
            qa=request.qa_json,
        )
        
        if not apply_kit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Apply kit not found"
            )
        
        await db.commit()
        
        return apply_kit
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating apply kit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating apply kit"
        )


@router.delete("/applykit/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_apply_kit(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete apply kit for a job.
    
    Args:
        job_id: Job ID
        
    Returns:
        204 No Content on success
    """
    try:
        deleted = await ApplyKitService.delete_apply_kit(
            db=db,
            user_id=current_user.id,
            job_id=job_id,
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Apply kit not found"
            )
        
        await db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting apply kit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting apply kit"
        )


# Task 2.2: Version History Endpoints
@router.get("/applykit/{job_id}/versions", response_model=list)
async def get_version_history(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all versions of apply kit for a job.
    
    Task 2.2: Version history endpoint.
    
    Args:
        job_id: Job ID
        
    Returns:
        List of all versions with metadata
    """
    try:
        versions = await ApplyKitService.get_version_history(
            db=db,
            user_id=current_user.id,
            job_id=job_id,
        )
        
        return [
            {
                'id': v.id,
                'version': v.version,
                'is_active': v.is_active,
                'created_at': v.created_at.isoformat(),
                'updated_at': v.updated_at.isoformat() if v.updated_at else None,
                'parent_version_id': v.parent_version_id,
            }
            for v in versions
        ]
        
    except Exception as e:
        logger.error(f"Error fetching version history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching version history"
        )


@router.get("/applykit/{job_id}/version/{version_number}", response_model=ApplyKitResponse)
async def get_specific_version(
    job_id: str,
    version_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific version of apply kit.
    
    Task 2.2: Specific version retrieval.
    
    Args:
        job_id: Job ID
        version_number: Version number to retrieve
        
    Returns:
        Apply kit for the specified version
    """
    try:
        apply_kit = await ApplyKitService.get_specific_version(
            db=db,
            user_id=current_user.id,
            job_id=job_id,
            version_number=version_number,
        )
        
        if not apply_kit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_number} not found"
            )
        
        return apply_kit
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching specific version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching specific version"
        )


@router.post("/applykit/{job_id}/version/{version_number}/activate", response_model=ApplyKitResponse)
async def activate_version(
    job_id: str,
    version_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate a specific version (deactivate others).
    
    Task 2.2: Version activation endpoint.
    
    Args:
        job_id: Job ID
        version_number: Version number to activate
        
    Returns:
        Activated apply kit
    """
    try:
        apply_kit = await ApplyKitService.activate_version(
            db=db,
            user_id=current_user.id,
            job_id=job_id,
            version_number=version_number,
        )
        
        if not apply_kit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_number} not found"
            )
        
        await db.commit()
        
        return apply_kit
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error activating version"
        )


@router.get("/applykit/{job_id}/download/pdf")
async def download_apply_kit_pdf(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download apply kit as PDF.
    
    Task 2.5: PDF download endpoint.
    
    Args:
        job_id: Job ID
        
    Returns:
        PDF file as streaming response
    """
    try:
        # Get active apply kit
        apply_kit = await ApplyKitService.get_apply_kit(
            db=db,
            user_id=current_user.id,
            job_id=job_id,
        )
        
        if not apply_kit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Apply kit not found"
            )
        
        # Get job details for PDF header
        job_result = await db.execute(
            select(JobPosting).where(JobPosting.id == job_id)
        )
        job = job_result.scalar_one_or_none()
        
        job_title = job.title if job else "Position"
        company_name = job.company if job else "Company"
        
        # Parse JSON fields
        tailored_bullets = json.loads(apply_kit.tailored_bullets_json) if apply_kit.tailored_bullets_json else []
        qa = json.loads(apply_kit.qa_json) if apply_kit.qa_json else {}
        
        # Generate PDF
        pdf_buffer = PDFGenerator.generate_apply_kit_pdf(
            cover_letter=apply_kit.cover_letter or "",
            tailored_bullets=tailored_bullets,
            qa=qa,
            job_title=job_title,
            company_name=company_name,
        )
        
        # Prepare filename
        safe_company = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"ApplyKit_{safe_company}_{safe_title}_v{apply_kit.version}.{PDFGenerator.get_file_extension()}"
        
        # Return streaming response
        return StreamingResponse(
            pdf_buffer,
            media_type=PDFGenerator.get_content_type(),
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating PDF"
        )


# Job Activity Endpoints
@router.post("/tracker/{job_id}", response_model=SetActivityStatusResponse)
async def set_activity_status(
    job_id: str,
    request: SetActivityStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Set or update job activity status.
    
    Args:
        job_id: Job ID
        request: Status update request
        
    Returns:
        Updated activity
    """
    try:
        # Convert string status to enum
        status_enum = ActivityStatus(request.status.value)
        
        activity = await ActivityService.set_activity_status(
            db=db,
            user_id=current_user.id,
            job_id=job_id,
            status=status_enum,
            notes=request.notes,
        )
        
        await db.commit()
        
        return SetActivityStatusResponse(
            activity_id=activity.id,
            job_id=job_id,
            status=ActivityStatusEnum(activity.status.value),
            message=f"Status updated to {activity.status.value}",
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error setting activity status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error setting activity status"
        )


@router.get("/tracker", response_model=JobActivityListResponse)
async def get_activities(
    status: str = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's job activities with pagination.
    
    Args:
        status: Optional status filter
        page: Page number
        page_size: Items per page
        
    Returns:
        Paginated list of activities
    """
    try:
        # Convert status string to enum if provided
        status_enum = None
        if status:
            status_enum = ActivityStatus(status)
        
        activities, total = await ActivityService.get_activities(
            db=db,
            user_id=current_user.id,
            status=status_enum,
            page=page,
            page_size=page_size,
        )
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return JobActivityListResponse(
            activities=activities,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status}"
        )
    except Exception as e:
        logger.error(f"Error fetching activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching activities"
        )


@router.get("/tracker/summary", response_model=Dict[str, int])
async def get_activity_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary of activities by status.
    
    Returns:
        Dictionary with status counts
    """
    try:
        summary = await ActivityService.get_activity_summary(
            db=db,
            user_id=current_user.id,
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Error fetching activity summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching activity summary"
        )
