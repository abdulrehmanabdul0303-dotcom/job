"""
Match service for database operations and match retrieval.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.match import JobMatch
from app.models.resume import Resume
from app.models.job import JobPosting
from app.models.preferences import UserPreferences
from app.models.user import User
from app.services.matcher import MatchingService
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

# Minimum matches threshold for suggestions
MIN_MATCHES_THRESHOLD = 5


class MatchDatabaseService:
    """Service for managing job matches in database."""
    
    @staticmethod
    async def store_match(
        db: AsyncSession,
        user_id: str,
        job_id: str,
        resume_id: str,
        match_score: float,
        score_breakdown: Dict[str, float],
        why: Dict[str, Any],
        missing_skills: List[str],
    ) -> JobMatch:
        """Store a job match in database."""
        match = JobMatch(
            user_id=user_id,
            job_id=job_id,
            resume_id=resume_id,
            match_score=match_score,
            score_breakdown=json.dumps(score_breakdown),
            why_json=json.dumps(why),
            missing_skills_json=json.dumps(missing_skills),
        )
        db.add(match)
        await db.flush()
        await db.refresh(match)
        return match
    
    @staticmethod
    async def get_matches_for_user(
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        min_score: float = 0,
    ) -> Tuple[List[JobMatch], int]:
        """
        Get matches for a user with pagination.
        
        Returns:
            Tuple of (matches list, total count)
        """
        # Build query
        query = select(JobMatch).where(
            and_(
                JobMatch.user_id == user_id,
                JobMatch.match_score >= min_score,
            )
        )
        
        # Get total count
        count_query = select(func.count(JobMatch.id)).where(
            and_(
                JobMatch.user_id == user_id,
                JobMatch.match_score >= min_score,
            )
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and sorting
        offset = (page - 1) * page_size
        query = query.order_by(JobMatch.match_score.desc(), JobMatch.created_at.desc())
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        matches = list(result.scalars().all())
        
        return matches, total
    
    @staticmethod
    async def get_match(db: AsyncSession, match_id: str) -> Optional[JobMatch]:
        """Get a specific match by ID."""
        result = await db.execute(
            select(JobMatch).where(JobMatch.id == match_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def delete_matches_for_job(db: AsyncSession, job_id: str) -> int:
        """Delete all matches for a job (when job is deleted)."""
        result = await db.execute(
            select(JobMatch).where(JobMatch.job_id == job_id)
        )
        matches = result.scalars().all()
        count = len(matches)
        
        for match in matches:
            await db.delete(match)
        
        await db.flush()
        return count
    
    @staticmethod
    async def delete_matches_for_resume(db: AsyncSession, resume_id: str) -> int:
        """Delete all matches for a resume (when resume is deleted)."""
        result = await db.execute(
            select(JobMatch).where(JobMatch.resume_id == resume_id)
        )
        matches = result.scalars().all()
        count = len(matches)
        
        for match in matches:
            await db.delete(match)
        
        await db.flush()
        return count
    
    @staticmethod
    async def clear_matches_for_user(db: AsyncSession, user_id: str) -> int:
        """Clear all matches for a user (for recomputation)."""
        result = await db.execute(
            select(JobMatch).where(JobMatch.user_id == user_id)
        )
        matches = result.scalars().all()
        count = len(matches)
        
        for match in matches:
            await db.delete(match)
        
        await db.flush()
        return count


class MatchComputationService:
    """Service for computing matches between resumes and jobs."""
    
    @staticmethod
    async def compute_matches_for_user(
        db: AsyncSession,
        user_id: str,
        resume_id: Optional[str] = None,
        min_score: float = 0,
    ) -> Dict[str, Any]:
        """
        Compute matches for a user against all active jobs.
        
        Args:
            db: Database session
            user_id: User ID
            resume_id: Specific resume to match (if None, use all user's resumes)
            min_score: Minimum score to store (0-100)
            
        Returns:
            Dictionary with computation statistics
        """
        # Get user's resumes
        if resume_id:
            result = await db.execute(
                select(Resume).where(
                    and_(
                        Resume.id == resume_id,
                        Resume.user_id == user_id,
                    )
                )
            )
            resumes = [result.scalar_one_or_none()]
            if not resumes[0]:
                raise ValueError(f"Resume not found: {resume_id}")
        else:
            result = await db.execute(
                select(Resume).where(Resume.user_id == user_id)
            )
            resumes = list(result.scalars().all())
        
        if not resumes:
            raise ValueError(f"No resumes found for user: {user_id}")
        
        # Get user preferences
        pref_result = await db.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        preferences = pref_result.scalar_one_or_none()
        
        # Get all active jobs
        job_result = await db.execute(
            select(JobPosting).where(JobPosting.is_active == True)
        )
        jobs = list(job_result.scalars().all())
        
        if not jobs:
            return {
                'matches_computed': 0,
                'matches_stored': 0,
                'min_score': min_score,
                'message': 'No active jobs found',
            }
        
        # Clear existing matches for this user
        await MatchDatabaseService.clear_matches_for_user(db, user_id)
        
        # Compute matches
        matches_computed = 0
        matches_stored = 0
        
        for resume in resumes:
            # Extract resume text and skills
            resume_text = f"{resume.raw_text or ''} {resume.parsed_data or ''}"
            resume_tech_skills, resume_soft_skills = MatchingService.extract_skills_from_text(resume_text)
            resume_skills = resume_tech_skills + resume_soft_skills
            
            for job in jobs:
                # Extract job text and skills
                job_text = f"{job.title} {job.description or ''} {job.requirements or ''}"
                job_tech_skills, job_soft_skills = MatchingService.extract_skills_from_text(job_text)
                job_skills = job_tech_skills + job_soft_skills
                
                # Get user preferences
                user_location = preferences.preferred_countries if preferences else None
                user_remote_pref = preferences.work_type if preferences else None
                
                # Compute match
                match_result = MatchingService.compute_match_score(
                    resume_text=resume_text,
                    job_description=job_text,
                    resume_skills=resume_skills,
                    job_skills=job_skills,
                    user_location=user_location,
                    user_remote_preference=user_remote_pref,
                    job_location=job.location,
                    job_work_type=job.work_type,
                )
                
                matches_computed += 1
                
                # Store if above threshold
                if match_result['match_score'] >= min_score:
                    await MatchDatabaseService.store_match(
                        db=db,
                        user_id=user_id,
                        job_id=job.id,
                        resume_id=resume.id,
                        match_score=match_result['match_score'],
                        score_breakdown=match_result['score_breakdown'],
                        why=match_result['why'],
                        missing_skills=match_result['missing_skills'],
                    )
                    matches_stored += 1
        
        await db.commit()
        
        return {
            'matches_computed': matches_computed,
            'matches_stored': matches_stored,
            'min_score': min_score,
            'message': f'Computed {matches_computed} matches, stored {matches_stored} above threshold',
        }


    @staticmethod
    async def generate_suggestions(
        db: AsyncSession,
        user_id: str,
        match_count: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate suggestions when user has no or few matches.
        
        Args:
            db: Database session
            user_id: User ID
            match_count: Current number of matches
            
        Returns:
            List of suggestion dictionaries
        """
        suggestions = []
        
        # Check if user has a resume
        resume_result = await db.execute(
            select(Resume).where(Resume.user_id == user_id)
        )
        resumes = list(resume_result.scalars().all())
        
        if not resumes:
            suggestions.append({
                'type': 'resume',
                'title': 'Upload your resume',
                'description': 'Upload your CV/resume to enable job matching. We support PDF and DOCX formats.',
                'action_url': '/api/v1/resume/upload',
            })
        else:
            # Check if resume has parsed content
            has_parsed = any(r.raw_text for r in resumes)
            if not has_parsed:
                suggestions.append({
                    'type': 'resume',
                    'title': 'Resume parsing incomplete',
                    'description': 'Your resume is still being processed. Please wait a moment and try again.',
                    'action_url': None,
                })
        
        # Check if user has preferences set
        pref_result = await db.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        preferences = pref_result.scalar_one_or_none()
        
        if not preferences:
            suggestions.append({
                'type': 'preferences',
                'title': 'Set your job preferences',
                'description': 'Configure your preferred job roles, locations, salary range, and work type to improve match quality.',
                'action_url': '/api/v1/preferences/me',
            })
        else:
            # Check if preferences are too restrictive
            if preferences.work_type == 'onsite' and preferences.preferred_countries:
                suggestions.append({
                    'type': 'preferences',
                    'title': 'Consider remote work',
                    'description': 'Enabling remote or hybrid work options can significantly increase your job matches.',
                    'action_url': '/api/v1/preferences/me',
                })
            
            if preferences.min_salary and preferences.min_salary > 150000:
                suggestions.append({
                    'type': 'preferences',
                    'title': 'Adjust salary expectations',
                    'description': 'Your minimum salary requirement may be limiting matches. Consider adjusting for more opportunities.',
                    'action_url': '/api/v1/preferences/me',
                })
        
        # Check job availability
        job_result = await db.execute(
            select(func.count(JobPosting.id)).where(JobPosting.is_active == True)
        )
        job_count = job_result.scalar()
        
        if job_count == 0:
            suggestions.append({
                'type': 'jobs',
                'title': 'No active jobs available',
                'description': 'There are currently no active job listings. New jobs are fetched hourly from configured sources.',
                'action_url': None,
            })
        elif job_count < 10:
            suggestions.append({
                'type': 'jobs',
                'title': 'Limited job listings',
                'description': f'Only {job_count} jobs are currently available. More jobs will be added as sources are fetched.',
                'action_url': None,
            })
        
        # If user has everything set up but still few matches
        if resumes and preferences and match_count < MIN_MATCHES_THRESHOLD and job_count >= 10:
            suggestions.append({
                'type': 'profile',
                'title': 'Enhance your profile',
                'description': 'Add more skills and experience details to your resume to improve match scores.',
                'action_url': '/api/v1/resume/upload',
            })
            suggestions.append({
                'type': 'preferences',
                'title': 'Broaden your search criteria',
                'description': 'Try expanding your preferred roles or locations to discover more opportunities.',
                'action_url': '/api/v1/preferences/me',
            })
        
        return suggestions
    
    @staticmethod
    async def compute_matches_for_all_users(
        db: AsyncSession,
        min_score: float = 30,
    ) -> Dict[str, Any]:
        """
        Batch compute matches for all active users.
        Used by daily scheduler.
        
        Args:
            db: Database session
            min_score: Minimum score threshold
            
        Returns:
            Statistics about batch computation
        """
        # Get all active users with resumes
        user_result = await db.execute(
            select(User).where(User.is_active == True)
        )
        users = list(user_result.scalars().all())
        
        total_users = len(users)
        users_processed = 0
        users_with_matches = 0
        total_matches = 0
        errors = []
        
        logger.info(f"Starting batch match computation for {total_users} users")
        
        for user in users:
            try:
                stats = await MatchComputationService.compute_matches_for_user(
                    db=db,
                    user_id=user.id,
                    min_score=min_score,
                )
                users_processed += 1
                
                if stats['matches_stored'] > 0:
                    users_with_matches += 1
                    total_matches += stats['matches_stored']
                    
            except ValueError as e:
                # User has no resume - skip silently
                logger.debug(f"Skipping user {user.id}: {e}")
                users_processed += 1
            except Exception as e:
                logger.error(f"Error computing matches for user {user.id}: {e}")
                errors.append({'user_id': user.id, 'error': str(e)})
        
        logger.info(
            f"Batch match computation complete: {users_processed}/{total_users} users, "
            f"{users_with_matches} with matches, {total_matches} total matches"
        )
        
        return {
            'total_users': total_users,
            'users_processed': users_processed,
            'users_with_matches': users_with_matches,
            'total_matches': total_matches,
            'errors': errors,
            'message': f'Processed {users_processed} users, {total_matches} matches created',
        }
