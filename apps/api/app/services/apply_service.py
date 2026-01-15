"""
Apply kit and activity database service.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.apply import ApplyKit, JobActivity, ActivityStatus
from app.models.resume import Resume
from app.models.job import JobPosting
from app.services.apply_kit import ApplyKitGenerator
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class ApplyKitService:
    """Service for managing apply kits."""
    
    @staticmethod
    async def generate_apply_kit(
        db: AsyncSession,
        user_id: str,
        job_id: str,
        resume_id: Optional[str] = None,
        regenerate: bool = False,  # Task 2.2: Support regeneration
    ) -> Dict[str, Any]:
        """
        Generate an apply kit for a job.
        
        Task 2.2: Added version management and regeneration support.
        
        Args:
            db: Database session
            user_id: User ID
            job_id: Job ID
            resume_id: Specific resume to use (if None, use first resume)
            regenerate: If True, create new version even if one exists
            
        Returns:
            Dictionary with generated content
        """
        # Get job
        job_result = await db.execute(
            select(JobPosting).where(JobPosting.id == job_id)
        )
        job = job_result.scalar_one_or_none()
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Get resume
        if resume_id:
            resume_result = await db.execute(
                select(Resume).where(
                    and_(
                        Resume.id == resume_id,
                        Resume.user_id == user_id,
                    )
                )
            )
            resume = resume_result.scalar_one_or_none()
            if not resume:
                raise ValueError(f"Resume not found: {resume_id}")
        else:
            # Get first resume
            resume_result = await db.execute(
                select(Resume).where(Resume.user_id == user_id).limit(1)
            )
            resume = resume_result.scalar_one_or_none()
            if not resume:
                raise ValueError(f"No resume found for user: {user_id}")
        
        # Get user name (from resume or default)
        user_name = "Applicant"
        if resume.full_text:
            # Try to extract name from resume
            lines = resume.full_text.split('\n')
            if lines:
                user_name = lines[0].strip()
        
        # Generate content
        resume_text = f"{resume.full_text or ''} {resume.parsed_data or ''}"
        job_text = f"{job.title} {job.description or ''} {job.requirements or ''}"
        
        cover_letter = ApplyKitGenerator.generate_cover_letter(
            user_name=user_name,
            job_title=job.title,
            company_name=job.company,
            resume_text=resume_text,
            job_description=job_text,
        )
        
        tailored_bullets = ApplyKitGenerator.generate_tailored_bullets(
            resume_text=resume_text,
            job_description=job_text,
            job_title=job.title,
        )
        
        qa = ApplyKitGenerator.generate_interview_qa(
            resume_text=resume_text,
            job_description=job_text,
            job_title=job.title,
        )
        
        # Task 2.2: Version management
        # Check if apply kit already exists
        existing_result = await db.execute(
            select(ApplyKit).where(
                and_(
                    ApplyKit.user_id == user_id,
                    ApplyKit.job_id == job_id,
                    ApplyKit.is_active == True,
                )
            )
        )
        existing_kit = existing_result.scalar_one_or_none()
        
        if existing_kit and not regenerate:
            # Return existing active version
            return {
                'apply_kit_id': existing_kit.id,
                'job_id': job_id,
                'cover_letter': existing_kit.cover_letter,
                'tailored_bullets': json.loads(existing_kit.tailored_bullets_json) if existing_kit.tailored_bullets_json else [],
                'qa': json.loads(existing_kit.qa_json) if existing_kit.qa_json else {},
                'version': existing_kit.version,
                'is_active': existing_kit.is_active,
            }
        
        if existing_kit and regenerate:
            # Deactivate existing version
            existing_kit.is_active = False
            await db.flush()
            
            # Create new version
            new_version = existing_kit.version + 1
            apply_kit = ApplyKit(
                user_id=user_id,
                job_id=job_id,
                cover_letter=cover_letter,
                tailored_bullets_json=json.dumps(tailored_bullets),
                qa_json=json.dumps(qa),
                version=new_version,
                is_active=True,
                parent_version_id=existing_kit.id,
            )
            db.add(apply_kit)
            await db.flush()
            await db.refresh(apply_kit)
        else:
            # Create first version
            apply_kit = ApplyKit(
                user_id=user_id,
                job_id=job_id,
                cover_letter=cover_letter,
                tailored_bullets_json=json.dumps(tailored_bullets),
                qa_json=json.dumps(qa),
                version=1,
                is_active=True,
                parent_version_id=None,
            )
            db.add(apply_kit)
            await db.flush()
            await db.refresh(apply_kit)
        
        return {
            'apply_kit_id': apply_kit.id,
            'job_id': job_id,
            'cover_letter': cover_letter,
            'tailored_bullets': tailored_bullets,
            'qa': qa,
            'version': apply_kit.version,
            'is_active': apply_kit.is_active,
        }
    
    @staticmethod
    async def get_apply_kit(
        db: AsyncSession,
        user_id: str,
        job_id: str,
    ) -> Optional[ApplyKit]:
        """Get apply kit for a job."""
        result = await db.execute(
            select(ApplyKit).where(
                and_(
                    ApplyKit.user_id == user_id,
                    ApplyKit.job_id == job_id,
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_apply_kit(
        db: AsyncSession,
        user_id: str,
        job_id: str,
        cover_letter: Optional[str] = None,
        tailored_bullets: Optional[List[str]] = None,
        qa: Optional[Dict[str, str]] = None,
    ) -> Optional[ApplyKit]:
        """Update apply kit."""
        apply_kit = await ApplyKitService.get_apply_kit(db, user_id, job_id)
        
        if not apply_kit:
            return None
        
        if cover_letter is not None:
            apply_kit.cover_letter = cover_letter
        
        if tailored_bullets is not None:
            apply_kit.tailored_bullets_json = json.dumps(tailored_bullets)
        
        if qa is not None:
            apply_kit.qa_json = json.dumps(qa)
        
        apply_kit.updated_at = datetime.utcnow()
        await db.flush()
        await db.refresh(apply_kit)
        
        return apply_kit
    
    @staticmethod
    async def delete_apply_kit(
        db: AsyncSession,
        user_id: str,
        job_id: str,
    ) -> bool:
        """Delete apply kit."""
        apply_kit = await ApplyKitService.get_apply_kit(db, user_id, job_id)
        
        if not apply_kit:
            return False
        
        await db.delete(apply_kit)
        await db.flush()
        
        return True
    
    @staticmethod
    async def get_version_history(
        db: AsyncSession,
        user_id: str,
        job_id: str,
    ) -> List[ApplyKit]:
        """
        Get all versions of apply kit for a job.
        
        Task 2.2: Version history retrieval.
        
        Args:
            db: Database session
            user_id: User ID
            job_id: Job ID
            
        Returns:
            List of all versions, ordered by version number descending
        """
        result = await db.execute(
            select(ApplyKit).where(
                and_(
                    ApplyKit.user_id == user_id,
                    ApplyKit.job_id == job_id,
                )
            ).order_by(ApplyKit.version.desc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_specific_version(
        db: AsyncSession,
        user_id: str,
        job_id: str,
        version_number: int,
    ) -> Optional[ApplyKit]:
        """
        Get a specific version of apply kit.
        
        Task 2.2: Specific version retrieval.
        
        Args:
            db: Database session
            user_id: User ID
            job_id: Job ID
            version_number: Version number to retrieve
            
        Returns:
            ApplyKit for the specified version, or None if not found
        """
        result = await db.execute(
            select(ApplyKit).where(
                and_(
                    ApplyKit.user_id == user_id,
                    ApplyKit.job_id == job_id,
                    ApplyKit.version == version_number,
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def activate_version(
        db: AsyncSession,
        user_id: str,
        job_id: str,
        version_number: int,
    ) -> Optional[ApplyKit]:
        """
        Activate a specific version (deactivate others).
        
        Task 2.2: Version activation.
        
        Args:
            db: Database session
            user_id: User ID
            job_id: Job ID
            version_number: Version number to activate
            
        Returns:
            Activated ApplyKit, or None if version not found
        """
        # Get the version to activate
        target_version = await ApplyKitService.get_specific_version(
            db, user_id, job_id, version_number
        )
        
        if not target_version:
            return None
        
        # Deactivate all versions for this job
        all_versions = await ApplyKitService.get_version_history(db, user_id, job_id)
        for version in all_versions:
            version.is_active = False
        
        # Activate target version
        target_version.is_active = True
        target_version.updated_at = datetime.utcnow()
        
        await db.flush()
        await db.refresh(target_version)
        
        return target_version


class ActivityService:
    """Service for managing job activities."""
    
    @staticmethod
    async def set_activity_status(
        db: AsyncSession,
        user_id: str,
        job_id: str,
        status: ActivityStatus,
        notes: Optional[str] = None,
    ) -> JobActivity:
        """Set or update job activity status."""
        # Check if activity exists
        result = await db.execute(
            select(JobActivity).where(
                and_(
                    JobActivity.user_id == user_id,
                    JobActivity.job_id == job_id,
                )
            )
        )
        activity = result.scalar_one_or_none()
        
        if activity:
            # Update existing
            activity.status = status
            if notes is not None:
                activity.notes = notes
            activity.updated_at = datetime.utcnow()
            await db.flush()
            await db.refresh(activity)
        else:
            # Create new
            activity = JobActivity(
                user_id=user_id,
                job_id=job_id,
                status=status,
                notes=notes,
            )
            db.add(activity)
            await db.flush()
            await db.refresh(activity)
        
        return activity
    
    @staticmethod
    async def get_activity(
        db: AsyncSession,
        user_id: str,
        job_id: str,
    ) -> Optional[JobActivity]:
        """Get activity for a job."""
        result = await db.execute(
            select(JobActivity).where(
                and_(
                    JobActivity.user_id == user_id,
                    JobActivity.job_id == job_id,
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_activities(
        db: AsyncSession,
        user_id: str,
        status: Optional[ActivityStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[JobActivity], int]:
        """Get user's activities with pagination."""
        # Build query
        query = select(JobActivity).where(JobActivity.user_id == user_id)
        count_query = select(func.count(JobActivity.id)).where(JobActivity.user_id == user_id)
        
        if status:
            query = query.where(JobActivity.status == status)
            count_query = count_query.where(JobActivity.status == status)
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(JobActivity.updated_at.desc())
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        activities = list(result.scalars().all())
        
        return activities, total
    
    @staticmethod
    async def get_activity_summary(
        db: AsyncSession,
        user_id: str,
    ) -> Dict[str, int]:
        """Get summary of activities by status."""
        result = await db.execute(
            select(JobActivity.status, func.count(JobActivity.id)).where(
                JobActivity.user_id == user_id
            ).group_by(JobActivity.status)
        )
        
        summary = {}
        for status, count in result.all():
            summary[status.value] = count
        
        return summary
