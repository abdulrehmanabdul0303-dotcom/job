"""
AI Resume Versioning Service.
Handles job-specific resume optimization and version generation.
"""
import json
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.resume import Resume
from app.models.job import JobPosting
from app.models.ai_resume import AIResumeVersion, ResumeOptimizationLog
import uuid


class ResumeVersioningEngine:
    """Core engine for AI-powered resume versioning."""
    
    def __init__(self):
        self.optimization_strategies = {
            "keywords": self._optimize_keywords,
            "ats_score": self._optimize_ats_score,
            "relevance": self._optimize_relevance,
            "formatting": self._optimize_formatting
        }
    
    async def generate_version(
        self,
        db: AsyncSession,
        user_id: str,
        job_id: str,
        base_resume_id: str,
        optimization_focus: List[str] = None,
        regenerate: bool = False
    ) -> Dict[str, Any]:
        """Generate a job-specific resume version."""
        start_time = time.time()
        
        try:
            # Check if version already exists
            if not regenerate:
                existing_version = await self._get_existing_version(db, user_id, job_id)
                if existing_version:
                    return await self._format_version_response(existing_version)
            
            # Get base resume and job posting
            base_resume = await self._get_resume(db, base_resume_id, user_id)
            job_posting = await self._get_job_posting(db, job_id)
            
            if not base_resume:
                # PATCH 15: Log failure with null version_id
                processing_time = int((time.time() - start_time) * 1000)
                log_entry = ResumeOptimizationLog(
                    id=str(uuid.uuid4()),
                    version_id=None,
                    user_id=user_id,
                    operation_type="generate",
                    processing_time_ms=processing_time,
                    ai_parameters=json.dumps({"optimization_focus": optimization_focus}),
                    optimization_focus=json.dumps(optimization_focus or []),
                    success=False,
                    error_message="Resume not found"
                )
                db.add(log_entry)
                await db.commit()
                raise ValueError("Resume not found")
            
            if not job_posting:
                # PATCH 15: Log failure with null version_id
                processing_time = int((time.time() - start_time) * 1000)
                log_entry = ResumeOptimizationLog(
                    id=str(uuid.uuid4()),
                    version_id=None,
                    user_id=user_id,
                    operation_type="generate",
                    processing_time_ms=processing_time,
                    ai_parameters=json.dumps({"optimization_focus": optimization_focus}),
                    optimization_focus=json.dumps(optimization_focus or []),
                    success=False,
                    error_message="Job posting not found"
                )
                db.add(log_entry)
                await db.commit()
                raise ValueError("Job posting not found")
            
            # Parse resume content
            resume_content = self._parse_resume_content(base_resume.parsed_data)
            job_requirements = self._parse_job_requirements(job_posting)
            
            # Generate optimized version
            optimized_content = await self._optimize_resume(
                resume_content, 
                job_requirements, 
                optimization_focus or ["keywords", "ats_score", "relevance"]
            )
            
            # Calculate scores
            ats_score = self._calculate_ats_score(optimized_content, job_requirements)
            match_score = self._calculate_match_score(optimized_content, job_requirements)
            keyword_analysis = self._analyze_keywords(optimized_content, job_requirements)
            
            # Generate explanation
            changes_explanation = self._generate_explanation(
                resume_content, optimized_content, job_requirements
            )
            
            # PATCH 15: Atomic version creation with proper transaction management
            version = AIResumeVersion(
                id=str(uuid.uuid4()),
                user_id=user_id,
                job_id=job_id,
                base_resume_id=base_resume_id,
                optimized_content=json.dumps(optimized_content),
                changes_explanation=changes_explanation,
                ats_score=ats_score,
                keyword_density=json.dumps(keyword_analysis),
                match_score=match_score,
                formats=json.dumps({}),  # Will be populated by format converter
                version_number=1
            )
            
            db.add(version)
            await db.commit()
            await db.refresh(version)
            
            # Log the successful operation in separate transaction
            processing_time = int((time.time() - start_time) * 1000)
            log_entry = ResumeOptimizationLog(
                id=str(uuid.uuid4()),
                version_id=version.id,
                user_id=user_id,
                operation_type="generate",
                processing_time_ms=processing_time,
                ai_parameters=json.dumps({"optimization_focus": optimization_focus}),
                optimization_focus=json.dumps(optimization_focus or []),
                success=True,
                error_message=None
            )
            db.add(log_entry)
            await db.commit()
            
            return await self._format_version_response(version)
            
        except ValueError as e:
            # ValueError already logged above, just re-raise as HTTP exception
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            # PATCH 15: Log unexpected failures with null version_id
            processing_time = int((time.time() - start_time) * 1000)
            log_entry = ResumeOptimizationLog(
                id=str(uuid.uuid4()),
                version_id=None,
                user_id=user_id,
                operation_type="generate",
                processing_time_ms=processing_time,
                ai_parameters=json.dumps({"optimization_focus": optimization_focus}),
                optimization_focus=json.dumps(optimization_focus or []),
                success=False,
                error_message=str(e)[:500]  # Truncate long error messages
            )
            db.add(log_entry)
            await db.commit()
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Resume optimization failed")
    
    async def get_version(
        self, 
        db: AsyncSession, 
        user_id: str, 
        job_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get existing resume version for a job."""
        version = await self._get_existing_version(db, user_id, job_id)
        if version:
            return await self._format_version_response(version)
        return None
    
    async def compare_versions(
        self,
        db: AsyncSession,
        user_id: str,
        version_a_id: str,
        version_b_id: str
    ) -> Dict[str, Any]:
        """Compare two resume versions."""
        # Get both versions
        version_a = await self._get_version_by_id(db, version_a_id, user_id)
        version_b = await self._get_version_by_id(db, version_b_id, user_id)
        
        if not version_a or not version_b:
            raise ValueError("One or both versions not found")
        
        # Parse content
        content_a = json.loads(version_a.optimized_content)
        content_b = json.loads(version_b.optimized_content)
        
        # Calculate differences
        differences = self._calculate_differences(content_a, content_b)
        similarity_score = self._calculate_similarity(content_a, content_b)
        
        return {
            "version_a": {
                "id": version_a.id,
                "job_id": version_a.job_id,
                "ats_score": version_a.ats_score,
                "match_score": version_a.match_score,
                "created_at": version_a.created_at.isoformat()
            },
            "version_b": {
                "id": version_b.id,
                "job_id": version_b.job_id,
                "ats_score": version_b.ats_score,
                "match_score": version_b.match_score,
                "created_at": version_b.created_at.isoformat()
            },
            "comparison": {
                "differences": differences,
                "similarity_score": similarity_score,
                "ats_score_diff": version_b.ats_score - version_a.ats_score,
                "match_score_diff": version_b.match_score - version_a.match_score
            }
        }
    
    # Private helper methods
    
    async def _get_existing_version(
        self, db: AsyncSession, user_id: str, job_id: str
    ) -> Optional[AIResumeVersion]:
        """Get existing version for user and job."""
        result = await db.execute(
            select(AIResumeVersion)
            .where(
                AIResumeVersion.user_id == user_id,
                AIResumeVersion.job_id == job_id,
                AIResumeVersion.is_active == True
            )
            .order_by(AIResumeVersion.created_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def _get_resume(
        self, db: AsyncSession, resume_id: str, user_id: str
    ) -> Optional[Resume]:
        """Get resume by ID and user."""
        result = await db.execute(
            select(Resume).where(
                Resume.id == resume_id,
                Resume.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def _get_job_posting(
        self, db: AsyncSession, job_id: str
    ) -> Optional[JobPosting]:
        """Get job posting by ID."""
        result = await db.execute(
            select(JobPosting).where(JobPosting.id == job_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_version_by_id(
        self, db: AsyncSession, version_id: str, user_id: str
    ) -> Optional[AIResumeVersion]:
        """Get version by ID and user."""
        result = await db.execute(
            select(AIResumeVersion).where(
                AIResumeVersion.id == version_id,
                AIResumeVersion.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    def _parse_resume_content(self, parsed_data: str) -> Dict[str, Any]:
        """Parse resume content from stored JSON."""
        if not parsed_data:
            return {}
        try:
            return json.loads(parsed_data)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def _parse_job_requirements(self, job_posting: JobPosting) -> Dict[str, Any]:
        """Parse job requirements and extract key information."""
        requirements = {
            "title": job_posting.title,
            "company": job_posting.company,
            "description": job_posting.description,
            "requirements": job_posting.requirements,
            "skills": [],
            "keywords": []
        }
        
        # Extract skills and keywords from job description and requirements
        text = f"{job_posting.description} {job_posting.requirements}".lower()
        
        # Common technical skills
        tech_skills = [
            "python", "javascript", "react", "node.js", "sql", "aws", "docker", 
            "kubernetes", "machine learning", "ai", "data science", "fastapi",
            "postgresql", "mongodb", "redis", "git", "ci/cd", "devops"
        ]
        
        found_skills = [skill for skill in tech_skills if skill in text]
        requirements["skills"] = found_skills
        
        # Extract keywords (simple approach)
        keywords = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        requirements["keywords"] = list(set(keywords))[:20]  # Top 20 keywords
        
        return requirements
    
    async def _optimize_resume(
        self, 
        resume_content: Dict[str, Any], 
        job_requirements: Dict[str, Any],
        optimization_focus: List[str]
    ) -> Dict[str, Any]:
        """Optimize resume content for the specific job."""
        optimized = resume_content.copy()
        
        for strategy in optimization_focus:
            if strategy in self.optimization_strategies:
                optimized = await self.optimization_strategies[strategy](
                    optimized, job_requirements
                )
        
        return optimized
    
    async def _optimize_keywords(
        self, content: Dict[str, Any], job_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize keyword density and relevance."""
        job_skills = job_requirements.get("skills", [])
        job_keywords = job_requirements.get("keywords", [])
        
        # Enhance summary with relevant keywords
        if "summary" in content:
            summary = content["summary"]
            for skill in job_skills[:3]:  # Add top 3 relevant skills
                if skill.lower() not in summary.lower():
                    summary += f" Experienced with {skill}."
            content["summary"] = summary
        
        # Enhance skills section
        if "skills" in content:
            current_skills = content["skills"]
            for skill in job_skills:
                if skill not in [s.lower() for s in current_skills]:
                    current_skills.append(skill.title())
            content["skills"] = current_skills
        
        return content
    
    async def _optimize_ats_score(
        self, content: Dict[str, Any], job_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize for ATS compatibility."""
        # Ensure proper section headers
        if "experience" in content:
            for exp in content["experience"]:
                if "achievements" not in exp:
                    exp["achievements"] = [
                        "Delivered high-quality solutions",
                        "Collaborated with cross-functional teams",
                        "Improved system performance"
                    ]
        
        # Add relevant certifications section if missing
        if "certifications" not in content:
            content["certifications"] = []
        
        return content
    
    async def _optimize_relevance(
        self, content: Dict[str, Any], job_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize content relevance to the job."""
        job_title = job_requirements.get("title", "").lower()
        
        # Adjust professional title to match job
        if "title" in content:
            if any(word in job_title for word in ["senior", "lead", "principal"]):
                if "senior" not in content["title"].lower():
                    content["title"] = f"Senior {content['title']}"
        
        return content
    
    async def _optimize_formatting(
        self, content: Dict[str, Any], job_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize formatting and structure."""
        # Ensure consistent formatting
        if "experience" in content:
            for exp in content["experience"]:
                if "description" in exp and not exp["description"].endswith("."):
                    exp["description"] += "."
        
        return content
    
    def _calculate_ats_score(
        self, content: Dict[str, Any], job_requirements: Dict[str, Any]
    ) -> float:
        """Calculate ATS compatibility score."""
        score = 0.0
        
        # Check for required sections (40 points)
        required_sections = ["name", "email", "experience", "skills"]
        for section in required_sections:
            if section in content and content[section]:
                score += 10
        
        # Check keyword match (30 points)
        job_skills = [s.lower() for s in job_requirements.get("skills", [])]
        resume_skills = [s.lower() for s in content.get("skills", [])]
        
        if job_skills:
            skill_match_ratio = len(set(job_skills) & set(resume_skills)) / len(job_skills)
            score += skill_match_ratio * 30
        
        # Check formatting (20 points)
        if "experience" in content:
            for exp in content["experience"]:
                if all(key in exp for key in ["company", "position", "duration"]):
                    score += 5
                    break
        
        # Check contact info (10 points)
        if "phone" in content and "email" in content:
            score += 10
        
        return min(score, 100.0)
    
    def _calculate_match_score(
        self, content: Dict[str, Any], job_requirements: Dict[str, Any]
    ) -> float:
        """Calculate job match score."""
        score = 0.0
        
        # Skills match (60 points)
        job_skills = [s.lower() for s in job_requirements.get("skills", [])]
        resume_skills = [s.lower() for s in content.get("skills", [])]
        
        if job_skills:
            skill_match_ratio = len(set(job_skills) & set(resume_skills)) / len(job_skills)
            score += skill_match_ratio * 60
        
        # Experience relevance (25 points)
        job_title = job_requirements.get("title", "").lower()
        resume_title = content.get("title", "").lower()
        
        if any(word in resume_title for word in job_title.split()):
            score += 25
        
        # Education match (15 points)
        if "education" in content and content["education"]:
            score += 15
        
        return min(score, 100.0)
    
    def _analyze_keywords(
        self, content: Dict[str, Any], job_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze keyword density and coverage."""
        job_keywords = job_requirements.get("keywords", [])
        resume_text = json.dumps(content).lower()
        
        keyword_analysis = {
            "total_keywords": len(job_keywords),
            "matched_keywords": [],
            "missing_keywords": [],
            "density_score": 0.0
        }
        
        for keyword in job_keywords:
            if keyword.lower() in resume_text:
                keyword_analysis["matched_keywords"].append(keyword)
            else:
                keyword_analysis["missing_keywords"].append(keyword)
        
        if job_keywords:
            keyword_analysis["density_score"] = (
                len(keyword_analysis["matched_keywords"]) / len(job_keywords) * 100
            )
        
        return keyword_analysis
    
    def _generate_explanation(
        self, 
        original: Dict[str, Any], 
        optimized: Dict[str, Any], 
        job_requirements: Dict[str, Any]
    ) -> str:
        """Generate explanation of changes made."""
        changes = []
        
        # Check for skill additions
        original_skills = set(s.lower() for s in original.get("skills", []))
        optimized_skills = set(s.lower() for s in optimized.get("skills", []))
        new_skills = optimized_skills - original_skills
        
        if new_skills:
            changes.append(f"Added relevant skills: {', '.join(new_skills)}")
        
        # Check for summary changes
        if original.get("summary") != optimized.get("summary"):
            changes.append("Enhanced professional summary with job-relevant keywords")
        
        # Check for experience enhancements
        if "experience" in optimized:
            for i, exp in enumerate(optimized["experience"]):
                if i < len(original.get("experience", [])):
                    if exp.get("achievements") != original["experience"][i].get("achievements"):
                        changes.append("Enhanced experience descriptions with quantifiable achievements")
                        break
        
        if not changes:
            changes.append("Optimized content structure and keyword density for better ATS compatibility")
        
        return ". ".join(changes) + "."
    
    def _calculate_differences(
        self, content_a: Dict[str, Any], content_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate differences between two resume versions."""
        differences = {
            "sections_changed": [],
            "skills_added": [],
            "skills_removed": [],
            "content_changes": []
        }
        
        # Compare skills
        skills_a = set(s.lower() for s in content_a.get("skills", []))
        skills_b = set(s.lower() for s in content_b.get("skills", []))
        
        differences["skills_added"] = list(skills_b - skills_a)
        differences["skills_removed"] = list(skills_a - skills_b)
        
        # Compare sections
        for section in ["summary", "experience", "education"]:
            if content_a.get(section) != content_b.get(section):
                differences["sections_changed"].append(section)
        
        return differences
    
    def _calculate_similarity(
        self, content_a: Dict[str, Any], content_b: Dict[str, Any]
    ) -> float:
        """Calculate similarity score between two resume versions."""
        # Simple similarity based on common fields
        total_fields = 0
        matching_fields = 0
        
        all_keys = set(content_a.keys()) | set(content_b.keys())
        
        for key in all_keys:
            total_fields += 1
            if content_a.get(key) == content_b.get(key):
                matching_fields += 1
        
        return (matching_fields / total_fields * 100) if total_fields > 0 else 0.0
    
    async def _log_operation(
        self,
        db: AsyncSession,
        version_id: Optional[str],
        user_id: str,
        operation_type: str,
        processing_time: int,
        optimization_focus: Optional[List[str]],
        success: bool,
        error_message: Optional[str] = None
    ):
        """Log resume optimization operation."""
        log_entry = ResumeOptimizationLog(
            id=str(uuid.uuid4()),
            version_id=version_id,
            user_id=user_id,
            operation_type=operation_type,
            processing_time_ms=processing_time,
            ai_parameters=json.dumps({"optimization_focus": optimization_focus}),
            optimization_focus=json.dumps(optimization_focus or []),
            success=success,
            error_message=error_message
        )
        
        db.add(log_entry)
        await db.flush()
    
    async def _format_version_response(self, version: AIResumeVersion) -> Dict[str, Any]:
        """Format version for API response."""
        return {
            "id": version.id,
            "job_id": version.job_id,
            "base_resume_id": version.base_resume_id,
            "optimized_content": json.loads(version.optimized_content),
            "changes_explanation": version.changes_explanation,
            "ats_score": version.ats_score,
            "match_score": version.match_score,
            "keyword_density": json.loads(version.keyword_density) if version.keyword_density else {},
            "formats": json.loads(version.formats) if version.formats else {},
            "version_number": version.version_number,
            "created_at": version.created_at.isoformat(),
            "updated_at": version.updated_at.isoformat() if version.updated_at else None
        }