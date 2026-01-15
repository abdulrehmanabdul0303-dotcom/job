"""
AI Skill Gap Analysis API endpoints.
Provides skill gap analysis, learning recommendations, and progress tracking.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.ai.skill_analyzer import SkillAnalyzerEngine

router = APIRouter()
skill_analyzer = SkillAnalyzerEngine()


# Request/Response Models
class SkillGapAnalysisRequest(BaseModel):
    job_id: str = Field(..., description="Job posting ID to analyze against")
    include_market_data: bool = Field(True, description="Include market demand data")
    regenerate: bool = Field(False, description="Force regenerate analysis")


class SkillProgressUpdateRequest(BaseModel):
    skill_name: str = Field(..., description="Name of the skill to update")
    current_level: Optional[float] = Field(None, ge=0, le=5, description="Current skill level (0-5)")
    progress_percentage: Optional[float] = Field(None, ge=0, le=100, description="Progress percentage (0-100)")
    hours_invested: Optional[float] = Field(None, ge=0, description="Hours invested in learning")
    resources_completed: Optional[int] = Field(None, ge=0, description="Number of resources completed")
    certifications_earned: Optional[List[str]] = Field(None, description="List of certifications earned")
    self_assessment_score: Optional[float] = Field(None, ge=0, le=5, description="Self-assessment score (0-5)")
    progress_notes: Optional[str] = Field(None, description="User's progress notes")


class SkillGapAnalysisResponse(BaseModel):
    id: str
    job_id: str
    missing_skills: List[Dict[str, Any]]
    learning_recommendations: List[Dict[str, Any]]
    estimated_timeline: Dict[str, Any]
    priority_scores: Dict[str, float]
    market_demand: Dict[str, Any]
    metrics: Dict[str, Any]
    analysis_version: str
    created_at: str
    updated_at: Optional[str]


class SkillProgressResponse(BaseModel):
    skill_name: str
    current_level: float
    progress_percentage: float
    hours_invested: float
    ai_feedback: Dict[str, Any]
    updated_at: str


class LearningPathResponse(BaseModel):
    id: str
    path_name: str
    description: str
    target_role: Optional[str]
    learning_steps: List[Dict[str, Any]]
    milestones: List[Dict[str, Any]]
    skill_progression: Dict[str, Any]
    estimated_total_hours: int
    estimated_weeks: int
    difficulty_level: str
    current_step: int
    completion_percentage: float
    priority_order: List[str]
    market_alignment_score: float
    personalization_score: float
    created_at: str


@router.post("/analyze", response_model=SkillGapAnalysisResponse)
async def analyze_skill_gaps(
    request: SkillGapAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze skill gaps for a specific job posting.
    
    This endpoint performs comprehensive skill gap analysis by:
    - Comparing user's skills with job requirements
    - Identifying missing or insufficient skills
    - Generating learning recommendations
    - Calculating learning timeline and priorities
    - Providing market demand insights
    
    **Performance Target**: ≤ 5 seconds
    """
    try:
        result = await skill_analyzer.analyze_skill_gaps(
            db=db,
            user_id=current_user.id,
            job_id=request.job_id,
            include_market_data=request.include_market_data,
            regenerate=request.regenerate
        )
        
        return SkillGapAnalysisResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze skill gaps: {str(e)}"
        )


@router.get("/analysis/{job_id}", response_model=Optional[SkillGapAnalysisResponse])
async def get_skill_analysis(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get existing skill gap analysis for a job.
    
    Returns the most recent skill gap analysis for the specified job,
    or null if no analysis exists.
    """
    try:
        result = await skill_analyzer.get_skill_analysis(
            db=db,
            user_id=current_user.id,
            job_id=job_id
        )
        
        if result:
            return SkillGapAnalysisResponse(**result)
        return None
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve skill analysis: {str(e)}"
        )


@router.put("/progress", response_model=SkillProgressResponse)
async def update_skill_progress(
    request: SkillProgressUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update progress on a specific skill.
    
    This endpoint allows users to track their learning progress including:
    - Current skill level assessment
    - Progress percentage completion
    - Hours invested in learning
    - Resources completed
    - Certifications earned
    - Self-assessment scores
    - Progress notes
    
    The system provides AI-generated feedback based on the progress data.
    """
    try:
        progress_data = request.dict(exclude_unset=True, exclude={"skill_name"})
        
        result = await skill_analyzer.update_skill_progress(
            db=db,
            user_id=current_user.id,
            skill_name=request.skill_name,
            progress_data=progress_data
        )
        
        return SkillProgressResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update skill progress: {str(e)}"
        )


