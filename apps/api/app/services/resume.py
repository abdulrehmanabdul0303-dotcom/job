"""
Resume service - handles resume upload, parsing, and scoring operations.
"""
import os
import json
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import UploadFile, HTTPException

from app.models.resume import Resume, ResumeScorecard, ResumeShareLink
from app.services.resume_parser import ResumeParser
from app.services.ats_scoring import ATSScorer
from app.core.config import settings


class ResumeService:
    """Service for resume operations."""
    
    @staticmethod
    async def save_uploaded_file(file: UploadFile, user_id: str) -> tuple[str, int]:
        """
        Save uploaded file to disk.
        
        Returns:
            Tuple of (file_path, file_size)
        """
        # Create upload directory if not exists
        upload_dir = Path(settings.UPLOAD_DIR) / str(user_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        unique_filename = f"{secrets.token_hex(16)}{file_ext}"
        file_path = upload_dir / unique_filename
        
        # Save file
        content = await file.read()
        file_size = len(content)
        
        # Validate size
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
            )
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return str(file_path), file_size
    
    @staticmethod
    async def create_resume(
        db: AsyncSession,
        user_id: str,
        filename: str,
        file_path: str,
        file_size: int,
        mime_type: str
    ) -> Resume:
        """Create resume record in database."""
        resume = Resume(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            is_parsed=False
        )
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        return resume
    
    @staticmethod
    async def create_parsed_resume(
        db: AsyncSession,
        user_id: str,
        filename: str,
        parsed_content: str,
        skills: List[str],
        experience_years: int
    ) -> Resume:
        """Create resume record with pre-parsed data (for testing/API integration)."""
        # Create parsed data structure
        parsed_data = {
            "contact": {
                "name": "Test User",
                "email": "test@example.com",
                "phone": "+1-555-0123"
            },
            "skills": skills,
            "experience": [
                {
                    "company": "Test Company",
                    "position": "Software Engineer",
                    "duration": f"{experience_years} years",
                    "description": "Developed software solutions using various technologies.",
                    "achievements": ["Delivered high-quality code", "Collaborated with teams"]
                }
            ],
            "education": [],
            "sections": ["contact", "skills", "experience"]
        }
        
        resume = Resume(
            user_id=user_id,
            filename=filename,
            file_path="",  # No physical file for parsed data
            file_size=len(parsed_content.encode('utf-8')),
            mime_type="application/json",
            raw_text=parsed_content,
            parsed_data=json.dumps(parsed_data),
            is_parsed=True,
            parsed_at=datetime.utcnow()
        )
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        return resume
    
    @staticmethod
    async def parse_resume(db: AsyncSession, resume: Resume) -> Resume:
        """Parse resume and update database."""
        try:
            # Parse resume
            parsed = ResumeParser.parse(resume.file_path, resume.mime_type)
            
            # Update resume record
            resume.raw_text = parsed['raw_text']
            # Convert dict to JSON string for SQLite
            resume.parsed_data = json.dumps(parsed['parsed_data']) if isinstance(parsed['parsed_data'], dict) else parsed['parsed_data']
            resume.is_parsed = True
            resume.parsed_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(resume)
            
            return resume
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")
    
    @staticmethod
    async def calculate_ats_score(db: AsyncSession, resume: Resume) -> ResumeScorecard:
        """Calculate ATS score for resume."""
        if not resume.is_parsed or not resume.parsed_data:
            raise HTTPException(status_code=400, detail="Resume must be parsed first")
        
        # Parse JSON string to dict if needed
        parsed_data = resume.parsed_data
        if isinstance(parsed_data, str):
            try:
                parsed_data = json.loads(parsed_data)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid parsed data format")
        
        # Ensure parsed_data is a dict
        if not isinstance(parsed_data, dict):
            raise HTTPException(status_code=400, detail="Parsed data must be a dictionary")
        
        # Calculate score
        try:
            score_data = ATSScorer.calculate_score(parsed_data, resume.raw_text or "")
        except Exception as e:
            # Log the error and create a default scorecard
            import logging
            logging.error(f"ATS scoring failed for resume {resume.id}: {e}")
            score_data = {
                'ats_score': 50,
                'contact_score': 10,
                'sections_score': 10,
                'keywords_score': 10,
                'formatting_score': 10,
                'impact_score': 10,
                'missing_keywords': [],
                'formatting_issues': ["Unable to analyze formatting"],
                'suggestions': ["Please review resume format"],
                'strengths': ["Resume uploaded successfully"]
            }
        
        # Check if scorecard exists
        result = await db.execute(
            select(ResumeScorecard).where(ResumeScorecard.resume_id == resume.id)
        )
        scorecard = result.scalar_one_or_none()
        
        if scorecard:
            # Update existing scorecard
            scorecard.ats_score = score_data['ats_score']
            scorecard.contact_score = score_data['contact_score']
            scorecard.sections_score = score_data['sections_score']
            scorecard.keywords_score = score_data['keywords_score']
            scorecard.formatting_score = score_data['formatting_score']
            scorecard.impact_score = score_data['impact_score']
            scorecard.missing_keywords = json.dumps(score_data['missing_keywords'])
            scorecard.formatting_issues = json.dumps(score_data['formatting_issues'])
            scorecard.suggestions = json.dumps(score_data['suggestions'])
            scorecard.strengths = json.dumps(score_data['strengths'])
            scorecard.calculated_at = datetime.utcnow()
        else:
            # Create new scorecard
            scorecard = ResumeScorecard(
                resume_id=resume.id,
                user_id=resume.user_id,
                ats_score=score_data['ats_score'],
                contact_score=score_data['contact_score'],
                sections_score=score_data['sections_score'],
                keywords_score=score_data['keywords_score'],
                formatting_score=score_data['formatting_score'],
                impact_score=score_data['impact_score'],
                missing_keywords=json.dumps(score_data['missing_keywords']),
                formatting_issues=json.dumps(score_data['formatting_issues']),
                suggestions=json.dumps(score_data['suggestions']),
                strengths=json.dumps(score_data['strengths'])
            )
            db.add(scorecard)
        
        await db.commit()
        await db.refresh(scorecard)
        return scorecard
    
    @staticmethod
    async def get_user_resumes(db: AsyncSession, user_id: str) -> List[Resume]:
        """Get all resumes for a user."""
        result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.uploaded_at.desc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_resume_by_id(db: AsyncSession, resume_id: str, user_id: str) -> Optional[Resume]:
        """Get resume by ID for specific user."""
        result = await db.execute(
            select(Resume).where(
                Resume.id == resume_id,
                Resume.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_scorecard(db: AsyncSession, resume_id: str, user_id: str) -> Optional[ResumeScorecard]:
        """Get scorecard for resume."""
        result = await db.execute(
            select(ResumeScorecard).where(
                ResumeScorecard.resume_id == resume_id,
                ResumeScorecard.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_share_link(
        db: AsyncSession,
        resume_id: str,
        user_id: str,
        expires_days: Optional[int] = 30
    ) -> ResumeShareLink:
        """Create shareable link for resume scorecard."""
        # Check if link already exists
        result = await db.execute(
            select(ResumeShareLink).where(
                ResumeShareLink.resume_id == resume_id,
                ResumeShareLink.user_id == user_id,
                ResumeShareLink.is_active == True
            )
        )
        existing_link = result.scalar_one_or_none()
        
        if existing_link:
            return existing_link
        
        # Generate unique token
        share_token = secrets.token_urlsafe(32)
        
        # Calculate expiry
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        share_link = ResumeShareLink(
            resume_id=resume_id,
            user_id=user_id,
            share_token=share_token,
            is_active=True,
            expires_at=expires_at
        )
        
        db.add(share_link)
        await db.commit()
        await db.refresh(share_link)
        return share_link
    
    @staticmethod
    async def get_public_scorecard(db: AsyncSession, share_token: str) -> Optional[dict]:
        """Get public scorecard by share token (privacy-safe)."""
        # Get share link
        result = await db.execute(
            select(ResumeShareLink).where(
                ResumeShareLink.share_token == share_token,
                ResumeShareLink.is_active == True
            )
        )
        share_link = result.scalar_one_or_none()
        
        if not share_link:
            return None
        
        # Check expiry
        if share_link.expires_at and share_link.expires_at < datetime.utcnow():
            return None
        
        # Get scorecard
        result = await db.execute(
            select(ResumeScorecard).where(
                ResumeScorecard.resume_id == share_link.resume_id
            )
        )
        scorecard = result.scalar_one_or_none()
        
        if not scorecard:
            return None
        
        # Update view count and last viewed
        share_link.view_count += 1
        share_link.last_viewed_at = datetime.utcnow()
        await db.commit()
        
        # Return privacy-safe data (NO personal info)
        # Parse JSON strings back to lists
        missing_keywords = scorecard.missing_keywords
        if isinstance(missing_keywords, str):
            missing_keywords = json.loads(missing_keywords)
        
        formatting_issues = scorecard.formatting_issues
        if isinstance(formatting_issues, str):
            formatting_issues = json.loads(formatting_issues)
        
        suggestions = scorecard.suggestions
        if isinstance(suggestions, str):
            suggestions = json.loads(suggestions)
        
        strengths = scorecard.strengths
        if isinstance(strengths, str):
            strengths = json.loads(strengths)
        
        return {
            'ats_score': scorecard.ats_score,
            'contact_score': scorecard.contact_score,
            'sections_score': scorecard.sections_score,
            'keywords_score': scorecard.keywords_score,
            'formatting_score': scorecard.formatting_score,
            'impact_score': scorecard.impact_score,
            'missing_keywords': missing_keywords or [],
            'formatting_issues': formatting_issues or [],
            'suggestions': suggestions or [],
            'strengths': strengths or [],
            'calculated_at': scorecard.calculated_at
        }
    
    @staticmethod
    async def delete_resume(db: AsyncSession, resume_id: str, user_id: str) -> bool:
        """Delete resume and associated data."""
        resume = await ResumeService.get_resume_by_id(db, resume_id, user_id)
        if not resume:
            return False
        
        # Delete file from disk
        try:
            if os.path.exists(resume.file_path):
                os.remove(resume.file_path)
        except Exception:
            pass  # Continue even if file deletion fails
        
        # Manually delete related records (no FK cascade in SQLite)
        # Delete scorecard
        result = await db.execute(
            select(ResumeScorecard).where(ResumeScorecard.resume_id == resume_id)
        )
        scorecard = result.scalar_one_or_none()
        if scorecard:
            await db.delete(scorecard)
        
        # Delete share links
        result = await db.execute(
            select(ResumeShareLink).where(ResumeShareLink.resume_id == resume_id)
        )
        share_links = result.scalars().all()
        for link in share_links:
            await db.delete(link)
        
        # Delete resume
        await db.delete(resume)
        await db.commit()
        return True
