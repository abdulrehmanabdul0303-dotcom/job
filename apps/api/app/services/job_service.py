"""
Job service for database operations.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from app.models.job import JobSource, JobPosting
from app.schemas.job import JobSourceCreate, JobSourceUpdate, JobFilters
from app.services.job_fetcher import JobFetcher
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class JobService:
    """Service for managing job sources and postings."""
    
    @staticmethod
    async def create_source(db: AsyncSession, source_data: JobSourceCreate) -> JobSource:
        """Create a new job source."""
        source = JobSource(**source_data.model_dump())
        db.add(source)
        await db.flush()
        await db.refresh(source)
        return source
    
    @staticmethod
    async def get_sources(db: AsyncSession, active_only: bool = False) -> List[JobSource]:
        """Get all job sources."""
        query = select(JobSource)
        if active_only:
            query = query.where(JobSource.is_active == True)
        query = query.order_by(JobSource.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_source_by_id(db: AsyncSession, source_id: str) -> Optional[JobSource]:
        """Get job source by ID."""
        result = await db.execute(
            select(JobSource).where(JobSource.id == source_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_source(
        db: AsyncSession, 
        source_id: str, 
        source_data: JobSourceUpdate
    ) -> Optional[JobSource]:
        """Update job source."""
        source = await JobService.get_source_by_id(db, source_id)
        if not source:
            return None
        
        update_data = source_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(source, field, value)
        
        await db.flush()
        await db.refresh(source)
        return source
    
    @staticmethod
    async def delete_source(db: AsyncSession, source_id: str) -> bool:
        """Delete job source."""
        source = await JobService.get_source_by_id(db, source_id)
        if not source:
            return False
        
        await db.delete(source)
        await db.flush()
        return True
    
    @staticmethod
    async def fetch_and_store_jobs(db: AsyncSession, source_id: str) -> Dict[str, Any]:
        """
        Fetch jobs from a source and store them in database.
        
        Returns:
            Dictionary with fetch statistics
        """
        source = await JobService.get_source_by_id(db, source_id)
        if not source:
            raise ValueError(f"Source not found: {source_id}")
        
        if not source.is_active:
            raise ValueError(f"Source is not active: {source.name}")
        
        try:
            # Fetch jobs based on source type
            if source.source_type == 'rss':
                jobs_data = await JobFetcher.fetch_rss_jobs(source.url)
            elif source.source_type == 'html':
                jobs_data = await JobFetcher.fetch_html_jobs(source.url)
            else:
                raise ValueError(f"Unsupported source type: {source.source_type}")
            
            # Store jobs with deduplication
            stats = await JobService._store_jobs(db, source_id, jobs_data)
            
            # Update source metadata
            source.last_fetched_at = datetime.utcnow()
            source.last_fetch_status = 'success'
            source.last_fetch_error = None
            source.jobs_fetched_count += stats['new']
            
            await db.flush()
            
            return {
                'source_id': source_id,
                'source_name': source.name,
                'jobs_fetched': len(jobs_data),
                'jobs_new': stats['new'],
                'jobs_updated': stats['updated'],
                'status': 'success',
            }
            
        except Exception as e:
            logger.error(f"Error fetching jobs from source {source.name}: {e}")
            
            # Update source with error
            source.last_fetched_at = datetime.utcnow()
            source.last_fetch_status = 'failed'
            source.last_fetch_error = str(e)
            await db.flush()
            
            raise
    
    @staticmethod
    async def _store_jobs(
        db: AsyncSession, 
        source_id: str, 
        jobs_data: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Store jobs in database with deduplication.
        
        Returns:
            Dictionary with counts of new and updated jobs
        """
        new_count = 0
        updated_count = 0
        
        for job_data in jobs_data:
            url_hash = job_data.get('url_hash')
            if not url_hash:
                continue
            
            # Check if job already exists
            result = await db.execute(
                select(JobPosting).where(JobPosting.url_hash == url_hash)
            )
            existing_job = result.scalar_one_or_none()
            
            if existing_job:
                # Update existing job
                existing_job.title = job_data.get('title', existing_job.title)
                existing_job.company = job_data.get('company', existing_job.company)
                existing_job.location = job_data.get('location', existing_job.location)
                existing_job.description = job_data.get('description', existing_job.description)
                existing_job.work_type = job_data.get('work_type', existing_job.work_type)
                existing_job.is_active = True
                existing_job.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                # Create new job
                new_job = JobPosting(
                    source_id=source_id,
                    title=job_data.get('title', ''),
                    company=job_data.get('company', 'Unknown'),
                    location=job_data.get('location'),
                    description=job_data.get('description'),
                    requirements=job_data.get('requirements'),
                    salary_min=job_data.get('salary_min'),
                    salary_max=job_data.get('salary_max'),
                    salary_currency=job_data.get('salary_currency'),
                    work_type=job_data.get('work_type'),
                    application_url=job_data.get('application_url', ''),
                    url_hash=url_hash,
                    posted_date=job_data.get('posted_date'),
                    raw_data=json.dumps(job_data),
                )
                db.add(new_job)
                new_count += 1
        
        await db.flush()
        
        return {'new': new_count, 'updated': updated_count}
    
    @staticmethod
    async def get_jobs(
        db: AsyncSession, 
        filters: JobFilters
    ) -> Tuple[List[JobPosting], int]:
        """
        Get jobs with filtering and pagination.
        
        Returns:
            Tuple of (jobs list, total count)
        """
        # Build query
        query = select(JobPosting)
        count_query = select(func.count(JobPosting.id))
        
        # Apply filters
        conditions = []
        
        if filters.title:
            conditions.append(JobPosting.title.ilike(f"%{filters.title}%"))
        
        if filters.company:
            conditions.append(JobPosting.company.ilike(f"%{filters.company}%"))
        
        if filters.location:
            conditions.append(JobPosting.location.ilike(f"%{filters.location}%"))
        
        if filters.work_type:
            conditions.append(JobPosting.work_type == filters.work_type)
        
        if filters.min_salary:
            conditions.append(JobPosting.salary_min >= filters.min_salary)
        
        if filters.source_id:
            conditions.append(JobPosting.source_id == filters.source_id)
        
        if filters.is_active is not None:
            conditions.append(JobPosting.is_active == filters.is_active)
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        query = query.order_by(JobPosting.created_at.desc())
        query = query.offset(offset).limit(filters.page_size)
        
        # Execute query
        result = await db.execute(query)
        jobs = list(result.scalars().all())
        
        return jobs, total
