"""
Job sources and postings API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.auth import get_current_user_from_cookie
from app.services.job_service import JobService
from app.schemas.job import (
    JobSourceCreate,
    JobSourceUpdate,
    JobSourceResponse,
    JobPostingResponse,
    JobPostingListResponse,
    JobFilters,
    FetchJobsResponse,
)
from app.models.user import User
from typing import List
import math

router = APIRouter()


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Get current user from cookie-based auth."""
    return await get_current_user_from_cookie(request, db)


# Job Sources Endpoints
@router.post("/sources", response_model=JobSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_job_source(
    source_data: JobSourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new job source.
    Only authenticated users can create sources.
    
    Args:
        source_data: Job source configuration
        
    Returns:
        Created job source
    """
    source = await JobService.create_source(db, source_data)
    await db.commit()
    return source


@router.get("/sources", response_model=List[JobSourceResponse])
async def get_job_sources(
    active_only: bool = Query(False, description="Filter active sources only"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all job sources.
    
    Args:
        active_only: If True, return only active sources
        
    Returns:
        List of job sources
    """
    sources = await JobService.get_sources(db, active_only=active_only)
    return sources


@router.get("/sources/{source_id}", response_model=JobSourceResponse)
async def get_job_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific job source by ID.
    
    Args:
        source_id: Job source ID
        
    Returns:
        Job source details
    """
    source = await JobService.get_source_by_id(db, source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job source not found"
        )
    return source


@router.put("/sources/{source_id}", response_model=JobSourceResponse)
async def update_job_source(
    source_id: str,
    source_data: JobSourceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a job source.
    
    Args:
        source_id: Job source ID
        source_data: Updated source data
        
    Returns:
        Updated job source
    """
    source = await JobService.update_source(db, source_id, source_data)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job source not found"
        )
    await db.commit()
    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a job source.
    
    Args:
        source_id: Job source ID
        
    Returns:
        204 No Content on success
    """
    deleted = await JobService.delete_source(db, source_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job source not found"
        )
    await db.commit()
    return None


@router.post("/sources/{source_id}/fetch", response_model=FetchJobsResponse)
async def fetch_jobs_from_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger job fetching from a source.
    
    Args:
        source_id: Job source ID
        
    Returns:
        Fetch statistics
    """
    try:
        stats = await JobService.fetch_and_store_jobs(db, source_id)
        await db.commit()
        
        return FetchJobsResponse(
            **stats,
            message=f"Successfully fetched {stats['jobs_new']} new jobs"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching jobs: {str(e)}"
        )


# Job Postings Endpoints
@router.post("/jobs", response_model=JobPostingResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new job posting (for testing and manual job creation).
    
    Args:
        job_data: Job posting data
        
    Returns:
        Created job posting
    """
    from app.models.job import JobPosting
    from uuid import uuid4
    from datetime import datetime
    import hashlib
    
    # Generate URL hash for deduplication
    url_content = f"{job_data.get('title', '')}-{job_data.get('company', '')}-{job_data.get('source', 'manual')}"
    url_hash = hashlib.sha256(url_content.encode()).hexdigest()
    
    # Create job posting
    job = JobPosting(
        id=str(uuid4()),
        source_id="manual-source",  # Default source for manual jobs
        title=job_data.get("title"),
        company=job_data.get("company"),
        location=job_data.get("location"),
        description=job_data.get("description"),
        requirements=job_data.get("requirements"),
        salary_min=job_data.get("salary_min"),
        salary_max=job_data.get("salary_max"),
        work_type=job_data.get("job_type", "full-time"),  # Map job_type to work_type
        application_url=f"https://example.com/apply/{str(uuid4())}",  # Dummy URL
        url_hash=url_hash,
        is_active=True,
        posted_date=datetime.utcnow()
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    return job


@router.get("/jobs", response_model=JobPostingListResponse)
async def get_jobs(
    title: str = Query(None, description="Filter by title"),
    company: str = Query(None, description="Filter by company"),
    location: str = Query(None, description="Filter by location"),
    work_type: str = Query(None, description="Filter by work type"),
    min_salary: int = Query(None, description="Minimum salary"),
    source_id: str = Query(None, description="Filter by source ID"),
    is_active: bool = Query(True, description="Filter active jobs"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get job postings with filtering and pagination.
    
    Args:
        Various filter parameters
        
    Returns:
        Paginated list of job postings
    """
    filters = JobFilters(
        title=title,
        company=company,
        location=location,
        work_type=work_type,
        min_salary=min_salary,
        source_id=source_id,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    
    jobs, total = await JobService.get_jobs(db, filters)
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    return JobPostingListResponse(
        jobs=jobs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/jobs/{job_id}", response_model=JobPostingResponse)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific job posting by ID.
    
    Args:
        job_id: Job posting ID
        
    Returns:
        Job posting details
    """
    from sqlalchemy import select
    from app.models.job import JobPosting
    
    result = await db.execute(
        select(JobPosting).where(JobPosting.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job


@router.post("/jobs/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_import_jobs(
    jobs_data: List[dict],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk import multiple job postings.
    
    Args:
        jobs_data: List of job posting data
        
    Returns:
        Import statistics
    """
    from app.models.job import JobPosting
    from uuid import uuid4
    from datetime import datetime
    import hashlib
    
    created = 0
    skipped = 0
    errors = []
    
    for idx, job_data in enumerate(jobs_data):
        try:
            # Generate URL hash for deduplication
            url_content = f"{job_data.get('title', '')}-{job_data.get('company', '')}-{job_data.get('source', 'bulk')}"
            url_hash = hashlib.sha256(url_content.encode()).hexdigest()
            
            # Check if job already exists
            from sqlalchemy import select
            result = await db.execute(
                select(JobPosting).where(JobPosting.url_hash == url_hash)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                skipped += 1
                continue
            
            # Map employment_type to work_type
            work_type = job_data.get("employment_type", job_data.get("work_type", "full-time"))
            
            # Create job posting
            job = JobPosting(
                id=str(uuid4()),
                source_id=job_data.get("source", "bulk-import"),
                title=job_data.get("title"),
                company=job_data.get("company"),
                location=job_data.get("location"),
                description=job_data.get("description"),
                requirements=", ".join(job_data.get("skills", [])) if job_data.get("skills") else None,
                salary_min=job_data.get("salary_min"),
                salary_max=job_data.get("salary_max"),
                work_type=work_type,
                application_url=job_data.get("url", f"https://example.com/apply/{str(uuid4())}"),
                url_hash=url_hash,
                is_active=True,
                posted_date=datetime.utcnow()
            )
            
            db.add(job)
            created += 1
            
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})
    
    await db.commit()
    
    return {
        "success": True,
        "created": created,
        "skipped": skipped,
        "errors": errors,
        "message": f"Imported {created} jobs, skipped {skipped} duplicates"
    }
