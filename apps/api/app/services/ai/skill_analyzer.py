"""
AI Skill Gap Analysis Service.
Handles skill gap identification, learning recommendations, and progress tracking.
"""
import json
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.resume import Resume
from app.models.job import JobPosting
from app.models.ai_skills import (
    SkillGapAnalysis, SkillGap, LearningResource, 
    SkillProgressTracking, SkillMarketData, LearningPath
)
import uuid


class SkillAnalyzerEngine:
    """Core engine for AI-powered skill gap analysis."""
    
    def __init__(self):
        self.skill_categories = {
            "technical": ["programming", "frameworks", "databases", "cloud", "devops"],
            "soft": ["leadership", "communication", "problem-solving", "teamwork"],
            "certification": ["aws", "azure", "google cloud", "kubernetes", "security"],
            "domain": ["machine learning", "data science", "web development", "mobile"]
        }
        
        self.skill_database = {
            # Programming Languages
            "python": {"category": "technical", "difficulty": "intermediate", "market_demand": 95, "avg_salary_impact": 15000},
            "javascript": {"category": "technical", "difficulty": "intermediate", "market_demand": 92, "avg_salary_impact": 12000},
            "typescript": {"category": "technical", "difficulty": "intermediate", "market_demand": 88, "avg_salary_impact": 14000},
            "java": {"category": "technical", "difficulty": "intermediate", "market_demand": 85, "avg_salary_impact": 13000},
            "go": {"category": "technical", "difficulty": "advanced", "market_demand": 78, "avg_salary_impact": 18000},
            "rust": {"category": "technical", "difficulty": "advanced", "market_demand": 72, "avg_salary_impact": 20000},
            
            # Frameworks & Libraries
            "react": {"category": "technical", "difficulty": "intermediate", "market_demand": 90, "avg_salary_impact": 10000},
            "node.js": {"category": "technical", "difficulty": "intermediate", "market_demand": 87, "avg_salary_impact": 11000},
            "fastapi": {"category": "technical", "difficulty": "intermediate", "market_demand": 75, "avg_salary_impact": 12000},
            "django": {"category": "technical", "difficulty": "intermediate", "market_demand": 80, "avg_salary_impact": 11000},
            "angular": {"category": "technical", "difficulty": "intermediate", "market_demand": 75, "avg_salary_impact": 10000},
            "vue.js": {"category": "technical", "difficulty": "intermediate", "market_demand": 70, "avg_salary_impact": 9000},
            
            # Cloud & DevOps
            "aws": {"category": "technical", "difficulty": "intermediate", "market_demand": 93, "avg_salary_impact": 16000},
            "docker": {"category": "technical", "difficulty": "intermediate", "market_demand": 89, "avg_salary_impact": 12000},
            "kubernetes": {"category": "technical", "difficulty": "advanced", "market_demand": 85, "avg_salary_impact": 18000},
            "terraform": {"category": "technical", "difficulty": "intermediate", "market_demand": 82, "avg_salary_impact": 15000},
            "jenkins": {"category": "technical", "difficulty": "intermediate", "market_demand": 78, "avg_salary_impact": 10000},
            
            # Databases
            "postgresql": {"category": "technical", "difficulty": "intermediate", "market_demand": 85, "avg_salary_impact": 8000},
            "mongodb": {"category": "technical", "difficulty": "intermediate", "market_demand": 80, "avg_salary_impact": 7000},
            "redis": {"category": "technical", "difficulty": "intermediate", "market_demand": 75, "avg_salary_impact": 6000},
            
            # Soft Skills
            "leadership": {"category": "soft", "difficulty": "advanced", "market_demand": 95, "avg_salary_impact": 25000},
            "communication": {"category": "soft", "difficulty": "intermediate", "market_demand": 98, "avg_salary_impact": 15000},
            "problem-solving": {"category": "soft", "difficulty": "intermediate", "market_demand": 97, "avg_salary_impact": 12000},
            "teamwork": {"category": "soft", "difficulty": "beginner", "market_demand": 95, "avg_salary_impact": 8000},
            "project management": {"category": "soft", "difficulty": "intermediate", "market_demand": 90, "avg_salary_impact": 18000},
            
            # Emerging Technologies
            "machine learning": {"category": "domain", "difficulty": "advanced", "market_demand": 88, "avg_salary_impact": 22000},
            "ai": {"category": "domain", "difficulty": "advanced", "market_demand": 92, "avg_salary_impact": 25000},
            "data science": {"category": "domain", "difficulty": "advanced", "market_demand": 85, "avg_salary_impact": 20000},
            "blockchain": {"category": "domain", "difficulty": "advanced", "market_demand": 65, "avg_salary_impact": 15000}
        }
    
    async def analyze_skill_gaps(
        self,
        db: AsyncSession,
        user_id: str,
        job_id: str,
        include_market_data: bool = True,
        regenerate: bool = False
    ) -> Dict[str, Any]:
        """Analyze skill gaps for a specific job."""
        start_time = time.time()
        
        try:
            # Check if analysis already exists
            if not regenerate:
                existing_analysis = await self._get_existing_analysis(db, user_id, job_id)
                if existing_analysis:
                    return await self._format_analysis_response(existing_analysis)
            
            # Get user resume and job posting
            user_resume = await self._get_user_resume(db, user_id)
            job_posting = await self._get_job_posting(db, job_id)
            
            if not user_resume or not job_posting:
                raise ValueError("Resume or job posting not found")
            
            # Parse data
            resume_data = self._parse_resume_content(user_resume.parsed_data)
            job_requirements = self._parse_job_requirements(job_posting)
            
            # Extract skills
            user_skills = self._extract_user_skills(resume_data)
            required_skills = self._extract_required_skills(job_requirements)
            
            # Identify skill gaps
            skill_gaps = await self._identify_skill_gaps(user_skills, required_skills)
            
            # Generate learning recommendations
            learning_recommendations = await self._generate_learning_recommendations(skill_gaps)
            
            # Calculate timeline and priorities
            timeline_data = self._calculate_learning_timeline(skill_gaps)
            priority_scores = self._calculate_priority_scores(skill_gaps, job_requirements)
            
            # Get market data if requested
            market_data = {}
            if include_market_data:
                market_data = await self._get_market_data(db, [gap["skill_name"] for gap in skill_gaps])
            
            # Calculate overall metrics
            total_missing_skills = len(skill_gaps)
            critical_skills_count = len([gap for gap in skill_gaps if gap["importance"] == "critical"])
            estimated_total_hours = sum(gap["estimated_learning_hours"] for gap in skill_gaps)
            overall_readiness_score = self._calculate_readiness_score(user_skills, required_skills, skill_gaps)
            
            # Create analysis record
            analysis = SkillGapAnalysis(
                id=str(uuid.uuid4()),
                user_id=user_id,
                job_id=job_id,
                missing_skills=json.dumps(skill_gaps),
                learning_recommendations=json.dumps(learning_recommendations),
                estimated_timeline=json.dumps(timeline_data),
                priority_score=json.dumps(priority_scores),
                market_demand=json.dumps(market_data),
                total_missing_skills=total_missing_skills,
                critical_skills_count=critical_skills_count,
                estimated_total_hours=estimated_total_hours,
                overall_readiness_score=overall_readiness_score
            )
            
            db.add(analysis)
            await db.flush()
            
            # Create individual skill gap records
            await self._create_skill_gap_records(db, analysis.id, user_id, skill_gaps, market_data)
            
            # Create learning resource records
            await self._create_learning_resource_records(db, user_id, skill_gaps, learning_recommendations)
            
            # Generate learning path
            learning_path = await self._generate_learning_path(
                db, user_id, analysis.id, skill_gaps, job_requirements
            )
            
            await db.commit()
            
            processing_time = time.time() - start_time
            print(f"Skill gap analysis completed in {processing_time:.2f}s")
            
            return await self._format_analysis_response(analysis)
            
        except Exception as e:
            await db.rollback()
            raise
    
    async def get_skill_analysis(
        self, 
        db: AsyncSession, 
        user_id: str, 
        job_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get existing skill gap analysis for a job."""
        analysis = await self._get_existing_analysis(db, user_id, job_id)
        if analysis:
            return await self._format_analysis_response(analysis)
        return None
    
    async def update_skill_progress(
        self,
        db: AsyncSession,
        user_id: str,
        skill_name: str,
        progress_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user's progress on a specific skill."""
        try:
            # Get or create progress tracking record
            result = await db.execute(
                select(SkillProgressTracking).where(
                    SkillProgressTracking.user_id == user_id,
                    SkillProgressTracking.skill_name == skill_name
                )
            )
            progress_record = result.scalar_one_or_none()
            
            if not progress_record:
                progress_record = SkillProgressTracking(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    skill_name=skill_name,
                    current_level=0.0,
                    progress_percentage=0.0
                )
                db.add(progress_record)
            
            # Update progress data
            progress_record.previous_level = progress_record.current_level
            progress_record.current_level = progress_data.get("current_level", progress_record.current_level)
            progress_record.progress_percentage = progress_data.get("progress_percentage", progress_record.progress_percentage)
            progress_record.hours_invested = progress_data.get("hours_invested", progress_record.hours_invested)
            progress_record.resources_completed = progress_data.get("resources_completed", progress_record.resources_completed)
            
            if progress_data.get("certifications_earned"):
                progress_record.certifications_earned = json.dumps(progress_data["certifications_earned"])
            
            if progress_data.get("self_assessment_score"):
                progress_record.self_assessment_score = progress_data["self_assessment_score"]
            
            if progress_data.get("progress_notes"):
                progress_record.progress_notes = progress_data["progress_notes"]
            
            # Generate AI feedback
            ai_feedback = self._generate_progress_feedback(progress_record, progress_data)
            progress_record.ai_feedback = json.dumps(ai_feedback)
            
            progress_record.last_updated = datetime.utcnow()
            
            await db.commit()
            
            return {
                "skill_name": skill_name,
                "current_level": progress_record.current_level,
                "progress_percentage": progress_record.progress_percentage,
                "hours_invested": progress_record.hours_invested,
                "ai_feedback": ai_feedback,
                "updated_at": progress_record.last_updated.isoformat()
            }
            
        except Exception as e:
            await db.rollback()
            raise
    
    async def get_learning_path(
        self,
        db: AsyncSession,
        user_id: str,
        analysis_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get learning path for a skill gap analysis."""
        result = await db.execute(
            select(LearningPath).where(
                LearningPath.user_id == user_id,
                LearningPath.analysis_id == analysis_id,
                LearningPath.is_active == True
            ).order_by(LearningPath.created_at.desc())
        )
        path = result.scalar_one_or_none()
        
        if path:
            return {
                "id": path.id,
                "path_name": path.path_name,
                "description": path.description,
                "target_role": path.target_role,
                "learning_steps": json.loads(path.learning_steps),
                "milestones": json.loads(path.milestones),
                "skill_progression": json.loads(path.skill_progression),
                "estimated_total_hours": path.estimated_total_hours,
                "estimated_weeks": path.estimated_weeks,
                "difficulty_level": path.difficulty_level,
                "current_step": path.current_step,
                "completion_percentage": path.completion_percentage,
                "priority_order": json.loads(path.priority_order),
                "market_alignment_score": path.market_alignment_score,
                "personalization_score": path.personalization_score,
                "created_at": path.created_at.isoformat()
            }
        
        return None
    
    # Private helper methods
    
    async def _get_existing_analysis(
        self, db: AsyncSession, user_id: str, job_id: str
    ) -> Optional[SkillGapAnalysis]:
        """Get existing skill gap analysis."""
        result = await db.execute(
            select(SkillGapAnalysis).where(
                SkillGapAnalysis.user_id == user_id,
                SkillGapAnalysis.job_id == job_id,
                SkillGapAnalysis.is_active == True
            ).order_by(SkillGapAnalysis.created_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def _get_user_resume(
        self, db: AsyncSession, user_id: str
    ) -> Optional[Resume]:
        """Get user's primary resume."""
        result = await db.execute(
            select(Resume).where(
                Resume.user_id == user_id,
                Resume.is_parsed == True
            ).order_by(Resume.uploaded_at.desc())
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
        return {
            "title": job_posting.title,
            "company": job_posting.company,
            "description": job_posting.description,
            "requirements": job_posting.requirements,
            "seniority": self._extract_seniority(job_posting.title),
            "industry": self._extract_industry(job_posting.company)
        }
    
    def _extract_user_skills(self, resume_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract user's skills from resume data."""
        user_skills = []
        
        # Extract from skills section
        if "skills" in resume_data:
            for skill in resume_data["skills"]:
                skill_info = self._get_skill_info(skill.lower())
                user_skills.append({
                    "name": skill.lower(),
                    "level": 3,  # Default intermediate level
                    "category": skill_info.get("category", "technical"),
                    "years_experience": 2  # Default 2 years
                })
        
        # Extract from experience descriptions
        if "experience" in resume_data:
            for exp in resume_data["experience"]:
                description = exp.get("description", "").lower()
                for skill_name in self.skill_database.keys():
                    if skill_name in description and skill_name not in [s["name"] for s in user_skills]:
                        skill_info = self._get_skill_info(skill_name)
                        user_skills.append({
                            "name": skill_name,
                            "level": 2,  # Lower level from experience mention
                            "category": skill_info.get("category", "technical"),
                            "years_experience": 1
                        })
        
        return user_skills
    
    def _extract_required_skills(self, job_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract required skills from job posting."""
        required_skills = []
        
        # Combine description and requirements text
        text = f"{job_requirements.get('description', '')} {job_requirements.get('requirements', '')}".lower()
        
        # Extract skills from our database
        for skill_name, skill_data in self.skill_database.items():
            if skill_name in text:
                # Determine importance based on context
                importance = "critical" if any(word in text for word in ["required", "must", "essential"]) else "important"
                if any(word in text for word in ["nice", "plus", "preferred"]):
                    importance = "nice-to-have"
                
                # Determine required level based on seniority
                seniority = job_requirements.get("seniority", "mid")
                required_level = {"junior": 2, "mid": 3, "senior": 4}.get(seniority, 3)
                
                required_skills.append({
                    "name": skill_name,
                    "required_level": required_level,
                    "importance": importance,
                    "category": skill_data["category"],
                    "market_demand": skill_data["market_demand"],
                    "salary_impact": skill_data["avg_salary_impact"]
                })
        
        return required_skills
    
    async def _identify_skill_gaps(
        self, 
        user_skills: List[Dict[str, Any]], 
        required_skills: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify skill gaps between user and job requirements."""
        skill_gaps = []
        user_skill_names = [skill["name"] for skill in user_skills]
        
        for required_skill in required_skills:
            skill_name = required_skill["name"]
            
            if skill_name not in user_skill_names:
                # Complete skill gap
                gap_score = 100.0  # Maximum gap
                current_level = 0
            else:
                # Partial skill gap
                user_skill = next(s for s in user_skills if s["name"] == skill_name)
                current_level = user_skill["level"]
                required_level = required_skill["required_level"]
                
                if current_level >= required_level:
                    continue  # No gap
                
                gap_score = ((required_level - current_level) / required_level) * 100
            
            # Calculate learning time
            skill_info = self._get_skill_info(skill_name)
            base_hours = {"beginner": 20, "intermediate": 40, "advanced": 80}.get(
                skill_info.get("difficulty", "intermediate"), 40
            )
            estimated_hours = int(base_hours * (gap_score / 100))
            
            skill_gaps.append({
                "skill_name": skill_name,
                "skill_category": required_skill["category"],
                "importance": required_skill["importance"],
                "current_level": current_level,
                "required_level": required_skill["required_level"],
                "gap_score": gap_score,
                "market_demand_score": required_skill["market_demand"],
                "salary_impact": required_skill["salary_impact"],
                "estimated_learning_hours": estimated_hours,
                "difficulty_level": skill_info.get("difficulty", "intermediate")
            })
        
        return skill_gaps
    
    async def _generate_learning_recommendations(
        self, skill_gaps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate learning resource recommendations for skill gaps."""
        recommendations = []
        
        for gap in skill_gaps:
            skill_name = gap["skill_name"]
            difficulty = gap["difficulty_level"]
            
            # Generate resources based on skill type
            resources = self._get_learning_resources_for_skill(skill_name, difficulty)
            
            for resource in resources:
                recommendations.append({
                    "skill_name": skill_name,
                    "title": resource["title"],
                    "provider": resource["provider"],
                    "resource_type": resource["type"],
                    "url": resource.get("url"),
                    "estimated_hours": resource["hours"],
                    "difficulty": difficulty,
                    "cost": resource.get("cost", 0),
                    "rating": resource.get("rating", 4.0),
                    "relevance_score": resource["relevance"],
                    "priority_rank": resource["priority"]
                })
        
        return recommendations
    
    def _get_learning_resources_for_skill(
        self, skill_name: str, difficulty: str
    ) -> List[Dict[str, Any]]:
        """Get learning resources for a specific skill."""
        # This would typically connect to a learning resource database
        # For demo purposes, we'll generate sample resources
        
        base_resources = {
            "python": [
                {"title": "Python Crash Course", "provider": "No Starch Press", "type": "book", "hours": 40, "relevance": 95, "priority": 1, "rating": 4.8},
                {"title": "Python for Everybody", "provider": "Coursera", "type": "course", "hours": 30, "relevance": 90, "priority": 2, "rating": 4.7},
                {"title": "Real Python Tutorials", "provider": "Real Python", "type": "tutorial", "hours": 20, "relevance": 85, "priority": 3, "rating": 4.6}
            ],
            "javascript": [
                {"title": "JavaScript: The Definitive Guide", "provider": "O'Reilly", "type": "book", "hours": 50, "relevance": 95, "priority": 1, "rating": 4.7},
                {"title": "JavaScript Algorithms and Data Structures", "provider": "freeCodeCamp", "type": "course", "hours": 35, "relevance": 90, "priority": 2, "rating": 4.8},
                {"title": "MDN JavaScript Guide", "provider": "Mozilla", "type": "tutorial", "hours": 25, "relevance": 85, "priority": 3, "rating": 4.5}
            ],
            "react": [
                {"title": "React - The Complete Guide", "provider": "Udemy", "type": "course", "hours": 45, "relevance": 95, "priority": 1, "rating": 4.8},
                {"title": "Official React Tutorial", "provider": "React.dev", "type": "tutorial", "hours": 15, "relevance": 90, "priority": 2, "rating": 4.6},
                {"title": "React Hooks in Action", "provider": "Manning", "type": "book", "hours": 30, "relevance": 85, "priority": 3, "rating": 4.5}
            ],
            "aws": [
                {"title": "AWS Certified Solutions Architect", "provider": "AWS", "type": "certification", "hours": 60, "relevance": 95, "priority": 1, "rating": 4.7},
                {"title": "AWS Cloud Practitioner Essentials", "provider": "AWS", "type": "course", "hours": 25, "relevance": 90, "priority": 2, "rating": 4.6},
                {"title": "AWS Hands-On Labs", "provider": "AWS", "type": "practice", "hours": 40, "relevance": 85, "priority": 3, "rating": 4.5}
            ]
        }
        
        # Return resources for the skill, or generic resources if not found
        return base_resources.get(skill_name, [
            {"title": f"Complete {skill_name.title()} Guide", "provider": "Online Learning", "type": "course", "hours": 30, "relevance": 80, "priority": 1, "rating": 4.0},
            {"title": f"{skill_name.title()} Documentation", "provider": "Official Docs", "type": "tutorial", "hours": 15, "relevance": 75, "priority": 2, "rating": 4.2},
            {"title": f"Hands-on {skill_name.title()} Projects", "provider": "Practice Platform", "type": "practice", "hours": 25, "relevance": 85, "priority": 3, "rating": 4.1}
        ])
    
    def _calculate_learning_timeline(self, skill_gaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate learning timeline for skill gaps."""
        timeline = {}
        
        # Sort by priority (critical first)
        priority_order = {"critical": 1, "important": 2, "nice-to-have": 3}
        sorted_gaps = sorted(skill_gaps, key=lambda x: priority_order.get(x["importance"], 3))
        
        cumulative_hours = 0
        for gap in sorted_gaps:
            skill_name = gap["skill_name"]
            hours = gap["estimated_learning_hours"]
            
            timeline[skill_name] = {
                "hours": hours,
                "start_week": cumulative_hours // 40,  # Assuming 40 hours per week
                "end_week": (cumulative_hours + hours) // 40,
                "priority": gap["importance"]
            }
            
            cumulative_hours += hours
        
        return timeline
    
    def _calculate_priority_scores(
        self, skill_gaps: List[Dict[str, Any]], job_requirements: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate priority scores for each skill gap."""
        priority_scores = {}
        
        for gap in skill_gaps:
            skill_name = gap["skill_name"]
            
            # Base score from importance
            importance_score = {"critical": 100, "important": 75, "nice-to-have": 50}.get(
                gap["importance"], 50
            )
            
            # Market demand factor
            market_factor = gap["market_demand_score"] / 100
            
            # Gap severity factor
            gap_factor = gap["gap_score"] / 100
            
            # Calculate final priority score
            priority_score = importance_score * market_factor * gap_factor
            priority_scores[skill_name] = round(priority_score, 2)
        
        return priority_scores
    
    async def _get_market_data(
        self, db: AsyncSession, skill_names: List[str]
    ) -> Dict[str, Any]:
        """Get market data for skills."""
        market_data = {}
        
        for skill_name in skill_names:
            # Check if we have existing market data
            result = await db.execute(
                select(SkillMarketData).where(
                    SkillMarketData.skill_name == skill_name
                )
            )
            existing_data = result.scalar_one_or_none()
            
            if existing_data:
                market_data[skill_name] = {
                    "demand_score": existing_data.demand_score,
                    "job_postings_count": existing_data.job_postings_count,
                    "growth_rate": existing_data.growth_rate,
                    "average_salary_impact": existing_data.average_salary_impact,
                    "remote_friendly": existing_data.remote_friendly
                }
            else:
                # Generate market data from our skill database
                skill_info = self._get_skill_info(skill_name)
                market_data[skill_name] = {
                    "demand_score": skill_info.get("market_demand", 70),
                    "job_postings_count": skill_info.get("market_demand", 70) * 100,  # Rough estimate
                    "growth_rate": 15.0,  # Default growth rate
                    "average_salary_impact": skill_info.get("avg_salary_impact", 10000),
                    "remote_friendly": skill_info.get("category") == "technical"
                }
        
        return market_data
    
    def _calculate_readiness_score(
        self, 
        user_skills: List[Dict[str, Any]], 
        required_skills: List[Dict[str, Any]], 
        skill_gaps: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall job readiness score."""
        if not required_skills:
            return 100.0
        
        total_skills = len(required_skills)
        missing_skills = len(skill_gaps)
        
        # Base readiness from skill coverage
        skill_coverage = ((total_skills - missing_skills) / total_skills) * 100
        
        # Adjust for critical skills
        critical_gaps = [gap for gap in skill_gaps if gap["importance"] == "critical"]
        critical_penalty = len(critical_gaps) * 10  # 10 points per critical gap
        
        # Final readiness score
        readiness_score = max(0, skill_coverage - critical_penalty)
        
        return round(readiness_score, 2)
    
    async def _create_skill_gap_records(
        self,
        db: AsyncSession,
        analysis_id: str,
        user_id: str,
        skill_gaps: List[Dict[str, Any]],
        market_data: Dict[str, Any]
    ):
        """Create individual skill gap records."""
        for gap in skill_gaps:
            skill_name = gap["skill_name"]
            market_info = market_data.get(skill_name, {})
            
            skill_gap_record = SkillGap(
                id=str(uuid.uuid4()),
                analysis_id=analysis_id,
                user_id=user_id,
                skill_name=skill_name,
                skill_category=gap["skill_category"],
                importance=gap["importance"],
                current_level=gap["current_level"],
                required_level=gap["required_level"],
                gap_score=gap["gap_score"],
                market_demand_score=market_info.get("demand_score"),
                salary_impact=gap["salary_impact"],
                job_postings_count=market_info.get("job_postings_count"),
                estimated_learning_hours=gap["estimated_learning_hours"],
                difficulty_level=gap["difficulty_level"]
            )
            
            db.add(skill_gap_record)
    
    async def _create_learning_resource_records(
        self,
        db: AsyncSession,
        user_id: str,
        skill_gaps: List[Dict[str, Any]],
        learning_recommendations: List[Dict[str, Any]]
    ):
        """Create learning resource records."""
        # Create a mapping of skill gaps to their IDs (we'll need to flush first)
        await db.flush()
        
        for recommendation in learning_recommendations:
            # Find the corresponding skill gap
            skill_name = recommendation["skill_name"]
            
            # For demo purposes, we'll create a placeholder skill_gap_id
            # In production, you'd query the actual skill gap record
            skill_gap_id = str(uuid.uuid4())  # This should be the actual skill gap ID
            
            resource = LearningResource(
                id=str(uuid.uuid4()),
                skill_gap_id=skill_gap_id,
                user_id=user_id,
                title=recommendation["title"],
                provider=recommendation["provider"],
                resource_type=recommendation["resource_type"],
                url=recommendation.get("url"),
                estimated_hours=recommendation["estimated_hours"],
                difficulty=recommendation["difficulty"],
                cost=recommendation.get("cost"),
                rating=recommendation.get("rating"),
                relevance_score=recommendation["relevance_score"],
                priority_rank=recommendation["priority_rank"]
            )
            
            db.add(resource)
    
    async def _generate_learning_path(
        self,
        db: AsyncSession,
        user_id: str,
        analysis_id: str,
        skill_gaps: List[Dict[str, Any]],
        job_requirements: Dict[str, Any]
    ) -> LearningPath:
        """Generate a structured learning path."""
        # Sort skills by priority
        priority_order = {"critical": 1, "important": 2, "nice-to-have": 3}
        sorted_gaps = sorted(skill_gaps, key=lambda x: (
            priority_order.get(x["importance"], 3),
            -x["market_demand_score"]
        ))
        
        # Create learning steps
        learning_steps = []
        milestones = []
        skill_progression = {}
        
        cumulative_weeks = 0
        for i, gap in enumerate(sorted_gaps):
            skill_name = gap["skill_name"]
            hours = gap["estimated_learning_hours"]
            weeks = max(1, hours // 10)  # Assuming 10 hours per week
            
            learning_steps.append({
                "step": i + 1,
                "skill": skill_name,
                "description": f"Master {skill_name} fundamentals and practical application",
                "estimated_weeks": weeks,
                "resources_count": 3,
                "milestone": f"Complete {skill_name} certification or project"
            })
            
            cumulative_weeks += weeks
            if i % 3 == 2:  # Milestone every 3 skills
                milestones.append({
                    "week": cumulative_weeks,
                    "title": f"Milestone {len(milestones) + 1}: Core Skills Mastery",
                    "description": f"Completed {min(i + 1, 3)} essential skills",
                    "skills_completed": [s["skill"] for s in learning_steps[-3:]]
                })
            
            skill_progression[skill_name] = gap["required_level"]
        
        # Calculate path metrics
        total_hours = sum(gap["estimated_learning_hours"] for gap in skill_gaps)
        total_weeks = max(1, total_hours // 10)
        
        # Determine difficulty level
        avg_difficulty = sum(
            {"beginner": 1, "intermediate": 2, "advanced": 3}.get(gap["difficulty_level"], 2)
            for gap in skill_gaps
        ) / len(skill_gaps)
        difficulty_level = {1: "beginner", 2: "intermediate", 3: "advanced"}[round(avg_difficulty)]
        
        # Calculate alignment scores
        market_alignment = sum(gap["market_demand_score"] for gap in skill_gaps) / len(skill_gaps)
        personalization_score = 85.0  # Based on user's background and preferences
        
        learning_path = LearningPath(
            id=str(uuid.uuid4()),
            user_id=user_id,
            analysis_id=analysis_id,
            path_name=f"Path to {job_requirements.get('title', 'Target Role')}",
            description=f"Structured learning path to master {len(skill_gaps)} essential skills",
            target_role=job_requirements.get("title"),
            learning_steps=json.dumps(learning_steps),
            milestones=json.dumps(milestones),
            skill_progression=json.dumps(skill_progression),
            estimated_total_hours=total_hours,
            estimated_weeks=total_weeks,
            difficulty_level=difficulty_level,
            priority_order=json.dumps([gap["skill_name"] for gap in sorted_gaps]),
            market_alignment_score=market_alignment,
            personalization_score=personalization_score
        )
        
        db.add(learning_path)
        return learning_path
    
    def _get_skill_info(self, skill_name: str) -> Dict[str, Any]:
        """Get skill information from database."""
        return self.skill_database.get(skill_name, {
            "category": "technical",
            "difficulty": "intermediate",
            "market_demand": 70,
            "avg_salary_impact": 10000
        })
    
    def _extract_seniority(self, title: str) -> str:
        """Extract seniority level from job title."""
        title_lower = title.lower()
        if any(word in title_lower for word in ["senior", "sr", "lead", "principal", "staff"]):
            return "senior"
        elif any(word in title_lower for word in ["junior", "jr", "entry", "associate"]):
            return "junior"
        else:
            return "mid"
    
    def _extract_industry(self, company: str) -> str:
        """Extract industry from company name."""
        company_lower = company.lower()
        if any(word in company_lower for word in ["tech", "software", "ai", "data"]):
            return "technology"
        elif any(word in company_lower for word in ["bank", "finance", "capital"]):
            return "finance"
        elif any(word in company_lower for word in ["health", "medical", "pharma"]):
            return "healthcare"
        else:
            return "general"
    
    def _generate_progress_feedback(
        self, 
        progress_record: SkillProgressTracking, 
        progress_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI feedback for skill progress."""
        current_level = progress_record.current_level
        progress_percentage = progress_record.progress_percentage
        hours_invested = progress_record.hours_invested or 0
        
        feedback = {
            "overall_assessment": "Good progress" if progress_percentage > 50 else "Keep going",
            "strengths": [],
            "areas_for_improvement": [],
            "next_steps": [],
            "motivation": ""
        }
        
        # Analyze progress
        if progress_percentage > 75:
            feedback["strengths"].append("Excellent completion rate")
            feedback["next_steps"].append("Consider advanced topics or real-world projects")
        elif progress_percentage > 50:
            feedback["strengths"].append("Steady progress")
            feedback["next_steps"].append("Continue with current learning plan")
        else:
            feedback["areas_for_improvement"].append("Consider increasing study time")
            feedback["next_steps"].append("Focus on foundational concepts")
        
        if hours_invested > 20:
            feedback["strengths"].append("Strong time investment")
        else:
            feedback["areas_for_improvement"].append("Consider dedicating more time to practice")
        
        # Motivational message
        if progress_percentage > 80:
            feedback["motivation"] = "You're almost there! Keep up the excellent work."
        elif progress_percentage > 50:
            feedback["motivation"] = "Great progress! You're on the right track."
        else:
            feedback["motivation"] = "Every expert was once a beginner. Keep learning!"
        
        return feedback
    
    async def _format_analysis_response(self, analysis: SkillGapAnalysis) -> Dict[str, Any]:
        """Format skill gap analysis for API response."""
        return {
            "id": analysis.id,
            "job_id": analysis.job_id,
            "missing_skills": json.loads(analysis.missing_skills),
            "learning_recommendations": json.loads(analysis.learning_recommendations),
            "estimated_timeline": json.loads(analysis.estimated_timeline),
            "priority_scores": json.loads(analysis.priority_score),
            "market_demand": json.loads(analysis.market_demand) if analysis.market_demand else {},
            "metrics": {
                "total_missing_skills": analysis.total_missing_skills,
                "critical_skills_count": analysis.critical_skills_count,
                "estimated_total_hours": analysis.estimated_total_hours,
                "overall_readiness_score": analysis.overall_readiness_score
            },
            "analysis_version": analysis.analysis_version,
            "created_at": analysis.created_at.isoformat(),
            "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None
        }