@router.get("/learning-path/{analysis_id}", response_model=Optional[LearningPathResponse])
async def get_learning_path(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get structured learning path for a skill gap analysis.
    
    Returns a personalized learning path with:
    - Ordered learning steps
    - Milestone checkpoints
    - Skill progression targets
    - Time estimates
    - Priority ordering
    - Market alignment scores
    """
    try:
        result = await skill_analyzer.get_learning_path(
            db=db,
            user_id=current_user.id,
            analysis_id=analysis_id
        )
        
        if result:
            return LearningPathResponse(**result)
        return None
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve learning path: {str(e)}"
        )


@router.get("/market-data/{skill_name}")
async def get_skill_market_data(
    skill_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get market data for a specific skill.
    
    Returns market insights including:
    - Demand score and trends
    - Job postings count
    - Salary impact data
    - Growth rate
    - Remote work compatibility
    - Top locations and industries
    """
    try:
        # Get market data for single skill
        market_data = await skill_analyzer._get_market_data(db, [skill_name])
        
        if skill_name in market_data:
            return {
                "skill_name": skill_name,
                "market_data": market_data[skill_name]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Market data not found for skill: {skill_name}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve market data: {str(e)}"
        )


@router.get("/skills/trending")
async def get_trending_skills(
    limit: int = 10,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trending skills based on market demand.
    
    Returns a list of skills with high market demand and growth potential.
    Can be filtered by category (technical, soft, certification, domain).
    """
    try:
        # Get skills from our database, filtered by category if specified
        skills_data = skill_analyzer.skill_database
        
        if category:
            skills_data = {
                name: data for name, data in skills_data.items()
                if data.get("category") == category
            }
        
        # Sort by market demand and return top skills
        trending_skills = sorted(
            skills_data.items(),
            key=lambda x: x[1].get("market_demand", 0),
            reverse=True
        )[:limit]
        
        result = []
        for skill_name, skill_data in trending_skills:
            result.append({
                "skill_name": skill_name,
                "category": skill_data.get("category"),
                "market_demand": skill_data.get("market_demand"),
                "difficulty": skill_data.get("difficulty"),
                "avg_salary_impact": skill_data.get("avg_salary_impact")
            })
        
        return {
            "trending_skills": result,
            "category_filter": category,
            "total_count": len(result)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve trending skills: {str(e)}"
        )


@router.get("/recommendations/{job_id}")
async def get_skill_recommendations(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get quick skill recommendations for a job without full analysis.
    
    This is a lightweight endpoint that provides immediate skill suggestions
    based on job requirements, useful for quick insights before running
    full skill gap analysis.
    """
    try:
        # Get job posting
        job_posting = await skill_analyzer._get_job_posting(db, job_id)
        if not job_posting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found"
            )
        
        # Parse job requirements
        job_requirements = skill_analyzer._parse_job_requirements(job_posting)
        required_skills = skill_analyzer._extract_required_skills(job_requirements)
        
        # Format recommendations
        recommendations = []
        for skill in required_skills[:10]:  # Top 10 recommendations
            skill_info = skill_analyzer._get_skill_info(skill["name"])
            recommendations.append({
                "skill_name": skill["name"],
                "importance": skill["importance"],
                "category": skill["category"],
                "market_demand": skill["market_demand"],
                "difficulty": skill_info.get("difficulty"),
                "estimated_learning_hours": skill_info.get("difficulty") == "advanced" and 80 or 
                                           skill_info.get("difficulty") == "intermediate" and 40 or 20
            })
        
        return {
            "job_id": job_id,
            "job_title": job_posting.title,
            "company": job_posting.company,
            "skill_recommendations": recommendations,
            "total_skills": len(recommendations)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get skill recommendations: {str(e)}"
        )